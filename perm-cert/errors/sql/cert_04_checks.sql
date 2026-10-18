-- =====================================================================
-- cert errors/cert_04_checks.sql : population vs public FY 2025 aggregates
-- ---------------------------------------------------------------------
-- Source: CMS 2025 Medicare FFS Supplemental Improper Payment Data,
-- Tables A1 and A4 (adjusted): total $439.9B paid, 6.55% gross
-- ($28.8B), overpayments $27.9B, underpayments $1.0B; gross rates by
-- claim type from config. Rates within 0.3 points; total payments within
-- 0.1%.
-- =====================================================================
CREATE OR REPLACE TABLE checks AS
WITH t AS (SELECT key, metric, value FROM truth WHERE level IN ('overall', 'claim_type'))
SELECT 'gross_rate: overall' AS metric, value, 0.0655 AS target, value - 0.0655 AS diff, 0.003 AS tolerance,
       false AS rel, CASE WHEN abs(value - 0.0655) <= 0.003 THEN 'pass' ELSE 'FAIL' END AS status,
       'CERT FY 2025 gross improper rate 6.55%' AS source
FROM t WHERE key IS NULL AND metric = 'gross_rate'
UNION ALL
SELECT 'underpayments: overall ($B)', value / 1e9, 1.0, value / 1e9 - 1.0, 0.2, false,
       CASE WHEN abs(value / 1e9 - 1.0) <= 0.2 THEN 'pass' ELSE 'FAIL' END,
       'CERT FY 2025 underpayments $1.0B (rounded by claim type)'
FROM t WHERE key IS NULL AND metric = 'underpayments'
UNION ALL
SELECT 'payments: overall ($B)', value / 1e9, 439.9, value / 1e9 - 439.9, 0.44, false,
       CASE WHEN abs(value / 1e9 - 439.9) <= 0.44 THEN 'pass' ELSE 'FAIL' END,
       'CERT FY 2025 total payments $439.9B'
FROM t WHERE key IS NULL AND metric = 'payments'
UNION ALL
SELECT 'gross_rate: ' || c.claim_type, t.value, c.gross / c.paid, t.value - c.gross / c.paid, 0.003, false,
       CASE WHEN abs(t.value - c.gross / c.paid) <= 0.003 THEN 'pass' ELSE 'FAIL' END,
       'CERT FY 2025 gross rate by claim type'
FROM t JOIN claim_types c ON t.key = c.claim_type WHERE t.metric = 'gross_rate'
UNION ALL
SELECT 'unique ids: population', (count(*) - count(DISTINCT unit_id))::DOUBLE, 0, (count(*) - count(DISTINCT unit_id))::DOUBLE,
       0, false, CASE WHEN count(*) = count(DISTINCT unit_id) THEN 'pass' ELSE 'FAIL' END,
       'every row has a unique id (value = number of duplicates)'
FROM population;
