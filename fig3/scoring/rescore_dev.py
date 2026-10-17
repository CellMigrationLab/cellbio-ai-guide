"""Re-score each annotation-guided agent's final development-half output with OUR scorer.

The 'reported' development F1 in row c came from scoring code each agent wrote itself (fig3/optimise/runs/
with_annotation_*/artifacts/score.py), which differs from ours in matching and border handling. This puts the
reported and held-out numbers on the same scale.  Usage: PYTHONPATH=. python fig3/scoring/rescore_dev.py
"""
import json

import numpy as np
import tifffile
from skimage.segmentation import clear_border

from common.paths import REPO_ROOT
from fig3.scoring.tasks import HALF_X, _counts, cancer_mask, drop_objects_on_cancer_cells, reference

RUNS = REPO_ROOT / "fig3" / "optimise" / "runs"
DEV_OUTPUTS = {  # final development-half label image written by each agent
    "nuclei": RUNS / "with_annotation_nuclei" / "artifacts" / "written_outside_sandbox" / "final.tif",
    "cancer": RUNS / "with_annotation_cancer" / "artifacts" / "out_final.tif",
    "endo": RUNS / "with_annotation_endothelial" / "artifacts" / "final.tif",
}


def score_dev(task: str, pred: np.ndarray) -> dict:
    """Score a prediction on the development (left) half with the same conventions as the held-out scorer."""
    gt = reference(task)[:, :HALF_X].copy()
    pred = np.squeeze(pred).astype(int)[:, :HALF_X]
    if task == "endo":
        gt, pred = clear_border(gt), clear_border(pred)
    if task == "nuclei":
        pred = drop_objects_on_cancer_cells(pred, cancer_mask()[:, :HALF_X])
    return _counts(gt, pred)


def main() -> None:
    """Re-score each agent's final development output and write optimise/dev_rescored.json."""
    out = {}
    for task, path in DEV_OUTPUTS.items():
        artifacts = next(parent for parent in path.parents if parent.name == "artifacts")
        reported = json.loads((artifacts / "reported.json").read_text())
        out[task] = {"reported_by_agent": reported.get("f1"), "our_scorer": score_dev(task, tifffile.imread(path))["f1"]}
        print(task, out[task])
    (REPO_ROOT / "fig3" / "optimise" / "dev_rescored.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
