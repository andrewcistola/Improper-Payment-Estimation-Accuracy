-- =====================================================================
-- perm estimation/40_simulation_inputs.sql : simulation inputs
-- ---------------------------------------------------------------------
-- One row per payment in the state (unit index = position), with its
-- beneficiary, and -- for audited payments -- the findings:
--   claims review : improper share of the payment (taint = y_claims / x)
--   eligibility   : the beneficiary's eligibility error (all payments)
-- Donor kinds: claims findings within the payment stratum (payment type
-- x payment quintile P1..P5, claims_kind 0..9); eligibility from the
-- audited beneficiaries of the state.
-- Donor-kind post-stratification (sim_kind_deciles = K > 0): the claims
-- kind becomes the design stratum x K equal-count quantiles of the
-- payment x within the stratum, computed on the state's population
-- (ntile over x, ties broken by unit_id), claims_kind = stratum x K +
-- quantile - 1 (0..10K-1); stratum_kind keeps the design stratum (0..9) so
-- the kernel can fall back to the stratum's pooled audit for a kind with no
-- audited payment. The audit design, strata, allocation, the eligibility
-- kinds and the analytic estimators are unchanged.
-- =====================================================================
CREATE OR REPLACE TABLE sim_units AS
WITH p AS (
    SELECT unit_id, bene_id, stratum, x, y_claims, y_elig,
           (CASE payment_type WHEN 'FFS' THEN 0 ELSE 1 END) * 5 + (right(stratum, 1)::INTEGER - 1) AS stratum_kind,
           coalesce(getvariable('sim_kind_deciles'), 0)::INTEGER AS kq
    FROM read_parquet(getvariable('repo_root') || '/' || getvariable('population_dir') || '/population.parquet')
    WHERE state_id = getvariable('state_id')
)
SELECT row_number() OVER (ORDER BY unit_id) - 1 AS unit_idx, unit_id, bene_id, stratum, stratum_kind,
       CASE WHEN kq > 0
            THEN stratum_kind * kq + ntile(greatest(kq, 1)) OVER (PARTITION BY stratum_kind ORDER BY x, unit_id) - 1
            ELSE stratum_kind END AS claims_kind,
       (x * 100)::BIGINT AS x_cents, (y_claims * 100)::BIGINT AS y_claims_cents,
       y_elig > 0 AS elig_error
FROM p
ORDER BY unit_id;
