-- =====================================================================
-- partd errors/04_apply_errors.sql : activate candidate errors at current m
-- ---------------------------------------------------------------------
-- A PDE's candidate error (step 02) is active when u_act < m x rate x
-- size_mult, with
--   rate      = ltc_error_rate for LTC claims, error_rate otherwise
--   m         = 1.0 (Part D is uncalibrated: the stated rates are the base)
--   size_mult = (gdc / mean gdc within the PDE's LTC / non-LTC group)
--               ^ size_beta
-- and the product capped at 0.95. size_beta (default 0.0) sets how error
-- incidence rises with claim size: at 0.0 the multiplier is exactly 1 for
-- every PDE and incidence is independent of GDC within LTC / non-LTC (the
-- reported population); 0.5 roughly doubles the rate of a claim four
-- times the mean size. The group mean of GDC keeps the stated rate as the
-- rate of a mean-sized claim. size_beta is read with a default so configs
-- written before it existed need no change.
-- =====================================================================
CREATE OR REPLACE TABLE pde_versions AS
WITH m AS (SELECT * FROM calib ORDER BY pass DESC LIMIT 1),
g AS (SELECT ltc, avg(gdc::DOUBLE) AS mean_gdc FROM pdes GROUP BY ltc),
a AS (
    SELECT p.*,
           p.u_act < least(0.95,
                           m.m * CASE WHEN p.ltc THEN getvariable('ltc_error_rate') ELSE getvariable('error_rate') END
                               * power(p.gdc::DOUBLE / g.mean_gdc, coalesce(getvariable('size_beta'), 0.0)::DOUBLE)) AS active
    FROM pdes p JOIN g USING (ltc), m
)
SELECT 'submitted' AS version, bene_id, pde_id, fill_day, lis, brand, gdc, active,
       CASE WHEN active THEN cand_type ELSE 'none' END AS error_type
FROM a
UNION ALL
SELECT 'corrected', bene_id, pde_id, fill_day, lis, brand,
       CASE WHEN active THEN cand_gdc ELSE gdc END, active,
       CASE WHEN active THEN cand_type ELSE 'none' END
FROM a;
