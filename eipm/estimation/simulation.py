"""EIPM: payment function and audit-finding simulation kernel.

Payment function (same as errors/sql/01_population.sql and 02):
  applicable % = linear within the configured %FPL bands (enhanced schedule)
  APTC/month   = round(max(0, benchmark - applicable% x income / 12), cents)
                 income = %FPL / 100 x poverty guideline for the household
  annual APTC  = APTC/month x months
  y (income misstatement) = APTC paid - APTC at the income the record supports
  y (eligibility failure or missing documentation) = APTC paid
Float arithmetic follows the SQL; shared/tests/test_simulation.py checks
that each application's own finding reproduces errors/ y to the cent.

Audit finding transferred (application level): error type and, for an
income misstatement, the ratio supported income / reported income; the
recipient's supported income is clip(reported x ratio, 100%, 600% FPL).
Donor kind: income-band stratum.
"""
import json

import numpy as np

from ipsim.simulation import RowSet, round_half_away


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
        self.apps = RowSet(np.arange(self.units), self.units, kind=np.asarray(u["stratum_code"], dtype=np.int64),
                           identity=(self.finding == 0))

    def improper_cents(self, finding, supported_fpl):
        y = np.zeros(self.units, dtype=np.int64)
        y[finding >= 2] = self.x[finding >= 2]
        inc = np.flatnonzero(finding == 1)
        correct = annual_aptc_cents(supported_fpl[inc], self.bench[inc], self.fpl_dollars[inc],
                                    self.months[inc], self.schedule)
        y[inc] = self.x[inc] - correct
        return y

    def audited(self, rep):
        s = self.con.execute("SELECT unit_id FROM sample WHERE rep = ? AND domain = 'national' "
                             "ORDER BY unit_id", [rep]).fetchnumpy()
        return np.searchsorted(self.unit_id, np.asarray(s["unit_id"]))

    def prepare(self, rep, audited_mask):
        self.apps.prepare(audited_mask)
        self._finding = np.where(audited_mask, self.finding, 0)
        self._fpl = np.where(audited_mask & (self.finding == 1), self.true_fpl, self.fpl)

    def iterate(self, donors, rng):
        finding, fpl = self._finding.copy(), self._fpl.copy()
        units, d = self.apps.assign(donors, rng)
        finding[units] = self.finding[d]
        fpl[units] = np.clip(self.fpl[units] * self.ratio[d], 100.0, 600.0)
        y = self.improper_cents(finding, fpl)
        return {"national": float(np.abs(y).sum()) / self.X}
