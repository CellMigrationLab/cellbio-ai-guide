"""The three Figure 3 tasks: references and scoring conventions, for field 104 (development) and field 209 (test).

* nuclei      reference: all manually annotated endothelial nuclei (DAPI; 441 in field 104, 473 in field 209). Predictions are matched to the full
              manual reference first; only predicted objects left UNMATCHED and lying >30 % on annotated cancer cells
              are then ignored, because cancer-cell nuclei were not annotated (rule "match_first", used from round 2).
              Round 1 used rule "drop_first" (drop such objects before matching), which also discarded correct
              predictions of the 17 annotated nuclei under cancer cells (best F1 0.98); kept only to reproduce round 1.
* cancer      reference: manually annotated cancer cells (brightfield; 124 in field 104, 163 in field 209).
* endo        reference: endothelial cells from annotator 1's junction lines (lines_to_cells); objects touching the image
              border are removed from reference and prediction.
All: object F1 at IoU >= 0.5, greedy one-to-one matching (common.matching).
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np
import tifffile
from skimage.segmentation import clear_border

from common.annotations import lines_to_cells
from common.matching import match
from common.paths import raw_file
from common.labels import read_labels
from common.labels import validate_labels

TASKS = ("nuclei", "cancer", "endo")
FIELDS = (104, 209)  # 104: development field (round 1 and figures); 209: test field (round 2)
HALF_X = 512  # round 1 only: development half x < 512, held-out half x >= 512 of field 104 (row c)
CANCER_OVERLAP_MAX = 0.3


@lru_cache(maxsize=None)
def reference(task: str, field: int = 104) -> np.ndarray:
    """Manual reference label image for a task and field (whole field), read from the authors' annotations."""
    if field not in FIELDS:
        raise ValueError(f"Unknown field {field!r}; expected one of {FIELDS}")
    f = f"field{field}"
    if task == "nuclei":
        return read_labels(raw_file(f"{f}_endothelial_nuclei_manual_labels.tif"))
    if task == "cancer":
        return read_labels(raw_file(f"{f}_cancer_cells_manual_labels.tif"))
    if task == "endo":
        return lines_to_cells(tifffile.imread(raw_file(f"{f}_endothelial_junctions_annotator1.tif")) > 0)
    raise ValueError(f"Unknown task {task!r}; expected one of {TASKS}")


@lru_cache(maxsize=None)
def cancer_mask(field: int = 104) -> np.ndarray:
    """Boolean mask of the annotated cancer cells of a field (used to ignore cancer-cell nuclei)."""
    return reference("cancer", field) > 0


def drop_objects_on_cancer_cells(pred: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Remove predicted objects lying more than CANCER_OVERLAP_MAX of their area on annotated cancer cells."""
    pred = pred.copy()
    ids, counts = np.unique(pred[pred > 0], return_counts=True)
    on_cancer = dict(zip(*np.unique(pred[(pred > 0) & mask], return_counts=True)))
    pred[np.isin(pred, [i for i, n in zip(ids, counts) if on_cancer.get(i, 0) > CANCER_OVERLAP_MAX * n])] = 0
    return pred


def unmatched_on_cancer_cells(pred: np.ndarray, ids: set, mask: np.ndarray) -> set:
    """Of the predicted object ids given, those lying more than CANCER_OVERLAP_MAX of their area on cancer cells."""
    if not ids:
        return set()
    sizes = dict(zip(*np.unique(pred[pred > 0], return_counts=True)))
    on_cancer = dict(zip(*np.unique(pred[(pred > 0) & mask], return_counts=True)))
    return {i for i in ids if on_cancer.get(i, 0) > CANCER_OVERLAP_MAX * sizes[i]}


def _counts(gt: np.ndarray, pred: np.ndarray, ignore_unmatched_on: np.ndarray | None = None) -> dict:
    """Counts, F1 and median matched area ratio (prediction / reference) for two prepared label images.

    ignore_unmatched_on: optional mask; unmatched predictions lying mostly on it are not counted as false positives
    (and not counted in n_pred).
    """
    matched, fn, fp = match(gt, pred, 0.5)
    if ignore_unmatched_on is not None:
        ignored = unmatched_on_cancer_cells(pred, set(fp), ignore_unmatched_on)
        fp = set(fp) - ignored
        pred = np.where(np.isin(pred, list(ignored)), 0, pred)
    tp = len(matched)
    out = {"n_pred": int(len(np.unique(pred[pred > 0]))), "n_ref": int(len(np.unique(gt[gt > 0]))),
           "tp": tp, "fn": len(fn), "fp": len(fp),
           "f1": round(2 * tp / (2 * tp + len(fn) + len(fp)), 3) if (tp + len(fn) + len(fp)) else 0.0}
    if matched:
        ratios = [(pred == p).sum() / (gt == g).sum() for g, p, _ in matched]
        out["area_ratio_median"] = round(float(np.median(ratios)), 3)
    return out


def score(task: str, pred: np.ndarray, nuclei_rule: str = "match_first", field: int = 104) -> dict:
    """Whole-field score of a predicted label image for one task and field (nuclei_rule: see module docstring)."""
    pred = validate_labels(pred, name=f"{task} prediction", squeeze=True)
    gt = reference(task, field)
    if pred.shape != gt.shape:
        raise ValueError(f"{task}: prediction shape {pred.shape} differs from reference {gt.shape}")
    if task == "endo":
        pred = clear_border(pred)
    if task == "nuclei":
        return _nuclei_counts(gt, pred, cancer_mask(field), nuclei_rule)
    return _counts(gt, pred)


def _nuclei_counts(gt: np.ndarray, pred: np.ndarray, mask: np.ndarray, rule: str) -> dict:
    """Nuclei scoring under the given rule ("match_first" from round 2; "drop_first" reproduces round 1)."""
    if rule == "match_first":
        return _counts(gt, pred, ignore_unmatched_on=mask)
    if rule == "drop_first":
        return _counts(gt, drop_objects_on_cancer_cells(pred, mask))
    raise ValueError(f"Unknown nuclei rule {rule!r}; expected 'match_first' or 'drop_first'")


def score_heldout(task: str, pred: np.ndarray, nuclei_rule: str = "match_first", field: int = 104) -> dict:
    """Score on the held-out right half (x >= HALF_X) of a field. Accepts a whole-field or a half-width prediction.
    Round 1 used field 104 only (default); protocol v2 scores the right halves of fields 104 and 209."""
    pred = validate_labels(pred, name=f"{task} prediction", squeeze=True)
    gt = heldout_reference(task, field)
    pred = pred[:, HALF_X:].copy() if pred.shape[1] == gt.shape[1] + HALF_X else pred.copy()
    if pred.shape != gt.shape:
        raise ValueError(f"{task}: held-out prediction shape {pred.shape} differs from {gt.shape}")
    if task == "endo":
        gt, pred = clear_border(gt), clear_border(pred)
    if task == "nuclei":
        return _nuclei_counts(gt, pred, cancer_mask(field)[:, HALF_X:], nuclei_rule)
    return _counts(gt, pred)


def heldout_reference(task: str, field: int = 104) -> np.ndarray:
    """Manual reference of the held-out right half (x >= HALF_X) of a field (objects cut by the crop stay cut)."""
    return reference(task, field)[:, HALF_X:].copy()
