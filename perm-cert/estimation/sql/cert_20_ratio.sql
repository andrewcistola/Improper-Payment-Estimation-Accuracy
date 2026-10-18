-- =====================================================================
-- cert estimation/cert_20_ratio.sql : ratio estimator
-- ---------------------------------------------------------------------
-- Estimands: national over, under, gross and net rates and gross by claim type, sum y / sum x (cert_01_frame.sql).
-- theta_hat = T_y / T_x, both from the sample; Taylor linearization
-- standard error. Normal 95% interval.
-- Formula: shared/sql/lib/02_estimators.sql (ipm_ratio).
-- =====================================================================
CREATE OR REPLACE TABLE est_ratio AS
SELECT * FROM ipm_ratio(getvariable('alpha'));
