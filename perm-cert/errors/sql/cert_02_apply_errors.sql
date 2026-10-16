-- =====================================================================
-- cert errors/cert_02_apply_errors.sql : fake claim errors and truth
-- ---------------------------------------------------------------------
-- Errors are placed on exactly round(p*N) claims (the claim error rate is
-- exact, not expected), chosen in random order.
--   all_or_nothing : y = x                     (Edwards et al. model)
--   mixed          : a share of the error claims are partial,
--                    y = x * Kumaraswamy(2,2)
-- Output: population, truth
-- =====================================================================
-- random order for error placement; first round(p*N) units are in error
CREATE OR REPLACE TABLE ranked AS
SELECT b.*,
       row_number() OVER (ORDER BY u01(getvariable('seed'), 'err', unit_id), unit_id) AS err_rank,
       u01(getvariable('seed'), 'partial', unit_id) AS u_partial,
       rkuma(getvariable('seed'), 'frac', unit_id, 2.0, 2.0) AS frac
FROM base b;

CREATE OR REPLACE TABLE population AS
WITH k AS (SELECT round(getvariable('error_rate') * count(*))::BIGINT AS n_err FROM ranked)
SELECT
    unit_id,
    'all' AS stratum,
    x,
    CASE WHEN err_rank > n_err THEN usd(0)
         WHEN getvariable('error_model') = 'mixed' AND u_partial < getvariable('partial_share')
              THEN usd(x * frac)
         ELSE x END AS y,
    CASE WHEN err_rank > n_err THEN 'none'
         WHEN getvariable('error_model') = 'mixed' AND u_partial < getvariable('partial_share')
              THEN 'partial'
         ELSE 'missing_documentation' END AS error_type,
    1.0::DOUBLE AS w_pop
FROM ranked, k;

CREATE OR REPLACE TABLE truth AS
WITH a AS (
    SELECT count(*)::DOUBLE AS n, sum(x)::DOUBLE AS x_tot, sum(y)::DOUBLE AS y_tot,
           avg((y <> 0)::INT)::DOUBLE AS unit_err_rate,
           avg((error_type = 'partial')::INT)::DOUBLE AS partial_rate
    FROM population)
SELECT 'overall' AS level, NULL::VARCHAR AS key, metric, value FROM a
UNPIVOT (value FOR metric IN (
    n, x_tot, y_tot, unit_err_rate, partial_rate))
UNION ALL
SELECT 'overall', NULL, 'dollar_err_rate', y_tot / x_tot FROM a;
