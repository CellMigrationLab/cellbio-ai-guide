"""Segment endothelial cells in a brightfield monolayer; measure area and aspect ratio.

Usage: python pipeline.py <input.tif> <labels.tif> <measurements.csv>

Steps (all parameters are constants below):
 1. Load a 2D uint16 image (Y, X); validate.
 2. Flatten: subtract Gaussian background and divide by local SD (removes the
    illumination/offset differences, e.g. a seam between tiles), clip to 1-99 pct, scale to 0-1.
 3. Downscale to ~1.3 um/px (cells ~30 px, Cellpose-SAM's training scale).
 4. Cellpose 4 'cpsam' (no GPU needed), diameter=None (no internal rescale).
 5. Upsample labels to the original grid (nearest neighbour).
 6. Remove cancer cells (small, round, with a bright/dark refractile halo) and tiny
    fragments; remove cells touching the image border from the measurements/labels.
 7. Measure area (um^2) and aspect ratio (major/minor axis of the fitted ellipse).
A review overlay is written next to the labels as <labels>_overlay.png.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from skimage import io, measure, segmentation, transform

PIXEL_SIZE_UM = 0.65
FLATTEN_SIGMA_PX = 40          # background / local SD scale (~ 1 cell diameter)
CLIP_PERCENTILES = (1, 99)
WORK_SCALE = 0.5               # 0.65 -> 1.3 um/px
FLOW_THRESHOLD = 0.4           # Cellpose default
CELLPROB_THRESHOLD = 0.0       # Cellpose default
MIN_AREA_UM2 = 100.0
HALO_Z = 2.5                   # |z| above which a pixel counts as halo
CANCER_MAX_AREA_UM2 = 500.0    # halo rule applies to labels smaller than this
CANCER_HALO_FRACTION = 0.02
CANCER_STD = 1.3
CANCER_ANY_SIZE_HALO_FRACTION = 0.08


def load_image(path: Path) -> np.ndarray:
    image = tifffile.imread(path)
    if image.ndim != 2:
        raise ValueError(f"Expected a 2D (Y, X) image, got shape {image.shape}")
    if image.dtype != np.uint16:
        raise ValueError(f"Expected uint16 data, got {image.dtype}")
    return image.astype(np.float32)


def local_zscore(image: np.ndarray) -> np.ndarray:
    deviation = image - ndi.gaussian_filter(image, FLATTEN_SIGMA_PX)
    local_sd = np.sqrt(ndi.gaussian_filter(deviation**2, FLATTEN_SIGMA_PX))
    if np.any(local_sd <= 0):
        raise ValueError("Image has zero local variance; cannot normalise")
    return deviation / local_sd


def to_unit_range(zimage: np.ndarray) -> np.ndarray:
    low, high = np.percentile(zimage, CLIP_PERCENTILES)
    return np.clip((zimage - low) / (high - low), 0, 1).astype(np.float32)


def run_cellpose(unit_image: np.ndarray) -> np.ndarray:
    from cellpose import models
    small = transform.rescale(unit_image, WORK_SCALE, order=1, anti_aliasing=True)
    model = models.CellposeModel(gpu=False)  # default pretrained cpsam
    labels = model.eval(small.astype(np.float32), diameter=None,
                        flow_threshold=FLOW_THRESHOLD,
                        cellprob_threshold=CELLPROB_THRESHOLD, batch_size=1)[0]
    return transform.resize(labels, unit_image.shape, order=0, preserve_range=True,
                            anti_aliasing=False).astype(np.int32)


def cancer_label_ids(labels: np.ndarray, zimage: np.ndarray) -> list[int]:
    ids = []
    for region in measure.regionprops(labels):
        values = zimage[region.slice][labels[region.slice] == region.label]
        halo = np.mean(np.abs(values) > HALO_Z)
        area = region.area * PIXEL_SIZE_UM**2
        small_halo = area < CANCER_MAX_AREA_UM2 and (
            halo > CANCER_HALO_FRACTION or values.std() > CANCER_STD)
        if small_halo or halo > CANCER_ANY_SIZE_HALO_FRACTION:
            ids.append(region.label)
    return ids


def filter_labels(labels: np.ndarray, zimage: np.ndarray) -> np.ndarray:
    out = labels.copy()
    out[np.isin(out, cancer_label_ids(labels, zimage))] = 0
    for region in measure.regionprops(out):
        r0, c0, r1, c1 = region.bbox
        touches = r0 == 0 or c0 == 0 or r1 == out.shape[0] or c1 == out.shape[1]
        if touches or region.area * PIXEL_SIZE_UM**2 < MIN_AREA_UM2:
            out[out == region.label] = 0
    relabeled, _, _ = segmentation.relabel_sequential(out)
    return relabeled.astype(np.int32)


def measure_cells(labels: np.ndarray) -> pd.DataFrame:
    rows = [{"label": r.label,
             "area_um2": r.area * PIXEL_SIZE_UM**2,
             "aspect_ratio": r.major_axis_length / r.minor_axis_length,
             "centroid_y_um": r.centroid[0] * PIXEL_SIZE_UM,
             "centroid_x_um": r.centroid[1] * PIXEL_SIZE_UM}
            for r in measure.regionprops(labels)]
    return pd.DataFrame(rows, columns=["label", "area_um2", "aspect_ratio",
                                       "centroid_y_um", "centroid_x_um"])


def save_overlay(zimage: np.ndarray, labels: np.ndarray, path: Path) -> None:
    gray = np.clip((zimage + 3) / 6, 0, 1)
    overlay = segmentation.mark_boundaries(np.dstack([gray] * 3), labels, color=(1, 0, 0))
    io.imsave(path, (overlay * 255).astype(np.uint8), check_contrast=False)


def main(input_path: str, labels_path: str, csv_path: str) -> None:
    image = load_image(Path(input_path))
    zimage = local_zscore(image)
    raw_labels = run_cellpose(to_unit_range(zimage))
    labels = filter_labels(raw_labels, zimage)
    table = measure_cells(labels)
    tifffile.imwrite(labels_path, labels, compression="zlib")
    table.to_csv(csv_path, index=False)
    save_overlay(zimage, labels, Path(labels_path).with_name(Path(labels_path).stem + "_overlay.png"))
    print(f"{raw_labels.max()} raw labels -> {len(table)} endothelial cells; "
          f"median area {table.area_um2.median():.0f} um2, "
          f"median aspect ratio {table.aspect_ratio.median():.2f}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
