-- =====================================================================
-- partc estimation/40_simulation.sql : simulation (bootstrap)
-- ---------------------------------------------------------------------
-- Rescaled bootstrap (Rao-Wu) of the ratio estimator within risk-score
-- strata, boot_reps replicates per sample; percentile, bootstrap-t and
-- BCa 95% intervals.
-- Formula: shared/sql/lib/02_estimators.sql (ipm_bootstrap).
-- =====================================================================
CREATE OR REPLACE TABLE est_simulation AS
SELECT * FROM ipm_bootstrap(getvariable('boot_reps'), getvariable('alpha'));
