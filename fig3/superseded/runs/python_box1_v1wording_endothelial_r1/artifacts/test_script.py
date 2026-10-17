#!/usr/bin/env python
"""Compare segmentation with a manual annotation (annot.tif) and save an outline overlay."""
import argparse
import numpy as np
import tifffile
from scipy.optimize import linear_sum_assignment
from skimage.io import imsave
from skimage.segmentation import find_boundaries

from segment_endothelial import load_image, segment


def iou_matrix(pred, gt):
    npred, ngt = int(pred.max()), int(gt.max())
    inter = np.zeros((npred + 1, ngt + 1), dtype=np.int64)
    both = (pred > 0) & (gt > 0)
    pairs, counts = np.unique(np.stack([pred[both], gt[both]]), axis=1, return_counts=True)
    inter[pairs[0], pairs[1]] = counts
    ap = np.bincount(pred.ravel(), minlength=npred + 1)
    ag = np.bincount(gt.ravel(), minlength=ngt + 1)
    union = ap[:, None] + ag[None, :] - inter
    iou = inter / np.maximum(union, 1)
    return iou[1:, 1:]


def f1_at(iou, thr):
    npred, ngt = iou.shape
    if npred == 0 or ngt == 0:
        tp = 0
    else:
        r, c = linear_sum_assignment(-iou)
        tp = int((iou[r, c] >= thr).sum())
    fp, fn = npred - tp, ngt - tp
    denom = 2 * tp + fp + fn
    return tp, fp, fn, (2 * tp / denom if denom else 1.0)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--image", default="bf.tif")
    p.add_argument("--annot", default="annot.tif")
    p.add_argument("--overlay", default="overlay.png")
    a = p.parse_args()

    img = load_image(a.image)
    gt = tifffile.imread(a.annot)
    if gt.shape != img.shape:
        raise ValueError(f"annot shape {gt.shape} != image shape {img.shape}")
    if not np.issubdtype(gt.dtype, np.integer) or gt.min() < 0:
        raise ValueError("annot.tif must be a non-negative integer label image")
    _, gt = np.unique(gt, return_inverse=True)   # make ids consecutive (0 stays background)
    gt = gt.reshape(img.shape).astype(np.int64)

    pred, _, _ = segment(img)                    # same defaults as the main script
    pred = pred.astype(np.int64)
    iou = iou_matrix(pred, gt)
    print(f"Object count: predicted {int(pred.max())}, annotated {int(gt.max())}")
    for thr in (0.5, 0.75):
        tp, fp, fn, f1 = f1_at(iou, thr)
        print(f"IoU>={thr}: TP={tp} FP={fp} FN={fn} F1={f1:.3f}")

    # overlay (display-only contrast stretch; data themselves are unchanged)
    lo, hi = np.percentile(img, [1, 99])
    disp = np.clip((img.astype(float) - lo) / max(hi - lo, 1e-9), 0, 1)
    rgb = np.stack([disp] * 3, -1)
    rgb[find_boundaries(gt, mode="inner")] = (0, 1, 0)      # annotation: green
    rgb[find_boundaries(pred, mode="inner")] = (1, 0, 0)    # prediction: red
    imsave(a.overlay, (rgb * 255).astype(np.uint8), check_contrast=False)
    print(f"Overlay saved to {a.overlay} (red = prediction, green = annotation)")


if __name__ == "__main__":
    main()
