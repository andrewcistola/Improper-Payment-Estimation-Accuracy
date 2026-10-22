-- =====================================================================
-- cert estimation/40_simulation_inputs.sql : simulation inputs
-- ---------------------------------------------------------------------
-- One row per claim (unit index = position by unit_id) with its amount
-- paid, its claim type and stratum (claim type x payment quintile,
-- kind = type_code x 5 + quintile - 1, 0..19), and -- for audited claims
-- -- the finding y (cents; negative = underpayment).
-- =====================================================================
CREATE OR REPLACE TABLE sim_units AS
SELECT row_number() OVER (ORDER BY unit_id) - 1 AS unit_idx, unit_id, type_code,
       type_code * 5 + right(stratum, 1)::INTEGER - 1 AS kind,
       (x * 100)::BIGINT AS x_cents, (y * 100)::BIGINT AS y_cents
FROM read_parquet(getvariable('repo_root') || '/' || getvariable('population_dir') || '/population.parquet')
ORDER BY unit_id;
