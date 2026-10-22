"""Check that your run reproduced the published results.

    python start-here/verify.py snapshot   # copy the published results to start-here/_reference/
    python start-here/verify.py check      # compare your results with that copy

run_all.py takes the snapshot automatically before its first stage and runs
the check as its last stage, so you normally never call this yourself.

What is compared:
  1. Every output file listed in a manifest.json (populations, estimates,
     metrics, truth, the report): its SHA-256 fingerprint must be identical.
     The pipeline is deterministic, so on the same software versions every
     file should match exactly.
  2. The tables the findings are reported from (shared/results/report/
     by_scenario.csv, the README tables; manuscripts/generated/results_long.csv
     and tables.md, the manuscript tables; part-d-ipm/pre-ira-reference.md).
     If a fingerprint differs, for example because a different operating
     system rounds the last digit of a floating-point number differently,
     every number in these tables is compared and must agree to 9
     significant digits. That is "reproduced to rounding": the published
     findings are unchanged.
"""
import csv
import hashlib
import json
import math
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "start-here" / "_reference"
TABLES = ["shared/results/report/by_scenario.csv", "manuscripts/generated/results_long.csv",
          "manuscripts/generated/tables.md", "part-d-ipm/pre-ira-reference.md"]
SKIP_DIRS = {"start-here", ".git", "robustness", "qa"}   # robustness is the optional stage 9; qa holds reviewers' copies
NUM = re.compile(r"-?\d+(?:,\d{3})*(?:\.\d+)?(?:[eE][-+]?\d+)?")


def manifests(base):
    out = []
    for p in sorted(base.rglob("manifest.json")):
        rel = p.relative_to(base)
        if rel.parts[0] in SKIP_DIRS:
            continue
        files = json.loads(p.read_text()).get("files")
        if files:   # scenario-level manifests list files; program-level ones list scenarios
            out.append((rel, files))
    return out


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def snapshot():
    if REF.exists():
        shutil.rmtree(REF)
    REF.mkdir(parents=True)
    expected = {}
    for rel, files in manifests(ROOT):
        for name, info in files.items():
            expected[str(rel.parent / name)] = info["sha256"]
    (REF / "expected_sha256.json").write_text(json.dumps(expected, indent=1, sort_keys=True))
    for t in TABLES:
        src = ROOT / t
        if src.exists():
            (REF / t).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, REF / t)
    print(f"Saved the published results ({len(expected)} files) to start-here/_reference/.")


def numbers(path):
    text = path.read_text()
    if path.suffix == ".csv":
        cells = [c for row in csv.reader(text.splitlines()) for c in row]
    else:
        cells = [text]
    vals = []
    for c in cells:
        vals += [float(m.replace(",", "")) for m in NUM.findall(c)]
    return vals


def same_numbers(a, b):
    na, nb = numbers(a), numbers(b)
    if len(na) != len(nb):
        return False, f"{len(na)} numbers published, {len(nb)} in your run"
    worst = 0.0
    for x, y in zip(na, nb):
        if not math.isclose(x, y, rel_tol=1e-9, abs_tol=1e-12):
            return False, f"published {x!r}, your run {y!r}"
        worst = max(worst, abs(x - y))
    return True, f"largest difference {worst:.1e}"


def check():
    exp_file = REF / "expected_sha256.json"
    if not exp_file.exists():
        sys.exit("No snapshot found. Run  python start-here/verify.py snapshot  before running the pipeline.")
    expected = json.loads(exp_file.read_text())
    same, differ, missing = 0, [], []
    for rel, digest in sorted(expected.items()):
        p = ROOT / rel
        if not p.exists():
            missing.append(rel)
        elif sha256(p) == digest:
            same += 1
        else:
            differ.append(rel)

    print("\nRESULT CHECK")
    print(f"  Output files identical to the published files: {same} of {len(expected)}")
    tables_ok = True
    for t in TABLES:
        mine, ref = ROOT / t, REF / t
        if not ref.exists():
            continue
        if not mine.exists():
            print(f"  MISSING  {t}")
            tables_ok = False
        elif sha256(mine) == sha256(ref):
            print(f"  identical            {t}")
        else:
            ok, why = same_numbers(ref, mine)
            print(f"  {'same to rounding' if ok else 'DIFFERENT':<20} {t} ({why})")
            tables_ok &= ok
    if missing:
        print(f"  Not produced by your run ({len(missing)}): " + ", ".join(missing[:5])
              + (" ..." if len(missing) > 5 else ""))
    if differ:
        print(f"  Files whose fingerprint differs ({len(differ)}): " + ", ".join(differ[:5])
              + (" ..." if len(differ) > 5 else ""))

    if not differ and not missing and tables_ok:
        print("\nREPRODUCED EXACTLY: every output file is byte-for-byte identical to the published results.")
    elif tables_ok and not missing:
        print("\nREPRODUCED: every number in the results tables matches the published results.\n"
              "Some files differ in their last stored digits (usually a different operating system or\n"
              "library version), which does not change any reported finding.")
    else:
        print("\nNOT REPRODUCED: see the lines marked DIFFERENT or MISSING above, and the\n"
              "troubleshooting section of start-here/README.md.")
        sys.exit(1)


if __name__ == "__main__":
    {"snapshot": snapshot, "check": check}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: sys.exit(__doc__))()
