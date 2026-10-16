"""CERT: payment function and audit-finding simulation kernel.

Payment function: a claim's improper amount is round(x x taint, cents),
taint = improper share of the payment found on review.
Audit finding transferred (claim level): the taint of a randomly drawn
audited claim (one donor kind).
"""
import numpy as np

from ipsim.simulation import RowSet, round_half_away


class Kernel:
    def __init__(self, con, v):
        self.con = con
        u = con.execute("SELECT * FROM sim_units ORDER BY unit_idx").fetchnumpy()
        self.units = len(u["unit_idx"])
        self.unit_id = np.asarray(u["unit_id"])
        self.x = np.asarray(u["x_cents"], dtype=np.int64)
        self.X = float(self.x.sum())
        self.y = np.asarray(u["y_cents"], dtype=np.int64)
        self.taint = self.y / self.x
        self.claims = RowSet(np.arange(self.units), self.units, kind=np.zeros(self.units, dtype=np.int64),
                             identity=(self.y == 0))

    def audited(self, rep):
        s = self.con.execute("SELECT unit_id FROM sample WHERE rep = ? AND domain = 'national' "
                             "ORDER BY unit_id", [rep]).fetchnumpy()
        return np.searchsorted(self.unit_id, np.asarray(s["unit_id"]))

    def prepare(self, rep, audited_mask):
        self.claims.prepare(audited_mask)
        self._y = np.where(audited_mask, self.y, 0)

    def iterate(self, donors, rng):
        y = self._y.copy()
        units, d = self.claims.assign(donors, rng)
        y[units] = round_half_away(self.x[units] * self.taint[d]).astype(np.int64)
        return {"national": float(y.sum()) / self.X}
