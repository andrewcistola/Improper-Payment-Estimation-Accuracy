-- =====================================================================
-- cert estimation/cert_40_simulation_inputs.sql : simulation inputs
-- ---------------------------------------------------------------------
-- One row per claim, with -- for audited claims -- the finding: the
-- improper share of the payment (taint = y / x). One donor kind.
-- =====================================================================
CREATE OR REPLACE TABLE sim_units AS
SELECT row_number() OVER (ORDER BY unit_id) - 1 AS unit_idx, unit_id, stratum,
       (x * 100)::BIGINT AS x_cents, (y * 100)::BIGINT AS y_cents
FROM read_parquet(getvariable('repo_root') || '/' || getvariable('population_dir') || '/population.parquet')
ORDER BY unit_id;
