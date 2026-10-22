-- =====================================================================
-- cert estimation/02_sample.sql : audit years (Monte Carlo replicates)
-- ---------------------------------------------------------------------
-- Stratified SRS without replacement, the same rule as
-- shared/sql/sample_srs.sql: within each stratum, the samp_h claims with
-- the smallest key u01f(rbase(seed, 'srs', rep, 0), unit_id). The CERT
-- universe has 5.3 million claims, so instead of ranking every claim in
-- every audit year, claims are first kept only if their key is below
-- c_h = min(1, (n_h + 10 sqrt(n_h) + 50) / N_h) -- the smallest n_h keys
-- are always below c_h unless fewer than n_h claims pass, which the check
-- at the end rules out (it stops the run) -- and the survivors are
-- ranked. The result is identical to ranking every claim.
-- One sampled claim gives one row per domain (national over, under,
-- gross, net, and its claim type's gross).
-- Output: sample(rep, domain, stratum, pop_h, samp_h, unit_id, y, x, w),
--         frame_totals(domain, X, Y, theta)
-- =====================================================================
CREATE OR REPLACE TABLE strata AS
SELECT f.stratum, count(*) AS pop_h, least(count(*), any_value(a.n_h)) AS samp_h,
       least(1.0, (any_value(a.n_h) + 10 * sqrt(any_value(a.n_h)) + 50) / count(*)) AS c_h
FROM cert_frame f JOIN alloc a USING (stratum)
GROUP BY f.stratum;

CREATE OR REPLACE TABLE cert_domains AS
SELECT unit_id, claim_type, stratum, x, d.domain,
       (CASE d.measure WHEN 'over' THEN greatest(y, 0) WHEN 'under' THEN greatest(-y, 0)
                       WHEN 'gross' THEN abs(y) ELSE y END)::DECIMAL(18, 6) AS y
FROM cert_frame,
     LATERAL (SELECT 'national|' || m AS domain, m AS measure FROM unnest(['over', 'under', 'gross', 'net']) t(m)
              UNION ALL SELECT claim_type || '|gross', 'gross') d;

CREATE OR REPLACE TABLE frame_totals AS
SELECT domain, sum(x)::DOUBLE AS X, sum(y)::DOUBLE AS Y, sum(y)::DOUBLE / sum(x)::DOUBLE AS theta
FROM cert_domains GROUP BY domain;

CREATE OR REPLACE TABLE sample_units AS
WITH r AS (SELECT range::INTEGER AS rep, rbase(getvariable('seed'), 'srs', range, 0) AS base
           FROM range(1, getvariable('reps') + 1)),
k AS (SELECT r.rep, f.stratum, f.unit_id, u01f(r.base, f.unit_id) AS key, s.samp_h, s.pop_h
      FROM cert_frame f JOIN strata s USING (stratum) CROSS JOIN r
      WHERE u01f(r.base, f.unit_id) < s.c_h)
SELECT rep, stratum, unit_id, pop_h, samp_h, count(*) OVER (PARTITION BY rep, stratum) AS n_pass
FROM k
QUALIFY row_number() OVER (PARTITION BY rep, stratum ORDER BY key, unit_id) <= samp_h;

-- every stratum must have had at least samp_h claims below its cutoff
SELECT CASE WHEN count(*) = 0 THEN 'ok' ELSE error('cert sample: a stratum had too few claims below its cutoff') END
FROM (SELECT rep, stratum, any_value(samp_h) AS samp_h, count(*) AS got FROM sample_units
      GROUP BY rep, stratum HAVING count(*) < any_value(samp_h));

CREATE OR REPLACE TABLE sample AS
SELECT s.rep, d.domain, s.stratum, s.pop_h, s.samp_h, s.unit_id,
       d.y::DECIMAL(18, 6) AS y, d.x::DECIMAL(18, 6) AS x, s.pop_h::DOUBLE / s.samp_h AS w
FROM sample_units s JOIN cert_domains d USING (unit_id);

DROP TABLE cert_domains;
