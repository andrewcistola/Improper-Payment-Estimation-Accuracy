-- =====================================================================
-- perm errors/perm_02_claims_errors.sql : fake claims-review errors
-- ---------------------------------------------------------------------
-- Data processing / medical review errors, one Bernoulli draw per payment:
--   FFS : p = p_ffs; 70% all-or-nothing (no documentation, y = x),
--         30% partial pricing (y = x * Kumaraswamy(2,2))
--   MC  : p = p_mc; all-or-nothing (capitation paid in error)
-- Output: perm_payments + y_claims, claims_error_type
-- =====================================================================
CREATE OR REPLACE TABLE perm_payments AS
WITH d AS (
    SELECT p.*,
           u01(getvariable('seed'), 'cerr', payment_id) AS u_err,
           u01(getvariable('seed'), 'ckind', payment_id) AS u_kind,
           rkuma(getvariable('seed'), 'cfrac', payment_id, 2.0, 2.0) AS frac
    FROM perm_payments p
)
SELECT state_id, bene_id, payment_id, payment_type, month, quarter, stratum, fmap, x,
       CASE WHEN payment_type = 'FFS' AND u_err < getvariable('p_ffs')
                 THEN CASE WHEN u_kind < 0.70 THEN x ELSE usd(x * frac) END
            WHEN payment_type = 'MC' AND u_err < getvariable('p_mc') THEN x
            ELSE usd(0) END AS y_claims,
       CASE WHEN payment_type = 'FFS' AND u_err < getvariable('p_ffs')
                 THEN CASE WHEN u_kind < 0.70 THEN 'no_documentation' ELSE 'partial_pricing' END
            WHEN payment_type = 'MC' AND u_err < getvariable('p_mc') THEN 'mc_processing'
            ELSE 'none' END AS claims_error_type
FROM d;
