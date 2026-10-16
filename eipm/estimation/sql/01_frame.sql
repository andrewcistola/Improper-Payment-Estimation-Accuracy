-- =====================================================================
-- eipm estimation/01_frame.sql : estimand and production design
-- ---------------------------------------------------------------------
-- Estimand: GROSS APTC improper payment rate,
--   theta = sum |y| / sum x  over all FFE applications receiving APTC,
--   y = APTC paid - correct APTC, x = APTC paid.
-- Design: stratified SRS of applications, ~2,000 in total; strata are
-- income bands (EIPM strata are not public; illustrative).
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
