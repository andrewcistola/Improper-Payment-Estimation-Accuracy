-- =====================================================================
-- eipm estimation/01_frame.sql : estimands and production design
-- ---------------------------------------------------------------------
-- Estimands, one domain each, over all FFE applications receiving APTC,
-- divided by the KNOWN total APTC paid X (x = annual APTC paid):
--   national|gross     : y = improper APTC (every error is an
--                        overpayment, so gross = overpayments = net)
--   national|technical : y = whole APTC where a required data match was
--                        not run (technically improper)
--   national|monetary  : y = APTC paid - APTC at the supported income
-- Design: stratified SRS of applications; strata = five equal-count
-- quintiles of annual APTC paid (P1..P5; EIPM strata are not public, so
-- these are illustrative, the same rule as PERM's payment quintiles).
-- Neyman allocation of audit_size (2,000) applications:
--   n_h ~ N_h x S_h, S_h = standard deviation of gross improper dollars in
--   stratum h (from the population, standing in for prior-year data);
--   integers by largest remainder, at least 2 per stratum. All three
--   domains share one sample (same stratum and unit_id).
-- Output: pop, alloc  (input to shared/sql/sample_srs.sql)
-- =====================================================================
CREATE OR REPLACE TABLE eipm_frame AS
SELECT *
FROM read_parquet(getvariable('repo_root') || '/' || getvariable('population_dir') || '/population.parquet');

CREATE OR REPLACE TABLE pop AS
SELECT 'national|' || c.component AS domain, stratum, unit_id,
       (CASE c.component WHEN 'gross' THEN y WHEN 'technical' THEN y_technical ELSE y_monetary END)::DECIMAL(18, 6) AS y,
       x::DECIMAL(18, 6) AS x
FROM eipm_frame,
     (SELECT unnest(from_json(getvariable('components')::JSON, '["VARCHAR"]')) AS component) c;

-- Neyman allocation per stratum (same for every domain)
CREATE OR REPLACE TABLE eipm_neyman AS
WITH s AS (SELECT stratum, count(*) AS big_n,   -- population SD from exact DECIMAL sums (thread-order independent)
                  sqrt(greatest(0, sum(y::DECIMAL(38, 6) * y::DECIMAL(38, 6))::DOUBLE / count(*)
                                   - power(sum(y)::DOUBLE / count(*), 2))) AS s_h
           FROM eipm_frame GROUP BY stratum),
raw AS (SELECT *, getvariable('audit_size') * big_n * s_h / sum(big_n * s_h) OVER () AS n_raw FROM s),
fl AS (SELECT *, floor(n_raw)::BIGINT AS n_floor,
              row_number() OVER (ORDER BY n_raw - floor(n_raw) DESC, stratum) AS rk FROM raw),
lr AS (SELECT *, n_floor + CASE WHEN rk <= getvariable('audit_size') - sum(n_floor) OVER () THEN 1 ELSE 0 END AS n_lr FROM fl),
mn AS (SELECT *, greatest(n_lr, 2) AS n_min FROM lr),
big AS (SELECT stratum FROM mn ORDER BY n_min DESC, stratum LIMIT 1)   -- any units added by the minimum
SELECT stratum, big_n, s_h,                                            -- come out of the largest stratum
       n_min - CASE WHEN stratum = (SELECT stratum FROM big)
                    THEN (SELECT sum(n_min) FROM mn) - getvariable('audit_size') ELSE 0 END AS n_h
FROM mn;

CREATE OR REPLACE TABLE alloc AS
SELECT DISTINCT p.domain, p.stratum, n.n_h::BIGINT AS n_h
FROM pop p JOIN eipm_neyman n USING (stratum);
