"""Copy a QA re-run's logs and results into one dated folder under qa/reruns/.

Run from the repository's top folder after the full replication
(start-here/run_all.py) has finished:

    .venv/bin/python qa/collect_rerun.py --reviewer "Jane Doe" --initials JD
    (Windows: .venv\\Scripts\\python qa\\collect_rerun.py --reviewer "Jane Doe" --initials JD)

It creates qa/reruns/<YYYY-MM-DD>_<INITIALS>/ (today's date; --date to set
another) containing:

  RERUN_SUMMARY.md     who, when, which computer and software, which project
                       version, how long each run took, and the result check
  logs/                every date-stamped run folder from start-here/logs/
                       (environment.txt, run_log.txt, one log per command)
  results/             the re-run's outputs, in the same folders as in the
                       project (for example results/part-c-ipm/estimation/results/)
  verification/
    verify_check.txt   the output of start-here/verify.py check
    file_inventory.csv every collected file with its size and SHA-256
                       fingerprint, and whether it matches the published file
  review/              an empty folder for the completed checklist, the signed
                       sign-off form, and any notes or screenshots

Large population files (*.parquet under errors/output) are not copied; their
fingerprints are recorded in the copied manifest.json files and checked in
file_inventory.csv. The folder holds synthetic data only (about 15 MB).
"""
import argparse
import csv
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "start-here" / "_reference" / "expected_sha256.json"

# Re-run outputs to collect, as (folder or file, patterns); paths as in the project
RESULTS = [
    ("part-c-ipm/errors/output", ["**/*.json", "**/*.yaml"]),
    ("part-d-ipm/errors/output", ["**/*.json", "**/*.yaml"]),
    ("part-d-ipm/errors/output_pre_ira", ["**/*.json", "**/*.yaml"]),
    ("eipm/errors/output", ["**/*.json", "**/*.yaml"]),
    ("perm-cert/errors/output", ["**/*.json", "**/*.yaml"]),
    ("part-c-ipm/estimation", ["results*/**/*"]),
    ("part-d-ipm/estimation", ["results*/**/*"]),
    ("eipm/estimation", ["results*/**/*"]),
    ("perm-cert/estimation", ["results*/**/*"]),
    ("shared/results", ["**/*"]),
    ("manuscripts/generated", ["*"]),
    ("manuscripts", ["manuscript.md"]),
    ("part-d-ipm", ["pre-ira-reference.md"]),
]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_results(dest):
    copied = []
    for base, patterns in RESULTS:
        for pat in patterns:
            for p in sorted((ROOT / base).glob(pat)):
                if p.is_file():
                    rel = p.relative_to(ROOT)
                    (dest / rel).parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(p, dest / rel)
                    copied.append(rel)
    return sorted(set(copied))


def run_dirs():
    logs = ROOT / "start-here" / "logs"
    return sorted(d for d in logs.glob("run_*") if d.is_dir()) if logs.exists() else []


def read_run(d):
    """Start, end, type and outcome of one run folder, from its run_log.txt."""
    text = (d / "run_log.txt").read_text(encoding="utf-8") if (d / "run_log.txt").exists() else ""
    stamps = re.findall(r"^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)\]", text, re.M)
    if "All stages finished" in text:
        outcome = "finished"
    elif "FAILED" in text:
        outcome = "FAILED (see the command logs)"
    else:
        outcome = "did not finish (interrupted)"
    env = (d / "environment.txt").read_text(encoding="utf-8") if (d / "environment.txt").exists() else ""
    kind = re.search(r"Run type:\s+(.+)", env)
    stages = [(m.group(1), m.group(2)) for m in re.finditer(r"Stage (\d+) finished in (.+)", text)]
    return {"name": d.name, "type": kind.group(1).strip() if kind else "unknown",
            "start": stamps[0] if stamps else "unknown", "end": stamps[-1] if stamps else "unknown",
            "outcome": outcome, "stages": stages}


def main():
    ap = argparse.ArgumentParser(description="Collect a QA re-run into qa/reruns/<date>_<initials>/.")
    ap.add_argument("--reviewer", required=True, help='your full name, in quotes, e.g. "Jane Doe"')
    ap.add_argument("--initials", required=True, help="your initials, e.g. JD (used in the folder name)")
    ap.add_argument("--date", default=time.strftime("%Y-%m-%d"), help="folder date, YYYY-MM-DD (default: today)")
    a = ap.parse_args()

    initials = re.sub(r"[^A-Za-z0-9]", "", a.initials).upper()
    if not initials or not re.fullmatch(r"\d{4}-\d\d-\d\d", a.date):
        sys.exit("Give initials (letters) and a date in the form YYYY-MM-DD.")
    runs = run_dirs()
    if not any("full replication" in read_run(d)["type"] for d in runs):
        sys.exit("No full replication found in start-here/logs/. Run  python start-here/run_all.py  first.")

    dest = ROOT / "qa" / "reruns" / f"{a.date}_{initials}"
    if dest.exists():
        sys.exit(f"{dest.relative_to(ROOT)} already exists. Rename or remove it, or use --date.")
    print(f"Collecting the re-run into {dest.relative_to(ROOT)}/ ...")
    for sub in ("logs", "results", "verification", "review"):
        (dest / sub).mkdir(parents=True)

    for d in runs:
        shutil.copytree(d, dest / "logs" / d.name)
    if (ROOT / "start-here" / "run_log.txt").exists():
        shutil.copy2(ROOT / "start-here" / "run_log.txt", dest / "logs" / "run_log_all_runs.txt")
    copied = collect_results(dest / "results")

    # the result check, saved as text
    r = subprocess.run([sys.executable, "start-here/verify.py", "check"], cwd=ROOT, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    check = (f"Run {time.strftime('%Y-%m-%d %H:%M:%S %Z')}: python start-here/verify.py check\n"
             + r.stdout + r.stderr)
    (dest / "verification" / "verify_check.txt").write_text(check, encoding="utf-8")
    verdict = next((ln for ln in check.splitlines() if ln.startswith(("REPRODUCED", "NOT REPRODUCED"))),
                   "No result: the published results were not snapshotted (see verify_check.txt)")

    # inventory: every collected file, and every manifest-listed file, against the published fingerprints
    expected = json.loads(REF.read_text()) if REF.exists() else {}
    with open(dest / "verification" / "file_inventory.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["file", "collected", "bytes", "sha256_rerun", "sha256_published", "matches_published"])
        for rel in sorted(set(map(str, (p.as_posix() for p in copied))) | set(expected)):
            src = ROOT / rel
            have = src.exists()
            digest = sha256(src) if have else ""
            pub = expected.get(rel, "")
            match = ("" if not pub else "yes" if digest == pub else "NO")
            w.writerow([rel, "yes" if (dest / "results" / rel).exists() else "no (fingerprint only)",
                        src.stat().st_size if have else "", digest, pub, match])

    env_files = [d / "environment.txt" for d in runs if (d / "environment.txt").exists()]
    env = env_files[-1].read_text(encoding="utf-8") if env_files else "(no environment.txt found)"
    lines = [f"# QA re-run: {a.date}, {a.reviewer} ({initials})", "",
             f"Collected {time.strftime('%Y-%m-%d %H:%M:%S %Z')} by `qa/collect_rerun.py`.", "",
             f"**Result check:** {verdict}", "",
             "## Runs", "",
             "| Run folder (logs/) | Type | Started | Last entry | Outcome |", "|---|---|---|---|---|"]
    for d in runs:
        x = read_run(d)
        lines.append(f"| `{x['name']}` | {x['type']} | {x['start']} | {x['end']} | {x['outcome']} |")
    lines += ["", "## Stage run times (full replication runs)", "", "| Run folder | Stage | Time |", "|---|---|---|"]
    for d in runs:
        x = read_run(d)
        if "full replication" in x["type"]:
            lines += [f"| `{x['name']}` | {s} | {t} |" for s, t in x["stages"]]
    lines += ["", "## Computer and software (latest run)", "", "```", env.rstrip(), "```", "",
              "## Contents", "",
              "- `logs/`: the date-stamped run folders from `start-here/logs/` (environment, run log, one log per command)",
              "- `results/`: the re-run's output files, in the same folders as in the project",
              "- `verification/verify_check.txt`: the result check",
              "- `verification/file_inventory.csv`: every file with its fingerprint and whether it matches the published file",
              "- `review/`: the completed checklist, the signed sign-off form, and any notes or screenshots", ""]
    (dest / "RERUN_SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")
    (dest / "review" / "PUT_COMPLETED_CHECKLIST_AND_SIGNOFF_HERE.txt").write_text(
        "Save the completed QA checklist (.xlsx) and the signed sign-off form (.docx or .pdf) in this folder,\n"
        "along with any notes or screenshots that support your review.\n", encoding="utf-8")

    print(f"  {len(runs)} run folder(s), {len(copied)} result files, check: {verdict}")
    print(f"Done. Open {(dest / 'RERUN_SUMMARY.md').relative_to(ROOT)} to see the summary.")


if __name__ == "__main__":
    main()
