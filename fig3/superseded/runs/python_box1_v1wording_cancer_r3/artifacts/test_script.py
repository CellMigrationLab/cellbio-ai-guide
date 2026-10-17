#!/usr/bin/env python
"""Compare labels.tif with a manual annotation (annot.tif); report counts and F1; save overlay."""
import argparse
import sys

import numpy as np
import tifffile
from scipy.optimize import linear_sum_assignment
from skimage import io
from skimage.segmentation import find_boundaries


def f1_score(pred, true, iou_thr=0.5):
    p_ids = np.unique(pred[pred > 0])
    t_ids = np.unique(true[true > 0])
    if len(p_ids) == 0 or len(t_ids) == 0:
        tp = 0
    else:
        pi = np.searchsorted(p_ids, pred.ravel())
        ti = np.searchsorted(t_ids, true.ravel())
        both = (pred.ravel() > 0) & (true.ravel() > 0)
        inter = np.zeros((len(p_ids), len(t_ids)))
        np.add.at(inter, (pi[both], ti[both]), 1)
        pa = np.bincount(pred.ravel())[p_ids][:, None]
        ta = np.bincount(true.ravel())[t_ids][None, :]
        iou = inter / (pa + ta - inter)
        r, c = linear_sum_assignment(-iou)
        tp = int((iou[r, c] >= iou_thr).sum())
    fp, fn = len(p_ids) - tp, len(t_ids) - tp
    f1 = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 1.0
    return dict(n_pred=len(p_ids), n_true=len(t_ids), tp=tp, fp=fp, fn=fn, f1=f1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", default="bf.tif")
    ap.add_argument("--labels", default="labels.tif")
    ap.add_argument("--annot", default="annot.tif")
    ap.add_argument("--overlay", default="overlay.png")
    ap.add_argument("--iou", type=float, default=0.5)
    a = ap.parse_args()

    img = tifffile.imread(a.image)
    pred = tifffile.imread(a.labels)
    true = tifffile.imread(a.annot)
    if not (img.shape == pred.shape == true.shape and img.ndim == 2):
        sys.exit(f"ERROR: shapes differ or not 2D: image {img.shape}, labels {pred.shape}, "
                 f"annot {true.shape}")
    for name, arr in (("labels", pred), ("annot", true)):
        if not np.issubdtype(arr.dtype, np.integer):
            sys.exit(f"ERROR: {name} must be an integer label image, got {arr.dtype}")
    pred = pred.astype(np.int64)
    true = true.astype(np.int64)

    res = f1_score(pred, true, a.iou)
    print(f"predicted objects: {res['n_pred']}  annotated objects: {res['n_true']}")
    print(f"IoU>={a.iou}: TP={res['tp']} FP={res['fp']} FN={res['fn']}  F1={res['f1']:.3f}")

    # Display-only contrast stretch (1-99 percentile); does not affect any measurement.
    lo, hi = np.percentile(img, (1, 99))
    disp = np.clip((img.astype(float) - lo) / max(hi - lo, 1e-9), 0, 1)
    rgb = np.dstack([disp] * 3)
    rgb[find_boundaries(true, mode="outer")] = (0, 1, 0)   # annotation: green
    rgb[find_boundaries(pred, mode="outer")] = (1, 0, 0)   # prediction: red
    io.imsave(a.overlay, (rgb * 255).astype(np.uint8), check_contrast=False)
    print(f"overlay saved to {a.overlay} (red = prediction, green = annotation)")


if __name__ == "__main__":
    main()
