-- =====================================================================
-- shared/sql/lib/02_estimators.sql : analytic IPM estimators and scoring
-- ---------------------------------------------------------------------
-- Written once here and called by every program's estimation/sql files.
-- Estimand (per domain): the improper payment RATE  theta = Y / X,
--   Y = sum of improper amounts y, X = sum of amounts paid x (known from
--   the frame, as it is in production).
-- Notation (stratum h): N_h = pop_h, n_h = samp_h, f_h = n_h / N_h,
--   w = N_h / n_h, s2_* = sample variances/covariance within stratum,
--   T_y = sum_h N_h * ybar_h, T_x likewise.
--
-- 1. expansion   theta = T_y / X
--                V(T_y) = sum_h N_h^2 (1 - f_h) s2_y / n_h,  se = sqrt(V) / X
-- 2. ratio       theta = T_y / T_x                          (linearization)
--                e = y - theta*x;  s2_e = s2_y - 2 theta s_xy + theta^2 s2_x
--                se = sqrt(sum_h N_h^2 (1 - f_h) s2_e / n_h) / T_x
-- 3. regression  combined GREG with an intercept and one auxiliary (x):
--                b = sum w(x - xbar)(y - ybar) / sum w(x - xbar)^2
--                T_reg = T_y + b (X - T_x);  theta = T_reg / X
--                s2_e = s2_y - 2 b s_xy + b^2 s2_x
--                se = sqrt(sum_h N_h^2 (1 - f_h) s2_e / n_h) / X
--    Methods 1-3 report a normal two-sided interval: theta +/- z se.
-- 4. simulation  NOT here: the audit-finding bootstrap simulation reruns each
--                program's payment function over the whole population,
--                so it lives in shared/ipsim/simulation.py (the loop) and
--                <program>/estimation/*simulation.py (payment function).
--                Its results join the others in the same estimates table
--                and are scored by ipm_score below.
--
-- Input contract (placeholder tables; programs replace them with data):
-- =====================================================================

CREATE TABLE IF NOT EXISTS sample (
    rep INTEGER, domain VARCHAR, stratum VARCHAR, pop_h BIGINT, samp_h BIGINT,
    unit_id BIGINT, y DECIMAL(18, 6), x DECIMAL(18, 6), w DOUBLE);
CREATE TABLE IF NOT EXISTS frame_totals (domain VARCHAR, X DOUBLE, Y DOUBLE, theta DOUBLE);
CREATE TABLE IF NOT EXISTS estimates (
    method VARCHAR, interval VARCHAR, rep INTEGER, domain VARCHAR,
    estimate DOUBLE, se DOUBLE, lower DOUBLE, upper DOUBLE);

-- Stratum moments for every sample. Sums are exact (DECIMAL), so results
-- do not depend on thread scheduling.
CREATE OR REPLACE MACRO ipm_strata() AS TABLE
SELECT rep, domain, stratum,
       any_value(pop_h)::DOUBLE AS big_n, any_value(samp_h)::DOUBLE AS small_n,
       sum(y)::DOUBLE AS sy, sum(x)::DOUBLE AS sx,
       sum(y::DECIMAL(38, 6) * y::DECIMAL(38, 6))::DOUBLE AS syy,
       sum(x::DECIMAL(38, 6) * x::DECIMAL(38, 6))::DOUBLE AS sxx,
       sum(x::DECIMAL(38, 6) * y::DECIMAL(38, 6))::DOUBLE AS sxy
FROM sample GROUP BY rep, domain, stratum;

CREATE OR REPLACE MACRO ipm_moments() AS TABLE
SELECT *,
       big_n / small_n AS w,
       1.0 - small_n / big_n AS fpc,
       CASE WHEN small_n > 1 THEN greatest(0.0, (syy - sy * sy / small_n) / (small_n - 1)) ELSE 0 END AS vy,
       CASE WHEN small_n > 1 THEN greatest(0.0, (sxx - sx * sx / small_n) / (small_n - 1)) ELSE 0 END AS vx,
       CASE WHEN small_n > 1 THEN (sxy - sx * sy / small_n) / (small_n - 1) ELSE 0 END AS cxy
FROM ipm_strata();

-- 1. Expansion -------------------------------------------------------
CREATE OR REPLACE MACRO ipm_expansion(alpha) AS TABLE
WITH d AS (
    SELECT rep, domain,
           fsum(w * sy) AS t_y,
           fsum(big_n * big_n * fpc * vy / small_n) AS v_ty
    FROM ipm_moments() GROUP BY rep, domain
)
SELECT 'expansion' AS method, 'normal' AS interval, d.rep, d.domain,
       d.t_y / f.X AS estimate, sqrt(d.v_ty) / f.X AS se,
       d.t_y / f.X - z.z * sqrt(d.v_ty) / f.X AS lower,
       d.t_y / f.X + z.z * sqrt(d.v_ty) / f.X AS upper
FROM d JOIN frame_totals f USING (domain), (SELECT norm_ppf(1 - alpha / 2) AS z) z;

-- 2. Ratio -----------------------------------------------------------
CREATE OR REPLACE MACRO ipm_ratio_point() AS TABLE
SELECT rep, domain, fsum(w * sy) AS t_y, fsum(w * sx) AS t_x, fsum(w * sy) / fsum(w * sx) AS theta
FROM ipm_moments() GROUP BY rep, domain;

CREATE OR REPLACE MACRO ipm_ratio(alpha) AS TABLE
WITH v AS (
    SELECT m.rep, m.domain, r.theta, r.t_x,
           fsum(m.big_n * m.big_n * m.fpc
               * greatest(0.0, m.vy - 2 * r.theta * m.cxy + r.theta * r.theta * m.vx) / m.small_n) AS v_e
    FROM ipm_moments() m JOIN ipm_ratio_point() r USING (rep, domain)
    GROUP BY m.rep, m.domain, r.theta, r.t_x
)
SELECT 'ratio' AS method, 'normal' AS interval, rep, domain,
       theta AS estimate, sqrt(v_e) / t_x AS se,
       theta - z.z * sqrt(v_e) / t_x AS lower,
       theta + z.z * sqrt(v_e) / t_x AS upper
FROM v, (SELECT norm_ppf(1 - alpha / 2) AS z) z;

-- 3. Regression (GREG, one auxiliary) --------------------------------
CREATE OR REPLACE MACRO ipm_regression(alpha) AS TABLE
WITH p AS (  -- pooled weighted moments
    SELECT rep, domain,
           fsum(big_n) AS n_hat, fsum(w * sy) AS t_y, fsum(w * sx) AS t_x,
           fsum(w * sxx) AS t_xx, fsum(w * sxy) AS t_xy
    FROM ipm_moments() GROUP BY rep, domain
),
b AS (
    SELECT p.*,
           CASE WHEN t_xx - t_x * t_x / n_hat > 0
                THEN (t_xy - t_x * t_y / n_hat) / (t_xx - t_x * t_x / n_hat) ELSE 0 END AS slope
    FROM p
),
v AS (
    SELECT b.rep, b.domain, b.t_y, b.t_x, b.slope,
           fsum(m.big_n * m.big_n * m.fpc
               * greatest(0.0, m.vy - 2 * b.slope * m.cxy + b.slope * b.slope * m.vx) / m.small_n) AS v_e
    FROM ipm_moments() m JOIN b USING (rep, domain)
    GROUP BY b.rep, b.domain, b.t_y, b.t_x, b.slope
)
SELECT 'regression' AS method, 'normal' AS interval, v.rep, v.domain,
       (v.t_y + v.slope * (f.X - v.t_x)) / f.X AS estimate,
       sqrt(v.v_e) / f.X AS se,
       (v.t_y + v.slope * (f.X - v.t_x)) / f.X - z.z * sqrt(v.v_e) / f.X AS lower,
       (v.t_y + v.slope * (f.X - v.t_x)) / f.X + z.z * sqrt(v.v_e) / f.X AS upper
FROM v JOIN frame_totals f USING (domain), (SELECT norm_ppf(1 - alpha / 2) AS z) z;

-- Scoring against the truth ------------------------------------------
-- covered      : lower <= theta <= upper (an undefined interval counts
--                as not covered; n_undefined reports how many)
-- above / below: interval entirely above (lower > theta) or below
--                (upper < theta) the truth; balance between the two
--                tails matters for PIIA rate reporting
-- rel_bias, rel_rmse, rel_width: relative to the true rate
-- median_rel_width: median width / true rate (robust to a few huge
--                intervals)
-- mc_se_coverage: Monte Carlo standard error of the coverage estimate
CREATE OR REPLACE MACRO ipm_score() AS TABLE
SELECT e.domain, e.method, e.interval,
       count(*) AS reps,
       any_value(f.theta) AS theta,
       favg(e.estimate) AS mean_estimate,
       favg(e.estimate) / any_value(f.theta) - 1 AS rel_bias,
       sqrt(favg(power(e.estimate - f.theta, 2))) / any_value(f.theta) AS rel_rmse,
       avg(coalesce(e.lower <= f.theta AND f.theta <= e.upper, false)::INT) AS coverage,
       sqrt(avg(coalesce(e.lower <= f.theta AND f.theta <= e.upper, false)::INT)
            * (1 - avg(coalesce(e.lower <= f.theta AND f.theta <= e.upper, false)::INT)) / count(*)) AS mc_se_coverage,
       avg(coalesce(e.lower > f.theta, false)::INT) AS above,
       avg(coalesce(e.upper < f.theta, false)::INT) AS below,
       count(*) FILTER (WHERE e.lower IS NULL OR e.upper IS NULL) AS n_undefined,
       favg(e.upper - e.lower) / any_value(f.theta) AS rel_width,
       qsorted(list_sort(list((e.upper - e.lower)::DOUBLE)), 0.5) / any_value(f.theta) AS median_rel_width,
       favg(e.se) AS mean_se,
       fsd(e.estimate) AS empirical_se
FROM estimates e JOIN frame_totals f USING (domain)
GROUP BY e.domain, e.method, e.interval;
