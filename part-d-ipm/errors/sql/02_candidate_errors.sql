-- =====================================================================
-- partd errors/02_candidate_errors.sql : one candidate error per PDE
-- ---------------------------------------------------------------------
-- Every PDE carries a CANDIDATE error and an activation uniform u_act.
-- Step 04 activates it when u_act < m x (ltc_error_mult if LTC else 1),
-- one calibrated multiplier m (step 03), so an LTC claim is
-- ltc_error_mult (10) times as likely to be in error.
-- The error is a share of the PDE's gross drug cost (GDC):
--   e = (submitted GDC - correct GDC) / submitted GDC,  -1 <= e <= 1
--   full error     90% of errors: e = 1 (correct GDC = 0)
--   partial error  10% of errors: e uniform on [-1, 1); e < 0 is an
--                  underpayment (at e = -1 the correct GDC is double)
--   correct GDC = round(GDC x (1 - e))
-- =====================================================================

-- Step 3. Candidate error per PDE (not yet active).
CREATE OR REPLACE TABLE pdes AS
WITH t AS (
    SELECT *,
           u01(getvariable('seed'), 'etype', pde_id) AS u_type,
           -1.0 + 2.0 * u01(getvariable('seed'), 'emag', pde_id) AS e_partial,
           u01(getvariable('seed'), 'act', pde_id) AS u_act
    FROM pdes
),
k AS (
    SELECT *,
           CASE WHEN u_type < getvariable('full_error_share') THEN 'full_error' ELSE 'partial_error' END AS cand_type
    FROM t
)
SELECT *,
       CASE WHEN cand_type = 'full_error' THEN 1.0 ELSE e_partial END AS cand_e,
       CASE WHEN cand_type = 'full_error' OR e_partial >= 0 THEN 'over' ELSE 'under' END AS cand_dir,
       usd(gdc * (1 - CASE WHEN cand_type = 'full_error' THEN 1.0 ELSE e_partial END)) AS cand_gdc
FROM k;
