-- =====================================================================
-- partd/03_apply_errors.sql : activate candidate errors at current m
-- =====================================================================
CREATE OR REPLACE TABLE pde_versions AS
WITH m AS (SELECT * FROM calib ORDER BY pass DESC LIMIT 1),
a AS (
    SELECT p.*,
           p.u_act < least(0.95, m.m) AS active   -- type already drawn with the published shares
    FROM pdes p, m
)
SELECT 'submitted' AS version, bene_id, pde_id, fill_day, lis, brand, gdc, active,
       CASE WHEN active THEN cand_type ELSE 'none' END AS error_type
FROM a
UNION ALL
SELECT 'corrected', bene_id, pde_id, fill_day, lis, brand,
       CASE WHEN active THEN cand_gdc ELSE gdc END, active,
       CASE WHEN active THEN cand_type ELSE 'none' END
FROM a;
