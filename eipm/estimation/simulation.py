"""EIPM: payment function and audit-finding bootstrap simulation kernel.

Payment function (same as errors/sql/01_population.sql and 02):
  applicable % = linear within the configured %FPL bands (enhanced schedule)
  APTC/month   = round(max(0, benchmark - applicable% x income / 12), cents)
                 income = %FPL / 100 x poverty guideline for the household
  annual APTC  = APTC/month x months
  y (monetary)  = APTC paid - APTC at the income the record supports
  y (technical) = APTC paid
Every error is an overpayment. Float arithmetic follows the SQL;
shared/tests/test_simulation.py checks that each application's own finding
reproduces errors/ y to the cent.

Bootstrap simulation, from the audit year's audit, per stratum (APTC
quintile):
  a non-audited application is in error with probability p = f/n (f of the
  n audited applications in error); given an error, it is monetary with
  probability q = g/f (g audited monetary errors), its supported / used
  income ratio drawn from the stratum's audited monetary findings and its
  APTC recomputed (supported income clipped to 100-600% FPL); otherwise it
  is technical (whole APTC). This is the same as taking the finding of a
  random audited application of the stratum, drawn in two steps.
  Audited applications keep their own findings.
  sim_rates: fixed       rates as audited
             parametric  before each iteration p and q are redrawn as
                         Binomial(n, p)/n and Binomial(f, q)/f
Domains: national|gross, national|technical, national|monetary.
"""
import json

import numpy as np

from ipsim.simulation import bernoulli_positions, round_half_away

N_STRATA = 5


def applicable_pct(f, schedule):
    out = np.full(len(f), np.nan)
    for b in schedule:
        m = (f >= b["lo"]) & (f < b["hi"])
        out[m] = b["p_lo"] + (b["p_hi"] - b["p_lo"]) * (f[m] - b["lo"]) / (b["hi"] - b["lo"])
    return np.where(np.isnan(out), 0.085, out)


def annual_aptc_cents(fpl_pct, benchmark, fpl_dollars, months, schedule):
    monthly = np.maximum(0.0, benchmark - applicable_pct(fpl_pct, schedule) * fpl_pct / 100.0 * fpl_dollars / 12.0)
    return round_half_away(monthly * 100.0).astype(np.int64) * months


class Kernel:
    def __init__(self, con, v):
        self.con = con
        self.parametric = str(v.get("sim_rates", "fixed")) == "parametric"
        u = con.execute("SELECT * FROM sim_units ORDER BY unit_idx").fetchnumpy()
        sched = v["applicable_schedule"]
        self.schedule = json.loads(sched) if isinstance(sched, str) else sched
        self.units = len(u["unit_idx"])
        self.unit_id = np.asarray(u["unit_id"])
        self.fpl = np.asarray(u["fpl_pct"], dtype=float)
        self.bench = np.asarray(u["benchmark_month"], dtype=float)
        self.months = np.asarray(u["months"], dtype=np.int64)
        self.fpl_dollars = float(v["fpl_base"]) + float(v["fpl_per_person"]) * (np.asarray(u["hh_size"]) - 1)
        self.x = np.asarray(u["x_cents"], dtype=np.int64)
        self.X = float(self.x.sum())
        self.finding = np.asarray(u["finding"], dtype=np.int64)
        self.ratio = np.asarray(u["income_ratio"], dtype=float)
        self.true_fpl = np.asarray(u["true_fpl_pct"], dtype=float)
        self.kind = np.asarray(u["stratum_code"], dtype=np.int64)

    def improper_cents(self, finding, supported_fpl):
        """y per application (cents) by component, given findings."""
        tech = np.where(finding == 2, self.x, 0)
        mon = np.zeros(self.units, dtype=np.int64)
        inc = np.flatnonzero(finding == 1)
        correct = annual_aptc_cents(supported_fpl[inc], self.bench[inc], self.fpl_dollars[inc],
                                    self.months[inc], self.schedule)
        mon[inc] = self.x[inc] - correct
        return {"gross": tech + mon, "technical": tech, "monetary": mon}

    def audited(self, rep):
        s = self.con.execute("SELECT unit_id FROM sample WHERE rep = ? AND domain = 'national|gross' "
                             "ORDER BY unit_id", [rep]).fetchnumpy()
        return np.searchsorted(self.unit_id, np.asarray(s["unit_id"]))

    def prepare(self, rep, audited_mask):
        self._finding = np.where(audited_mask, self.finding, 0)
        self._fpl = np.where(audited_mask & (self.finding == 1), self.true_fpl, self.fpl)
        self._n, self._f, self._g, self._ratios, self._recip = [], [], [], [], []
        for h in range(N_STRATA):
            a = np.flatnonzero(audited_mask & (self.kind == h))
            fnd = self.finding[a]
            self._n.append(len(a)); self._f.append(int((fnd > 0).sum())); self._g.append(int((fnd == 1).sum()))
            self._ratios.append(self.ratio[a][fnd == 1])
            self._recip.append(np.flatnonzero(~audited_mask & (self.kind == h)))

    def iterate(self, donors, rng):
        finding, fpl = self._finding.copy(), self._fpl.copy()
        for h in range(N_STRATA):
            n, f, g = self._n[h], self._f[h], self._g[h]
            p = f / n if n else 0.0
            q = g / f if f else 0.0
            if self.parametric:
                p = rng.binomial(n, p) / n if n else 0.0
                q = rng.binomial(f, q) / f if f else 0.0
            if p <= 0:
                continue
            hit = self._recip[h][bernoulli_positions(len(self._recip[h]), p, rng)]
            mon = (rng.random(len(hit)) < q) if len(self._ratios[h]) else np.zeros(len(hit), bool)
            finding[hit[~mon]] = 2
            mh = hit[mon]
            if len(mh):
                finding[mh] = 1
                r = self._ratios[h][rng.integers(0, len(self._ratios[h]), len(mh))]
                fpl[mh] = np.clip(self.fpl[mh] * r, 100.0, 600.0)
        y = self.improper_cents(finding, fpl)
        return {f"national|{k}": float(v.sum()) / self.X for k, v in y.items()}
