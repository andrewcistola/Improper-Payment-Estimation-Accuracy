-- =====================================================================
-- eipm errors/01_population.sql : Marketplace APTC applications (no errors)
-- ---------------------------------------------------------------------
-- Application 4: beneficiary subsidy eligibility (EIPM-like, FFE).
-- Unit = FFE application (household). Annual APTC paid:
--   benchmark  = monthly second-lowest-cost silver premium for household
--   applicable % of income by %FPL (schedule from config; default is the
--     enhanced ARPA/IRA schedule in force for plan years 2021-2025)
--   APTC/month = max(0, benchmark - applicable% * income / 12)
--   x          = APTC/month * months enrolled
-- Only APTC recipients are kept (the measured population).
-- Output: hh (one row per application, error-free)
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
