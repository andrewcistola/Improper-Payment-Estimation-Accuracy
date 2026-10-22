-- =====================================================================
-- perm errors/01_population.sql : state payment universes (no errors)
-- ---------------------------------------------------------------------
-- Application 3: Medicaid PERM-like measurement, one state cycle.
-- States are listed explicitly in the config (state_id, fmap, and the
-- eligibility error rate used later in perm_03). Measurement year runs
-- July-June; quarter 1 = Jul-Sep.
-- Payments:
--   FFS : fee-for-service claims, lognormal amounts
--   MC  : one managed-care capitation payment per enrolled month
-- Strata: within state x payment type, 5 equal-count quintiles of the
-- amount paid (stratum = <state>_<type>_P1..P5; 10 per state). Quarter is
-- recorded on every payment but is not a stratification variable.
-- Output: states, perm_benes, perm_payments (error-free)
-- =====================================================================

CREATE OR REPLACE TABLE states AS
SELECT state_id, fmap::DECIMAL(6, 4) AS fmap, elig_rate::DECIMAL(8, 6) AS elig_rate
FROM (SELECT unnest(from_json(getvariable('states')::JSON,
       '[{"state_id":"INTEGER","fmap":"DOUBLE","elig_rate":"DOUBLE"}]'), recursive := true));

-- Step 1. Beneficiaries: bene_id = state_id * 10,000,000 + i
CREATE OR REPLACE TABLE perm_benes AS
SELECT s.state_id, s.fmap,
       s.state_id::BIGINT * 10000000 + i AS bene_id,
       u01(getvariable('seed'), 'mc', s.state_id::BIGINT * 10000000 + i) < getvariable('mc_share') AS mc_enrolled,
       1 + floor(12 * u01(getvariable('seed'), 'start', s.state_id::BIGINT * 10000000 + i))::INT AS first_month,
       least(500, rcount(getvariable('seed'), 'n_ffs', s.state_id::BIGINT * 10000000 + i, 1.5, 1.0, 0)) AS n_ffs
FROM states s, LATERAL range(1, getvariable('benes_per_state') + 1) t(i);

-- Step 2. Payments. month = 1..12 of the July-June year; quarter = ceil(month/3)
-- payment_id = bene_id * 1000 + j for FFS claims (j = 1..500, FFS claims
-- per beneficiary capped at 500) and bene_id * 1000 + 900 + month for MC,
-- so every payment id is unique (checked in perm_05).
CREATE OR REPLACE TABLE perm_payments AS
SELECT b.state_id, b.bene_id, b.fmap,
       b.bene_id * 1000 + j AS payment_id, 'FFS' AS payment_type,
       1 + floor(12 * u01(getvariable('seed'), 'ffs_month', b.bene_id * 1000 + j))::INT AS month,
       usd(greatest(5.0, rlnorm(getvariable('seed'), 'ffs_amt', b.bene_id * 1000 + j, 4.8, 1.4))) AS x
FROM perm_benes b, LATERAL range(1, b.n_ffs + 1) t(j)
UNION ALL
SELECT b.state_id, b.bene_id, b.fmap,
       b.bene_id * 1000 + 900 + m AS payment_id, 'MC',
       m AS month,
       usd(380.0 * rlnorm(getvariable('seed'), 'mc_amt', b.bene_id, 0.0, 0.45)) AS x  -- rate cell varies by enrollee
FROM perm_benes b, LATERAL range(b.first_month, 13) t(m)
WHERE b.mc_enrolled;

-- Step 3. Quarter, and payment strata: within state x payment type, five
-- equal-count quintiles of the amount paid (P1 lowest .. P5 highest).
CREATE OR REPLACE TABLE perm_payments AS
WITH q AS (SELECT *, ((month - 1) // 3 + 1)::INT AS quarter FROM perm_payments)
SELECT state_id, bene_id, payment_id, payment_type, month, quarter,
       concat(state_id, '_', payment_type, '_P',
              ntile(5) OVER (PARTITION BY state_id, payment_type ORDER BY x, payment_id)) AS stratum,
       fmap, x
FROM q;
