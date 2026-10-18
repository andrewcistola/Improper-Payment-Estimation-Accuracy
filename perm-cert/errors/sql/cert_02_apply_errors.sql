-- =====================================================================
-- cert errors/cert_02_apply_errors.sql : fake claim errors
-- ---------------------------------------------------------------------
-- At most one error per claim, from one uniform u_act per claim. Per
-- claim type, from its FY 2025 overpayment rate o = over / paid and
-- underpayment rate u = (gross - over) / paid:
--   whole-claim overpayment (no or insufficient documentation, medical
--     necessity, other): y = x                     u_act < p_full
--   partial overpayment (coding): y = round(x t_o), t_o ~ U(taint_over)
--                                        p_full <= u_act < p_full + p_po
--   underpayment (coding): y = -round(x t_u), t_u ~ U(taint_under)
--                          p_full + p_po <= u_act < p_full + p_po + p_u
-- Rates are closed form (each claim's candidate amounts are known, so
-- the expected dollars are exact):
--   p_full = o x (1 - partial_over_share)
--   p_po   = o x partial_over_share x X / sum(x t_o)
--   p_u    = u x X / sum(x t_u)                    (X = type's payments)
-- Errors do not depend on claim size or stratum.
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

CREATE OR REPLACE TABLE calib AS
SELECT c.type_code, any_value(t.claim_type) AS claim_type,
       round(any_value(t.over / t.paid) * (1 - getvariable('partial_over_share')), 8) AS p_full,
       round(any_value(t.over / t.paid) * getvariable('partial_over_share')
             * sum(c.x)::DOUBLE / fsum(c.x::DOUBLE * c.t_o), 8) AS p_po,
       round(any_value((t.gross - t.over) / t.paid) * sum(c.x)::DOUBLE / fsum(c.x::DOUBLE * c.t_u), 8) AS p_u
FROM cand c JOIN claim_types t ON t.code = c.type_code
GROUP BY c.type_code;

CREATE OR REPLACE TABLE population AS
WITH a AS (
    SELECT c.*,
           CASE WHEN c.u_act < k.p_full THEN 'full_over'
                WHEN c.u_act < k.p_full + k.p_po THEN 'partial_over'
                WHEN c.u_act < k.p_full + k.p_po + k.p_u THEN 'under'
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
