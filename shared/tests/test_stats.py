"""Normal CDF / quantile and list quantile macros vs scipy and numpy."""
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy.stats import norm

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ipsim.engine import connect  # noqa: E402


def test_norm_cdf_and_ppf():
    c = connect()
    xs = np.linspace(-6, 6, 241)
    ps = np.concatenate([np.linspace(1e-6, 0.02, 50), np.linspace(0.02, 0.98, 97), np.linspace(0.98, 1 - 1e-6, 50)])
    cdf = np.array([c.execute("SELECT norm_cdf(?)", [float(x)]).fetchone()[0] for x in xs])
    ppf = np.array([c.execute("SELECT norm_ppf(?)", [float(p)]).fetchone()[0] for p in ps])
    assert np.abs(cdf - norm.cdf(xs)).max() < 2e-7
    ref = norm.ppf(ps)
    assert np.max(np.abs(ppf - ref) / np.maximum(np.abs(ref), 1e-3)) < 2e-9


@pytest.mark.parametrize("p", [0, 0.025, 0.1, 0.5, 0.9, 0.975, 1])
def test_qsorted_matches_numpy(p):
    c = connect()
    v = sorted(np.random.default_rng(1).normal(size=101).tolist())
    assert c.execute("SELECT qsorted(?::DOUBLE[], ?)", [v, p]).fetchone()[0] == pytest.approx(np.quantile(v, p))


def test_fsum_is_order_independent():
    c = connect()
    a = c.execute("SELECT fsum(v) FROM (SELECT 1e16 v UNION ALL SELECT 1.0 UNION ALL SELECT -1e16)").fetchone()[0]
    b = c.execute("SELECT fsum(v) FROM (SELECT -1e16 v UNION ALL SELECT 1e16 UNION ALL SELECT 1.0)").fetchone()[0]
    assert a == b
