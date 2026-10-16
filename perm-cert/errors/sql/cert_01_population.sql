-- =====================================================================
-- cert errors/cert_01_population.sql : claim payment universes (no errors)
-- ---------------------------------------------------------------------
-- Application 3: claim-level errors (CERT-like), stress family.
-- Stylized versions of the three payment shapes in Edwards, Liu &
-- Delage (2023): synthetic shapes only, no source data.
--   right     : beneficiary-level totals, lognormal (N = 59,804)
--   two_spike : two narrow payment modes, 30% low / 70% high (N = 249)
--   left      : claims piled up near a per-claim ceiling (N = 570)
-- Output: base(unit_id, x)
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
