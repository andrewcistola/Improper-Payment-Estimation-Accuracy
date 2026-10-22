-- =====================================================================
-- cert estimation/01_frame.sql : estimands and production design
-- ---------------------------------------------------------------------
-- Estimands (each claim is its own unit, so netting is per claim), all
-- divided by the KNOWN payments X of the domain:
--   national|over  : y = max(y, 0)       national|under : y = max(-y, 0)
--   national|gross : y = |y|              national|net   : y = y
--   <claim type>|gross : |y| within one claim type (ipps, part_a_other,
--                        part_b, dmepos), divided by that type's payments
-- Design (CERT production-like, no MAC jurisdictions): stratified SRS of
-- claims; strata = claim type x five equal-count payment quintiles (20).
-- Claims per claim type = FY 2025 claims reviewed (config claim_audit);
-- within a claim type, Neyman allocation across its quintiles:
--   n_h ~ N_h x S_h, S_h = standard deviation of gross improper dollars
--   |y| in stratum h (from the population, standing in for prior-year
--   data); integers by largest remainder, at least 2 per stratum. Every
--   domain uses the same sample.
-- Output: cert_frame, alloc  (input to 02_sample.sql)
-- =====================================================================
CREATE OR REPLACE TABLE cert_frame AS
SELECT unit_id, claim_type, stratum, x::DECIMAL(18, 6) AS x, y::DECIMAL(18, 6) AS y
FROM read_parquet(getvariable('repo_root') || '/' || getvariable('population_dir') || '/population.parquet');

CREATE OR REPLACE TABLE claim_audit AS
SELECT * FROM (SELECT unnest(from_json(getvariable('claim_audit')::JSON,
    '[{"claim_type":"VARCHAR","n":"BIGINT"}]'), recursive := true));

-- Neyman allocation within each claim type
CREATE OR REPLACE TABLE cert_neyman AS
WITH s AS (SELECT claim_type, stratum, count(*) AS big_n,   -- population SD of |y| from exact DECIMAL sums
                  sqrt(greatest(0, sum(y::DECIMAL(38, 6) * y::DECIMAL(38, 6))::DOUBLE / count(*)
                                   - power(sum(abs(y))::DOUBLE / count(*), 2))) AS s_h
           FROM cert_frame GROUP BY claim_type, stratum),
raw AS (SELECT s.*, a.n AS n_type, a.n * big_n * s_h / sum(big_n * s_h) OVER (PARTITION BY claim_type) AS n_raw
        FROM s JOIN claim_audit a USING (claim_type)),
fl AS (SELECT *, floor(n_raw)::BIGINT AS n_floor,
              row_number() OVER (PARTITION BY claim_type ORDER BY n_raw - floor(n_raw) DESC, stratum) AS rk FROM raw),
lr AS (SELECT *, n_floor + CASE WHEN rk <= n_type - sum(n_floor) OVER (PARTITION BY claim_type) THEN 1 ELSE 0 END AS n_lr FROM fl),
mn AS (SELECT *, greatest(n_lr, 2) AS n_min FROM lr),
big AS (SELECT claim_type, arg_max(stratum, n_min * 1e6 - right(stratum, 1)::INT) AS big_stratum,
               sum(n_min) - any_value(n_type) AS excess
        FROM mn GROUP BY claim_type)                                   -- any units added by the minimum
SELECT m.claim_type, m.stratum, m.big_n, m.s_h,                        -- come out of the type's largest stratum
       (m.n_min - CASE WHEN m.stratum = b.big_stratum THEN b.excess ELSE 0 END)::BIGINT AS n_h
FROM mn m JOIN big b USING (claim_type);

CREATE OR REPLACE TABLE alloc AS SELECT stratum, n_h FROM cert_neyman;
