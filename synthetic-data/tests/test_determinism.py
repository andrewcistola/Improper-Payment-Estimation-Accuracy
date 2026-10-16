"""Same config + seed -> byte-identical files, regardless of thread count."""
import json
from pathlib import Path

import pytest

from ipsim import Engine

CFG = Path(__file__).resolve().parents[1] / "config"


@pytest.mark.parametrize("cfg,scen", [("ffs_stress.yaml", "left_all_or_nothing_p0.70"),
                                      ("eipm.yaml", "base"),
                                      ("partc.yaml", "base")])
def test_identical_hashes(tmp_path, cfg, scen):
    hashes = []
    for threads in (1, 4):
        out = tmp_path / f"t{threads}"
        Engine(CFG / cfg, out, threads).run([scen])
        prog = Engine(CFG / cfg).program
        man = json.loads((out / prog / scen / "manifest.json").read_text())
        hashes.append({k: v["sha256"] for k, v in man["files"].items()})
    assert hashes[0] == hashes[1]
