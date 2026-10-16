"""Samplers take exactly the allocated number of units per stratum."""
from pathlib import Path

import duckdb
import pytest

SQL = Path(__file__).resolve().parents[1] / "src" / "sql"


@pytest.mark.parametrize("selection", ["srs", "systematic"])
def test_exact_sample_sizes(selection):
    c = duckdb.connect()
    c.execute((SQL / "lib" / "rng.sql").read_text())
    c.execute("CREATE TABLE pop AS SELECT i AS unit_id, 'S' || (i % 3) AS stratum, "
              "(i % 3)::DOUBLE AS y, (i * 7 % 101 + 1)::DOUBLE AS x FROM range(1, 1001) t(i)")
    c.execute("CREATE TABLE alloc AS SELECT * FROM (VALUES ('S0', 17), ('S1', 40), ('S2', 333)) t(stratum, n_h)")
    for k, v in dict(seed=3, reps=50, selection=selection).items():
        c.execute(f"SET VARIABLE {k} = ?", [v])
    c.execute((SQL / "estimate" / "sample.sql").read_text())
    got = dict(c.execute("SELECT stratum, min(n) FROM (SELECT rep, stratum, count(*) n FROM sample "
                         "GROUP BY rep, stratum) GROUP BY stratum").fetchall())
    mx = dict(c.execute("SELECT stratum, max(n) FROM (SELECT rep, stratum, count(*) n FROM sample "
                        "GROUP BY rep, stratum) GROUP BY stratum").fetchall())
    assert got == mx == {"S0": 17, "S1": 40, "S2": 333}
    # every unit selected at most once per replicate
    assert c.execute("SELECT max(c) FROM (SELECT rep, unit_id, count(*) c FROM sample GROUP BY 1, 2)").fetchone()[0] == 1
