#!/usr/bin/env python3
"""Compare labels.tif with a manual annotation: object counts, F1 at IoU>=0.5, outline overlay.

Usage: python test_seg.py bf.tif labels.tif annot.tif [--iou 0.5]
Output: overlay.tif (RGB; red = prediction outlines, green = annotation outlines).
"""
import argparse

import numpy as np
import tifffile
from scipy.optimize import linear_sum_assignment
from skimage.segmentation import find_boundaries


def iou_matrix(gt, pred):
    n_gt, n_pr = int(gt.max()), int(pred.max())
    inter = np.zeros((n_gt + 1, n_pr + 1), dtype=np.int64)
    np.add.at(inter, (gt.ravel(), pred.ravel()), 1)
    a_gt = inter.sum(1, keepdims=True)
    a_pr = inter.sum(0, keepdims=True)
    union = a_gt + a_pr - inter
    with np.errstate(divide="ignore", invalid="ignore"):
        iou = np.where(union > 0, inter / union, 0.0)
    return iou[1:, 1:]  # drop background


def main():
    p = argparse.ArgumentParser()
    p.add_argument("image")
    p.add_argument("labels")
    p.add_argument("annot")
    p.add_argument("--iou", type=float, default=0.5)
    p.add_argument("--out", default="overlay.tif")
    a = p.parse_args()

    img = tifffile.imread(a.image)
    pred = tifffile.imread(a.labels).astype(np.int64)
    gt = tifffile.imread(a.annot).astype(np.int64)
    if not (img.shape == pred.shape == gt.shape) or img.ndim != 2:
        raise ValueError(f"Shapes must match and be 2D: image {img.shape}, "
                         f"labels {pred.shape}, annot {gt.shape}.")
    if pred.min() < 0 or gt.min() < 0:
        raise ValueError("Label images must be non-negative.")

    n_gt, n_pr = len(np.unique(gt)) - (0 in gt), len(np.unique(pred)) - (0 in pred)
    # Use the number of distinct labels (not max) in case labels are not sequential.
    _, gt = np.unique(gt, return_inverse=True); gt = gt.reshape(img.shape)
    _, pred = np.unique(pred, return_inverse=True); pred = pred.reshape(img.shape)
    if 0 in np.unique(tifffile.imread(a.annot)):
        pass  # background stays 0 after unique-remap because 0 is the smallest value
    else:
        gt += 1; pred += 0  # annotation without background: unusual, flagged below
        print("WARNING: annot.tif contains no background (0) pixels.")

    tp = fp = fn = 0
    if n_gt and n_pr:
        iou = iou_matrix(gt, pred)
        r, c = linear_sum_assignment(-iou)
        tp = int((iou[r, c] >= a.iou).sum())
    fp, fn = n_pr - tp, n_gt - tp
    f1 = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else float("nan")

    print(f"Annotated objects: {n_gt}\nPredicted objects: {n_pr}")
    print(f"IoU threshold {a.iou}: TP={tp} FP={fp} FN={fn}  F1={f1:.3f}")

    lo, hi = np.percentile(img, (1, 99))
    g = np.clip((img.astype(float) - lo) / max(hi - lo, 1e-9), 0, 1)
    rgb = np.stack([g, g, g], -1)
    rgb[find_boundaries(gt, mode="inner") & (gt > 0)] = (0, 1, 0)
    rgb[find_boundaries(pred, mode="inner") & (pred > 0)] = (1, 0, 0)
    tifffile.imwrite(a.out, (rgb * 255).astype(np.uint8), photometric="rgb")
    print(f"Saved {a.out} (red = prediction, green = annotation)")


if __name__ == "__main__":
    main()
