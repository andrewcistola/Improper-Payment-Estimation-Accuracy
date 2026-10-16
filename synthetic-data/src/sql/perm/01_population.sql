-- =====================================================================
-- perm/01_population.sql : PERM-like state universes (Medicaid)
-- ---------------------------------------------------------------------
-- Application 3: claim/benefit-level errors plus eligibility errors.
-- One state cycle; states listed explicitly in the config (state_id,
-- fmap, elig_rate). Measurement year runs July-June; quarter 1 = Jul-Sep.
-- Payments:
--   FFS  : fee-for-service claims, lognormal amounts
--   MC   : one managed-care capitation payment per enrolled month
-- Errors:
--   claims (data processing / medical review), Bernoulli per payment:
--     FFS p = p_ffs (70% all-or-nothing, 30% partial), MC p = p_mc
--   eligibility, per beneficiary (all of that beneficiary's payments in
--     the year are improper): beneficiaries are put in random order and
--     flagged while their cumulative FEDERAL dollars stay at or below
--     elig_rate x the state's federal dollars. The true rate is therefore
--     never above the configured value and is within one beneficiary's
--     dollars of it (exact truth is in truth.json).
--     Types: documentation (85%) or ineligible (15%).
-- All rates are at federal share: improper * FMAP / paid * FMAP.
-- =====================================================================

CREATE OR REPLACE TABLE states AS
SELECT state_id, fmap::DECIMAL(6, 4) AS fmap, elig_rate::DECIMAL(8, 6) AS elig_rate
FROM (SELECT unnest(from_json(getvariable('states')::JSON,
       '[{"state_id":"INTEGER","fmap":"DOUBLE","elig_rate":"DOUBLE"}]'), recursive := true));

-- Step 1. Beneficiaries: bene_id = state_id * 10,000,000 + i
CREATE OR REPLACE TABLE perm_benes AS
SELECT s.state_id, s.fmap, s.elig_rate,
       s.state_id::BIGINT * 10000000 + i AS bene_id,
       u01(getvariable('seed'), 'mc', s.state_id::BIGINT * 10000000 + i) < getvariable('mc_share') AS mc_enrolled,
       1 + floor(12 * u01(getvariable('seed'), 'start', s.state_id::BIGINT * 10000000 + i))::INT AS first_month,
       rcount(getvariable('seed'), 'n_ffs', s.state_id::BIGINT * 10000000 + i, 1.5, 1.0, 0) AS n_ffs
FROM states s, LATERAL range(1, getvariable('benes_per_state') + 1) t(i);

-- Step 2. Payments. month = 1..12 of the July-June year; quarter = ceil(month/3)
CREATE OR REPLACE TABLE perm_payments AS
SELECT b.state_id, b.bene_id, b.fmap,
       b.bene_id * 100 + j AS payment_id, 'FFS' AS payment_type,
       1 + floor(12 * u01(getvariable('seed'), 'ffs_month', b.bene_id * 100 + j))::INT AS month,
       usd(greatest(5.0, rlnorm(getvariable('seed'), 'ffs_amt', b.bene_id * 100 + j, 4.8, 1.4))) AS x
FROM perm_benes b, LATERAL range(1, b.n_ffs + 1) t(j)
UNION ALL
SELECT b.state_id, b.bene_id, b.fmap,
       b.bene_id * 100 + 50 + m AS payment_id, 'MC',
       m AS month,
       usd(380.0 * rlnorm(getvariable('seed'), 'mc_amt', b.bene_id, 0.0, 0.45)) AS x  -- rate cell varies by enrollee
FROM perm_benes b, LATERAL range(b.first_month, 13) t(m)
WHERE b.mc_enrolled;

-- Step 3. Claims errors (Bernoulli per payment).
CREATE OR REPLACE TABLE perm_payments AS
WITH d AS (
    SELECT p.*, ((p.month - 1) // 3 + 1)::INT AS quarter,
           u01(getvariable('seed'), 'cerr', payment_id) AS u_err,
           u01(getvariable('seed'), 'ckind', payment_id) AS u_kind,
           rkuma(getvariable('seed'), 'cfrac', payment_id, 2.0, 2.0) AS frac
    FROM perm_payments p
)
SELECT state_id, bene_id, payment_id, payment_type, month, quarter, fmap, x,
       CASE WHEN payment_type = 'FFS' AND u_err < getvariable('p_ffs')
                 THEN CASE WHEN u_kind < 0.70 THEN x ELSE usd(x * frac) END
            WHEN payment_type = 'MC' AND u_err < getvariable('p_mc') THEN x
            ELSE usd(0) END AS y_claims,
       CASE WHEN payment_type = 'FFS' AND u_err < getvariable('p_ffs')
                 THEN CASE WHEN u_kind < 0.70 THEN 'no_documentation' ELSE 'partial_pricing' END
            WHEN payment_type = 'MC' AND u_err < getvariable('p_mc') THEN 'mc_processing'
            ELSE 'none' END AS claims_error_type
FROM d;

-- Step 4. Eligibility errors: exact-rate placement by random order.
CREATE OR REPLACE TABLE perm_elig AS
WITH b AS (
    SELECT p.state_id, p.bene_id, sum(p.x * p.fmap)::DECIMAL(18, 6) AS fed_paid
    FROM perm_payments p GROUP BY p.state_id, p.bene_id
),
o AS (
    SELECT b.*, s.elig_rate,
           sum(fed_paid) OVER (PARTITION BY b.state_id) AS state_fed,
           sum(fed_paid) OVER (PARTITION BY b.state_id
                               ORDER BY u01(getvariable('seed'), 'elig_order', b.bene_id), b.bene_id
                               ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) - fed_paid AS fed_before
    FROM b JOIN states s USING (state_id)
)
SELECT state_id, bene_id,
       fed_before + fed_paid <= elig_rate * state_fed AS elig_error,
       CASE WHEN u01(getvariable('seed'), 'elig_type', bene_id) < 0.85
            THEN 'eligibility_documentation' ELSE 'ineligible' END AS elig_error_type_if_any
FROM o;

-- Step 5. Payment-level population.
CREATE OR REPLACE TABLE population AS
SELECT p.payment_id AS unit_id, p.state_id, p.bene_id, p.payment_type, p.month, p.quarter, p.fmap,
       p.x,
       p.y_claims,
       CASE WHEN e.elig_error THEN p.x ELSE usd(0) END AS y_elig,
       CASE WHEN e.elig_error THEN p.x ELSE p.y_claims END AS y,     -- overall: claims + elig - overlap
       p.claims_error_type,
       CASE WHEN e.elig_error THEN e.elig_error_type_if_any ELSE 'none' END AS elig_error_type,
       getvariable('w_pop')::DOUBLE AS w_pop
FROM perm_payments p JOIN perm_elig e USING (state_id, bene_id);

-- Step 6. Strata within state x quarter x payment type: 5 equal-dollar
-- payment-size strata (each holds ~1/5 of paid dollars).
CREATE OR REPLACE TABLE population AS
WITH c AS (
    SELECT *,
           sum(x) OVER (PARTITION BY state_id, quarter, payment_type ORDER BY x, unit_id
                        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)::DOUBLE
           / sum(x) OVER (PARTITION BY state_id, quarter, payment_type)::DOUBLE AS cum_share
    FROM population
)
SELECT unit_id, state_id, bene_id, payment_type, month, quarter,
       concat(state_id, '_Q', quarter, '_', payment_type, '_S', least(5, floor(cum_share * 5)::INT + 1)) AS stratum,
       fmap, x, y_claims, y_elig, y, claims_error_type, elig_error_type, w_pop
FROM c;
