-- =====================================================================
-- partc errors/03_payments.sql : risk scores and payments (no errors)
-- ---------------------------------------------------------------------
-- Risk score (submitted)  R0 = demo_score + sum(coef_paid)
-- Annual payment          x  = R0 * county_rate * months
-- County rates are scaled once so that the weighted payments equal the
-- FY 2025 Part C total (payment_target).
-- Output: enr_score (one row per enrollee, error-free)
-- =====================================================================

-- Step 3. Scale county rates so weighted payments hit payment_target
-- (Part C national total).
CREATE OR REPLACE TABLE enr_score AS
SELECT e.*, round(e.demo_score + coalesce(h.sum_coef, 0), 3)::DECIMAL(8, 3) AS risk_orig,
       coalesce(h.n_hcc, 0) AS n_hcc
FROM enrollees e
LEFT JOIN (SELECT enrollee_id, sum(coef_paid) AS sum_coef, count(*) AS n_hcc
           FROM hccs GROUP BY enrollee_id) h USING (enrollee_id);

CREATE OR REPLACE TABLE rate_factor AS
SELECT getvariable('payment_target')
       / (getvariable('w_pop') * sum((risk_orig * county_rate_raw * months)::DECIMAL(38, 6))::DOUBLE) AS f
FROM enr_score;

CREATE OR REPLACE TABLE enr_score AS
SELECT s.*, round(s.county_rate_raw * f.f, 2)::DECIMAL(10, 2) AS county_rate
FROM enr_score s, rate_factor f;
