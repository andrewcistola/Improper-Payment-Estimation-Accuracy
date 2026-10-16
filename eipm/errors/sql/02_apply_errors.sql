-- =====================================================================
-- eipm errors/02_apply_errors.sql : fake APTC eligibility errors
-- ---------------------------------------------------------------------
-- Errors are rare. Each application carries one candidate error whose
-- type is drawn with the configured shares, and is in error with
-- probability m (same for every type). m is ONE closed-form multiplier:
-- target gross dollars / expected gross dollars at m = 1 (candidate
-- dollar amounts are known, so the expectation is exact).
--   income_misstatement  : APTC recomputed at true income (two-sided, partial)
--   eligibility_failure  : not eligible for APTC (e.g. other coverage),
--                          whole APTC improper (all-or-nothing)
--   missing_documentation: unverifiable, whole APTC improper
-- Output: population (one row per application), calib
-- =====================================================================
-- Step 3. Candidate errors and their dollar amounts
CREATE OR REPLACE TABLE hh AS
WITH c AS (
    SELECT h.*,
           u01(getvariable('seed'), 'etype', unit_id) AS u_type,
           -- true income differs by a lognormal factor (either direction)
           least(600.0, greatest(100.0, h.fpl_pct * rlnorm(getvariable('seed'), 'true_inc', unit_id, 0.0, 0.35)))
               AS true_fpl_pct,
           u01(getvariable('seed'), 'act', unit_id) AS u_act
    FROM hh h
),
k AS (
    SELECT *,
           CASE WHEN u_type < getvariable('share_income') THEN 'income_misstatement'
                WHEN u_type < getvariable('share_income') + getvariable('share_elig') THEN 'eligibility_failure'
                ELSE 'missing_documentation' END AS cand_type
    FROM c
)
SELECT k.*,
       CASE WHEN cand_type = 'income_misstatement' THEN
                (usd(greatest(0, benchmark_month - applicable_pct(true_fpl_pct) * true_fpl_pct / 100.0 * fpl_dollars / 12.0))
                 * months)::DECIMAL(18, 2)
            ELSE usd(0) END AS cand_correct_aptc
FROM k;

-- Step 4. Calibrate m (closed form) and activate
CREATE OR REPLACE TABLE calib AS
SELECT round(getvariable('target_rate') * sum(x)::DOUBLE / sum(abs(x - cand_correct_aptc))::DOUBLE, 8) AS m
FROM hh;

CREATE OR REPLACE TABLE population AS
SELECT h.unit_id,
       CASE WHEN h.fpl_pct < 150 THEN 'A_lt150' WHEN h.fpl_pct < 250 THEN 'B_150_250'
            WHEN h.fpl_pct < 400 THEN 'C_250_400' ELSE 'D_ge400' END AS stratum,
       h.region, h.hh_size, h.age, h.fpl_pct, h.months,
       h.benchmark_month, h.aptc_month, h.x,
       CASE WHEN h.u_act < least(0.95, c.m) THEN (h.x - h.cand_correct_aptc)::DECIMAL(18, 2) ELSE usd(0) END AS y,
       CASE WHEN h.u_act < least(0.95, c.m) THEN h.cand_type ELSE 'none' END AS error_type,
       getvariable('w_pop')::DOUBLE AS w_pop,
       CASE WHEN h.u_act < least(0.95, c.m) AND h.cand_type = 'income_misstatement'
            THEN h.true_fpl_pct END AS true_fpl_pct   -- audit finding: income the record supports
FROM hh h, calib c;
