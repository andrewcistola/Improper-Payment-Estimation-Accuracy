"""shared/sql/sample.sql takes exactly the allocated number of units."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ipsim.engine import ROOT, connect  # noqa: E402


@pytest.mark.parametrize("selection", ["srs", "systematic"])
def test_exact_sample_sizes(selection):
    c = connect()
    c.execute("CREATE TABLE pop AS SELECT d.domain, 'S' || (i % 3) AS stratum, i AS unit_id, "
              "(i % 3)::DECIMAL(18,6) AS y, (i * 7 % 101 + 1)::DECIMAL(18,6) AS x "
              "FROM range(1, 1001) t(i), (VALUES ('a'), ('b')) d(domain)")
    c.execute("CREATE TABLE alloc AS SELECT d.domain, t.* FROM (VALUES ('S0', 17), ('S1', 40), ('S2', 333)) "
              "t(stratum, n_h), (VALUES ('a'), ('b')) d(domain)")
    for k, v in dict(seed=3, reps=50, selection=selection).items():
        c.execute(f"SET VARIABLE {k} = ?", [v])
    c.execute((ROOT / "shared" / "sql" / "sample.sql").read_text())
    sizes = c.execute("SELECT stratum, min(n), max(n) FROM (SELECT rep, domain, stratum, count(*) n "
                      "FROM sample GROUP BY ALL) GROUP BY stratum ORDER BY stratum").fetchall()
    assert sizes == [("S0", 17, 17), ("S1", 40, 40), ("S2", 333, 333)]
    # no unit twice in one sample
    assert c.execute("SELECT max(c) FROM (SELECT rep, domain, unit_id, count(*) c FROM sample GROUP BY ALL)").fetchone()[0] == 1
    # domains with the same strata get the same sample (PERM components)
    assert c.execute("SELECT count(*) FROM (SELECT rep, unit_id FROM sample WHERE domain = 'a' "
                     "EXCEPT SELECT rep, unit_id FROM sample WHERE domain = 'b')").fetchone()[0] == 0
    # weights reproduce the stratum sizes
    assert c.execute("SELECT min(s), max(s) FROM (SELECT rep, domain, sum(w) s FROM sample GROUP BY ALL)").fetchone() \
        == pytest.approx((1000, 1000))
