-- =====================================================================
-- cert errors/02_apply_errors.sql : fake claim errors
-- ---------------------------------------------------------------------
-- At most one error per claim, from one uniform u_act per claim. Per
-- claim type, from its FY 2025 overpayment rate o = over / paid and
-- underpayment rate u = (gross - over) / paid:
--   whole-claim overpayment (no or insufficient documentation, medical
--     necessity, other): y = x                     u_act < p_full s_i
--   partial overpayment (coding): y = round(x t_o), t_o ~ U(taint_over)
--                                  p_full s_i <= u_act < (p_full + p_po) s_i
--   underpayment (coding): y = -round(x t_u), t_u ~ U(taint_under)
--                (p_full + p_po) s_i <= u_act < (p_full + p_po + p_u) s_i
-- Rates are closed form (each claim's candidate amounts are known, so
-- the expected dollars are exact):
--   p_full = o x (1 - partial_over_share) x sum x / sum(s_i x_i)
--   p_po   = o x partial_over_share x X / sum(s_i x_i t_o)
--   p_u    = u x X / sum(s_i x_i t_u)                (X = type's payments)
-- size_beta (default 0): dependence of the error probability on the
-- claim's amount. Within claim type, s_i = (x_i / mean x)^size_beta,
-- capped so that a claim's total error probability stays at or below
-- 0.95. The three expected dollar amounts are computed with the
-- per-claim probabilities (p s_i), so the calibration hits each FY 2025
-- target at any size_beta. At size_beta = 0 every s_i = 1 and the size
-- adjustment factors (fsum(c) / fsum(c x s_i)) are exactly 1, so the
-- output is byte-identical to the version without this variable; at
-- size_beta > 0 large claims are more likely to be in error (0.5: with
-- the square root of the amount). Otherwise errors do not depend on
-- claim size or stratum.
-- Output: population (one row per claim), calib
-- =====================================================================
CREATE OR REPLACE TABLE cand AS
SELECT c.*,
       u01(getvariable('seed'), 'act', unit_id) AS u_act,
       (getvariable('taint_over')::JSON->>0)::DOUBLE + ((getvariable('taint_over')::JSON->>1)::DOUBLE - (getvariable('taint_over')::JSON->>0)::DOUBLE)
           * u01(getvariable('seed'), 't_over', unit_id) AS t_o,
       (getvariable('taint_under')::JSON->>0)::DOUBLE + ((getvariable('taint_under')::JSON->>1)::DOUBLE - (getvariable('taint_under')::JSON->>0)::DOUBLE)
           * u01(getvariable('seed'), 't_under', unit_id) AS t_u
FROM claims c;

-- size-independent rates (size_beta = 0), used to cap the size factor
CREATE OR REPLACE TABLE calib0 AS
SELECT c.type_code,
       any_value(t.over / t.paid) * (1 - getvariable('partial_over_share'))
         + any_value(t.over / t.paid) * getvariable('partial_over_share') * sum(c.x)::DOUBLE / fsum(c.x::DOUBLE * c.t_o)
         + any_value((t.gross - t.over) / t.paid) * sum(c.x)::DOUBLE / fsum(c.x::DOUBLE * c.t_u) AS p_any0,
       fsum(c.x) / count(*) AS mean_x
FROM cand c JOIN claim_types t ON t.code = c.type_code
GROUP BY c.type_code;

CREATE OR REPLACE TABLE cand AS
SELECT c.*, least(pow(c.x::DOUBLE / k.mean_x, coalesce(getvariable('size_beta'), 0.0)::DOUBLE), 0.95 / k.p_any0) AS s_size
FROM cand c JOIN calib0 k USING (type_code);

CREATE OR REPLACE TABLE calib AS
SELECT c.type_code, any_value(t.claim_type) AS claim_type,
       round(any_value(t.over / t.paid) * (1 - getvariable('partial_over_share'))
             * (fsum(c.x) / fsum(c.x::DOUBLE * c.s_size)), 8) AS p_full,
       round(any_value(t.over / t.paid) * getvariable('partial_over_share')
             * sum(c.x)::DOUBLE / fsum(c.x::DOUBLE * c.t_o)
             * (fsum(c.x::DOUBLE * c.t_o) / fsum(c.x::DOUBLE * c.t_o * c.s_size)), 8) AS p_po,
       round(any_value((t.gross - t.over) / t.paid) * sum(c.x)::DOUBLE / fsum(c.x::DOUBLE * c.t_u)
             * (fsum(c.x::DOUBLE * c.t_u) / fsum(c.x::DOUBLE * c.t_u * c.s_size)), 8) AS p_u
FROM cand c JOIN claim_types t ON t.code = c.type_code
GROUP BY c.type_code;

CREATE OR REPLACE TABLE population AS
WITH a AS (
    SELECT c.*,
           CASE WHEN c.u_act < c.s_size * k.p_full THEN 'full_over'
                WHEN c.u_act < c.s_size * (k.p_full + k.p_po) THEN 'partial_over'
                WHEN c.u_act < least(0.95, c.s_size * (k.p_full + k.p_po + k.p_u)) THEN 'under'
                ELSE 'none' END AS error_type
    FROM cand c JOIN calib k USING (type_code)
)
SELECT unit_id, claim_type, type_code, stratum, x,
       CASE error_type WHEN 'full_over' THEN x
                       WHEN 'partial_over' THEN usd(x::DOUBLE * t_o)
                       WHEN 'under' THEN -usd(x::DOUBLE * t_u)
                       ELSE usd(0) END AS y,
       error_type,
       getvariable('w_pop')::DOUBLE AS w_pop
FROM a;

DROP TABLE cand;
DROP TABLE calib0;
