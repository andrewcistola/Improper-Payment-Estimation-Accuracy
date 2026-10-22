"""PERM: payment function and audit-finding bootstrap simulation kernel (one state).

Payment function (same as errors/sql/perm_02 and perm_03), per payment:
  claims error      y_claims = round(x x taint, cents)
  eligibility error y_elig   = x if the beneficiary is in error, else 0
  gross             y        = x if eligibility error, else y_claims
                               (= claims + eligibility - overlap)
Every PERM error is an overpayment (y >= 0). Rates are sum y / sum x within
the state (FMAP is constant within a state, so the federal-share rate is
the same).

Bootstrap simulation, from the audit year's audit:
  claims      : per stratum (payment type x payment quintile), a non-audited
                payment is in error with probability p = f/n (f of n
                audited payments in error); given an error, it is partial
                with probability q = g/f (g audited errors with taint < 1),
                its taint drawn from the stratum's audited partial taints;
                otherwise the whole payment is improper. This is the same
                as taking the finding of a random audited payment of the
                stratum, drawn in two steps.
  eligibility : a beneficiary none of whose payments was sampled is in
                error with probability p_e = audited beneficiaries in error /
                audited beneficiaries.
  Audited payments and beneficiaries keep their own findings.
  sim_rates: fixed       rates as audited
             parametric  before each iteration the counts are redrawn: the
                         error count f~ = Binomial(n, p), then the partial
                         count out of it, g~ = Binomial(f~, q), so p~ = f~/n and
                         q~ = g~/f~ (0 when f~ = 0); eligibility p_e~ =
                         Binomial(n_e, p_e)/n_e
"""
import numpy as np

from ipsim.simulation import bernoulli_positions, round_half_away

N_KIND = 10   # payment type (FFS, MC) x 5 payment quintiles


class Kernel:
    def __init__(self, con, v):
        self.con = con
        self.state = int(v["state_id"])
        self.parametric = str(v.get("sim_rates", "fixed")) == "parametric"
        u = con.execute("SELECT * FROM sim_units ORDER BY unit_idx").fetchnumpy()
        self.units = len(u["unit_idx"])
        self.unit_id = np.asarray(u["unit_id"])
        self.x = np.asarray(u["x_cents"], dtype=np.int64)
        self.X = float(self.x.sum())
        self.yc = np.asarray(u["y_claims_cents"], dtype=np.int64)
        self.taint = self.yc / self.x
        self.kind = np.asarray(u["claims_kind"], dtype=np.int64)
        bene = np.asarray(u["bene_id"])
        self.benes, self.bene_of = np.unique(bene, return_inverse=True)
        self.n_benes = len(self.benes)
        elig = np.zeros(self.n_benes, dtype=bool)
        elig[self.bene_of] = np.asarray(u["elig_error"], dtype=bool)
        self.elig = elig

    def improper_cents(self, y_claims, elig_bene):
        e = elig_bene[self.bene_of]
        y_elig = np.where(e, self.x, 0)
        y = np.where(e, self.x, y_claims)
        return {"gross": y, "eligibility": y_elig, "claims": y_claims}

    def rates(self, y):
        return {f"{self.state}|{k}": float(v.sum()) / self.X for k, v in y.items()}

    def audited(self, rep):
        s = self.con.execute("SELECT unit_id FROM sample WHERE rep = ? AND domain = ? "
                             "ORDER BY unit_id", [rep, f"{self.state}|gross"]).fetchnumpy()
        return np.searchsorted(self.unit_id, np.asarray(s["unit_id"]))

    def prepare(self, rep, audited_mask):
        self._yc = np.where(audited_mask, self.yc, 0)
        self._n, self._f, self._g, self._partial, self._recip = [], [], [], [], []
        for h in range(N_KIND):
            a = np.flatnonzero(audited_mask & (self.kind == h))
            err = self.yc[a] > 0
            part = err & (self.yc[a] < self.x[a])
            self._n.append(len(a)); self._f.append(int(err.sum())); self._g.append(int(part.sum()))
            self._partial.append(self.taint[a][part])
            self._recip.append(np.flatnonzero(~audited_mask & (self.kind == h)))
        aud_bene = np.zeros(self.n_benes, dtype=bool)
        aud_bene[self.bene_of[audited_mask]] = True
        self._n_e, self._f_e = int(aud_bene.sum()), int((aud_bene & self.elig).sum())
        self._recip_bene = np.flatnonzero(~aud_bene)
        self._elig = np.where(aud_bene, self.elig, False)

    def iterate(self, donors, rng):
        yc = self._yc.copy()
        for h in range(N_KIND):
            n, f, k = self._n[h], self._f[h], self._g[h]
            p = f / n if n else 0.0
            q = k / f if f else 0.0
            if self.parametric:   # redraw the error count first, then the partial count out of it
                f_t = int(rng.binomial(n, p)) if n else 0
                p = f_t / n if n else 0.0
                q = rng.binomial(f_t, q) / f_t if f_t else 0.0
            if p <= 0:
                continue
            hit = self._recip[h][bernoulli_positions(len(self._recip[h]), p, rng)]
            partial = (rng.random(len(hit)) < q) if len(self._partial[h]) else np.zeros(len(hit), bool)
            yc[hit[~partial]] = self.x[hit[~partial]]                       # whole payment improper
            ph = hit[partial]
            if len(ph):
                t = self._partial[h][rng.integers(0, len(self._partial[h]), len(ph))]
                yc[ph] = round_half_away(self.x[ph] * t).astype(np.int64)
        p_e = self._f_e / self._n_e if self._n_e else 0.0
        if self.parametric and self._n_e:
            p_e = rng.binomial(self._n_e, p_e) / self._n_e
        elig = self._elig.copy()
        elig[self._recip_bene[bernoulli_positions(len(self._recip_bene), p_e, rng)]] = True
        return self.rates(self.improper_cents(yc, elig))
