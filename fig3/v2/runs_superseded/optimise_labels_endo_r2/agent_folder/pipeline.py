"""Segment endothelial cells in a brightfield monolayer and measure area / aspect ratio.

Usage: python pipeline.py <input.tif> <labels.tif> <measurements.csv>

Steps (all parameters are constants below):
 1. Read 2D uint16 image; validate.
 2. Flat-field: subtract Gaussian background (sigma 40 px), clip to 1-99 percentile, scale to [0, 1].
 3. Cellpose-SAM (cpsam, Cellpose 4.x) on CPU, diameter 70 px (~45 um), no internal normalisation.
 4. Remove cancer cells: small objects with strong internal contrast (round, refractile cells on top).
    The freed area is re-assigned to neighbouring endothelial labels (bounded expansion).
 5. Remove tiny debris objects; relabel sequentially.
 6. Measure area (um^2) and aspect ratio (major/minor axis of the fitted ellipse).
Output labels have the same shape / pixel grid as the input (no resampling of the output).
"""
import sys
import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from skimage import measure, segmentation

PIXEL_SIZE_UM = 0.65
BACKGROUND_SIGMA_PX = 40
PERCENTILES = (1, 99)
CELLPOSE_DIAMETER_PX = 70
FLOW_THRESHOLD = 0.4
CELLPROB_THRESHOLD = 0.0
CANCER_MAX_AREA_UM2 = 700.0
CANCER_MIN_CONTRAST = 120.0     # std of flat-fielded grey values (raw 12-bit units) inside object
FILL_DILATION_PX = 3
FILL_MAX_DISTANCE_PX = 40
MIN_CELL_AREA_UM2 = 150.0


def read_image(path: str) -> np.ndarray:
    image = tifffile.imread(path)
    if image.ndim != 2:
        raise ValueError(f"Expected a 2D (Y, X) image, got shape {image.shape}")
    if image.dtype != np.uint16:
        raise ValueError(f"Expected uint16 image, got {image.dtype}")
    return image


def flat_field(image: np.ndarray) -> np.ndarray:
    """Background-subtracted float32 image (original intensity units)."""
    image = image.astype(np.float32)
    return image - ndi.gaussian_filter(image, BACKGROUND_SIGMA_PX)


def rescale_unit(image: np.ndarray) -> np.ndarray:
    low, high = np.percentile(image, PERCENTILES)
    if high <= low:
        raise ValueError("Image has no contrast after flat-fielding")
    return np.clip((image - low) / (high - low), 0, 1).astype(np.float32)


def run_cellpose(unit_image: np.ndarray) -> np.ndarray:
    from cellpose import models
    model = models.CellposeModel(gpu=False)
    labels, _, _ = model.eval(unit_image, diameter=CELLPOSE_DIAMETER_PX,
                              flow_threshold=FLOW_THRESHOLD,
                              cellprob_threshold=CELLPROB_THRESHOLD, normalize=False)
    return labels.astype(np.int32)


def find_cancer_labels(labels: np.ndarray, flat: np.ndarray) -> list[int]:
    found = []
    for region in measure.regionprops(labels, intensity_image=flat):
        area_um2 = region.area * PIXEL_SIZE_UM ** 2
        contrast = float(np.std(flat[labels == region.label]))
        if area_um2 < CANCER_MAX_AREA_UM2 and contrast >= CANCER_MIN_CONTRAST:
            found.append(region.label)
    return found


def remove_and_fill(labels: np.ndarray, remove: list[int]) -> np.ndarray:
    """Delete labels, then let neighbours grow into the freed area only."""
    removed = np.isin(labels, remove)
    kept = labels.copy()
    kept[removed] = 0
    freed = ndi.binary_dilation(removed, iterations=FILL_DILATION_PX) & (kept == 0)
    grown = segmentation.expand_labels(kept, distance=FILL_MAX_DISTANCE_PX)
    kept[freed] = grown[freed]
    return kept


def drop_small(labels: np.ndarray) -> np.ndarray:
    min_px = MIN_CELL_AREA_UM2 / PIXEL_SIZE_UM ** 2
    sizes = np.bincount(labels.ravel())
    small = np.flatnonzero(sizes < min_px)
    small = small[small > 0]
    out = labels.copy()
    out[np.isin(out, small)] = 0
    return segmentation.relabel_sequential(out)[0].astype(np.int32)


def measure_cells(labels: np.ndarray) -> pd.DataFrame:
    h, w = labels.shape
    rows = []
    for r in measure.regionprops(labels):
        y0, x0, y1, x1 = r.bbox
        rows.append({
            "label": r.label,
            "area_um2": r.area * PIXEL_SIZE_UM ** 2,
            "aspect_ratio": r.axis_major_length / r.axis_minor_length,
            "centroid_y_um": r.centroid[0] * PIXEL_SIZE_UM,
            "centroid_x_um": r.centroid[1] * PIXEL_SIZE_UM,
            "touches_border": bool(y0 == 0 or x0 == 0 or y1 == h or x1 == w),
        })
    return pd.DataFrame(rows)


def main(input_path: str, labels_path: str, csv_path: str) -> None:
    image = read_image(input_path)
    flat = flat_field(image)
    labels = run_cellpose(rescale_unit(flat))
    cancer = find_cancer_labels(labels, flat)
    print(f"cellpose objects: {labels.max()}, removed as cancer cells: {len(cancer)}")
    labels = drop_small(remove_and_fill(labels, cancer))
    tifffile.imwrite(labels_path, labels, compression="zlib")
    table = measure_cells(labels)
    table.to_csv(csv_path, index=False)
    print(f"endothelial cells: {len(table)} ({int(table.touches_border.sum())} touch the border)")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
