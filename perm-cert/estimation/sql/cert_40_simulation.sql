-- =====================================================================
-- cert estimation/cert_40_simulation.sql : simulation (bootstrap)
-- ---------------------------------------------------------------------
-- Estimand: claim improper payment rate, sum y / sum x.
-- Rescaled bootstrap (Rao-Wu) of the ratio estimator (one stratum: SRS of claims),
-- boot_reps replicates per sample; percentile, bootstrap-t and BCa 95%
-- intervals.
-- Formula: shared/sql/lib/02_estimators.sql (ipm_bootstrap).
-- =====================================================================
CREATE OR REPLACE TABLE est_simulation AS
SELECT * FROM ipm_bootstrap(getvariable('boot_reps'), getvariable('alpha'));
