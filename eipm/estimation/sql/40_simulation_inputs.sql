-- =====================================================================
-- eipm estimation/40_simulation_inputs.sql : inputs for the simulation
-- ---------------------------------------------------------------------
-- One row per APTC application, with what the payment function needs
-- (benchmark premium, household size, income as %FPL, months) and -- for
-- audited applications -- the finding:
--   finding 0 none, 1 monetary (with the income the record supports,
--   true_fpl_pct, and its ratio to the income used), 2 technical.
-- Donor kind: the APTC quintile stratum (P1..P5 -> 0..4).
-- =====================================================================
CREATE OR REPLACE TABLE sim_units AS
SELECT row_number() OVER (ORDER BY unit_id) - 1 AS unit_idx, unit_id, stratum,
       right(stratum, 1)::INTEGER - 1 AS stratum_code,
       hh_size, fpl_pct, months, benchmark_month::DOUBLE AS benchmark_month,
       (x * 100)::BIGINT AS x_cents, (y * 100)::BIGINT AS y_cents,
       CASE error_type WHEN 'none' THEN 0 WHEN 'monetary' THEN 1 ELSE 2 END AS finding,
       coalesce(true_fpl_pct / fpl_pct, 1.0) AS income_ratio,
       true_fpl_pct
FROM read_parquet(getvariable('repo_root') || '/' || getvariable('population_dir') || '/population.parquet')
ORDER BY unit_id;
