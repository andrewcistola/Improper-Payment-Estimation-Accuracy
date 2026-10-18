-- =====================================================================
-- eipm estimation/20_ratio.sql : ratio estimator
-- ---------------------------------------------------------------------
-- Estimands: gross, technical and monetary APTC improper payment rates, sum y / sum x (01_frame.sql).
-- theta_hat = T_y / T_x, both from the sample; Taylor linearization
-- standard error. Normal 95% interval.
-- Formula: shared/sql/lib/02_estimators.sql (ipm_ratio).
-- =====================================================================
CREATE OR REPLACE TABLE est_ratio AS
SELECT * FROM ipm_ratio(getvariable('alpha'));
