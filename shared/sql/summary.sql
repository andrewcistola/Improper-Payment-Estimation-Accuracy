-- =====================================================================
-- shared/sql/summary.sql : one table of results across all programs
-- ---------------------------------------------------------------------
-- Reads every <program>/estimation/results/**/metrics.json and lists,
-- per program, scenario, domain, method and interval: true rate,
-- coverage of the 95% interval, tail balance, bias and width.
-- =====================================================================
CREATE OR REPLACE TABLE summary AS
SELECT regexp_extract(filename, '([^/]+)/estimation/results/', 1) AS program_folder,
       regexp_extract(filename, 'results/(.*)/metrics\.json$', 1) AS scenario,
       domain, method, "interval", reps, theta, coverage, mc_se_coverage, above, below,
       n_undefined, rel_bias, rel_rmse, rel_width, median_rel_width
FROM read_json(getvariable('repo_root') || '/*/estimation/results/**/metrics.json', filename = true);
