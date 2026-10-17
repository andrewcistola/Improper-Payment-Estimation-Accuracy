"""Part C: payment function and bootstrap simulation kernel.

Payment function (same as errors/sql/04_apply_errors.sql), per enrollee:
  HCC error  = sum over HCCs of  coef (deleted) | severe - mild (moved) | 0
  Delta-R    = (R0 - demographic score if missing documentation else HCC error)
               - mild coef of an additional HCC (if its family is not coded)
  y          = round(Delta-R x county rate x months, cents)
improper_cents() reproduces errors/ exactly (shared/tests/test_simulation.py).

Bootstrap simulation: rates from the audit year's audit, applied to the
whole population, 1,000 iterations.
  HCC failure rate, one per HCC (20 = 10 families x mild/severe):
      f_k = audited instances of HCC k that failed / audited instances of k,
      failed = deleted, moved down the hierarchy, or on a record with
      missing documentation (which loses every coded HCC). A failed
      instance loses L_k, the average risk score its HCC's audited
      failures lost (full coefficient for deleted or missing
      documentation, severe - mild for a move). An HCC with no audited
      instances gets f_k = 0: no extrapolation.
  HCC addition rate, one per family (10):
      a_f = audited enrollees with family f added / audited enrollees
      without family f coded. An addition subtracts the family's mild
      coefficient (an underpayment).
  Each iteration: every HCC instance of a non-audited enrollee fails with
  probability f_k, and every non-audited enrollee without family f coded
  gains it with probability a_f (independent draws). Audited enrollees
  keep their own findings. Each enrollee's error is
      y_i = round(Delta-R_i x county rate_i x months_i)   (cents)
  over = sum of positive y_i, under = sum of -y_i where negative,
  gross = over + under, net = over - under; each divided by total payments.

sim_rates (config):
  fixed       the audit's rates are used as observed in every iteration
  parametric  parametric bootstrap of the rates: before each iteration,
              every rate is redrawn as Binomial(n, rate) / n, n = the
              audited instances (or eligible enrollees) behind it. An HCC
              with no audited failures always redraws 0; average losses
              stay fixed.
"""
import numpy as np

from ipsim.simulation import bernoulli_positions, round_half_away

N_HCC, N_FAM = 20, 10
DOMAINS = ("over", "under", "gross", "net")


class Kernel:
    def __init__(self, con, v):
        self.con = con
        self.parametric = str(v.get("sim_rates", "fixed")) == "parametric"
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
        self.y_cents = np.asarray(u["y_cents"], dtype=np.int64)
        self.md = np.asarray(u["missing_doc"], dtype=bool)
        self.add_fam = np.asarray(u["add_fam_code"], dtype=np.int64)
        self.mild = np.asarray(fam["mild_milli"], dtype=np.int64)
        self.row_unit = np.asarray(r["unit_idx"], dtype=np.int64)
        self.row_fam = np.asarray(r["fam_code"], dtype=np.int64)
        self.hcc = np.asarray(r["hcc_code"], dtype=np.int64)
        self.paid = np.asarray(r["paid_milli"], dtype=np.int64)
        self.move = np.asarray(r["move_milli"], dtype=np.int64)
        self.outcome = np.asarray(r["outcome"], dtype=np.int64)
        # families coded per enrollee, as a bit mask (10 families)
        self.fam_mask = np.zeros(self.units, dtype=np.int64)
        np.bitwise_or.at(self.fam_mask, self.row_unit, np.left_shift(1, self.row_fam))
        # what each HCC instance actually lost on review (thousandths)
        md_row = self.md[self.row_unit]
        self.failed_row = (self.outcome != 0) | md_row
        self.loss_row = np.where(md_row | (self.outcome == 1), self.paid,
                                 np.where(self.outcome == 2, self.move, 0))

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
        s = self.con.execute("SELECT unit_id FROM sample WHERE rep = ? AND domain = 'national|gross' "
                             "ORDER BY unit_id", [rep]).fetchnumpy()
        return np.searchsorted(self.unit_id, np.asarray(s["unit_id"]))

    def prepare(self, rep, audited_mask):
        """The audit year's rates, and which units and HCCs receive draws."""
        aud_row = audited_mask[self.row_unit]
        n_k = np.bincount(self.hcc[aud_row], minlength=N_HCC)
        fail = aud_row & self.failed_row
        nf_k = np.bincount(self.hcc[fail], minlength=N_HCC)
        loss_k = np.bincount(self.hcc[fail], weights=self.loss_row[fail], minlength=N_HCC)
        self.f_rate = np.where(n_k > 0, nf_k / np.maximum(n_k, 1), 0.0)     # 0 if not audited
        self.f_loss = np.where(nf_k > 0, loss_k / np.maximum(nf_k, 1), 0.0)
        self._n_k = n_k
        recip = np.flatnonzero(~aud_row)
        recip = recip[np.argsort(self.hcc[recip], kind="stable")]
        bounds = np.searchsorted(self.hcc[recip], np.arange(N_HCC + 1))
        self._recip_hcc = [recip[bounds[k]:bounds[k + 1]] for k in range(N_HCC)]
        self.a_rate = np.zeros(N_FAM)
        self._elig = np.zeros(N_FAM, dtype=np.int64)
        self._recip_add = []
        for f in range(N_FAM):
            lacks = ((self.fam_mask >> f) & 1) == 0
            eligible = int((audited_mask & lacks).sum())
            added = int((audited_mask & (self.add_fam == f)).sum())
            self.a_rate[f] = added / eligible if eligible else 0.0
            self._elig[f] = eligible
            self._recip_add.append(np.flatnonzero(~audited_mask & lacks))
        self._audited = audited_mask

    def iterate(self, donors, rng):
        """One iteration (donors = the audit; its rates were set in prepare)."""
        f_rate, a_rate = self.f_rate, self.a_rate
        if self.parametric:                       # redraw the audit's rates
            f_rate = rng.binomial(self._n_k, f_rate) / np.maximum(self._n_k, 1)
            a_rate = rng.binomial(self._elig, a_rate) / np.maximum(self._elig, 1)
        rows, losses = [], []
        for k in range(N_HCC):
            if f_rate[k] > 0:
                hit = self._recip_hcc[k][bernoulli_positions(len(self._recip_hcc[k]), f_rate[k], rng)]
                rows.append(hit)
                losses.append(np.full(len(hit), self.f_loss[k]))
        rows = np.concatenate(rows) if rows else np.empty(0, dtype=np.int64)
        losses = np.concatenate(losses) if losses else np.empty(0)
        dr = np.bincount(self.row_unit[rows], weights=losses, minlength=self.units)   # thousandths
        for f in range(N_FAM):
            if a_rate[f] > 0:
                gain = self._recip_add[f][bernoulli_positions(len(self._recip_add[f]), a_rate[f], rng)]
                dr[gain] -= self.mild[f]
        y = round_half_away(dr * (self.rate * self.months) / 1000.0)                 # cents
        y = np.where(self._audited, self.y_cents, y)
        over, under = float(y[y > 0].sum()), float(-y[y < 0].sum())
        return {"national|over": over / self.X, "national|under": under / self.X,
                "national|gross": (over + under) / self.X, "national|net": (over - under) / self.X}
