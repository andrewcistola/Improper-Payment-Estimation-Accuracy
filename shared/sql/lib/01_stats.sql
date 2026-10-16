-- =====================================================================
-- shared/sql/lib/01_stats.sql : normal distribution and quantiles
-- ---------------------------------------------------------------------
-- DuckDB has no normal CDF or quantile function, so these are written
-- out from standard published approximations (tested against scipy in
-- shared/tests/test_stats.py):
--   norm_cdf(x) : Phi(x) via erf, Abramowitz & Stegun 7.1.26
--                 (absolute error < 1.5e-7)
--   norm_ppf(p) : Phi^-1(p), Acklam's rational approximation
--                 (relative error < 1.2e-9)
--   qsorted(l, p): quantile p of an already-sorted list l, linear
--                 interpolation between order statistics (Hyndman-Fan
--                 type 7, the R and numpy default)
-- =====================================================================

CREATE OR REPLACE MACRO erf_pos(z) AS (
    1.0 - (((((1.061405429 * (1.0 / (1.0 + 0.3275911 * z)) - 1.453152027) * (1.0 / (1.0 + 0.3275911 * z))
               + 1.421413741) * (1.0 / (1.0 + 0.3275911 * z)) - 0.284496736) * (1.0 / (1.0 + 0.3275911 * z))
               + 0.254829592) * (1.0 / (1.0 + 0.3275911 * z))) * exp(-z * z)
);

CREATE OR REPLACE MACRO norm_cdf(x) AS
    0.5 * (1.0 + sign(x) * erf_pos(abs(x) / sqrt(2.0)));

CREATE OR REPLACE MACRO ppf_tail(q) AS (   -- q = sqrt(-2 ln p) for the lower tail
    (((((-7.784894002430293e-03 * q - 3.223964580411365e-01) * q - 2.400758277161838e+00) * q
        - 2.549732539343734e+00) * q + 4.374664141464968e+00) * q + 2.938163982698783e+00)
    / ((((7.784695709041462e-03 * q + 3.224671290700398e-01) * q + 2.445134137142996e+00) * q
        + 3.754408661907416e+00) * q + 1.0)
);

CREATE OR REPLACE MACRO ppf_central(q) AS (  -- q = p - 0.5, r = q^2
    (((((-3.969683028665376e+01 * q * q + 2.209460984245205e+02) * q * q - 2.759285104469687e+02) * q * q
        + 1.383577518672690e+02) * q * q - 3.066479806614716e+01) * q * q + 2.506628277459239e+00) * q
    / (((((-5.447609879822406e+01 * q * q + 1.615858368580409e+02) * q * q - 1.556989798598866e+02) * q * q
        + 6.680131188771972e+01) * q * q - 1.328068155288572e+01) * q * q + 1.0)
);

CREATE OR REPLACE MACRO norm_ppf(p) AS
    CASE WHEN p <= 0 THEN '-infinity'::DOUBLE
         WHEN p >= 1 THEN 'infinity'::DOUBLE
         WHEN p < 0.02425 THEN ppf_tail(sqrt(-2.0 * ln(p)))
         WHEN p > 1 - 0.02425 THEN -ppf_tail(sqrt(-2.0 * ln(1.0 - p)))
         ELSE ppf_central(p - 0.5) END;

CREATE OR REPLACE MACRO qsorted(l, p) AS
    CASE WHEN len(l) = 0 THEN NULL
         WHEN len(l) = 1 THEN l[1]
         ELSE l[1 + floor((len(l) - 1) * least(1.0, greatest(0.0, p)))::BIGINT]
              + ((len(l) - 1) * least(1.0, greatest(0.0, p)) - floor((len(l) - 1) * least(1.0, greatest(0.0, p))))
                * (l[least(len(l), 2 + floor((len(l) - 1) * least(1.0, greatest(0.0, p)))::BIGINT)]
                   - l[1 + floor((len(l) - 1) * least(1.0, greatest(0.0, p)))::BIGINT]) END;

-- fsum(v): sum of DOUBLE values in a fixed (sorted) order. A plain sum()
-- adds partial results in whatever order threads finish, which changes
-- the last digits between runs; sorting first makes results byte-for-byte
-- reproducible. Use it for every floating-point aggregate.
CREATE OR REPLACE MACRO fsum(v) AS list_sum(list_sort(list(v::DOUBLE)));
CREATE OR REPLACE MACRO favg(v) AS list_sum(list_sort(list(v::DOUBLE))) / count(v);
CREATE OR REPLACE MACRO fsd(v) AS
    sqrt(greatest(0.0, (list_sum(list_sort(list(v::DOUBLE * v::DOUBLE)))
                        - power(list_sum(list_sort(list(v::DOUBLE))), 2) / count(v)) / (count(v) - 1)));
