-- =====================================================================
-- estimate/estimators.sql : point estimators for every replicate
-- ---------------------------------------------------------------------
-- Input : sample(rep, stratum, pop_h, samp_h, y, x, w), variable X_total
--         (known frame total of the auxiliary x)
-- Output: estimates(rep, t_expansion, t_ratio, t_regression, rate)
--   expansion  : T_y = sum w*y                      (Horvitz-Thompson)
--   ratio      : (sum w*y / sum w*x) * X            (uses known X)
--   regression : T_y + b * (X - T_x), with the combined weighted slope
--                b = sum w(x-xbar)(y-ybar) / sum w(x-xbar)^2
--                (GREG with one auxiliary and an intercept)
--   rate       : sum w*y / sum w*x                  (improper payment rate)
-- Analytic and bootstrap intervals are built on these in the aims.
-- =====================================================================
CREATE OR REPLACE TABLE estimates AS
WITH m AS (
    SELECT rep, sum(w * y) / sum(w) AS ybar, sum(w * x) / sum(w) AS xbar,
           sum(w * y) AS t_y, sum(w * x) AS t_x
    FROM (SELECT rep, w, y::DOUBLE AS y, x::DOUBLE AS x FROM sample) GROUP BY rep
),
b AS (
    SELECT s.rep,
           sum(s.w * (s.x::DOUBLE - m.xbar) * (s.y::DOUBLE - m.ybar))
             / nullif(sum(s.w * (s.x::DOUBLE - m.xbar) ^ 2), 0) AS slope
    FROM sample s JOIN m USING (rep) GROUP BY s.rep
)
SELECT m.rep,
       m.t_y AS t_expansion,
       m.t_y / m.t_x * getvariable('X_total') AS t_ratio,
       m.t_y + coalesce(b.slope, 0) * (getvariable('X_total') - m.t_x) AS t_regression,
       m.t_y / m.t_x AS rate
FROM m JOIN b USING (rep);
