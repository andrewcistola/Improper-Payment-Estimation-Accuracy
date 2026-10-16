-- =====================================================================
-- partd/01_beneficiaries_pdes.sql : beneficiaries, PDEs, candidate errors
-- ---------------------------------------------------------------------
-- Application 1: claim-level errors that flow through a benefit design
-- to a reinsurance / subsidy payment (Part D-like).
-- GDC = ingredient cost + dispensing fee + sales tax + vaccine admin fee
-- Every PDE carries a CANDIDATE error (type, direction, corrected GDC)
-- and an activation uniform u_act. Step 03 activates a candidate when
-- u_act < m, one calibrated multiplier for all types (see step 02).
-- Error types and base relative probabilities (FY 2025 count shares of
-- sampled errors): missing/invalid documentation 75.00% (all-or-nothing,
-- corrected GDC = 0), pricing 17.86% (partial +/- ~12% of GDC, 40% are
-- underpayments), drug discrepancy 7.14% (half are a costlier drug
-- supported by the record -> underpayment; half a cheaper one).
-- One multiplier m applies to all types, so active errors keep the
-- published type shares in expectation.
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

-- Step 3. Candidate error per PDE (not yet active).
CREATE OR REPLACE TABLE pdes AS
WITH t AS (
    SELECT *,
           u01(getvariable('seed'), 'etype', pde_id) AS u_type,
           u01(getvariable('seed'), 'edir', pde_id) AS u_dir,
           rkuma(getvariable('seed'), 'emag', pde_id, 1.5, 6.0) AS f_price,          -- mean ~0.12
           rlnorm(getvariable('seed'), 'emag_dd', pde_id, 0.0, 0.5) AS f_drug,
           u01(getvariable('seed'), 'act', pde_id) AS u_act
    FROM pdes
),
k AS (
    SELECT *,
           CASE WHEN u_type < 0.7500 THEN 'missing_documentation'
                WHEN u_type < 0.9286 THEN 'pricing'
                ELSE 'drug_discrepancy' END AS cand_type
    FROM t
)
SELECT *,
       CASE cand_type WHEN 'missing_documentation' THEN 'over'
                      WHEN 'pricing' THEN CASE WHEN u_dir < 0.40 THEN 'under' ELSE 'over' END
                      ELSE CASE WHEN u_dir < 0.50 THEN 'under' ELSE 'over' END END AS cand_dir,
       CASE cand_type
            WHEN 'missing_documentation' THEN usd(0)
            WHEN 'pricing' THEN CASE WHEN u_dir < 0.40 THEN usd(gdc * (1 + f_price))
                                     ELSE usd(gdc * (1 - f_price)) END
            ELSE CASE WHEN u_dir < 0.50 THEN usd(gdc * (1 + 3.5 * f_drug))               -- costlier drug (factor tuned once to the public over/under split)
                      ELSE usd(gdc * greatest(0.0, 1 - abs(f_drug - 1) - 0.05)) END   -- cheaper drug
       END AS cand_gdc
FROM k;
