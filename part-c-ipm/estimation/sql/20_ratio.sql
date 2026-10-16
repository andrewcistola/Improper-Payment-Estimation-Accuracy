-- =====================================================================
-- partc estimation/20_ratio.sql : ratio estimator
-- ---------------------------------------------------------------------
-- theta_hat = T_y / T_x: weighted |y| over weighted payments, both from
-- the sample; Taylor linearization standard error. Normal 95% interval.
-- Formula: shared/sql/lib/02_estimators.sql (ipm_ratio).
-- =====================================================================
CREATE OR REPLACE TABLE est_ratio AS
SELECT * FROM ipm_ratio(getvariable('alpha'));
