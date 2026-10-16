-- =====================================================================
-- shared/sql/sample.sql : draw Monte Carlo samples from the frame
-- ---------------------------------------------------------------------
-- Inputs (built by each program's estimation/sql/01_frame.sql):
--   pop(domain, stratum, unit_id, y, x)  one row per frame unit per domain
--       domain  = what is estimated (e.g. 'national', or a PERM state and
--                 component); units in different domains with the same
--                 stratum label and unit_id are sampled identically, so
--                 components of one state share one sample
--       y, x    = DECIMAL(18,6): improper amount and amount paid
--   alloc(domain, stratum, n_h)          sample size per stratum
--   variables: seed, reps, selection ('srs' | 'systematic')
-- Outputs:
--   sample(rep, domain, stratum, pop_h, samp_h, unit_id, y, x, w)
--   frame_totals(domain, X, Y, theta)    known totals and the true rate
-- Selection rules (rep = 1..reps, each an independent production sample):
--   srs        : without replacement within stratum; the samp_h units
--                with the smallest uniform key u(seed, rep, unit_id)
--                (fast integer stream: rbase per rep, u01f per unit)
--   systematic : units sorted by x (ties by unit_id) within stratum;
--                random start s in [0, k), k = pop_h / samp_h; units at
--                sorted positions floor(s + j*k), j = 0..samp_h-1
-- Weight w = pop_h / samp_h under both rules.
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
CREATE OR REPLACE TABLE sample_srs AS
SELECT r.rep, p.domain, p.stratum, s.pop_h, s.samp_h, p.unit_id, p.y, p.x
FROM pop p
JOIN strata s USING (domain, stratum)
CROSS JOIN (SELECT range::INTEGER AS rep, rbase(getvariable('seed'), 'srs', range, 0) AS base
            FROM range(1, getvariable('reps') + 1)) r
WHERE getvariable('selection') = 'srs'
QUALIFY row_number() OVER (PARTITION BY r.rep, p.domain, p.stratum
                           ORDER BY u01f(r.base, p.unit_id), p.unit_id) <= s.samp_h;

-- Systematic sampling after sorting by amount paid
CREATE OR REPLACE TABLE sample_sys AS
WITH sorted AS (
    SELECT p.*, s.pop_h, s.samp_h,
           row_number() OVER (PARTITION BY p.domain, p.stratum ORDER BY p.x, p.unit_id) - 1 AS pos
    FROM pop p JOIN strata s USING (domain, stratum)
    WHERE getvariable('selection') = 'systematic'
),
hits AS (
    SELECT r.rep, s.domain, s.stratum,
           floor(u01b(getvariable('seed'), 'start|' || s.stratum, r.rep, 0) * s.pop_h / s.samp_h
                 + j.j * s.pop_h / s.samp_h)::BIGINT AS pos
    FROM strata s
    CROSS JOIN (SELECT range::INTEGER AS rep FROM range(1, getvariable('reps') + 1)) r,
    LATERAL range(0, s.samp_h) j(j)
    WHERE getvariable('selection') = 'systematic'
)
SELECT h.rep, t.domain, t.stratum, t.pop_h, t.samp_h, t.unit_id, t.y, t.x
FROM hits h JOIN sorted t USING (domain, stratum, pos);

CREATE OR REPLACE TABLE sample AS
SELECT rep, domain, stratum, pop_h, samp_h, unit_id,
       y::DECIMAL(18, 6) AS y, x::DECIMAL(18, 6) AS x, pop_h::DOUBLE / samp_h AS w
FROM (SELECT * FROM sample_srs UNION ALL SELECT * FROM sample_sys);

DROP TABLE sample_srs;
DROP TABLE sample_sys;
