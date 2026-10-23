-- =====================================================================
-- cert estimation/40_simulation_inputs.sql : simulation inputs
-- ---------------------------------------------------------------------
-- One row per claim (unit index = position by unit_id) with its amount
-- paid, its claim type and stratum (claim type x payment quintile,
-- kind = type_code x 5 + quintile - 1, 0..19), and -- for audited claims
-- -- the finding y (cents; negative = underpayment).
-- Donor-kind post-stratification (sim_kind_deciles = K > 0): the
-- simulation's donor kind becomes the design stratum x K equal-count
-- quantiles of the amount paid within the stratum, computed on the
-- population (ntile over x, ties broken by unit_id), kind = stratum x K
-- + quantile - 1 (0..20K-1); stratum_kind keeps the design stratum (0..19)
-- so the kernel can fall back to the stratum's pooled audit for a kind with
-- no audited claim. The audit design, strata, allocation and the analytic
-- estimators are unchanged. K = 0 (default): the design stratum is the kind.
-- =====================================================================
CREATE OR REPLACE TABLE sim_units AS
WITH p AS (
    SELECT unit_id, type_code, type_code * 5 + right(stratum, 1)::INTEGER - 1 AS stratum_kind, x, y,
           coalesce(getvariable('sim_kind_deciles'), 0)::INTEGER AS kq
    FROM read_parquet(getvariable('repo_root') || '/' || getvariable('population_dir') || '/population.parquet')
)
SELECT row_number() OVER (ORDER BY unit_id) - 1 AS unit_idx, unit_id, type_code, stratum_kind,
       CASE WHEN kq > 0
            THEN stratum_kind * kq + ntile(greatest(kq, 1)) OVER (PARTITION BY stratum_kind ORDER BY x, unit_id) - 1
            ELSE stratum_kind END AS kind,
       (x * 100)::BIGINT AS x_cents, (y * 100)::BIGINT AS y_cents
FROM p
ORDER BY unit_id;
