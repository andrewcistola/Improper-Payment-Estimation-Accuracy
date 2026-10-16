-- =====================================================================
-- shared/sql/lib/02_estimators.sql : the four IPM estimation methods
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
-- 4. simulation  rescaled bootstrap (Rao & Wu 1988) of the ratio
--                estimator, B replicates. In each replicate and stratum,
--                draw m_h = n_h - 1 units with replacement (count c_i);
--                replicate weight w* = w [1 - lambda + lambda (n_h/m_h) c_i],
--                lambda = sqrt(m_h (1 - f_h) / (n_h - 1)) = sqrt(1 - f_h).
--                theta*_b = sum w* y / sum w* x. Intervals:
--                  percentile  : quantiles a/2, 1-a/2 of theta*
--                  bootstrap_t : t*_b = (theta*_b - theta) / se*_b, with
--                                se*_b the ratio formula on replicate b;
--                                [theta - t*_(1-a/2) se, theta - t*_(a/2) se];
--                                replicates with se*_b = 0 (e.g. no errors
--                                drawn) are left out of the t* distribution
--                  bca         : quantiles at Phi(z0 + (z0+z)/(1 - a(z0+z))),
--                                z0 from the share of theta*_b < theta,
--                                acceleration a from the delete-one
--                                stratified jackknife of the ratio estimator
--                Strata with n_h < 2 keep their original weights.
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

-- 4. Simulation (rescaled bootstrap of the ratio estimator) ----------
CREATE OR REPLACE MACRO ipm_bootstrap(boot_reps, alpha) AS TABLE
WITH
indexed AS (   -- sampled units numbered 1..n_h within each stratum
    SELECT rep, domain, stratum, y::DECIMAL(38, 6) AS y, x::DECIMAL(38, 6) AS x,
           row_number() OVER (PARTITION BY rep, domain, stratum ORDER BY unit_id) AS idx
    FROM sample
),
lists AS (   -- stratum summaries (one row per sample x domain x stratum)
    SELECT rep, domain, stratum,
           any_value(pop_h)::DOUBLE AS big_n, any_value(samp_h)::BIGINT AS small_n,
           sum(y)::DOUBLE AS sy, sum(x)::DOUBLE AS sx,
           rbase(getvariable('seed'), 'boot|' || stratum, rep, 0) AS boot_base  -- same across domains
    FROM sample GROUP BY rep, domain, stratum
),
draw_idx AS (   -- m_h = n_h - 1 unit numbers drawn with replacement, per replicate b
    SELECT l.rep, l.domain, l.stratum, bb.b,
           1 + floor(l.small_n * u01f(l.boot_base, bb.b * 1000003 + d.d))::BIGINT AS idx
    FROM lists l
    CROSS JOIN (SELECT range AS b FROM range(1, boot_reps + 1)) bb,
    LATERAL range(1, l.small_n) d(d)
    WHERE l.small_n >= 2
),
draws AS (   -- sums over the drawn units (each draw counted once)
    SELECT d.rep, d.domain, d.stratum, d.b,
           sum(i.y)::DOUBLE AS dy, sum(i.x)::DOUBLE AS dx,
           sum(i.y * i.y)::DOUBLE AS dyy, sum(i.x * i.x)::DOUBLE AS dxx, sum(i.y * i.x)::DOUBLE AS dxy
    FROM draw_idx d JOIN indexed i USING (rep, domain, stratum, idx)
    GROUP BY d.rep, d.domain, d.stratum, d.b
),
rep_strata AS (   -- replicate totals per stratum (n_h < 2: original weights)
    SELECT l.rep, l.domain, l.stratum, bb.b, l.big_n, l.small_n,
           d.dy, d.dx, d.dyy, d.dxx, d.dxy,
           CASE WHEN l.small_n >= 2
                THEN (l.big_n / l.small_n) * ((1 - sqrt(1 - l.small_n / l.big_n)) * l.sy
                     + sqrt(1 - l.small_n / l.big_n) * l.small_n / (l.small_n - 1) * d.dy)
                ELSE (l.big_n / l.small_n) * l.sy END AS ty_star,
           CASE WHEN l.small_n >= 2
                THEN (l.big_n / l.small_n) * ((1 - sqrt(1 - l.small_n / l.big_n)) * l.sx
                     + sqrt(1 - l.small_n / l.big_n) * l.small_n / (l.small_n - 1) * d.dx)
                ELSE (l.big_n / l.small_n) * l.sx END AS tx_star
    FROM lists l
    CROSS JOIN (SELECT range AS b FROM range(1, boot_reps + 1)) bb
    LEFT JOIN draws d USING (rep, domain, stratum, b)
),
reps AS (   -- theta*_b
    SELECT rep, domain, b, fsum(ty_star) / fsum(tx_star) AS theta_star, fsum(tx_star) AS tx_star
    FROM rep_strata GROUP BY rep, domain, b
),
reps_se AS (   -- se*_b: ratio linearization on the m_h drawn units of replicate b
    SELECT r.rep, r.domain, r.b, r.theta_star,
           sqrt(fsum(CASE WHEN s.small_n >= 3 THEN
                    s.big_n * s.big_n * (1 - s.small_n / s.big_n) / s.small_n
                    * greatest(0.0, ((s.dyy - 2 * r.theta_star * s.dxy + r.theta_star * r.theta_star * s.dxx)
                                     - power(s.dy - r.theta_star * s.dx, 2) / (s.small_n - 1))
                                    / (s.small_n - 2))
                    ELSE 0 END)) / r.tx_star AS se_star
    FROM reps r JOIN rep_strata s USING (rep, domain, b)
    GROUP BY r.rep, r.domain, r.b, r.theta_star, r.tx_star
),
est AS (   -- the sample's own ratio estimate and linearization se
    SELECT * FROM ipm_ratio(alpha)
),
jack AS (   -- delete-one stratified jackknife of the ratio estimator
    SELECT s.rep, s.domain,
           (r.t_y - m.w * m.sy + m.big_n / (m.small_n - 1) * (m.sy - s.y::DOUBLE))
           / (r.t_x - m.w * m.sx + m.big_n / (m.small_n - 1) * (m.sx - s.x::DOUBLE)) AS theta_i
    FROM sample s
    JOIN ipm_moments() m USING (rep, domain, stratum)
    JOIN ipm_ratio_point() r USING (rep, domain)
    WHERE m.small_n >= 2
),
jack_mean AS (
    SELECT rep, domain, favg(theta_i) AS avg_i FROM jack GROUP BY rep, domain
),
accel AS (
    SELECT rep, domain,
           CASE WHEN fsum(power(avg_i - theta_i, 2)) > 0
                THEN fsum(power(avg_i - theta_i, 3)) / (6 * power(fsum(power(avg_i - theta_i, 2)), 1.5))
                ELSE 0 END AS a
    FROM jack JOIN jack_mean USING (rep, domain)
    GROUP BY rep, domain
),
dist AS (
    SELECT s.rep, s.domain, e.estimate, e.se,
           list_sort(list(s.theta_star)) AS th,
           list_sort(list((s.theta_star - e.estimate) / s.se_star) FILTER (WHERE s.se_star > 0)) AS tt,
           fsd(s.theta_star) AS boot_se,
           (count(*) FILTER (WHERE s.theta_star < e.estimate)
            + 0.5 * count(*) FILTER (WHERE s.theta_star = e.estimate)) / count(*) AS p0
    FROM reps_se s JOIN est e USING (rep, domain)
    GROUP BY s.rep, s.domain, e.estimate, e.se
),
z AS (   -- normal quantiles, computed once
    SELECT norm_ppf(alpha / 2) AS z_lo, norm_ppf(1 - alpha / 2) AS z_hi
),
bca0 AS (
    SELECT d.*, coalesce(a.a, 0) AS a, z.z_lo, z.z_hi,
           least(1 - 0.5 / boot_reps, greatest(0.5 / boot_reps, d.p0)) AS p0_clipped
    FROM dist d LEFT JOIN accel a USING (rep, domain), z
),
bca1 AS (
    SELECT *, norm_ppf(p0_clipped) AS z0 FROM bca0
),
bca2 AS (   -- BCa-adjusted percentile arguments
    SELECT *, z0 + (z0 + z_lo) / (1 - a * (z0 + z_lo)) AS arg_lo,
              z0 + (z0 + z_hi) / (1 - a * (z0 + z_hi)) AS arg_hi
    FROM bca1
),
bca AS (
    SELECT *, norm_cdf(arg_lo) AS level_lo, norm_cdf(arg_hi) AS level_hi FROM bca2
)
SELECT 'simulation' AS method, 'percentile' AS interval, rep, domain, estimate, boot_se AS se,
       qsorted(th, alpha / 2) AS lower, qsorted(th, 1 - alpha / 2) AS upper
FROM bca
UNION ALL
SELECT 'simulation', 'bootstrap_t', rep, domain, estimate, boot_se,
       estimate - coalesce(qsorted(tt, 1 - alpha / 2), 0) * se,
       estimate - coalesce(qsorted(tt, alpha / 2), 0) * se
FROM bca
UNION ALL
SELECT 'simulation', 'bca', rep, domain, estimate, boot_se,
       qsorted(th, level_lo), qsorted(th, level_hi)
FROM bca;

-- Scoring against the truth ------------------------------------------
-- covered      : lower <= theta <= upper (an undefined interval counts
--                as not covered; n_undefined reports how many)
-- above / below: interval entirely above (lower > theta) or below
--                (upper < theta) the truth; balance between the two
--                tails matters for PIIA rate reporting
-- rel_bias, rel_rmse, rel_width: relative to the true rate
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
       favg(e.se) AS mean_se,
       fsd(e.estimate) AS empirical_se
FROM estimates e JOIN frame_totals f USING (domain)
GROUP BY e.domain, e.method, e.interval;
