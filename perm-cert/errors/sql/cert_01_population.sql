-- =====================================================================
-- cert errors/cert_01_population.sql : Medicare FFS claims (no errors)
-- ---------------------------------------------------------------------
-- Application 3: claim-level errors (CERT-like), national universe.
-- Four claim types (the CERT claim-type strata): Part A hospital IPPS,
-- Part A excluding IPPS, Part B, DMEPOS. No MAC jurisdictions.
-- Per claim type (config claim_types):
--   n_claims synthetic claims (1 = w_pop real claims)
--   raw amount  r_i ~ lognormal(0, sigma)
--   x_i = round(r_i x (paid / w_pop) / sum r, cents), at least $1, so
--         the type's synthetic total x w_pop matches its FY 2025 payments
-- Strata: claim type x five equal-count quintiles of x (P1 smallest).
-- Output: claims(unit_id, claim_type, type_code, stratum, x)
-- =====================================================================
CREATE OR REPLACE TABLE claim_types AS
SELECT * FROM (SELECT unnest(from_json(getvariable('claim_types')::JSON,
    '[{"claim_type":"VARCHAR","code":"INTEGER","n_claims":"BIGINT","sigma":"DOUBLE","paid":"DOUBLE","gross":"DOUBLE","over":"DOUBLE"}]'),
    recursive := true));

-- unit_id = code x 10^8 + i (unique, and sorted by claim type)
CREATE OR REPLACE TABLE claims_raw AS
SELECT t.claim_type, t.code AS type_code, t.code::BIGINT * 100000000 + i AS unit_id,
       rlnorm(getvariable('seed'), 'x', t.code::BIGINT * 100000000 + i, 0.0, t.sigma) AS r,
       t.paid / getvariable('w_pop') AS target
FROM claim_types t, LATERAL range(1, t.n_claims + 1) r(i);

CREATE OR REPLACE TABLE claims AS
WITH s AS (SELECT type_code, fsum(r) AS sum_r FROM claims_raw GROUP BY type_code),
c AS (SELECT c.unit_id, c.claim_type, c.type_code,
             usd(greatest(1.0, c.r * c.target / s.sum_r)) AS x
      FROM claims_raw c JOIN s USING (type_code))
SELECT unit_id, claim_type, type_code,
       claim_type || '_P' || ntile(5) OVER (PARTITION BY type_code ORDER BY x, unit_id) AS stratum, x
FROM c;

DROP TABLE claims_raw;
