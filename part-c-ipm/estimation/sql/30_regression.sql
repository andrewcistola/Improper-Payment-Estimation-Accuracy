-- =====================================================================
-- partc estimation/30_regression.sql : regression (GREG) estimator
-- ---------------------------------------------------------------------
-- For each domain (over, under, gross, net; see 01_frame.sql): the
-- enrollee value regressed on enrollee payment x (intercept + slope,
-- design-weighted). With an intercept, the GREG total
--   T_y + b (X - T_x)
-- equals the sum of the model's predicted values over every enrollee in
-- the population; divided by the known total payments X. The fit is
-- linear in the enrollee values, so gross and net equal the sums and
-- differences of the over and under predictions. Residual-based standard
-- error, normal 95% interval.
-- Formula: shared/sql/lib/02_estimators.sql (ipm_regression).
-- =====================================================================
CREATE OR REPLACE TABLE est_regression AS
SELECT * FROM ipm_regression(getvariable('alpha'));
