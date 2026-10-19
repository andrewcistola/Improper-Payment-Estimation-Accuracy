-- =====================================================================
-- partd estimation/30_regression.sql : regression estimator inputs
-- ---------------------------------------------------------------------
-- Regression (model-assisted): on the same audit as the ratio estimator,
-- improper dollars are regressed, within each model stratum, on an
-- intercept and basic beneficiary variables plus the amount paid; the
-- fitted models predict every population unit and the audit residuals
-- correct the total. Interval from the audit's residuals (one audit).
-- Fitting, prediction and the interval: shared/ipsim/regression.py.
-- Unit: beneficiary (beneficiary audit of 990, simple random sample).
-- Model strata = post-strata: LTC; LIS (not LTC); other. Predictors:
-- Medicare payment x, gross drug cost, number of PDEs, reached the
-- catastrophic phase (0/1).
-- Output: reg_population(unit_id, stratum, model_stratum, <predictors>)
-- =====================================================================
CREATE OR REPLACE TABLE reg_population AS
SELECT unit_id, stratum, CASE WHEN ltc THEN 'ltc' WHEN lis THEN 'lis' ELSE 'other' END AS model_stratum,
       x, gdc_sub, n_pde, reached_catastrophic::INT AS catastrophic
FROM read_parquet(getvariable('repo_root') || '/' || getvariable('population_dir') || '/population.parquet');
