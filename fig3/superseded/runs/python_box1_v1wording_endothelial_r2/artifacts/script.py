#!/usr/bin/env python
"""Segment endothelial cells in a single-channel 16-bit 2D brightfield image
with Cellpose (Cellpose-SAM, v4), remove round cancer cells by shape, and
write labels.tif and areas.csv (areas in um^2).

Usage: python segment_endothelial.py bf.tif --out-dir .
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile
from skimage.measure import regionprops
from skimage.segmentation import relabel_sequential


def load_image(path):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Input image not found: {path}")
    img = tifffile.imread(path)
    if img.ndim != 2:
        raise ValueError(
            f"Expected a single-channel 2D image (Y, X); got shape {img.shape}.")
    if img.dtype != np.uint16:
        raise ValueError(f"Expected 16-bit unsigned (uint16); got {img.dtype}.")
    if min(img.shape) < 64:
        raise ValueError(f"Image too small: {img.shape}.")
    if img.min() == img.max():
        raise ValueError("Image is constant; nothing to segment.")
    return img


def segment_endothelial(
    img,
    pixel_size_um=0.65,
    model_name="cpsam",          # NOT verified as library default; see notes
    diameter=None,               # library default: no rescaling
    flow_threshold=0.4,          # library default
    cellprob_threshold=0.0,      # library default
    min_size=15,                 # library default (pixels)
    normalize=True,              # library default (1-99 percentile)
    resample=True,               # library default
    min_diameter_um=15.0,        # mine: debris removal
    cancer_filter=True,          # mine: shape/size heuristic
    cancer_max_diameter_um=28.0,
    cancer_min_solidity=0.90,
    cancer_max_eccentricity=0.6,
):
    """Return (labels, info). labels is uint32, same shape as img (no resizing)."""
    if img.ndim != 2 or img.dtype != np.uint16:
        raise ValueError("img must be a 2D uint16 array.")
    if not pixel_size_um > 0:
        raise ValueError("pixel_size_um must be > 0.")
    if diameter is not None and not diameter > 0:
        raise ValueError("diameter must be None or > 0 (pixels).")

    from cellpose import models  # imported here so --help works without it

    model = models.CellposeModel(gpu=False, pretrained_model=model_name)
    out = model.eval(
        img,
        diameter=diameter,
        flow_threshold=flow_threshold,
        cellprob_threshold=cellprob_threshold,
        min_size=min_size,
        normalize=normalize,
        resample=resample,
    )
    masks = out[0]
    if isinstance(masks, (list, tuple)):
        masks = masks[0]
    masks = np.asarray(masks)
    if masks.shape != img.shape:
        raise RuntimeError(
            f"Cellpose returned shape {masks.shape}, expected {img.shape}.")

    n_raw = int(masks.max())
    labels = masks.astype(np.uint32)
    removed_small = removed_round = 0
    for rp in regionprops(labels):
        d_um = rp.equivalent_diameter_area * pixel_size_um
        if d_um < min_diameter_um:
            labels[labels == rp.label] = 0
            removed_small += 1
        elif (cancer_filter and d_um <= cancer_max_diameter_um
              and rp.solidity >= cancer_min_solidity
              and rp.eccentricity <= cancer_max_eccentricity):
            labels[labels == rp.label] = 0
            removed_round += 1
    labels, _, _ = relabel_sequential(labels)
    labels = labels.astype(np.uint32)
    info = dict(n_cellpose=n_raw, removed_small=removed_small,
                removed_round=removed_round, n_final=int(labels.max()))
    return labels, info


def measure(labels, pixel_size_um):
    h, w = labels.shape
    rows = []
    for rp in regionprops(labels):
        r0, c0, r1, c1 = rp.bbox
        rows.append(dict(
            label=rp.label,
            area_px=int(rp.area),
            area_um2=float(rp.area) * pixel_size_um ** 2,
            equiv_diameter_um=rp.equivalent_diameter_area * pixel_size_um,
            solidity=rp.solidity,
            centroid_y_px=rp.centroid[0],
            centroid_x_px=rp.centroid[1],
            touches_border=bool(r0 == 0 or c0 == 0 or r1 == h or c1 == w),
        ))
    return pd.DataFrame(rows)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("image", nargs="?", default="bf.tif")
    p.add_argument("--out-dir", default=".")
    p.add_argument("--pixel-size", type=float, default=0.65, help="um per pixel")
    p.add_argument("--model", default="cpsam")
    p.add_argument("--diameter", type=float, default=None,
                   help="pixels; default None = no rescaling")
    p.add_argument("--flow-threshold", type=float, default=0.4)
    p.add_argument("--cellprob-threshold", type=float, default=0.0)
    p.add_argument("--min-size", type=int, default=15)
    p.add_argument("--min-diameter-um", type=float, default=15.0)
    p.add_argument("--no-cancer-filter", action="store_true")
    p.add_argument("--cancer-max-diameter-um", type=float, default=28.0)
    p.add_argument("--cancer-min-solidity", type=float, default=0.90)
    p.add_argument("--cancer-max-eccentricity", type=float, default=0.6)
    a = p.parse_args(argv)

    try:
        img = load_image(a.image)
        labels, info = segment_endothelial(
            img, pixel_size_um=a.pixel_size, model_name=a.model,
            diameter=a.diameter, flow_threshold=a.flow_threshold,
            cellprob_threshold=a.cellprob_threshold, min_size=a.min_size,
            min_diameter_um=a.min_diameter_um,
            cancer_filter=not a.no_cancer_filter,
            cancer_max_diameter_um=a.cancer_max_diameter_um,
            cancer_min_solidity=a.cancer_min_solidity,
            cancer_max_eccentricity=a.cancer_max_eccentricity)
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    tifffile.imwrite(out / "labels.tif", labels)
    df = measure(labels, a.pixel_size)
    df.to_csv(out / "areas.csv", index=False)
    print(info)
    if len(df):
        print(f"Median area: {df.area_um2.median():.0f} um^2 "
              f"({df.touches_border.sum()} cells touch the border)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
