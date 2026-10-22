-- =====================================================================
-- perm estimation/30_regression.sql : regression estimator inputs
-- ---------------------------------------------------------------------
-- Regression (model-assisted): on the same audit as the ratio estimator,
-- improper dollars are regressed, within each model stratum, on an
-- intercept and basic beneficiary variables plus the amount paid; the
-- fitted models predict every population unit and the audit residuals
-- correct the total. Interval from the audit's residuals (one audit).
-- Fitting, prediction and the interval: shared/ipsim/regression.py.
-- Unit: payment (520 per state). Model strata = design strata (payment
-- type x payment quintile). Predictors: amount paid x, month of service,
-- the beneficiary's number of payments and total paid in the year.
-- Output: reg_population(unit_id, stratum, model_stratum, <predictors>)
-- =====================================================================
CREATE OR REPLACE TABLE reg_population AS
SELECT unit_id, stratum, stratum AS model_stratum, x, month,
       count(*) OVER (PARTITION BY bene_id) AS bene_n_pay,
       sum(x) OVER (PARTITION BY bene_id) AS bene_paid
FROM perm_frame;
