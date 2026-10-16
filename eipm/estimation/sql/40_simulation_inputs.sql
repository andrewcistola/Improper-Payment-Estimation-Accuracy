-- =====================================================================
-- eipm estimation/40_simulation_inputs.sql : inputs for the simulation
-- ---------------------------------------------------------------------
-- One row per APTC application, with what the payment function needs
-- (benchmark premium, household size, income as %FPL, months) and -- for
-- audited applications -- the finding: error type and, for an income
-- misstatement, the income the record supports (true_fpl_pct).
-- Donor kind: income-band stratum.
-- =====================================================================
CREATE OR REPLACE TABLE sim_units AS
SELECT row_number() OVER (ORDER BY unit_id) - 1 AS unit_idx, unit_id, stratum,
       CASE stratum WHEN 'A_lt150' THEN 0 WHEN 'B_150_250' THEN 1 WHEN 'C_250_400' THEN 2 ELSE 3 END AS stratum_code,
       hh_size, fpl_pct, months, benchmark_month::DOUBLE AS benchmark_month,
       (x * 100)::BIGINT AS x_cents, (y * 100)::BIGINT AS y_cents,
       CASE error_type WHEN 'none' THEN 0 WHEN 'income_misstatement' THEN 1
                       WHEN 'eligibility_failure' THEN 2 ELSE 3 END AS finding,
       coalesce(true_fpl_pct / fpl_pct, 1.0) AS income_ratio,
       true_fpl_pct
FROM read_parquet(getvariable('repo_root') || '/' || getvariable('population_dir') || '/population.parquet')
ORDER BY unit_id;
