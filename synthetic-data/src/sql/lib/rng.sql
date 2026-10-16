-- =====================================================================
-- rng.sql : counter-based (hash) random number macros
-- ---------------------------------------------------------------------
-- Every random draw is a pure function of (seed, stream, key...), so a
-- value never depends on thread scheduling, row order or which other
-- rows exist. That makes generation reproducible byte-for-byte and lets
-- any single unit be regenerated in isolation.
--
--   seed   : BIGINT master or child seed (from config)
--   stream : TEXT label naming what the draw is for ('payment', 'err')
--   a, b   : unit keys (BIGINT)
--
-- The key is ONE string 'seed|stream|a|b'. Do not pass several arguments
-- to hash(): DuckDB combines per-argument hashes with a weak mix, and
-- draws that differ only in one key are then strongly correlated (we
-- measured 24 of 30 units shared between "independent" SRS replicates
-- vs 3.6 expected). Hashing a single concatenated string fixes this;
-- tests/test_rng.py guards it.
-- hash() is stable within a DuckDB release; the version is pinned in
-- requirements.txt and recorded in every manifest. The top 53 bits give
-- a uniform on (0,1) that never returns exactly 0 or 1.
-- =====================================================================

CREATE OR REPLACE MACRO rkey(s, k, a) AS concat_ws('|', s, k, a);
CREATE OR REPLACE MACRO rkeyb(s, k, a, b) AS concat_ws('|', s, k, a, b);

CREATE OR REPLACE MACRO u01(s, k, a) AS
    ((hash(rkey(s, k, a)) >> 11)::DOUBLE + 0.5) / 9007199254740992.0;

CREATE OR REPLACE MACRO u01b(s, k, a, b) AS
    ((hash(rkeyb(s, k, a, b)) >> 11)::DOUBLE + 0.5) / 9007199254740992.0;

-- Standard normal by Box-Muller (two independent sub-streams).
CREATE OR REPLACE MACRO rnorm(s, k, a) AS
    sqrt(-2.0 * ln(u01(s, k || '#1', a))) * cos(2.0 * pi() * u01(s, k || '#2', a));

CREATE OR REPLACE MACRO rnormb(s, k, a, b) AS
    sqrt(-2.0 * ln(u01b(s, k || '#1', a, b))) * cos(2.0 * pi() * u01b(s, k || '#2', a, b));

CREATE OR REPLACE MACRO rlnorm(s, k, a, mu, sig) AS exp(mu + sig * rnorm(s, k, a));
CREATE OR REPLACE MACRO rlnormb(s, k, a, b, mu, sig) AS exp(mu + sig * rnormb(s, k, a, b));

-- Exponential with given rate.
CREATE OR REPLACE MACRO rexp(s, k, a, rate) AS -ln(u01(s, k, a)) / rate;

-- Kumaraswamy(p, q) on (0,1): closed-form inverse CDF, used as a
-- Beta-like draw for partial error fractions. Mean = q*B(1+1/p, q).
CREATE OR REPLACE MACRO rkuma(s, k, a, p, q) AS
    pow(1.0 - pow(1.0 - u01(s, k, a), 1.0 / q), 1.0 / p);
CREATE OR REPLACE MACRO rkumab(s, k, a, b, p, q) AS
    pow(1.0 - pow(1.0 - u01b(s, k, a, b), 1.0 / q), 1.0 / p);

-- Geometric-tailed count >= lo: floor of a lognormal, used for counts
-- (HCCs per enrollee, PDEs per beneficiary) where a heavy right tail is
-- wanted and an exact Poisson/NB form is not.
CREATE OR REPLACE MACRO rcount(s, k, a, mu, sig, lo) AS
    greatest(lo, floor(rlnorm(s, k, a, mu, sig)))::INTEGER;

-- Weighted random order key (Efraimidis-Spirakis): sorting ascending by
-- key draws units without replacement with probability proportional to
-- w. Used to *place* errors with covariate-dependent propensity while a
-- cumulative-sum threshold hits a dollar target exactly.
CREATE OR REPLACE MACRO wkey(s, k, a, w) AS -ln(u01(s, k, a)) / greatest(w, 1e-12);
CREATE OR REPLACE MACRO wkeyb(s, k, a, b, w) AS -ln(u01b(s, k, a, b)) / greatest(w, 1e-12);

-- Logistic helper for propensity models.
CREATE OR REPLACE MACRO expit(z) AS 1.0 / (1.0 + exp(-z));

-- Money: everything dollar-valued is DECIMAL(18,2) so sums are exact and
-- thread-order independent (a requirement for identical file hashes).
CREATE OR REPLACE MACRO usd(v) AS round(v, 2)::DECIMAL(18, 2);
