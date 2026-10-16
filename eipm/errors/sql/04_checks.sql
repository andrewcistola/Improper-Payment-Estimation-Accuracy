-- =====================================================================
-- eipm errors/04_checks.sql : population vs public FY 2025 aggregate
-- ---------------------------------------------------------------------
-- Source: CMS FY 2025 EIPM result (0.89%, $657.46M).
-- =====================================================================
CREATE OR REPLACE TABLE checks AS
SELECT 'gross_rate' AS metric, value, 0.0089 AS target, value - 0.0089 AS diff, 0.0010 AS tolerance,
       false AS rel, CASE WHEN abs(value - 0.0089) <= 0.0010 THEN 'pass' ELSE 'FAIL' END AS status,
       'EIPM gross improper rate 0.89%' AS source
FROM truth WHERE level = 'overall' AND metric = 'gross_rate'
UNION ALL
SELECT 'unique ids: population', (count(*) - count(DISTINCT unit_id))::DOUBLE, 0, (count(*) - count(DISTINCT unit_id))::DOUBLE,
       0, false, CASE WHEN count(*) = count(DISTINCT unit_id) THEN 'pass' ELSE 'FAIL' END,
       'every row has a unique id (value = number of duplicates)'
FROM population;
