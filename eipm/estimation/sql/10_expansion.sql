-- =====================================================================
-- eipm estimation/10_expansion.sql : expansion (Horvitz-Thompson)
-- ---------------------------------------------------------------------
-- Estimand: gross APTC improper payment rate, sum |y| / sum x over applications.
-- theta_hat = T_y / X: weighted sum of y over the sample divided by
-- the KNOWN total APTC paid X. Normal 95% interval.
-- Formula: shared/sql/lib/02_estimators.sql (ipm_expansion).
-- =====================================================================
CREATE OR REPLACE TABLE est_expansion AS
SELECT * FROM ipm_expansion(getvariable('alpha'));
