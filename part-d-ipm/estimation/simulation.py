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
Neyman allocation. Finding = corrected GDC / submitted GDC. The strata and
the size are illustrative (the production design is not public).

Expansion, plug-in benefit rerun (run_expansion, method 'expansion'):
  r_h = audited error dollars / audited submitted GDC in stratum h. Every
  PDE in the population gets corrected GDC = round(GDC x (1 - r_h)), a
  UNIFORM haircut, and the benefit is rerun for every beneficiary. The
  haircut spreads the stratum's error dollars over every PDE instead of
  concentrating them in a few, so it misses the nonlinear benefit's
  response to whole-PDE errors (its point estimate runs low).
  Interval (delta method): Var(r_h) is the stratified ratio variance
  (1 - n_h/N_h) s_h^2(d - r_h g) / (n_h gbar_h^2); each stratum's
  contribution is [T(r_h + SE_h) - T(r_h - SE_h)] / 2 (one rerun each way,
  other strata at their r); Var(T) = sum of squared contributions;
  T +- 1.96 sqrt(Var(T)), divided by X. This SE describes the propagated
  uncertainty of r_h only and understates the method's own sampling SD.

Design-based PDE-level estimators (run_pde_estimators, methods
'pde_expansion' and 'pde_ratio'): the fair same-audit analytic comparator.
  For each audited PDE i, the marginal Medicare-payment effect
    y_i = Medicare(all PDEs as submitted)
        - Medicare(all PDEs as submitted, only PDE i corrected)
  for its beneficiary (one benefit rerun per audited PDE in error; a PDE
  whose finding is "no error" has y_i = 0 exactly). y_i is signed; over,
  under, gross and net are defined AT THE PDE LEVEL for these two methods
  (over = sum of max(y_i, 0), under = sum of max(-y_i, 0), gross = |y_i|,
  net = y_i); beneficiary netting does not apply. Totals come from
  shared/sql/lib/02_estimators.sql on the sample table pde_sample:
    pde_expansion  stratified-SRS Horvitz-Thompson (expansion) total with
                   FPC, divided by the known total payments X
    pde_ratio      ratio estimator with x_i = the PDE's submitted GDC,
                   times the population GDC total (the only PDE-level
                   payment proxy that is known for every PDE; Medicare's
                   payment is defined per beneficiary, not per PDE),
                   divided by X
  Both use the tested stratified variance formulas; normal intervals.
  With every PDE audited both reproduce the PDE-level totals exactly;
  they equal the beneficiary-netted truth when no beneficiary has more
  than one PDE in error (then the y_i of a beneficiary's PDEs sum to its
  netted payment error).

Bootstrap simulation (Kernel): every non-audited PDE in the full
  population takes a finding from the audited PDEs of its own donor kind
  (the claim stratum; with sim_kind_deciles = K > 0, the stratum x K
  quantiles of submitted GDC within the stratum, computed on the
  population -- sql/40_simulation_inputs.sql; the strata and the other
  estimators are unchanged); audited PDEs keep their own. Drawing a random
  audited donor is done in two equivalent steps per kind: an error with
  probability p = f/n
  (f of n audited PDEs in error), and, given an error, a partial one
  (correct GDC > 0) with probability q = g/f, its corrected/submitted
  ratio drawn from the audited partial errors; full errors set GDC to 0.
  sim_rates: fixed       p and q as audited
             parametric  before each iteration the audit's counts are
                         redrawn: f~ = Binomial(n, p), then
                         g~ = Binomial(f~, q); p~ = f~/n, q~ = g~/f~
                         (q~ = 0 when f~ = 0)
  A kind with NO audited PDE (possible only with sim_kind_deciles > 0)
  borrows its parent design stratum's pooled audit: p, q, the partial list
  and the parametric redraw all come from the stratum's audited PDEs
  (stratum = kind // K). A kind with audited PDEs but no failure stays
  at zero, as before.
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
    r = con.execute("SELECT unit_idx, brand, lis, stratum_code, kind, sub_cents, cor_cents FROM sim_rows "
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
        self.stratum = np.asarray(r["stratum_code"], dtype=np.int64)   # claim strata (audit design, 3)
        self.kind = np.asarray(r["kind"], dtype=np.int64)              # simulation donor kind (3, or 3 x sim_kind_deciles)
        self.n_kind = int(self.kind.max()) + 1
        self.stratum_of_kind = np.zeros(self.n_kind, dtype=np.int64)   # kind -> claim stratum (identity when K = 0)
        self.stratum_of_kind[self.kind] = self.stratum
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
        """The audit year's counts and partial-error lists, per donor kind."""
        self._audited = audited_mask
        self._n, self._f, self._g, self._partial, self._recip = [], [], [], [], []
        for h in range(self.n_kind):
            a = np.flatnonzero(audited_mask & (self.kind == h))
            if len(a) == 0:   # no audited PDE of this kind: the parent stratum's pooled audit
                a = np.flatnonzero(audited_mask & (self.stratum == self.stratum_of_kind[h]))
            err = self.cor[a] != self.sub[a]
            part = err & (self.cor[a] != 0)
            self._n.append(len(a)); self._f.append(int(err.sum())); self._g.append(int(part.sum()))
            self._partial.append(self.cor[a][part] / self.sub[a][part])
            self._recip.append(np.flatnonzero(~audited_mask & (self.kind == h)))

    def iterate(self, donors, rng):
        g = np.where(self._audited, self.cor, self.sub)          # audited keep their own findings
        for h in range(self.n_kind):
            n, f, k = self._n[h], self._f[h], self._g[h]
            p = f / n if n else 0.0
            q = k / f if f else 0.0
            if self.parametric:                                  # redraw the audit's counts
                f_new = int(rng.binomial(n, p)) if n else 0      # f~ ~ Binomial(n, f/n)
                g_new = int(rng.binomial(f_new, q)) if f_new else 0   # g~ ~ Binomial(f~, g/f)
                p = f_new / n if n else 0.0
                q = g_new / f_new if f_new else 0.0
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


def marginal_effects(k, rows):
    """Marginal Medicare-payment effect y_i (cents) of each PDE in `rows`:
    its beneficiary's Medicare payment with every PDE as submitted minus the
    same with only that PDE corrected. One benefit rerun of the
    beneficiary's PDEs per row whose finding is an error; 0 otherwise."""
    rows = np.asarray(rows, dtype=np.int64)
    y = np.zeros(len(rows), dtype=np.int64)
    counts = np.bincount(k.row_unit, minlength=k.n_benes)
    start = np.concatenate([[0], np.cumsum(counts)[:-1]])
    end = start + counts
    for j in np.flatnonzero(k.cor[rows] != k.sub[rows]):     # only PDEs whose finding is an error
        i = rows[j]
        u = k.row_unit[i]
        a, b = start[u], end[u]
        g = k.sub[a:b].copy()
        g[i - a] = k.cor[i]
        unit0 = np.zeros(b - a, dtype=np.int64)
        m_cor = k.payment(g, unit0, k.lis[a:b], k.brand[a:b], 1, *k.p)[0]
        y[j] = int(round(k.m_sub[u] - m_cor))
    return y


def run_pde_estimators(con, v):
    """Design-based PDE-level estimators on the PDE audit: 'pde_expansion'
    (stratified-SRS Horvitz-Thompson total of the marginal effects y_i,
    FPC) and 'pde_ratio' (ratio to submitted GDC, times the population GDC
    total), both divided by the known total payments X. Variance formulas
    are shared/sql/lib/02_estimators.sql (ipm_expansion / ipm_ratio), run
    on the sample table pde_sample. Over, under, gross and net are PDE-level
    (y_i signed, not netted per beneficiary). Writes tables pde_sample and
    est_pde."""
    import pyarrow as pa
    from ipsim.simulation import population_variables
    v = population_variables(v)
    k = Kernel(con, v)
    N = np.bincount(k.stratum, minlength=N_STRATA)
    names = np.array(["a_ltc", "b_low_cost", "c_other"])
    reps = sorted(r for (r,) in con.execute("SELECT DISTINCT rep FROM sim_audit_sample ORDER BY rep").fetchall())
    parts = {c: [] for c in ("rep", "domain", "stratum", "pop_h", "samp_h", "unit_id", "y", "x", "w")}
    for rep in reps:
        a = k.audited(rep)
        y = marginal_effects(k, a) / 100.0                      # dollars
        x = k.sub[a] / 100.0
        h = k.stratum[a]
        n_h = np.bincount(h, minlength=N_STRATA)
        m = len(a)
        for d in DOMAINS:
            yd = {"over": np.maximum(y, 0), "under": np.maximum(-y, 0), "gross": np.abs(y), "net": y}[d]
            parts["rep"].append(np.full(m, rep, dtype=np.int32))
            parts["domain"].append(np.full(m, f"national|{d}", dtype=object))
            parts["stratum"].append(names[h])
            parts["pop_h"].append(N[h].astype(np.int64)); parts["samp_h"].append(n_h[h].astype(np.int64))
            parts["unit_id"].append(a); parts["y"].append(yd); parts["x"].append(x)
            parts["w"].append(N[h] / n_h[h])
    cat = {c: np.concatenate(v) for c, v in parts.items()}
    tbl = pa.table({"rep": pa.array(cat["rep"], pa.int32()), "domain": pa.array(cat["domain"], pa.string()),
                    "stratum": pa.array(cat["stratum"], pa.string()), "pop_h": pa.array(cat["pop_h"], pa.int64()),
                    "samp_h": pa.array(cat["samp_h"], pa.int64()), "unit_id": pa.array(cat["unit_id"], pa.int64()),
                    "y": pa.array(cat["y"], pa.float64()), "x": pa.array(cat["x"], pa.float64()),
                    "w": pa.array(cat["w"], pa.float64())})
    con.register("pde_sample_arrow", tbl)
    con.execute("CREATE OR REPLACE TABLE pde_sample AS SELECT rep, domain, stratum, pop_h, samp_h, unit_id, "
                "y::DECIMAL(18, 6) AS y, x::DECIMAL(18, 6) AS x, w FROM pde_sample_arrow")
    con.unregister("pde_sample_arrow")
    gdc_total = float(k.sub.sum()) / 100.0                        # population submitted GDC (dollars)
    X = k.X / 100.0
    # the shared macros read the table named `sample`: swap the beneficiary audit out and back
    con.execute("ALTER TABLE sample RENAME TO sample_bene_audit")
    try:
        con.execute("CREATE TABLE sample AS SELECT * FROM pde_sample")
        con.execute(f"""
            CREATE OR REPLACE TABLE est_pde AS
            SELECT 'pde_expansion' AS method, "interval", rep, domain, estimate, se, lower, upper
            FROM ipm_expansion(getvariable('alpha'))
            UNION ALL
            SELECT 'pde_ratio', "interval", rep, domain,
                   estimate * {gdc_total!r} / {X!r}, se * {gdc_total!r} / {X!r},
                   lower * {gdc_total!r} / {X!r}, upper * {gdc_total!r} / {X!r}
            FROM ipm_ratio(getvariable('alpha'))""")
    finally:
        con.execute("DROP TABLE IF EXISTS sample")
        con.execute("ALTER TABLE sample_bene_audit RENAME TO sample")


def run_expansion(con, v):
    """Expansion (plug-in benefit rerun) with a delta-method interval;
    writes table est_expansion."""
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
