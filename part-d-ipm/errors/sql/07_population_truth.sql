-- =====================================================================
-- partd errors/07_population_truth.sql : beneficiary population and truth
-- ---------------------------------------------------------------------
-- x (paid)  = direct subsidy + reinsurance + LICS for the beneficiary
--             (direct subsidy set so weighted x sums to payment_target)
-- y (error) = Medicare(submitted PDEs) - Medicare(corrected PDEs)
-- =====================================================================
UPDATE calib SET realized_gross = (SELECT sum(abs(medicare_pde_sub - medicare_pde_cor))::DOUBLE FROM bene_pay)
WHERE pass = (SELECT max(pass) FROM calib);

CREATE OR REPLACE TABLE direct_subsidy AS
SELECT usd((getvariable('payment_target') / getvariable('w_pop') - sum(medicare_pde_sub)::DOUBLE) / count(*)) AS ds
FROM bene_pay;

CREATE OR REPLACE TABLE population AS
WITH t AS (
    SELECT bene_id,
           CASE WHEN bool_or(error_type = 'full_error') THEN 'full_error'
                WHEN bool_or(error_type = 'partial_error') THEN 'partial_error'
                ELSE 'none' END AS error_type
    FROM pde_versions WHERE version = 'submitted' GROUP BY bene_id
)
SELECT p.bene_id AS unit_id, 'all' AS stratum, e.lis, e.ltc, e.n_pde,
       p.gdc_sub, p.gdc_cor, p.reins_sub, p.lics_sub, p.reached_catastrophic, p.n_err_pde,
       d.ds AS direct_subsidy,
       (d.ds + p.medicare_pde_sub)::DECIMAL(18, 2) AS x,
       (p.medicare_pde_sub - p.medicare_pde_cor)::DECIMAL(18, 2) AS y,
       CASE WHEN p.medicare_pde_sub = p.medicare_pde_cor AND t.error_type <> 'none'
            THEN t.error_type || '_no_payment_effect' ELSE t.error_type END AS error_type,
       getvariable('w_pop')::DOUBLE AS w_pop
FROM bene_pay p JOIN benes e USING (bene_id) JOIN t USING (bene_id), direct_subsidy d;

-- PDE-level trace: submitted vs corrected liability for every PDE
CREATE OR REPLACE TABLE pde_detail AS
SELECT p.bene_id, p.pde_id, p.fill_day, p.lis, p.ltc, p.brand, p.specialty,
       p.ingredient_cost, p.dispensing_fee, p.sales_tax, p.vaccine_admin_fee,
       p.gdc AS gdc_submitted, c.gdc AS gdc_corrected,
       p.cand_type, p.cand_dir, p.cand_e, s.active, s.error_type,
       s.ded_amt AS ded_sub, s.ini_amt AS ini_sub, s.cat_amt AS cat_sub,
       s.reinsurance AS reins_sub, c.reinsurance AS reins_cor,
       s.lics AS lics_sub, c.lics AS lics_cor,
       s.plan_paid AS plan_sub, c.plan_paid AS plan_cor,
       s.manufacturer AS mfr_sub, c.manufacturer AS mfr_cor
FROM pdes p
JOIN pde_benefit s ON s.pde_id = p.pde_id AND s.version = 'submitted'
JOIN pde_benefit c ON c.pde_id = p.pde_id AND c.version = 'corrected';

CREATE OR REPLACE TABLE truth AS
WITH a AS (
    SELECT count(*)::DOUBLE AS n_units,
           any_value(w_pop) * sum(x)::DOUBLE AS payments,
           any_value(w_pop) * sum(y) FILTER (WHERE y > 0)::DOUBLE AS overpayments,
           any_value(w_pop) * -sum(y) FILTER (WHERE y < 0)::DOUBLE AS underpayments,
           any_value(w_pop) * sum(reins_sub)::DOUBLE AS reinsurance,
           any_value(w_pop) * sum(lics_sub)::DOUBLE AS lics,
           any_value(w_pop) * sum(direct_subsidy)::DOUBLE AS direct_subsidy,
           avg((y <> 0)::INT)::DOUBLE AS unit_err_rate,
           avg(reached_catastrophic::INT)::DOUBLE AS share_catastrophic
    FROM population
),
r AS (
    SELECT *, (overpayments + underpayments) / payments AS gross_rate,
              (overpayments - underpayments) / payments AS net_rate
    FROM a
),
rates AS (   -- share of claims in error, LTC and other (targets 10% and 2.5%)
    SELECT CASE WHEN ltc THEN 'claim_err_rate_ltc' ELSE 'claim_err_rate_other' END AS metric,
           avg(active::INT)::DOUBLE AS value
    FROM pde_detail GROUP BY 1
),
shares AS (  -- count shares among active PDE errors (targets: 90% full, 10% partial)
    SELECT error_type AS metric, count(*)::DOUBLE / sum(count(*)) OVER () AS value
    FROM pde_detail WHERE active GROUP BY error_type
)
SELECT 'overall' AS level, NULL::VARCHAR AS key, metric, value FROM r
UNPIVOT (value FOR metric IN (n_units, payments, overpayments, underpayments, reinsurance, lics,
                              direct_subsidy, unit_err_rate, share_catastrophic, gross_rate, net_rate))
UNION ALL SELECT 'error_type_share', 'pde_count', metric, value FROM shares
UNION ALL SELECT 'overall', NULL, metric, value FROM rates
UNION ALL
SELECT 'calibration', 'pass_' || pass, metric, value FROM calib
UNPIVOT (value FOR metric IN (m, realized_gross));
