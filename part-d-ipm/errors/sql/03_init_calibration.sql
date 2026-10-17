-- =====================================================================
-- partd errors/03_init_calibration.sql : error rates as stated
-- ---------------------------------------------------------------------
-- No calibration: a PDE's candidate error (step 02) is active with
-- probability error_rate (2.5%), or ltc_error_rate (10%) for LTC claims.
-- Gross, over and under dollars are outcomes, reported in truth.json and
-- compared with FY 2025 in checks.json. The calib table records m = 1
-- (rates used as stated) for the truth file.
-- =====================================================================
CREATE OR REPLACE TABLE calib AS
SELECT 1 AS pass, 1.0::DOUBLE AS m, NULL::DOUBLE AS realized_gross;
