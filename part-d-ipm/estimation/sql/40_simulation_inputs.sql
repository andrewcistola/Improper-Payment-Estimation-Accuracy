-- =====================================================================
-- partd estimation/40_simulation_inputs.sql : inputs for the simulation
-- ---------------------------------------------------------------------
-- The Part D simulation uses its own audit design (claim level), as in
-- production:
--   audit      : sim_claims PDEs drawn at random from ALL PDEs,
--                independent of beneficiary (sim_claim_sample, one set
--                per Monte Carlo sample); their findings are the ratios
--                corrected GDC / submitted GDC
--   projection : each iteration draws sim_bene_draws beneficiaries with
--                replacement, applies audited-claim findings to their
--                PDEs, and reruns the benefit (simulation.py)
-- The expansion, ratio and regression methods keep the beneficiary audit.
--   sim_units : one row per beneficiary (unit index = position)
--   sim_rows  : one row per PDE, sorted by beneficiary then fill order
-- Amounts are integer cents so the payment function can be exact.
-- =====================================================================
CREATE OR REPLACE TABLE sim_units AS
SELECT row_number() OVER (ORDER BY unit_id) - 1 AS unit_idx, unit_id AS bene_id, stratum, lis,
       (x * 100)::BIGINT AS x_cents, (y * 100)::BIGINT AS y_cents
FROM read_parquet(getvariable('repo_root') || '/' || getvariable('population_dir') || '/population.parquet')
ORDER BY unit_id;

CREATE OR REPLACE TABLE sim_rows AS
WITH r AS (
    SELECT u.unit_idx, p.pde_id,
           row_number() OVER (PARTITION BY u.unit_idx ORDER BY p.fill_day, p.pde_id) AS seq,
           p.brand, p.lis,
           (p.gdc_submitted * 100)::BIGINT AS sub_cents,
           (p.gdc_corrected * 100)::BIGINT AS cor_cents
    FROM read_parquet(getvariable('repo_root') || '/' || getvariable('population_dir') || '/pde_detail.parquet') p
    JOIN sim_units u USING (bene_id)
)
SELECT row_number() OVER (ORDER BY unit_idx, seq) - 1 AS row_idx, *
FROM r ORDER BY unit_idx, seq;

-- Claim-level audit: SRS of sim_claims PDEs per Monte Carlo sample
CREATE OR REPLACE TABLE sim_claim_sample AS
SELECT r.rep, s.row_idx
FROM sim_rows s
CROSS JOIN (SELECT range::INTEGER AS rep, rbase(getvariable('seed'), 'claims', range, 0) AS base
            FROM range(1, getvariable('sim_reps') + 1)) r
QUALIFY row_number() OVER (PARTITION BY r.rep ORDER BY u01f(r.base, s.pde_id), s.pde_id) <= getvariable('sim_claims');
