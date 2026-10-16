"""PERM: payment function and audit-finding simulation kernel (one state).

Payment function (same as errors/sql/perm_02 and perm_03), per payment:
  claims error      y_claims = round(x x taint, cents)
  eligibility error y_elig   = x if the beneficiary is in error, else 0
  overall           y        = x if eligibility error, else y_claims
                               (= claims + eligibility - overlap)
Rates are sum y / sum x within the state (FMAP is constant within a state,
so the federal-share rate is the same).

Audit findings transferred:
  claims      : taint of an audited payment of the same payment type and
                payment-size class (S1..S5); a recipient's y_claims is
                round(x x taint)
  eligibility : beneficiary level: a non-audited beneficiary (none of whose
                payments were sampled) takes the eligibility finding of a
                randomly drawn audited beneficiary
"""
import numpy as np

from ipsim.simulation import RowSet, bernoulli_positions, round_half_away


class Kernel:
    def __init__(self, con, v):
        self.con = con
        self.state = int(v["state_id"])
        u = con.execute("SELECT * FROM sim_units ORDER BY unit_idx").fetchnumpy()
        self.units = len(u["unit_idx"])
        self.unit_id = np.asarray(u["unit_id"])
        self.x = np.asarray(u["x_cents"], dtype=np.int64)
        self.X = float(self.x.sum())
        self.yc = np.asarray(u["y_claims_cents"], dtype=np.int64)
        self.taint = self.yc / self.x
        bene = np.asarray(u["bene_id"])
        self.benes, self.bene_of = np.unique(bene, return_inverse=True)
        self.n_benes = len(self.benes)
        elig = np.zeros(self.n_benes, dtype=bool)
        elig[self.bene_of] = np.asarray(u["elig_error"], dtype=bool)
        self.elig = elig
        self.claims = RowSet(np.arange(self.units), self.units,
                             kind=np.asarray(u["claims_kind"], dtype=np.int64), identity=(self.yc == 0))

    def improper_cents(self, y_claims, elig_bene):
        e = elig_bene[self.bene_of]
        y_elig = np.where(e, self.x, 0)
        y = np.where(e, self.x, y_claims)
        return {"overall": y, "eligibility": y_elig, "claims": y_claims}

    def rates(self, y):
        return {f"{self.state}|{k}": float(v.sum()) / self.X for k, v in y.items()}

    def audited(self, rep):
        s = self.con.execute("SELECT unit_id, stratum FROM sample WHERE rep = ? AND domain = ? "
                             "ORDER BY unit_id", [rep, f"{self.state}|overall"]).fetchnumpy()
        return np.searchsorted(self.unit_id, np.asarray(s["unit_id"])), np.asarray(s["stratum"])

    def prepare(self, audited_mask):
        self.claims.prepare(audited_mask)
        self._yc = np.where(audited_mask, self.yc, 0)
        aud_bene = np.zeros(self.n_benes, dtype=bool)
        aud_bene[self.bene_of[audited_mask]] = True
        self._aud_bene = aud_bene
        self._recip_bene = np.flatnonzero(~aud_bene)
        self._elig = np.where(aud_bene, self.elig, False)

    def iterate(self, donors, rng):
        yc = self._yc.copy()
        units, d = self.claims.assign(donors, rng)
        yc[units] = round_half_away(self.x[units] * self.taint[d]).astype(np.int64)
        elig = self._elig.copy()
        donor_benes = self.bene_of[donors]               # audited beneficiaries, as drawn
        p = self.elig[donor_benes].mean()
        elig[self._recip_bene[bernoulli_positions(len(self._recip_bene), p, rng)]] = True
        return self.rates(self.improper_cents(yc, elig))
