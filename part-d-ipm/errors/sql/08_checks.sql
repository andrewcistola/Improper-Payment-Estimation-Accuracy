-- =====================================================================
-- partd errors/08_checks.sql : population vs public FY 2025 aggregates
-- ---------------------------------------------------------------------
-- The stated error rates (10% LTC, 2.5% other) and the 90/10 full/partial
-- split are checked. Gross, over and under dollars are outcomes of those
-- rates and are only REPORTED against CMS FY 2025 Part D figures.
-- =====================================================================
CREATE OR REPLACE TABLE checks AS
WITH t AS (
    SELECT metric, value FROM truth WHERE level = 'overall'
    UNION ALL
    SELECT 'share_' || metric, value FROM truth WHERE level = 'error_type_share'
),
targets AS (
    SELECT * FROM (VALUES
        ('gross_rate',                  0.0400,    NULL,   false, 'FY 2025 gross rate 4.00% (reported, not a target)'),
        ('overpayments',                3.70e9,    NULL,   true,  'FY 2025 overpayments $3.70B (reported, not a target)'),
        ('underpayments',               0.52e9,    NULL,   true,  'FY 2025 underpayments $0.52B (reported, not a target)'),
        ('claim_err_rate_ltc',          0.10,      0.005,  false, 'LTC claims in error: 10%'),
        ('claim_err_rate_other',        0.025,     0.001,  false, 'other claims in error: 2.5%'),
        ('payments',                    105.56e9,  0.001,  true,  'Part D payments $105.56B'),
        ('share_full_error',            0.9000,    0.01,   false, '90% of errors are full (100% of GDC)'),
        ('share_partial_error',         0.1000,    0.01,   false, '10% of errors are partial')
    ) v(metric, target, tolerance, rel, source)
)
SELECT g.metric, t.value, g.target,
       CASE WHEN g.rel THEN t.value / g.target - 1 ELSE t.value - g.target END AS diff,
       g.tolerance, g.rel,
       CASE WHEN g.tolerance IS NULL THEN 'reported'
            WHEN abs(CASE WHEN g.rel THEN t.value / g.target - 1 ELSE t.value - g.target END) <= g.tolerance
            THEN 'pass' ELSE 'FAIL' END AS status,
       g.source
FROM targets g JOIN t USING (metric)
UNION ALL
SELECT 'unique ids: population', (count(*) - count(DISTINCT unit_id))::DOUBLE, 0, (count(*) - count(DISTINCT unit_id))::DOUBLE,
       0, false, CASE WHEN count(*) = count(DISTINCT unit_id) THEN 'pass' ELSE 'FAIL' END,
       'every row has a unique id (value = number of duplicates)'
FROM population
UNION ALL
SELECT 'unique ids: pde_detail', (count(*) - count(DISTINCT pde_id))::DOUBLE, 0, (count(*) - count(DISTINCT pde_id))::DOUBLE,
       0, false, CASE WHEN count(*) = count(DISTINCT pde_id) THEN 'pass' ELSE 'FAIL' END,
       'every row has a unique id (value = number of duplicates)'
FROM pde_detail;
