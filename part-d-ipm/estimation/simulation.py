"""Part D: payment function, expansion and bootstrap simulation.

Payment function (same as errors/sql/05_benefit.sql, CY 2025 post-IRA
standard benefit), per beneficiary, PDEs in fill order:
  deductible [0, D), initial [D, I), catastrophic [I, inf) in cumulative GDC
  reinsurance = round(share * catastrophic GDC), share 0.20 brand / 0.40 generic
  LICS (LIS only) = round(enrollee share - min(enrollee share, copay)),
      enrollee share = deductible GDC + 0.25 * initial GDC
  Medicare (PDE-driven) = sum over PDEs of reinsurance + LICS
  payment error y = Medicare(submitted PDEs) - Medicare(corrected PDEs),
  netted within the beneficiary
Cents and SQL rounding are reproduced exactly (shared/tests/test_simulation.py).

Alternative design (benefit_design: pre_ira_2023, errors/pre_ira.yaml): the
CY 2023 benefit of errors/sql/05_benefit_pre_ira.sql (deductible, initial
coverage, coverage gap with the 70% manufacturer discount, 80% catastrophic
reinsurance), in medicare_cents_pre_ira. The population's config selects it.
Every method sums y over beneficiaries: over = sum of positive y, under =
sum of -y where negative, gross = over + under, net = over - under, each
divided by total payments X (direct subsidy + reinsurance + LICS).

PDE audit (40_simulation_inputs.sql): 5,000 PDEs per audit year, stratified
SRS over claim strata (LTC; non-LTC lowest cost decile; other non-LTC),
Neyman allocation. Finding = corrected GDC / submitted GDC.

Expansion (run_expansion): r_h = audited error dollars / audited submitted
  GDC in stratum h. Every PDE in the population gets corrected GDC =
  round(GDC x (1 - r_h)); the benefit is rerun for every beneficiary.
  Interval (delta method): Var(r_h) is the stratified ratio variance
  (1 - n_h/N_h) s_h^2(d - r_h g) / (n_h gbar_h^2); each stratum's
  contribution is [T(r_h + SE_h) - T(r_h - SE_h)] / 2 (one rerun each way,
  other strata at their r); Var(T) = sum of squared contributions;
  T +- 1.96 sqrt(Var(T)), divided by X.

Bootstrap simulation (Kernel): every non-audited PDE in the full
  population takes a finding from the audited PDEs of its own stratum;
  audited PDEs keep their own. Drawing a random audited donor is done in
  two equivalent steps per stratum: an error with probability p = f/n
  (f of n audited PDEs in error), and, given an error, a partial one
  (correct GDC > 0) with probability q = g/f, its corrected/submitted
  ratio drawn from the audited partial errors; full errors set GDC to 0.
  sim_rates: fixed       p and q as audited
             parametric  p and q redrawn before each iteration as
                         Binomial(n, p)/n and Binomial(f, q)/f
  The benefit is rerun for all beneficiaries; 1,000 iterations; mean and
  2.5th-97.5th percentiles.
"""
import numpy as np
from numba import njit

from ipsim.simulation import bernoulli_positions, round_half_away, round_half_away_scalar

DOMAINS = ("over", "under", "gross", "net")
N_STRATA = 3


def benefit_params(v):
    """(payment function, its parameters) for the population's benefit design."""
    if str(v.get("benefit_design", "post_ira_2025")) == "pre_ira_2023":
        D = round(float(v["deductible"]) * 100)
        ICL = round(float(v["initial_coverage_limit"]) * 100)
        L = round((float(v["oop_threshold"]) - float(v["deductible"])
                   - float(v["init_enrollee_coins"]) * (float(v["initial_coverage_limit"]) - float(v["deductible"])))
                  * 10000)                                            # cent-percent, as in the SQL
        return medicare_cents_pre_ira, (D, ICL, L, float(v["init_enrollee_coins"]), float(v["gap_enrollee_coins"]),
                                        float(v["gap_mfr_brand"]), float(v["cat_enrollee_coins"]),
                                        float(v["cat_reins"]), float(v["lis_copay_brand"]),
                                        float(v["lis_copay_generic"]))
    D = round(float(v["deductible"]) * 100)
    I = round((float(v["deductible"]) + (float(v["oop_threshold"]) - float(v["deductible"]))
               / float(v["init_enrollee_coins"])) * 100)
    return medicare_cents, (D, I, float(v["init_enrollee_coins"]), float(v["cat_reins_brand"]),
                            float(v["cat_reins_generic"]), float(v["lis_copay_brand"]), float(v["lis_copay_generic"]))


@njit
def medicare_cents_pre_ira(g, row_unit, lis, brand, n_units, D, ICL, L, coins, gap_coins, gap_mfr,
                           cat_coins, cat_reins, copay_brand, copay_generic):
    """Medicare PDE-driven payment per beneficiary (cents), CY 2023 benefit
    (errors/sql/05_benefit_pre_ira.sql). g = GDC cents per PDE; rows sorted
    by beneficiary, then fill order."""
    out = np.zeros(n_units)
    pre = 0
    w = 0
    last = -1
    for i in range(len(g)):
        u = row_unit[i]
        if u != last:                     # new beneficiary: benefit year starts at 0
            pre = 0
            w = 0
            last = u
        post = pre + g[i]
        ded = max(0, min(post, D) - min(pre, D))
        ini = max(0, min(post, ICL) - max(pre, D))
        above = max(0, post - max(pre, ICL))
        r = 100 if lis[i] else (95 if brand[i] else 25)              # TrOOP accrual in the gap (percent)
        w_post = w + r * above
        gap = round_half_away_scalar((min(w_post, L) - min(w, L)) / r)
        cat = above - gap
        reins = round_half_away_scalar(cat_reins * cat)
        lics = 0.0
        if lis[i]:
            std = ded / 100.0 + coins * (ini / 100.0) + 1.0 * (gap / 100.0)
            copay = copay_brand if brand[i] else copay_generic
            lics = round_half_away_scalar((std - min(std, copay)) * 100.0) + round_half_away_scalar(cat_coins * cat)
        out[u] += reins + lics
        pre = post
        w = w_post
    return out


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


def load_rows(con):
    u = con.execute("SELECT unit_idx, x_cents, y_cents FROM sim_units ORDER BY unit_idx").fetchnumpy()
    r = con.execute("SELECT unit_idx, brand, lis, stratum_code, sub_cents, cor_cents FROM sim_rows "
                    "ORDER BY row_idx").fetchnumpy()
    return u, r


def measures(y, X):
    """Domain rates from beneficiary-level payment errors (cents)."""
    over, under = float(y[y > 0].sum()), float(-y[y < 0].sum())
    return {"national|over": over / X, "national|under": under / X,
            "national|gross": (over + under) / X, "national|net": (over - under) / X}


class Kernel:
    """Audit units are PDEs; payment errors are netted per beneficiary."""

    def __init__(self, con, v):
        self.con = con
        self.parametric = str(v.get("sim_rates", "fixed")) == "parametric"
        u, r = load_rows(con)
        self.n_benes = len(u["unit_idx"])
        self.X = float(np.asarray(u["x_cents"]).sum())
        self.y_true = np.asarray(u["y_cents"], dtype=np.int64)
        self.row_unit = np.asarray(r["unit_idx"], dtype=np.int64)
        self.brand = np.asarray(r["brand"], dtype=np.bool_)
        self.lis = np.asarray(r["lis"], dtype=np.bool_)
        self.stratum = np.asarray(r["stratum_code"], dtype=np.int64)
        self.sub = np.asarray(r["sub_cents"], dtype=np.int64)
        self.cor = np.asarray(r["cor_cents"], dtype=np.int64)
        self.payment, self.p = benefit_params(v)        # post-IRA (default) or pre-IRA payment function
        self.units = len(self.sub)                      # audit units = PDEs
        self.m_sub = self.payment(self.sub, self.row_unit, self.lis, self.brand, self.n_benes, *self.p)

    def improper_cents(self, g_corrected):
        """y per beneficiary for a corrected GDC vector (all PDEs)."""
        return self.m_sub - self.payment(g_corrected, self.row_unit, self.lis, self.brand, self.n_benes, *self.p)

    def audited(self, rep):
        s = self.con.execute("SELECT row_idx FROM sim_audit_sample WHERE rep = ? ORDER BY row_idx",
                             [rep]).fetchnumpy()
        return np.asarray(s["row_idx"], dtype=np.int64)

    def prepare(self, rep, audited_mask):
        """The audit year's counts and partial-error lists, per stratum."""
        self._audited = audited_mask
        self._n, self._f, self._g, self._partial, self._recip = [], [], [], [], []
        for h in range(N_STRATA):
            a = np.flatnonzero(audited_mask & (self.stratum == h))
            err = self.cor[a] != self.sub[a]
            part = err & (self.cor[a] != 0)
            self._n.append(len(a)); self._f.append(int(err.sum())); self._g.append(int(part.sum()))
            self._partial.append(self.cor[a][part] / self.sub[a][part])
            self._recip.append(np.flatnonzero(~audited_mask & (self.stratum == h)))

    def iterate(self, donors, rng):
        g = np.where(self._audited, self.cor, self.sub)          # audited keep their own findings
        for h in range(N_STRATA):
            n, f, k = self._n[h], self._f[h], self._g[h]
            p = f / n if n else 0.0
            q = k / f if f else 0.0
            if self.parametric:                                  # redraw the audit's rates
                p = rng.binomial(n, p) / n if n else 0.0
                q = rng.binomial(f, q) / f if f else 0.0
            if p <= 0:
                continue
            hit = self._recip[h][bernoulli_positions(len(self._recip[h]), p, rng)]
            partial = (rng.random(len(hit)) < q) if len(self._partial[h]) else np.zeros(len(hit), bool)
            g[hit[~partial]] = 0                                 # full error: GDC 0
            ph = hit[partial]
            if len(ph):
                ratio = self._partial[h][rng.integers(0, len(self._partial[h]), len(ph))]
                g[ph] = round_half_away(self.sub[ph] * ratio).astype(np.int64)
        return measures(self.improper_cents(g), self.X)


def run_expansion(con, v):
    """Expansion with a delta-method interval; writes table est_expansion."""
    import pyarrow as pa
    from ipsim.simulation import population_variables
    v = population_variables(v)
    k = Kernel(con, v)
    z = 1.959963984540054
    N = np.bincount(k.stratum, minlength=N_STRATA).astype(float)
    reps = sorted(r for (r,) in con.execute("SELECT DISTINCT rep FROM sim_audit_sample ORDER BY rep").fetchall())

    def totals(rate):
        g = round_half_away(k.sub * (1.0 - rate[k.stratum])).astype(np.int64)
        return measures(k.improper_cents(g), k.X)

    rows = []
    for rep in reps:
        a = k.audited(rep)
        r, se = np.zeros(N_STRATA), np.zeros(N_STRATA)
        for h in range(N_STRATA):
            ah = a[k.stratum[a] == h]
            d = (k.sub[ah] - k.cor[ah]).astype(float)            # error dollars (cents)
            s = k.sub[ah].astype(float)
            n = len(ah)
            r[h] = d.sum() / s.sum()
            if n > 1:
                e = d - r[h] * s
                se[h] = np.sqrt((1 - n / N[h]) * e.var(ddof=1) / (n * s.mean() ** 2))
        base = totals(r)
        var = dict.fromkeys(base, 0.0)
        for h in range(N_STRATA):
            if se[h] == 0:
                continue
            up, dn = r.copy(), r.copy()
            up[h] += se[h]; dn[h] -= se[h]
            tu, td = totals(up), totals(dn)
            for d_ in base:
                var[d_] += ((tu[d_] - td[d_]) / 2.0) ** 2
        for d_, est in base.items():
            sd = float(np.sqrt(var[d_]))
            rows.append(("expansion", "normal", rep, d_, est, sd, est - z * sd, est + z * sd))
    cols = list(zip(*rows))
    tbl = pa.table({"method": pa.array(cols[0], pa.string()), "interval": pa.array(cols[1], pa.string()),
                    "rep": pa.array(cols[2], pa.int32()), "domain": pa.array(cols[3], pa.string()),
                    "estimate": pa.array(cols[4], pa.float64()), "se": pa.array(cols[5], pa.float64()),
                    "lower": pa.array(cols[6], pa.float64()), "upper": pa.array(cols[7], pa.float64())})
    con.register("est_expansion_arrow", tbl)
    con.execute("CREATE OR REPLACE TABLE est_expansion AS SELECT * FROM est_expansion_arrow")
    con.unregister("est_expansion_arrow")
