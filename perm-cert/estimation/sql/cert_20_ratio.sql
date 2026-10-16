-- =====================================================================
-- cert estimation/cert_20_ratio.sql : ratio estimator
-- ---------------------------------------------------------------------
-- Estimand: claim improper payment rate, sum y / sum x.
-- theta_hat = T_y / T_x, both from the sample; Taylor linearization
-- standard error. Normal 95% interval.
-- Formula: shared/sql/lib/02_estimators.sql (ipm_ratio).
-- =====================================================================
CREATE OR REPLACE TABLE est_ratio AS
SELECT * FROM ipm_ratio(getvariable('alpha'));
