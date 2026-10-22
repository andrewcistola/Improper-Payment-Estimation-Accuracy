-- =====================================================================
-- partc estimation/10_expansion.sql : risk-score expansion
-- ---------------------------------------------------------------------
-- Part C expansion works in risk score units, then prices them with one
-- national average county rate:
--   d_i   = audited enrollee's risk score error (original - validated)
--   r_i   = the part of d_i that the domain measures:
--             over  max(d_i, 0)      under max(-d_i, 0)
--             gross |d_i|            net   d_i
--   c_bar = national average annual county rate
--         = average over ALL enrollees of (monthly county rate x months)
--   z_i   = r_i x c_bar             (dollars per audited enrollee)
--   T     = sum_h N_h x mean_h(z)   (improper dollars, terciles h)
--   V(T)  = sum_h N_h^2 (1 - n_h/N_h) s_h^2(z) / n_h
--           (a stratum with one audited unit contributes 0 variance, the
--           same guard as ipm_moments in shared/sql/lib/02_estimators.sql;
--           fsd would otherwise divide by n_h - 1 = 0)
--   estimate = T / X, se = sqrt(V) / X, 95% interval = (T +- 1.96 sqrt(V)) / X
-- X = KNOWN total Part C payments. Dollars and their interval are formed
-- first and then divided by X, so the rate and the dollars agree.
-- =====================================================================
CREATE OR REPLACE TABLE partc_risk_error AS
SELECT unit_id, delta_r::DOUBLE AS d
FROM read_parquet(getvariable('repo_root') || '/' || getvariable('population_dir') || '/population.parquet');

CREATE OR REPLACE TABLE partc_avg_rate AS
SELECT favg(county_rate::DOUBLE * months) AS c_bar
FROM read_parquet(getvariable('repo_root') || '/' || getvariable('population_dir') || '/population.parquet');

CREATE OR REPLACE TABLE est_expansion AS
WITH z AS (
    SELECT s.rep, s.domain, s.stratum, s.pop_h::DOUBLE AS big_n, s.samp_h::DOUBLE AS small_n,
           (CASE split_part(s.domain, '|', 2) WHEN 'over'  THEN greatest(r.d, 0)
                                              WHEN 'under' THEN greatest(-r.d, 0)
                                              WHEN 'gross' THEN abs(r.d)
                                              ELSE r.d END) * c.c_bar AS z
    FROM sample s JOIN partc_risk_error r USING (unit_id), partc_avg_rate c
),
h AS (
    SELECT rep, domain, stratum, any_value(big_n) AS big_n, any_value(small_n) AS small_n,
           favg(z) AS z_bar,
           CASE WHEN count(*) > 1 THEN fsd(z) ELSE 0.0 END AS s_z
    FROM z GROUP BY rep, domain, stratum
),
t AS (
    SELECT rep, domain,
           fsum(big_n * z_bar) AS t_y,
           fsum(big_n * big_n * (1 - small_n / big_n) * s_z * s_z / small_n) AS v_t
    FROM h GROUP BY rep, domain
)
SELECT 'expansion' AS method, 'normal' AS interval, t.rep, t.domain,
       t.t_y / f.X AS estimate, sqrt(t.v_t) / f.X AS se,
       (t.t_y - q.z * sqrt(t.v_t)) / f.X AS lower,
       (t.t_y + q.z * sqrt(t.v_t)) / f.X AS upper
FROM t JOIN frame_totals f USING (domain), (SELECT norm_ppf(1 - getvariable('alpha') / 2) AS z) q;
