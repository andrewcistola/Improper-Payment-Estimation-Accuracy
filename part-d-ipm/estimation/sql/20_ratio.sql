-- =====================================================================
-- partd estimation/20_ratio.sql : ratio estimator
-- ---------------------------------------------------------------------
-- For each domain (over, under, gross, net; see 01_frame.sql), on the
-- beneficiary audit of 990 (every PDE reviewed, errors netted per beneficiary).
-- theta_hat = T_y / T_x, both from the sample; Taylor linearization
-- standard error. Normal 95% interval.
-- Formula: shared/sql/lib/02_estimators.sql (ipm_ratio).
-- =====================================================================
CREATE OR REPLACE TABLE est_ratio AS
SELECT * FROM ipm_ratio(getvariable('alpha'));
