-- =====================================================================
-- cert estimation/90_score.sql : compare every interval with the truth
-- ---------------------------------------------------------------------
-- estimates: one row per sample x domain x method x interval
-- metrics  : coverage, tail balance, bias, RMSE and width per method
-- Formula: shared/sql/lib/02_estimators.sql (ipm_score).
-- =====================================================================
CREATE OR REPLACE TABLE estimates AS
SELECT * FROM est_expansion
UNION ALL SELECT * FROM est_ratio
UNION ALL SELECT * FROM est_regression
UNION ALL SELECT * FROM est_simulation;

CREATE OR REPLACE TABLE metrics AS SELECT * FROM ipm_score();
