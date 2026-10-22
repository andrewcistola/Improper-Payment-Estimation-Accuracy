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
-- =====================================================================
CREATE OR REPLACE TABLE sim_units AS
SELECT row_number() OVER (ORDER BY unit_id) - 1 AS unit_idx, unit_id, bene_id, stratum,
       (CASE payment_type WHEN 'FFS' THEN 0 ELSE 1 END) * 5
         + (right(stratum, 1)::INTEGER - 1) AS claims_kind,
       (x * 100)::BIGINT AS x_cents, (y_claims * 100)::BIGINT AS y_claims_cents,
       y_elig > 0 AS elig_error
FROM read_parquet(getvariable('repo_root') || '/' || getvariable('population_dir') || '/population.parquet')
WHERE state_id = getvariable('state_id')
ORDER BY unit_id;
