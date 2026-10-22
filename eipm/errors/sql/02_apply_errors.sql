-- =====================================================================
-- eipm errors/02_apply_errors.sql : fake APTC errors (overpayments only)
-- ---------------------------------------------------------------------
-- The public FFE results report no underpayments (FY 2023-2025), so every
-- error here is an overpayment (y >= 0). Two error types, at most one per
-- application, from one uniform u_act per application:
--   technical : a required periodic data match was not run, so the whole
--               APTC is improper ("technically improper"; FY 2025: 0.43
--               of the 0.89 points). y = x.          u_act < p_t
--   monetary  : income entered wrong (or documents accepted that do not
--               support it): the income the record supports is HIGHER
--               than the income used, by a factor max(r, 1/r),
--               r ~ lognormal(0, 0.35); APTC recomputed at the supported
--               income. y = x - correct APTC (partial, or whole when the
--               correct APTC is 0).        p_t <= u_act < p_t + p_m
-- Rates are closed form (candidate amounts are known, so expectations are
-- exact), with per-application probabilities p_t s_i and p_m s_i:
--   p_t = target_rate x technical_share x sum x / sum(s_i x_i)
--   p_m = target_rate x (1 - technical_share) x sum x / sum(s_i x cand y)
-- size_beta (default 0): dependence of the error probability on the APTC
-- paid, s_i = (x_i / mean x)^size_beta, capped so that an application's
-- total error probability (p_t + p_m) s_i stays at or below 0.95. At
-- size_beta = 0 every s_i = 1 and the adjustment factors are exactly 1,
-- so the output is byte-identical to the version without this variable;
-- at size_beta > 0 larger APTC amounts are more likely to be in error
-- (0.5: with the square root of the amount).
-- A monetary candidate whose correct APTC equals the APTC paid (income
-- already at the 600% FPL cap) has y = 0 and is not an error.
-- Strata (for estimation): five equal-count quintiles of annual APTC
-- paid, P1 (smallest) .. P5.
-- Output: population (one row per application), calib
-- =====================================================================
-- Step 3. Candidate monetary error and its dollar amount
CREATE OR REPLACE TABLE hh AS
WITH c AS (
    SELECT h.*,
           rlnorm(getvariable('seed'), 'true_inc', unit_id, 0.0, 0.35) AS r_inc,
           u01(getvariable('seed'), 'act', unit_id) AS u_act
    FROM hh h
),
t AS (SELECT *, least(600.0, fpl_pct * greatest(r_inc, 1.0 / r_inc)) AS true_fpl_pct FROM c)
SELECT t.*,
       (usd(greatest(0, benchmark_month - applicable_pct(true_fpl_pct) * true_fpl_pct / 100.0 * fpl_dollars / 12.0))
        * months)::DECIMAL(18, 2) AS cand_correct_aptc
FROM t;

-- Step 4. Rates (closed form) and activation
-- size factor s_i, capped so that (p_t + p_m) s_i <= 0.95 at the size-independent rates
CREATE OR REPLACE TABLE hh AS
WITH k AS (
    SELECT fsum(x) / count(*) AS mean_x,
           getvariable('target_rate') * getvariable('technical_share')
             + getvariable('target_rate') * (1 - getvariable('technical_share'))
               * sum(x)::DOUBLE / sum(x - cand_correct_aptc)::DOUBLE AS p_any0
    FROM hh
)
SELECT h.*, least(pow(h.x::DOUBLE / k.mean_x, coalesce(getvariable('size_beta'), 0.0)::DOUBLE), 0.95 / k.p_any0) AS s_size
FROM hh h, k;

CREATE OR REPLACE TABLE calib AS
SELECT round(getvariable('target_rate') * getvariable('technical_share')
             * (fsum(x) / fsum(x::DOUBLE * s_size)), 8) AS p_t,
       round(getvariable('target_rate') * (1 - getvariable('technical_share'))
             * sum(x)::DOUBLE / sum(x - cand_correct_aptc)::DOUBLE
             * (fsum((x - cand_correct_aptc)::DOUBLE) / fsum((x - cand_correct_aptc)::DOUBLE * s_size)), 8) AS p_m
FROM hh;

CREATE OR REPLACE TABLE population AS
WITH a AS (
    SELECT h.*,
           CASE WHEN h.u_act < h.s_size * c.p_t THEN 'technical'
                WHEN h.u_act < least(0.95, h.s_size * (c.p_t + c.p_m)) AND h.cand_correct_aptc < h.x THEN 'monetary'
                ELSE 'none' END AS error_type
    FROM hh h, calib c
)
SELECT unit_id,
       'P' || ntile(5) OVER (ORDER BY x, unit_id) AS stratum,
       region, hh_size, age, fpl_pct, months,
       benchmark_month, aptc_month, x,
       CASE error_type WHEN 'technical' THEN x
                       WHEN 'monetary' THEN (x - cand_correct_aptc)::DECIMAL(18, 2)
                       ELSE usd(0) END AS y,
       CASE WHEN error_type = 'technical' THEN x ELSE usd(0) END AS y_technical,
       CASE WHEN error_type = 'monetary' THEN (x - cand_correct_aptc)::DECIMAL(18, 2) ELSE usd(0) END AS y_monetary,
       error_type,
       getvariable('w_pop')::DOUBLE AS w_pop,
       CASE WHEN error_type = 'monetary' THEN true_fpl_pct END AS true_fpl_pct   -- audit finding: supported income
FROM a;
