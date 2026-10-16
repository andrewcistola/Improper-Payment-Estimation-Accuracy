-- =====================================================================
-- partd errors/02_candidate_errors.sql : one candidate error per PDE
-- ---------------------------------------------------------------------
-- Every PDE carries a CANDIDATE error (type, direction, corrected GDC)
-- and an activation uniform u_act. Step 04 activates a candidate when
-- u_act < m, one calibrated multiplier for all types (see step 03).
-- Error types and base relative probabilities (FY 2025 count shares of
-- sampled errors): missing/invalid documentation 75.00% (all-or-nothing,
-- corrected GDC = 0), pricing 17.86% (partial +/- ~12% of GDC, 40% are
-- underpayments), drug discrepancy 7.14% (half are a costlier drug
-- supported by the record -> underpayment; half a cheaper one).
-- One multiplier m applies to all types, so active errors keep the
-- published type shares in expectation.
-- =====================================================================

-- Step 3. Candidate error per PDE (not yet active).
CREATE OR REPLACE TABLE pdes AS
WITH t AS (
    SELECT *,
           u01(getvariable('seed'), 'etype', pde_id) AS u_type,
           u01(getvariable('seed'), 'edir', pde_id) AS u_dir,
           rkuma(getvariable('seed'), 'emag', pde_id, 1.5, 6.0) AS f_price,          -- mean ~0.12
           rlnorm(getvariable('seed'), 'emag_dd', pde_id, 0.0, 0.5) AS f_drug,
           u01(getvariable('seed'), 'act', pde_id) AS u_act
    FROM pdes
),
k AS (
    SELECT *,
           CASE WHEN u_type < 0.7500 THEN 'missing_documentation'
                WHEN u_type < 0.9286 THEN 'pricing'
                ELSE 'drug_discrepancy' END AS cand_type
    FROM t
)
SELECT *,
       CASE cand_type WHEN 'missing_documentation' THEN 'over'
                      WHEN 'pricing' THEN CASE WHEN u_dir < 0.40 THEN 'under' ELSE 'over' END
                      ELSE CASE WHEN u_dir < 0.50 THEN 'under' ELSE 'over' END END AS cand_dir,
       CASE cand_type
            WHEN 'missing_documentation' THEN usd(0)
            WHEN 'pricing' THEN CASE WHEN u_dir < 0.40 THEN usd(gdc * (1 + f_price))
                                     ELSE usd(gdc * (1 - f_price)) END
            ELSE CASE WHEN u_dir < 0.50 THEN usd(gdc * (1 + 3.5 * f_drug))               -- costlier drug (factor tuned once to the public over/under split)
                      ELSE usd(gdc * greatest(0.0, 1 - abs(f_drug - 1) - 0.05)) END   -- cheaper drug
       END AS cand_gdc
FROM k;
