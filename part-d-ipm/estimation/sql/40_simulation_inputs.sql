-- =====================================================================
-- partd estimation/40_simulation_inputs.sql : the PDE audit and the
-- population rows for expansion and the bootstrap simulation
-- ---------------------------------------------------------------------
-- Claim strata (every PDE in the population):
--   0 a_ltc       long-term care claims, any cost
--   1 b_low_cost  non-LTC claims in the lowest decile of submitted GDC
--   2 c_other     all other non-LTC claims
-- PDE audit: stratified SRS of sim_audit_size (5,000) PDEs per audit
-- year, Neyman allocation n_h ~ N_h x S_h, S_h = standard deviation of
-- the PDE's GDC error dollars in stratum h. S_h comes from the
-- population and stands in for prior-year audit data; integers by
-- largest remainder, at least 2 per stratum. Finding = corrected GDC /
-- submitted GDC.
--   sim_units  : one row per beneficiary (unit index = position)
--   sim_rows   : one row per PDE, sorted by beneficiary then fill order,
--                with the simulation's donor kind: the claim stratum, or,
--                with sim_kind_deciles = K > 0, stratum_code x K + the
--                PDE's equal-count quantile (1..K) of submitted GDC within
--                its stratum, computed on the population (ntile over
--                sub_cents, ties broken by pde_id), minus 1 (0..3K-1).
--                The strata, the Neyman PDE audit and the expansion /
--                pde_expansion / pde_ratio estimators keep the 3 strata.
--   pde_strata : N_h, S_h, n_h per stratum
--   sim_audit_sample(rep, row_idx)
-- Amounts are integer cents so the benefit rerun is exact.
-- =====================================================================
CREATE OR REPLACE TABLE sim_units AS
SELECT row_number() OVER (ORDER BY unit_id) - 1 AS unit_idx, unit_id AS bene_id, lis,
       (x * 100)::BIGINT AS x_cents, (y * 100)::BIGINT AS y_cents
FROM read_parquet(getvariable('repo_root') || '/' || getvariable('population_dir') || '/population.parquet')
ORDER BY unit_id;

CREATE OR REPLACE TABLE sim_rows AS
WITH p AS (
    SELECT * FROM read_parquet(getvariable('repo_root') || '/' || getvariable('population_dir') || '/pde_detail.parquet')
),
cut AS (SELECT quantile_cont(gdc_submitted::DOUBLE, 0.10) AS low FROM p WHERE NOT ltc),
r AS (
    SELECT u.unit_idx, p.pde_id,
           row_number() OVER (PARTITION BY u.unit_idx ORDER BY p.fill_day, p.pde_id) AS seq,
           p.brand, p.lis,
           CASE WHEN p.ltc THEN 0 WHEN p.gdc_submitted::DOUBLE <= cut.low THEN 1 ELSE 2 END AS stratum_code,
           (p.gdc_submitted * 100)::BIGINT AS sub_cents,
           (p.gdc_corrected * 100)::BIGINT AS cor_cents,
           coalesce(getvariable('sim_kind_deciles'), 0)::INTEGER AS kq
    FROM p JOIN sim_units u USING (bene_id), cut
),
k AS (   -- the simulation's donor kind (post-stratified by submitted GDC when sim_kind_deciles > 0)
    SELECT * EXCLUDE (kq),
           CASE WHEN kq > 0
                THEN stratum_code * kq + ntile(greatest(kq, 1)) OVER (PARTITION BY stratum_code ORDER BY sub_cents, pde_id) - 1
                ELSE stratum_code END AS kind
    FROM r
)
SELECT row_number() OVER (ORDER BY unit_idx, seq) - 1 AS row_idx, *
FROM k ORDER BY unit_idx, seq;

-- Neyman allocation of the PDE audit
CREATE OR REPLACE TABLE pde_strata AS
WITH s AS (
    SELECT stratum_code, count(*) AS big_n, stddev_pop((sub_cents - cor_cents) / 100.0) AS s_h
    FROM sim_rows GROUP BY stratum_code
),
raw AS (SELECT *, getvariable('sim_audit_size') * big_n * s_h / sum(big_n * s_h) OVER () AS n_raw FROM s),
fl AS (SELECT *, floor(n_raw)::BIGINT AS n_floor,
              row_number() OVER (ORDER BY n_raw - floor(n_raw) DESC, stratum_code) AS rk FROM raw),
lr AS (SELECT *, n_floor + CASE WHEN rk <= getvariable('sim_audit_size') - sum(n_floor) OVER () THEN 1 ELSE 0 END AS n_lr
       FROM fl),
mn AS (SELECT *, greatest(n_lr, 2) AS n_min FROM lr)   -- at least 2 per stratum (variance)
SELECT stratum_code, CASE stratum_code WHEN 0 THEN 'a_ltc' WHEN 1 THEN 'b_low_cost' ELSE 'c_other' END AS stratum,
       big_n, s_h,
       -- any units added by the minimum come out of the largest stratum
       n_min - CASE WHEN n_min = max(n_min) OVER () THEN sum(n_min) OVER () - getvariable('sim_audit_size') ELSE 0 END AS n_h
FROM mn ORDER BY stratum_code;

-- PDE audit: stratified SRS per audit year
CREATE OR REPLACE TABLE sim_audit_sample AS
SELECT r.rep, s.row_idx
FROM sim_rows s
JOIN pde_strata a USING (stratum_code)
CROSS JOIN (SELECT range::INTEGER AS rep, rbase(getvariable('seed'), 'claims', range, 0) AS base
            FROM range(1, getvariable('sim_reps') + 1)) r
QUALIFY row_number() OVER (PARTITION BY r.rep, s.stratum_code ORDER BY u01f(r.base, s.pde_id), s.pde_id) <= a.n_h
ORDER BY r.rep, s.row_idx;
