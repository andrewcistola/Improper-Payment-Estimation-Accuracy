-- =====================================================================
-- partc estimation/40_simulation_inputs.sql : inputs for the simulation
-- ---------------------------------------------------------------------
-- The audit-finding simulation (simulation.py) needs every enrollee and
-- every submitted HCC in the population, with -- for audited enrollees --
-- what record review found:
--   HCC level      : supported / deleted / hierarchy move (hcc_detail)
--   enrollee level : missing documentation; additional HCC found
-- Coefficients are in thousandths (integers) and dollars in cents so the
-- payment function reproduces errors/ exactly.
--   sim_units    : one row per enrollee (unit index = position)
--   sim_rows     : one row per enrollee x HCC family, sorted by enrollee
--   sim_families : family code -> mild coefficient (for additional HCCs)
-- Donor kinds: HCC = (risk stratum, family, severity), falling back to
-- (family, severity); enrollee finding = (risk stratum, has any HCC).
-- =====================================================================
CREATE OR REPLACE TABLE sim_families AS
SELECT fam, row_number() OVER (ORDER BY fam) - 1 AS fam_code,
       (any_value(coef_mild) * 1000)::BIGINT AS mild_milli
FROM read_parquet(getvariable('repo_root') || '/' || getvariable('population_dir') || '/hcc_detail.parquet')
GROUP BY fam;

CREATE OR REPLACE TABLE sim_units AS
SELECT row_number() OVER (ORDER BY p.unit_id) - 1 AS unit_idx, p.unit_id, p.stratum,
       CASE p.stratum WHEN 'low' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END AS stratum_code,
       (p.demo_score * 1000)::BIGINT AS demo_milli, (p.risk_orig * 1000)::BIGINT AS r0_milli,
       (p.county_rate * 100)::BIGINT AS rate_cents, p.months,
       (p.x * 100)::BIGINT AS x_cents, (p.y * 100)::BIGINT AS y_cents,
       p.n_hcc > 0 AS has_hcc,
       p.missing_doc, coalesce(f.fam_code, -1) AS add_fam_code
FROM read_parquet(getvariable('repo_root') || '/' || getvariable('population_dir') || '/population.parquet') p
LEFT JOIN sim_families f ON f.fam = p.add_fam
ORDER BY p.unit_id;

CREATE OR REPLACE TABLE sim_rows AS
SELECT u.unit_idx, f.fam_code, h.severe,
       (h.coef_paid * 1000)::BIGINT AS paid_milli,
       ((h.coef_severe - h.coef_mild) * 1000)::BIGINT AS move_milli,
       CASE h.validation WHEN 'supported' THEN 0 WHEN 'deleted' THEN 1 ELSE 2 END AS outcome,
       (u.stratum_code * 10 + f.fam_code) * 2 + h.severe::INT AS kind,
       f.fam_code * 2 + h.severe::INT AS fallback
FROM read_parquet(getvariable('repo_root') || '/' || getvariable('population_dir') || '/hcc_detail.parquet') h
JOIN sim_units u ON u.unit_id = h.enrollee_id
JOIN sim_families f USING (fam)
ORDER BY u.unit_idx, f.fam_code;
