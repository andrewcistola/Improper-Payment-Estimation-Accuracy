"""Check the SQL estimators (shared/sql/lib/02_estimators.sql) against an
independent numpy implementation written directly from textbook formulas
(per-unit residuals, not the moment identities the SQL uses)."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ipsim.engine import connect  # noqa: E402

Z = 1.959963984540054


def toy(seed=3, sizes=((5000, 60), (2000, 40), (800, 25))):
    """A stratified sample with skewed, zero-heavy errors and known X."""
    rng = np.random.default_rng(seed)
    rows, X = [], 0.0
    for h, (N, n) in enumerate(sizes):
        x_pop = np.round(rng.lognormal(6 + h, 0.8, N), 2)
        X += x_pop.sum()
        idx = rng.choice(N, n, replace=False)
        x = x_pop[idx]
        y = np.where(rng.random(n) < 0.3, np.round(x * rng.uniform(0.2, 1, n), 2), 0.0)
        for i in range(n):
            rows.append((1, "d", f"S{h}", N, n, h * 100000 + i, y[i], x[i], N / n))
    return rows, X


def load(rows, X, extra_vars=None):
    con = connect()
    con.execute("CREATE OR REPLACE TABLE sample AS SELECT * FROM (VALUES "
                + ",".join(f"({r[0]},'{r[1]}','{r[2]}',{r[3]},{r[4]},{r[5]},{r[6]:.6f},{r[7]:.6f},{r[8]})" for r in rows)
                + ") t(rep, domain, stratum, pop_h, samp_h, unit_id, y, x, w)")
    con.execute("CREATE OR REPLACE TABLE sample AS SELECT rep::INTEGER rep, domain, stratum, pop_h::BIGINT pop_h, "
                "samp_h::BIGINT samp_h, unit_id::BIGINT unit_id, y::DECIMAL(18,6) y, x::DECIMAL(18,6) x, w::DOUBLE w FROM sample")
    con.execute(f"CREATE OR REPLACE TABLE frame_totals AS SELECT 'd' AS domain, {X}::DOUBLE AS X, NULL::DOUBLE AS Y, NULL::DOUBLE AS theta")
    for k, v in (extra_vars or {"seed": 5}).items():
        con.execute(f"SET VARIABLE {k} = ?", [v])
    return con


def numpy_reference(rows, X):
    strata = {}
    for _, _, h, N, n, _, y, x, _ in rows:
        strata.setdefault(h, {"N": N, "n": n, "y": [], "x": []})
        strata[h]["y"].append(y)
        strata[h]["x"].append(x)
    for s in strata.values():
        s["y"], s["x"] = np.array(s["y"]), np.array(s["x"])
    T_y = sum(s["N"] * s["y"].mean() for s in strata.values())
    T_x = sum(s["N"] * s["x"].mean() for s in strata.values())

    def var_total(resid):  # resid: dict stratum -> per-unit residuals
        return sum(s["N"] ** 2 * (1 - s["n"] / s["N"]) * np.var(resid[h], ddof=1) / s["n"]
                   for h, s in strata.items())

    out = {}
    out["expansion"] = (T_y / X, np.sqrt(var_total({h: s["y"] for h, s in strata.items()})) / X)
    R = T_y / T_x
    out["ratio"] = (R, np.sqrt(var_total({h: s["y"] - R * s["x"] for h, s in strata.items()})) / T_x)
    # GREG, one auxiliary + intercept, weighted least squares with w = N/n
    w = np.concatenate([np.full(s["n"], s["N"] / s["n"]) for s in strata.values()])
    xs = np.concatenate([s["x"] for s in strata.values()])
    ys = np.concatenate([s["y"] for s in strata.values()])
    xbar, ybar = np.average(xs, weights=w), np.average(ys, weights=w)
    b = np.sum(w * (xs - xbar) * (ys - ybar)) / np.sum(w * (xs - xbar) ** 2)
    a = ybar - b * xbar
    T_reg = T_y + b * (X - T_x)
    out["regression"] = (T_reg / X, np.sqrt(var_total({h: s["y"] - a - b * s["x"] for h, s in strata.items()})) / X)
    return out, strata, R


@pytest.mark.parametrize("method,macro", [("expansion", "ipm_expansion"), ("ratio", "ipm_ratio"),
                                          ("regression", "ipm_regression")])
def test_analytic_estimators_match_numpy(method, macro):
    rows, X = toy()
    con = load(rows, X)
    est, se, lo, hi = con.execute(f"SELECT estimate, se, lower, upper FROM {macro}(0.05)").fetchone()
    ref, _, _ = numpy_reference(rows, X)
    assert est == pytest.approx(ref[method][0], rel=1e-10)
    assert se == pytest.approx(ref[method][1], rel=1e-8)
    assert lo == pytest.approx(ref[method][0] - Z * ref[method][1], rel=1e-7)
    assert hi == pytest.approx(ref[method][0] + Z * ref[method][1], rel=1e-7)


def test_bootstrap_matches_independent_numpy_bootstrap():
    """Rao-Wu rescaled bootstrap, written separately in numpy with its own
    RNG; the SQL and numpy bootstrap distributions must agree within Monte
    Carlo error (B = 4000 each)."""
    rows, X = toy()
    con = load(rows, X)
    B = 4000
    res = {r[0]: r[1:] for r in con.execute(
        f"SELECT interval, estimate, se, lower, upper FROM ipm_bootstrap({B}, 0.05)").fetchall()}
    ref, strata, R = numpy_reference(rows, X)
    rng = np.random.default_rng(11)
    th = np.empty(B)
    for b in range(B):
        ty = tx = 0.0
        for s in strata.values():
            N, n = s["N"], s["n"]
            m, lam = n - 1, np.sqrt(1 - n / N)
            c = np.bincount(rng.integers(0, n, m), minlength=n)
            wstar = (N / n) * (1 - lam + lam * (n / m) * c)
            ty += np.sum(wstar * s["y"])
            tx += np.sum(wstar * s["x"])
        th[b] = ty / tx
    pct = res["percentile"]
    assert pct[0] == pytest.approx(R, rel=1e-10)                 # point estimate = ratio
    assert pct[1] == pytest.approx(th.std(ddof=1), rel=0.06)     # bootstrap SE
    assert pct[1] == pytest.approx(ref["ratio"][1], rel=0.08)    # ~ linearization SE
    assert pct[2] == pytest.approx(np.quantile(th, 0.025), abs=0.25 * th.std())
    assert pct[3] == pytest.approx(np.quantile(th, 0.975), abs=0.25 * th.std())
    for interval in ("bootstrap_t", "bca"):
        lo, hi = res[interval][2], res[interval][3]
        assert lo < R < hi
        assert (hi - lo) == pytest.approx(pct[3] - pct[2], rel=0.25)


def test_census_has_zero_variance():
    """Sampling every unit (f = 1): all standard errors are 0 and every
    interval collapses to the true rate."""
    rows, X = toy(sizes=((40, 40), (25, 25)))
    X = sum(r[7] for r in rows)
    con = load(rows, X)
    theta = sum(r[6] for r in rows) / X
    for macro in ("ipm_expansion(0.05)", "ipm_ratio(0.05)", "ipm_regression(0.05)", "ipm_bootstrap(200, 0.05)"):
        for est, se, lo, hi in con.execute(f"SELECT estimate, se, lower, upper FROM {macro}").fetchall():
            assert est == pytest.approx(theta, rel=1e-10)
            assert se == pytest.approx(0, abs=1e-12)
            assert lo == pytest.approx(theta, rel=1e-9) and hi == pytest.approx(theta, rel=1e-9)
