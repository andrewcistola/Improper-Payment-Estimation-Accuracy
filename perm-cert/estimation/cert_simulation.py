"""CERT: payment function and audit-finding bootstrap simulation kernel.

Payment function (same as errors/sql/cert_02_apply_errors.sql), per claim:
  y = round(x x taint, cents), taint = improper share of the payment found
  on review: 1 for a whole-claim overpayment, in (0, 1) for a partial
  (coding) overpayment, negative for an underpayment. One error per claim,
  so each claim is netted on its own: over = sum of positive y, under =
  sum of -y where negative, gross = over + under, net = over - under.

Bootstrap simulation, from the audit year's audit, per stratum (claim type
x payment quintile, 20):
  a non-audited claim is in error with probability p = f/n (f of the n
  audited claims in error); given an error, it is partial with
  probability q = g/f (g audited errors with taint other than 1), its
  taint drawn from the stratum's audited partial taints (over or under);
  otherwise the whole claim is improper. This is the same as taking the
  finding of a random audited claim of the stratum, drawn in two steps.
  Audited claims keep their own findings.
  sim_rates: fixed       rates as audited
             parametric  before each iteration p and q are redrawn as
                         Binomial(n, p)/n and Binomial(f, q)/f
Non-audited claims without an assigned error have y = 0, so each
iteration adds the assigned errors to the audited claims' totals instead
of rerunning 5.3 million zeros.
Domains: national|over, national|under, national|gross, national|net,
<claim type>|gross.
"""
import numpy as np

from ipsim.simulation import bernoulli_positions, round_half_away

N_KIND = 20
TYPES = ("ipps", "part_a_other", "part_b", "dmepos")   # type_code 0..3


class Kernel:
    def __init__(self, con, v):
        self.con = con
        self.parametric = str(v.get("sim_rates", "fixed")) == "parametric"
        u = con.execute("SELECT * FROM sim_units ORDER BY unit_idx").fetchnumpy()
        self.units = len(u["unit_idx"])
        self.unit_id = np.asarray(u["unit_id"])
        self.x = np.asarray(u["x_cents"], dtype=np.int64)
        self.y = np.asarray(u["y_cents"], dtype=np.int64)
        self.taint = self.y / self.x
        self.kind = np.asarray(u["kind"], dtype=np.int64)
        self.type = np.asarray(u["type_code"], dtype=np.int64)
        self.X = float(self.x.sum())
        self.X_type = np.bincount(self.type, weights=self.x, minlength=4)

    def improper_cents(self, taint):
        """y per claim (cents) given each claim's taint."""
        return round_half_away(self.x * taint).astype(np.int64)

    def _rates(self, y, t):
        over, under = float(y[y > 0].sum()), float(-y[y < 0].sum())
        g = np.bincount(t, weights=np.abs(y), minlength=4)
        out = {"national|over": over, "national|under": under,
               "national|gross": over + under, "national|net": over - under}
        return {k: v / self.X for k, v in out.items()} | \
               {f"{TYPES[c]}|gross": float(g[c]) / self.X_type[c] for c in range(4)}

    def audited(self, rep):
        s = self.con.execute("SELECT unit_id FROM sample WHERE rep = ? AND domain = 'national|gross' "
                             "ORDER BY unit_id", [rep]).fetchnumpy()
        return np.searchsorted(self.unit_id, np.asarray(s["unit_id"]))

    def prepare(self, rep, audited_mask):
        a = np.flatnonzero(audited_mask)
        self._ya, self._ta = self.y[a], self.type[a]          # audited claims keep their findings
        self._n, self._f, self._g, self._partial, self._recip = [], [], [], [], []
        for h in range(N_KIND):
            ah = np.flatnonzero(audited_mask & (self.kind == h))
            err = self.y[ah] != 0
            part = err & (self.y[ah] != self.x[ah])
            self._n.append(len(ah)); self._f.append(int(err.sum())); self._g.append(int(part.sum()))
            self._partial.append(self.taint[ah][part])
            self._recip.append(np.flatnonzero(~audited_mask & (self.kind == h)))

    def iterate(self, donors, rng):
        ys, ts = [self._ya], [self._ta]
        for h in range(N_KIND):
            n, f, g = self._n[h], self._f[h], self._g[h]
            p = f / n if n else 0.0
            q = g / f if f else 0.0
            if self.parametric:
                p = rng.binomial(n, p) / n if n else 0.0
                q = rng.binomial(f, q) / f if f else 0.0
            if p <= 0:
                continue
            hit = self._recip[h][bernoulli_positions(len(self._recip[h]), p, rng)]
            taint = np.ones(len(hit))
            if len(self._partial[h]):
                part = rng.random(len(hit)) < q
                taint[part] = self._partial[h][rng.integers(0, len(self._partial[h]), int(part.sum()))]
            ys.append(self.improper_cents_rows(hit, taint)); ts.append(self.type[hit])
        return self._rates(np.concatenate(ys), np.concatenate(ts))

    def improper_cents_rows(self, rows, taint):
        return round_half_away(self.x[rows] * taint).astype(np.int64)
