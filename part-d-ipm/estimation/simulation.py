"""Part D: payment function and audit-finding bootstrap simulation kernel.

Payment function (same as errors/sql/05_benefit.sql, CY 2025 post-IRA
standard benefit), per beneficiary, PDEs in fill order:
  deductible [0, D), initial [D, I), catastrophic [I, inf) in cumulative GDC
  reinsurance = round(share * catastrophic GDC), share 0.20 brand / 0.40 generic
  LICS (LIS only) = round(enrollee share - min(enrollee share, copay)),
      enrollee share = deductible GDC + 0.25 * initial GDC
  Medicare (PDE-driven) = sum over PDEs of reinsurance + LICS
  improper payment y = Medicare(submitted PDEs) - Medicare(corrected PDEs)
Amounts follow the SQL arithmetic exactly (cents; DOUBLE shares; round
half away from zero); shared/tests/test_simulation.py checks that applying
each PDE's own finding reproduces errors/ y to the cent.

Design (claim level, as in production). Each audit year has two samples,
drawn once in SQL (40_simulation_inputs.sql) and held fixed for all of
that year's iterations:
  audit sample       : sim_audit_size PDEs sampled from all PDEs,
                       independent of beneficiary (sim_audit_sample).
                       Finding = corrected GDC / submitted GDC
                       (0 = missing documentation; 1 = no error).
  beneficiary sample : sim_bene_size beneficiaries drawn with replacement
                       (sim_bene_sample; 108,000 = the population size,
                       standing in for production's random 1 million).
Each iteration:
  1. every PDE of a beneficiary-sample beneficiary takes the finding of a
     random audit-sample PDE of the same kind (brand vs generic); audited
     PDEs keep their own finding; corrected GDC = round(submitted x ratio)
  2. rerun the benefit for each beneficiary in the beneficiary sample; the
     iteration's rate is sum |y| / sum x over the beneficiary sample
"""
import numpy as np
from numba import njit

from ipsim.simulation import RowSet, round_half_away, round_half_away_scalar


def benefit_params(v):
    D = round(float(v["deductible"]) * 100)
    I = round((float(v["deductible"]) + (float(v["oop_threshold"]) - float(v["deductible"]))
               / float(v["init_enrollee_coins"])) * 100)
    return (D, I, float(v["init_enrollee_coins"]), float(v["cat_reins_brand"]), float(v["cat_reins_generic"]),
            float(v["lis_copay_brand"]), float(v["lis_copay_generic"]))


@njit
def medicare_cents(g, row_unit, lis, brand, n_units, D, I, coins, reins_brand, reins_generic,
                   copay_brand, copay_generic):
    """Medicare PDE-driven payment per beneficiary (cents).
    g = GDC cents per PDE; rows sorted by beneficiary, then fill order."""
    out = np.zeros(n_units)
    pre = 0
    last = -1
    for i in range(len(g)):
        u = row_unit[i]
        if u != last:                     # new beneficiary: benefit year starts at 0
            pre = 0
            last = u
        post = pre + g[i]
        ded = max(0, min(post, D) - min(pre, D))          # deductible phase GDC
        ini = max(0, min(post, I) - max(pre, D))          # initial coverage GDC
        cat = max(0, post - max(pre, I))                  # catastrophic GDC
        share = reins_brand if brand[i] else reins_generic
        reins = round_half_away_scalar(share * (cat / 100.0) * 100.0)
        lics = 0.0
        if lis[i]:
            std = ded / 100.0 + coins * (ini / 100.0)     # standard enrollee share
            copay = copay_brand if brand[i] else copay_generic
            lics = round_half_away_scalar((std - min(std, copay)) * 100.0)
        out[u] += reins + lics
        pre = post
    return out


@njit
def drawn_medicare(drawn, start, count, sub, cor, audited, brand, lis, u, p_err, err_off, err_ratio,
                   D, I, coins, reins_brand, reins_generic, copay_brand, copay_generic):
    """Corrected Medicare payment for each drawn beneficiary (cents).
    u: one uniform per PDE of the drawn beneficiaries, in order. A PDE of
    kind k gets an error when u < p_err[k]; its donor is then
    err_ratio[err_off[k] + floor(u / p_err[k] * n_err[k])] (u / p_err[k] is
    uniform on (0, 1) given the error, so no second draw is needed)."""
    out = np.zeros(len(drawn))
    pos = 0
    for j in range(len(drawn)):
        b = drawn[j]
        pre = 0
        m = 0.0
        for r in range(start[b], start[b] + count[b]):
            k = 1 if brand[r] else 0
            if audited[r]:
                g = cor[r]                                     # own finding
            elif u[pos] < p_err[k]:
                n_err = err_off[k + 1] - err_off[k]
                idx = err_off[k] + min(int(u[pos] / p_err[k] * n_err), n_err - 1)
                g = np.int64(round_half_away_scalar(sub[r] * err_ratio[idx]))
            else:
                g = sub[r]                                     # no error
            pos += 1
            post = pre + g
            ded = max(0, min(post, D) - min(pre, D))
            ini = max(0, min(post, I) - max(pre, D))
            cat = max(0, post - max(pre, I))
            share = reins_brand if brand[r] else reins_generic
            reins = round_half_away_scalar(share * (cat / 100.0) * 100.0)
            lics = 0.0
            if lis[r]:
                std = ded / 100.0 + coins * (ini / 100.0)
                copay = copay_brand if brand[r] else copay_generic
                lics = round_half_away_scalar((std - min(std, copay)) * 100.0)
            m += reins + lics
            pre = post
        out[j] = m
    return out


class Kernel:
    """Audit units are PDE claims; projection units are beneficiaries."""

    def __init__(self, con, v):
        self.con = con
        u = con.execute("SELECT unit_idx, x_cents FROM sim_units ORDER BY unit_idx").fetchnumpy()
        r = con.execute("SELECT unit_idx, brand, lis, sub_cents, cor_cents FROM sim_rows "
                        "ORDER BY row_idx").fetchnumpy()
        self.n_benes = len(u["unit_idx"])
        self.x = np.asarray(u["x_cents"], dtype=np.int64)
        self.row_unit = np.asarray(r["unit_idx"], dtype=np.int64)
        self.brand = np.asarray(r["brand"], dtype=np.bool_)
        self.lis = np.asarray(r["lis"], dtype=np.bool_)
        self.sub = np.asarray(r["sub_cents"], dtype=np.int64)
        self.cor = np.asarray(r["cor_cents"], dtype=np.int64)
        self.ratio = self.cor / self.sub
        self.p = benefit_params(v)
        self.units = len(self.sub)                      # audit units = claims
        counts = np.bincount(self.row_unit, minlength=self.n_benes)
        self.start = np.concatenate([[0], np.cumsum(counts)[:-1]]).astype(np.int64)
        self.count = counts.astype(np.int64)
        self.m_sub = medicare_cents(self.sub, self.row_unit, self.lis, self.brand, self.n_benes, *self.p)

    def improper_cents(self, g_corrected):
        """y per beneficiary for a corrected GDC vector (all beneficiaries)."""
        return self.m_sub - medicare_cents(g_corrected, self.row_unit, self.lis, self.brand, self.n_benes, *self.p)

    def audited(self, rep):
        """The audit year's audit sample: row indices of the audited PDEs."""
        s = self.con.execute("SELECT row_idx FROM sim_audit_sample WHERE rep = ? ORDER BY row_idx",
                             [rep]).fetchnumpy()
        return np.asarray(s["row_idx"], dtype=np.int64)

    def prepare(self, rep, audited_mask):
        """Fix the audit year's samples: audited PDEs and beneficiary sample."""
        self._audited = audited_mask
        b = self.con.execute("SELECT unit_idx FROM sim_bene_sample WHERE rep = ? ORDER BY unit_idx",
                             [rep]).fetchnumpy()
        self._benes = np.asarray(b["unit_idx"], dtype=np.int64)  # sorted; a repeat = drawn twice
        self._n_rows = int(self.count[self._benes].sum())        # PDEs of the beneficiary sample
        self._m_sub = self.m_sub[self._benes]
        self._x = float(self.x[self._benes].sum())

    def iterate(self, donors, rng):
        kind = self.brand[donors].astype(np.int64)
        err = self.cor[donors] != self.sub[donors]
        p_err = np.array([err[kind == k].mean() if (kind == k).any() else 0.0 for k in (0, 1)])
        order = np.argsort(kind[err], kind="stable")
        err_ratio = self.ratio[donors[err]][order]
        err_off = np.searchsorted(kind[err][order], np.arange(3)).astype(np.int64)
        u = rng.random(self._n_rows)
        m_cor = drawn_medicare(self._benes, self.start, self.count, self.sub, self.cor, self._audited,
                               self.brand, self.lis, u, p_err, err_off, err_ratio, *self.p)
        y = self._m_sub - m_cor
        return {"national": float(np.abs(y).sum()) / self._x}
