-- =====================================================================
-- radv/05_frame_truth.sql : RADV contract frames, sample sizes, truth
-- ---------------------------------------------------------------------
-- PY 2021 method (public description):
--   eligible  : enrollees with >= 1 payment HCC
--   frame     : top quartile of eligible enrollees by the prediction
--               model score (ml_scores), within contract; frames < 30
--               are not audited
--   n         : 200 for the 10 largest frames; otherwise 100 / 50 / 35
--               by thirds of frame size; capped at the frame size
--   estimator : month-weighted mean Delta-R  x  sum of county rate*months
--   gate      : extrapolate if the one-sided 90% lower bound
--               (t with n-1 df, FPC) is above zero
-- Truth columns per contract (level = 'contract'):
--   theta_prod   = (sum dR*m / sum m) * sum(rate*m)   [production estimand]
--   frame_over   = sum dR*rate*m over the frame       [actual frame dollars]
--   mean_dr_m    = month-weighted mean Delta-R in the frame
-- The two can differ when Delta-R correlates with county rate; that gap
-- is itself a study quantity.
-- =====================================================================

CREATE OR REPLACE TABLE population AS
WITH s AS (
    SELECT u.*, m.pred_score,
           u.n_hcc > 0 AS eligible,
           count(*) FILTER (WHERE u.n_hcc > 0) OVER (PARTITION BY u.contract_id) AS n_eligible,
           CASE WHEN u.n_hcc > 0 THEN
               row_number() OVER (PARTITION BY u.contract_id, u.n_hcc > 0
                                  ORDER BY m.pred_score DESC, u.unit_id) END AS score_rank
    FROM capitation_units u JOIN ml_scores m USING (unit_id)
)
SELECT unit_id, contract_id, contract_id::VARCHAR AS stratum,
       months, county_rate, demo_score, n_hcc, risk_orig, risk_radv, delta_r,
       x, y, error_type, pred_score, eligible,
       coalesce(score_rank <= ceil(0.25 * n_eligible), false) AS in_frame,
       w_pop
FROM s;

CREATE OR REPLACE TABLE frames AS
WITH f AS (
    SELECT contract_id, count(*) AS frame_n
    FROM population WHERE in_frame GROUP BY contract_id
),
audited AS (
    SELECT *,
           row_number() OVER (ORDER BY frame_n DESC, contract_id) AS size_rank
    FROM f WHERE frame_n >= 30
),
thirds AS (
    SELECT *, ntile(3) OVER (ORDER BY frame_n DESC, contract_id) AS third
    FROM audited WHERE size_rank > 10
)
SELECT a.contract_id, a.frame_n,
       least(a.frame_n, CASE WHEN a.size_rank <= 10 THEN 200
                             WHEN t.third = 1 THEN 100
                             WHEN t.third = 2 THEN 50
                             ELSE 35 END) AS sample_n
FROM audited a LEFT JOIN thirds t USING (contract_id);

CREATE OR REPLACE TABLE truth AS
WITH c AS (
    SELECT p.contract_id::VARCHAR AS key,
           count(*)::DOUBLE AS frame_n,
           any_value(f.sample_n)::DOUBLE AS sample_n,
           sum(p.months)::DOUBLE AS frame_months,
           sum(p.delta_r * p.months)::DOUBLE / sum(p.months) AS mean_dr_m,
           sum(p.county_rate * p.months)::DOUBLE AS sum_rate_months,
           sum(p.y)::DOUBLE AS frame_over,
           sum(p.x)::DOUBLE AS frame_payments,
           avg((p.y <> 0)::INT)::DOUBLE AS frame_unit_err_rate
    FROM population p JOIN frames f USING (contract_id)
    WHERE p.in_frame GROUP BY p.contract_id
),
w AS (  -- whole-contract quantities (beyond the frame; not estimable from it)
    SELECT contract_id::VARCHAR AS key, count(*)::DOUBLE AS enrollment,
           sum(y)::DOUBLE AS contract_over, sum(x)::DOUBLE AS contract_payments
    FROM population GROUP BY contract_id
),
r AS (
    SELECT c.*, c.mean_dr_m * c.sum_rate_months AS theta_prod,
           greatest(0, c.mean_dr_m * c.sum_rate_months) AS recoverable,
           w.enrollment, w.contract_over, w.contract_payments
    FROM c JOIN w USING (key)
)
SELECT 'contract' AS level, key, metric, value FROM r
UNPIVOT (value FOR metric IN (frame_n, sample_n, frame_months, mean_dr_m, sum_rate_months,
                              frame_over, frame_payments, frame_unit_err_rate, theta_prod,
                              recoverable, enrollment, contract_over, contract_payments))
UNION ALL
SELECT 'overall', NULL, 'n_contracts_audited', count(*)::DOUBLE FROM frames
UNION ALL
SELECT 'overall', NULL, 'frame_unit_err_rate',
       avg((y <> 0)::INT)::DOUBLE FROM population WHERE in_frame
UNION ALL
SELECT 'overall', NULL, 'nonframe_unit_err_rate',
       avg((y <> 0)::INT)::DOUBLE FROM population WHERE NOT in_frame AND eligible
UNION ALL
SELECT 'overall', NULL, 'model_auc_current_year', getvariable('ml_auc')::DOUBLE;
