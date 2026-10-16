-- =====================================================================
-- eipm/01_population.sql : Marketplace APTC applications (EIPM-like)
-- ---------------------------------------------------------------------
-- Application 4: beneficiary subsidy eligibility errors.
-- Unit = FFE application (household). Annual APTC paid:
--   benchmark  = monthly second-lowest-cost silver premium for household
--   applicable % of income by %FPL (schedule from config; default is the
--     enhanced ARPA/IRA schedule in force for plan years 2021-2025)
--   APTC/month = max(0, benchmark - applicable% * income / 12)
--   x          = APTC/month * months enrolled
-- Errors are rare. Each application carries one candidate error whose
-- type is drawn with the configured shares, and is in error with
-- probability m (same for every type). m is ONE closed-form
-- multiplier: target gross dollars / expected gross dollars at m = 1
-- (candidate dollar amounts are known, so the expectation is exact).
--   income_misstatement : APTC recomputed at true income (two-sided, partial)
--   eligibility_failure : not eligible for APTC (e.g. other coverage),
--                         whole APTC improper (all-or-nothing)
--   missing_documentation: unverifiable, whole APTC improper
-- =====================================================================

-- Step 1. Households
CREATE OR REPLACE TABLE hh AS
SELECT i AS unit_id,
       1 + floor(4 * pow(u01(getvariable('seed'), 'size', i), 1.6))::INT AS hh_size,      -- 1..4, mostly 1-2
       21 + floor(44 * u01(getvariable('seed'), 'age', i))::INT AS age,
       least(600.0, greatest(100.0, 100.0 + rlnorm(getvariable('seed'), 'fpl', i, 4.6, 0.75))) AS fpl_pct,
       CASE WHEN u01(getvariable('seed'), 'full', i) < 0.75 THEN 12
            ELSE 1 + floor(11 * u01(getvariable('seed'), 'months', i))::INT END AS months,
       1 + floor(4 * u01(getvariable('seed'), 'region', i))::INT AS region
FROM range(1, getvariable('n_households') + 1) t(i);

-- applicable percentage: linear within bands (config list of [lo, hi, pct_lo, pct_hi])
CREATE OR REPLACE MACRO applicable_pct(f) AS (
    SELECT coalesce(max(b.p_lo + (b.p_hi - b.p_lo) * (f - b.lo) / (b.hi - b.lo)), 0.085)
    FROM (SELECT unnest(from_json(getvariable('applicable_schedule')::JSON,
                 '[{"lo":"DOUBLE","hi":"DOUBLE","p_lo":"DOUBLE","p_hi":"DOUBLE"}]'), recursive := true)) b
    WHERE f >= b.lo AND f < b.hi
);

-- Step 2. APTC
CREATE OR REPLACE TABLE hh AS
SELECT h.*,
       getvariable('fpl_base') + getvariable('fpl_per_person') * (h.hh_size - 1) AS fpl_dollars,
       usd(getvariable('benchmark_base') * pow(1.0 + 0.018, h.age - 21)   -- age rating (illustrative)
           * (0.80 + 0.20 * h.hh_size) * (0.85 + 0.10 * h.region)) AS benchmark_month
FROM hh h;

CREATE OR REPLACE TABLE hh AS
SELECT h.*,
       h.fpl_pct / 100.0 * h.fpl_dollars AS income,
       applicable_pct(h.fpl_pct) AS app_pct,
       usd(greatest(0, h.benchmark_month - applicable_pct(h.fpl_pct) * h.fpl_pct / 100.0 * h.fpl_dollars / 12.0))
           AS aptc_month
FROM hh h;

-- keep only APTC recipients (the measured population)
CREATE OR REPLACE TABLE hh AS
SELECT *, (aptc_month * months)::DECIMAL(18, 2) AS x FROM hh WHERE aptc_month > 0;

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
       h.region, h.hh_size, h.age, round(h.fpl_pct, 1) AS fpl_pct, h.months,
       h.benchmark_month, h.aptc_month, h.x,
       CASE WHEN h.u_act < least(0.95, c.m) THEN (h.x - h.cand_correct_aptc)::DECIMAL(18, 2) ELSE usd(0) END AS y,
       CASE WHEN h.u_act < least(0.95, c.m) THEN h.cand_type ELSE 'none' END AS error_type,
       getvariable('w_pop')::DOUBLE AS w_pop
FROM hh h, calib c;

CREATE OR REPLACE TABLE truth AS
WITH g AS (
    SELECT 'overall' AS level, NULL::VARCHAR AS key, * FROM population
    UNION ALL SELECT 'stratum', stratum, * FROM population
),
a AS (
    SELECT level, key, count(*)::DOUBLE AS n_units,
           any_value(w_pop) * sum(x)::DOUBLE AS payments,
           any_value(w_pop) * sum(y) FILTER (WHERE y > 0)::DOUBLE AS overpayments,
           any_value(w_pop) * -sum(y) FILTER (WHERE y < 0)::DOUBLE AS underpayments,
           avg((y <> 0)::INT)::DOUBLE AS unit_err_rate
    FROM g GROUP BY level, key
)
SELECT level, key, metric, value FROM (
    SELECT *, (coalesce(overpayments, 0) + coalesce(underpayments, 0)) / payments AS gross_rate FROM a)
UNPIVOT (value FOR metric IN (n_units, payments, overpayments, underpayments, unit_err_rate, gross_rate))
UNION ALL SELECT 'calibration', 'multiplier', 'm', m FROM calib;
