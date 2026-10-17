"""Check that everything in this repository reproduces: tests, raw-data checksums, figures and scores.

Usage (from the repository root):  python tools/check_all.py [--with-squirrel]
Each step prints PASS/FAIL; the exit code is non-zero if any step fails. Figures and scores are rebuilt in a temporary
copy, so the committed files are never modified.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FIGURES = {  # figure folder -> (builder relative to the folder, output written by the builder, committed reference)
    "fig1": ("code/make_fig1.py", "figure/fig1.svg"),
    "fig2": ("code/make_fig2.py", "figure/fig2.svg"),
    "fig3/figure": ("code/make_fig3.py", "output/fig3.svg"),
}
FIG2_SCORING_ORDER = ["errors", "score_perturb", "annot_agree", "bio_result", "al_intensity", "tubule_width"]
FIG2_KNOWN_EXTRA_KEYS = {("panels/al_intensity.json", "r_pixel")}  # added by a recovered inline command, not used by Fig 2


def md5(path: Path) -> str:
    """MD5 of a file (used only to compare rebuilt and committed files)."""
    return hashlib.md5(path.read_bytes()).hexdigest()


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
    """Run a command with the repository root on PYTHONPATH and capture its output."""
    env = dict(os.environ, PYTHONPATH=str(REPO))
    return subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)


def report(name: str, ok: bool, detail: str = "") -> bool:
    """Print one PASS/FAIL line and return ok."""
    print(f"{'PASS' if ok else 'FAIL'}  {name}{('  ' + detail) if detail else ''}", flush=True)
    return ok


def strip_known_extras(rel: str, data: object) -> object:
    """Remove documented extra keys (FIG2_KNOWN_EXTRA_KEYS) before comparing JSON outputs."""
    for path, key in FIG2_KNOWN_EXTRA_KEYS:
        if rel == path and isinstance(data, dict):
            for value in data.values():
                if isinstance(value, dict):
                    value.pop(key, None)
    return data


def check_figures(tmp: Path) -> list[bool]:
    """Rebuild each figure in a temporary copy and compare its SVG with the committed one."""
    results = []
    for folder, (builder, output) in FIGURES.items():
        work = tmp / folder
        shutil.copytree(REPO / folder, work, dirs_exist_ok=True)
        proc = run([sys.executable, str(work / builder)], cwd=work / "source_data")
        same = proc.returncode == 0 and md5(work / output) == md5(REPO / folder / output)
        results.append(report(f"{folder}: rebuilt SVG is byte-identical", same, proc.stderr[-300:] if proc.returncode else ""))
    return results


def check_fig1_scores(tmp: Path) -> bool:
    """Recompute the Fig 1c F1 scores and compare with the file the figure reads."""
    proc = run([sys.executable, "../code/f1_scores.py"], cwd=tmp / "fig1" / "source_data")
    if proc.returncode:
        return report("fig1: F1 scores", False, proc.stderr[-300:])
    recomputed = ast.literal_eval(proc.stdout.strip().splitlines()[-1])  # the script prints a dict literal
    published = json.loads((REPO / "fig1/source_data/panel_c_step3/A_scores.json").read_text())
    return report("fig1: F1 scores recomputed from label images", recomputed == published, f"{recomputed}")


def check_fig2_scores(tmp: Path, with_squirrel: bool) -> list[bool]:
    """Re-run the Fig 2 scoring scripts (in their required order) and compare every JSON output."""
    results, src = [], tmp / "fig2" / "source_data"
    scripts = FIG2_SCORING_ORDER + (["squirrel_run"] if with_squirrel else [])
    for script in scripts:
        proc = run([sys.executable, f"../code/{script}.py"], cwd=src)
        results.append(report(f"fig2: {script}.py runs", proc.returncode == 0, proc.stderr[-300:] if proc.returncode else ""))
    for committed in sorted((REPO / "fig2/source_data/panels").glob("*.json")):
        rel = f"panels/{committed.name}"
        a = strip_known_extras(rel, json.loads(committed.read_text()))
        b = strip_known_extras(rel, json.loads((src / rel).read_text()))
        if a != b:
            results.append(report(f"fig2: {rel} reproduced", False))
    results.append(report("fig2: all JSON outputs equal to the committed source data", all(results)))
    return results


def main(with_squirrel: bool) -> None:
    """Run all checks; exit 1 if any fails."""
    results = []
    proc = run([sys.executable, "-m", "unittest", "discover", "-s", ".", "-p", "test_*.py", "-t", "."], cwd=REPO)
    results.append(report("unit tests (common/, fig2/, fig3/)", proc.returncode == 0, proc.stderr.strip().splitlines()[-1]))
    proc = run([sys.executable, "data/make_manifest.py", "--verify"], cwd=REPO)
    results.append(report("raw data checksums", proc.returncode == 0, proc.stdout.strip().splitlines()[-1]))
    with tempfile.TemporaryDirectory() as tmp_name:
        tmp = Path(tmp_name)
        results += check_figures(tmp)
        results.append(check_fig1_scores(tmp))
        results += check_fig2_scores(tmp, with_squirrel)
    proc = run([sys.executable, "fig3/scoring/build_scores.py", "--check"], cwd=REPO)
    results.append(report("fig3: every score recomputed from the stored runs", proc.returncode == 0, proc.stdout.strip()[-300:]))
    print(f"\n{sum(results)}/{len(results)} checks passed")
    raise SystemExit(0 if all(results) else 1)


if __name__ == "__main__":
    main("--with-squirrel" in sys.argv[1:])
