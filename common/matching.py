"""Object matching and object-level F1, shared by Figures 1-3.

Matching rule (identical to the code that produced the published scores):
every pair of overlapping objects (one reference, one predicted) is scored by intersection-over-union (IoU);
pairs are accepted greedily from the highest IoU downwards, one-to-one, keeping only IoU >= threshold.
F1 = 2 TP / (2 TP + FP + FN); F1 is 0 when there are no matches (including two empty images).
An IoU exactly equal to the threshold counts as a match. Labels do not overlap within an image, so for thresholds above
0.5 each object has at most one candidate partner and greedy matching equals optimal matching
(tests/test_matching_edge_cases.py). At thr = 0.5 a greedy pass can lose a tied maximum-cardinality solution; the edge
case test does not hit an exact tie, so prefer not to call at exactly 0.5 in new code.
"""
from __future__ import annotations

import numpy as np

from common.labels import validate_labels


def match(gt: np.ndarray, pr: np.ndarray, thr: float = 0.5) -> tuple[list[tuple[int, int, float]], set, set]:
    """Greedy one-to-one matching of two label images (0 = background).

    Returns (matched pairs [(gt_id, pred_id, iou)], unmatched reference ids (FN), unmatched predicted ids (FP)).
    """
    gt = validate_labels(gt, name="reference")
    pr = validate_labels(pr, name="prediction")
    if gt.shape != pr.shape:
        raise ValueError(f"Label images differ in shape: reference {gt.shape} vs prediction {pr.shape}")
    if not 0 < thr <= 1:
        raise ValueError(f"IoU threshold must be in (0, 1], got {thr}")
    m = (gt > 0) & (pr > 0)
    pairs: dict[tuple, int] = {}
    for g, p in zip(gt[m], pr[m]):
        pairs[(g, p)] = pairs.get((g, p), 0) + 1
    ga = dict(zip(*np.unique(gt[gt > 0], return_counts=True)))
    pa = dict(zip(*np.unique(pr[pr > 0], return_counts=True)))
    ious = sorted(((n / (ga[g] + pa[p] - n), g, p) for (g, p), n in pairs.items()), reverse=True)
    ug, up, matched = set(), set(), []
    for iou, g, p in ious:
        if iou >= thr and g not in ug and p not in up:
            ug.add(g)
            up.add(p)
            matched.append((g, p, iou))
    return matched, set(ga) - ug, set(pa) - up


def f1_score(gt: np.ndarray, pr: np.ndarray, thr: float = 0.5) -> dict:
    """Object-level counts and F1 (rounded to 3 decimals, as reported in the figures)."""
    matched, fn, fp = match(gt, pr, thr)
    tp = len(matched)
    f1 = 2 * tp / (2 * tp + len(fn) + len(fp)) if tp else 0.0
    return {"n_ref": tp + len(fn), "n_pred": tp + len(fp), "tp": tp, "fn": len(fn), "fp": len(fp), "f1": round(f1, 3)}
