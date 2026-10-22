"""Same config + seed -> byte-identical files at any thread count."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ipsim.engine import ROOT, Engine  # noqa: E402


@pytest.mark.parametrize("cfg,scenario", [
    ("eipm/errors/config.yaml", "base"),
    ("part-c-ipm/errors/config.yaml", "base"),
    ("part-d-ipm/errors/config.yaml", "base"),
    ("cert/errors/config.yaml", "national"),
    ("perm/errors/config.yaml", "state_elig_grid"),
])
def test_errors_outputs_identical(tmp_path, cfg, scenario):
    hashes = []
    for threads in (1, 4):
        out = tmp_path / f"t{threads}"
        Engine(ROOT / cfg, out, threads).run([scenario])
        man = json.loads((out / scenario / "manifest.json").read_text())
        hashes.append({k: v["sha256"] for k, v in man["files"].items()})
    assert hashes[0] == hashes[1]


@pytest.mark.parametrize("cfg,pop", [
    ("eipm/estimation/config.yaml", "eipm/errors/output/base/population.parquet"),
    ("part-c-ipm/estimation/config.yaml", "part-c-ipm/errors/output/base/population.parquet"),
    ("cert/estimation/config.yaml", "cert/errors/output/national/population.parquet"),
])
def test_estimation_outputs_identical(tmp_path, cfg, pop):
    """Needs the program's errors/ output (committed or built)."""
    cfg = ROOT / cfg
    if not (ROOT / pop).exists():
        pytest.skip(f"build {pop} first")
    hashes = []
    for threads in (1, 4):
        out = tmp_path / f"t{threads}"
        e = Engine(cfg, out, threads)
        e.config["defaults"].update(reps=10, sim_reps=3, sim_iterations=100)
        e.run()
        mans = sorted(out.glob("*/manifest.json"))
        hashes.append({m.parent.name: {k: v["sha256"] for k, v in json.loads(m.read_text())["files"].items()}
                       for m in mans})
    assert hashes[0] == hashes[1]
