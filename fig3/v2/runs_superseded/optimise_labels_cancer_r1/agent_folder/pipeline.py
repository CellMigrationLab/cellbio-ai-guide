"""Segment cancer cells in 2D brightfield images (on endothelial monolayer) with Cellpose
and measure area (um^2) and aspect ratio.

Usage: python pipeline.py <input.tif> <labels.tif> <measurements.csv>
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from skimage import measure, morphology

PIXEL_SIZE_UM = 0.65
EXPECTED_SHAPE_NDIM = 2
BIT_DEPTH_MAX = 4095           # 12-bit data stored in uint16
FLATFIELD_SIGMA_PX = 50        # background estimate scale (>> cell diameter of ~30 px)
NORM_PERCENTILES = (1.0, 99.0)  # robust intensity scaling
DIAMETER_PX = 30.0             # expected cell diameter 15-25 um / 0.65 ~ 23-38 px; None = model default
FLOW_THRESHOLD = 0.4
CELLPROB_THRESHOLD = 0.0
MIN_AREA_UM2 = 80.0            # drop fragments / debris smaller than this
MAX_AREA_UM2 = 600.0           # drop large smooth endothelial cells / merged objects
MIN_SOLIDITY = 0.93            # drop irregular shapes
MIN_INTENSITY_STD = 0.20       # std of normalised intensity inside object: endothelial cells are smooth, cancer cells textured
FILL_HOLES = True


def load_image(path: Path) -> np.ndarray:
    """Load a single-channel 2D image and validate it."""
    image = tifffile.imread(path)
    if image.ndim != EXPECTED_SHAPE_NDIM:
        raise ValueError(f"Expected 2D (Y, X) image, got shape {image.shape} for {path}")
    if image.dtype != np.uint16:
        raise ValueError(f"Expected uint16 image, got {image.dtype}")
    if image.max() > BIT_DEPTH_MAX:
        raise ValueError(f"Values exceed 12-bit range: max {image.max()}")
    return image


def preprocess(image: np.ndarray) -> np.ndarray:
    """Flat-field (divide by large Gaussian background), then percentile-normalise to ~[0, 1]."""
    img = image.astype(np.float32)
    if FLATFIELD_SIGMA_PX:
        background = ndi.gaussian_filter(img, FLATFIELD_SIGMA_PX, mode="reflect")
        img = img / background
    lo, hi = np.percentile(img, NORM_PERCENTILES)
    if hi <= lo:
        raise ValueError("Image has no contrast after flat-fielding")
    return ((img - lo) / (hi - lo)).astype(np.float32)


def run_cellpose(img: np.ndarray) -> np.ndarray:
    """Cellpose-SAM (default pretrained model of Cellpose 4.x) on CPU; returns int label image."""
    from cellpose import models
    model = models.CellposeModel(gpu=False)
    masks, _, _ = model.eval(
        img, diameter=DIAMETER_PX, flow_threshold=FLOW_THRESHOLD,
        cellprob_threshold=CELLPROB_THRESHOLD, normalize=False, batch_size=4)
    return masks.astype(np.int32)


def filter_labels(labels: np.ndarray, normalised: np.ndarray) -> np.ndarray:
    """Fill holes, drop objects by area/solidity/texture, relabel consecutively."""
    out = np.zeros_like(labels)
    next_id = 1
    min_px = MIN_AREA_UM2 / PIXEL_SIZE_UM**2
    max_px = MAX_AREA_UM2 / PIXEL_SIZE_UM**2
    for region in measure.regionprops(labels):
        mask = region.image
        if FILL_HOLES:
            mask = ndi.binary_fill_holes(mask)
        area = mask.sum()
        if not (min_px <= area <= max_px):
            continue
        if measure.regionprops(mask.astype(np.uint8))[0].solidity < MIN_SOLIDITY:
            continue
        r0, c0, r1, c1 = region.bbox
        if normalised[r0:r1, c0:c1][mask].std() < MIN_INTENSITY_STD:
            continue
        view = out[r0:r1, c0:c1]
        view[mask & (view == 0)] = next_id
        next_id += 1
    return out


def measure_cells(labels: np.ndarray) -> pd.DataFrame:
    """Area (um^2), aspect ratio (major/minor axis of fitted ellipse, >=1), edge flag."""
    h, w = labels.shape
    rows = []
    for r in measure.regionprops(labels):
        r0, c0, r1, c1 = r.bbox
        minor = r.axis_minor_length
        rows.append({
            "label": r.label,
            "centroid_y_um": r.centroid[0] * PIXEL_SIZE_UM,
            "centroid_x_um": r.centroid[1] * PIXEL_SIZE_UM,
            "area_um2": r.area * PIXEL_SIZE_UM**2,
            "aspect_ratio": r.axis_major_length / minor if minor > 0 else np.nan,
            "touches_border": bool(r0 == 0 or c0 == 0 or r1 == h or c1 == w),
        })
    return pd.DataFrame(rows, columns=["label", "centroid_y_um", "centroid_x_um",
                                       "area_um2", "aspect_ratio", "touches_border"])


def segment(image: np.ndarray) -> np.ndarray:
    normalised = preprocess(image)
    return filter_labels(run_cellpose(normalised), normalised)


def main(argv: list[str]) -> None:
    if len(argv) != 4:
        raise SystemExit(__doc__)
    inp, out_labels, out_csv = map(Path, argv[1:])
    if not inp.exists():
        raise FileNotFoundError(inp)
    labels = segment(load_image(inp))
    tifffile.imwrite(out_labels, labels.astype(np.int32))
    table = measure_cells(labels)
    table.to_csv(out_csv, index=False)
    print(f"{len(table)} cells; median area {table.area_um2.median():.1f} um^2")


if __name__ == "__main__":
    main(sys.argv)
