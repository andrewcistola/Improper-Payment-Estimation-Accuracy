-- =====================================================================
-- partd estimation/10_expansion.sql : expansion (Horvitz-Thompson)
-- ---------------------------------------------------------------------
-- Estimand: gross improper payment rate for Part D, sum |y| / sum x over beneficiaries.
-- theta_hat = T_y / X: weighted sum of y over the sample divided by
-- the KNOWN national Part D payment total X. Normal 95% interval.
-- Formula: shared/sql/lib/02_estimators.sql (ipm_expansion).
-- =====================================================================
CREATE OR REPLACE TABLE est_expansion AS
SELECT * FROM ipm_expansion(getvariable('alpha'));
