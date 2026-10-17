"""The three Figure 3 tasks: references and scoring conventions (same rules as the code that produced the figure).

* nuclei      reference: 441 manually annotated endothelial nuclei (DAPI). Predicted objects lying >30 % on annotated
              cancer cells are ignored, because cancer-cell nuclei are not annotated. This also drops the 17 annotated
              nuclei lying under cancer cells, so the best achievable F1 is 0.98 (held-out half 0.983).
* cancer      reference: 124 manually annotated cancer cells (brightfield).
* endo        reference: endothelial cells from annotator 1's junction lines (lines_to_cells); objects touching the image
              border are removed from reference and prediction.
All: object F1 at IoU >= 0.5, greedy one-to-one matching (common.matching).
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np
import tifffile
from skimage.measure import label
from skimage.segmentation import clear_border, expand_labels

from common.matching import match
from common.paths import raw_file

TASKS = ("nuclei", "cancer", "endo")
HALF_X = 512  # development half x < 512, held-out half x >= 512 (row c)
CANCER_OVERLAP_MAX = 0.3
SLIVER_PX = 150


def lines_to_cells(lines: np.ndarray) -> np.ndarray:
    """Convert drawn junction lines (True on lines) to a label image of complete cells."""
    lab = expand_labels(label(~lines, connectivity=1), 2)
    lab = clear_border(lab)
    sizes = np.bincount(lab.ravel())
    lab[np.isin(lab, np.where(sizes < SLIVER_PX)[0])] = 0
    return lab


@lru_cache(maxsize=None)
def reference(task: str) -> np.ndarray:
    """Manual reference label image for a task (whole field)."""
    if task == "nuclei":
        return tifffile.imread(raw_file("field104_endothelial_nuclei_manual_labels.tif")).astype(int)
    if task == "cancer":
        return tifffile.imread(raw_file("field104_cancer_cells_manual_labels.tif")).astype(int)
    if task == "endo":
        return lines_to_cells(tifffile.imread(raw_file("field104_endothelial_junctions_annotator1.tif")) > 0)
    raise ValueError(f"Unknown task {task!r}; expected one of {TASKS}")


@lru_cache(maxsize=None)
def cancer_mask() -> np.ndarray:
    """Boolean mask of the annotated cancer cells (used to ignore cancer-cell nuclei)."""
    return reference("cancer") > 0


def drop_objects_on_cancer_cells(pred: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Remove predicted objects lying more than CANCER_OVERLAP_MAX of their area on annotated cancer cells."""
    pred = pred.copy()
    ids, counts = np.unique(pred[pred > 0], return_counts=True)
    on_cancer = dict(zip(*np.unique(pred[(pred > 0) & mask], return_counts=True)))
    pred[np.isin(pred, [i for i, n in zip(ids, counts) if on_cancer.get(i, 0) > CANCER_OVERLAP_MAX * n])] = 0
    return pred


def _counts(gt: np.ndarray, pred: np.ndarray) -> dict:
    """Counts, F1 and median matched area ratio (prediction / reference) for two prepared label images."""
    matched, fn, fp = match(gt, pred, 0.5)
    tp = len(matched)
    out = {"n_pred": int(len(np.unique(pred[pred > 0]))), "n_ref": int(len(np.unique(gt[gt > 0]))),
           "tp": tp, "fn": len(fn), "fp": len(fp),
           "f1": round(2 * tp / (2 * tp + len(fn) + len(fp)), 3) if (tp + len(fn) + len(fp)) else 0.0}
    if matched:
        ratios = [(pred == p).sum() / (gt == g).sum() for g, p, _ in matched]
        out["area_ratio_median"] = round(float(np.median(ratios)), 3)
    return out


def score(task: str, pred: np.ndarray) -> dict:
    """Whole-field score of a predicted label image for one task."""
    pred = np.squeeze(pred).astype(int)
    gt = reference(task)
    if pred.shape != gt.shape:
        raise ValueError(f"{task}: prediction shape {pred.shape} differs from reference {gt.shape}")
    if task == "nuclei":
        pred = drop_objects_on_cancer_cells(pred, cancer_mask())
    if task == "endo":
        pred = clear_border(pred)
    return _counts(gt, pred)


def score_heldout(task: str, pred: np.ndarray) -> dict:
    """Score on the held-out right half (row c). Accepts a whole-field or a half-width prediction."""
    pred = np.squeeze(pred).astype(int)
    gt = reference(task)[:, HALF_X:].copy()
    pred = pred[:, HALF_X:].copy() if pred.shape[1] == gt.shape[1] + HALF_X else pred.copy()
    if pred.shape != gt.shape:
        raise ValueError(f"{task}: held-out prediction shape {pred.shape} differs from {gt.shape}")
    if task == "endo":
        gt, pred = clear_border(gt), clear_border(pred)
    if task == "nuclei":
        pred = drop_objects_on_cancer_cells(pred, cancer_mask()[:, HALF_X:])
    return _counts(gt, pred)
