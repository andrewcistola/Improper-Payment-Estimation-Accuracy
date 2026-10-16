# Synthetic Data

Synthetic finite populations with **known true improper payments**, for testing whether improper payment estimates (expansion, ratio, regression/GREG and bootstrap) hold their stated accuracy under each CMS program's sampling design. This implements step 1 ("Build populations") of the study pipeline in [`../literature-review/`](../literature-review/bootstrap-simulation-for-improper-payment-estimation-in-cms-programs.md).

**Scope: improper payment rate estimation for PIIA reporting only.** Recovery and extrapolation uses (contract-level RADV audits, provider overpayment demands) are out of scope.

No PHI, no unit-level data from any source, and nothing non-public. Every number is drawn from stated distributions and calibrated only to public aggregate results.

## Design principles (for expert review)

1. **SQL does the work.** Generation, error injection, the Part D benefit, calibration, sampling, estimators and truth are DuckDB SQL in `src/sql/`. Python only reads configs, runs the SQL files in order and writes the outputs.
2. **Few scenarios, each named.** One base scenario per program, plus the published FFS stress grid and the PERM 3% grid.
3. **Errors are stated probabilities.** Each error is a Bernoulli draw whose probability is written in the SQL header and config. Calibration to a public rate is one closed-form multiplier, `m = target $ / expected $ at m = 1`, logged in `truth.json`.
4. **Every dollar is traceable.** Unit-level detail (HCCs, PDEs, payments) is exported, so any enrollee's or beneficiary's error can be recomputed by hand from its rows.
5. **Exact and reproducible.** Every random draw is a hash of `(seed, stream, key)`, and every dollar is `DECIMAL`. Same config and seed give byte-identical files at any thread count (`tests/test_determinism.py`). `manifest.json` records SHA-256 hashes and the DuckDB version.

## Quick start

```bash
cd synthetic-data
pip install -e .                       # duckdb (pinned), pyarrow, numpy, pyyaml
ipsim config/*.yaml                    # build all populations into output/  (~1 min)
python -m ipsim.validate all           # calibration, benchmark, smoke tests -> output/validation/report.md
python -m pytest -q tests              # RNG, sampler and determinism tests
```

## The four applications

| # | Application | Config | Unit | Error mechanism | Calibrated to (public) |
|---|---|---|---|---|---|
| 1 | Claim errors flowing through a benefit to reinsurance/subsidy (**Part D**) | `partd.yaml` | Beneficiary (cluster of PDEs) | PDE-level: missing documentation (GDC → 0), pricing (±~12%), drug discrepancy (cheaper/costlier drug); corrected PDEs re-run through the **CY 2025 post-IRA benefit**; error = Δ(reinsurance + LICS) | Gross 4.00%; over $3.70B / under $0.52B; type shares 75.00 / 17.86 / 7.14 |
| 2 | Risk-score errors on capitated payments (**Part C IPM**) | `partc.yaml` | Enrollee | HCC unsupported (deletion, or severe→mild hierarchy move); missing documentation (all HCCs deleted); additional HCC (underpayment) | Gross 6.09%; over $21.43B / under $2.23B; missing doc 0.22% |
| 3 | Claim/benefit errors (**CERT/PIM** stress, **PERM**) | `ffs_stress.yaml`, `perm.yaml` | Claim / payment | FFS: all-or-nothing on exactly round(p·N) claims. PERM: claims errors per payment plus beneficiary eligibility errors (all of that beneficiary's payments) | Edwards et al. (2023) payment shapes; Medicaid overall 6.12%; nine states at true eligibility rates 2.00–4.00% |
| 4 | Beneficiary subsidy eligibility (**Marketplace APTC / EIPM**) | `eipm.yaml` | FFE application | Income misstatement (APTC recomputed, two-sided), eligibility failure and missing documentation (all-or-nothing) | Gross 0.89% |

### Where calibration targets come from

All targets are FY 2025 public results unless noted; sources are in the literature review. Interpretations a reviewer should check:

- **Part C:** the public 5.51% total overpayment is read as 5.29% unsupported diagnoses plus 0.22% missing documentation.
- **Part D:** the payment error is Medicare's change in reinsurance plus low-income cost-sharing (LICS) when corrected PDEs are re-run through the benefit. The direct subsidy is prospective and therefore never in error.
- **Part D:** the over/under split is not forced. It follows from one structural parameter (the costlier-drug factor, 3.5, tuned once) and is reported against the target.
- **PERM:** the 6.12% Medicaid rate is a pooled sanity check, not an exact target. The real national rate rolls three cycles.

### Values that are NOT public (illustrative; flagged in configs)

- HCC families A–J and their coefficients (not CMS-HCC values)
- Part C, Part D and EIPM sample sizes and strata
- PERM claims error probabilities and state FMAPs
- EIPM error type split, benchmark premium and age curve
- Payment distributions for every program

Each is a named config value or a commented SQL literal, so a reviewer can change it and rebuild.

## Pipeline

```
config/<program>.yaml ──► src/ipsim/engine.py (sets variables, runs steps in order)
   │
   ├─ src/sql/lib/rng.sql             hash-based RNG macros (uniform, normal, lognormal, Kumaraswamy, weighted keys)
   ├─ src/sql/<program>/NN_*.sql      numbered generation steps (headers explain each mechanism)
   └─ output/<program>/<scenario>/
         population.parquet           one row per sampling unit: unit_id, stratum, x (paid), y (true error), error_type, program fields
         <detail>.parquet             hcc_detail / pde_detail / contracts / states
         truth.json                   true totals, rates, component rates, calibration multipliers
         design.yaml                  production design: strata, sample sizes, selection rule, estimator
         config.yaml                  every variable and the scenario seed
         manifest.json                SHA-256 of every file, DuckDB and Python versions
src/sql/estimate/sample.sql           replicate samples: SRS w/o replacement, or systematic after sorting by x
src/sql/estimate/estimators.sql       expansion, ratio, regression (GREG, one auxiliary), rate
src/sql/validate/ffs_benchmark.sql    Edwards et al. Fig. 4.1 replication
```

`x` is the amount paid and `y` the true improper amount (positive = overpayment, negative = underpayment). `w_pop` is the scale weight: 1 synthetic unit represents `w_pop` real units, so dollar truths are reported on the national scale.

## Validation (current results: `output/validation/report.md`)

- **Calibration:** 23 of 23 checks within tolerance. For example, Part C gross is 6.06% (target 6.09%), Part D 3.98% (target 4.00%), EIPM 0.93% (target 0.89%). Every PERM state's true eligibility rate is at or below its grid value, and within 0.02 points of it.
- **Benchmark (checks the payment shapes only):** reproduces the Edwards et al. (2023) pattern. With an SRS of 30 and the normal 90% lower bound, coverage holds at or above 90% for right-skewed payments. It falls to 87–89% for two-spike and 82–87% for left-skewed payments once the error rate exceeds 0.6.
- **Smoke test:** one production-style design per program (stratified SRS, systematic PERM selection) is unbiased for the true rate or total over 300 draws, within 3.5 Monte Carlo standard errors.
- **Tests:** RNG independence and moments, exact sample sizes, byte-identical output at 1 and 4 threads.

## Two pitfalls found while building (worth knowing for review)

1. **DuckDB's multi-argument `hash(a, b, c)` is not a good random key.** Draws that differed in only one argument were strongly correlated: "independent" SRS replicates shared 24 of 30 units, against 3.6 expected. `rng.sql` hashes one concatenated string instead, and `tests/test_rng.py` guards the fix.
2. **SQL identifiers are case-insensitive.** The textbook names `N_h` and `n_h` refer to the *same* column in DuckDB. The sampler uses `pop_h` and `samp_h` instead.

## Not yet built (next steps, in the aims)

- Interval methods: analytic normal/t, design (Rao–Wu rescaled) bootstrap with percentile, bootstrap-t and BCa intervals.
- GREG with several auxiliaries (and, if wanted, a model-assisted version with ML predictions as the auxiliary).
- Coverage scoring at 10,000 replications per cell.
- Optional measurement error (reviewer misclassification, appeal overturns).

## Storage

Only the small reference populations (`ffs_stress`, `eipm`, `partc`) are committed with their Parquet files. For the larger programs, the repository keeps `truth.json`, `design.yaml`, `config.yaml` and `manifest.json`. Regenerating the Parquet files and comparing hashes against the committed manifests verifies a rebuild.
