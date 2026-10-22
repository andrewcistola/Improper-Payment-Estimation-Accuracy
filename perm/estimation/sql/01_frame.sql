-- =====================================================================
-- perm estimation/01_frame.sql : estimands and production design
-- ---------------------------------------------------------------------
-- One state per scenario (states are sampled independently in PERM).
-- Estimands, one per component (domain = 'state|component'):
--   theta = sum y*fmap / sum x*fmap   (federal share)
--   gross       : y = whole payment if eligibility is in error, else the
--                 claims error (= claims + eligibility - overlap). Every
--                 PERM error is an overpayment, so gross = over = net.
--   eligibility : y = whole payment if eligibility is in error
--   claims      : y = claims-review error
-- Design: each state sampled independently; strata = payment type (FFS,
-- MC) x five equal-count quintiles of the amount paid (10 per state);
-- systematic selection after sorting by amount paid within stratum.
-- Neyman allocation of audit_size (520) payments per state-year:
--   n_h ~ N_h x S_h, S_h = standard deviation of the payment's gross
--   improper dollars in stratum h (from the population, standing in for
--   prior-year data); integers by largest remainder, at least 2 per
--   stratum. All components use the same sample (eligibility cases are
--   attached to sampled payments).
-- Output: pop, alloc  (input to shared/sql/sample_systematic.sql)
-- =====================================================================
CREATE OR REPLACE TABLE perm_frame AS
SELECT *
FROM read_parquet(getvariable('repo_root') || '/' || getvariable('population_dir') || '/population.parquet')
WHERE state_id = getvariable('state_id');

CREATE OR REPLACE TABLE pop AS
SELECT state_id || '|' || c.component AS domain, stratum, unit_id,
       (CASE c.component WHEN 'gross' THEN y WHEN 'eligibility' THEN y_elig ELSE y_claims END
        * fmap)::DECIMAL(18, 6) AS y,
       (x * fmap)::DECIMAL(18, 6) AS x
FROM perm_frame,
     (SELECT unnest(from_json(getvariable('components')::JSON, '["VARCHAR"]')) AS component) c;

-- Neyman allocation per stratum (same for every component)
CREATE OR REPLACE TABLE perm_neyman AS
WITH s AS (SELECT stratum, count(*) AS big_n, stddev_pop((y * fmap)::DOUBLE) AS s_h FROM perm_frame GROUP BY stratum),
raw AS (SELECT *, getvariable('audit_size') * big_n * s_h / sum(big_n * s_h) OVER () AS n_raw FROM s),
fl AS (SELECT *, floor(n_raw)::BIGINT AS n_floor,
              row_number() OVER (ORDER BY n_raw - floor(n_raw) DESC, stratum) AS rk FROM raw),
lr AS (SELECT *, n_floor + CASE WHEN rk <= getvariable('audit_size') - sum(n_floor) OVER () THEN 1 ELSE 0 END AS n_lr FROM fl),
mn AS (SELECT *, greatest(n_lr, 2) AS n_min FROM lr),
big AS (SELECT stratum FROM mn ORDER BY n_min DESC, stratum LIMIT 1)   -- any units added by the minimum
SELECT stratum, big_n, s_h,                                            -- come out of the largest stratum
       n_min - CASE WHEN stratum = (SELECT stratum FROM big)
                    THEN (SELECT sum(n_min) FROM mn) - getvariable('audit_size') ELSE 0 END AS n_h
FROM mn;

CREATE OR REPLACE TABLE alloc AS
SELECT DISTINCT p.domain, p.stratum, n.n_h::BIGINT AS n_h
FROM pop p JOIN perm_neyman n USING (stratum);
