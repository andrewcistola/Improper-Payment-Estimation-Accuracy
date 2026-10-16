-- =====================================================================
-- partd errors/03_init_calibration.sql : start with no active errors
-- ---------------------------------------------------------------------
-- Each PDE's candidate type was drawn in step 02 with the published
-- shares (0.7500 / 0.1786 / 0.0714); every candidate then becomes active
-- with the same probability m, so active errors keep those shares.
-- m is calibrated to GROSS improper dollars (over + under = $4.22B).
-- The over/under split is NOT forced; it follows from the error
-- directions and sizes in step 02 and is reported against $3.70B/$0.52B.
-- Pass 0: m = 0 (no errors) -> benefit run gives submitted payments.
-- Pass 1: m from a linear expectation (each PDE's marginal Medicare
--         share of its submitted dollars).
-- Pass 2: one proportional refinement, m <- m * target / realized,
--         because benefit phases and within-beneficiary netting make
--         the error nonlinear.
-- Every pass is written to truth.json (level 'calibration').
-- =====================================================================
CREATE OR REPLACE TABLE calib AS
SELECT 0 AS pass, 0.0::DOUBLE AS m, NULL::DOUBLE AS realized_gross;
