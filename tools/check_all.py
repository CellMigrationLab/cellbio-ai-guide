"""Fast check: tests, raw-data checksums, and figures and scores rebuilt from the committed source data.
(The full check from data/raw is tools/check_full.py.)

Usage (from the repository root):  python tools/check_all.py [--with-squirrel]
Each step prints PASS/FAIL; the exit code is non-zero if any step fails. Figures and scores are rebuilt in a temporary
copy, so the committed files are never modified. Every expected output is deleted before its producer runs, so a
producer that exits 0 without writing anything fails instead of leaving the copy of the committed file to compare equal.
"""
from __future__ import annotations

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
    "fig3/figure_v2": ("code/make_fig3_v2.py", "output/fig3_v2.svg"),
}
# In the required order (score_perturb adds to errors' summary). Together these scripts write every JSON in
# fig2/source_data/panels except panels/squirrel.json (squirrel_run.py, only ran with --with-squirrel).
FIG2_SCORING_ORDER = ["errors", "score_perturb", "score_fields", "annot_agree", "bio_result", "al_roi", "al_gray",
                      "al_intensity", "image_generation", "export_errors_window", "tubule_width"]
TEST_DIRS = ("common/tests", "fig2/tests", "fig3/tests")
FIG2_KNOWN_EXTRA_KEYS = {("panels/al_intensity.json", "r_pixel"),  # added by a recovered inline command, not used by Fig 2
                         ("panels/squirrel.json", "s")}           # runtime in s, no longer stored by squirrel_run.py


def sha256(path: Path) -> str:
    """SHA-256 of a file (the same hash as data/manifest.csv)."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def delete_all(paths: list[Path]) -> None:
    """Remove files (or all files inside directories), so a producer that writes nothing cannot pass."""
    for path in paths:
        if path.is_dir():
            for item in sorted(path.iterdir()):
                if item.is_file():
                    item.unlink()
        else:
            path.unlink(missing_ok=True)


def check_figures(tmp: Path) -> list[bool]:
    """Rebuild each figure in a temporary copy and compare its SVG with the committed one."""
    results = []
    for folder, (builder, output) in FIGURES.items():
        work = tmp / folder
        shutil.copytree(REPO / folder, work, dirs_exist_ok=True)
        delete_all([work / output])
        proc = run([sys.executable, str(work / builder)], cwd=work / "source_data")
        same = (proc.returncode == 0 and (work / output).is_file()
                and sha256(work / output) == sha256(REPO / folder / output))
        detail = "" if proc.returncode == 0 else proc.stderr[-300:]
        results.append(report(f"{folder}: rebuilt SVG is byte-identical", same, detail))
    return results


def check_fig1_scores(tmp: Path) -> bool:
    """Recompute the Fig 1c F1 scores and compare the rewritten A_scores.json with the committed one."""
    src = tmp / "fig1" / "source_data"
    rel = "panel_c_step3/A_scores.json"
    (src / rel).unlink(missing_ok=True)
    proc = run([sys.executable, "../code/f1_scores.py"], cwd=src)
    if proc.returncode or not (src / rel).is_file():
        return report("fig1: F1 scores", False, proc.stderr[-300:] or f"producer did not write {rel}")
    same = sha256(src / rel) == sha256(REPO / "fig1/source_data" / rel)
    return report("fig1: F1 scores recomputed from label images", same, (src / rel).read_text())


def check_fig1_step4(tmp: Path) -> bool:
    """Re-export the Fig 1c step-4 crop of field 209 and compare every file with the committed one."""
    src = tmp / "fig1" / "source_data"
    delete_all([src / "panel_c_step4"])
    proc = run([sys.executable, "../code/export_fresh_field.py"], cwd=src)
    if proc.returncode:
        return report("fig1: step-4 crop (field 209)", False, proc.stderr[-300:])
    committed = sorted((REPO / "fig1/source_data/panel_c_step4").iterdir())
    missing = [f.name for f in committed if not (src / "panel_c_step4" / f.name).is_file()]
    differ = [f.name for f in committed if (src / "panel_c_step4" / f.name).is_file()
              and sha256(f) != sha256(src / "panel_c_step4" / f.name)]
    return report("fig1: step-4 crop (field 209) re-exported byte-identical", not differ and not missing,
                  f"missing: {missing}" if missing else f"differ: {differ}" if differ else "")


def check_fig2_scores(tmp: Path, with_squirrel: bool) -> list[bool]:
    """Re-run the Fig 2 scoring scripts (in their required order) and compare every JSON output."""
    results, src = [], tmp / "fig2" / "source_data"
    scripts = FIG2_SCORING_ORDER + (["squirrel_run"] if with_squirrel else [])
    expected = [p for p in sorted((REPO / "fig2/source_data/panels").glob("*.json"))
                if with_squirrel or p.name != "squirrel.json"]
    delete_all([src / "panels" / p.name for p in expected])   # a no-op producer must fail, not pass by the old copy
    for script in scripts:
        proc = run([sys.executable, f"../code/{script}.py"], cwd=src)
        results.append(report(f"fig2: {script}.py runs", proc.returncode == 0, proc.stderr[-300:] if proc.returncode else ""))
    for committed in expected:
        rel = f"panels/{committed.name}"
        out = src / rel
        if not out.is_file():
            results.append(report(f"fig2: {rel} reproduced", False, "producer did not write it"))
            continue
        a = strip_known_extras(rel, json.loads(committed.read_text()))
        b = strip_known_extras(rel, json.loads(out.read_text()))
        if a != b:
            results.append(report(f"fig2: {rel} reproduced", False))
    results.append(report("fig2: all JSON outputs equal to the committed source data",
                          all(results), f"({len(scripts)} scripts)" if not with_squirrel else ""))
    return results


def check_no_nan_json() -> bool:
    """No committed source-data or score JSON may contain NaN or Infinity (undefined values must be explicit nulls)."""
    bad = []
    for folder in ("fig1/source_data", "fig2/source_data", "fig2/analysis", "fig3/figure_v2", "fig3/scoring",
                   "fig3/v2"):
        for path in sorted((REPO / folder).rglob("*.json")):
            try:
                json.loads(path.read_text(), parse_constant=lambda c: bad.append(f"{path.relative_to(REPO)}: {c}"))
            except json.JSONDecodeError as exc:
                bad.append(f"{path.relative_to(REPO)}: not valid JSON ({exc})")
    return report("no NaN/Infinity in committed JSON", not bad, "; ".join(bad[:5]))


def check_unit_tests() -> bool:
    """Run each test folder's discovery on its own: recorded LLM-written test_*.py files elsewhere must not execute."""
    results, total = [], 0
    for folder in TEST_DIRS:
        if not (REPO / folder).is_dir():
            continue
        proc = run([sys.executable, "-m", "unittest", "discover", "-s", folder, "-p", "test_*.py", "-t", "."], cwd=REPO)
        ran = proc.stderr.strip().splitlines() or [""]
        count = next((line for line in reversed(ran) if line.startswith("Ran ")), "")
        n = int(count.split()[1]) if len(count.split()) > 1 else 0
        total += n
        results.append(report(f"unit tests {folder}", proc.returncode == 0 and n > 0,
                              f"({n} tests)" + (" " + proc.stderr.strip().splitlines()[-1] if proc.returncode else "")))
    return all(results)


def check_manifest() -> bool:
    """Verify the raw-data manifest (checksum and recorded size)."""
    proc = run([sys.executable, "data/make_manifest.py", "--verify"], cwd=REPO)
    lines = proc.stdout.strip().splitlines() or [""]
    return report("raw data checksums", proc.returncode == 0, lines[-1])


def main(with_squirrel: bool) -> None:
    """Run all checks; exit 1 if any fails."""
    results = [check_unit_tests()]
    results.append(check_no_nan_json())
    results.append(check_manifest())
    with tempfile.TemporaryDirectory() as tmp_name:
        tmp = Path(tmp_name)
        results += check_figures(tmp)
        results.append(check_fig1_scores(tmp))
        results.append(check_fig1_step4(tmp))
        results += check_fig2_scores(tmp, with_squirrel)
    proc = run([sys.executable, "fig3/v2/check_scores.py"], cwd=REPO)
    results.append(report("fig3: every score recomputed from the stored runs", proc.returncode == 0,
                          (proc.stdout.strip().splitlines() or [""])[-1][-300:]))
    print(f"\n{sum(results)}/{len(results)} checks passed")
    raise SystemExit(0 if all(results) else 1)


if __name__ == "__main__":
    main("--with-squirrel" in sys.argv[1:])
