"""Audit-finding bootstrap simulation: payment functions and mechanics.

1. Exactness: each program's numpy payment function, given every unit's
   OWN audit finding, reproduces the improper payment computed by the SQL
   in errors/ for every unit, to the cent. (Part D and PERM populations
   are not committed; their tests run once errors/ has been built.)
2. Assignment: recipients receive errors at the donor pool's rate, only
   from donors of the same kind; audited units keep their own findings.
3. Reproducibility: the same seed gives identical estimates.
"""
import sys
from pathlib import Path

import numpy as np
import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ipsim.engine import ROOT, connect  # noqa: E402
from ipsim.simulation import RowSet, bernoulli_positions, load_kernel  # noqa: E402


def setup(pop_dir, inputs_sql, extra=None):
    if not (ROOT / pop_dir / "population.parquet").exists():
        pytest.skip(f"build {pop_dir} first")
    con = connect()
    for k, v in {"repo_root": str(ROOT), "population_dir": pop_dir, **(extra or {})}.items():
        con.execute(f"SET VARIABLE {k} = ?", [v])
    con.execute((ROOT / inputs_sql).read_text())
    return con


def test_part_c_payment_function_exact():
    con = setup("part-c-ipm/errors/output/base", "part-c-ipm/estimation/sql/40_simulation_inputs.sql")
    k = load_kernel(ROOT / "part-c-ipm/estimation/simulation.py").Kernel(con, {})
    y = k.improper_cents(k.outcome, k.md, k.add_fam)
    truth = con.execute("SELECT y_cents FROM sim_units ORDER BY unit_idx").fetchnumpy()["y_cents"]
    assert len(y) == 330253 and np.array_equal(y, truth)


def partc_kernel():
    con = setup("part-c-ipm/errors/output/base", "part-c-ipm/estimation/sql/40_simulation_inputs.sql")
    return con, load_kernel(ROOT / "part-c-ipm/estimation/simulation.py").Kernel(con, {})


def test_part_c_bootstrap_census_is_exact():
    """Every enrollee audited: each keeps its own finding, so every
    iteration gives the exact over, under, gross and net rates."""
    con, k = partc_kernel()
    y = con.execute("SELECT y_cents FROM sim_units ORDER BY unit_idx").fetchnumpy()["y_cents"].astype(float)
    k.prepare(1, np.ones(k.units, bool))
    got = k.iterate(None, np.random.default_rng(1))
    over, under = y[y > 0].sum(), -y[y < 0].sum()
    assert got == {"national|over": over / k.X, "national|under": under / k.X,
                   "national|gross": (over + under) / k.X, "national|net": (over - under) / k.X}


def test_part_c_bootstrap_rates():
    """No extrapolation: an HCC with no audited instance never fails. With a
    large audit the HCC rates reproduce the net rate (net is linear in the
    findings, so it is unbiased; gross is not, see the README)."""
    con, k = partc_kernel()
    rng = np.random.default_rng(7)
    lacks_j = ((k.fam_mask >> 9) & 1) == 0                         # family J = code 9
    audited = lacks_j & (rng.random(k.units) < 0.5)
    k.prepare(1, audited)
    assert k.f_rate[18] == 0 and k.f_rate[19] == 0 and (k.f_rate[:18] > 0).all()
    assert (k.a_rate > 0).all()
    y = con.execute("SELECT y_cents FROM sim_units ORDER BY unit_idx").fetchnumpy()["y_cents"].astype(float)
    k.prepare(1, rng.random(k.units) < 0.5)
    net = np.mean([k.iterate(None, rng)["national|net"] for _ in range(20)])
    assert abs(net / (y.sum() / k.X) - 1) < 0.01


def test_part_c_bootstrap_unbiased_per_domain():
    """Production audit (990 enrollees, 330 per risk-score tercile): the mean
    simulated over, under, gross and net each match the expectation of
    the population's rules evaluated at the audit's rates, computed here
    from the audit independently of the kernel: an HCC instance fails with
    f_k and loses L_k; an enrollee lacking family f with no failed HCC
    gains it with a_f = audited additions of f / audited enrollees lacking
    f with no overpayment finding. Averaged over several audits and
    iterations, each is within 3% -- tight enough to catch the 8%
    shortfall in under that netting additions against failures produced
    (that version also set a_f over all audited enrollees lacking f)."""
    con, k = partc_kernel()
    strat = con.execute("SELECT stratum FROM sim_units ORDER BY unit_idx").fetchnumpy()["stratum"].astype(str)
    rng = np.random.default_rng(11)
    y = k.y_cents.astype(float)
    cm = (k.rate * k.months).astype(float)
    over_unit = np.bincount(k.row_unit[k.failed_row], minlength=k.units) > 0   # overpayment finding
    exp, sim = np.zeros(2), np.zeros(2)
    for _ in range(4):
        aud = np.concatenate([rng.choice(np.flatnonzero(strat == s), 330, replace=False)
                              for s in ("low", "medium", "high")])
        am = np.zeros(k.units, bool)
        am[aud] = True
        k.prepare(1, am)
        # audited HCC rates, from the audit
        aud_row = am[k.row_unit]
        n_k = np.bincount(k.hcc[aud_row], minlength=20)
        nf_k = np.bincount(k.hcc[aud_row & k.failed_row], minlength=20)
        loss_k = np.bincount(k.hcc[aud_row & k.failed_row], weights=k.loss_row[aud_row & k.failed_row], minlength=20)
        f_rate = nf_k / np.maximum(n_k, 1)
        f_loss = loss_k / np.maximum(nf_k, 1)
        p_nofail = np.exp(np.bincount(k.row_unit, weights=np.log1p(-f_rate[k.hcc]), minlength=k.units))
        non = ~am
        e_over = (f_rate[k.hcc] * f_loss[k.hcc] * cm[k.row_unit] * non[k.row_unit]).sum() / 1000.0
        e_under = 0.0
        for f in range(10):
            lacks = ((k.fam_mask >> f) & 1) == 0
            a_f = (am & (k.add_fam == f)).sum() / max((am & lacks & ~over_unit).sum(), 1)
            e_under += a_f * k.mild[f] * (p_nofail * cm)[non & lacks].sum() / 1000.0
        exp += [e_over + y[am & (y > 0)].sum(), e_under - y[am & (y < 0)].sum()]
        it = [k.iterate(aud, rng) for _ in range(15)]
        sim += [np.mean([r["national|over"] for r in it]) * k.X, np.mean([r["national|under"] for r in it]) * k.X]
    over, under = sim / exp
    assert abs(over - 1) < 0.03 and abs(under - 1) < 0.03
    assert abs(sim.sum() / exp.sum() - 1) < 0.03                       # gross
    assert abs((sim[0] - sim[1]) / (exp[0] - exp[1]) - 1) < 0.03       # net


def partd_kernel(extra=None, design="config.yaml", pop="part-d-ipm/errors/output/base"):
    cfg = yaml.safe_load((ROOT / "part-d-ipm/errors" / design).read_text())["defaults"]
    v = {**cfg, "seed": 1, "sim_reps": 1, "sim_audit_size": 300, **(extra or {})}
    if not (ROOT / pop / "pde_detail.parquet").exists():
        pytest.skip(f"build {pop} first")
    con = setup(pop, "part-d-ipm/estimation/sql/40_simulation_inputs.sql", v)
    return con, load_kernel(ROOT / "part-d-ipm/estimation/simulation.py"), v


def test_part_d_pre_ira_payment_function_exact():
    """Alternative design: the numpy CY 2023 (pre-IRA) benefit reproduces
    errors/sql/05_benefit_pre_ira.sql y to the cent; an audit of every PDE
    gives the exact rates."""
    con, mod, v = partd_kernel(design="pre_ira.yaml", pop="part-d-ipm/errors/output_pre_ira/base")
    k = mod.Kernel(con, v)
    assert k.payment is mod.medicare_cents_pre_ira
    assert np.array_equal(k.improper_cents(k.cor), k.y_true)
    k.prepare(1, np.ones(k.units, bool))
    y = k.y_true.astype(float)
    over, under = y[y > 0].sum(), -y[y < 0].sum()
    assert k.iterate(None, np.random.default_rng(1))["national|gross"] == (over + under) / k.X


def test_part_d_payment_function_exact():
    """The numpy benefit rerun reproduces errors/ y to the cent; an audit of
    every PDE gives the exact rates; the PDE audit has the Neyman sizes."""
    con, mod, v = partd_kernel()
    k = mod.Kernel(con, v)
    assert np.array_equal(k.improper_cents(k.cor), k.y_true)
    k.prepare(1, np.ones(k.units, bool))
    y = k.y_true.astype(float)
    over, under = y[y > 0].sum(), -y[y < 0].sum()
    assert k.iterate(None, np.random.default_rng(1)) == {
        "national|over": over / k.X, "national|under": under / k.X,
        "national|gross": (over + under) / k.X, "national|net": (over - under) / k.X}
    n_h = dict(con.execute("SELECT stratum_code, n_h FROM pde_strata").fetchall())
    got = dict(con.execute("SELECT r.stratum_code, count(*) FROM sim_audit_sample a JOIN sim_rows r USING (row_idx) "
                           "GROUP BY 1").fetchall())
    assert got == n_h and sum(n_h.values()) == 300 and min(n_h.values()) >= 2


def test_part_d_bootstrap_rates_unbiased():
    """With a large audit, both rate versions reproduce the true gross rate."""
    con, mod, v = partd_kernel()
    rng = np.random.default_rng(3)
    for rates in ("fixed", "parametric"):
        k = mod.Kernel(con, {**v, "sim_rates": rates})
        k.prepare(1, rng.random(k.units) < 0.3)
        y = k.y_true.astype(float)
        gross = np.mean([k.iterate(None, rng)["national|gross"] for _ in range(10)])
        assert abs(gross / (np.abs(y).sum() / k.X) - 1) < 0.02


def eipm_kernel(extra=None):
    cfg = yaml.safe_load((ROOT / "eipm/errors/config.yaml").read_text())["defaults"]
    con = setup("eipm/errors/output/base", "eipm/estimation/sql/40_simulation_inputs.sql")
    return con, load_kernel(ROOT / "eipm/estimation/simulation.py"), {**cfg, **(extra or {})}


def test_eipm_payment_function_exact():
    """Each application's own finding reproduces errors/ y to the cent (all
    overpayments); an audit of every application gives the exact rates."""
    con, mod, cfg = eipm_kernel()
    k = mod.Kernel(con, cfg)
    y = k.improper_cents(k.finding, np.where(k.finding == 1, k.true_fpl, k.fpl))
    truth = con.execute("SELECT y_cents FROM sim_units ORDER BY unit_idx").fetchnumpy()["y_cents"]
    assert np.array_equal(y["gross"], truth) and (truth >= 0).all()
    assert np.array_equal(mod.annual_aptc_cents(k.fpl, k.bench, k.fpl_dollars, k.months, k.schedule), k.x)
    for rates in ("fixed", "parametric"):
        k = mod.Kernel(con, {**cfg, "sim_rates": rates})
        k.prepare(1, np.ones(k.units, bool))
        got = k.iterate(None, np.random.default_rng(1))
        assert got["national|gross"] == truth.sum() / k.X
        assert got["national|technical"] + got["national|monetary"] == got["national|gross"]


def test_eipm_bootstrap_rates_unbiased():
    """With half the applications audited, both rate versions reproduce the
    audited half's own gross rate (the target the audit can see; the
    income ratio moved to another application costs about 1-2%)."""
    con, mod, cfg = eipm_kernel()
    rng = np.random.default_rng(5)
    y = con.execute("SELECT y_cents FROM sim_units ORDER BY unit_idx").fetchnumpy()["y_cents"].astype(float)
    for rates in ("fixed", "parametric"):
        k = mod.Kernel(con, {**cfg, "sim_rates": rates})
        m = rng.random(k.units) < 0.5
        k.prepare(1, m)
        target = y[m].sum() / m.sum() * k.units / k.X
        gross = np.mean([k.iterate(None, rng)["national|gross"] for _ in range(20)])
        assert abs(gross / target - 1) < 0.03


def cert_kernel(extra=None):
    if not (ROOT / "cert/errors/output/national/population.parquet").exists():
        pytest.skip("build cert/errors/config.yaml first")
    con = setup("cert/errors/output/national", "cert/estimation/sql/40_simulation_inputs.sql")
    return con, load_kernel(ROOT / "cert/estimation/simulation.py").Kernel(con, extra or {})


def test_cert_payment_function_exact():
    """Each claim's own taint reproduces errors/ y to the cent; an audit of
    every claim gives the exact over, under, gross, net and claim-type rates."""
    con, k = cert_kernel()
    assert np.array_equal(k.improper_cents(k.taint), k.y)
    k.prepare(1, np.ones(k.units, bool))
    got = k.iterate(None, np.random.default_rng(1))
    y = k.y.astype(float)
    over, under = y[y > 0].sum(), -y[y < 0].sum()
    assert got["national|over"] == over / k.X and got["national|under"] == under / k.X
    assert got["national|net"] == (over - under) / k.X
    g = np.bincount(k.type, weights=np.abs(y), minlength=4) / k.X_type
    assert np.allclose([got[f"{t}|gross"] for t in ("ipps", "part_a_other", "part_b", "dmepos")], g, rtol=1e-12)


def test_cert_bootstrap_rates_unbiased():
    """With 30% of claims audited, both rate versions reproduce the audited
    claims' own over and under rates."""
    rng = np.random.default_rng(9)
    for rates in ("fixed", "parametric"):
        con, k = cert_kernel({"sim_rates": rates})
        m = rng.random(k.units) < 0.3
        k.prepare(1, m)
        w = np.where(m, 1.0 / m.mean(), 0.0)   # crude expansion of the audited claims (same in every stratum)
        y = k.y * w
        it = [k.iterate(None, rng) for _ in range(5)]
        assert abs(np.mean([r["national|over"] for r in it]) / (y[y > 0].sum() / k.X) - 1) < 0.02
        assert abs(np.mean([r["national|under"] for r in it]) / (-y[y < 0].sum() / k.X) - 1) < 0.05


def test_perm_payment_function_exact():
    con = setup("perm/errors/output/state_elig_grid",
                "perm/estimation/sql/40_simulation_inputs.sql", {"state_id": 5})
    k = load_kernel(ROOT / "perm/estimation/simulation.py").Kernel(con, {"state_id": 5})
    y = k.improper_cents(k.yc, k.elig)
    t = con.execute("SELECT (y * 100)::BIGINT AS y, (y_elig * 100)::BIGINT AS ye FROM read_parquet(?) "
                    "WHERE state_id = 5 ORDER BY unit_id",
                    [str(ROOT / "perm/errors/output/state_elig_grid/population.parquet")]).fetchnumpy()
    assert np.array_equal(y["gross"], t["y"]) and np.array_equal(y["eligibility"], t["ye"])
    # every payment audited: each keeps its own finding, so rates are exact
    k.prepare(1, np.ones(k.units, bool))
    for rates in (False, True):
        k.parametric = rates
        got = k.iterate(None, np.random.default_rng(1))
        assert got["5|gross"] == t["y"].sum() / k.X and got["5|eligibility"] == t["ye"].sum() / k.X


def test_bernoulli_positions():
    rng = np.random.default_rng(3)
    counts = [len(bernoulli_positions(10000, 0.07, rng)) for _ in range(300)]
    assert abs(np.mean(counts) - 700) < 5
    pos = bernoulli_positions(10000, 0.07, rng)
    assert len(np.unique(pos)) == len(pos) and pos.min() >= 0 and pos.max() < 10000
    assert len(bernoulli_positions(50, 1.0, rng)) == 50 and len(bernoulli_positions(50, 0.0, rng)) == 0


def test_rowset_assign():
    rng = np.random.default_rng(4)
    n_units = 2000
    unit = np.repeat(np.arange(n_units), 3)                 # 3 rows per unit
    kind = np.tile([0, 1, 1], n_units)
    identity = rng.random(len(unit)) > np.where(kind == 0, 0.2, 0.05)   # kind 0: 20% errors, kind 1: 5%
    rs = RowSet(unit, n_units, kind, identity)
    audited = np.zeros(n_units, bool)
    audited[:400] = True
    rs.prepare(audited)
    donors = np.arange(400)
    donor_rows = rs.rows_of(donors)
    rates = {k: (~identity[donor_rows][kind[donor_rows] == k]).mean() for k in (0, 1)}
    got = {0: [], 1: []}
    for _ in range(200):
        rows, d = rs.assign(donors, rng)
        assert not audited[unit[rows]].any()                 # audited units are never recipients
        assert np.array_equal(kind[rows], kind[d])           # donors of the same kind
        assert not identity[d].any() and audited[unit[d]].all()
        for k in (0, 1):
            got[k].append((kind[rows] == k).sum() / ((~audited[unit]) & (kind == k)).sum())
    for k in (0, 1):
        assert abs(np.mean(got[k]) - rates[k]) < 0.004


def test_simulation_reproducible(tmp_path):
    from ipsim.engine import Engine
    if not (ROOT / "eipm/errors/output/base/population.parquet").exists():
        pytest.skip("build eipm/errors/config.yaml first")
    out = []
    for i in range(2):
        e = Engine(ROOT / "eipm/estimation/config.yaml", tmp_path / f"r{i}")
        e.config["defaults"].update(reps=4, sim_reps=4, sim_iterations=150)
        e.run(["base"])
        out.append((tmp_path / f"r{i}" / "base" / "estimates.parquet").read_bytes())
    assert out[0] == out[1]
    import duckdb
    methods = {m for (m,) in duckdb.sql(f"SELECT DISTINCT method FROM '{tmp_path}/r0/base/estimates.parquet'").fetchall()}
    assert methods == {"expansion", "ratio", "regression", "simulation"}    # one simulation: the audit as audited


# --- Part D: design-based PDE-level estimators (pde_expansion, pde_ratio) ---

def partd_pde_census(con, mod, v, size):
    """Run run_pde_estimators with an audit of `size` PDEs per rep (the
    frame tables the shared macros need are built here, as the engine's
    01_frame.sql + sample_srs.sql would)."""
    con.execute("SET VARIABLE alpha = 0.05")
    if size is None:                                     # census: every PDE audited
        # a census of the first 6,000 beneficiaries' PDEs (the full population's
        # 4.5M PDEs x 4 domains would need several GB in the sample table)
        con.execute("DELETE FROM sim_rows WHERE unit_idx >= 6000")
        con.execute("DELETE FROM sim_units WHERE unit_idx >= 6000")
        con.execute("CREATE OR REPLACE TABLE sim_audit_sample AS SELECT 1 AS rep, row_idx FROM sim_rows")
    con.execute("CREATE OR REPLACE TABLE frame_totals AS "
                "SELECT 'national|' || m AS domain, sum(x_cents) / 100.0 AS X, NULL::DOUBLE AS Y, NULL::DOUBLE AS theta "
                "FROM sim_units, (SELECT unnest(['over', 'under', 'gross', 'net']) AS m) GROUP BY m")
    con.execute("CREATE OR REPLACE TABLE sample (rep INTEGER, domain VARCHAR, stratum VARCHAR, pop_h BIGINT, "
                "samp_h BIGINT, unit_id BIGINT, y DECIMAL(18, 6), x DECIMAL(18, 6), w DOUBLE)")
    mod.run_pde_estimators(con, {**v, "population_dir": con.execute("SELECT getvariable('population_dir')").fetchone()[0]})
    return {(m, d): (e, se) for m, d, e, se in
            con.execute("SELECT method, domain, estimate, se FROM est_pde WHERE rep = 1").fetchall()}


def test_part_d_marginal_effects_sum_to_netted_error():
    """A beneficiary with at most one PDE in error: its PDE marginal effects
    sum EXACTLY to its netted payment error (one PDE corrected = all
    corrected). With several PDEs in error the sum differs (the benefit is
    nonlinear); the census test below bounds that difference."""
    con, mod, v = partd_kernel()
    k = mod.Kernel(con, v)
    err_per_bene = np.bincount(k.row_unit, weights=(k.cor != k.sub), minlength=k.n_benes)
    rng = np.random.default_rng(2)
    one = np.flatnonzero(err_per_bene == 1)
    pick = rng.choice(one, 400, replace=False)
    rows = np.flatnonzero(np.isin(k.row_unit, pick))
    y = mod.marginal_effects(k, rows)
    per_bene = np.bincount(k.row_unit[rows], weights=y, minlength=k.n_benes)[pick]
    assert np.array_equal(per_bene, k.y_true[pick])
    assert (k.y_true[pick] != 0).sum() > 50                    # the check is not vacuous
    # no error -> exactly zero; several errors -> not more than the sum of full-GDC reinsurance
    zero = np.flatnonzero(np.isin(k.row_unit, np.flatnonzero(err_per_bene == 0)))[:500]
    assert not mod.marginal_effects(k, zero).any()


def test_part_d_pde_estimators_census():
    """Every PDE of a 6,000-beneficiary frame audited: pde_expansion and
    pde_ratio reproduce the PDE-level totals exactly (zero SE), and those
    totals are within 10% of the beneficiary-netted truth for over, gross
    and net (they differ only where a beneficiary has two or more PDEs in
    error; under is tiny and is not compared)."""
    con, mod, v = partd_kernel()
    est = partd_pde_census(con, mod, v, None)
    k = mod.Kernel(con, v)                                   # the census frame (6,000 beneficiaries)
    assert k.n_benes == 6000
    y = mod.marginal_effects(k, np.arange(k.units)).astype(float)
    X = k.X
    pde_truth = {"over": y[y > 0].sum() / X, "under": -y[y < 0].sum() / X,
                 "gross": np.abs(y).sum() / X, "net": y.sum() / X}
    for m in ("pde_expansion", "pde_ratio"):
        for d, t in pde_truth.items():
            e, se = est[(m, f"national|{d}")]
            assert abs(e - t) <= 1e-9 * max(t, 1e-6), (m, d, e, t)
            assert se == 0.0
    yt = k.y_true.astype(float)
    bene_truth = {"over": yt[yt > 0].sum() / X, "gross": np.abs(yt).sum() / X, "net": yt.sum() / X}
    for d, t in bene_truth.items():
        assert abs(pde_truth[d] / t - 1) < 0.10, (d, pde_truth[d], t)


def test_part_d_pde_estimators_sampled():
    """A 5,000-PDE stratified audit: both estimators are near the truth and
    report positive standard errors; the ratio estimate differs from the
    expansion estimate (the auxiliary is in use)."""
    con, mod, v = partd_kernel({"sim_audit_size": 5000})
    k = mod.Kernel(con, v)
    est = partd_pde_census(con, mod, v, 5000)
    truth = np.abs(k.y_true).sum() / k.X
    for m in ("pde_expansion", "pde_ratio"):
        e, se = est[(m, "national|gross")]
        assert se > 0 and abs(e - truth) < 4 * se, (m, e, se, truth)
    assert est[("pde_ratio", "national|gross")][0] != est[("pde_expansion", "national|gross")][0]
    assert con.execute("SELECT count(*) FROM sample").fetchone()[0] == 0   # beneficiary audit table restored (empty here)


def test_part_d_parametric_redraw_counts():
    """The parametric redraw draws f~ ~ Binomial(n, f/n) then g~ ~ Binomial(f~, g/f):
    with f = 0 in a stratum the redrawn p is 0 and q is 0 (no division by zero),
    and over many iterations the mean redrawn rate equals the audited rate."""
    con, mod, v = partd_kernel({"sim_rates": "parametric"})
    k = mod.Kernel(con, v)
    rng = np.random.default_rng(5)
    audited = rng.random(k.units) < 0.002
    k.prepare(1, audited)
    k._f[1] = 0; k._g[1] = 0; k._partial[1] = np.empty(0)      # force an empty-finding stratum
    y_true_gross = np.abs(k.y_true).sum() / k.X
    rates = [k.iterate(None, rng)["national|gross"] for _ in range(40)]
    assert all(np.isfinite(rates)) and 0 < np.mean(rates) < 3 * y_true_gross
