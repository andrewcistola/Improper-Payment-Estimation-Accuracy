-- =====================================================================
-- cert estimation/cert_01_frame.sql : estimand and design
-- ---------------------------------------------------------------------
-- Estimand: claim improper payment rate, theta = sum y / sum x, for each
-- stress population (shape x error rate; see errors/cert.yaml).
-- Design: simple random sample of n claims (Edwards et al. use n = 30),
-- the small-sample, skewed regime where normal intervals are known to
-- fail.
-- Output: pop, alloc  (input to shared/sql/sample.sql)
-- =====================================================================
CREATE OR REPLACE TABLE pop AS
SELECT 'national' AS domain, stratum, unit_id,
       y::DECIMAL(18, 6) AS y, x::DECIMAL(18, 6) AS x
FROM read_parquet(getvariable('repo_root') || '/' || getvariable('population_dir') || '/population.parquet');

CREATE OR REPLACE TABLE alloc AS
SELECT 'national' AS domain, 'all' AS stratum, getvariable('n')::BIGINT AS n_h;
