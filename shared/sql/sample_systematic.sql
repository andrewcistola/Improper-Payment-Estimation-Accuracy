-- =====================================================================
-- shared/sql/sample_systematic.sql : audit years (Monte Carlo replicates), systematic
-- ---------------------------------------------------------------------
-- Rule: within each stratum, units sorted by amount paid x (ties by
-- unit_id); random start s in [0, k), k = pop_h / samp_h; units at sorted
-- positions floor(s + j*k), j = 0..samp_h-1 (exactly samp_h units).
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

-- Systematic sampling after sorting by amount paid
CREATE OR REPLACE TABLE sample_raw AS
WITH sorted AS (
    SELECT p.*, s.pop_h, s.samp_h,
           row_number() OVER (PARTITION BY p.domain, p.stratum ORDER BY p.x, p.unit_id) - 1 AS pos
    FROM pop p JOIN strata s USING (domain, stratum)
),
hits AS (
    SELECT r.rep, s.domain, s.stratum,
           floor(u01b(getvariable('seed'), 'start|' || s.stratum, r.rep, 0) * s.pop_h / s.samp_h
                 + j.j * s.pop_h / s.samp_h)::BIGINT AS pos
    FROM strata s
    CROSS JOIN (SELECT range::INTEGER AS rep FROM range(1, getvariable('reps') + 1)) r,
    LATERAL range(0, s.samp_h) j(j)
)
SELECT h.rep, t.domain, t.stratum, t.pop_h, t.samp_h, t.unit_id, t.y, t.x
FROM hits h JOIN sorted t USING (domain, stratum, pos);

CREATE OR REPLACE TABLE sample AS
SELECT rep, domain, stratum, pop_h, samp_h, unit_id,
       y::DECIMAL(18, 6) AS y, x::DECIMAL(18, 6) AS x, pop_h::DOUBLE / samp_h AS w
FROM sample_raw;

DROP TABLE sample_raw;
