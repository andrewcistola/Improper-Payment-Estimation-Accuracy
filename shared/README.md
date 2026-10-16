# shared/

Code used by all four programs. Each program folder states *what* is estimated and *how it is sampled*; the code here defines *how* every estimator and interval is computed, once.

| Path | Contents |
|---|---|
| `ipsim/engine.py` | Runner: reads a config, sets variables, runs its SQL files in order, writes outputs and `manifest.json` (SHA-256 of every file). Orchestration only. |
| `sql/lib/00_rng.sql` | Counter-based random numbers: every draw is a hash of `(seed, stream, key)`, so results do not depend on thread scheduling or row order |
| `sql/lib/01_stats.sql` | Normal CDF and quantile (DuckDB has none), list quantiles, and order-independent floating-point sums |
| `sql/lib/02_estimators.sql` | **The analytic methods**: expansion, ratio and regression (GREG) with normal intervals, plus scoring. Formulas are written out in the file header. |
| `ipsim/simulation.py` | **The audit-finding simulation**: the shared loop (donor findings exactly as audited, assignment by kind, 1,000 iterations). Each program's payment function is in its `estimation/*simulation.py`. |
| `sql/sample_srs.sql`, `sql/sample_systematic.sql` | Monte Carlo sampling within strata: SRS without replacement, or systematic selection after sorting by amount paid. Each program's config names the one its design uses. |
| `sql/report.sql`, `report.yaml` | Fabricated truth vs every estimate and CI: `results/report/by_scenario.csv` (one row per scenario × method, with sample 1 as a worked example and the count of CIs containing the truth) and `by_sample.parquet` (every sample) |
| `sql/summary.sql`, `summary.yaml` | All `metrics.json` files in one table |
| `tests/` | RNG independence, normal functions vs scipy, exact sample sizes, **estimators vs an independent numpy implementation**, byte-identical reruns |
| `data_dictionary.md` | Every column of every output |

## How a program uses it

```
<program>/errors/config.yaml       population SQL -> fake-error SQL -> truth -> checks
<program>/estimation/config.yaml   01_frame.sql          estimand (y, x), strata, sample sizes
                                   shared/sql/sample_srs.sql (or sample_systematic.sql)  Monte Carlo samples
                                   10_expansion.sql      SELECT * FROM ipm_expansion(alpha)
                                   20_ratio.sql          SELECT * FROM ipm_ratio(alpha)
                                   30_regression.sql     SELECT * FROM ipm_regression(alpha)
                                   40_simulation_inputs.sql + simulation.py   audit-finding simulation
                                   90_score.sql          SELECT * FROM ipm_score()
```

All configs and SQL paths are relative to the repository root. Run any config with `ipsim <config.yaml>`. Useful flags:

- `--timing` prints each step's run time.
- `--set reps=20 sim_reps=3 sim_iterations=100` overrides variables for a quick pilot run.
- `--out <dir>` writes the outputs somewhere else.

## Things a reviewer should know

- **Inputs are declared before the macros.** DuckDB binds table macros when they are defined. `02_estimators.sql` therefore declares its input tables (`sample`, `frame_totals`, `estimates`) at the top; each program then replaces them with data. The declarations double as the input contract.
- **Random keys are hashed as one string.** Multi-argument `hash(a, b)` produced correlated draws in testing. High-volume streams hash one string per stream, then one integer per draw (10× faster, same independence test).
- **Identifiers are case-insensitive.** `N_h` and `n_h` would be the same column in DuckDB, so the code uses `pop_h`/`samp_h` and `big_n`/`small_n`.
- **Sums are exact or order-fixed.** Money is `DECIMAL`, and every floating-point sum uses `fsum` (sort, then add). That keeps output files byte-identical across thread counts.
- **Why the simulation is in Python.** It reruns a payment function over the whole population 1,000 times per audited sample; in DuckDB that takes about 1 s per Part D iteration (17 minutes per sample). numpy, with numba compiling the Part D benefit loop, does it in 0.07 s. Each numpy payment function is tested to reproduce the SQL result in `errors/` to the cent for every unit.
- **Simulation edge cases:**
  - A recipient row whose kind has no audited donor takes the fallback kind (Part C: same HCC family and severity in any stratum); if there is none, it gets "no error".
  - An interval that cannot be formed counts as not covering the truth, and the scorer reports how many there were (`n_undefined`).

Run the tests with `python -m pytest -q shared/tests` from the repository root.
