-- =====================================================================
-- partd estimation/01_frame.sql : estimands and the beneficiary audit
-- ---------------------------------------------------------------------
-- Estimands, one domain each, over every beneficiary, divided by the
-- KNOWN total Part D payments X (all reported payment sources: direct
-- subsidy + reinsurance + LICS, $105.56B national):
--   national|over  : y = max(payment error, 0)      overpayments
--   national|under : y = max(-payment error, 0)     underpayments
--   national|gross : y = |payment error|            (= over + under)
--   national|net   : y = payment error              (= over - under)
-- payment error = Medicare(submitted PDEs) - Medicare(corrected PDEs),
-- reinsurance + LICS, after re-running the CY 2025 benefit (errors/),
-- netted within each beneficiary.
-- Beneficiary audit (ratio and regression): simple random sample of 990
-- beneficiaries, every PDE reviewed. The PDE audit used by expansion and
-- the bootstrap simulation is in 40_simulation_inputs.sql.
-- Output: pop, alloc  (input to shared/sql/sample_srs.sql)
-- =====================================================================
CREATE OR REPLACE TABLE pop AS
SELECT 'national|' || m.measure AS domain, p.stratum, p.unit_id,
       (CASE m.measure WHEN 'over'  THEN greatest(p.y, 0)
                       WHEN 'under' THEN greatest(-p.y, 0)
                       WHEN 'gross' THEN abs(p.y)
                       ELSE p.y END)::DECIMAL(18, 6) AS y,
       p.x::DECIMAL(18, 6) AS x
FROM read_parquet(getvariable('repo_root') || '/' || getvariable('population_dir') || '/population.parquet') p,
     (SELECT unnest(['over', 'under', 'gross', 'net']) AS measure) m;

CREATE OR REPLACE TABLE alloc AS
SELECT 'national|' || m.measure AS domain, a.stratum, a.n_h
FROM (SELECT unnest(from_json(getvariable('allocation')::JSON,
                              '[{"stratum":"VARCHAR","n_h":"BIGINT"}]'), recursive := true)) a,
     (SELECT unnest(['over', 'under', 'gross', 'net']) AS measure) m;
