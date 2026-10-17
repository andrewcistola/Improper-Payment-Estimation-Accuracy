-- =====================================================================
-- partc estimation/20_ratio.sql : ratio estimator
-- ---------------------------------------------------------------------
-- For each domain (over, under, gross, net; see 01_frame.sql):
--   theta_hat = T_y / T_x: weighted dollars in error of the audited
--   enrollees (their own county rate and months) over their weighted
--   payments. As improper dollars, theta_hat x X; divided by the known
--   total payments X this is theta_hat again. Taylor linearization
--   standard error, normal 95% interval. Gross and net are linear in the
--   enrollee values, so they equal over + under and over - under.
-- Formula: shared/sql/lib/02_estimators.sql (ipm_ratio).
-- =====================================================================
CREATE OR REPLACE TABLE est_ratio AS
SELECT * FROM ipm_ratio(getvariable('alpha'));
