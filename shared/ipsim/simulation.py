"""Audit-finding bootstrap simulation estimator: the shared loop.

This is the one estimation method that runs in Python. It reruns each
program's payment function over the whole population 1,000 times per
audit year, which is about 20x too slow in SQL (Part D: ~1 s per
iteration in DuckDB). Everything around it -- frames, samples, findings,
scoring -- stays in SQL. Each program's payment function lives in its
estimation/simulation.py and is tested to reproduce the SQL (errors/)
result to the cent on every unit (shared/tests/test_simulation.py).

Method. Each Monte Carlo replicate is one audit year: the year's audit
is the only audit the estimator gets. For each audit and each of sim_iterations iterations:
  1. Donor findings. Every audited unit's row-level findings (PDEs, HCCs,
     payments, applications) form the donor pool, exactly as audited.
  2. Assignment. Every row of every NON-audited unit receives the finding
     of a donor row of the same kind (e.g. brand vs generic PDE; HCC
     family and severity within risk stratum), drawn uniformly at random
     (RowSet.assign). If no donor of that kind exists, the fallback kind
     is used; if none exists either, the row gets "no error". Audited
     units keep their own findings.
  3. Payment function. The program's payment function is rerun for every
     unit with the assigned findings, giving each unit's improper payment
     and the improper payment rate for each domain.
  The estimate is the mean of the iteration rates; the interval is their
  alpha/2 and 1 - alpha/2 quantiles (linear interpolation, numpy default).
  The audit itself is never resampled, so the interval reflects only the
  randomness of the assignment. (Part D also fixes a beneficiary sample
  per audit year; see part-d-ipm/estimation/simulation.py.)

Randomness: numpy PCG64 seeded from SeedSequence([scenario seed, rep]),
so every run reproduces exactly.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pyarrow as pa
from numba import njit

class RowSet:
    """Rows (PDEs, HCCs, payments, ...) sorted by unit, with donor kinds.

    unit_of_row : int array, owning unit of each row (rows sorted by unit)
    kind        : int array, donor kind of each row (0..K-1)
    identity    : bool array, True where the row's own finding is "no error"
    fallback_of_kind : optional int array (K,), second-choice kind for each
                  kind, used when the donor pool has no row of the kind

    Drawing a donor row uniformly from the pool of kind k is done in two
    equivalent steps, which only touch rows that receive an error:
      (a) the recipient gets an error with probability e_k / n_k
          (e_k = donor rows of kind k with an error, n_k = all donor rows);
          which recipients get one is drawn as a Bernoulli process by its
          geometric gaps (same distribution, ~e_k/n_k as many draws);
      (b) if so, its donor is drawn uniformly from those e_k error rows.
    """

    def __init__(self, unit_of_row, n_units, kind, identity, fallback_of_kind=None):
        self.unit_of_row = np.asarray(unit_of_row, dtype=np.int64)
        assert np.all(np.diff(self.unit_of_row) >= 0), "rows must be sorted by unit"
        self.n_units = n_units
        self.kind = np.asarray(kind, dtype=np.int64)
        self.n_kind = int(self.kind.max()) + 1 if len(self.kind) else 1
        self.identity = np.asarray(identity, dtype=bool)
        self.fallback_of_kind = None if fallback_of_kind is None else np.asarray(fallback_of_kind, dtype=np.int64)
        counts = np.bincount(self.unit_of_row, minlength=n_units)
        self.start = np.concatenate([[0], np.cumsum(counts)[:-1]])
        self.count = counts

    def rows_of(self, units):
        """Row indices of the given units (repeats allowed), in order."""
        units = np.asarray(units, dtype=np.int64)
        lengths = self.count[units]
        if lengths.sum() == 0:
            return np.empty(0, dtype=np.int64)
        offsets = np.repeat(self.start[units] - np.concatenate([[0], np.cumsum(lengths)[:-1]]), lengths)
        return offsets + np.arange(lengths.sum())

    def prepare(self, audited_mask):
        """Cache the rows of NON-audited units, grouped by kind."""
        recip = np.flatnonzero(~audited_mask[self.unit_of_row])
        order = np.argsort(self.kind[recip], kind="stable")
        recip = recip[order]
        bounds = np.searchsorted(self.kind[recip], np.arange(self.n_kind + 1))
        self._recip_by_kind = [recip[bounds[k]:bounds[k + 1]] for k in range(self.n_kind)]

    def assign(self, donor_units, rng):
        """Rows that receive an error, and the donor row of each."""
        donor_rows = self.rows_of(donor_units)
        dk = self.kind[donor_rows]
        n_k = np.bincount(dk, minlength=self.n_kind)
        err = donor_rows[~self.identity[donor_rows]]
        ek = self.kind[err]
        order = np.argsort(ek, kind="stable")
        err, ek = err[order], ek[order]
        eb = np.searchsorted(ek, np.arange(self.n_kind + 1))
        if self.fallback_of_kind is not None:   # pools by fallback kind
            fk_all = self.fallback_of_kind[dk]
            n_f = np.bincount(fk_all, minlength=self.fallback_of_kind.max() + 1)
            fe = self.fallback_of_kind[ek]
            forder = np.argsort(fe, kind="stable")
            ferr, fe = err[forder], fe[forder]
            fb = np.searchsorted(fe, np.arange(len(n_f) + 1))
        got_rows, got_donors = [], []
        for k in range(self.n_kind):
            recip = self._recip_by_kind[k]
            if len(recip) == 0:
                continue
            if n_k[k] > 0:
                pool, n = err[eb[k]:eb[k + 1]], n_k[k]
            elif self.fallback_of_kind is not None and n_f[self.fallback_of_kind[k]] > 0:
                f = self.fallback_of_kind[k]
                pool, n = ferr[fb[f]:fb[f + 1]], n_f[f]
            else:
                continue                      # no donor of this kind: no error
            if len(pool) == 0:
                continue
            pos = bernoulli_positions(len(recip), len(pool) / n, rng)
            if len(pos):
                got_rows.append(recip[pos])
                got_donors.append(pool[rng.integers(0, len(pool), len(pos))])
        if not got_rows:
            return np.empty(0, dtype=np.int64), np.empty(0, dtype=np.int64)
        return np.concatenate(got_rows), np.concatenate(got_donors)


def bernoulli_positions(n, p, rng):
    """Positions 0..n-1 that succeed in n independent Bernoulli(p) trials,
    generated from geometric gaps between successes."""
    if p <= 0 or n == 0:
        return np.empty(0, dtype=np.int64)
    if p >= 1:
        return np.arange(n)
    out, last = [], -1
    while True:
        k = int(n * p + 6 * np.sqrt(n * p) + 16)
        pos = last + np.cumsum(rng.geometric(p, k))
        if pos[-1] >= n:
            out.append(pos[pos < n])
            return np.concatenate(out)
        out.append(pos)
        last = pos[-1]


def round_half_away(x):
    """Round to the nearest integer, halves away from zero (SQL ROUND)."""
    return np.where(x >= 0, np.floor(x + 0.5), np.ceil(x - 0.5))


@njit(cache=True)
def round_half_away_scalar(x):
    return np.floor(x + 0.5) if x >= 0 else np.ceil(x - 0.5)


def load_kernel(path):
    spec = importlib.util.spec_from_file_location(Path(path).stem + "_kernel", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def population_variables(v):
    """This run's variables on top of those that built the population
    (errors/output/<scenario>/config.yaml, e.g. benefit parameters)."""
    import yaml
    from .engine import ROOT
    pop_cfg = yaml.safe_load((ROOT / v["population_dir"] / "config.yaml").read_text())["variables"]
    return {**pop_cfg, **v}


def run(con, v, kernel_module):
    """Engine entry point: run the simulation for the first sim_reps audit years.

    kernel_module.Kernel(con, v) gets the population's own variables
  (errors/output/<scenario>/config.yaml, e.g. benefit parameters) merged
  with this run's, and must provide:
      units          : number of population units
      audited(rep)   : unit indices of the audit year's audit sample
      prepare(rep, audited_mask) : called once per audit year, before its iterations
      iterate(donor_units, rng) -> {domain: rate}
    Writes table est_simulation(method, interval, rep, domain, estimate,
    se, lower, upper).
    """
    # payment-function parameters: exactly those that built the population
    # (errors/output/<scenario>/config.yaml), then this run's variables
    kernel = kernel_module.Kernel(con, population_variables(v))
    n_iter, alpha = int(v["sim_iterations"]), float(v["alpha"])
    reps = sorted(r for (r,) in con.execute("SELECT DISTINCT rep FROM sample ORDER BY rep").fetchall())
    reps = reps[: int(v["sim_reps"])]
    rows = []
    for rep in reps:
        audited = kernel.audited(rep)
        audited_mask = np.zeros(kernel.units, dtype=bool)
        audited_mask[audited] = True
        kernel.prepare(rep, audited_mask)
        rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([int(v["seed"]), rep])))
        draws = {}
        for _ in range(n_iter):
            for domain, rate in kernel.iterate(audited, rng).items():
                draws.setdefault(domain, []).append(rate)
        for domain, rates in draws.items():
            rates = np.asarray(rates)
            lo, hi = np.quantile(rates, [alpha / 2, 1 - alpha / 2])
            rows.append(("simulation", "percentile", rep, domain, float(rates.mean()),
                         float(rates.std(ddof=1)), float(lo), float(hi)))
    cols = list(zip(*rows)) if rows else [[]] * 8
    tbl = pa.table({"method": pa.array(cols[0], pa.string()), "interval": pa.array(cols[1], pa.string()),
                    "rep": pa.array(cols[2], pa.int32()), "domain": pa.array(cols[3], pa.string()),
                    "estimate": pa.array(cols[4], pa.float64()), "se": pa.array(cols[5], pa.float64()),
                    "lower": pa.array(cols[6], pa.float64()), "upper": pa.array(cols[7], pa.float64())})
    con.register("est_simulation_arrow", tbl)
    con.execute("CREATE OR REPLACE TABLE est_simulation AS SELECT * FROM est_simulation_arrow")
    con.unregister("est_simulation_arrow")
