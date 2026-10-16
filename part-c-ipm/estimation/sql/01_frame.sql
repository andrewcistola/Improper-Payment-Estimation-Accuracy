-- =====================================================================
-- partc estimation/01_frame.sql : estimand and production design
-- ---------------------------------------------------------------------
-- Estimand: national GROSS improper payment rate for Part C,
--   theta = sum |y| / sum x  over all enrollees,
--   y = enrollee payment error (over- or underpayment), x = payment.
-- Design: stratified SRS of enrollees within risk-score terciles
-- (low / medium / high); stratum sample sizes from config (Part C IPM
-- sizes are not public). Errors are taken from the errors/ population
-- (in production they come from medical record review).
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
