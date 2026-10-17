-- =====================================================================
-- partd errors/04_apply_errors.sql : activate candidate errors at current m
-- =====================================================================
CREATE OR REPLACE TABLE pde_versions AS
WITH m AS (SELECT * FROM calib ORDER BY pass DESC LIMIT 1),
a AS (
    SELECT p.*,
           p.u_act < least(0.95, m.m * CASE WHEN p.ltc THEN getvariable('ltc_error_mult') ELSE 1 END) AS active
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
