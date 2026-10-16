-- =====================================================================
-- partc errors/06_checks.sql : population vs public FY 2025 aggregates
-- ---------------------------------------------------------------------
-- Source: CMS FY 2025 Medicare Part C error rate findings (see the
-- literature review). Tolerances are absolute rate points, or relative
-- (rel = true) for dollar amounts.
-- =====================================================================
CREATE OR REPLACE TABLE checks AS
WITH t AS (SELECT metric, value FROM truth WHERE level = 'overall'),
targets AS (
    SELECT * FROM (VALUES
        ('gross_rate',    0.0609,     0.0010, false, 'gross improper rate 6.09%'),
        ('overpayments',  21.43e9,    0.02,   true,  'overpayments $21.43B'),
        ('underpayments', 2.23e9,     0.02,   true,  'underpayments $2.23B'),
        ('md_rate',       0.0022,     0.0005, false, 'missing documentation 0.22% of payments'),
        ('payments',      388.72e9,   0.001,  true,  'payments subject to risk adjustment $388.72B')
    ) v(metric, target, tolerance, rel, source)
)
SELECT g.metric, t.value, g.target,
       CASE WHEN g.rel THEN t.value / g.target - 1 ELSE t.value - g.target END AS diff,
       g.tolerance, g.rel,
       CASE WHEN abs(CASE WHEN g.rel THEN t.value / g.target - 1 ELSE t.value - g.target END) <= g.tolerance
            THEN 'pass' ELSE 'FAIL' END AS status,
       g.source
FROM targets g JOIN t USING (metric)
UNION ALL
SELECT 'unique ids: population', (count(*) - count(DISTINCT unit_id))::DOUBLE, 0, (count(*) - count(DISTINCT unit_id))::DOUBLE,
       0, false, CASE WHEN count(*) = count(DISTINCT unit_id) THEN 'pass' ELSE 'FAIL' END,
       'every row has a unique id (value = number of duplicates)'
FROM population
UNION ALL
SELECT 'unique ids: hccs', (count(*) - count(DISTINCT enrollee_id || '|' || fam))::DOUBLE, 0, (count(*) - count(DISTINCT enrollee_id || '|' || fam))::DOUBLE,
       0, false, CASE WHEN count(*) = count(DISTINCT enrollee_id || '|' || fam) THEN 'pass' ELSE 'FAIL' END,
       'every row has a unique id (value = number of duplicates)'
FROM hccs;
