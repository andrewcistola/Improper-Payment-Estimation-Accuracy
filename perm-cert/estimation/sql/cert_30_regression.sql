-- =====================================================================
-- cert estimation/cert_30_regression.sql : regression (GREG) estimator
-- ---------------------------------------------------------------------
-- Estimands: national over, under, gross and net rates and gross by claim type, sum y / sum x (cert_01_frame.sql).
-- theta_hat = [T_y + b (X - T_x)] / X: y regressed on the amount paid x
-- (intercept + slope), calibrated to the KNOWN total paid X.
-- Residual-based standard error. Normal 95% interval.
-- Formula: shared/sql/lib/02_estimators.sql (ipm_regression).
-- =====================================================================
CREATE OR REPLACE TABLE est_regression AS
SELECT * FROM ipm_regression(getvariable('alpha'));
