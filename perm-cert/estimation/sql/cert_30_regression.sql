-- =====================================================================
-- cert estimation/cert_30_regression.sql : regression (GREG) estimator
-- ---------------------------------------------------------------------
-- Estimand: claim improper payment rate, sum y / sum x.
-- theta_hat = [T_y + b (X - T_x)] / X: y regressed on the amount paid x
-- (intercept + slope), calibrated to the KNOWN total paid X.
-- Residual-based standard error. Normal 95% interval.
-- Formula: shared/sql/lib/02_estimators.sql (ipm_regression).
-- =====================================================================
CREATE OR REPLACE TABLE est_regression AS
SELECT * FROM ipm_regression(getvariable('alpha'));
