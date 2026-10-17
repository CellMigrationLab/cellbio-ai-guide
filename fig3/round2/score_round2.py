"""Score one round-2 run folder and write score.json next to it.

  PYTHONPATH=. python fig3/round2/score_round2.py RUN_DIR

RUN_DIR must contain meta.json with "row" and "task" (written by the operator) and, depending on the row:
  code_python, code_fiji, optimise : labels.tif  (whole field; optimise: the frozen pipeline's output on the whole field)
  direct (box1)                    : reply.json  {"count": n, "cells": [{"points": [[x, y], ...]}, ...]}
  direct (generic)                 : stated_count.txt  (the number the model gave, as an integer)
Segmentation is scored on the held-out right half only (fig3/STRATEGY.md, section 2). Counts are compared with the
whole-field manual count. A missing labels.tif for a code/optimise run is recorded as a crash (F1 0).
"""
import json
import sys
from pathlib import Path

import numpy as np
import tifffile
from skimage.draw import polygon

from fig3.scoring.tasks import score_heldout

FIELD_SHAPE = (1022, 1024)
MANUAL_WHOLE_FIELD = {"nuclei": 441, "cancer": 124, "endo": 382}


def rasterise(cells: list[dict]) -> tuple[np.ndarray, int]:
    """Label image from the model's polygons (later polygons overwrite earlier ones) and the number of invalid outlines."""
    labels, invalid = np.zeros(FIELD_SHAPE, np.int32), 0
    for k, cell in enumerate(cells, start=1):
        points = np.asarray(cell.get("points", []), float) if isinstance(cell, dict) else np.empty((0, 2))
        if points.ndim != 2 or points.shape[1] != 2 or points.shape[0] < 3:
            invalid += 1  # not a polygon
            continue
        rr, cc = polygon(points[:, 1], points[:, 0], FIELD_SHAPE)
        labels[rr, cc] = k
    return labels, invalid


def score_run(run_dir: Path) -> dict:
    """Score one run folder according to its row (see module docstring)."""
    meta = json.loads((run_dir / "meta.json").read_text())
    row, task, condition = meta["row"], meta["task"], meta.get("condition", "")
    if task not in MANUAL_WHOLE_FIELD:
        raise ValueError(f"Unknown task {task!r} in {run_dir / 'meta.json'}")
    if row in ("code_python", "code_fiji", "optimise"):
        labels_path = run_dir / "labels.tif"
        if not labels_path.is_file():
            return {"crashed": True, "f1_heldout": 0.0}
        labels = np.squeeze(tifffile.imread(labels_path))
        if labels.shape != FIELD_SHAPE:
            return {"crashed": False, "error": f"labels shape {labels.shape} != {FIELD_SHAPE}", "f1_heldout": 0.0}
        s = score_heldout(task, labels)
        return {"crashed": False, "f1_heldout": s["f1"], "n_pred_heldout": s["n_pred"], "n_ref_heldout": s["n_ref"],
                "tp": s["tp"], "fn": s["fn"], "fp": s["fp"], "area_ratio_median": s.get("area_ratio_median")}
    if row == "direct":
        manual = MANUAL_WHOLE_FIELD[task]
        if condition == "generic":
            stated = int((run_dir / "stated_count.txt").read_text().strip())
            return {"stated_count": stated, "manual_count": manual, "count_error": stated - manual}
        reply = json.loads((run_dir / "reply.json").read_text())
        labels, invalid = rasterise(reply.get("cells", []))
        s = score_heldout(task, labels)
        stated = reply.get("count")
        return {"stated_count": stated, "n_outlines": len(reply.get("cells", [])), "n_invalid_outlines": invalid,
                "manual_count": manual, "count_error": None if stated is None else stated - manual, "f1_heldout": s["f1"]}
    if row == "advice":
        return {"note": "advice is scored with the rubric (STRATEGY 6.1), not here"}
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
