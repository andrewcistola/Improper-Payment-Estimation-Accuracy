-- =====================================================================
-- estimate/sample.sql : draw replicate samples from a population
-- ---------------------------------------------------------------------
-- Inputs : pop(unit_id, stratum, y, x)           one row per frame unit
--          alloc(stratum, n_h)                    sample size per stratum
--          variables: seed, reps, selection ('srs' | 'systematic')
-- Output : sample(rep, stratum, pop_h, samp_h, unit_id, y, x, w)
--   srs        : without replacement; the samp_h units with the smallest
--                uniform key u(seed, rep, unit) in each stratum
--   systematic : units sorted by x within stratum; random start in
--                [0, pop_h/samp_h); every (pop_h/samp_h)-th unit (fractional
--                interval, so exactly samp_h units are taken)
-- Weight w = pop_h / samp_h (Horvitz-Thompson under either design).
-- NOTE: DuckDB identifiers are case-insensitive, so the textbook names
-- N_h and n_h would be the SAME column. Use pop_h (stratum population
-- size) and samp_h (stratum sample size) instead.
-- =====================================================================
CREATE OR REPLACE TABLE strata AS
SELECT p.stratum, count(*) AS pop_h, least(count(*), any_value(a.n_h)) AS samp_h
FROM pop p JOIN alloc a USING (stratum) GROUP BY p.stratum;

CREATE OR REPLACE TABLE sample AS
WITH r AS (SELECT range AS rep FROM range(1, getvariable('reps') + 1)),
srs AS (
    SELECT r.rep, p.*, s.pop_h, s.samp_h,
           row_number() OVER (PARTITION BY r.rep, p.stratum
                              ORDER BY u01b(getvariable('seed'), 'srs', r.rep, p.unit_id), p.unit_id) AS k
    FROM pop p JOIN strata s USING (stratum), r
    WHERE getvariable('selection') = 'srs'
),
sys AS (
    SELECT r.rep, p.*, s.pop_h, s.samp_h,
           row_number() OVER (PARTITION BY r.rep, p.stratum ORDER BY p.x, p.unit_id) - 1 AS pos,
           u01b(getvariable('seed'), 'start', r.rep, hash(p.stratum)) * s.pop_h / s.samp_h AS start
    FROM pop p JOIN strata s USING (stratum), r
    WHERE getvariable('selection') = 'systematic'
)
SELECT rep, stratum, pop_h, samp_h, unit_id, y, x, pop_h::DOUBLE / samp_h AS w
FROM srs WHERE k <= samp_h
UNION ALL
SELECT rep, stratum, pop_h, samp_h, unit_id, y, x, pop_h::DOUBLE / samp_h AS w
FROM sys
-- sorted position pos (0-based) is selected when some j >= 0 has
-- start + j*k in [pos, pos+1), k = pop_h/samp_h; this takes exactly samp_h units
WHERE greatest(0, ceil((pos + 1 - start) * samp_h / pop_h)) - greatest(0, ceil((pos - start) * samp_h / pop_h)) = 1;
