-- =====================================================================
-- cert estimation/30_regression.sql : regression estimator inputs
-- ---------------------------------------------------------------------
-- Regression (model-assisted): on the same audit as the ratio estimator,
-- improper dollars are regressed, within each model stratum, on an
-- intercept and basic beneficiary variables plus the amount paid; the
-- fitted models predict every population unit and the audit residuals
-- correct the total. Interval from the audit's residuals (one audit).
-- Fitting, prediction and the interval: shared/ipsim/regression.py.
-- Unit: claim (37,651). Model strata = design strata (claim type x payment
-- quintile). Predictor: amount paid x (the claims carry no beneficiary
-- variables).
-- Output: reg_population(unit_id, stratum, model_stratum, <predictors>)
-- =====================================================================
CREATE OR REPLACE TABLE reg_population AS
SELECT unit_id, stratum, stratum AS model_stratum, x
FROM cert_frame;
