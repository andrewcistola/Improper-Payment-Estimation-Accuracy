-- =====================================================================
-- partd estimation/30_regression.sql : regression (GREG) estimator
-- ---------------------------------------------------------------------
-- For each domain (over, under, gross, net; see 01_frame.sql), on the
-- beneficiary audit of 990 (every PDE reviewed, errors netted per beneficiary).
-- theta_hat = [T_y + b (X - T_x)] / X: y regressed on the amount paid x
-- (intercept + slope), calibrated to the KNOWN national Part D payment total X.
-- Residual-based standard error. Normal 95% interval.
-- Formula: shared/sql/lib/02_estimators.sql (ipm_regression).
-- =====================================================================
CREATE OR REPLACE TABLE est_regression AS
SELECT * FROM ipm_regression(getvariable('alpha'));
