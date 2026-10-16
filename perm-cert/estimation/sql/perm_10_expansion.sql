-- =====================================================================
-- perm estimation/perm_10_expansion.sql : expansion (Horvitz-Thompson)
-- ---------------------------------------------------------------------
-- Estimand: state improper payment rates at federal share, sum y*fmap / sum x*fmap, for the overall, eligibility and claims components.
-- theta_hat = T_y / X: weighted sum of y over the sample divided by
-- the state's KNOWN federal-share payment total X. Normal 95% interval.
-- Formula: shared/sql/lib/02_estimators.sql (ipm_expansion).
-- =====================================================================
CREATE OR REPLACE TABLE est_expansion AS
SELECT * FROM ipm_expansion(getvariable('alpha'));
