-- =====================================================================
-- cert estimation/cert_10_expansion.sql : expansion (Horvitz-Thompson)
-- ---------------------------------------------------------------------
-- Estimands: national over, under, gross and net rates and gross by claim type, sum y / sum x (cert_01_frame.sql).
-- theta_hat = T_y / X: weighted sum of y over the sample divided by
-- the KNOWN total paid X. Normal 95% interval.
-- Formula: shared/sql/lib/02_estimators.sql (ipm_expansion).
-- =====================================================================
CREATE OR REPLACE TABLE est_expansion AS
SELECT * FROM ipm_expansion(getvariable('alpha'));
