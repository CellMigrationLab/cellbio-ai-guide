"""Scripted runner for Figure 3 protocol v2 (rows B and C): runs a returned script or frozen pipeline, unchanged, on
field 104 and field 209, each in a clean folder and a fresh virtual environment.

Usage: PYTHONPATH=. python fig3/v2/runner.py RUN_DIR [--field 104|209]

RUN_DIR (fig3/v2/runs/<scenario_id>/) must contain meta.json and:
  row B (code):     code_as_returned.py, optionally code_run.py (input/output paths edited only; diff in EDITS.md)
  row C (optimise): agent_folder/ with pipeline.py and runtime_manifest.json (files the pipeline needs), optionally
                    pipeline_run.py (paths edited only; diff in EDITS.md)
  packages.txt (optional): packages the reply asked to install, one pip requirement per line (recorded as given)
Per field it writes execution_fF.json (command, exit code, timeout, runtime, status), run_fF.log, and on success
labels_fF.tif and measurements_fF.csv. Status: ok | crashed | timeout | no_output | install_failed. A script that
exits non-zero or times out is never 'ok', even if it wrote a file.
"""
from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
import time
import venv
from pathlib import Path

from common.paths import REPO_ROOT

ASSETS = REPO_ROOT / "fig3" / "v2" / "assets"
EXEC_ROOT = Path("/home/user/r2exec_v2")
TIMEOUT_S = 3600
FIELD_ASSET = {104: "dev_{task}_image.tif", 209: "test_{task}_image.tif"}
NEVER_COPY = ("annotation", "image.tif", "image.png")   # development data must not reach the test run


def runtime_files(agent_folder: Path) -> list[Path]:
    """Files listed in runtime_manifest.json (row C); development images and annotations are refused."""
    manifest = agent_folder / "runtime_manifest.json"
    if not manifest.is_file():
        return []
    data = json.loads(manifest.read_text())
    names = data if isinstance(data, list) else data.get("files", [])
    out = []
    for name in names:
        path = (agent_folder / str(name)).resolve()
        if not path.is_relative_to(agent_folder.resolve()):
            raise ValueError(f"runtime file outside the agent folder: {name}")
        if any(k in path.name for k in NEVER_COPY):
            continue          # recorded in execution.json as refused
        if path.is_file():
            out.append(path)
    return out


def make_env(env_dir: Path, packages: list[str], log: list[str]) -> Path | None:
    """Fresh venv on top of the frozen base (system site-packages); returns its python, or None if install failed."""
    venv.EnvBuilder(system_site_packages=True, with_pip=bool(packages), clear=True).create(env_dir)
    python = env_dir / "bin" / "python"
    if packages:
        proc = subprocess.run([str(python), "-m", "pip", "install", "--disable-pip-version-check", *packages],
                              capture_output=True, text=True)
        log.append(f"$ pip install {' '.join(packages)}\nexit {proc.returncode}\n{proc.stdout[-3000:]}\n{proc.stderr[-3000:]}")
        if proc.returncode:
            return None
    return python


def run_field(run_dir: Path, field: int) -> dict:
    meta = json.loads((run_dir / "meta.json").read_text())
    row, task = meta["row"], meta["task"]
    exec_dir = EXEC_ROOT / run_dir.name / f"f{field}"
    if exec_dir.exists():
        shutil.rmtree(exec_dir)
    work = exec_dir / "work"
    work.mkdir(parents=True)
    shutil.copyfile(ASSETS / FIELD_ASSET[field].format(task=task), work / "image.tif")
    refused = []
    if row == "code":
        script = run_dir / ("code_run.py" if (run_dir / "code_run.py").is_file() else "code_as_returned.py")
        shutil.copyfile(script, work / "script.py")
        args = ["script.py"]
    elif row == "optimise":
        folder = run_dir / "agent_folder"
        script = run_dir / ("pipeline_run.py" if (run_dir / "pipeline_run.py").is_file() else "agent_folder/pipeline.py")
        shutil.copyfile(script, work / "pipeline.py")
        for f in runtime_files(folder):
            shutil.copyfile(f, work / f.name)
        manifest = folder / "runtime_manifest.json"
        if manifest.is_file():
            data = json.loads(manifest.read_text())
            names = data if isinstance(data, list) else data.get("files", [])
            refused = [n for n in names if any(k in Path(str(n)).name for k in NEVER_COPY)]
        args = ["pipeline.py", "image.tif", "labels.tif", "measurements.csv"]
    else:
        raise ValueError(f"row {row!r} has nothing to run")
    packages = [p.strip() for p in (run_dir / "packages.txt").read_text().splitlines()
                if p.strip() and not p.startswith("#")] if (run_dir / "packages.txt").is_file() else []
    log: list[str] = []
    python = make_env(exec_dir / "venv", packages, log)
    record = {"field": field, "script": script.name, "packages": packages, "runtime_files_refused": refused,
              "command": None, "exit_code": None, "timeout": False, "runtime_s": None}
    if python is None:
        record["status"] = "install_failed"
    else:
        record["command"] = [str(python), *args]
        t0 = time.time()
        proc = subprocess.Popen([str(python), *args], cwd=work, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, start_new_session=True, env={**os.environ, "PYTHONPATH": ""})
        try:
            out, err = proc.communicate(timeout=TIMEOUT_S)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)          # the whole process group, so no child keeps writing
            out, err = proc.communicate()
            record["timeout"] = True
        record["runtime_s"] = round(time.time() - t0, 1)
        record["exit_code"] = proc.returncode
        log.append(f"$ {' '.join(args)}\nexit {proc.returncode}\n--- stdout\n{out[-20000:]}\n--- stderr\n{err[-20000:]}")
        if record["timeout"]:
            record["status"] = "timeout"
        elif proc.returncode != 0:
            record["status"] = "crashed"
        elif not (work / "labels.tif").is_file():
            record["status"] = "no_output"
        else:
            record["status"] = "ok"
    for name, target in (("labels.tif", f"labels_f{field}.tif"), ("measurements.csv", f"measurements_f{field}.csv")):
        (run_dir / target).unlink(missing_ok=True)
        if record["status"] == "ok" and (work / name).is_file():
            shutil.copyfile(work / name, run_dir / target)
    (run_dir / f"run_f{field}.log").write_text("\n\n".join(log))
    (run_dir / f"execution_f{field}.json").write_text(json.dumps(record, indent=1))
    return record


def main(argv: list[str]) -> None:
    if len(argv) < 2:
        raise SystemExit(__doc__)
    run_dir = Path(argv[1]).resolve()
    fields = [int(argv[3])] if argv[2:3] == ["--field"] else [104, 209]
    for f in fields:
        r = run_field(run_dir, f)
        print(run_dir.name, f, r["status"], r["runtime_s"], "s")


if __name__ == "__main__":
    main(sys.argv)
