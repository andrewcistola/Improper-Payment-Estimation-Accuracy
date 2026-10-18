-- =====================================================================
-- partd errors/05_benefit_pre_ira.sql : pre-IRA standard benefit (CY 2023)
-- ---------------------------------------------------------------------
-- Alternative to 05_benefit.sql (post-IRA, CY 2025), used by
-- part-d-ipm/errors/pre_ira.yaml. Run separately for the submitted and
-- corrected PDE streams of every beneficiary, in fill order. All amounts
-- are integer cents, so the numpy payment function reproduces them exactly.
-- Phases (CY 2023 parameters, config):
--   deductible : cumulative GDC in [0, D)                      D = $505
--   initial    : cumulative GDC in [D, ICL)                    ICL = $4,660
--   gap        : above ICL until TrOOP reaches the out-of-pocket threshold
--                ($7,400); TrOOP at ICL is T0 = D + 25% (ICL - D)
--   catastrophic: after that
-- TrOOP accrues in the gap at rate r per GDC dollar:
--   non-LIS brand   r = 95%  (enrollee 25% + manufacturer discount 70%)
--   non-LIS generic r = 25%  (enrollee 25%)
--   LIS             r = 100% (no manufacturer discount; enrollee standard
--                             share 100%, paid by LICS except the copay)
-- Gap GDC of a PDE: with W = cumulative sum of r x (GDC above ICL) in
-- cent-percent units and L = 100 x (OOP threshold - T0) in cents,
--   gap = round((min(W_i, L) - min(W_{i-1}, L)) / r),  catastrophic = rest.
-- Liability shares:
--                     enrollee  plan   manufacturer  Medicare reinsurance
--   deductible        100%      0      0             0
--   initial           25%       75%    0             0
--   gap, brand        25%       5%     70%           0      (non-LIS)
--   gap, generic      25%       75%    0             0      (non-LIS)
--   gap, LIS          100%      0      0             0      (LICS pays all but the copay)
--   catastrophic      5%        15%    0             80%
-- LIS enrollees pay the nominal copay before the threshold and nothing
-- after it (LICS pays the 5%). Simplification: the catastrophic minimum
-- copays ($4.15 / $10.35) are not applied; enrollee coinsurance is 5%.
-- Medicare PDE-driven payment = reinsurance + LICS (direct subsidy is
-- prospective; added in step 07). Output columns match 05_benefit.sql.
-- =====================================================================
CREATE OR REPLACE TABLE pde_benefit AS
WITH lim AS (
    SELECT round(getvariable('deductible') * 100)::BIGINT AS D,
           round(getvariable('initial_coverage_limit') * 100)::BIGINT AS ICL,
           round((getvariable('oop_threshold') - getvariable('deductible')
                  - getvariable('init_enrollee_coins') * (getvariable('initial_coverage_limit') - getvariable('deductible')))
                 * 10000)::BIGINT AS L                                   -- cent-percent
),
c0 AS (
    SELECT v.*, (v.gdc * 100)::BIGINT AS g,
           CASE WHEN v.lis THEN 100 WHEN v.brand THEN 95 ELSE 25 END AS r
    FROM pde_versions v
),
cum AS (
    SELECT c0.*,
           sum(g) OVER (PARTITION BY version, bene_id ORDER BY fill_day, pde_id
                        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) - g AS pre_c
    FROM c0
),
ph AS (
    SELECT cum.*, lim.D, lim.ICL, lim.L,
           greatest(0, least(pre_c + g, lim.D) - least(pre_c, lim.D)) AS ded_c,
           greatest(0, least(pre_c + g, lim.ICL) - greatest(pre_c, lim.D)) AS ini_c,
           greatest(0, pre_c + g - greatest(pre_c, lim.ICL)) AS above_c
    FROM cum, lim
),
w AS (
    SELECT ph.*,
           sum(r * above_c) OVER (PARTITION BY version, bene_id ORDER BY fill_day, pde_id
                                  ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS w_post
    FROM ph
),
gp AS (
    SELECT w.*,
           round((least(w_post, L) - least(w_post - r * above_c, L))::DOUBLE / r)::BIGINT AS gap_c
    FROM w
),
sh AS (
    SELECT gp.*, above_c - gap_c AS cat_c,
           ded_c / 100.0 + getvariable('init_enrollee_coins') * (ini_c / 100.0)
             + (CASE WHEN lis THEN 1.0 ELSE getvariable('gap_enrollee_coins') END) * (gap_c / 100.0) AS std_pre,
           CASE WHEN brand AND NOT lis THEN round(getvariable('gap_mfr_brand') * gap_c) ELSE 0 END AS mfr_c,
           round(getvariable('cat_reins') * (above_c - gap_c)) AS reins_c,
           round(getvariable('cat_enrollee_coins') * (above_c - gap_c)) AS cat_enr_c
    FROM gp
),
fin AS (
    SELECT sh.*,
           CASE WHEN brand THEN getvariable('lis_copay_brand') ELSE getvariable('lis_copay_generic') END AS copay
    FROM sh
)
SELECT version, bene_id, pde_id, fill_day, lis, brand, gdc, active, error_type,
       (pre_c / 100.0)::DECIMAL(18, 2) AS pre,
       (ded_c / 100.0)::DECIMAL(18, 2) AS ded_amt, (ini_c / 100.0)::DECIMAL(18, 2) AS ini_amt,
       (gap_c / 100.0)::DECIMAL(18, 2) AS gap_amt, (cat_c / 100.0)::DECIMAL(18, 2) AS cat_amt,
       (mfr_c / 100.0)::DECIMAL(18, 2) AS manufacturer,
       (reins_c / 100.0)::DECIMAL(18, 2) AS reinsurance,
       (CASE WHEN lis THEN round((std_pre - least(std_pre, copay)) * 100.0) + cat_enr_c ELSE 0 END / 100.0)
           ::DECIMAL(18, 2) AS lics,
       (CASE WHEN lis THEN round(least(std_pre, copay) * 100.0) ELSE round(std_pre * 100.0) + cat_enr_c END / 100.0)
           ::DECIMAL(18, 2) AS enrollee_paid,
       ((g - mfr_c - reins_c
         - CASE WHEN lis THEN round((std_pre - least(std_pre, copay)) * 100.0) + cat_enr_c + round(least(std_pre, copay) * 100.0)
                ELSE round(std_pre * 100.0) + cat_enr_c END) / 100.0)::DECIMAL(18, 2) AS plan_paid
FROM fin;

CREATE OR REPLACE TABLE bene_pay AS
SELECT bene_id,
       sum(reinsurance + lics) FILTER (WHERE version = 'submitted') AS medicare_pde_sub,
       sum(reinsurance + lics) FILTER (WHERE version = 'corrected') AS medicare_pde_cor,
       sum(reinsurance) FILTER (WHERE version = 'submitted') AS reins_sub,
       sum(lics) FILTER (WHERE version = 'submitted') AS lics_sub,
       sum(gdc) FILTER (WHERE version = 'submitted') AS gdc_sub,
       sum(gdc) FILTER (WHERE version = 'corrected') AS gdc_cor,
       count(*) FILTER (WHERE version = 'submitted' AND active) AS n_err_pde,
       bool_or(cat_amt > 0) FILTER (WHERE version = 'submitted') AS reached_catastrophic
FROM pde_benefit GROUP BY bene_id;
