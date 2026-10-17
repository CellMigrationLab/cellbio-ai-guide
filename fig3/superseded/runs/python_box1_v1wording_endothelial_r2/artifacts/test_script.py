#!/usr/bin/env python
"""Compare segmentation with a manual annotation (annot.tif) and save an overlay.

Usage: python test_segmentation.py bf.tif annot.tif --out-dir test_out
Extra segmentation parameters can be changed in the call to segment_endothelial.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import tifffile
from skimage.io import imsave
from skimage.segmentation import find_boundaries

from segment_endothelial import load_image, segment_endothelial


def f1_at_iou(pred, gt, thr=0.5):
    """Object-level F1; a match needs IoU > thr (so matches are unique)."""
    p_ids = np.unique(pred[pred > 0])
    g_ids = np.unique(gt[gt > 0])
    if len(p_ids) == 0 or len(g_ids) == 0:
        return 0.0, 0, len(p_ids), len(g_ids)
    both = (pred > 0) & (gt > 0)
    pairs, inter = np.unique(
        np.stack([pred[both], gt[both]], 1), axis=0, return_counts=True)
    p_area = dict(zip(*np.unique(pred[pred > 0], return_counts=True)))
    g_area = dict(zip(*np.unique(gt[gt > 0], return_counts=True)))
    tp = 0
    for (pi, gi), n in zip(pairs, inter):
        iou = n / (p_area[pi] + g_area[gi] - n)
        if iou > thr:
            tp += 1
    fp, fn = len(p_ids) - tp, len(g_ids) - tp
    f1 = 2 * tp / (2 * tp + fp + fn)
    return f1, tp, len(p_ids), len(g_ids)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("annot")
    ap.add_argument("--out-dir", default="test_out")
    ap.add_argument("--pixel-size", type=float, default=0.65)
    ap.add_argument("--iou", type=float, default=0.5)
    a = ap.parse_args()

    try:
        img = load_image(a.image)
        gt = tifffile.imread(a.annot)
        if gt.shape != img.shape:
            raise ValueError(
                f"annot.tif shape {gt.shape} != image shape {img.shape}.")
        if not np.issubdtype(gt.dtype, np.integer):
            raise ValueError(f"annot.tif must be an integer label image; got {gt.dtype}.")
        pred, info = segment_endothelial(img, pixel_size_um=a.pixel_size)
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    f1, tp, n_pred, n_gt = f1_at_iou(pred, gt, a.iou)
    print(f"Predicted objects: {n_pred}   Annotated objects: {n_gt}")
    print(f"TP={tp} FP={n_pred - tp} FN={n_gt - tp}   F1 (IoU>{a.iou}) = {f1:.3f}")
    print(info)

    # Overlay (display only: the contrast stretch is NOT used for segmentation)
    lo, hi = np.percentile(img, (1, 99))
    disp = np.clip((img.astype(float) - lo) / max(hi - lo, 1), 0, 1)
    rgb = np.dstack([disp] * 3)
    rgb[find_boundaries(pred, mode="inner")] = [1, 0, 0]    # prediction: red
    rgb[find_boundaries(gt, mode="inner")] = [0, 1, 0]      # annotation: green
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    imsave(out / "overlay.png", (rgb * 255).astype(np.uint8), check_contrast=False)
    print(f"Saved {out / 'overlay.png'} (red = prediction, green = annotation)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
