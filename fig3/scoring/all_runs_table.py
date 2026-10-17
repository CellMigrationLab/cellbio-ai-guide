"""Write fig3/all_runs.csv: one row per LLM run of the round-1 draft figure, with its score where it produced labels.

Usage: PYTHONPATH=. python fig3/scoring/all_runs_table.py
Task and scoring follow fig3/scoring/tasks.py; runs without a whole-field label image get an empty score.
"""
import csv
import json

import numpy as np
import tifffile

from common.paths import REPO_ROOT
from functools import partial

from fig3.scoring import tasks

score = partial(tasks.score, nuclei_rule="drop_first")  # round-1 runs: the rule used for the draft figure

FIG3 = REPO_ROOT / "fig3"
TASK_WORDS = {"nuclei": "nuclei", "cancer": "cancer", "endothelial": "endo"}


def task_of(run_id: str) -> str | None:
    """Task scored for a run, inferred from its id (None for runs without a task)."""
    return next((task for word, task in TASK_WORDS.items() if word in run_id), None)


def main() -> None:
    """Write fig3/all_runs.csv."""
    rows = []
    for entry in csv.DictReader(open(FIG3 / "runs_index.csv")):
        run_dir = FIG3 / entry["section"] / "runs" / entry["run_id"]
        meta = json.loads((run_dir / "meta.json").read_text())
        labels = run_dir / "artifacts" / "labels.tif"
        task, result = task_of(entry["run_id"]), {}
        if labels.is_file() and task:
            image = np.squeeze(tifffile.imread(labels))
            if image.shape == (1022, 1024):
                result = score(task, image)
        rows.append({"section": entry["section"], "run_id": entry["run_id"], "status": entry["status"], "task": task or "",
                     "model": ";".join(meta.get("models", [])), "start": meta.get("start", ""),
                     "web_calls": len(meta.get("web", [])), "f1": result.get("f1", ""), "n_pred": result.get("n_pred", ""),
                     "labels_written": labels.is_file(), "note": entry["note"]})
    with open(FIG3 / "all_runs.csv", "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} rows")


if __name__ == "__main__":
    main()
