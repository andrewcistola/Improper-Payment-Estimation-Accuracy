"""Scenario runner (orchestration only).

For each scenario in a YAML config: open DuckDB, load the shared SQL
library (shared/sql/lib/*.sql), set the scenario's variables, run the
config's SQL files in order, then write the outputs. All data
generation, error injection, estimation and scoring live in SQL files.

Config keys
  program      name used in logs and manifests
  seed         master seed; each scenario gets child_seed(seed, program, scenario)
  steps        list of {sql: <path relative to the repo root>}, or
               {python: <estimation/simulation.py>} for the simulation
               estimator's numpy loop (see shared/ipsim/simulation.py), or
               {python: <file>, run: <function>} to call fn(con, variables)
  output_dir   folder for outputs, relative to the config file (default: output)
  defaults     variables shared by all scenarios
  scenarios    list of {name: ..., <variable overrides>}
  grid         optional cartesian scenarios: {name: "<format>", vars: {var: [values]}}
  lookups      optional derived variables: {var: {by: other_var, map: {value: result}}}
  exports      Parquet outputs: [{table, order_by, file?}]
  json         JSON outputs (list of records): [{table, order_by, file}]
  csv          CSV outputs with a header row: [{table, order_by, file}]
  truth        true -> write truth.json from table truth(level, key, metric, value)
  design       production design metadata written to design.yaml ($var substitutes)

String variables may reference other variables with {name} (str.format).
"""
from __future__ import annotations

import atexit
import hashlib
import itertools
import json
import platform
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import duckdb
import yaml

ROOT = Path(__file__).resolve().parents[2]      # repository root
LIB = ROOT / "shared" / "sql" / "lib"


def child_seed(master: int, *labels: Any) -> int:
    """Deterministic child seed from the master seed and labels (sha256)."""
    h = hashlib.sha256(":".join([str(master), *map(str, labels)]).encode()).digest()
    return int.from_bytes(h[:8], "big") >> 2  # fits a signed BIGINT


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def connect(threads: int | None = None, memory_limit: str | None = None) -> duckdb.DuckDBPyConnection:
    """DuckDB connection with the shared SQL library loaded (in file-name order).

    Each connection spills to its own temporary folder; DuckDB's default
    (./.tmp) is shared, and parallel runs corrupt each other's spill files.
    """
    con = duckdb.connect()
    tmp = tempfile.mkdtemp(prefix="ipsim-duckdb-")
    atexit.register(shutil.rmtree, tmp, True)
    con.execute(f"SET temp_directory = '{tmp}'")
    if threads:
        con.execute(f"SET threads = {int(threads)}")
    if memory_limit:
        con.execute(f"SET memory_limit = '{memory_limit}'")
    con.execute("SET preserve_insertion_order = true")
    for lib in sorted(LIB.glob("*.sql")):
        con.execute(lib.read_text())
    return con


def _package_versions() -> dict:
    """Versions of the packages whose numerics or random streams shape the outputs
    (recorded in every manifest; a rerun is byte-identical within one pinned set)."""
    out = {}
    for name in ("numpy", "scipy", "numba", "pyarrow", "pyyaml"):
        try:
            from importlib import metadata
            out[name] = metadata.version(name)
        except Exception:  # pragma: no cover
            out[name] = None
    try:
        import numpy as _np
        cfg = _np.show_config(mode="dicts")
        blas = cfg.get("Build Dependencies", {}).get("blas", {})
        out["blas"] = f"{blas.get('name')} {blas.get('version')}".strip()
    except Exception:  # pragma: no cover
        out["blas"] = None
    return out


def _json_value(v):
    if isinstance(v, float) or v is None or isinstance(v, (int, str, bool)):
        return v
    try:
        return float(v)
    except (TypeError, ValueError):
        return str(v)


class Engine:
    def __init__(self, config_path: str | Path, output_dir: str | Path | None = None,
                 threads: int | None = None):
        self.config_path = Path(config_path).resolve()
        self.config = yaml.safe_load(self.config_path.read_text())
        self.program = self.config["program"]
        self.seed = int(self.config["seed"])
        base = self.config_path.parent
        self.output_dir = (Path(output_dir).resolve() if output_dir
                           else (base / self.config.get("output_dir", "output")).resolve())
        self.threads = threads or self.config.get("threads")
        self.memory_limit = None
        self.timing = False

    # ------------------------------------------------------------------ #
    def scenarios(self) -> list[tuple[str, dict]]:
        defaults = dict(self.config.get("defaults", {}))
        out = []
        for sc in self.config.get("scenarios", []) or []:
            sc = dict(sc)
            name = sc.pop("name")
            out.append((name, {**defaults, **sc}))
        grid = self.config.get("grid")
        if grid:
            keys = list(grid["vars"])
            for combo in itertools.product(*[grid["vars"][k] for k in keys]):
                v = {**defaults, **dict(zip(keys, combo))}
                out.append((grid["name"].format(**v), v))
        for var, spec in (self.config.get("lookups") or {}).items():
            for _, v in out:
                v.setdefault(var, spec["map"][v[spec["by"]]])
        for name, v in out:  # {var} templates in string values
            v["scenario"] = name
            for k, val in list(v.items()):
                if isinstance(val, str) and "{" in val:
                    v[k] = val.format(**v)
        return out

    def run(self, only: list[str] | None = None) -> list[Path]:
        done = []
        for name, v in self.scenarios():
            if only and name not in only:
                continue
            done.append(self.run_scenario(name, v))
        self._program_manifest()
        return done

    # ------------------------------------------------------------------ #
    def run_scenario(self, name: str, v: dict) -> Path:
        con = connect(self.threads, self.memory_limit)
        outdir = self.output_dir / name
        outdir.mkdir(parents=True, exist_ok=True)
        v = dict(v)
        v["seed"] = child_seed(self.seed, self.program, name)
        v["master_seed"] = self.seed
        v["repo_root"] = str(ROOT)
        for k, val in v.items():
            con.execute(f"SET VARIABLE {k} = ?", [json.dumps(val) if isinstance(val, (list, dict)) else val])
        for step in self.config["steps"]:
            t0 = time.time()
            if "python" in step:  # numpy steps: the simulation (and Part D's benefit reruns)
                from . import simulation
                module = simulation.load_kernel(ROOT / step["python"])
                if "run" in step:     # a named function of the module: fn(con, variables)
                    getattr(module, step["run"])(con, v)
                else:                 # the bootstrap simulation loop
                    simulation.run(con, v, module)
            else:
                con.execute((ROOT / step["sql"]).read_text())
            if self.timing:
                print(f"  {time.time() - t0:7.1f}s  {step.get('sql') or step.get('python')}", file=sys.stderr)
        files = self._export(con, name, v, outdir)
        self._scenario_manifest(con, name, outdir, files)
        con.close()
        print(f"[{self.program}] {name}: " + ", ".join(p.name for p in files))
        return outdir

    def _export(self, con, name, v, outdir) -> list[Path]:
        files = []
        for spec in self.config.get("exports") or []:
            path = outdir / f"{spec.get('file', spec['table'])}.parquet"
            con.execute(f"COPY (SELECT * FROM {spec['table']} ORDER BY {spec['order_by']}) "
                        f"TO '{path}' (FORMAT parquet, COMPRESSION zstd, ROW_GROUP_SIZE 122880)")
            files.append(path)
        for spec in self.config.get("csv") or []:
            path = outdir / spec["file"]
            con.execute(f"COPY (SELECT * FROM {spec['table']} ORDER BY {spec['order_by']}) "
                        f"TO '{path}' (FORMAT csv, HEADER true)")
            files.append(path)
        for spec in self.config.get("json") or []:
            cur = con.execute(f"SELECT * FROM {spec['table']} ORDER BY {spec['order_by']}")
            cols = [d[0] for d in cur.description]
            rows = [{c: _json_value(x) for c, x in zip(cols, r)} for r in cur.fetchall()]
            path = outdir / spec["file"]
            path.write_text(json.dumps(rows, indent=2) + "\n")
            files.append(path)
        if self.config.get("truth"):
            truth = {"program": self.program, "scenario": name, "overall": {}, "by": {}}
            for level, key, metric, value in con.execute(
                    "SELECT level, key, metric, value FROM truth ORDER BY level, key, metric").fetchall():
                value = float(value) if value is not None else None
                if level == "overall":
                    truth["overall"][metric] = value
                else:
                    truth["by"].setdefault(level, {}).setdefault(str(key), {})[metric] = value
            path = outdir / "truth.json"
            path.write_text(json.dumps(truth, indent=2, sort_keys=True) + "\n")
            files.append(path)
        if self.config.get("design"):
            path = outdir / "design.yaml"
            path.write_text(yaml.safe_dump(self._render(self.config["design"], v), sort_keys=False))
            files.append(path)
        cfg = {"program": self.program, "scenario": name, "master_seed": self.seed,
               "scenario_seed": v["seed"],
               "variables": {k: x for k, x in v.items() if k not in ("seed", "master_seed", "repo_root")},
               "steps": self.config["steps"]}
        path = outdir / "config.yaml"
        path.write_text(yaml.safe_dump(cfg, sort_keys=False))
        files.append(path)
        return files

    @staticmethod
    def _render(obj, v):
        if isinstance(obj, dict):
            return {k: Engine._render(x, v) for k, x in obj.items()}
        if isinstance(obj, list):
            return [Engine._render(x, v) for x in obj]
        if isinstance(obj, str) and obj.startswith("$"):
            return v.get(obj[1:], obj)
        return obj

    def _scenario_manifest(self, con, name, outdir, files):
        entries = {}
        for f in files:
            e = {"sha256": sha256_file(f), "bytes": f.stat().st_size}
            if f.suffix == ".parquet":
                e["rows"] = con.execute(f"SELECT count(*) FROM '{f}'").fetchone()[0]
            entries[f.name] = e
        man = {"program": self.program, "scenario": name,
               "config_file": str(self.config_path.relative_to(ROOT)),
               "config_sha256": sha256_file(self.config_path),
               "duckdb": duckdb.__version__, "python": platform.python_version(),
               "packages": _package_versions(), "files": entries}
        (outdir / "manifest.json").write_text(json.dumps(man, indent=2, sort_keys=True) + "\n")

    def _program_manifest(self):
        out = {}
        for m in sorted(self.output_dir.glob("*/manifest.json")):
            d = json.loads(m.read_text())
            if "files" not in d:      # a program-level manifest of a nested run, not a scenario
                continue
            out[d["scenario"]] = {k: e["sha256"] for k, e in d["files"].items()}
        (self.output_dir / "manifest.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(prog="ipsim", description="Run errors/ or estimation/ configs")
    ap.add_argument("config", nargs="+")
    ap.add_argument("--only", nargs="*", help="scenario names to run")
    ap.add_argument("--out", help="output folder (default: the config's output_dir)")
    ap.add_argument("--threads", type=int)
    ap.add_argument("--timing", action="store_true", help="print the run time of each SQL step")
    ap.add_argument("--memory-limit", help="DuckDB memory limit, e.g. 2GB (when running configs in parallel)")
    ap.add_argument("--set", nargs="*", default=[], metavar="VAR=VALUE",
                    help="override a default variable for this run, e.g. --set reps=20 "
                         "(applies to `defaults` only; a value set inside a scenario or grid wins)")
    a = ap.parse_args(argv)
    for c in a.config:
        e = Engine(c, a.out, a.threads)
        e.timing = a.timing
        e.memory_limit = a.memory_limit
        for kv in a.set:
            k, v = kv.split("=", 1)
            e.config.setdefault("defaults", {})[k] = yaml.safe_load(v)
        e.run(a.only)


if __name__ == "__main__":
    sys.exit(main())
