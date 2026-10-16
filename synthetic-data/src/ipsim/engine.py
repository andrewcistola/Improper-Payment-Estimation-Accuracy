"""Scenario runner.

Python here is orchestration only: read a YAML config, open DuckDB, set
scenario variables, execute the program's SQL files in order, call the
rare Python step (an ML model fit, a calibration root-find), then export
tables. All data generation, error injection, benefit logic, frames and
truth tables live in ``src/sql``.
"""
from __future__ import annotations

import hashlib
import importlib
import json
import platform
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import duckdb
import yaml

SRC = Path(__file__).resolve().parents[1]
SQL_DIR = SRC / "sql"
ROOT = SRC.parent  # synthetic-data/


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


@dataclass
class Context:
    """Passed to Python steps."""

    con: duckdb.DuckDBPyConnection
    program: str
    scenario: str
    vars: dict
    config: dict
    outdir: Path
    log: list = field(default_factory=list)

    def var(self, name: str):
        return self.vars[name]

    def sql(self, q: str, params=None):
        return self.con.execute(q, params or [])

    def set_var(self, name: str, value):
        self.vars[name] = value
        self.con.execute(f"SET VARIABLE {name} = ?", [value])


class Engine:
    def __init__(self, config_path: str | Path, output_root: str | Path | None = None,
                 threads: int | None = None):
        self.config_path = Path(config_path).resolve()
        self.config = yaml.safe_load(self.config_path.read_text())
        self.program = self.config["program"]
        self.seed = int(self.config["seed"])
        if output_root:  # CLI value: relative to the current directory
            self.output_root = Path(output_root).resolve()
        else:            # config value: relative to synthetic-data/
            self.output_root = (ROOT / self.config.get("output_root", "output")).resolve()
        self.threads = threads or self.config.get("threads")

    # ------------------------------------------------------------------ #
    def _connect(self) -> duckdb.DuckDBPyConnection:
        con = duckdb.connect()
        if self.threads:
            con.execute(f"SET threads = {int(self.threads)}")
        con.execute("SET preserve_insertion_order = true")
        for lib in sorted((SQL_DIR / "lib").glob("*.sql")):
            con.execute(lib.read_text())
        return con

    def scenarios(self) -> list[tuple[str, dict]]:
        defaults = dict(self.config.get("defaults", {}))
        out = []
        for sc in self.config.get("scenarios", [{"name": "base"}]):
            sc = dict(sc)
            name = sc.pop("name")
            v = {**defaults, **sc}
            out.append((name, v))
        # optional cartesian grid: {grid: {var: [..], var2: [..]}, name: "{var}_{var2}"}
        grid = self.config.get("grid")
        if grid:
            import itertools
            keys = list(grid["vars"].keys())
            for combo in itertools.product(*[grid["vars"][k] for k in keys]):
                v = {**defaults, **dict(zip(keys, combo))}
                out.append((grid["name"].format(**v), v))
        # lookups: derive a variable from another, e.g. n_units by shape
        for var, spec in self.config.get("lookups", {}).items():
            for _, v in out:
                if var not in v:
                    v[var] = spec["map"][v[spec["by"]]]
        return out

    # ------------------------------------------------------------------ #
    def run(self, only: list[str] | None = None) -> list[Path]:
        written = []
        for name, v in self.scenarios():
            if only and name not in only:
                continue
            written.append(self.run_scenario(name, v))
        self._program_manifest()
        return written

    def run_scenario(self, name: str, v: dict) -> Path:
        con = self._connect()
        outdir = self.output_root / self.program / name
        outdir.mkdir(parents=True, exist_ok=True)
        v = dict(v)
        v["seed"] = child_seed(self.seed, self.program, name)
        v["master_seed"] = self.seed
        ctx = Context(con, self.program, name, v, self.config, outdir)
        for k, val in v.items():
            if isinstance(val, (list, dict)):
                val = json.dumps(val)
            con.execute(f"SET VARIABLE {k} = ?", [val])

        for step in self.config["steps"]:
            if "sql" in step:
                con.execute((SQL_DIR / step["sql"]).read_text())
            elif "python" in step:
                mod, fn = step["python"].split(":")
                getattr(importlib.import_module(mod), fn)(ctx, **step.get("args", {}))
            else:
                raise ValueError(f"unknown step {step}")

        files = self._export(ctx)
        self._scenario_manifest(ctx, files)
        con.close()
        print(f"[{self.program}] {name}: " + ", ".join(f"{p.name}" for p in files))
        return outdir

    # ------------------------------------------------------------------ #
    def _export(self, ctx: Context) -> list[Path]:
        con, outdir = ctx.con, ctx.outdir
        files = []
        for spec in self.config.get("exports", [{"table": "population", "order_by": "unit_id"}]):
            path = outdir / f"{spec.get('file', spec['table'])}.parquet"
            con.execute(
                f"COPY (SELECT * FROM {spec['table']} ORDER BY {spec['order_by']}) "
                f"TO '{path}' (FORMAT parquet, COMPRESSION zstd, ROW_GROUP_SIZE 122880)"
            )
            files.append(path)

        # truth: table truth(level, key, metric, value)
        truth = {"program": self.program, "scenario": ctx.scenario, "overall": {}, "by": {}}
        for level, key, metric, value in con.execute(
                "SELECT level, key, metric, value FROM truth ORDER BY level, key, metric").fetchall():
            value = float(value) if value is not None else None
            if level == "overall":
                truth["overall"][metric] = value
            else:
                truth["by"].setdefault(level, {}).setdefault(str(key), {})[metric] = value
        p = outdir / "truth.json"
        p.write_text(json.dumps(truth, indent=2, sort_keys=True) + "\n")
        files.append(p)

        design = self._render(self.config.get("design", {}), ctx.vars)
        p = outdir / "design.yaml"
        p.write_text(yaml.safe_dump(design, sort_keys=False))
        files.append(p)

        cfg = {"program": self.program, "scenario": ctx.scenario,
               "master_seed": self.seed, "scenario_seed": ctx.vars["seed"],
               "variables": {k: v for k, v in ctx.vars.items() if k not in ("seed", "master_seed")},
               "steps": self.config["steps"]}
        p = outdir / "config.yaml"
        p.write_text(yaml.safe_dump(cfg, sort_keys=False))
        files.append(p)
        if ctx.log:
            p = outdir / "calibration_log.json"
            p.write_text(json.dumps(ctx.log, indent=2) + "\n")
            files.append(p)
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

    def _scenario_manifest(self, ctx: Context, files: list[Path]):
        rows = {}
        for f in files:
            entry = {"sha256": sha256_file(f), "bytes": f.stat().st_size}
            if f.suffix == ".parquet":
                entry["rows"] = ctx.con.execute(f"SELECT count(*) FROM '{f}'").fetchone()[0]
            rows[f.name] = entry
        man = {"program": self.program, "scenario": ctx.scenario,
               "config_file": self.config_path.name,
               "config_sha256": sha256_file(self.config_path),
               "duckdb": duckdb.__version__, "python": platform.python_version(),
               "files": rows}
        (ctx.outdir / "manifest.json").write_text(json.dumps(man, indent=2, sort_keys=True) + "\n")

    def _program_manifest(self):
        base = self.output_root / self.program
        out = {}
        for m in sorted(base.glob("*/manifest.json")):
            d = json.loads(m.read_text())
            out[d["scenario"]] = {k: v["sha256"] for k, v in d["files"].items()}
        (base / "manifest.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(prog="ipsim", description="Build synthetic improper-payment populations")
    ap.add_argument("config", nargs="+")
    ap.add_argument("--only", nargs="*", help="scenario names to build")
    ap.add_argument("--out", help="output root (default: config output_root)")
    ap.add_argument("--threads", type=int)
    a = ap.parse_args(argv)
    for c in a.config:
        Engine(c, a.out, a.threads).run(a.only)


if __name__ == "__main__":
    sys.exit(main())
