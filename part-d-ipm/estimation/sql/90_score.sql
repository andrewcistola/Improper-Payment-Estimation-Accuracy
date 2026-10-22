-- =====================================================================
-- partd estimation/90_score.sql : compare every interval with the truth
-- ---------------------------------------------------------------------
-- estimates: one row per sample x domain x method x interval
--   expansion (plug-in benefit rerun), ratio, regression, pde_expansion,
--   pde_ratio, simulation. For pde_expansion and pde_ratio the domains are
--   defined at the PDE level (signed marginal effect per audited PDE, not
--   netted per beneficiary); they are scored against the same
--   beneficiary-netted truth as the other methods.
-- metrics  : coverage, tail balance, bias, RMSE and width per method
-- Formula: shared/sql/lib/02_estimators.sql (ipm_score).
-- =====================================================================
CREATE OR REPLACE TABLE estimates AS
SELECT * FROM est_expansion
UNION ALL SELECT * FROM est_ratio
UNION ALL SELECT * FROM est_regression
UNION ALL SELECT * FROM est_pde          -- pde_expansion, pde_ratio (PDE-level over/under/gross/net)
UNION ALL SELECT * FROM est_simulation;

CREATE OR REPLACE TABLE metrics AS SELECT * FROM ipm_score();
