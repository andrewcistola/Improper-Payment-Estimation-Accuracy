-- =====================================================================
-- cert estimation/cert_10_expansion.sql : expansion (Horvitz-Thompson)
-- ---------------------------------------------------------------------
-- Estimand: claim improper payment rate, sum y / sum x.
-- theta_hat = T_y / X: weighted sum of y over the sample divided by
-- the KNOWN total paid X. Normal 95% interval.
-- Formula: shared/sql/lib/02_estimators.sql (ipm_expansion).
-- =====================================================================
CREATE OR REPLACE TABLE est_expansion AS
SELECT * FROM ipm_expansion(getvariable('alpha'));
