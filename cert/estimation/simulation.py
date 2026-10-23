"""CERT: payment function and audit-finding bootstrap simulation kernel.

Payment function (same as errors/sql/02_apply_errors.sql), per claim:
  y = round(x x taint, cents), taint = improper share of the payment found
  on review: 1 for a whole-claim overpayment, in (0, 1) for a partial
  (coding) overpayment, negative for an underpayment. One error per claim,
  so each claim is netted on its own: over = sum of positive y, under =
  sum of -y where negative, gross = over + under, net = over - under.

Bootstrap simulation, from the audit year's audit, per donor kind (the
design stratum, claim type x payment quintile, 20; with sim_kind_deciles =
K > 0, stratum x K payment quantiles within the stratum, 20K -- see
sql/40_simulation_inputs.sql):
  a non-audited claim is in error with probability p = f/n (f of the n
  audited claims in error); given an error, it is partial with
  probability q = g/f (g audited errors with taint other than 1), its
  taint drawn from the stratum's audited partial taints (over or under);
  otherwise the whole claim is improper. This is the same as taking the
  finding of a random audited claim of the stratum, drawn in two steps.
  Audited claims keep their own findings.
  A kind with NO audited unit (possible only with sim_kind_deciles > 0)
  borrows its parent design stratum's pooled audit: p, q, the partial list
  and the parametric redraw all come from the stratum's audited units
  (stratum = kind // K). A kind with audited units but no failure stays
  at zero, as before.
  sim_rates: fixed       rates as audited
             parametric  before each iteration the counts are redrawn: the
                         error count f~ = Binomial(n, p), then the partial
                         count out of it, g~ = Binomial(f~, q), so p~ = f~/n
                         and q~ = g~/f~ (0 when f~ = 0)
Non-audited claims without an assigned error have y = 0, so each
iteration adds the assigned errors to the audited claims' totals instead
of rerunning 5.3 million zeros.
Domains: national|over, national|under, national|gross, national|net,
<claim type>|gross.
"""
import numpy as np

from ipsim.simulation import bernoulli_positions, round_half_away

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
        self.n_kind = int(self.kind.max()) + 1          # 20, or 20 x sim_kind_deciles
        self.stratum = np.asarray(u["stratum_kind"], dtype=np.int64)
        self.stratum_of_kind = np.zeros(self.n_kind, dtype=np.int64)   # kind -> design stratum (identity when K = 0)
        self.stratum_of_kind[self.kind] = self.stratum
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
        for h in range(self.n_kind):
            ah = np.flatnonzero(audited_mask & (self.kind == h))
            if len(ah) == 0:   # no audited claim of this kind: the parent stratum's pooled audit
                ah = np.flatnonzero(audited_mask & (self.stratum == self.stratum_of_kind[h]))
            err = self.y[ah] != 0
            part = err & (self.y[ah] != self.x[ah])
            self._n.append(len(ah)); self._f.append(int(err.sum())); self._g.append(int(part.sum()))
            self._partial.append(self.taint[ah][part])
            self._recip.append(np.flatnonzero(~audited_mask & (self.kind == h)))

    def iterate(self, donors, rng):
        ys, ts = [self._ya], [self._ta]
        for h in range(self.n_kind):
            n, f, g = self._n[h], self._f[h], self._g[h]
            p = f / n if n else 0.0
            q = g / f if f else 0.0
            if self.parametric:   # redraw the error count first, then the partial count out of it
                f_t = int(rng.binomial(n, p)) if n else 0
                p = f_t / n if n else 0.0
                q = rng.binomial(f_t, q) / f_t if f_t else 0.0
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
