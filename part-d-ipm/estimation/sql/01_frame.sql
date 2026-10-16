-- =====================================================================
-- partd estimation/01_frame.sql : estimand and production design
-- ---------------------------------------------------------------------
-- Estimand: national GROSS improper payment rate for Part D,
--   theta = sum |y| / sum x  over all beneficiaries,
--   y = Medicare payment error after re-running the benefit on corrected
--       PDEs (errors/), x = Medicare payment for the beneficiary.
-- Design: simple random sample of beneficiaries (random selection since
-- FY 2025); the beneficiary is the sampling unit and carries all of its
-- PDEs. Sample size from config (not public).
-- Output: pop, alloc  (input to shared/sql/sample_srs.sql)
-- =====================================================================
CREATE OR REPLACE TABLE pop AS
SELECT 'national' AS domain, stratum, unit_id,
       abs(y)::DECIMAL(18, 6) AS y, x::DECIMAL(18, 6) AS x
FROM read_parquet(getvariable('repo_root') || '/' || getvariable('population_dir') || '/population.parquet');

CREATE OR REPLACE TABLE alloc AS
SELECT 'national' AS domain, stratum, n_h
FROM (SELECT unnest(from_json(getvariable('allocation')::JSON,
                              '[{"stratum":"VARCHAR","n_h":"BIGINT"}]'), recursive := true));
