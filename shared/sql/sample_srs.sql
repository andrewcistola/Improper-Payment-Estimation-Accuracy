-- =====================================================================
-- shared/sql/sample_srs.sql : audit years (Monte Carlo replicates), stratified SRS
-- ---------------------------------------------------------------------
-- Rule: within each stratum, simple random sampling without replacement:
-- the samp_h units with the smallest uniform key u(seed, rep, unit_id)
-- (fast integer stream: rbase per rep, u01f per unit).
-- Inputs (built by each program's estimation/sql/*01_frame.sql):
--   pop(domain, stratum, unit_id, y, x)  one row per frame unit per domain
--       domain  = what is estimated (e.g. 'national', or a PERM state and
--                 component); units in different domains with the same
--                 stratum label and unit_id are sampled identically, so
--                 components of one state share one sample
--       y, x    = DECIMAL(18,6): improper amount and amount paid
--   alloc(domain, stratum, n_h)          sample size per stratum
--   variables: seed, reps
-- Outputs:
--   sample(rep, domain, stratum, pop_h, samp_h, unit_id, y, x, w)
--   frame_totals(domain, X, Y, theta)    known totals and the true rate
-- rep = 1..reps, each an independent production sample.
-- Weight w = pop_h / samp_h.
-- NOTE: DuckDB identifiers are case-insensitive, so the textbook N_h and
-- n_h would be the SAME column; pop_h and samp_h are used instead.
-- =====================================================================

CREATE OR REPLACE TABLE strata AS
SELECT p.domain, p.stratum, count(*) AS pop_h, least(count(*), any_value(a.n_h)) AS samp_h
FROM pop p JOIN alloc a USING (domain, stratum)
GROUP BY p.domain, p.stratum;

CREATE OR REPLACE TABLE frame_totals AS
SELECT domain, sum(x)::DOUBLE AS X, sum(y)::DOUBLE AS Y, sum(y)::DOUBLE / sum(x)::DOUBLE AS theta
FROM pop GROUP BY domain;

-- Simple random sampling without replacement
CREATE OR REPLACE TABLE sample_raw AS
SELECT r.rep, p.domain, p.stratum, s.pop_h, s.samp_h, p.unit_id, p.y, p.x
FROM pop p
JOIN strata s USING (domain, stratum)
CROSS JOIN (SELECT range::INTEGER AS rep, rbase(getvariable('seed'), 'srs', range, 0) AS base
            FROM range(1, getvariable('reps') + 1)) r
QUALIFY row_number() OVER (PARTITION BY r.rep, p.domain, p.stratum
                           ORDER BY u01f(r.base, p.unit_id), p.unit_id) <= s.samp_h;

CREATE OR REPLACE TABLE sample AS
SELECT rep, domain, stratum, pop_h, samp_h, unit_id,
       y::DECIMAL(18, 6) AS y, x::DECIMAL(18, 6) AS x, pop_h::DOUBLE / samp_h AS w
FROM sample_raw;

DROP TABLE sample_raw;
