-- =====================================================================
-- perm estimation/perm_30_regression.sql : regression (GREG) estimator
-- ---------------------------------------------------------------------
-- Estimand: state improper payment rates at federal share, sum y*fmap / sum x*fmap, for the overall, eligibility and claims components.
-- theta_hat = [T_y + b (X - T_x)] / X: y regressed on the amount paid x
-- (intercept + slope), calibrated to the state's KNOWN federal-share payment total X.
-- Residual-based standard error. Normal 95% interval.
-- Formula: shared/sql/lib/02_estimators.sql (ipm_regression).
-- =====================================================================
CREATE OR REPLACE TABLE est_regression AS
SELECT * FROM ipm_regression(getvariable('alpha'));
