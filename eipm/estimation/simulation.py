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

Bootstrap simulation, from the audit year's audit, per donor kind (the
design stratum, APTC quintile; with sim_kind_deciles = K > 0, stratum x K
APTC quantiles within the stratum -- see sql/40_simulation_inputs.sql),
with n audited applications, t of them technical and g monetary
findings (f = t + g in error):
  a non-audited application is technical (whole APTC) with probability
  p_t = t/n; an application that CAN have a monetary finding is monetary
  with probability p_m = g/n_m, where n_m counts the audited applications
  that can have one. Its supported / used income ratio is drawn from the
  stratum's audited monetary findings and its APTC recomputed (supported
  income clipped to 100-600% FPL). The two are drawn as one hit with
  probability p_t + p_m, monetary with probability p_m / (p_t + p_m) (at
  most one error per application, as in errors/02_apply_errors.sql).
  Monetary findings and y = 0. errors/02_apply_errors.sql makes a monetary
  candidate an error only when the recomputed APTC is below the APTC paid,
  so every audited monetary finding has y > 0. The kernel keeps that
  property on the recipients' side, otherwise applications given a
  monetary finding that cannot move their APTC would dilute the monetary
  rate (about 4.6% of applications here):
    - an application whose income is already at the 600% FPL cap can never
      have a monetary finding (any supported income clips to 600%); such
      applications are excluded from n_m and from monetary assignment
      (they can still be technical);
    - an application whose recomputed APTC equals the APTC paid under the
      drawn ratio (income below 150% FPL staying below 150%, where the
      applicable percentage is 0) draws another ratio, up to MAX_REDRAW
      times; what is left after that (practically none) stays y = 0.
  Audited applications keep their own findings.
  A kind with NO audited application (possible only with sim_kind_deciles > 0)
  borrows its parent design stratum's pooled audit: p, q, the ratio list
  and the parametric redraw all come from the stratum's audited applications
  (stratum = kind // K). A kind with audited applications but no failure stays
  at zero, as before.
  sim_rates: fixed       rates as audited
             parametric  before each iteration the counts are redrawn: the
                         error count f~ = Binomial(n, f/n), then the
                         monetary count out of it, g~ = Binomial(f~, g/f)
                         (0 when f~ = 0), t~ = f~ - g~, so p_t~ = t~/n and
                         p_m~ = g~/n_m
Domains: national|gross, national|technical, national|monetary.
"""
import json

import numpy as np

from ipsim.simulation import bernoulli_positions, round_half_away

FPL_CAP = 600.0     # income is capped at 600% FPL in errors/01_population.sql
MAX_REDRAW = 50


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
        self.kind = np.asarray(u["kind"], dtype=np.int64)   # donor kind: stratum, or stratum x quantile
        self.n_kind = int(self.kind.max()) + 1               # 5, or 5 x sim_kind_deciles
        self.stratum = np.asarray(u["stratum_code"], dtype=np.int64)
        self.stratum_of_kind = np.zeros(self.n_kind, dtype=np.int64)   # kind -> design stratum (identity when K = 0)
        self.stratum_of_kind[self.kind] = self.stratum
        self.can_monetary = self.fpl < FPL_CAP     # at the cap no supported income lowers the APTC

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
        self._n, self._n_m, self._f, self._g, self._ratios = [], [], [], [], []
        self._recip, self._recip_m = [], []
        for h in range(self.n_kind):
            a = np.flatnonzero(audited_mask & (self.kind == h))
            if len(a) == 0:   # no audited unit of this kind: the parent stratum's pooled audit
                a = np.flatnonzero(audited_mask & (self.stratum == self.stratum_of_kind[h]))
            fnd = self.finding[a]
            self._n.append(len(a)); self._n_m.append(int(self.can_monetary[a].sum()))
            self._f.append(int((fnd > 0).sum())); self._g.append(int((fnd == 1).sum()))
            self._ratios.append(self.ratio[a][fnd == 1])
            r = ~audited_mask & (self.kind == h)
            self._recip.append(np.flatnonzero(r & ~self.can_monetary))   # technical only
            self._recip_m.append(np.flatnonzero(r & self.can_monetary))  # technical or monetary

    def iterate(self, donors, rng):
        finding, fpl = self._finding.copy(), self._fpl.copy()
        for h in range(self.n_kind):
            n, n_m, f, g = self._n[h], self._n_m[h], self._f[h], self._g[h]
            if self.parametric:   # redraw the error count first, then the monetary count out of it
                f = int(rng.binomial(n, f / n)) if n else 0
                g = int(rng.binomial(f, g / self._f[h])) if f and self._f[h] else 0
            p_t = (f - g) / n if n else 0.0
            p_m = g / n_m if (n_m and len(self._ratios[h])) else 0.0
            # applications at the income cap: technical only
            if p_t > 0:
                finding[self._recip[h][bernoulli_positions(len(self._recip[h]), p_t, rng)]] = 2
            # the rest: one hit, technical or monetary
            p = p_t + p_m
            if p <= 0:
                continue
            hit = self._recip_m[h][bernoulli_positions(len(self._recip_m[h]), p, rng)]
            mon = rng.random(len(hit)) < p_m / p
            finding[hit[~mon]] = 2
            mh = hit[mon]
            if len(mh):
                finding[mh] = 1
                fpl[mh] = self._supported_fpl(mh, self._ratios[h], rng)
        y = self.improper_cents(finding, fpl)
        return {f"national|{k}": float(v.sum()) / self.X for k, v in y.items()}

    def _supported_fpl(self, rows, ratios, rng):
        """Supported income (% FPL) for monetary recipients: a donor ratio,
        redrawn while the recomputed APTC still equals the APTC paid (an
        audited monetary finding always has y > 0)."""
        out = np.clip(self.fpl[rows] * ratios[rng.integers(0, len(ratios), len(rows))], 100.0, FPL_CAP)
        for _ in range(MAX_REDRAW):
            same = np.flatnonzero(annual_aptc_cents(out, self.bench[rows], self.fpl_dollars[rows],
                                                    self.months[rows], self.schedule) == self.x[rows])
            if not len(same):
                break
            r = ratios[rng.integers(0, len(ratios), len(same))]
            out[same] = np.clip(self.fpl[rows[same]] * r, 100.0, FPL_CAP)
        return out
