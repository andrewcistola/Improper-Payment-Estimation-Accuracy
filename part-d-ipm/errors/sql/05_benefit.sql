-- =====================================================================
-- partd errors/05_benefit.sql : post-IRA standard benefit simulation
-- ---------------------------------------------------------------------
-- Run separately for the submitted and corrected PDE streams of every
-- beneficiary, in fill order. Phases are expressed in cumulative GDC:
--   deductible   : [0, D)                    D = deductible
--   initial      : [D, I)                    I = D + (oop_threshold - D) / enrollee_coins
--   catastrophic : [I, inf)
-- Liability shares (CY 2025 parameters, config):
--                     enrollee  plan    manufacturer  Medicare reinsurance
--   deductible        100%      0       0             0
--   initial  brand    25%       65%     10%           0
--   initial  generic  25%       75%     0             0
--   catastr. brand    0         60%     20%           20%
--   catastr. generic  0         60%     0             40%
-- LIS enrollees pay a nominal copay; Medicare's low-income cost-sharing
-- subsidy (LICS) pays the rest of the enrollee share. LICS counts toward
-- TrOOP, so phase thresholds in GDC terms are unchanged.
-- Medicare PDE-driven payment = reinsurance + LICS. (Direct subsidy is
-- prospective and not changed by PDE errors; added in step 07.)
-- =====================================================================
CREATE OR REPLACE TABLE pde_benefit AS
WITH lim AS (
    SELECT getvariable('deductible')::DECIMAL(18, 2) AS D,
           (getvariable('deductible') + (getvariable('oop_threshold') - getvariable('deductible'))
             / getvariable('init_enrollee_coins'))::DECIMAL(18, 2) AS I
),
cum AS (
    SELECT v.*,
           (sum(gdc) OVER (PARTITION BY version, bene_id ORDER BY fill_day, pde_id
                           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) - gdc) AS pre
    FROM pde_versions v
),
ph AS (
    SELECT c.*, lim.D, lim.I,
           greatest(0, least(c.pre + c.gdc, lim.D) - least(c.pre, lim.D)) AS ded_amt,
           greatest(0, least(c.pre + c.gdc, lim.I) - greatest(c.pre, lim.D)) AS ini_amt,
           greatest(0, c.pre + c.gdc - greatest(c.pre, lim.I)) AS cat_amt
    FROM cum c, lim
),
sh AS (
    SELECT ph.*,
           ded_amt + getvariable('init_enrollee_coins') * ini_amt AS enrollee_std,
           CASE WHEN brand THEN getvariable('init_mfr_brand') * ini_amt + getvariable('cat_mfr_brand') * cat_amt
                ELSE 0 END AS manufacturer,
           CASE WHEN brand THEN getvariable('cat_reins_brand') * cat_amt
                ELSE getvariable('cat_reins_generic') * cat_amt END AS reinsurance
    FROM ph
)
SELECT version, bene_id, pde_id, fill_day, lis, brand, gdc, active, error_type, pre,
       usd(ded_amt) AS ded_amt, usd(ini_amt) AS ini_amt, usd(cat_amt) AS cat_amt,
       usd(manufacturer) AS manufacturer,
       usd(reinsurance) AS reinsurance,
       usd(CASE WHEN lis THEN enrollee_std - least(enrollee_std,
                    CASE WHEN brand THEN getvariable('lis_copay_brand') ELSE getvariable('lis_copay_generic') END)
                ELSE 0 END) AS lics,
       usd(CASE WHEN lis THEN least(enrollee_std,
                    CASE WHEN brand THEN getvariable('lis_copay_brand') ELSE getvariable('lis_copay_generic') END)
                ELSE enrollee_std END) AS enrollee_paid,
       usd(gdc - enrollee_std - manufacturer - reinsurance) AS plan_paid
FROM sh;

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
