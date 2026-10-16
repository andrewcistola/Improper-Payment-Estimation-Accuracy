-- =====================================================================
-- perm/02_truth.sql : state and pooled truth at federal share
--   claims_rate  = sum(y_claims * fmap) / sum(x * fmap)
--   elig_rate    = sum(y_elig   * fmap) / sum(x * fmap)
--   overall_rate = sum(y        * fmap) / sum(x * fmap)
--                = claims + elig - overlap  (overlap = claims errors on
--                  payments that are also eligibility errors)
-- =====================================================================
CREATE OR REPLACE TABLE truth AS
WITH g AS (
    SELECT 'overall' AS level, NULL::VARCHAR AS key, * FROM population
    UNION ALL SELECT 'state', state_id::VARCHAR, * FROM population
    UNION ALL SELECT 'state_payment_type', state_id || '_' || payment_type, * FROM population
),
a AS (
    SELECT level, key,
           count(*)::DOUBLE AS n_payments,
           count(DISTINCT bene_id)::DOUBLE AS n_benes,
           sum(x * fmap)::DOUBLE AS fed_paid,
           sum(y_claims * fmap)::DOUBLE AS fed_claims_err,
           sum(y_elig * fmap)::DOUBLE AS fed_elig_err,
           sum(y * fmap)::DOUBLE AS fed_overall_err,
           sum(CASE WHEN y_elig > 0 THEN y_claims ELSE 0 END * fmap)::DOUBLE AS fed_overlap,
           any_value(w_pop) AS w
    FROM g GROUP BY level, key
)
SELECT level, key, metric, value FROM (
    SELECT level, key, n_payments, n_benes,
           w * fed_paid AS fed_paid_national_scale,
           fed_claims_err / fed_paid AS claims_rate,
           fed_elig_err / fed_paid AS elig_rate,
           fed_overlap / fed_paid AS overlap_rate,
           fed_overall_err / fed_paid AS overall_rate
    FROM a)
UNPIVOT (value FOR metric IN (n_payments, n_benes, fed_paid_national_scale,
                              claims_rate, elig_rate, overlap_rate, overall_rate));
