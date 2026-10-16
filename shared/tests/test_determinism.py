"""Same config + seed -> byte-identical files at any thread count."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ipsim.engine import ROOT, Engine  # noqa: E402


@pytest.mark.parametrize("cfg,scenario", [
    ("perm-cert/errors/cert.yaml", "left_all_or_nothing_p0.70"),
    ("eipm/errors/config.yaml", "base"),
    ("part-c-ipm/errors/config.yaml", "base"),
])
def test_errors_outputs_identical(tmp_path, cfg, scenario):
    hashes = []
    for threads in (1, 4):
        out = tmp_path / f"t{threads}"
        Engine(ROOT / cfg, out, threads).run([scenario])
        man = json.loads((out / scenario / "manifest.json").read_text())
        hashes.append({k: v["sha256"] for k, v in man["files"].items()})
    assert hashes[0] == hashes[1]


def test_estimation_outputs_identical(tmp_path):
    """Needs perm-cert/errors/output/cert (run perm-cert/errors/cert.yaml first)."""
    cfg = ROOT / "perm-cert/estimation/cert.yaml"
    if not (ROOT / "perm-cert/errors/output/cert/left_all_or_nothing_p0.70").exists():
        pytest.skip("build perm-cert/errors/cert.yaml first")
    hashes = []
    for threads in (1, 4):
        out = tmp_path / f"t{threads}"
        e = Engine(cfg, out, threads)
        e.config["defaults"].update(reps=40, sim_reps=3, sim_iterations=100)
        e.run(["left_p0.70"])
        man = json.loads((out / "left_p0.70" / "manifest.json").read_text())
        hashes.append({k: v["sha256"] for k, v in man["files"].items()})
    assert hashes[0] == hashes[1]
