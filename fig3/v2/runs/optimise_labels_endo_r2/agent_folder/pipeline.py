"""Segment endothelial cells in a 2D brightfield monolayer and measure area / aspect ratio.

Usage: python pipeline.py <input.tif> <labels.tif> <measurements.csv>

Steps (all parameters are constants below):
 1. Load 2D uint16 image (Y, X); reject anything else.
 2. Background removal: median of a 4x-downsampled image (size 15 -> ~60 px window),
    bilinearly upsampled and subtracted (a median keeps steps such as tile seams sharp,
    so the seam cancels). Divide by local RMS (gaussian sigma 40 px).
 3. Downscale to CELLPOSE_SCALE (0.4 -> 1.625 um/px), run Cellpose 4 (cpsam, CPU).
 4. Nearest-neighbour upsample of labels back to the original pixel grid.
 5. Remove cancer cells: small (<CANCER_MAX_AREA_PX) AND high texture (normalised
    intensity std > CANCER_MIN_STD) objects. Endothelium hidden under them is NOT recovered.
 6. Remove tiny fragments, expand labels by EXPAND_PX (Cellpose masks leave gaps between
    cells), relabel 1..N.
 7. Write labels (original grid), CSV (um^2, aspect ratio = major/minor axis of the
    fitted ellipse), and an overlay PNG next to the labels file.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from skimage import measure, segmentation, transform, io as skio

PIXEL_SIZE_UM = 0.65
BG_DOWNSAMPLE = 4
BG_MEDIAN_SIZE = 15
NORM_SIGMA_PX = 40
CELLPOSE_SCALE = 0.4
FLOW_THRESHOLD = 0.8
CELLPROB_THRESHOLD = -1.0
CANCER_MAX_AREA_PX = 1500   # ~630 um^2
CANCER_MIN_STD = 1.2        # std of normalised intensity inside the object
MIN_AREA_UM2 = 100.0
EXPAND_PX = 4


def load_image(path: str) -> np.ndarray:
    img = tifffile.imread(path)
    if img.ndim != 2:
        raise ValueError(f"Expected a 2D (Y, X) image, got shape {img.shape}")
    if img.dtype != np.uint16:
        raise ValueError(f"Expected uint16 image, got {img.dtype}")
    if img.max() > 4095:
        raise ValueError(f"Values exceed 12-bit range (max {img.max()}); input not as expected")
    return img.astype(np.float32)


def normalise(img: np.ndarray) -> np.ndarray:
    """Median background subtraction followed by local contrast normalisation."""
    small = transform.downscale_local_mean(img, (BG_DOWNSAMPLE, BG_DOWNSAMPLE))
    bg_small = ndi.median_filter(small, size=BG_MEDIAN_SIZE, mode="reflect")
    bg = transform.resize(bg_small, img.shape, order=1)
    x = img - bg
    local_rms = np.sqrt(ndi.gaussian_filter(x ** 2, NORM_SIGMA_PX))
    if local_rms.min() <= 0:
        raise ValueError("Image has a flat region; local normalisation undefined")
    return (x / local_rms).astype(np.float32)


def run_cellpose(x: np.ndarray) -> np.ndarray:
    from cellpose import models
    small = transform.rescale(x, CELLPOSE_SCALE, order=1, anti_aliasing=True).astype(np.float32)
    model = models.CellposeModel(gpu=False)  # default pretrained model of Cellpose 4.2 (cpsam_v2)
    labels = model.eval(small, flow_threshold=FLOW_THRESHOLD,
                        cellprob_threshold=CELLPROB_THRESHOLD)[0]
    up = transform.resize(labels, x.shape, order=0, preserve_range=True, anti_aliasing=False)
    return up.astype(np.int32)


def remove_cancer_cells(labels: np.ndarray, x: np.ndarray) -> np.ndarray:
    out = labels.copy()
    for r in measure.regionprops(labels, intensity_image=x):
        if r.area < CANCER_MAX_AREA_PX and r.intensity_std > CANCER_MIN_STD:
            out[labels == r.label] = 0
    return out


def remove_small(labels: np.ndarray) -> np.ndarray:
    min_px = MIN_AREA_UM2 / PIXEL_SIZE_UM ** 2
    out = labels.copy()
    for r in measure.regionprops(labels):
        if r.area < min_px:
            out[labels == r.label] = 0
    return out


def measure_cells(labels: np.ndarray) -> pd.DataFrame:
    rows = []
    h, w = labels.shape
    for r in measure.regionprops(labels):
        minor = r.axis_minor_length
        if minor <= 0:
            raise ValueError(f"Label {r.label} is degenerate (zero minor axis)")
        y0, x0, y1, x1 = r.bbox
        rows.append({
            "label": r.label,
            "area_um2": r.area * PIXEL_SIZE_UM ** 2,
            "aspect_ratio": r.axis_major_length / minor,
            "centroid_y_um": r.centroid[0] * PIXEL_SIZE_UM,
            "centroid_x_um": r.centroid[1] * PIXEL_SIZE_UM,
            "touches_border": bool(y0 == 0 or x0 == 0 or y1 == h or x1 == w),
        })
    return pd.DataFrame(rows, columns=["label", "area_um2", "aspect_ratio", "centroid_y_um",
                                       "centroid_x_um", "touches_border"])


def save_overlay(img: np.ndarray, labels: np.ndarray, path: Path) -> None:
    lo, hi = np.percentile(img, [0.5, 99.5])
    g = np.clip((img - lo) / (hi - lo), 0, 1)
    ov = segmentation.mark_boundaries(np.dstack([g] * 3), labels, color=(1, 0, 0))
    skio.imsave(str(path), (ov * 255).astype(np.uint8), check_contrast=False)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("input"); ap.add_argument("labels"); ap.add_argument("csv")
    a = ap.parse_args(argv)
    img = load_image(a.input)
    x = normalise(img)
    labels = run_cellpose(x)
    labels = remove_cancer_cells(labels, x)
    labels = remove_small(labels)
    labels = segmentation.expand_labels(labels, EXPAND_PX)
    labels, _, _ = segmentation.relabel_sequential(labels)
    labels = labels.astype(np.int32)
    tifffile.imwrite(a.labels, labels)
    table = measure_cells(labels)
    table.to_csv(a.csv, index=False)
    save_overlay(img, labels, Path(a.labels).with_suffix(".overlay.png"))
    print(f"{len(table)} endothelial cells; median area {table.area_um2.median():.0f} um2, "
          f"median aspect ratio {table.aspect_ratio.median():.2f}")


if __name__ == "__main__":
    try:
        main()
    except ValueError as e:
        sys.exit(f"ERROR: {e}")
