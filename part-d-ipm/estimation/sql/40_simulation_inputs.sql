-- =====================================================================
-- partd estimation/40_simulation_inputs.sql : inputs for the simulation
-- ---------------------------------------------------------------------
-- The Part D simulation uses its own design, as in production. Each
-- audit year has two samples, both drawn once and held fixed for all
-- of that year's iterations:
--   audit sample       : sim_audit_size PDEs drawn at random from ALL
--                        PDEs, independent of beneficiary (SRS without
--                        replacement); their findings are the ratios
--                        corrected GDC / submitted GDC
--   beneficiary sample : sim_bene_size beneficiaries drawn with
--                        replacement (108,000 = the population size,
--                        standing in for production's random 1 million)
-- Each iteration applies audit-sample findings to the PDEs of the
-- beneficiary sample and reruns the benefit (simulation.py).
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

-- Audit sample (table sim_audit_sample): SRS of sim_audit_size PDEs per audit year
CREATE OR REPLACE TABLE sim_audit_sample AS
SELECT r.rep, s.row_idx
FROM sim_rows s
CROSS JOIN (SELECT range::INTEGER AS rep, rbase(getvariable('seed'), 'claims', range, 0) AS base
            FROM range(1, getvariable('sim_reps') + 1)) r
QUALIFY row_number() OVER (PARTITION BY r.rep ORDER BY u01f(r.base, s.pde_id), s.pde_id) <= getvariable('sim_audit_size');

-- Beneficiary sample (table sim_bene_sample): sim_bene_size draws with replacement per audit
-- year; draw d picks beneficiary floor(u * N), u uniform on (0, 1)
CREATE OR REPLACE TABLE sim_bene_sample AS
SELECT r.rep, d.range + 1 AS draw,
       least(floor(u01f(r.base, d.range + 1) * n.big_n)::BIGINT, n.big_n - 1) AS unit_idx
FROM (SELECT range::INTEGER AS rep, rbase(getvariable('seed'), 'benes', range, 0) AS base
      FROM range(1, getvariable('sim_reps') + 1)) r
CROSS JOIN range(getvariable('sim_bene_size')) d
CROSS JOIN (SELECT count(*) AS big_n FROM sim_units) n
ORDER BY r.rep, draw;
