#!/usr/bin/env python
"""Compare labels with a manual annotation (annot.tif): object counts, F1 at IoU>=0.5,
and save an outline overlay.  Usage: python test_segmentation.py bf.tif labels.tif annot.tif
"""
import sys

import numpy as np
import tifffile
from scipy.optimize import linear_sum_assignment
from skimage.segmentation import find_boundaries

IOU_THRESHOLD = 0.5  # a prediction matches if IoU >= this


def f1_score(pred, ref, thr=IOU_THRESHOLD):
    p_ids = np.unique(pred)[1:]
    r_ids = np.unique(ref)[1:]
    if len(p_ids) == 0 or len(r_ids) == 0:
        tp = 0
    else:
        p_idx = {v: i for i, v in enumerate(p_ids)}
        r_idx = {v: i for i, v in enumerate(r_ids)}
        inter = np.zeros((len(p_ids), len(r_ids)))
        both = (pred > 0) & (ref > 0)
        for a, b in zip(pred[both], ref[both]):
            inter[p_idx[a], r_idx[b]] += 1
        p_area = np.array([(pred == v).sum() for v in p_ids])
        r_area = np.array([(ref == v).sum() for v in r_ids])
        iou = inter / (p_area[:, None] + r_area[None, :] - inter)
        rows, cols = linear_sum_assignment(-iou)
        tp = int((iou[rows, cols] >= thr).sum())
    fp, fn = len(p_ids) - tp, len(r_ids) - tp
    f1 = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 1.0
    return len(p_ids), len(r_ids), tp, fp, fn, f1


def main(bf_path, labels_path, annot_path):
    img = tifffile.imread(bf_path)
    pred = tifffile.imread(labels_path)
    ref = tifffile.imread(annot_path)
    if not (img.shape == pred.shape == ref.shape) or img.ndim != 2:
        raise ValueError(f"Shapes must match and be 2D: image {img.shape}, "
                         f"labels {pred.shape}, annot {ref.shape}")

    n_pred, n_ref, tp, fp, fn, f1 = f1_score(pred, ref)
    print(f"Predicted objects: {n_pred}\nAnnotated objects: {n_ref}")
    print(f"IoU threshold {IOU_THRESHOLD}: TP={tp} FP={fp} FN={fn}  F1={f1:.3f}")

    # Overlay (display-only contrast stretch; does not touch the data)
    lo, hi = np.percentile(img, [1, 99])
    disp = np.clip((img.astype(float) - lo) / (hi - lo), 0, 1)
    rgb = np.dstack([disp] * 3)
    rgb[find_boundaries(pred, mode="outer")] = [1, 0, 0]   # prediction: red
    rgb[find_boundaries(ref, mode="outer") & ~find_boundaries(pred, mode="outer")] = [0, 1, 0]  # annotation: green
    tifffile.imwrite("overlay.tif", (rgb * 255).astype(np.uint8), photometric="rgb")
    print("Saved overlay.tif (red = prediction, green = annotation)")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
