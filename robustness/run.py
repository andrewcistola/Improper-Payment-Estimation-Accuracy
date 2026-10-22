"""Robustness and calibration runs (Appendix D of the manuscript).

Two questions the main results cannot answer on their own:

1. Robustness to model misspecification. The synthetic populations
   fabricate errors independently of payment size within each stratum, which
   is exactly the model the bootstrap simulation assumes when it assigns
   count-based error rates to units whose sizes come from the population.
   Here every program's population is rebuilt with `size_beta` != 0, so that
   a unit's error probability is multiplied by (payment / stratum mean
   payment)^size_beta (capped at 0.95) before calibration, and the same
   designs are re-estimated with every method.

2. Calibration of the parametric interval. With 25 audit years the Monte
   Carlo standard error of a coverage estimate is about 4.4 points, so the
   interval's half-width is compared instead with the empirical standard
   deviation of the point estimates over 100 audit years (the ratio
   half-width / (1.96 x SD) should be close to 1).

Run from the repository root (about 2 to 3 hours on a 2-core machine):

    python robustness/run.py                 # everything below
    python robustness/run.py --only beta     # populations + estimation at each size_beta
    python robustness/run.py --only calib    # 100-audit-year calibration run on the base populations
    python robustness/run.py --only summary  # tables only (robustness/results/*.csv, manuscripts/generated/appendix_d.md)
    python robustness/run.py --list

Outputs:
    robustness/output/<program>/beta_<b>/...          rebuilt populations (parquet files are not committed; manifests are)
    robustness/results/<program>/beta_<b>/...         estimates for every method at that size_beta
    robustness/results/<program>/calibration/...      100 audit years, parametric rates, base population
    robustness/results/summary_*.csv                  the tables behind Appendix D
    manuscripts/generated/appendix_d.md               Appendix D tables (assembled into the manuscript)
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable

BETAS = [0.5, -0.5]          # error probability rising / falling with payment size

# Part D is the one population that is not calibrated to a dollar target: its error rates are
# stated count rates. Because gross drug cost is heavy-tailed, size_beta = +0.5 would multiply
# its gross rate five-fold (and -0.5 would halve it) while every other program's calibration
# multiplier holds the gross rate fixed. Part D therefore uses size_beta = +/-0.25 with the two
# stated count rates rescaled (linearly, below the cap) so that the true gross rate stays at
# the base population's 1.38%. The scenario folders keep the generic names beta_p0.5 / beta_m0.5.
PROGRAM_SETS = {
    "part-d-ipm": {0.5: ["size_beta=0.25", "error_rate=0.01197", "ltc_error_rate=0.04788"],
                   -0.5: ["size_beta=-0.25", "error_rate=0.04369", "ltc_error_rate=0.17478"]},
}
CALIB = ["reps=100", "sim_reps=100", "sim_iterations=500"]
ROBUST_SIM = ["sim_iterations=500"]

# program key, errors config(s) with their output scenario folder, estimation config, perm pooling
PROGRAMS = [
    ("part-c-ipm", [("part-c-ipm/errors/config.yaml", "base")], "part-c-ipm/estimation/config.yaml", None),
    ("part-d-ipm", [("part-d-ipm/errors/config.yaml", "base")], "part-d-ipm/estimation/config.yaml", None),
    ("eipm", [("eipm/errors/config.yaml", "base")], "eipm/estimation/config.yaml", None),
    ("perm", [("perm/errors/config.yaml", "state_elig_grid")], "perm/estimation/config.yaml",
     "perm/estimation/national.yaml"),
    ("cert", [("cert/errors/config.yaml", "national")], "cert/estimation/config.yaml", None),
]


def ipsim(*args):
    return [PY, "-m", "ipsim", *args]


def beta_tag(b):
    return f"beta_{b:+.1f}".replace("+", "p").replace("-", "m")   # beta_p0.5, beta_m0.5


def beta_commands():
    cmds = []
    for b in BETAS:
        tag = beta_tag(b)
        for prog, errs, est, pool in PROGRAMS:
            out_pop = f"robustness/output/{prog}/{tag}"
            out_res = f"robustness/results/{prog}/{tag}"
            sets = PROGRAM_SETS.get(prog, {}).get(b, [f"size_beta={b}"])
            for cfg, scen in errs:
                cmds.append(ipsim(cfg, "--out", out_pop, "--set", *sets))
            pop_dir = f"{out_pop}/{errs[0][1]}"
            cmds.append(ipsim(est, "--out", out_res, "--set", f"population_dir={pop_dir}", *ROBUST_SIM))
            if pool:
                cmds.append(ipsim(pool, "--out", out_res, "--set", f"perm_results_dir={out_res}"))
    return cmds


def calib_commands():
    cmds = []
    for prog, errs, est, pool in PROGRAMS:
        out_res = f"robustness/results/{prog}/calibration"
        cmds.append(ipsim(est, "--out", out_res, "--set", *CALIB))
        if pool:
            cmds.append(ipsim(pool, "--out", out_res, "--set", f"perm_results_dir={out_res}"))
    return cmds


def summary_commands():
    return [[PY, "robustness/summarize.py"]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=["beta", "calib", "summary"])
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    groups = {"beta": beta_commands, "calib": calib_commands, "summary": summary_commands}
    keys = [a.only] if a.only else ["beta", "calib", "summary"]
    for k in keys:
        for cmd in groups[k]():
            print(" ".join(cmd[1:]) if cmd[0] == PY else " ".join(cmd))
            if a.list:
                continue
            t0 = time.time()
            r = subprocess.run(cmd, cwd=ROOT)
            if r.returncode:
                sys.exit(f"FAILED: {' '.join(cmd)}")
            print(f"    done in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
