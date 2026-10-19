"""Segment endothelial nuclei in a 2D DAPI image and measure area and aspect ratio.

Usage: python pipeline.py <input.tif> <labels.tif> <measurements.csv>

Steps (all parameters are constants below):
 1. Read a 2D uint16 image (12-bit range), validate.
 2. Cellpose-SAM ('cpsam', Cellpose 4.x) at native resolution, intensity normalised to the
    1st-99.5th percentile of the image. No resizing, so the pixel grid is preserved.
 3. Per-object half-maximum refinement: the model includes a diffuse out-of-focus halo in
    parts of the image; each mask is trimmed to pixels above background + 0.5*(core - background).
 4. Class filter: cancer-cell nuclei are much brighter than endothelial nuclei, so objects with
    median intensity above MAX_MEDIAN_INTENSITY, or area outside the nuclear range, are dropped.
 5. Write labels (0 = background, 1..N), a measurements table, and a QC overlay.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from skimage.filters import gaussian
from skimage.measure import regionprops
from skimage.segmentation import find_boundaries, relabel_sequential
import skimage.io

PIXEL_SIZE_UM = 0.65
MAX_RAW_VALUE = 4095  # 12-bit data stored in uint16
NORMALIZE_PERCENTILES = [1, 99.5]
FLOW_THRESHOLD = 0.4
CELLPROB_THRESHOLD = -1.0  # permissive; halo is removed by refinement
REFINE_SMOOTH_SIGMA_PX = 1.0
REFINE_FRACTION = 0.45
REFINE_CORE_EROSION_PX = 3
REFINE_BACKGROUND_PERCENTILE = 5
MAX_MEDIAN_INTENSITY = 750  # raw counts; separates dim endothelial from bright cancer nuclei
MIN_AREA_UM2 = 60.0
MAX_AREA_UM2 = 500.0


def read_image(path: Path) -> np.ndarray:
    """Read and validate a single-channel 2D uint16 image."""
    if not path.is_file():
        raise FileNotFoundError(f"Input image not found: {path}")
    image = tifffile.imread(path)
    if image.ndim != 2:
        raise ValueError(f"Expected a 2D (Y, X) image, got shape {image.shape}")
    if image.dtype != np.uint16:
        raise ValueError(f"Expected uint16 data, got {image.dtype}")
    if image.max() > MAX_RAW_VALUE:
        raise ValueError(f"Max value {image.max()} exceeds 12-bit range {MAX_RAW_VALUE}; "
                         "intensity thresholds in this pipeline would not apply")
    return image


def segment_cellpose(image: np.ndarray) -> np.ndarray:
    """Cellpose-SAM instance segmentation on CPU at native pixel size."""
    from cellpose import models  # imported here: slow import, not needed for tests
    model = models.CellposeModel(gpu=False)
    labels, _, _ = model.eval(
        image.astype(np.float32), diameter=None,
        normalize={"percentile": NORMALIZE_PERCENTILES},
        flow_threshold=FLOW_THRESHOLD, cellprob_threshold=CELLPROB_THRESHOLD)
    return labels.astype(np.int32)


def refine_labels(labels: np.ndarray, image: np.ndarray) -> np.ndarray:
    """Trim each mask to its half-maximum contour, keeping the largest component."""
    smooth = gaussian(image.astype(np.float64), REFINE_SMOOTH_SIGMA_PX, preserve_range=True)
    refined = np.zeros_like(labels)
    for region in regionprops(labels):
        y0, x0, y1, x1 = region.bbox
        mask = region.image
        window = smooth[y0:y1, x0:x1]
        core = ndi.binary_erosion(mask, iterations=REFINE_CORE_EROSION_PX) if mask.sum() > 60 else mask
        if not core.any():
            core = mask
        background = np.percentile(window, REFINE_BACKGROUND_PERCENTILE)
        threshold = background + REFINE_FRACTION * (np.median(window[core]) - background)
        keep = ndi.binary_fill_holes(mask & (window > threshold))
        parts, n_parts = ndi.label(keep)
        if n_parts == 0:
            continue
        sizes = ndi.sum(keep, parts, range(1, n_parts + 1))
        keep = parts == (1 + int(np.argmax(sizes)))
        target = refined[y0:y1, x0:x1]
        target[keep & (target == 0)] = region.label
    return refined


def filter_endothelial(labels: np.ndarray, image: np.ndarray) -> np.ndarray:
    """Drop bright (cancer) and out-of-range-size objects; relabel 1..N."""
    out = labels.copy()
    for region in regionprops(labels, intensity_image=image):
        area_um2 = region.area * PIXEL_SIZE_UM ** 2
        median = np.median(image[labels == region.label])
        if median > MAX_MEDIAN_INTENSITY or not MIN_AREA_UM2 <= area_um2 <= MAX_AREA_UM2:
            out[labels == region.label] = 0
    return relabel_sequential(out)[0].astype(np.int32)


def measure(labels: np.ndarray, image: np.ndarray) -> pd.DataFrame:
    """Area (µm²) and aspect ratio (major/minor ellipse axis) per label."""
    rows = []
    for r in regionprops(labels, intensity_image=image):
        rows.append({
            "label": r.label,
            "area_um2": r.area * PIXEL_SIZE_UM ** 2,
            "aspect_ratio": r.axis_major_length / r.axis_minor_length,
            "centroid_y_um": r.centroid[0] * PIXEL_SIZE_UM,
            "centroid_x_um": r.centroid[1] * PIXEL_SIZE_UM,
            "median_intensity": float(np.median(image[labels == r.label])),
        })
    return pd.DataFrame(rows, columns=["label", "area_um2", "aspect_ratio",
                                       "centroid_y_um", "centroid_x_um", "median_intensity"])


def save_overlay(image: np.ndarray, labels: np.ndarray, path: Path) -> None:
    gray = np.clip(image / np.percentile(image, 99.0), 0, 1) ** 0.6
    rgb = np.dstack([gray] * 3)
    rgb[find_boundaries(labels, mode="inner")] = [1, 0, 0]
    skimage.io.imsave(path, (rgb * 255).astype(np.uint8), check_contrast=False)


def main(argv: list[str]) -> None:
    if len(argv) != 4:
        raise SystemExit(__doc__)
    input_path, labels_path, csv_path = (Path(a) for a in argv[1:])
    image = read_image(input_path)
    raw = segment_cellpose(image)
    tifffile.imwrite(labels_path.with_name(labels_path.stem + "_cellpose_raw.tif"), raw)
    refined = refine_labels(raw, image)
    labels = filter_endothelial(refined, image)
    tifffile.imwrite(labels_path, labels)
    table = measure(labels, image)
    table.to_csv(csv_path, index=False)
    save_overlay(image, labels, labels_path.with_name(labels_path.stem + "_overlay.png"))
    print(f"cellpose objects: {raw.max()}, after refinement: {len(np.unique(refined)) - 1}, "
          f"endothelial nuclei: {len(table)}")


if __name__ == "__main__":
    main(sys.argv)
