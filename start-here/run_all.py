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
so that stage 8 can compare them with the files your run produces.

Logs. Every run writes a date-stamped folder start-here/logs/run_<date>_<time>/
containing:
  environment.txt   when, on what computer, with what operating system, Python
                    and package versions, and from which version of the project
  run_log.txt       each stage and command with its start time and run time
  stage<N>_<k>_<name>.log   the complete output of each command, every line
                    prefixed with the date and time it was printed
A one-line-per-step summary of all runs is also appended to start-here/run_log.txt.

The full run overwrites the committed result files with the files it
computes. The quick run rebuilds the populations the same way and writes its
trial estimates to start-here/_quick/, leaving the published estimates
untouched.
"""
import argparse
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "start-here"
LOG = HERE / "run_log.txt"
PY = sys.executable

POPULATIONS = ["part-c-ipm/errors/config.yaml", "part-d-ipm/errors/config.yaml", "eipm/errors/config.yaml",
               "perm/errors/config.yaml", "cert/errors/config.yaml", "part-d-ipm/errors/pre_ira.yaml"]


def ipsim(*args):
    return [PY, "-m", "ipsim", *args]


def full_stages():
    fixed = ["--set", "sim_rates=fixed"]
    return [
        ("Build the synthetic populations", [ipsim(c) for c in POPULATIONS]),
        ("Estimate: every method, parametric-rate bootstrap (reported results)", [
            ipsim("part-c-ipm/estimation/config.yaml"),
            ipsim("part-d-ipm/estimation/config.yaml"),
            ipsim("eipm/estimation/config.yaml"),
            ipsim("perm/estimation/config.yaml"),
            ipsim("perm/estimation/national.yaml"),
            ipsim("cert/estimation/config.yaml"),
        ]),
        ("Estimate: fixed-rate bootstrap (comparison), same audits", [
            ipsim("part-c-ipm/estimation/config.yaml", "--out", "part-c-ipm/estimation/results_fixed", *fixed),
            ipsim("part-d-ipm/estimation/config.yaml", "--out", "part-d-ipm/estimation/results_fixed", *fixed),
            ipsim("eipm/estimation/config.yaml", "--out", "eipm/estimation/results_fixed", *fixed),
            ipsim("perm/estimation/config.yaml", "--out", "perm/estimation/results_fixed", *fixed),
            ipsim("perm/estimation/national.yaml", "--out", "perm/estimation/results_fixed",
                  "--set", "perm_results_dir=perm/estimation/results_fixed"),
            ipsim("cert/estimation/config.yaml", "--out", "cert/estimation/results_fixed", *fixed),
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
        ("Robustness and calibration runs for Appendix D (optional: --with-robustness; 2-3 hours)",
         [[PY, "robustness/run.py"]]),
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
            ipsim("perm/estimation/config.yaml", "--out", f"{q}/perm", *small),
            ipsim("perm/estimation/national.yaml", "--out", f"{q}/perm",
                  "--set", f"perm_results_dir={q}/perm"),
            ipsim("cert/estimation/config.yaml", "--out", f"{q}/cert", *small),
        ]),
    ]


def fmt(seconds):
    m, s = divmod(int(round(seconds)), 60)
    h, m = divmod(m, 60)
    return f"{h}h {m:02d}m {s:02d}s" if h else f"{m}m {s:02d}s"


RUN_DIR = None   # start-here/logs/run_<date>_<time>/, set in main()
PACKAGES = ["duckdb", "pyarrow", "numpy", "numba", "pyyaml", "scipy", "pandas", "matplotlib", "pytest"]


def stamp():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def log(line):
    print(line, flush=True)
    for path in (LOG, RUN_DIR / "run_log.txt"):
        with path.open("a", encoding="utf-8") as f:
            if line.startswith("\n"):
                f.write("\n")
            f.write(f"[{stamp()}] {line.lstrip(chr(10))}\n")


def memory_gb():
    try:
        if sys.platform.startswith("linux"):
            kb = int(re.search(r"MemTotal:\s+(\d+)", Path("/proc/meminfo").read_text()).group(1))
            return f"{kb / 1024 ** 2:.1f} GB"
        if sys.platform == "darwin":
            b = int(subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True).stdout)
            return f"{b / 1024 ** 3:.1f} GB"
        if sys.platform == "win32":
            import ctypes

            class MS(ctypes.Structure):
                _fields_ = [("l", ctypes.c_ulong), ("m", ctypes.c_ulong), ("t", ctypes.c_ulonglong),
                            ("a", ctypes.c_ulonglong), ("tp", ctypes.c_ulonglong), ("ap", ctypes.c_ulonglong),
                            ("tv", ctypes.c_ulonglong), ("av", ctypes.c_ulonglong), ("e", ctypes.c_ulonglong)]
            ms = MS()
            ms.l = ctypes.sizeof(MS)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(ms))
            return f"{ms.t / 1024 ** 3:.1f} GB"
    except Exception:
        pass
    return "unknown"


def project_version():
    try:
        r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True)
        if r.returncode == 0:
            dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT,
                                   capture_output=True, text=True).stdout.strip()
            return r.stdout.strip() + (" (with local changes)" if dirty else "")
    except OSError:
        pass
    return "not a Git checkout (downloaded as a ZIP file)"


def write_environment(mode):
    lines = [f"Run started:        {time.strftime('%Y-%m-%d %H:%M:%S %Z (UTC%z)')}",
             f"Run type:           {mode}",
             f"Command:            {' '.join([Path(sys.executable).name] + sys.argv)}",
             f"Project folder:     {ROOT}",
             f"Project version:    {project_version()}",
             f"Computer name:      {platform.node()}",
             f"Operating system:   {platform.platform()}",
             f"Processor:          {platform.machine()} {platform.processor()}".rstrip(),
             f"Processor cores:    {os.cpu_count()}",
             f"Memory:             {memory_gb()}",
             f"Python:             {sys.version.split()[0]} ({sys.executable})"]
    for p in PACKAGES:
        try:
            v = metadata.version(p)
        except metadata.PackageNotFoundError:
            v = "not installed"
        lines.append(f"  {p:<17} {v}")
    (RUN_DIR / "environment.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_logged(cmd, logfile):
    """Run one command: show its output and save every line with a date-time stamp."""
    env = dict(os.environ, PYTHONUNBUFFERED="1", PYTHONIOENCODING="utf-8")
    with logfile.open("w", encoding="utf-8") as f:
        f.write(f"[{stamp()}] command: {' '.join(cmd)}\n")
        p = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True, encoding="utf-8", errors="replace", env=env)
        for line in p.stdout:
            print(line, end="", flush=True)
            f.write(f"[{stamp()}] {line}")
        rc = p.wait()
        f.write(f"[{stamp()}] exit code: {rc}\n")
    return rc


def main():
    ap = argparse.ArgumentParser(description="Reproduce every result in the study.")
    ap.add_argument("--quick", action="store_true", help="short trial run that checks your setup")
    ap.add_argument("--list", action="store_true", help="list the stages and their commands, then stop")
    ap.add_argument("--from", dest="start", type=int, default=1, help="first stage to run")
    ap.add_argument("--only", type=int, help="run this one stage")
    ap.add_argument("--with-robustness", action="store_true",
                    help="also run stage 9 (robustness and calibration runs for Appendix D; 2-3 hours more)")
    a = ap.parse_args()

    stages = quick_stages() if a.quick else full_stages()
    if not a.quick and not a.with_robustness and a.only != len(stages):
        stages = stages[:-1]          # stage 9 is optional
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
    global RUN_DIR
    RUN_DIR = HERE / "logs" / f"run_{time.strftime('%Y-%m-%d_%H%M%S')}{'_quick' if a.quick else ''}"
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    mode = "quick trial" if a.quick else "full replication"
    write_environment(mode + (f", stages {first} to {last}" if (first, last) != (1, len(stages)) else ""))
    if first == 1 and not (HERE / "_reference").exists():
        subprocess.run([PY, "start-here/verify.py", "snapshot"], cwd=ROOT, check=True)
    if a.quick:
        shutil.rmtree(ROOT / "start-here" / "_quick", ignore_errors=True)

    log(f"=== {'Quick trial run' if a.quick else 'Full replication'} started {time.strftime('%Y-%m-%d %H:%M')} "
        f"(Python {sys.version.split()[0]}); logs in start-here/logs/{RUN_DIR.name}/ ===")
    t_all = time.time()
    for i in range(first, last + 1):
        title, cmds = stages[i - 1]
        log(f"\nStage {i} of {len(stages)}: {title}")
        t0 = time.time()
        for k, c in enumerate(cmds, 1):
            shown = " ".join(c[3:] if c[1:3] == ["-m", "ipsim"] else c[1:])
            log(f"  running: {shown}")
            t1 = time.time()
            target = c[3] if c[1:3] == ["-m", "ipsim"] else (c[2] if c[1] == "-m" else c[1])
            name = re.sub(r"[^A-Za-z0-9]+", "_", Path(target).with_suffix("").as_posix())
            rc = run_logged(c, RUN_DIR / f"stage{i}_{k:02d}_{name.strip('_')}.log")
            if rc != 0:
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
