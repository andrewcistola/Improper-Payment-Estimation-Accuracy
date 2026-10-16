-- =====================================================================
-- partc estimation/30_regression.sql : regression (GREG) estimator
-- ---------------------------------------------------------------------
-- theta_hat = [T_y + b (X - T_x)] / X: |y| regressed on enrollee payment
-- x (intercept + slope), calibrated to the known payment total X.
-- Residual-based standard error. Normal 95% interval.
-- Formula: shared/sql/lib/02_estimators.sql (ipm_regression).
-- =====================================================================
CREATE OR REPLACE TABLE est_regression AS
SELECT * FROM ipm_regression(getvariable('alpha'));
