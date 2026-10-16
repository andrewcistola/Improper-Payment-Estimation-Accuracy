"""RADV improper-payment prediction model (the one ML step).

Mirrors the CPI approach in spirit: a model trained on a PRIOR year's
audited outcomes scores the current year's enrollees, and each
contract's RADV frame is its top quartile by that score.

  1. Rebuild a prior-year population with the same SQL (capitation
     steps 01-03) and a different child seed.
  2. Fit a gradient-boosted classifier for P(Delta-R > 0) on features a
     plan's submission data would show before any record review.
  3. Score the current population; write ml_scores(unit_id, pred_score).

Everything is deterministic (fixed random_state, single thread).
Python is used only because SQL has no model fitting.
"""
from __future__ import annotations

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

from .engine import SQL_DIR, child_seed

FEATURES_SQL = """
SELECT u.unit_id, (u.delta_r > 0)::INT AS target,
       u.risk_orig, u.demo_score, u.n_hcc, u.months,
       coalesce(h.n_severe, 0) AS n_severe,
       coalesce(h.n_chart, 0) AS n_chart_review,
       {fam_cols},
       avg(u.risk_orig) OVER (PARTITION BY u.contract_id) AS contract_mean_risk,
       avg(coalesce(h.n_chart, 0)) OVER (PARTITION BY u.contract_id) AS contract_chart_rate
FROM capitation_units u
LEFT JOIN (
    SELECT enrollee_id, count(*) FILTER (WHERE severe) AS n_severe,
           count(*) FILTER (WHERE chart_review) AS n_chart,
           {fam_aggs}
    FROM hccs GROUP BY enrollee_id) h ON h.enrollee_id = u.unit_id
ORDER BY u.unit_id
"""
FAMS = list("ABCDEFGHIJ")


def _features(con):
    fam_aggs = ", ".join(
        f"max(CASE WHEN fam = '{f}' THEN (CASE WHEN severe THEN 2 ELSE 1 END) ELSE 0 END) AS fam_{f}"
        for f in FAMS)
    fam_cols = ", ".join(f"coalesce(h.fam_{f}, 0) AS fam_{f}" for f in FAMS)
    df = con.execute(FEATURES_SQL.format(fam_aggs=fam_aggs, fam_cols=fam_cols)).fetchnumpy()
    cols = [c for c in df if c not in ("unit_id", "target")]
    X = np.column_stack([np.asarray(df[c], dtype=float) for c in cols])
    return df["unit_id"], np.asarray(df["target"]), X, cols


def radv_frame_scores(ctx, prior_contract_scale: float = 1.0):
    con = ctx.con
    # ---- 1. prior-year population in a separate connection ----------
    import duckdb
    prior = duckdb.connect()
    for lib in sorted((SQL_DIR / "lib").glob("*.sql")):
        prior.execute(lib.read_text())
    for k, v in ctx.vars.items():
        if isinstance(v, (list, dict)):
            import json
            v = json.dumps(v)
        prior.execute(f"SET VARIABLE {k} = ?", [v])
    prior_seed = child_seed(ctx.vars["master_seed"], ctx.program, ctx.scenario, "prior_year")
    prior.execute("SET VARIABLE seed = ?", [prior_seed])
    for f in ("capitation/01_contracts.sql", "capitation/02_enrollees_hccs.sql",
              "capitation/03_payments_errors.sql"):
        prior.execute((SQL_DIR / f).read_text())

    # ---- 2. fit on prior year ---------------------------------------
    _, y_tr, X_tr, cols = _features(prior)
    model = HistGradientBoostingClassifier(
        max_iter=200, learning_rate=0.05, max_leaf_nodes=31,
        l2_regularization=1.0, random_state=0)
    model.fit(X_tr, y_tr)
    prior.close()

    # ---- 3. score current year --------------------------------------
    ids, y_cur, X_cur, _ = _features(con)
    score = model.predict_proba(X_cur)[:, 1]
    score = np.round(score, 6)  # fixed precision -> stable ranks and hashes
    import pyarrow as pa
    tbl = pa.table({"unit_id": ids, "pred_score": score})
    con.register("ml_scores_arrow", tbl)
    con.execute("CREATE OR REPLACE TABLE ml_scores AS SELECT * FROM ml_scores_arrow")
    con.unregister("ml_scores_arrow")

    auc_cur = float(roc_auc_score(y_cur, score)) if 0 < y_cur.sum() < len(y_cur) else None
    ctx.log.append({
        "step": "radv_prediction_model",
        "model": "sklearn HistGradientBoostingClassifier",
        "params": {"max_iter": 200, "learning_rate": 0.05, "max_leaf_nodes": 31,
                   "l2_regularization": 1.0, "random_state": 0},
        "features": cols,
        "train": {"population": "prior year (same generator, seed label 'prior_year')",
                  "seed": prior_seed, "n": int(len(y_tr)), "positives": int(y_tr.sum())},
        "score_population": {"n": int(len(y_cur)), "positives": int(y_cur.sum()),
                             "auc_current_year": auc_cur},
    })
    con.execute("SET VARIABLE ml_auc = ?", [auc_cur])
