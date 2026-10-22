-- =====================================================================
-- partc errors/04_apply_errors.sql : apply fake errors, Delta-R
-- ---------------------------------------------------------------------
-- Input: the error-free population from steps 01-03 (enrollees, hccs,
-- enr_score). This step only adds errors.
-- Error mechanisms (each a Bernoulli draw with a stated probability):
--   unsupported HCC  p = p_unsup(fam) * intensity(contract)
--                        * (3 if chart-review sourced) * m_unsup
--     - if severe, half of unsupported HCCs are hierarchy moves
--       (partial error: severe - mild); otherwise deleted (full coef)
--   missing documentation (enrollee with >= 1 HCC): p = p_md * m_md;
--     all HCCs deleted (all-or-nothing on the HCC part of the score)
--   additional HCC (underpayment): p = p_add * m_add, only for enrollees
--     with no overpayment; adds the mild coef of a family not coded
-- Payment-size dependence (size_beta, default 0.0 = none): the
--   unsupported-HCC and missing-documentation probabilities of enrollee i
--   are multiplied by s_i = (x_i / mean x in i's risk-score tercile)^size_beta,
--   x_i = R0 x county rate x months (the enrollee's payment), and the
--   result is capped at 0.95 as before. s_i enters the calibration
--   expectations too, so the multipliers still hit the targets with the
--   per-unit probabilities. size_beta = 0 gives s_i = 1.0 exactly and
--   reproduces the base population byte for byte.
-- Delta-R = R0 - R_validated (positive = overpayment), where R_validated
-- is the score supported by the medical record; payment error
-- y = Delta-R * county_rate * months.
-- Calibration: each multiplier m is ONE closed-form ratio, target dollars
-- / expected dollars at m = 1. Realized rates then match the targets up
-- to sampling noise; both are written to truth.json.
-- =====================================================================

-- Base probability that a submitted HCC lacks record support, by family,
-- before contract intensity, the chart-review factor and m_unsup.
CREATE OR REPLACE TABLE hcc_unsupported_rates AS
SELECT * FROM (VALUES
    ('A', 0.040),
    ('B', 0.050),
    ('C', 0.060),
    ('D', 0.100),
    ('E', 0.050),
    ('F', 0.120),
    ('G', 0.080),
    ('H', 0.150),
    ('I', 0.070),
    ('J', 0.110)
) t(fam, p_unsup);

-- Payment-size factor s_i = (x_i / tercile mean x)^size_beta. Terciles of
-- the original risk score, the same cut as the strata in 05 (ntile(3)
-- ORDER BY risk_orig, enrollee_id). Tercile means use favg (sorted sum)
-- so the factor is reproducible at any thread count.
CREATE OR REPLACE TABLE size_factor AS
WITH t AS (
    SELECT enrollee_id, risk_orig * county_rate * months AS x_raw,
           ntile(3) OVER (ORDER BY risk_orig, enrollee_id) AS tercile
    FROM enr_score),
     m AS (SELECT tercile, favg(x_raw) AS x_bar FROM t GROUP BY tercile)
SELECT t.enrollee_id, power(t.x_raw / m.x_bar, getvariable('size_beta')::DOUBLE) AS s
FROM t JOIN m USING (tercile);

-- Step 4. Base (m = 1) probabilities and expected error dollars.
CREATE OR REPLACE TABLE hcc_p AS
SELECT h.*, r.p_unsup, c.intensity, e.county_rate, e.months,
       r.p_unsup * c.intensity * CASE WHEN h.chart_review THEN 3.0 ELSE 1.0 END * sf.s AS p1,
       CASE WHEN h.severe THEN h.coef_severe - 0.5 * h.coef_mild ELSE h.coef_mild END AS exp_err_coef
FROM hccs h
JOIN hcc_unsupported_rates r USING (fam)
JOIN contracts c USING (contract_id)
JOIN enr_score e USING (enrollee_id)
JOIN size_factor sf USING (enrollee_id);

-- Per-enrollee missing-documentation base probability (before m_md).
CREATE OR REPLACE TABLE enr_score AS
SELECT e.*, getvariable('p_md') * sf.s AS p_md_i
FROM enr_score e JOIN size_factor sf USING (enrollee_id);

CREATE OR REPLACE TABLE multipliers AS
WITH tot AS (SELECT sum(risk_orig * county_rate * months)::DOUBLE AS X FROM enr_score),
     eu AS (SELECT sum((p1 * exp_err_coef * county_rate * months)::DECIMAL(38, 6))::DOUBLE AS e FROM hcc_p),
     em AS (SELECT sum((p_md_i * (risk_orig - demo_score) * county_rate * months)::DECIMAL(38, 6))::DOUBLE AS e
            FROM enr_score WHERE n_hcc > 0)
SELECT getvariable('target_unsup') * tot.X / eu.e AS m_unsup,
       getvariable('target_md')    * tot.X / em.e AS m_md,
       1.0 AS m_add
FROM tot, eu, em;

-- m_add uses the exact expected underpayment given the rules in Step 6:
-- an additional HCC counts only if (a) its family is not already coded
-- and (b) the enrollee has no overpayment. P(no overpayment) is computed
-- from the already-calibrated m_unsup and m_md.
CREATE OR REPLACE TABLE multipliers AS
WITH tot AS (SELECT sum(risk_orig * county_rate * months)::DOUBLE AS X FROM enr_score),
     p_over AS (
        SELECT h.enrollee_id,
               1 - exp(sum(ln(1 - least(0.95, h.p1 * m.m_unsup))::DECIMAL(38, 12))::DOUBLE) AS p_unsup_any
        FROM hcc_p h, multipliers m GROUP BY h.enrollee_id),
     absent AS (  -- expected mild coef of a drawn family that is not already coded
        SELECT e.enrollee_id,
               sum((f.prevalence * f.coef_mild)::DECIMAL(38, 12))::DOUBLE / (SELECT sum(prevalence) FROM hcc_families) AS exp_add_coef
        FROM enr_score e CROSS JOIN hcc_families f
        ANTI JOIN hccs h ON h.enrollee_id = e.enrollee_id AND h.fam = f.fam
        GROUP BY e.enrollee_id),
     ea AS (
        SELECT sum((getvariable('p_add') * a.exp_add_coef
                   * (1 - coalesce(o.p_unsup_any, 0))
                   * (1 - CASE WHEN e.n_hcc > 0 THEN least(0.95, e.p_md_i * m.m_md) ELSE 0 END)
                   * e.county_rate * e.months)::DECIMAL(38, 6))::DOUBLE AS e
        FROM enr_score e
        JOIN absent a USING (enrollee_id)
        LEFT JOIN p_over o USING (enrollee_id), multipliers m)
SELECT round(m.m_unsup, 8) AS m_unsup, round(m.m_md, 8) AS m_md,
       round(getvariable('target_under') * tot.X / ea.e, 8) AS m_add
FROM multipliers m, tot, ea;

-- Step 5. Realized HCC-level errors.
CREATE OR REPLACE TABLE hccs AS
SELECT h.enrollee_id, h.contract_id, h.fam, h.severe, h.chart_review,
       h.coef_mild, h.coef_severe, h.coef_paid,
       round(least(0.95, h.p1 * m.m_unsup), 8) AS p_unsupported,
       u01b(getvariable('seed'), 'unsup', h.enrollee_id, h.fam) < least(0.95, h.p1 * m.m_unsup) AS unsupported,
       h.severe AND u01b(getvariable('seed'), 'move', h.enrollee_id, h.fam) < 0.5 AS move_if_unsupported
FROM hcc_p h, multipliers m;

CREATE OR REPLACE TABLE hccs AS
SELECT *,
       CASE WHEN NOT unsupported THEN 'supported'
            WHEN move_if_unsupported THEN 'hierarchy_move'
            ELSE 'deleted' END AS validation,
       CASE WHEN NOT unsupported THEN 0
            WHEN move_if_unsupported THEN coef_severe - coef_mild
            ELSE coef_paid END AS err_coef
FROM hccs;

-- Step 6. Enrollee-level: missing documentation, additional HCC, Delta-R.
CREATE OR REPLACE TABLE enr_err AS
SELECT e.*,
       coalesce(h.err_coef, 0) AS hcc_err,
       coalesce(h.n_deleted, 0) AS n_deleted,
       coalesce(h.n_moved, 0) AS n_moved,
       e.n_hcc > 0 AND u01(getvariable('seed'), 'md', e.enrollee_id) < least(0.95, e.p_md_i * m.m_md)
           AS missing_doc,
       u01(getvariable('seed'), 'add', e.enrollee_id) < least(0.95, getvariable('p_add') * m.m_add) AS add_draw,
       u01(getvariable('seed'), 'add_fam', e.enrollee_id) AS u_add_fam
FROM enr_score e
LEFT JOIN (SELECT enrollee_id, sum(err_coef) AS err_coef,
                  count(*) FILTER (WHERE validation = 'deleted') AS n_deleted,
                  count(*) FILTER (WHERE validation = 'hierarchy_move') AS n_moved
           FROM hccs GROUP BY enrollee_id) h USING (enrollee_id),
     multipliers m;

CREATE OR REPLACE TABLE enr_err AS
SELECT e.*, f.fam AS add_fam,
       CASE WHEN e.add_draw AND NOT e.missing_doc AND e.hcc_err = 0 AND h.fam IS NULL
            THEN f.coef_mild ELSE 0 END AS add_coef
FROM enr_err e
JOIN fam_bounds f ON e.u_add_fam >= f.lo AND e.u_add_fam < f.hi
LEFT JOIN hccs h ON h.enrollee_id = e.enrollee_id AND h.fam = f.fam;

CREATE OR REPLACE TABLE capitation_units AS
SELECT enrollee_id AS unit_id, contract_id, months, county_rate, demo_score, n_hcc,
       risk_orig,
       round(CASE WHEN missing_doc THEN risk_orig - demo_score ELSE hcc_err END - add_coef, 3)::DECIMAL(8, 3) AS delta_r,
       CASE WHEN missing_doc THEN 'missing_documentation'
            WHEN n_deleted > 0 THEN 'unsupported_hcc'
            WHEN n_moved > 0 THEN 'hierarchy_move'
            WHEN add_coef > 0 THEN 'additional_hcc'
            ELSE 'none' END AS error_type,
       missing_doc,                                         -- enrollee-level finding
       CASE WHEN add_coef > 0 THEN add_fam END AS add_fam,  -- additional HCC found (family)
       add_coef::DECIMAL(4, 3) AS add_coef
FROM enr_err;

CREATE OR REPLACE TABLE capitation_units AS
SELECT *, (risk_orig - delta_r)::DECIMAL(8, 3) AS risk_validated,
       usd(risk_orig * county_rate * months) AS x,
       usd(delta_r * county_rate * months) AS y,
       getvariable('w_pop')::DOUBLE AS w_pop
FROM capitation_units;
