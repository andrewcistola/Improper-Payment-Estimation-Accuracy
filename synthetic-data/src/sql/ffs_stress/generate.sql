-- =====================================================================
-- ffs_stress/generate.sql : CERT/PIM-style claim stress populations
-- ---------------------------------------------------------------------
-- Application 3 (claim/benefit-level errors), benchmark family.
-- Stylized versions of the three payment shapes in Edwards, Liu &
-- Delage (2023): synthetic shapes only, no source data.
--   right     : hospice beneficiary totals, lognormal (N = 59,804)
--   two_spike : power wheelchair claims, two narrow modes, 30% low / 70% high (N = 249)
--   left      : hospice claims piled up near a per-claim ceiling (N = 570)
-- Errors are placed on exactly round(p*N) units (unit error rate is
-- exact, not expected), chosen in random order.
--   all_or_nothing : y = x                     (Edwards model)
--   mixed          : a share of the error units are partial,
--                    y = x * Kumaraswamy(2,2)  (realistic mix)
-- Variables: seed, shape, n_units, error_rate, error_model, partial_share
-- =====================================================================

CREATE OR REPLACE TABLE base AS
SELECT
    i::BIGINT AS unit_id,
    CASE getvariable('shape')
        WHEN 'right' THEN
            usd(greatest(25.0, rlnorm(getvariable('seed'), 'x', i, 7.6, 1.15)))
        WHEN 'two_spike' THEN
            usd(CASE WHEN u01(getvariable('seed'), 'mode', i) < 0.30
                     THEN 4800.0 + 180.0 * rnorm(getvariable('seed'), 'x', i)
                     ELSE 13500.0 + 420.0 * rnorm(getvariable('seed'), 'x', i) END)
        WHEN 'left' THEN
            usd(250.0 + 6750.0 * rkuma(getvariable('seed'), 'x', i, 6.0, 1.4))
    END AS x
FROM range(1, getvariable('n_units') + 1) t(i);

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
