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


def partd_kernel(extra=None):
    cfg = yaml.safe_load((ROOT / "part-d-ipm/errors/config.yaml").read_text())["defaults"]
    v = {**cfg, "seed": 1, "sim_reps": 1, "sim_audit_size": 300, **(extra or {})}
    if not (ROOT / "part-d-ipm/errors/output/base/pde_detail.parquet").exists():
        pytest.skip("build part-d-ipm/errors first")
    con = setup("part-d-ipm/errors/output/base", "part-d-ipm/estimation/sql/40_simulation_inputs.sql", v)
    return con, load_kernel(ROOT / "part-d-ipm/estimation/simulation.py"), v


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


def test_eipm_payment_function_exact():
    cfg = yaml.safe_load((ROOT / "eipm/errors/config.yaml").read_text())["defaults"]
    con = setup("eipm/errors/output/base", "eipm/estimation/sql/40_simulation_inputs.sql")
    mod = load_kernel(ROOT / "eipm/estimation/simulation.py")
    k = mod.Kernel(con, cfg)
    y = k.improper_cents(k.finding, np.where(k.finding == 1, k.true_fpl, k.fpl))
    truth = con.execute("SELECT y_cents FROM sim_units ORDER BY unit_idx").fetchnumpy()["y_cents"]
    assert np.array_equal(y, truth)
    assert np.array_equal(mod.annual_aptc_cents(k.fpl, k.bench, k.fpl_dollars, k.months, k.schedule), k.x)


def test_perm_payment_function_exact():
    con = setup("perm-cert/errors/output/perm/state_elig_grid",
                "perm-cert/estimation/sql/perm_40_simulation_inputs.sql", {"state_id": 5})
    k = load_kernel(ROOT / "perm-cert/estimation/perm_simulation.py").Kernel(con, {"state_id": 5})
    y = k.improper_cents(k.yc, k.elig)
    t = con.execute("SELECT (y * 100)::BIGINT AS y, (y_elig * 100)::BIGINT AS ye FROM read_parquet(?) "
                    "WHERE state_id = 5 ORDER BY unit_id",
                    [str(ROOT / "perm-cert/errors/output/perm/state_elig_grid/population.parquet")]).fetchnumpy()
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
    if not (ROOT / "perm-cert/errors/output/cert/left_all_or_nothing_p0.30").exists():
        pytest.skip("build perm-cert/errors/cert.yaml first")
    out = []
    for i in range(2):
        e = Engine(ROOT / "perm-cert/estimation/cert.yaml", tmp_path / f"r{i}")
        e.config["defaults"].update(reps=6, sim_reps=4, sim_iterations=150)
        e.run(["left_p0.30"])
        out.append((tmp_path / f"r{i}" / "left_p0.30" / "estimates.parquet").read_bytes())
    assert out[0] == out[1]
    import duckdb
    methods = {m for (m,) in duckdb.sql(f"SELECT DISTINCT method FROM '{tmp_path}/r0/left_p0.30/estimates.parquet'").fetchall()}
    assert methods == {"expansion", "ratio", "regression", "simulation"}    # one simulation: the audit as audited
