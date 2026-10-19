"""Segment endothelial cells in a brightfield monolayer image (Cellpose 4 / cpsam).

Usage: python pipeline.py <input.tif> <labels.tif> <measurements.csv>
Outputs: label image (uint32, 0 = background, same YX grid as input) and a CSV with
label, centroid, area_um2, aspect_ratio (ellipse major/minor axis length).
"""
import csv
import sys
from pathlib import Path

import numpy as np
import tifffile
from scipy import ndimage as ndi
from skimage import measure, morphology, transform

PIXEL_SIZE_UM = 0.65
EXPECTED_DTYPE = np.uint16
MAX_12BIT = 4095

# --- parameters (see log.txt for how they were chosen) ---
BACKGROUND_SIGMA_PX = 40      # gaussian scale for illumination / seam flattening
DOWNSCALE = 1.0               # resampling factor applied before Cellpose (1 = none)
DIAMETER_PX = 50              # approx. cell diameter in input pixels (~33 um)
FLOW_THRESHOLD = 0.4
CELLPROB_THRESHOLD = 0.0
MIN_AREA_UM2 = 100.0          # drop fragments smaller than this
EDGE_NOTE = "cells touching the image border are truncated and are flagged in the CSV"


def load_image(path: str) -> np.ndarray:
    img = tifffile.imread(path)
    if img.ndim == 3 and img.shape[0] == 1:
        img = img[0]
    if img.ndim != 2:
        raise ValueError(f"Expected a 2D (Y, X) single-channel image, got shape {img.shape}")
    if img.dtype != EXPECTED_DTYPE:
        raise ValueError(f"Expected dtype uint16, got {img.dtype}")
    if img.max() > MAX_12BIT:
        raise ValueError(f"Values exceed 12-bit range (max {img.max()})")
    return img


def flatten_background(img: np.ndarray, sigma: float = BACKGROUND_SIGMA_PX) -> np.ndarray:
    """Divide by a smooth background (removes uneven illumination and tile seams),
    then centre on 0 and scale by a robust spread (MAD)."""
    f = img.astype(np.float32)
    bg = ndi.gaussian_filter(f, sigma, mode="reflect")
    r = f / bg - 1.0
    mad = np.median(np.abs(r - np.median(r))) * 1.4826
    if mad == 0:
        raise ValueError("Image has no contrast after background flattening")
    return ((r - np.median(r)) / mad).astype(np.float32)


def run_cellpose(img: np.ndarray) -> np.ndarray:
    from cellpose import models
    model = models.CellposeModel(gpu=False)
    masks, _, _ = model.eval(
        img, diameter=DIAMETER_PX, channel_axis=None, normalize=True,
        flow_threshold=FLOW_THRESHOLD, cellprob_threshold=CELLPROB_THRESHOLD,
        batch_size=4,
    )
    return masks


def segment(img: np.ndarray) -> np.ndarray:
    x = flatten_background(img)
    if DOWNSCALE != 1.0:
        shape = tuple(int(round(s * DOWNSCALE)) for s in x.shape)
        x = transform.resize(x, shape, order=1, anti_aliasing=True, preserve_range=True).astype(np.float32)
    masks = run_cellpose(x)
    if DOWNSCALE != 1.0:
        masks = transform.resize(masks, img.shape, order=0, anti_aliasing=False,
                                 preserve_range=True).astype(np.int32)
    return postprocess(masks)


def postprocess(masks: np.ndarray) -> np.ndarray:
    """Remove small fragments, keep one connected component per label, relabel."""
    out = np.zeros(masks.shape, np.uint32)
    min_px = MIN_AREA_UM2 / PIXEL_SIZE_UM ** 2
    next_id = 1
    for r in measure.regionprops(masks):
        sl = r.slice
        m = ndi.binary_fill_holes(r.image)
        cc, n = ndi.label(m)
        if n > 1:
            m = cc == (np.argmax(np.bincount(cc.ravel())[1:]) + 1)
        if m.sum() < min_px:
            continue
        view = out[sl]
        view[m & (view == 0)] = next_id
        next_id += 1
    return out


def measure_cells(labels: np.ndarray) -> list[dict]:
    h, w = labels.shape
    rows = []
    for r in measure.regionprops(labels):
        minr, minc, maxr, maxc = r.bbox
        minor = r.axis_minor_length
        rows.append({
            "label": r.label,
            "centroid_y_um": round(r.centroid[0] * PIXEL_SIZE_UM, 3),
            "centroid_x_um": round(r.centroid[1] * PIXEL_SIZE_UM, 3),
            "area_um2": round(r.area * PIXEL_SIZE_UM ** 2, 3),
            "aspect_ratio": round(r.axis_major_length / minor, 4) if minor > 0 else float("nan"),
            "touches_border": bool(minr == 0 or minc == 0 or maxr == h or maxc == w),
        })
    return rows


def main(argv: list[str]) -> None:
    if len(argv) != 4:
        raise SystemExit(__doc__)
    inp, out_labels, out_csv = argv[1:]
    labels = segment(load_image(inp))
    tifffile.imwrite(out_labels, labels)
    rows = measure_cells(labels)
    with open(out_csv, "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) if rows else ["label"])
        wr.writeheader()
        wr.writerows(rows)
    print(f"{len(rows)} cells -> {out_labels}, {out_csv}")


if __name__ == "__main__":
    main(sys.argv)
