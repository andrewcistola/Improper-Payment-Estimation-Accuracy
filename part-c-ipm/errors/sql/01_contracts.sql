-- =====================================================================
-- partc errors/01_contracts.sql : Medicare Advantage contracts
-- ---------------------------------------------------------------------
-- Application 2: risk-score errors on capitated payments (Part C IPM).
-- n_contracts contracts with lognormal enrollment summing to
-- total_enrollees.
-- intensity = contract coding intensity; multiplies every HCC's
-- unsupported probability (1.0 = national average). It makes error
-- rates vary across contracts, as they do in practice.
-- county_rate_base = contract's average monthly county rate (USD).
-- =====================================================================

CREATE OR REPLACE TABLE contracts AS
WITH gen AS (
    SELECT i AS contract_id,
           rlnorm(getvariable('seed'), 'c_size', i, 0.0, 1.2)::DECIMAL(18, 6) AS size_w,
           rlnorm(getvariable('seed'), 'c_int', i, -0.08, 0.40) AS intensity,
           1000.0 * rlnorm(getvariable('seed'), 'c_rate', i, 0.0, 0.12) AS county_rate_base
    FROM range(1, getvariable('n_contracts') + 1) t(i)
)
SELECT contract_id,
       greatest(30, round(getvariable('total_enrollees') * size_w / sum(size_w) OVER ()))::BIGINT AS enrollment,
       intensity, county_rate_base
FROM gen;
