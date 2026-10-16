-- =====================================================================
-- capitation/01_contracts.sql : MA contracts (Part C IPM and RADV)
-- ---------------------------------------------------------------------
-- Application 2: risk-score errors on capitated payments.
-- Two modes:
--   contract_mode = 'generate' : n_contracts with lognormal enrollment
--                                summing to total_enrollees (Part C IPM)
--   contract_mode = 'list'     : explicit contracts from config
--                                (RADV: each row is readable by a reviewer)
-- intensity = contract coding intensity; multiplies every HCC's
-- unsupported probability. 1.0 = national average, 0 = clean contract.
-- county_rate_base = contract's average monthly county rate (USD).
-- =====================================================================

CREATE OR REPLACE TABLE contracts AS
WITH gen AS (
    SELECT i AS contract_id,
           rlnorm(getvariable('seed'), 'c_size', i, 0.0, 1.2)::DECIMAL(18, 6) AS size_w,
           rlnorm(getvariable('seed'), 'c_int', i, -0.08, 0.40) AS intensity,
           1000.0 * rlnorm(getvariable('seed'), 'c_rate', i, 0.0, 0.12) AS county_rate_base
    FROM range(1, getvariable('n_contracts') + 1) t(i)
    WHERE getvariable('contract_mode') = 'generate'
),
listed AS (
    SELECT unnest(from_json(getvariable('contracts')::JSON,
             '[{"contract_id":"BIGINT","enrollment":"BIGINT","intensity":"DOUBLE"}]'), recursive := true)
    WHERE getvariable('contract_mode') = 'list'
)
SELECT contract_id,
       greatest(30, round(getvariable('total_enrollees') * size_w / sum(size_w) OVER ()))::BIGINT AS enrollment,
       intensity, county_rate_base
FROM gen
UNION ALL
SELECT contract_id, enrollment, intensity,
       1000.0 * rlnorm(getvariable('seed'), 'c_rate', contract_id, 0.0, 0.12) AS county_rate_base
FROM listed;
