-- =====================================================================
-- eipm errors/03_truth.sql : true totals and rates (national scale)
-- =====================================================================
CREATE OR REPLACE TABLE truth AS
WITH g AS (
    SELECT 'overall' AS level, NULL::VARCHAR AS key, * FROM population
    UNION ALL SELECT 'stratum', stratum, * FROM population
),
a AS (
    SELECT level, key, count(*)::DOUBLE AS n_units,
           any_value(w_pop) * sum(x)::DOUBLE AS payments,
           any_value(w_pop) * sum(y) FILTER (WHERE y > 0)::DOUBLE AS overpayments,
           any_value(w_pop) * -sum(y) FILTER (WHERE y < 0)::DOUBLE AS underpayments,
           avg((y <> 0)::INT)::DOUBLE AS unit_err_rate
    FROM g GROUP BY level, key
)
SELECT level, key, metric, value FROM (
    SELECT *, (coalesce(overpayments, 0) + coalesce(underpayments, 0)) / payments AS gross_rate FROM a)
UNPIVOT (value FOR metric IN (n_units, payments, overpayments, underpayments, unit_err_rate, gross_rate))
UNION ALL SELECT 'calibration', 'multiplier', 'm', m FROM calib;
