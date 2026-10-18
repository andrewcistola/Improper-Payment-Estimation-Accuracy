-- =====================================================================
-- eipm errors/04_checks.sql : population vs public FY 2025 aggregates
-- ---------------------------------------------------------------------
-- Source: CMS FY 2025 EIPM result: 0.89% ($657.46M of $73.81B), of which
-- technically improper 0.43 points ($282.44M); no underpayments.
-- =====================================================================
CREATE OR REPLACE TABLE checks AS
WITH t AS (SELECT metric, value FROM truth WHERE level = 'overall')
SELECT 'gross_rate' AS metric, value, 0.0089 AS target, value - 0.0089 AS diff, 0.0010 AS tolerance,
       false AS rel, CASE WHEN abs(value - 0.0089) <= 0.0010 THEN 'pass' ELSE 'FAIL' END AS status,
       'EIPM gross improper rate 0.89% (FY 2025)' AS source
FROM t WHERE metric = 'gross_rate'
UNION ALL
SELECT 'technical_rate', value, 0.0043, value - 0.0043, 0.0010, false,
       CASE WHEN abs(value - 0.0043) <= 0.0010 THEN 'pass' ELSE 'FAIL' END,
       'technically improper 0.43 points (FY 2025, $282.44M)'
FROM t WHERE metric = 'technical_rate'
UNION ALL
SELECT 'underpayments', value, 0, value, 0, false, CASE WHEN value = 0 THEN 'pass' ELSE 'FAIL' END,
       'no underpayments (FY 2023-2025)'
FROM t WHERE metric = 'underpayments'
UNION ALL
SELECT 'unique ids: population', (count(*) - count(DISTINCT unit_id))::DOUBLE, 0, (count(*) - count(DISTINCT unit_id))::DOUBLE,
       0, false, CASE WHEN count(*) = count(DISTINCT unit_id) THEN 'pass' ELSE 'FAIL' END,
       'every row has a unique id (value = number of duplicates)'
FROM population;
