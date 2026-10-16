-- =====================================================================
-- partc/02_enrollees_hccs.sql : enrollees and submitted HCCs
-- ---------------------------------------------------------------------
-- HCC families are ILLUSTRATIVE (labels A-J), not CMS-HCC coefficients.
-- Each family has a mild and a severe level (a two-level hierarchy): if
-- both are coded, only the severe one pays. A hierarchy move (severe ->
-- mild) is therefore a partial error of (severe - mild).
-- p_unsup = base probability that a submitted HCC lacks record support,
-- before contract intensity and the chart-review factor.
-- =====================================================================

CREATE OR REPLACE TABLE hcc_families AS
SELECT * FROM (VALUES
 --  fam  prevalence  mild    severe  p_unsup
    ('A', 0.22,       0.105,  0.302,  0.040),
    ('B', 0.14,       0.191,  0.360,  0.050),
    ('C', 0.12,       0.250,  0.421,  0.060),
    ('D', 0.10,       0.299,  0.598,  0.100),
    ('E', 0.09,       0.318,  0.465,  0.050),
    ('F', 0.08,       0.155,  0.350,  0.120),
    ('G', 0.08,       0.209,  0.511,  0.080),
    ('H', 0.07,       0.330,  0.903,  0.150),
    ('I', 0.06,       0.441,  0.612,  0.070),
    ('J', 0.04,       0.598,  1.012,  0.110)
) t(fam, prevalence, coef_mild, coef_severe, p_unsup);

-- cumulative prevalence bounds for categorical draws
CREATE OR REPLACE TABLE fam_bounds AS
SELECT *, sum(prevalence) OVER (ORDER BY fam) / sum(prevalence) OVER () AS hi,
          (sum(prevalence) OVER (ORDER BY fam) - prevalence) / sum(prevalence) OVER () AS lo
FROM hcc_families;

-- Step 1. Enrollees: enrollee_id = contract_id * 10,000,000 + i
CREATE OR REPLACE TABLE enrollees AS
SELECT c.contract_id,
       c.contract_id * 10000000 + t.i AS enrollee_id,
       CASE WHEN u01(getvariable('seed'), 'full_year', c.contract_id * 10000000 + t.i) < 0.85 THEN 12
            ELSE 1 + floor(11 * u01(getvariable('seed'), 'months', c.contract_id * 10000000 + t.i))::INT
       END AS months,
       c.county_rate_base * exp(0.08 * rnorm(getvariable('seed'), 'county', c.contract_id * 10000000 + t.i))
           AS county_rate_raw,
       round(0.35 + 0.30 * rkuma(getvariable('seed'), 'demo', c.contract_id * 10000000 + t.i, 2.0, 3.0), 3)::DECIMAL(8, 3)
           AS demo_score,
       rcount(getvariable('seed'), 'n_hcc', c.contract_id * 10000000 + t.i, 0.2, 1.0, 0) AS n_draws
FROM contracts c, LATERAL range(1, c.enrollment + 1) t(i);

-- Step 2. Draw n_draws HCC families per enrollee; keep one row per
-- family at its most severe drawn level (hierarchy applied).
CREATE OR REPLACE TABLE hccs AS
WITH draws AS (
    SELECT e.enrollee_id, e.contract_id, d.j,
           u01b(getvariable('seed'), 'fam', e.enrollee_id, d.j) AS u_fam,
           u01b(getvariable('seed'), 'sev', e.enrollee_id, d.j) < 0.35 AS severe,
           u01b(getvariable('seed'), 'chart', e.enrollee_id, d.j) < 0.15 AS chart_review
    FROM enrollees e, LATERAL range(1, e.n_draws + 1) d(j)
)
SELECT d.enrollee_id, d.contract_id, f.fam,
       bool_or(d.severe) AS severe,
       bool_or(d.chart_review) AS chart_review   -- any chart-review-sourced instance
FROM draws d JOIN fam_bounds f ON d.u_fam >= f.lo AND d.u_fam < f.hi
GROUP BY d.enrollee_id, d.contract_id, f.fam;

CREATE OR REPLACE TABLE hccs AS
SELECT h.*, f.coef_mild, f.coef_severe, f.p_unsup,
       CASE WHEN h.severe THEN f.coef_severe ELSE f.coef_mild END AS coef_paid
FROM hccs h JOIN hcc_families f USING (fam);
