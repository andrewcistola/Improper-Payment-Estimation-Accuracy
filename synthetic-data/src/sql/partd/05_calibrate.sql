-- =====================================================================
-- partd/05_calibrate.sql : next calibration pass (see 02 header)
-- Target is national gross dollars; divided by w_pop for the scaled
-- population. Beneficiary-level payment error
--   y = Medicare(submitted) - Medicare(corrected);  gross = sum |y|.
-- =====================================================================
CREATE OR REPLACE TABLE calib AS
WITH last AS (SELECT * FROM calib ORDER BY pass DESC LIMIT 1),
realized AS (SELECT sum(abs(medicare_pde_sub - medicare_pde_cor))::DOUBLE AS gross FROM bene_pay),
linear AS (  -- expected gross dollars at m = 1
    SELECT sum((abs(p.gdc - p.cand_gdc) * (b.reinsurance + b.lics) / b.gdc)::DECIMAL(38, 6))::DOUBLE AS e
    FROM pdes p JOIN pde_benefit b ON b.pde_id = p.pde_id AND b.version = 'submitted'
    WHERE p.gdc > 0
),
tgt AS (SELECT (getvariable('target_over') + getvariable('target_under')) / getvariable('w_pop') AS t)
SELECT pass, m, CASE WHEN pass = last_pass THEN realized_gross_now ELSE realized_gross END AS realized_gross
FROM (SELECT c.*, last.pass AS last_pass, realized.gross AS realized_gross_now FROM calib c, last, realized)
UNION ALL
SELECT last.pass + 1,
       round(CASE WHEN last.pass = 0 THEN tgt.t / linear.e
                  ELSE last.m * tgt.t / realized.gross END, 8),
       NULL
FROM last, realized, linear, tgt;
