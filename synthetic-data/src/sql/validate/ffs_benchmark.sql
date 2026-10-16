-- =====================================================================
-- validate/ffs_benchmark.sql : Edwards, Liu & Delage (2023) Fig. 4.1
-- ---------------------------------------------------------------------
-- Purpose: check that the synthetic payment shapes reproduce a published
-- result. It reuses the paper's design (one-sided 90% bound) only for
-- that check; it is not part of the study's estimands.
-- For each FFS stress population: R simple random samples of n without
-- replacement; expansion estimate; one-sided 90% normal lower bound with
-- FPC; coverage = share of samples whose bound <= true total.
-- Expected: right-skewed stays near 90%; two-spike and left-skewed fall
-- below 90% once the error rate exceeds about 0.6.
-- Variables: seed, reps, n, pop_glob
-- =====================================================================

CREATE OR REPLACE TABLE pops AS
SELECT regexp_extract(filename, 'ffs_stress/([^/]+)/population', 1) AS scen,
       unit_id, y::DOUBLE AS y
FROM read_parquet(getvariable('pop_glob'), filename = true);

CREATE OR REPLACE TABLE sizes AS
SELECT scen, count(*) AS N, sum(y) AS T FROM pops GROUP BY scen;

-- Unit ids are 1..N and shared across error rates of one shape, so one
-- set of samples per population size is reused across the error grid
-- (common random numbers: differences between rates are not MC noise).
CREATE OR REPLACE TABLE draws AS
SELECT s.N, t.r, unnest(min_by(u.i, u01b(getvariable('seed'), 'srs', t.r, u.i), getvariable('n'))) AS unit_id
FROM (SELECT DISTINCT N FROM sizes) s,
     range(getvariable('reps')) t(r),
     LATERAL range(1, s.N + 1) u(i)
GROUP BY s.N, t.r;

CREATE OR REPLACE TABLE est AS
SELECT z.scen, d.r, z.N, z.T,
       z.N * avg(p.y) AS t_hat,
       z.N * avg(p.y)
         - 1.2815515655446004 * z.N * stddev_samp(p.y) / sqrt(getvariable('n'))
           * sqrt(1.0 - getvariable('n') / z.N) AS lb
FROM sizes z
JOIN draws d ON d.N = z.N
JOIN pops p ON p.scen = z.scen AND p.unit_id = d.unit_id
GROUP BY z.scen, d.r, z.N, z.T;

CREATE OR REPLACE TABLE benchmark AS
SELECT scen,
       regexp_extract(scen, '^(right|two_spike|left)_', 1) AS shape,
       regexp_extract(scen, '_p([0-9.]+)$', 1)::DOUBLE AS error_rate,
       avg((lb <= T)::INT) AS coverage,
       sqrt(avg((lb <= T)::INT) * (1 - avg((lb <= T)::INT)) / count(*)) AS mc_se,
       avg(t_hat) / any_value(T) - 1 AS rel_bias,
       count(*) AS reps
FROM est GROUP BY scen ORDER BY shape, error_rate;
