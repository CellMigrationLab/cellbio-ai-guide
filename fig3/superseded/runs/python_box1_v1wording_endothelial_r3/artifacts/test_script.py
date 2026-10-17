#!/usr/bin/env python
"""Compare labels.tif with a manual annotation (annot.tif): counts, F1 at IoU 0.5, overlay.

Usage: python test_against_annotation.py bf.tif labels.tif annot.tif overlay.tif
"""
import argparse
import sys

import numpy as np
import tifffile
from scipy.optimize import linear_sum_assignment
from skimage.segmentation import find_boundaries


def iou_matrix(a, b):
    na, nb = int(a.max()), int(b.max())
    inter = np.zeros((na + 1, nb + 1), dtype=np.int64)
    np.add.at(inter, (a.ravel(), b.ravel()), 1)
    area_a, area_b = inter.sum(1), inter.sum(0)
    union = area_a[:, None] + area_b[None, :] - inter
    return (inter / np.maximum(union, 1))[1:, 1:]  # drop background row/col


def f1_score(pred, ref, iou_thr=0.5):
    n_pred, n_ref = len(np.unique(pred)) - (0 in pred), len(np.unique(ref)) - (0 in ref)
    if n_pred == 0 or n_ref == 0:
        return 0.0, 0, n_pred, n_ref
    iou = iou_matrix(pred, ref)
    r, c = linear_sum_assignment(-iou)
    tp = int((iou[r, c] >= iou_thr).sum())
    fp, fn = n_pred - tp, n_ref - tp
    return 2 * tp / (2 * tp + fp + fn), tp, n_pred, n_ref


def main():
    p = argparse.ArgumentParser()
    p.add_argument("image")
    p.add_argument("pred")
    p.add_argument("annot")
    p.add_argument("overlay", nargs="?", default="overlay.tif")
    p.add_argument("--iou", type=float, default=0.5)
    a = p.parse_args()

    img = tifffile.imread(a.image)
    pred = tifffile.imread(a.pred)
    ref = tifffile.imread(a.annot)
    for name, arr in (("labels", pred), ("annot", ref)):
        if arr.shape != img.shape:
            sys.exit(f"ERROR: {name} shape {arr.shape} != image shape {img.shape}")
        if arr.min() < 0 or not np.issubdtype(arr.dtype, np.integer):
            sys.exit(f"ERROR: {name} must be an integer label image with values >= 0")
    # Relabel so each connected id is one object; ids must be compact for the matrix
    pred = np.unique(pred, return_inverse=True)[1].reshape(pred.shape) if pred.max() else pred
    ref = np.unique(ref, return_inverse=True)[1].reshape(ref.shape) if ref.max() else ref
    if (pred.max() and 0 not in pred) or (ref.max() and 0 not in ref):
        pass  # no background pixels; unusual but allowed

    f1, tp, n_pred, n_ref = f1_score(pred.astype(np.int64), ref.astype(np.int64), a.iou)
    print(f"Predicted objects: {n_pred}\nAnnotated objects: {n_ref}\n"
          f"TP={tp} FP={n_pred - tp} FN={n_ref - tp}\nF1 @ IoU {a.iou}: {f1:.3f}")

    # Overlay: display-only contrast stretch (1-99 pct); no effect on segmentation
    lo, hi = np.percentile(img, (1, 99))
    disp = np.clip((img.astype(float) - lo) / max(hi - lo, 1), 0, 1)
    rgb = np.stack([disp] * 3, -1)
    rgb[find_boundaries(ref, mode="inner")] = (0, 1, 0)    # annotation: green
    rgb[find_boundaries(pred, mode="inner")] = (1, 0, 0)   # prediction: red
    tifffile.imwrite(a.overlay, (rgb * 255).astype(np.uint8))
    print(f"Saved overlay (red = prediction, green = annotation): {a.overlay}")


if __name__ == "__main__":
    main()
