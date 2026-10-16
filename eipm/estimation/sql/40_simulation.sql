-- =====================================================================
-- eipm estimation/40_simulation.sql : simulation (bootstrap)
-- ---------------------------------------------------------------------
-- Estimand: gross APTC improper payment rate, sum |y| / sum x over applications.
-- Rescaled bootstrap (Rao-Wu) of the ratio estimator within income-band strata,
-- boot_reps replicates per sample; percentile, bootstrap-t and BCa 95%
-- intervals.
-- Formula: shared/sql/lib/02_estimators.sql (ipm_bootstrap).
-- =====================================================================
CREATE OR REPLACE TABLE est_simulation AS
SELECT * FROM ipm_bootstrap(getvariable('boot_reps'), getvariable('alpha'));
