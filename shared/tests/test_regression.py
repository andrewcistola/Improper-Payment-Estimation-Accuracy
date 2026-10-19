"""Regression estimator (shared/ipsim/regression.py) on a toy stratified audit.

1. Intercept-only (forced by reg_min_errors): the estimate and standard error
   equal the expansion estimator's (stratum means x N_h; stratified variance).
2. Linear in y: over + under = gross, over - under = net, for the estimate.
3. A predictor that explains y exactly gives zero residual variance and the
   true total.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ipsim.engine import connect  # noqa: E402
from ipsim.simulation import load_kernel  # noqa: E402

reg = load_kernel(Path(__file__).resolve().parents[1] / "ipsim" / "regression.py")


def toy(con, y_of):
    rng = np.random.default_rng(1)
    N = {"a": 400, "b": 600}
    rows, uid = [], 0
    for h, n_pop in N.items():
        for _ in range(n_pop):
            uid += 1
            rows.append((uid, h, float(rng.lognormal(5, 1)), float(rng.integers(20, 90))))
    pop = np.array([(r[0], r[2], r[3]) for r in rows])
    strata = [r[1] for r in rows]
    con.execute("CREATE TABLE reg_population (unit_id BIGINT, stratum VARCHAR, model_stratum VARCHAR, x DOUBLE, age DOUBLE)")
    con.executemany("INSERT INTO reg_population VALUES (?, ?, ?, ?, ?)", [(r[0], r[1], r[1], r[2], r[3]) for r in rows])
    take = {h: rng.choice([r[0] for r in rows if r[1] == h], 80, replace=False) for h in N}
    con.execute("CREATE OR REPLACE TABLE sample (rep INTEGER, domain VARCHAR, stratum VARCHAR, pop_h BIGINT, "
                "samp_h BIGINT, unit_id BIGINT, y DECIMAL(18,6), x DECIMAL(18,6), w DOUBLE)")
    con.execute("CREATE OR REPLACE TABLE frame_totals (domain VARCHAR, X DOUBLE, Y DOUBLE, theta DOUBLE)")
    X = float(pop[:, 1].sum())
    yv = {d: y_of(d, pop[:, 1], pop[:, 2], rng) for d in ("over", "under")}
    yv["gross"] = yv["over"] + yv["under"]
    yv["net"] = yv["over"] - yv["under"]
    for d, yy in yv.items():
        con.execute("INSERT INTO frame_totals VALUES (?, ?, ?, ?)", [d, X, float(yy.sum()), float(yy.sum()) / X])
        for h, ids in take.items():
            for u in ids:
                con.execute("INSERT INTO sample VALUES (1, ?, ?, ?, 80, ?, ?, ?, ?)",
                            [d, h, N[h], int(u), round(float(yy[u - 1]), 6), pop[u - 1, 1], N[h] / 80])
    return X, yv


def results(con):
    return {d: (e, s) for d, e, s in con.execute("SELECT domain, estimate, se FROM est_regression").fetchall()}


def test_intercept_only_is_expansion():
    con = connect()
    toy(con, lambda d, x, a, rng: np.where(rng.random(len(x)) < 0.2, x * (0.5 if d == "over" else 0.1), 0.0))
    reg.run(con, {"reg_predictors": ["x", "age"], "reg_min_errors": 10 ** 6, "alpha": 0.05})
    got = results(con)
    exp = dict((d, (e, s)) for d, e, s in con.execute(
        "SELECT domain, estimate, se FROM ipm_expansion(0.05)").fetchall())
    for d in exp:
        assert np.isclose(got[d][0], exp[d][0], rtol=1e-12) and np.isclose(got[d][1], exp[d][1], rtol=1e-9)


def test_linear_in_y_and_exact_fit():
    con = connect()
    X, yv = toy(con, lambda d, x, a, rng: (0.05 if d == "over" else 0.01) * x + (2.0 if d == "over" else 0.5) * a)
    reg.run(con, {"reg_predictors": ["x", "age"], "reg_min_errors": 0, "alpha": 0.05})
    got = results(con)
    assert np.isclose(got["gross"][0], got["over"][0] + got["under"][0], rtol=1e-10)
    assert np.isclose(got["net"][0], got["over"][0] - got["under"][0], rtol=1e-10)
    for d in ("over", "gross"):                 # y is an exact linear function: no residual error
        assert np.isclose(got[d][0], yv[d].sum() / X, rtol=1e-6) and got[d][1] < 1e-6
