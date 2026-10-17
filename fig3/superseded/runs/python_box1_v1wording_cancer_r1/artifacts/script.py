#!/usr/bin/env python
"""Segment round refractile cancer cells in a 16-bit brightfield image with Cellpose 4.

Usage: python segment_cancer.py bf.tif --out-labels labels.tif --out-csv areas.csv
Output labels have the same (Y, X) shape as the input; no resizing is done
(diameter=None, rescale=None). Areas are in um^2.
"""
import argparse
import importlib.metadata
import os
import sys
import warnings

import numpy as np
import pandas as pd
import tifffile
from skimage.measure import regionprops
from skimage.segmentation import relabel_sequential

EXPECTED_CELLPOSE = "4.2.1.1"


def load_image(path):
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Input file not found: {path}")
    img = tifffile.imread(path)
    if img.ndim != 2:
        raise ValueError(f"Expected a single-channel 2D (Y, X) image, got shape {img.shape}")
    if img.dtype != np.uint16:
        raise ValueError(f"Expected 16-bit unsigned (uint16) image, got dtype {img.dtype}")
    if min(img.shape) < 64:
        raise ValueError(f"Image too small: {img.shape}")
    if img.max() == img.min():
        raise ValueError("Image is constant; nothing to segment.")
    return img


def segment_cancer_cells(
    image,
    pixel_size_um=0.65,
    # --- Cellpose parameters (library defaults unless noted) ---
    pretrained_model=None,       # None -> library default model
    diameter=None,               # None -> no internal rescaling (cpsam is size-invariant)
    flow_threshold=0.4,          # library default
    cellprob_threshold=0.0,      # library default
    min_size=15,                 # library default (pixels)
    normalize=True,              # library default (1-99 percentile)
    # --- post-filters (NOT library defaults; tune on real data) ---
    min_area_um2=78.0,           # ~10 um diameter
    max_area_um2=962.0,          # ~35 um diameter
    min_contrast=0.25,           # refractile-contrast threshold to reject endothelium
):
    if not (np.isfinite(pixel_size_um) and pixel_size_um > 0):
        raise ValueError("pixel_size_um must be a positive number")
    if min_area_um2 >= max_area_um2:
        raise ValueError("min_area_um2 must be < max_area_um2")
    if image.ndim != 2 or image.dtype != np.uint16:
        raise ValueError("image must be a 2D uint16 array")

    try:
        ver = importlib.metadata.version("cellpose")
    except importlib.metadata.PackageNotFoundError:
        raise ImportError("cellpose is not installed")
    if ver != EXPECTED_CELLPOSE:
        warnings.warn(f"Cellpose {ver} installed, script written for {EXPECTED_CELLPOSE}")

    from cellpose import models

    kw = {} if pretrained_model is None else {"pretrained_model": pretrained_model}
    model = models.CellposeModel(gpu=False, **kw)
    print(f"Cellpose {ver}; model: {getattr(model, 'pretrained_model', 'unknown')}", file=sys.stderr)

    masks, _flows, _styles = model.eval(
        image,
        diameter=diameter,
        flow_threshold=flow_threshold,
        cellprob_threshold=cellprob_threshold,
        min_size=min_size,
        normalize=normalize,
    )
    masks = np.asarray(masks)
    if masks.shape != image.shape:
        raise RuntimeError(f"Output shape {masks.shape} != input shape {image.shape}; "
                           "refusing to return labels in a different coordinate system.")

    # Per-object features
    lo, hi = np.percentile(image, [1, 99]).astype(float)
    scale = hi - lo
    if scale <= 0:
        raise ValueError("Image has no dynamic range between 1st and 99th percentile.")
    im = image.astype(float)
    h, w = image.shape
    px_area = pixel_size_um ** 2
    rows = []
    keep = np.zeros(masks.max() + 1, dtype=bool)
    for rp in regionprops(masks):
        vals = im[rp.coords[:, 0], rp.coords[:, 1]]
        p5, p95 = np.percentile(vals, [5, 95])
        contrast = (p95 - p5) / scale
        area_um2 = rp.area * px_area
        minr, minc, maxr, maxc = rp.bbox
        border = minr == 0 or minc == 0 or maxr == h or maxc == w
        ok = (min_area_um2 <= area_um2 <= max_area_um2) and (contrast >= min_contrast)
        keep[rp.label] = ok
        rows.append(dict(cellpose_label=rp.label, area_px=int(rp.area), area_um2=area_um2,
                         contrast=contrast, touches_border=border, kept=ok))
    table = pd.DataFrame(rows)

    filtered = np.where(keep[masks], masks, 0)
    labels, _, _ = relabel_sequential(filtered)
    labels = labels.astype(np.uint16)
    old_to_new = {}
    for new in np.unique(labels)[1:]:
        old = masks[labels == new][0]
        old_to_new[old] = new
    if len(table):
        kept = table[table.kept].copy()
        kept["label"] = kept.cellpose_label.map(old_to_new)
        kept = kept.drop(columns=["kept"]).sort_values("label")
    else:
        kept = pd.DataFrame(columns=["cellpose_label", "area_px", "area_um2", "contrast",
                                     "touches_border", "label"])
    print(f"Cellpose objects: {len(table)}; kept after size/contrast filter: {len(kept)}",
          file=sys.stderr)
    return labels, kept[["label", "area_um2", "area_px", "contrast", "touches_border"]]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("image", nargs="?", default="bf.tif")
    p.add_argument("--out-labels", default="labels.tif")
    p.add_argument("--out-csv", default="areas.csv")
    p.add_argument("--pixel-size-um", type=float, default=0.65)
    p.add_argument("--diameter", type=float, default=None)
    p.add_argument("--flow-threshold", type=float, default=0.4)
    p.add_argument("--cellprob-threshold", type=float, default=0.0)
    p.add_argument("--min-size", type=int, default=15)
    p.add_argument("--min-area-um2", type=float, default=78.0)
    p.add_argument("--max-area-um2", type=float, default=962.0)
    p.add_argument("--min-contrast", type=float, default=0.25)
    a = p.parse_args()

    img = load_image(a.image)
    labels, table = segment_cancer_cells(
        img, pixel_size_um=a.pixel_size_um, diameter=a.diameter,
        flow_threshold=a.flow_threshold, cellprob_threshold=a.cellprob_threshold,
        min_size=a.min_size, min_area_um2=a.min_area_um2,
        max_area_um2=a.max_area_um2, min_contrast=a.min_contrast)
    tifffile.imwrite(a.out_labels, labels)
    table.to_csv(a.out_csv, index=False)
    print(f"Wrote {a.out_labels} and {a.out_csv}: {len(table)} cells, "
          f"median area {table.area_um2.median() if len(table) else float('nan'):.1f} um^2")


if __name__ == "__main__":
    main()
