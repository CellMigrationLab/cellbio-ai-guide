"""Score one round-2 run folder and write score.json next to it.

  PYTHONPATH=. python fig3/v2/score.py RUN_DIR

Everything is scored on the TEST field (209) against the authors' manual annotation, whole field
(fig3/PROTOCOL_V2.md, section 2; to be extended to the v2 measures, section 7). RUN_DIR must contain meta.json with "row", "task" and "condition"; then:
  code_python, code_fiji, optimise : labels.tif = output of the final script / frozen pipeline run on the test image
  direct, condition "box1"         : reply.json  {"count": n, "cells": [{"points": [[x, y], ...]}, ...]}
  direct, condition "generic"      : stated_count.txt (the number the model gave)
Nothing is guessed: a missing or malformed output gives an explicit status ("crashed", "missing_output",
"invalid_json", "invalid_count", "wrong_shape") with F1 0 or no count, never an exception or a silent default.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import tifffile
from skimage.draw import polygon

from fig3.scoring.tasks import TASKS, reference, score

TEST_FIELD = 209
SEGMENTATION_ROWS = ("code_python", "code_fiji", "optimise")


def manual_count(task: str) -> int:
    """Number of objects in the manual annotation of the test field (read from the label image, not hard-coded)."""
    ref = reference(task, TEST_FIELD)
    return int(len(np.unique(ref[ref > 0])))


def field_shape(task: str) -> tuple[int, int]:
    """Shape (rows, columns) of the test field."""
    return reference(task, TEST_FIELD).shape


def rasterise(cells: list, shape: tuple[int, int]) -> tuple[np.ndarray, dict]:
    """Label image from the model's polygons plus an audit of the outlines (invalid, empty, overlapping pixels)."""
    labels, coverage = np.zeros(shape, np.int32), np.zeros(shape, np.int16)
    audit = {"n_outlines": len(cells), "n_invalid": 0, "n_empty_or_outside": 0}
    for k, cell in enumerate(cells, start=1):
        points = np.asarray(cell.get("points", []) if isinstance(cell, dict) else [], float)
        if points.ndim != 2 or points.shape[1] != 2 or points.shape[0] < 3 or not np.isfinite(points).all():
            audit["n_invalid"] += 1
            continue
        rr, cc = polygon(points[:, 1], points[:, 0], shape)
        if rr.size == 0:
            audit["n_empty_or_outside"] += 1
            continue
        coverage[rr, cc] += 1
        labels[rr, cc] = k  # where outlines overlap, the later one wins; overlap is reported below
    audit["overlap_px"] = int((coverage > 1).sum())
    audit["n_valid"] = audit["n_outlines"] - audit["n_invalid"] - audit["n_empty_or_outside"]
    return labels, audit


def parse_count(text: str) -> int | None:
    """An integer count from the text the operator saved; a range 'a-b' gives its midpoint; anything else None."""
    text = text.strip().replace(",", "")
    if re.fullmatch(r"\d+", text):
        return int(text)
    match = re.fullmatch(r"(\d+)\s*[-–]\s*(\d+)", text)
    return round((int(match[1]) + int(match[2])) / 2) if match else None


def score_segmentation(run_dir: Path, task: str) -> dict:
    """Score labels.tif (output on the test image) against the test-field annotation."""
    labels_path = run_dir / "labels.tif"
    if not labels_path.is_file():
        return {"status": "crashed", "f1": 0.0}
    labels = np.squeeze(tifffile.imread(labels_path))
    if labels.shape != field_shape(task):
        return {"status": "wrong_shape", "shape": list(labels.shape), "f1": 0.0}
    s = score(task, labels, field=TEST_FIELD)
    return {"status": "ok", **s}


def score_direct(run_dir: Path, task: str, condition: str) -> dict:
    """Count error (both conditions) and, for drawn outlines, F1 of the rasterised outlines on the test field."""
    manual = manual_count(task)
    if condition == "generic":
        path = run_dir / "stated_count.txt"
        if not path.is_file():
            return {"status": "missing_output", "manual_count": manual}
        stated = parse_count(path.read_text())
        if stated is None:
            return {"status": "invalid_count", "raw": path.read_text().strip()[:200], "manual_count": manual}
        return {"status": "ok", "stated_count": stated, "manual_count": manual, "count_error": stated - manual}
    path = run_dir / "reply.json"
    if not path.is_file():
        return {"status": "missing_output", "manual_count": manual, "f1": 0.0}
    try:
        reply = json.loads(path.read_text())
    except json.JSONDecodeError as error:
        return {"status": "invalid_json", "error": str(error)[:200], "manual_count": manual, "f1": 0.0}
    cells = reply.get("cells", []) if isinstance(reply, dict) else []
    labels, audit = rasterise(cells if isinstance(cells, list) else [], field_shape(task))
    stated = reply.get("count") if isinstance(reply, dict) and isinstance(reply.get("count"), int) else None
    s = score(task, labels, field=TEST_FIELD)
    return {"status": "ok", "stated_count": stated, "manual_count": manual,
            "count_error": None if stated is None else stated - manual,
            "stated_minus_valid_outlines": None if stated is None else stated - audit["n_valid"],
            **audit, "f1": s["f1"], "tp": s["tp"], "fp": s["fp"], "fn": s["fn"]}


def score_run(run_dir: Path) -> dict:
    """Score one run folder according to its row (see module docstring)."""
    meta = json.loads((run_dir / "meta.json").read_text())
    row, task, condition = meta["row"], meta["task"], meta.get("condition", "")
    if task not in TASKS:
        raise ValueError(f"Unknown task {task!r} in {run_dir / 'meta.json'}")
    if row in SEGMENTATION_ROWS:
        return score_segmentation(run_dir, task)
    if row == "direct":
        return score_direct(run_dir, task, condition)
    if row == "advice":
        return {"status": "not_scored_here", "note": "advice is scored with the item check (PROTOCOL_V2 section 5)"}
    raise ValueError(f"Unknown row {row!r}")


def main(argv: list[str]) -> None:
    """Score the run folder given on the command line and write its score.json."""
    if len(argv) != 2:
        raise SystemExit(__doc__)
    run_dir = Path(argv[1])
    result = score_run(run_dir)
    (run_dir / "score.json").write_text(json.dumps(result, indent=1))
    print(run_dir.name, result)


if __name__ == "__main__":
    main(sys.argv)
