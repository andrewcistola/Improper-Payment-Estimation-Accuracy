-- =====================================================================
-- partd errors/01_population.sql : beneficiaries and PDEs (no errors)
-- ---------------------------------------------------------------------
-- Application 1: claim-level errors that flow through a benefit design
-- to a reinsurance / subsidy payment (Part D-like).
-- GDC = ingredient cost + dispensing fee + sales tax + vaccine admin fee
-- Output: benes, pdes (submitted, error-free)
-- =====================================================================

-- Step 1. Beneficiaries (bene_id 1..n_benes)
CREATE OR REPLACE TABLE benes AS
SELECT i AS bene_id,
       u01(getvariable('seed'), 'lis', i) < getvariable('lis_share') AS lis,
       u01(getvariable('seed'), 'specialty', i) < getvariable('specialty_share') AS specialty_user,
       rcount(getvariable('seed'), 'n_pde', i, 3.3, 0.9, 1) AS n_pde
FROM range(1, getvariable('n_benes') + 1) t(i);

-- Step 2. PDEs: pde_id = bene_id * 10,000 + j
CREATE OR REPLACE TABLE pdes AS
WITH d AS (
    SELECT b.bene_id, b.lis, b.specialty_user,
           b.bene_id * 10000 + j AS pde_id,
           1 + floor(365 * u01(getvariable('seed'), 'day', b.bene_id * 10000 + j))::INT AS fill_day,
           u01(getvariable('seed'), 'brand', b.bene_id * 10000 + j) AS u_brand,
           u01(getvariable('seed'), 'spec', b.bene_id * 10000 + j) AS u_spec
    FROM benes b, LATERAL range(1, b.n_pde + 1) t(j)
),
c AS (
    SELECT *,
           u_brand < 0.15 AS brand,   -- applicable drug (Manufacturer Discount Program)
           specialty_user AND u_spec < 0.25 AS specialty
    FROM d
)
SELECT bene_id, pde_id, fill_day, lis, brand, specialty,
       usd(CASE WHEN specialty THEN rlnorm(getvariable('seed'), 'ing', pde_id, 8.3, 0.6)
                WHEN brand     THEN rlnorm(getvariable('seed'), 'ing', pde_id, 5.6, 0.8)
                ELSE                rlnorm(getvariable('seed'), 'ing', pde_id, 2.4, 0.9) END) AS ingredient_cost,
       usd(1.50 + 1.00 * u01(getvariable('seed'), 'fee', pde_id)) AS dispensing_fee,
       usd(0) AS sales_tax,       -- most states exempt prescriptions
       usd(0) AS vaccine_admin_fee
FROM c;

CREATE OR REPLACE TABLE pdes AS
SELECT *, (ingredient_cost + dispensing_fee + sales_tax + vaccine_admin_fee)::DECIMAL(18, 2) AS gdc
FROM pdes;
