-- =====================================================================
-- perm estimation/perm_40_simulation.sql : simulation (bootstrap)
-- ---------------------------------------------------------------------
-- Estimand: state improper payment rates at federal share, sum y*fmap / sum x*fmap, for the overall, eligibility and claims components.
-- Rescaled bootstrap (Rao-Wu) of the ratio estimator within the state x quarter x payment-type x payment-size strata (systematic selection treated as stratified SRS),
-- boot_reps replicates per sample; percentile, bootstrap-t and BCa 95%
-- intervals.
-- Formula: shared/sql/lib/02_estimators.sql (ipm_bootstrap).
-- =====================================================================
CREATE OR REPLACE TABLE est_simulation AS
SELECT * FROM ipm_bootstrap(getvariable('boot_reps'), getvariable('alpha'));
