-- =====================================================================
-- perm errors/perm_03_eligibility_errors.sql : fake eligibility errors
-- ---------------------------------------------------------------------
-- Per beneficiary: all of that beneficiary's payments in the year are
-- improper. Beneficiaries are put in random order and flagged while
-- their cumulative FEDERAL dollars stay at or below elig_rate x the
-- state's federal dollars. The true state rate is therefore never above
-- the configured value and is within one beneficiary's dollars of it
-- (exact truth is in truth.json).
-- Types: documentation (85%) or ineligible (15%).
-- Overall error per payment = claims + eligibility - overlap, i.e.
-- the whole payment if eligibility is in error, else the claims error.
-- Output: population (one row per payment)
-- =====================================================================
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

CREATE OR REPLACE TABLE population AS
SELECT p.payment_id AS unit_id, p.state_id, p.bene_id, p.payment_type, p.month, p.quarter, p.stratum,
       p.fmap, p.x,
       p.y_claims,
       CASE WHEN e.elig_error THEN p.x ELSE usd(0) END AS y_elig,
       CASE WHEN e.elig_error THEN p.x ELSE p.y_claims END AS y,
       p.claims_error_type,
       CASE WHEN e.elig_error THEN e.elig_error_type_if_any ELSE 'none' END AS elig_error_type,
       getvariable('w_pop')::DOUBLE AS w_pop
FROM perm_payments p JOIN perm_elig e USING (state_id, bene_id);
