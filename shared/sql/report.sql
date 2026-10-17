-- =====================================================================
-- shared/sql/report.sql : fabricated truth vs each estimate and its CI
-- ---------------------------------------------------------------------
-- Joins every program's estimation results (estimates.parquet: one row
-- per audit year x method x interval) to the fabricated truth in
-- the population (truth.json: theta = true improper payment rate).
-- No estimation is redone here.
--
-- Audit years reported: 1 .. audit_years (report.yaml), the same years for
-- every method. Each audit year is an independent random sample, so the
-- first audit_years are a random set of that many; the bootstrap simulation
-- runs on the first sim_reps years, so these are the years it has.
--
-- Outputs
--   by_audit_year : one row per audit year: true rate, point estimate,
--                   its error (estimate - true rate, also relative to the
--                   true rate), CI, and whether the CI contains the truth
--                   (inside / above / below / undefined). Dollars are on
--                   the national scale.
--   by_scenario   : one row per program x scenario x domain x method x
--                   interval: the truth, audit year 1's estimate and CI as
--                   a worked example, the average and the median estimate
--                   and CI bounds over the reported audit years, the average error of the point
--                   estimate (signed and absolute), and how many CIs
--                   contain the truth.
-- National dollars = rate x frame payments (X) x w_pop, where w_pop is the
-- number of real units each synthetic unit stands for (from each
-- errors/config.yaml): Part C 100, Part D 500, EIPM 100, PERM 200
-- (federal share), CERT 1 (stress populations, not scaled).
-- =====================================================================

CREATE OR REPLACE TABLE est AS
SELECT regexp_extract(filename, '([^/]+)/estimation/results/', 1) AS program,
       regexp_extract(filename, 'results/(.*)/estimates\.parquet$', 1) AS scenario,
       domain, method, "interval", rep, estimate, se, lower, upper
FROM read_parquet(getvariable('repo_root') || '/*/estimation/results/**/estimates.parquet', filename = true)
WHERE rep <= getvariable('audit_years');

CREATE OR REPLACE TABLE truth_rates AS
SELECT regexp_extract(filename, '([^/]+)/estimation/results/', 1) AS program,
       regexp_extract(filename, 'results/(.*)/truth\.json$', 1) AS scenario,
       domain, X AS frame_paid, Y AS frame_improper, theta AS true_rate
FROM read_json(getvariable('repo_root') || '/*/estimation/results/**/truth.json', filename = true);

CREATE OR REPLACE TABLE scale AS
SELECT program, scenario,
       CASE WHEN program = 'part-c-ipm' THEN 100
            WHEN program = 'part-d-ipm' THEN 500
            WHEN program = 'eipm' THEN 100
            WHEN scenario LIKE 'perm/%' THEN 200
            ELSE 1 END::DOUBLE AS w_pop
FROM (SELECT DISTINCT program, scenario FROM truth_rates);

CREATE OR REPLACE TABLE by_audit_year AS
SELECT e.program, e.scenario, e.domain, e.method, e."interval", e.rep AS audit_year,
       t.true_rate, e.estimate,
       e.estimate - t.true_rate AS error,
       (e.estimate - t.true_rate) / t.true_rate AS rel_error,
       e.lower, e.upper,
       CASE WHEN e.lower IS NULL OR e.upper IS NULL THEN 'undefined'
            WHEN t.true_rate < e.lower THEN 'above'      -- whole CI above the truth
            WHEN t.true_rate > e.upper THEN 'below'      -- whole CI below the truth
            ELSE 'inside' END AS truth_in_ci,
       round(t.frame_paid * s.w_pop, 2) AS total_paid_usd,
       round(t.frame_improper * s.w_pop, 2) AS true_improper_usd,
       round(e.estimate * t.frame_paid * s.w_pop, 2) AS estimate_usd,
       round(e.lower * t.frame_paid * s.w_pop, 2) AS lower_usd,
       round(e.upper * t.frame_paid * s.w_pop, 2) AS upper_usd
FROM est e
JOIN truth_rates t USING (program, scenario, domain)
JOIN scale s USING (program, scenario);

CREATE OR REPLACE TABLE by_scenario AS
SELECT program, scenario, domain, method, "interval",
       any_value(true_rate) AS true_rate,
       any_value(true_improper_usd) AS true_improper_usd,
       max(estimate) FILTER (WHERE audit_year = 1) AS year1_estimate,
       max(lower) FILTER (WHERE audit_year = 1) AS year1_lower,
       max(upper) FILTER (WHERE audit_year = 1) AS year1_upper,
       any_value(truth_in_ci) FILTER (WHERE audit_year = 1) AS year1_truth_in_ci,
       favg(estimate) AS mean_estimate,
       favg(lower) AS mean_lower,
       favg(upper) AS mean_upper,
       favg(estimate_usd) AS mean_estimate_usd,     -- the same averages in national dollars
       favg(lower_usd) AS mean_lower_usd,
       favg(upper_usd) AS mean_upper_usd,
       any_value(total_paid_usd) AS total_paid_usd,
       median(estimate) AS median_estimate,         -- medians over the reported audit years (25: the 13th value)
       median(lower) AS median_lower,
       median(upper) AS median_upper,
       median(estimate_usd) AS median_estimate_usd,
       median(lower_usd) AS median_lower_usd,
       median(upper_usd) AS median_upper_usd,
       favg(error) AS mean_error,                   -- average signed error (bias)
       favg(abs(error)) AS mean_abs_error,          -- average distance from the truth
       favg(rel_error) AS mean_rel_error,           -- the same, relative to the true rate
       favg(abs(rel_error)) AS mean_abs_rel_error,
       count(*) AS n_audit_years,
       count(*) FILTER (WHERE truth_in_ci = 'inside') AS n_truth_inside,
       count(*) FILTER (WHERE truth_in_ci = 'above') AS n_ci_above_truth,
       count(*) FILTER (WHERE truth_in_ci = 'below') AS n_ci_below_truth,
       count(*) FILTER (WHERE truth_in_ci = 'undefined') AS n_undefined,
       round(100.0 * count(*) FILTER (WHERE truth_in_ci = 'inside') / count(*), 1) AS pct_truth_inside
FROM by_audit_year
GROUP BY program, scenario, domain, method, "interval";
