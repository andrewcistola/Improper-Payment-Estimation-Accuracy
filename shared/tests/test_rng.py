"""Guards on the hash-based RNG (shared/sql/lib/00_rng.sql)."""
from pathlib import Path

import duckdb

SQL = Path(__file__).resolve().parents[1] / "sql"


def con():
    c = duckdb.connect()
    c.execute((SQL / "lib" / "00_rng.sql").read_text())
    return c


def test_uniform_moments():
    m, v = con().execute(
        "SELECT avg(u), var_samp(u) FROM (SELECT u01(42, 'x', i) u FROM range(200000) t(i))").fetchone()
    assert abs(m - 0.5) < 0.003 and abs(v - 1 / 12) < 0.002


def test_replicates_are_independent():
    # Two SRS of 30 from 249 units should share ~30*30/249 = 3.6 units on
    # average. DuckDB's multi-argument hash() gave ~24; rng.sql must not.
    overlap = con().execute("""
        WITH d AS (SELECT r, unnest(min_by(i, u01b(7, 'srs', r, i), 30)) i
                   FROM range(200) t(r), range(1, 250) u(i) GROUP BY r)
        SELECT avg(cnt) FROM (SELECT a.r, b.r, count(*) cnt FROM d a JOIN d b
                              ON a.i = b.i AND a.r < b.r GROUP BY 1, 2)""").fetchone()[0]
    assert 3.0 < overlap < 4.3


def test_normal_moments():
    m, s = con().execute(
        "SELECT avg(z), stddev_samp(z) FROM (SELECT rnorm(1, 'z', i) z FROM range(200000) t(i))").fetchone()
    assert abs(m) < 0.01 and abs(s - 1) < 0.01


def test_fast_stream_independent_and_uniform():
    c = con()
    m, v = c.execute("SELECT avg(u), var_samp(u) FROM (SELECT u01f(rbase(1, 'b', 2, 0), i) u "
                     "FROM range(200000) t(i))").fetchone()
    assert abs(m - 0.5) < 0.003 and abs(v - 1 / 12) < 0.002
    overlap = c.execute("""
        WITH d AS (SELECT r, unnest(min_by(i, u01f(rbase(7, 'srs', r, 0), i), 30)) i
                   FROM range(200) t(r), range(1, 250) u(i) GROUP BY r)
        SELECT avg(cnt) FROM (SELECT a.r, b.r, count(*) cnt FROM d a JOIN d b
                              ON a.i = b.i AND a.r < b.r GROUP BY 1, 2)""").fetchone()[0]
    assert 3.0 < overlap < 4.3
