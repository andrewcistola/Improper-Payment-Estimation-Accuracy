-- =====================================================================
-- perm estimation/perm_01_frame.sql : estimands and production design
-- ---------------------------------------------------------------------
-- One state per scenario (states are sampled independently in PERM).
-- Estimands, one per component (domain = 'state|component'):
--   theta = sum y*fmap / sum x*fmap   (federal share)
--   overall     : y = whole payment if eligibility is in error, else the
--                 claims error (= claims + eligibility - overlap)
--   eligibility : y = whole payment if eligibility is in error
--   claims      : y = claims-review error
-- Design: each state sampled independently; within state, quarter,
-- payment type and payment-size stratum, systematic selection after
-- sorting by amount paid. Per state and year: FFS 400 (20 per stratum),
-- MC 120 (6 per stratum). All components of a state use the same sample
-- (eligibility cases are attached to sampled payments).
-- Output: pop, alloc  (input to shared/sql/sample_systematic.sql)
-- =====================================================================
CREATE OR REPLACE TABLE perm_frame AS
SELECT *
FROM read_parquet(getvariable('repo_root') || '/' || getvariable('population_dir') || '/population.parquet')
WHERE state_id = getvariable('state_id');

CREATE OR REPLACE TABLE pop AS
SELECT state_id || '|' || c.component AS domain, stratum, unit_id,
       (CASE c.component WHEN 'overall' THEN y WHEN 'eligibility' THEN y_elig ELSE y_claims END
        * fmap)::DECIMAL(18, 6) AS y,
       (x * fmap)::DECIMAL(18, 6) AS x
FROM perm_frame,
     (SELECT unnest(from_json(getvariable('components')::JSON, '["VARCHAR"]')) AS component) c;

CREATE OR REPLACE TABLE alloc AS
SELECT DISTINCT p.domain, p.stratum,
       CASE WHEN payment_type = 'FFS' THEN getvariable('n_ffs_per_stratum')
            ELSE getvariable('n_mc_per_stratum') END AS n_h
FROM pop p JOIN perm_frame f USING (unit_id);
