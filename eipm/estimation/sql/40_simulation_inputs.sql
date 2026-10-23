-- =====================================================================
-- eipm estimation/40_simulation_inputs.sql : inputs for the simulation
-- ---------------------------------------------------------------------
-- One row per APTC application, with what the payment function needs
-- (benchmark premium, household size, income as %FPL, months) and -- for
-- audited applications -- the finding:
--   finding 0 none, 1 monetary (with the income the record supports,
--   true_fpl_pct, and its ratio to the income used), 2 technical.
-- Donor kind: the APTC quintile stratum (P1..P5 -> stratum_code 0..4).
-- Donor-kind post-stratification (sim_kind_deciles = K > 0): kind becomes
-- the stratum x K equal-count quantiles of the annual APTC x within the
-- stratum, computed on the population (ntile over x, ties broken by
-- unit_id), kind = stratum_code x K + quantile - 1 (0..5K-1). With K = 0
-- (default) kind = stratum_code. The audit design, strata, allocation
-- and the analytic estimators are unchanged.
-- =====================================================================
CREATE OR REPLACE TABLE sim_units AS
WITH p AS (
    SELECT *, right(stratum, 1)::INTEGER - 1 AS stratum_code,
           coalesce(getvariable('sim_kind_deciles'), 0)::INTEGER AS kq
    FROM read_parquet(getvariable('repo_root') || '/' || getvariable('population_dir') || '/population.parquet')
)
SELECT row_number() OVER (ORDER BY unit_id) - 1 AS unit_idx, unit_id, stratum, stratum_code,
       CASE WHEN kq > 0
            THEN stratum_code * kq + ntile(greatest(kq, 1)) OVER (PARTITION BY stratum_code ORDER BY x, unit_id) - 1
            ELSE stratum_code END AS kind,
       hh_size, fpl_pct, months, benchmark_month::DOUBLE AS benchmark_month,
       (x * 100)::BIGINT AS x_cents, (y * 100)::BIGINT AS y_cents,
       CASE error_type WHEN 'none' THEN 0 WHEN 'monetary' THEN 1 ELSE 2 END AS finding,
       coalesce(true_fpl_pct / fpl_pct, 1.0) AS income_ratio,
       true_fpl_pct
FROM p
ORDER BY unit_id;
