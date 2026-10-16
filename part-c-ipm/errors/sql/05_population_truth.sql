-- =====================================================================
-- partc errors/05_population_truth.sql : Part C IPM population and truth
-- ---------------------------------------------------------------------
-- Strata: national terciles of the original risk score (low / medium /
-- high), the historically documented Part C IPM stratification.
-- Dollar truths are weighted by w_pop (scaled population) so they are
-- on the national scale; rates are unaffected by the constant weight.
-- =====================================================================

CREATE OR REPLACE TABLE population AS
SELECT unit_id, contract_id,
       CASE ntile(3) OVER (ORDER BY risk_orig, unit_id)
            WHEN 1 THEN 'low' WHEN 2 THEN 'medium' ELSE 'high' END AS stratum,
       months, county_rate, demo_score, n_hcc, risk_orig, risk_validated, delta_r,
       x, y, error_type, w_pop,
       missing_doc, add_fam, add_coef   -- enrollee-level audit findings (HCC-level: hcc_detail)
FROM capitation_units;

CREATE OR REPLACE TABLE truth AS
WITH g AS (
    SELECT 'overall' AS level, NULL::VARCHAR AS key, * FROM population
    UNION ALL
    SELECT 'stratum', stratum, * FROM population
),
a AS (
    SELECT level, key,
           count(*)::DOUBLE AS n_units,
           any_value(w_pop) * sum(x)::DOUBLE AS payments,
           any_value(w_pop) * sum(y) FILTER (WHERE y > 0)::DOUBLE AS overpayments,
           any_value(w_pop) * -sum(y) FILTER (WHERE y < 0)::DOUBLE AS underpayments,
           any_value(w_pop) * sum(y) FILTER (WHERE error_type = 'missing_documentation')::DOUBLE AS md_dollars,
           any_value(w_pop) * sum(y) FILTER (WHERE error_type IN ('unsupported_hcc', 'hierarchy_move'))::DOUBLE
               AS unsupported_dollars,
           avg((y <> 0)::INT)::DOUBLE AS unit_err_rate
    FROM g GROUP BY level, key
),
r AS (
    SELECT level, key, n_units, payments, overpayments, underpayments, unit_err_rate,
           (overpayments + underpayments) / payments AS gross_rate,
           (overpayments - underpayments) / payments AS net_rate,
           coalesce(md_dollars, 0) / payments AS md_rate,
           coalesce(unsupported_dollars, 0) / payments AS unsupported_rate,
           underpayments / payments AS under_rate
    FROM a
)
SELECT level, key, metric, value FROM r
UNPIVOT (value FOR metric IN (n_units, payments, overpayments, underpayments, unit_err_rate,
                              gross_rate, net_rate, md_rate, unsupported_rate, under_rate))
UNION ALL
SELECT 'calibration', 'multipliers', metric, value FROM multipliers
UNPIVOT (value FOR metric IN (m_unsup, m_md, m_add));
