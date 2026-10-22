-- =====================================================================
-- cert errors/03_truth.sql : true totals and rates (national scale)
-- ---------------------------------------------------------------------
-- Each claim is its own unit, so over/under are netted per claim (one
-- error per claim): over = sum of positive y, under = sum of -y where
-- negative, gross = over + under, net = over - under.
-- =====================================================================
CREATE OR REPLACE TABLE truth AS
WITH g AS (
    SELECT 'overall' AS level, NULL::VARCHAR AS key, * FROM population
    UNION ALL SELECT 'claim_type', claim_type, * FROM population
    UNION ALL SELECT 'stratum', stratum, * FROM population
),
a AS (
    SELECT level, key, count(*)::DOUBLE AS n_units,
           any_value(w_pop) * sum(x)::DOUBLE AS payments,
           any_value(w_pop) * coalesce(sum(y) FILTER (WHERE y > 0), 0)::DOUBLE AS overpayments,
           any_value(w_pop) * coalesce(-sum(y) FILTER (WHERE y < 0), 0)::DOUBLE AS underpayments,
           avg((y <> 0)::INT)::DOUBLE AS unit_err_rate
    FROM g GROUP BY level, key
)
SELECT level, key, metric, value FROM (
    SELECT *, overpayments / payments AS over_rate, underpayments / payments AS under_rate,
           (overpayments + underpayments) / payments AS gross_rate,
           (overpayments - underpayments) / payments AS net_rate FROM a)
UNPIVOT (value FOR metric IN (n_units, payments, overpayments, underpayments, unit_err_rate,
                              over_rate, under_rate, gross_rate, net_rate))
UNION ALL
SELECT 'calibration', claim_type, metric, value FROM calib UNPIVOT (value FOR metric IN (p_full, p_po, p_u));
