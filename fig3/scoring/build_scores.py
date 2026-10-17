"""Recompute every Figure 3 score from the run outputs stored in this repository and write fig_scores.json.

Usage (from the repository root):
  PYTHONPATH=. python fig3/scoring/build_scores.py OUTPUT.json            write the scores
  PYTHONPATH=. python fig3/scoring/build_scores.py --check                compare with the file the figure was built from

Round 1 is scored with the nuclei rule it was published with ("drop_first", see fig3/scoring/tasks.py).
Conventions: median of runs is taken by the figure builder; here each run is listed. A run whose code crashed or wrote
no label image is recorded as -1 (drawn as x, counted as F1 0). Row c is scored on the held-out half for both conditions.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import tifffile

from common.paths import REPO_ROOT
from functools import partial

from fig3.scoring import tasks

TASKS = tasks.TASKS
score = partial(tasks.score, nuclei_rule="drop_first")  # round-1 rule (reproduces the draft figure)
score_heldout = partial(tasks.score_heldout, nuclei_rule="drop_first")

FIG3 = REPO_ROOT / "fig3"
FIGURE_SCORES = FIG3 / "figure" / "source_data" / "bf3" / "fig_scores.json"
TASK_DIR_NAME = {"nuclei": "nuclei", "cancer": "cancer", "endo": "endothelial"}
CRASHED = -1


def _labels(run_dir: Path) -> Path:
    """Label image written by a run."""
    return run_dir / "artifacts" / "labels.tif"


def code_run(name: str, task: str) -> tuple[float, int | None]:
    """(F1, number of predicted objects) for a code run; (CRASHED, None) if it produced no label image."""
    run_dir = FIG3 / "code" / "runs" / name
    if not run_dir.is_dir():
        raise FileNotFoundError(f"Run folder missing: {run_dir}")
    if not _labels(run_dir).is_file():
        return CRASHED, None
    s = score(task, tifffile.imread(_labels(run_dir)))
    return s["f1"], s["n_pred"]


def code_condition(prefix: str, task: str) -> dict:
    """F1 and object counts of the three runs of one code condition."""
    runs = [code_run(f"{prefix}_{TASK_DIR_NAME[task]}_r{k}", task) for k in (1, 2, 3)]
    return {"f1": [r[0] for r in runs], "n": [r[1] for r in runs]}


def agent_condition(task: str) -> dict:
    """Row c: by-eye agent (its own whole-field labels) vs agent with annotation (frozen pipeline on held-out half)."""
    by_eye = score_heldout(task, tifffile.imread(FIG3 / "optimise" / "runs" / f"by_eye_{TASK_DIR_NAME[task]}" / "artifacts" / "labels.tif"))
    scored = score_heldout(task, tifffile.imread(FIG3 / "optimise" / "heldout" / f"ref_{task}_labels.tif"))
    reported = FIG3 / "optimise" / "runs" / f"with_annotation_{TASK_DIR_NAME[task]}" / "artifacts" / "reported.json"
    return {"before": [by_eye["f1"]], "after": [scored["f1"]], "before_n": [by_eye["n_pred"]], "after_n": [scored["n_pred"]],
            "dev_reported": json.loads(reported.read_text()).get("f1") if reported.is_file() else None,
            "n_ref_heldout": scored["n_ref"]}


def draw_condition(task: str) -> dict:
    """Row d: F1 of the outlines the model drew (rasterised), number drawn, and the counts it stated when asked."""
    f1s, drawn = [], []
    for k in (1, 2, 3):
        run_dir = FIG3 / "direct_answers" / "runs" / f"draw_{TASK_DIR_NAME[task]}_r{k}"
        labels = tifffile.imread(_labels(run_dir))
        f1s.append(score(task, labels)["f1"])
        drawn.append(int(len(set(labels[labels > 0].ravel().tolist()))))
    source = FIG3 / "direct_answers" / "source"
    if task == "nuclei":
        asked = json.loads((source / "nuclei_scores.json").read_text())["counts_asked_nuclei"]
    else:
        asked = json.loads((source / "round2_all_scores.json").read_text())["counts_asked"][task]
    return {"f1": f1s, "drawn_rasterised": drawn, "asked": asked}


def default_cellpose(task: str) -> float:
    """Grey dashed line: Cellpose-SAM with default settings."""
    if task == "nuclei":
        path = FIG3 / "baselines" / "cellpose_default_nuclei" / "labels.tif"
    else:
        path = REPO_ROOT / "fig1" / "source_data" / "full_field" / "cellpose_sam_labels.tif"
    return score(task, tifffile.imread(path))["f1"]


def build() -> dict:
    """All Figure 3 scores, per task and row."""
    out = {}
    for task in TASKS:
        out[task] = {"python": {"generic": code_condition("python_generic", task), "box1": code_condition("python_box1", task)},
                     "fiji": {"generic": code_condition("fiji_generic", task), "box1": code_condition("fiji_box1", task)},
                     "agent": agent_condition(task), "draw": draw_condition(task), "default": default_cellpose(task)}
    return out


def check(scores: dict) -> list[str]:
    """Differences between the recomputed scores and the file the figure was built from (empty list = identical)."""
    fig = json.loads(FIGURE_SCORES.read_text())["tasks"]
    problems = []

    def same(what: str, a: object, b: object) -> None:
        """Record a difference between a recomputed and a published value."""
        if a != b:
            problems.append(f"{what}: recomputed {a} vs figure {b}")

    for t in TASKS:
        s, f = scores[t], fig[t]
        for lang, key in (("python", "py"), ("fiji", "fj")):
            same(f"{t} {lang} generic F1", s[lang]["generic"]["f1"], f[key]["before"])
            same(f"{t} {lang} box1 F1", s[lang]["box1"]["f1"], f[key]["after"])
            same(f"{t} {lang} generic n", s[lang]["generic"]["n"], f[key]["before_n"])
            same(f"{t} {lang} box1 n", s[lang]["box1"]["n"], f[key]["after_n"])
        for k in ("before", "after", "before_n", "after_n", "dev_reported"):
            same(f"{t} agent {k}", s["agent"][k], f["agent"][k])
        same(f"{t} draw F1", s["draw"]["f1"], f["draw"]["f1"])
        same(f"{t} draw asked", s["draw"]["asked"], f["draw"]["asked"])
        same(f"{t} default", s["default"], f["default"])
    return problems


def main(argv: list[str]) -> None:
    """Write the scores, or check them against the figure (exit 1 on any difference)."""
    if len(argv) != 2:
        raise SystemExit(__doc__)
    scores = build()
    if argv[1] == "--check":
        problems = check(scores)
        print("\n".join(problems) if problems else "OK: all Figure 3 scores reproduced from the repository")
        raise SystemExit(1 if problems else 0)
    Path(argv[1]).write_text(json.dumps(scores, indent=1))


if __name__ == "__main__":
    main(sys.argv)
