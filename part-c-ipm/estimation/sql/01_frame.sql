-- =====================================================================
-- partc estimation/01_frame.sql : estimands and production design
-- ---------------------------------------------------------------------
-- Estimands, one domain each, all over every enrollee and divided by the
-- KNOWN total Part C payments X:
--   national|over  : y = overpayment  = max(payment error, 0)
--   national|under : y = underpayment = max(-payment error, 0)
--   national|gross : y = |payment error|           (= over + under)
--   national|net   : y = payment error             (= over - under)
-- payment error = enrollee risk score error x county rate x months
-- (errors/), so an enrollee is an overpayment or an underpayment by the
-- sign of its net risk score change. x = enrollee payment.
-- Design: stratified SRS of enrollees within national terciles of the
-- original risk score (low / medium / high); 330 per tercile (990 total)
-- from config. All four domains share one sample (same stratum and
-- unit_id, so shared/sql/sample_srs.sql draws the same enrollees).
-- Output: pop, alloc  (input to shared/sql/sample_srs.sql)
-- =====================================================================
CREATE OR REPLACE TABLE pop AS
SELECT 'national|' || m.measure AS domain, p.stratum, p.unit_id,
       (CASE m.measure WHEN 'over'  THEN greatest(p.y, 0)
                       WHEN 'under' THEN greatest(-p.y, 0)
                       WHEN 'gross' THEN abs(p.y)
                       ELSE p.y END)::DECIMAL(18, 6) AS y,
       p.x::DECIMAL(18, 6) AS x
FROM read_parquet(getvariable('repo_root') || '/' || getvariable('population_dir') || '/population.parquet') p,
     (SELECT unnest(['over', 'under', 'gross', 'net']) AS measure) m;

CREATE OR REPLACE TABLE alloc AS
SELECT 'national|' || m.measure AS domain, a.stratum, a.n_h
FROM (SELECT unnest(from_json(getvariable('allocation')::JSON,
                              '[{"stratum":"VARCHAR","n_h":"BIGINT"}]'), recursive := true)) a,
     (SELECT unnest(['over', 'under', 'gross', 'net']) AS measure) m;
