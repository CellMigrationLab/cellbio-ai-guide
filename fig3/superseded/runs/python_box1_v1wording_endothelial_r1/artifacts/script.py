#!/usr/bin/env python
"""Segment endothelial cells in a single-channel 16-bit brightfield image with
Cellpose (v4 / Cellpose-SAM), then remove round refractile cancer cells and debris.

Outputs: labels.tif (uint32, same Y,X as input, 0 = background),
         labels_excluded.tif (removed objects, original label ids),
         areas.csv (kept objects, area in um^2), objects_all.csv (all objects + features).
"""
import argparse
import sys
from importlib.metadata import version

import numpy as np
import pandas as pd
import tifffile
from skimage.measure import regionprops
from skimage.segmentation import relabel_sequential


def load_image(path):
    img = tifffile.imread(path)
    validate_image(img)
    return img


def validate_image(img):
    if not isinstance(img, np.ndarray):
        raise TypeError("image must be a numpy array")
    if img.ndim != 2:
        raise ValueError(f"expected a single-channel 2D (Y, X) image, got shape {img.shape}")
    if min(img.shape) < 64:
        raise ValueError(f"image too small: {img.shape}")
    if not (np.issubdtype(img.dtype, np.integer) or np.issubdtype(img.dtype, np.floating)):
        raise TypeError(f"unsupported dtype {img.dtype}")
    if not np.isfinite(img).all():
        raise ValueError("image contains NaN/inf")
    if img.max() == img.min():
        raise ValueError("image is constant; nothing to segment")
    if img.dtype != np.uint16:
        print(f"WARNING: expected uint16, got {img.dtype}; data are passed unchanged.",
              file=sys.stderr)


def run_cellpose(img, diameter_px, flow_threshold, cellprob_threshold, min_size):
    import cellpose
    from cellpose import models
    ver = version("cellpose")
    if int(ver.split(".")[0]) < 4:
        raise RuntimeError(f"Cellpose >= 4 required (API differs), found {ver}")
    print(f"Cellpose {ver}, CPU", file=sys.stderr)
    model = models.CellposeModel(gpu=False)          # default pretrained model
    masks, flows, styles = model.eval(
        img,                                          # 2D array, unchanged
        diameter=diameter_px,                         # non-default: see docs table
        flow_threshold=flow_threshold,                # default 0.4
        cellprob_threshold=cellprob_threshold,        # default 0.0
        min_size=min_size,                            # default 15
        # normalize=True, resample=True are the defaults and are left as is
    )
    masks = np.asarray(masks)
    if masks.shape != img.shape:
        raise RuntimeError(f"mask shape {masks.shape} != image shape {img.shape}")
    return masks.astype(np.int64)


def classify(img, masks, pixel_um, min_area_um2, max_cancer_diam_um,
             min_aspect, min_solidity, min_contrast):
    g_lo, g_hi = np.percentile(img, [1, 99])
    g_range = float(g_hi - g_lo)
    if g_range <= 0:
        raise ValueError("image has zero intensity range between p1 and p99")
    rows = []
    for rp in regionprops(masks, intensity_image=img):
        vals = rp.image_intensity[rp.image]           # raw intensities inside object
        lo, hi = np.percentile(vals, [1, 99])
        area_um2 = rp.area * pixel_um ** 2
        diam_um = rp.equivalent_diameter_area * pixel_um
        aspect = rp.minor_axis_length / rp.major_axis_length if rp.major_axis_length > 0 else 0.0
        contrast = float(hi - lo) / g_range
        minr, minc, maxr, maxc = rp.bbox
        border = minr == 0 or minc == 0 or maxr == img.shape[0] or maxc == img.shape[1]
        if area_um2 < min_area_um2:
            reason = "debris_small"
        elif (diam_um <= max_cancer_diam_um and aspect >= min_aspect
              and rp.solidity >= min_solidity and contrast >= min_contrast):
            reason = "cancer_like"
        else:
            reason = ""
        rows.append(dict(cellpose_label=rp.label, area_px=int(rp.area), area_um2=area_um2,
                         equiv_diam_um=diam_um, aspect=aspect, solidity=rp.solidity,
                         contrast=contrast, touches_border=border,
                         centroid_y_px=rp.centroid[0], centroid_x_px=rp.centroid[1],
                         excluded_reason=reason, kept=(reason == "")))
    return pd.DataFrame(rows)


def segment(img, pixel_um=0.65, diameter_px=58.0, flow_threshold=0.4,
            cellprob_threshold=0.0, min_size=15, min_area_um2=150.0,
            max_cancer_diam_um=30.0, min_aspect=0.8, min_solidity=0.93,
            min_contrast=0.30):
    """Return (labels_kept, labels_excluded, table). Labels are in img's Y,X frame."""
    validate_image(img)
    if pixel_um <= 0 or diameter_px <= 0:
        raise ValueError("pixel_um and diameter_px must be > 0")
    masks = run_cellpose(img, diameter_px, flow_threshold, cellprob_threshold, min_size)
    table = classify(img, masks, pixel_um, min_area_um2, max_cancer_diam_um,
                     min_aspect, min_solidity, min_contrast)
    if len(table) == 0:
        return masks.astype(np.uint32), masks.astype(np.uint32), table
    keep_ids = table.loc[table.kept, "cellpose_label"].to_numpy()
    kept_mask = np.isin(masks, keep_ids)
    labels_kept, fw, _ = relabel_sequential(np.where(kept_mask, masks, 0))
    table["label"] = 0
    for old, new in zip(keep_ids, fw[keep_ids]):
        table.loc[table.cellpose_label == old, "label"] = int(new)
    excluded = np.where(kept_mask, 0, masks)
    return labels_kept.astype(np.uint32), excluded.astype(np.uint32), table


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--image", default="bf.tif")
    p.add_argument("--pixel-um", type=float, default=0.65)
    p.add_argument("--diameter-px", type=float, default=58.0)
    p.add_argument("--flow-threshold", type=float, default=0.4)
    p.add_argument("--cellprob-threshold", type=float, default=0.0)
    p.add_argument("--min-size", type=int, default=15)
    p.add_argument("--min-area-um2", type=float, default=150.0)
    p.add_argument("--max-cancer-diam-um", type=float, default=30.0)
    p.add_argument("--min-aspect", type=float, default=0.8)
    p.add_argument("--min-solidity", type=float, default=0.93)
    p.add_argument("--min-contrast", type=float, default=0.30)
    a = p.parse_args()

    img = load_image(a.image)
    labels, excluded, table = segment(
        img, a.pixel_um, a.diameter_px, a.flow_threshold, a.cellprob_threshold,
        a.min_size, a.min_area_um2, a.max_cancer_diam_um, a.min_aspect,
        a.min_solidity, a.min_contrast)
    assert labels.shape == img.shape
    tifffile.imwrite("labels.tif", labels)
    tifffile.imwrite("labels_excluded.tif", excluded)
    table.to_csv("objects_all.csv", index=False)
    kept = table[table.kept] if len(table) else table
    cols = ["label", "area_um2", "area_px", "touches_border"]
    (kept[cols] if len(kept) else pd.DataFrame(columns=cols)).to_csv("areas.csv", index=False)
    n_ex = len(table) - len(kept)
    print(f"Kept {len(kept)} endothelial objects; excluded {n_ex} "
          f"({(table.excluded_reason == 'cancer_like').sum() if len(table) else 0} cancer-like, "
          f"{(table.excluded_reason == 'debris_small').sum() if len(table) else 0} small debris).")
    if len(kept):
        print(f"Median area {kept.area_um2.median():.0f} um^2; "
              f"{int(kept.touches_border.sum())} touch the image border (area underestimated).")


if __name__ == "__main__":
    main()
