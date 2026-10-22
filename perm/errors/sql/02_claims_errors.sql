-- =====================================================================
-- perm errors/02_claims_errors.sql : fake claims-review errors
-- ---------------------------------------------------------------------
-- Data processing / medical review errors, one Bernoulli draw per payment:
--   FFS : p = p_ffs; 70% all-or-nothing (no documentation, y = x),
--         30% partial pricing (y = x * Kumaraswamy(2,2))
--   MC  : p = p_mc; all-or-nothing (capitation paid in error)
-- size_beta (default 0): dependence of the error probability on the
-- amount paid. Per payment i, within state x payment type,
--   s_i = (x_i / mean x)^size_beta, capped at 0.95 / p_type
--   p_i = p_type x r x s_i, capped at 0.95, with
--   r   = sum x / sum(s_i x_i)  (calibration multiplier, one per state x
--         payment type) so that the EXPECTED claims-error dollars, computed
--         with the per-payment probabilities, equal p_type x sum x: the
--         same as at size_beta = 0, which keeps the pooled 6.12% check.
-- At size_beta = 0 every s_i = 1 and r = 1 exactly (same sorted sums in
-- numerator and denominator), so the output is byte-identical to the
-- version without this variable. size_beta > 0 makes large payments more
-- likely to be in error (0.5: probability rises with the square root of
-- the payment); eligibility errors (perm_03) are not affected.
-- Output: perm_payments + y_claims, claims_error_type
-- =====================================================================
CREATE OR REPLACE TABLE perm_payments AS
WITH m AS (   -- mean paid within state x payment type (fixed-order sum: the same at any thread count)
    SELECT state_id, payment_type, fsum(x) / count(*) AS mean_x
    FROM perm_payments GROUP BY state_id, payment_type
),
s AS (        -- size factor, capped so that p_type x s_i <= 0.95
    SELECT p.*,
           least(pow(p.x::DOUBLE / m.mean_x, coalesce(getvariable('size_beta'), 0.0)::DOUBLE),
                 0.95 / CASE p.payment_type WHEN 'FFS' THEN getvariable('p_ffs') ELSE getvariable('p_mc') END) AS s_size
    FROM perm_payments p JOIN m USING (state_id, payment_type)
),
k AS (        -- calibration multiplier r: expected claims-error dollars = p_type x sum x
    SELECT state_id, payment_type, fsum(x) / fsum(x::DOUBLE * s_size) AS r_size
    FROM s GROUP BY state_id, payment_type
),
d AS (
    SELECT s.*,
           least(0.95, CASE s.payment_type WHEN 'FFS' THEN getvariable('p_ffs') ELSE getvariable('p_mc') END
                       * k.r_size * s.s_size) AS p_err,
           u01(getvariable('seed'), 'cerr', payment_id) AS u_err,
           u01(getvariable('seed'), 'ckind', payment_id) AS u_kind,
           rkuma(getvariable('seed'), 'cfrac', payment_id, 2.0, 2.0) AS frac
    FROM s JOIN k USING (state_id, payment_type)
)
SELECT state_id, bene_id, payment_id, payment_type, month, quarter, stratum, fmap, x,
       CASE WHEN payment_type = 'FFS' AND u_err < p_err
                 THEN CASE WHEN u_kind < 0.70 THEN x ELSE usd(x * frac) END
            WHEN payment_type = 'MC' AND u_err < p_err THEN x
            ELSE usd(0) END AS y_claims,
       CASE WHEN payment_type = 'FFS' AND u_err < p_err
                 THEN CASE WHEN u_kind < 0.70 THEN 'no_documentation' ELSE 'partial_pricing' END
            WHEN payment_type = 'MC' AND u_err < p_err THEN 'mc_processing'
            ELSE 'none' END AS claims_error_type
FROM d;
