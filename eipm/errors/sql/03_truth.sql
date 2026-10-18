-- =====================================================================
-- eipm errors/03_truth.sql : true totals and rates (national scale)
-- ---------------------------------------------------------------------
-- Every error is an overpayment: gross = overpayments = net, and
-- underpayments are zero (kept as a metric so the check can show it).
-- =====================================================================
CREATE OR REPLACE TABLE truth AS
WITH g AS (
    SELECT 'overall' AS level, NULL::VARCHAR AS key, * FROM population
    UNION ALL SELECT 'stratum', stratum, * FROM population
),
a AS (
    SELECT level, key, count(*)::DOUBLE AS n_units,
           any_value(w_pop) * sum(x)::DOUBLE AS payments,
           any_value(w_pop) * coalesce(sum(y) FILTER (WHERE y > 0), 0)::DOUBLE AS overpayments,
           any_value(w_pop) * coalesce(-sum(y) FILTER (WHERE y < 0), 0)::DOUBLE AS underpayments,
           any_value(w_pop) * sum(y_technical)::DOUBLE AS technical,
           any_value(w_pop) * sum(y_monetary)::DOUBLE AS monetary,
           avg((y <> 0)::INT)::DOUBLE AS unit_err_rate,
           avg((error_type = 'technical')::INT)::DOUBLE AS unit_technical_rate
    FROM g GROUP BY level, key
)
SELECT level, key, metric, value FROM (
    SELECT *, (overpayments + underpayments) / payments AS gross_rate,
           technical / payments AS technical_rate, monetary / payments AS monetary_rate FROM a)
UNPIVOT (value FOR metric IN (n_units, payments, overpayments, underpayments, technical, monetary,
                              unit_err_rate, unit_technical_rate, gross_rate, technical_rate, monetary_rate))
UNION ALL SELECT 'calibration', 'rate', 'p_technical', p_t FROM calib
UNION ALL SELECT 'calibration', 'rate', 'p_monetary', p_m FROM calib;
