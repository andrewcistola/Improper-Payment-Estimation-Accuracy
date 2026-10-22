-- =====================================================================
-- perm errors/05_checks.sql : population checks
-- ---------------------------------------------------------------------
-- (1) Pooled overall rate vs the FY 2025 Medicaid rate (6.12%). This is
--     a sanity check: the real national rate rolls three state cycles.
-- (2) Each state's true eligibility rate is at or below its configured
--     grid value and within 0.02 points of it.
-- =====================================================================
CREATE OR REPLACE TABLE checks AS
SELECT 'pooled overall_rate' AS metric, value, 0.0612 AS target, value - 0.0612 AS diff,
       0.0030 AS tolerance, false AS rel,
       CASE WHEN abs(value - 0.0612) <= 0.0030 THEN 'pass' ELSE 'FAIL' END AS status,
       'Medicaid FY 2025 6.12% (pooled sanity check)' AS source
FROM truth WHERE level = 'overall' AND metric = 'overall_rate'
UNION ALL
SELECT 'state ' || s.state_id || ' elig_rate', t.value, s.elig_rate::DOUBLE, t.value - s.elig_rate::DOUBLE,
       0.0002, false,
       CASE WHEN t.value <= s.elig_rate::DOUBLE + 1e-12 AND s.elig_rate::DOUBLE - t.value < 0.0002
            THEN 'pass' ELSE 'FAIL' END,
       'grid value; never above, within 0.02 pt'
FROM states s JOIN truth t ON t.level = 'state' AND t.key = s.state_id::VARCHAR AND t.metric = 'elig_rate'
UNION ALL
SELECT 'unique ids: population', (count(*) - count(DISTINCT unit_id))::DOUBLE, 0, (count(*) - count(DISTINCT unit_id))::DOUBLE,
       0, false, CASE WHEN count(*) = count(DISTINCT unit_id) THEN 'pass' ELSE 'FAIL' END,
       'every row has a unique id (value = number of duplicates)'
FROM population;
