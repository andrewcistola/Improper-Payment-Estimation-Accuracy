"""Reproduce every result in the study, in order, with one command.

Run from the repository's top folder (the one that contains README.md):

    python start-here/run_all.py            # the full replication (several hours)
    python start-here/run_all.py --quick    # a 10-20 minute trial run that checks your setup
    python start-here/run_all.py --list     # show the stages without running anything
    python start-here/run_all.py --from 4   # start again at stage 4 (after an interruption)
    python start-here/run_all.py --only 7   # run one stage

The stages:
  1. Build the synthetic populations (errors/) for all five programs, plus the
     pre-IRA Part D population.
  2. Estimate with every method, bootstrap simulation with parametric rates
     (estimation/results/, the reported results).
  3. Estimate again with fixed-rate bootstrap simulation, the same audits
     (estimation/results_fixed/, the comparison in the manuscript).
  4. Part D under the pre-IRA benefit (the robustness reference).
  5. Join every estimate to the truth (shared/results/report/by_scenario.csv,
     which the README tables come from).
  6. Build the manuscript's tables and figures (manuscripts/generated/).
  7. Run the automated tests.
  8. Compare your results with the published ones (start-here/verify.py).

Before stage 1, the published results are copied to start-here/_reference/
so that stage 8 can compare them with the files your run produces. Each
stage's run time is written to start-here/run_log.txt.

The full run overwrites the committed result files with identical copies. The
quick run writes to start-here/_quick/ instead and leaves the published
results untouched.
"""
import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "start-here"
LOG = HERE / "run_log.txt"
PY = sys.executable

POPULATIONS = ["part-c-ipm/errors/config.yaml", "part-d-ipm/errors/config.yaml", "eipm/errors/config.yaml",
               "perm-cert/errors/perm.yaml", "perm-cert/errors/cert.yaml", "part-d-ipm/errors/pre_ira.yaml"]


def ipsim(*args):
    return [PY, "-m", "ipsim.engine", *args]


def full_stages():
    fixed = ["--set", "sim_rates=fixed"]
    return [
        ("Build the synthetic populations", [ipsim(c) for c in POPULATIONS]),
        ("Estimate: every method, parametric-rate bootstrap (reported results)", [
            ipsim("part-c-ipm/estimation/config.yaml"),
            ipsim("part-d-ipm/estimation/config.yaml"),
            ipsim("eipm/estimation/config.yaml"),
            ipsim("perm-cert/estimation/perm.yaml"),
            ipsim("perm-cert/estimation/perm_national.yaml"),
            ipsim("perm-cert/estimation/cert.yaml"),
        ]),
        ("Estimate: fixed-rate bootstrap (comparison), same audits", [
            ipsim("part-c-ipm/estimation/config.yaml", "--out", "part-c-ipm/estimation/results_fixed", *fixed),
            ipsim("part-d-ipm/estimation/config.yaml", "--out", "part-d-ipm/estimation/results_fixed", *fixed),
            ipsim("eipm/estimation/config.yaml", "--out", "eipm/estimation/results_fixed", *fixed),
            ipsim("perm-cert/estimation/perm.yaml", "--out", "perm-cert/estimation/results_fixed/perm", *fixed),
            ipsim("perm-cert/estimation/perm_national.yaml", "--out", "perm-cert/estimation/results_fixed/perm",
                  "--set", "perm_results_dir=perm-cert/estimation/results_fixed/perm"),
            ipsim("perm-cert/estimation/cert.yaml", "--out", "perm-cert/estimation/results_fixed/cert", *fixed),
        ]),
        ("Part D under the pre-IRA benefit (robustness reference)", [
            ipsim("part-d-ipm/estimation/pre_ira.yaml"),
            ipsim("part-d-ipm/estimation/pre_ira.yaml", "--out", "part-d-ipm/estimation/results_pre_ira_fixed", *fixed),
            [PY, "part-d-ipm/estimation/pre_ira_reference.py"],
        ]),
        ("Join every estimate to the truth (README tables)", [
            ipsim("shared/summary.yaml"),
            ipsim("shared/report.yaml"),
        ]),
        ("Build the manuscript's tables and figures", [
            [PY, "manuscripts/scripts/build_tables.py"],
            [PY, "manuscripts/scripts/assemble.py"],
        ]),
        ("Run the automated tests", [[PY, "-m", "pytest", "-q", "shared/tests"]]),
        ("Compare your results with the published results", [[PY, "start-here/verify.py", "check"]]),
    ]


def quick_stages():
    """A small version of stages 1-2: every program, 3 audit years, 100 iterations."""
    q = "start-here/_quick"
    small = ["--set", "reps=3", "sim_reps=3", "sim_iterations=100"]
    return [
        ("Build the synthetic populations", [ipsim(c) for c in POPULATIONS[:5]]),
        ("Trial estimation: 3 audit years, 100 iterations (written to start-here/_quick/)", [
            ipsim("part-c-ipm/estimation/config.yaml", "--out", f"{q}/part-c", *small),
            ipsim("part-d-ipm/estimation/config.yaml", "--out", f"{q}/part-d", *small),
            ipsim("eipm/estimation/config.yaml", "--out", f"{q}/eipm", *small),
            ipsim("perm-cert/estimation/perm.yaml", "--out", f"{q}/perm", *small),
            ipsim("perm-cert/estimation/perm_national.yaml", "--out", f"{q}/perm",
                  "--set", f"perm_results_dir={q}/perm"),
            ipsim("perm-cert/estimation/cert.yaml", "--out", f"{q}/cert", *small),
        ]),
    ]


def fmt(seconds):
    m, s = divmod(int(round(seconds)), 60)
    h, m = divmod(m, 60)
    return f"{h}h {m:02d}m {s:02d}s" if h else f"{m}m {s:02d}s"


def log(line):
    print(line, flush=True)
    with LOG.open("a") as f:
        f.write(line + "\n")


def main():
    ap = argparse.ArgumentParser(description="Reproduce every result in the study.")
    ap.add_argument("--quick", action="store_true", help="short trial run that checks your setup")
    ap.add_argument("--list", action="store_true", help="list the stages and their commands, then stop")
    ap.add_argument("--from", dest="start", type=int, default=1, help="first stage to run")
    ap.add_argument("--only", type=int, help="run this one stage")
    a = ap.parse_args()

    stages = quick_stages() if a.quick else full_stages()
    first, last = (a.only, a.only) if a.only else (a.start, len(stages))
    if not 1 <= first <= last <= len(stages):
        sys.exit(f"Stage numbers run from 1 to {len(stages)}.")

    if a.list:
        for i, (title, cmds) in enumerate(stages, 1):
            print(f"\nStage {i}. {title}")
            for c in cmds:
                print("   ", " ".join(Path(c[0]).name if j == 0 else x for j, x in enumerate(c)))
        return

    if not (ROOT / "shared" / "ipsim" / "engine.py").exists():
        sys.exit("Run this from the repository's top folder (the one that contains README.md).")
    if not a.quick and first == 1 and not (HERE / "_reference").exists():
        subprocess.run([PY, "start-here/verify.py", "snapshot"], cwd=ROOT, check=True)
    if a.quick:
        shutil.rmtree(ROOT / "start-here" / "_quick", ignore_errors=True)

    log(f"\n=== {'Quick trial run' if a.quick else 'Full replication'} started {time.strftime('%Y-%m-%d %H:%M')} "
        f"(Python {sys.version.split()[0]}) ===")
    t_all = time.time()
    for i in range(first, last + 1):
        title, cmds = stages[i - 1]
        log(f"\nStage {i} of {len(stages)}: {title}")
        t0 = time.time()
        for c in cmds:
            shown = " ".join(c[3:] if c[1:3] == ["-m", "ipsim.engine"] else c[1:])
            log(f"  running: {shown}")
            t1 = time.time()
            r = subprocess.run(c, cwd=ROOT)
            if r.returncode != 0:
                log(f"  FAILED after {fmt(time.time() - t1)}: {shown}")
                log(f"  Fix the problem above, then continue with:  python start-here/run_all.py "
                    f"{'--quick ' if a.quick else ''}--from {i}")
                sys.exit(1)
            log(f"    done in {fmt(time.time() - t1)}")
        log(f"Stage {i} finished in {fmt(time.time() - t0)}")
    log(f"\nAll stages finished in {fmt(time.time() - t_all)}.")
    if a.quick:
        log("Your setup works. Start the full replication with:  python start-here/run_all.py")


if __name__ == "__main__":
    main()
