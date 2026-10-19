"""Segment endothelial cells in a brightfield monolayer image (cancer cells on top are excluded).

Usage: python pipeline.py <input.tif> <labels.tif> <measurements.csv>
Also writes <labels stem>_overlay.png next to the labels file for visual QC.

Steps (all parameters in the constants below):
 1. Validate input: single-plane 2D uint16 image.
 2. Flat-field: subtract a large Gaussian background (sigma 50 px); no resizing, coordinates preserved.
 3. Cellpose-SAM (cpsam, Cellpose 4) on CPU; intensity normalised to 1-99 percentile; diameter 50 px.
 4. Reject labels that look like cancer cells (small, compact, high internal contrast) or debris.
 5. Measure area (um^2) and aspect ratio (major/minor axis of the fitted ellipse) per remaining label.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from skimage import measure, segmentation
from skimage.io import imsave

PIXEL_SIZE_UM = 0.65
BACKGROUND_SIGMA_PX = 50
CELLPOSE_DIAMETER_PX = 50          # ~32 um; endothelial cells here are 25-50 um
CELLPROB_THRESHOLD = 0.0
FLOW_THRESHOLD = 0.4
NORM_PERCENTILES = [1, 99]
# cancer-cell / debris rejection (pixel units; contrast in raw 12-bit intensity units)
CANCER_MAX_AREA_PX = 2500          # ~1050 um^2; cancer cells up to ~2000 px seen
CANCER_MIN_STD = 110.0             # std of flat-fielded intensity inside the label
MIN_ENDOTHELIAL_AREA_UM2 = 450.0   # below ~24 um equivalent diameter: fragment or small cancer cell/debris


def load_image(path: str) -> np.ndarray:
    image = tifffile.imread(path)
    if image.ndim != 2:
        raise ValueError(f"Expected a 2D (Y, X) image, got shape {image.shape}")
    if image.dtype != np.uint16:
        raise ValueError(f"Expected uint16 image, got {image.dtype}")
    return image


def flatten_background(image: np.ndarray) -> np.ndarray:
    image = image.astype(np.float32)
    return image - ndi.gaussian_filter(image, BACKGROUND_SIGMA_PX)


def run_cellpose(flat: np.ndarray) -> np.ndarray:
    from cellpose import models
    model = models.CellposeModel(gpu=False)
    # Cellpose can normalise its input in place; pass a copy so `flat` keeps physical intensities.
    labels, _, _ = model.eval(
        flat.copy(), diameter=CELLPOSE_DIAMETER_PX, normalize={"percentile": NORM_PERCENTILES},
        flow_threshold=FLOW_THRESHOLD, cellprob_threshold=CELLPROB_THRESHOLD)
    return labels


def is_cancer_or_debris(region, flat: np.ndarray) -> bool:
    inside = flat[region.slice][region.image]
    return region.area <= CANCER_MAX_AREA_PX and inside.std() >= CANCER_MIN_STD


def split_labels(labels: np.ndarray, flat: np.ndarray):
    """Return (endothelial label image with original ids renumbered, removed mask)."""
    keep = np.zeros_like(labels)
    removed = np.zeros(labels.shape, bool)
    min_px = MIN_ENDOTHELIAL_AREA_UM2 / PIXEL_SIZE_UM**2
    next_id = 1
    for region in measure.regionprops(labels):
        if is_cancer_or_debris(region, flat) or region.area < min_px:
            removed[labels == region.label] = True
        else:
            keep[labels == region.label] = next_id
            next_id += 1
    return keep, removed


def measure_cells(labels: np.ndarray, removed: np.ndarray) -> pd.DataFrame:
    near_removed = ndi.binary_dilation(removed, iterations=3)
    rows = []
    h, w = labels.shape
    for r in measure.regionprops(labels):
        minr, minc, maxr, maxc = r.bbox
        rows.append({
            "label": r.label,
            "area_um2": r.area * PIXEL_SIZE_UM**2,
            "aspect_ratio": r.major_axis_length / r.minor_axis_length,
            "centroid_y_um": r.centroid[0] * PIXEL_SIZE_UM,
            "centroid_x_um": r.centroid[1] * PIXEL_SIZE_UM,
            "touches_border": bool(minr == 0 or minc == 0 or maxr == h or maxc == w),
            "touches_cancer_or_debris": bool(near_removed[labels == r.label].any()),
        })
    return pd.DataFrame(rows, columns=["label", "area_um2", "aspect_ratio", "centroid_y_um",
                                       "centroid_x_um", "touches_border", "touches_cancer_or_debris"])


def save_overlay(flat, labels, removed, path: Path) -> None:
    lo, hi = np.percentile(flat, [1, 99])
    gray = np.clip((flat - lo) / (hi - lo), 0, 1)
    rgb = np.dstack([gray] * 3)
    rgb[segmentation.find_boundaries(labels, mode="inner")] = [1, 0, 0]
    rgb[segmentation.find_boundaries(removed, mode="inner")] = [0, 0.6, 1]
    imsave(path, (rgb * 255).astype(np.uint8), check_contrast=False)


def main(input_path: str, labels_path: str, csv_path: str) -> None:
    image = load_image(input_path)
    flat = flatten_background(image)
    raw_labels = run_cellpose(flat)
    labels, removed = split_labels(raw_labels, flat)
    table = measure_cells(labels, removed)
    tifffile.imwrite(labels_path, labels.astype(np.uint16))
    table.to_csv(csv_path, index=False)
    save_overlay(flat, labels, removed, Path(labels_path).with_name(Path(labels_path).stem + "_overlay.png"))
    interior = table[~table.touches_border]
    print(f"cellpose objects: {raw_labels.max()}, removed as cancer/debris/fragment: "
          f"{raw_labels.max() - len(table)}, endothelial cells: {len(table)} "
          f"({len(interior)} not touching border)")
    print(f"median area (interior) {interior.area_um2.median():.0f} um2, "
          f"median aspect ratio {interior.aspect_ratio.median():.2f}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
