"""Regression estimator: model fit within strata on the audit, predicted for
the population, residual (linearization) confidence interval from one audit.

Called as a config step {python: shared/ipsim/regression.py, run: run} after
the program's audit (`sample`, `frame_totals`) and its 30_regression.sql,
which builds:
  reg_population(unit_id, stratum, model_stratum, <predictors>)
      one row per population unit: its design stratum, the stratum its model
      is fit in (the design stratum, or a post-stratum), and the predictors
      named in the config variable reg_predictors (basic beneficiary
      variables and the amount paid).

For each audit year and domain (the audit is the one the ratio estimator
uses):
  1. Fit, in each model stratum m, a design-weighted least-squares regression
     of the audited improper dollars y on an intercept and the predictors.
     If the stratum's audit has fewer than reg_min_errors units with an
     error (in any domain, so that a sparse measure such as underpayments
     shares the model chosen for the gross rate) or fewer than (terms + 5)
     units, the model is intercept-only there (the stratum's weighted mean:
     expansion). The same design matrix is used for every domain, so the fit
     is linear in y: gross = over + under and net = over - under exactly.
     The price of that linearity is that a sparse domain can be fit with a
     full model chosen because of errors in another domain.
  2. Predict every population unit of the domain: the population total of
     the predictions is beta_m . (sum of the predictors over the stratum's
     population units), so unit-level predictions are never materialized.
  3. Estimate  T = sum over population of y_hat + sum over audit of w (y - y_hat)
     (model-assisted: the residual term keeps it design-consistent even if
     the model is wrong).
  4. Variance from the residuals e = y - y_hat, by design stratum h:
       V = sum_h N_h^2 (1 - n_h / N_h) s_e,h^2 / n_h
     95% interval: T +- t(df) sqrt(V), df = audit units in the domain -
     model terms fitted (intercepts included, one per model stratum);
     everything divided by the known total payments X.
Writes table est_regression(method, interval, rep, domain, estimate, se,
lower, upper), the same columns as the other estimators.
"""
from __future__ import annotations

import json

import numpy as np
import pyarrow as pa
from scipy import stats


def _predictors(v):
    p = v["reg_predictors"]
    return json.loads(p) if isinstance(p, str) else list(p)


def run(con, v):
    preds = _predictors(v)
    min_err = int(v.get("reg_min_errors", 10))
    alpha = float(v.get("alpha", 0.05))
    cols = ", ".join(f"{c}::DOUBLE AS {c}" for c in preds)
    sums = ", ".join(f"fsum({c}) AS {c}" for c in preds)   # fixed-order sums: identical at any thread count

    # population totals of the predictors by (design stratum, model stratum)
    tot = con.execute(f"SELECT stratum, model_stratum, count(*)::DOUBLE AS n, {sums} FROM reg_population "
                      f"GROUP BY stratum, model_stratum ORDER BY stratum, model_stratum").fetchnumpy()
    totals = {}
    for i in range(len(tot["n"])):
        totals[(str(tot["stratum"][i]), str(tot["model_stratum"][i]))] = np.array(
            [tot["n"][i]] + [tot[c][i] for c in preds])

    X_tot = dict(con.execute("SELECT domain, X FROM frame_totals").fetchall())
    all_reps = [r for (r,) in con.execute("SELECT DISTINCT rep FROM sample ORDER BY rep").fetchall()]
    rows = []
    for r in all_reps:
        # audited units with their predictors, one audit year at a time (all of them at once
        # is 30M rows for CERT at 100 audit years)
        s = con.execute(f"""
            SELECT s.rep, s.domain, s.stratum, s.pop_h::DOUBLE AS pop_h, s.samp_h::DOUBLE AS samp_h, s.w,
                   s.unit_id, s.y::DOUBLE AS y, p.model_stratum, {', '.join('p.' + c + '::DOUBLE AS ' + c for c in preds)}
            FROM sample s JOIN reg_population p USING (unit_id)
            WHERE s.rep = ?
            ORDER BY s.rep, s.domain, s.unit_id""", [r]).fetchnumpy()
        rep, dom = np.asarray(s["rep"]), np.asarray(s["domain"]).astype(str)
        strat, mstrat = np.asarray(s["stratum"]).astype(str), np.asarray(s["model_stratum"]).astype(str)
        unit, y, w = np.asarray(s["unit_id"]), np.asarray(s["y"], float), np.asarray(s["w"], float)
        pop_h, samp_h = np.asarray(s["pop_h"], float), np.asarray(s["samp_h"], float)
        Z = np.column_stack([np.ones(len(y))] + [np.asarray(s[c], float) for c in preds])
        in_r = rep == r
        # units with an error in any domain this audit year (sets intercept-only fallback)
        err_units = np.unique(unit[in_r & (y != 0)])
        for d in np.unique(dom[in_r]):
            k = in_r & (dom == d)
            zk, yk, wk, sk, mk = Z[k], y[k], w[k], strat[k], mstrat[k]
            uk = unit[k]
            pred_tot, resid, terms = 0.0, np.empty(len(yk)), 0
            strata_d = sorted(set(sk.tolist()))   # sorted: fixed summation order in every process
            for m in np.unique(mk):
                j = mk == m
                n_err = int(np.isin(uk[j], err_units).sum())
                full = n_err >= min_err and j.sum() >= zk.shape[1] + 5
                cols_m = slice(None) if full else slice(0, 1)
                zm = zk[j][:, cols_m]
                sw = np.sqrt(wk[j])
                beta, *_ = np.linalg.lstsq(zm * sw[:, None], yk[j] * sw, rcond=None)
                terms += int(np.linalg.matrix_rank(zm))
                resid[j] = yk[j] - zm @ beta
                # population total of predictions in model stratum m, over the domain's design strata
                for (h, mm), t in totals.items():
                    if mm == m and h in strata_d:
                        pred_tot += float(t[cols_m] @ beta)
            est = pred_tot + float(np.sum(wk * resid))
            var = 0.0
            for h in strata_d:
                jh = sk == h
                n, N = jh.sum(), pop_h[k][jh][0]
                if n > 1:
                    var += N * N * (1 - n / N) * resid[jh].var(ddof=1) / n
            # terms already counts one intercept per model stratum, so the
            # design strata are not subtracted again
            df = max(1, len(yk) - terms)
            tq = float(stats.t.ppf(1 - alpha / 2, df))
            X = float(X_tot[d])
            se = np.sqrt(var) / X
            rows.append(("regression", "normal", int(r), d, est / X, se, est / X - tq * se, est / X + tq * se))

    cols_out = list(zip(*rows))
    tbl = pa.table({"method": pa.array(cols_out[0], pa.string()), "interval": pa.array(cols_out[1], pa.string()),
                    "rep": pa.array(cols_out[2], pa.int32()), "domain": pa.array(cols_out[3], pa.string()),
                    "estimate": pa.array(cols_out[4], pa.float64()), "se": pa.array(cols_out[5], pa.float64()),
                    "lower": pa.array(cols_out[6], pa.float64()), "upper": pa.array(cols_out[7], pa.float64())})
    con.register("est_regression_arrow", tbl)
    con.execute("CREATE OR REPLACE TABLE est_regression AS SELECT * FROM est_regression_arrow")
    con.unregister("est_regression_arrow")
