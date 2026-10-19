"""Segment endothelial nuclei in a 2D DAPI widefield image (cancer cells on top are excluded).

Usage: python pipeline.py <input.tif> <labels.tif> <measurements.csv>

Steps (all parameters are constants below):
 1. Read 2D uint16 image (Y, X); no resampling, so coordinates/pixel size are preserved.
 2. Cellpose-SAM (cpsam_v2, CPU) with 1-99.5 percentile normalisation, native scale.
 3. Remove objects smaller than MIN_AREA_UM2.
 4. Classify objects: bright, round objects (aspect-dependent mean raw intensity threshold) are
    treated as cancer cells lying on top of the monolayer and removed, unless larger than
    LARGE_NUCLEUS_AREA_UM2 (cancer cells in this data are smaller than that).
 5. Relabel 1..N, write label image and area (um^2) / aspect ratio table.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile
from skimage import measure, segmentation

PIXEL_SIZE_UM = 0.65
EXPECTED_DTYPE = np.uint16
MAX_VALUE_12BIT = 4095
MODEL_NAME = "cpsam_v2"
NORM_PERCENTILES = [1.0, 99.5]
BATCH_SIZE = 4
MIN_AREA_UM2 = 80.0   # ~190 px; smaller objects are debris/fragments
# Cancer-cell rule: mean raw intensity >= CANCER_BASE_INTENSITY + CANCER_ASPECT_SLOPE*(aspect-1),
# capped at CANCER_MAX_INTENSITY. Round objects are more likely cancer cells, so need less brightness.
CANCER_BASE_INTENSITY = 500.0   # raw 12-bit counts, tuned on image.tif only
CANCER_ASPECT_SLOPE = 1000.0
CANCER_MAX_INTENSITY = 1000.0
LARGE_NUCLEUS_AREA_UM2 = 200.0  # ~475 px; bright objects above this are kept as endothelial


def read_image(path: Path) -> np.ndarray:
    image = tifffile.imread(path)
    if image.ndim != 2:
        raise ValueError(f"Expected 2D (Y, X) image, got shape {image.shape}")
    if image.dtype != EXPECTED_DTYPE:
        raise ValueError(f"Expected dtype uint16, got {image.dtype}")
    if image.max() > MAX_VALUE_12BIT:
        raise ValueError(f"Values exceed 12-bit range: max {image.max()}")
    return image


def load_model():
    from cellpose import models
    model_path = models.MODEL_DIR / MODEL_NAME
    if not model_path.exists():
        raise FileNotFoundError(f"Cellpose model weights not found: {model_path}")
    return models.CellposeModel(gpu=False, pretrained_model=str(model_path))


def segment_nuclei(image: np.ndarray) -> np.ndarray:
    masks, _, _ = load_model().eval(
        image.astype(np.float32), batch_size=BATCH_SIZE,
        normalize={"percentile": NORM_PERCENTILES})
    return masks.astype(np.int32)


def remove_small(labels: np.ndarray) -> np.ndarray:
    min_px = MIN_AREA_UM2 / PIXEL_SIZE_UM ** 2
    out = labels.copy()
    for r in measure.regionprops(labels):
        if r.area < min_px:
            out[labels == r.label] = 0
    return out


def remove_cancer_cells(labels: np.ndarray, image: np.ndarray) -> np.ndarray:
    large_px = LARGE_NUCLEUS_AREA_UM2 / PIXEL_SIZE_UM ** 2
    out = labels.copy()
    for r in measure.regionprops(labels, intensity_image=image):
        aspect = r.major_axis_length / r.minor_axis_length
        threshold = min(CANCER_MAX_INTENSITY,
                        CANCER_BASE_INTENSITY + CANCER_ASPECT_SLOPE * (aspect - 1.0))
        if r.intensity_mean >= threshold and r.area < large_px:
            out[labels == r.label] = 0
    return out


def measure_nuclei(labels: np.ndarray) -> pd.DataFrame:
    h, w = labels.shape
    rows = []
    for r in measure.regionprops(labels):
        y0, x0, y1, x1 = r.bbox
        rows.append({
            "label": r.label,
            "centroid_y_um": r.centroid[0] * PIXEL_SIZE_UM,
            "centroid_x_um": r.centroid[1] * PIXEL_SIZE_UM,
            "area_um2": r.area * PIXEL_SIZE_UM ** 2,
            "aspect_ratio": r.major_axis_length / r.minor_axis_length,
            "touches_border": bool(y0 == 0 or x0 == 0 or y1 == h or x1 == w),
        })
    return pd.DataFrame(rows)


def main(input_path: str, labels_path: str, csv_path: str) -> None:
    image = read_image(Path(input_path))
    labels = remove_cancer_cells(remove_small(segment_nuclei(image)), image)
    labels, _, _ = segmentation.relabel_sequential(labels)
    labels = labels.astype(np.uint16)
    tifffile.imwrite(labels_path, labels)
    table = measure_nuclei(labels)
    table.to_csv(csv_path, index=False)
    print(f"{len(table)} endothelial nuclei "
          f"({int(table.touches_border.sum())} touch the border); "
          f"median area {table.area_um2.median():.1f} um^2, "
          f"median aspect {table.aspect_ratio.median():.2f}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
