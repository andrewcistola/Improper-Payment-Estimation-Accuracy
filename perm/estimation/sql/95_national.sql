-- =====================================================================
-- perm estimation/95_national.sql : pool the 9 states
-- ---------------------------------------------------------------------
-- States are sampled independently, so for each audit year and component:
--   expansion, ratio, regression:
--     national dollars T = sum_s rate_s X_s,  Var(T) = sum_s (se_s X_s)^2
--     rate = T / X, X = sum_s X_s; normal 95% interval (T +- 1.96 sqrt(Var)) / X
--   bootstrap simulation: iteration i's national rate is
--     sum_s rate_{s,i} X_s / X  (iterations of different states are
--     independent, so pairing them by index is a valid draw); estimate =
--     mean, interval = 2.5th-97.5th percentiles (linear interpolation).
-- X_s = the state's payments at federal share (its truth.json).
-- Output: estimates, frame_totals, metrics for domain national|<component>.
-- =====================================================================
CREATE OR REPLACE MACRO perm_dir() AS
    CASE WHEN starts_with(getvariable('perm_results_dir'), '/') THEN getvariable('perm_results_dir')
         ELSE getvariable('repo_root') || '/' || getvariable('perm_results_dir') END;

CREATE OR REPLACE TABLE st_tot AS
SELECT regexp_extract(filename, 'state_([0-9]+)', 1)::INTEGER AS state, split_part(domain, '|', 2) AS component, X, Y
FROM read_json(perm_dir() || '/state_*/truth.json', filename = true);

CREATE OR REPLACE TABLE frame_totals AS
SELECT 'national|' || component AS domain, fsum(X) AS X, fsum(Y) AS Y, fsum(Y) / fsum(X) AS theta
FROM st_tot GROUP BY component;

CREATE OR REPLACE TABLE st_est AS
SELECT regexp_extract(filename, 'state_([0-9]+)', 1)::INTEGER AS state, split_part(domain, '|', 2) AS component,
       method, "interval", rep, estimate, se
FROM read_parquet(perm_dir() || '/state_*/estimates.parquet', filename = true);

CREATE OR REPLACE TABLE st_draws AS
SELECT regexp_extract(filename, 'state_([0-9]+)', 1)::INTEGER AS state, split_part(domain, '|', 2) AS component,
       rep, iter, rate
FROM read_parquet(perm_dir() || '/state_*/sim_draws.parquet', filename = true);

CREATE OR REPLACE TABLE estimates AS
WITH a AS (
    SELECT e.method, e."interval", e.rep, 'national|' || e.component AS domain,
           fsum(e.estimate * t.X) AS t_y, sqrt(fsum(power(e.se * t.X, 2))) AS sd_t, fsum(t.X) AS x_tot
    FROM st_est e JOIN st_tot t USING (state, component)
    WHERE e.method <> 'simulation'
    GROUP BY e.method, e."interval", e.rep, e.component
),
nd AS (
    SELECT d.rep, d.iter, 'national|' || d.component AS domain, fsum(d.rate * t.X) / fsum(t.X) AS rate
    FROM st_draws d JOIN st_tot t USING (state, component)
    GROUP BY d.rep, d.iter, d.component
)
SELECT method, "interval", rep, domain, t_y / x_tot AS estimate, sd_t / x_tot AS se,
       (t_y - norm_ppf(1 - getvariable('alpha') / 2) * sd_t) / x_tot AS lower,
       (t_y + norm_ppf(1 - getvariable('alpha') / 2) * sd_t) / x_tot AS upper
FROM a
UNION ALL
SELECT 'simulation', 'percentile', rep, domain, favg(rate), fsd(rate),
       quantile_cont(rate, getvariable('alpha') / 2), quantile_cont(rate, 1 - getvariable('alpha') / 2)
FROM nd GROUP BY rep, domain;

CREATE OR REPLACE TABLE metrics AS SELECT * FROM ipm_score();
