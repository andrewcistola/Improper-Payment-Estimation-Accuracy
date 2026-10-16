"""Part C: payment function and audit-finding simulation kernel.

Payment function (same as errors/sql/04_apply_errors.sql), per enrollee:
  HCC error  = sum over HCCs of  coef (deleted) | severe - mild (moved) | 0
  Delta-R    = (R0 - demographic score if missing documentation else HCC error)
               - mild coef of an additional HCC (if its family is not coded)
  y          = round(Delta-R x county rate x months, cents)
Integer thousandths and cents reproduce errors/ exactly; checked in
shared/tests/test_simulation.py.

Audit findings transferred:
  HCC level      : supported / deleted / hierarchy move, from audited HCCs
                   of the same risk stratum, family and severity (fallback:
                   same family and severity in any stratum)
  enrollee level : (missing documentation, additional HCC family) from an
                   audited enrollee of the same risk stratum that also has
                   (or also lacks) coded HCCs
"""
import numpy as np

from ipsim.simulation import RowSet


class Kernel:
    def __init__(self, con, v):
        self.con = con
        u = con.execute("SELECT * FROM sim_units ORDER BY unit_idx").fetchnumpy()
        r = con.execute("SELECT * FROM sim_rows ORDER BY unit_idx, fam_code").fetchnumpy()
        fam = con.execute("SELECT fam_code, mild_milli FROM sim_families ORDER BY fam_code").fetchnumpy()
        self.units = len(u["unit_idx"])
        self.unit_id = np.asarray(u["unit_id"])
        self.demo = np.asarray(u["demo_milli"], dtype=np.int64)
        self.r0 = np.asarray(u["r0_milli"], dtype=np.int64)
        self.rate = np.asarray(u["rate_cents"], dtype=np.int64)
        self.months = np.asarray(u["months"], dtype=np.int64)
        self.X = float(np.asarray(u["x_cents"]).sum())
        self.md = np.asarray(u["missing_doc"], dtype=bool)
        self.add_fam = np.asarray(u["add_fam_code"], dtype=np.int64)
        self.mild = np.asarray(fam["mild_milli"], dtype=np.int64)
        has_hcc = np.asarray(u["has_hcc"], dtype=bool)
        stratum = np.asarray(u["stratum_code"], dtype=np.int64)
        self.row_unit = np.asarray(r["unit_idx"], dtype=np.int64)
        self.row_fam = np.asarray(r["fam_code"], dtype=np.int64)
        self.paid = np.asarray(r["paid_milli"], dtype=np.int64)
        self.move = np.asarray(r["move_milli"], dtype=np.int64)
        self.outcome = np.asarray(r["outcome"], dtype=np.int64)
        # families coded per enrollee, as a bit mask (10 families)
        self.fam_mask = np.zeros(self.units, dtype=np.int64)
        np.bitwise_or.at(self.fam_mask, self.row_unit, np.left_shift(1, self.row_fam))
        kind = np.asarray(r["kind"], dtype=np.int64)
        fb = np.asarray(r["fallback"], dtype=np.int64)
        fallback_of_kind = np.zeros(kind.max() + 1, dtype=np.int64)
        fallback_of_kind[kind] = fb
        self.hccs = RowSet(self.row_unit, self.units, kind=kind, identity=(self.outcome == 0),
                           fallback_of_kind=fallback_of_kind)
        self.enrollees = RowSet(np.arange(self.units), self.units, kind=stratum * 2 + has_hcc,
                                identity=(~self.md) & (self.add_fam < 0))

    def improper_cents(self, outcome, md, add_fam):
        """y per enrollee given HCC outcomes and enrollee-level findings."""
        err = np.where(outcome == 1, self.paid, np.where(outcome == 2, self.move, 0))
        hcc_err = np.bincount(self.row_unit, weights=err, minlength=self.units).astype(np.int64)
        has_fam = (self.fam_mask >> np.maximum(add_fam, 0)) & 1
        add = np.where((add_fam >= 0) & (has_fam == 0), self.mild[np.maximum(add_fam, 0)], 0)
        delta = np.where(md, self.r0 - self.demo, hcc_err) - add            # thousandths
        v = delta * self.rate * self.months                                 # 1e-5 dollars
        return np.sign(v) * ((np.abs(v) + 500) // 1000)                     # cents, half away

    def audited(self, rep):
        s = self.con.execute("SELECT unit_id, stratum FROM sample WHERE rep = ? AND domain = 'national' "
                             "ORDER BY unit_id", [rep]).fetchnumpy()
        return np.searchsorted(self.unit_id, np.asarray(s["unit_id"])), np.asarray(s["stratum"])

    def prepare(self, audited_mask):
        self.hccs.prepare(audited_mask)
        self.enrollees.prepare(audited_mask)
        own_h = audited_mask[self.row_unit]
        self._outcome = np.where(own_h, self.outcome, 0)     # audited keep their findings
        self._md = np.where(audited_mask, self.md, False)
        self._add = np.where(audited_mask, self.add_fam, -1)

    def iterate(self, donors, rng):
        outcome, md, add = self._outcome.copy(), self._md.copy(), self._add.copy()
        rows, d = self.hccs.assign(donors, rng)
        outcome[rows] = self.outcome[d]
        units, d = self.enrollees.assign(donors, rng)
        md[units] = self.md[d]
        add[units] = self.add_fam[d]
        y = self.improper_cents(outcome, md, add)
        return {"national": float(np.abs(y).sum()) / self.X}
