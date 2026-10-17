"""Segment cancer cells in 2D brightfield images and measure area and aspect ratio.

Usage: python pipeline.py <input.tif> <labels.tif> <measurements.csv>

Steps (all parameters are constants below):
 1. Read a single-channel 2D uint16 image; validate.
 2. Cellpose-SAM (cpsam) on the raw image, per-image 1-99 percentile normalisation (Cellpose built-in),
    native pixel size, no resizing (cpsam is scale-agnostic; diameter is not set).
 3. Remove non-cancer objects (endothelial cells, debris): keep objects whose intensity std
    (after subtracting a Gaussian background, sigma 40 px) >= MIN_CONTRAST and whose area is within bounds.
 4. Relabel consecutively, write label image (same shape/coordinates as input) and CSV (area um^2, aspect ratio).
Aspect ratio = major axis / minor axis of the ellipse with the same second moments (>= 1).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from skimage.measure import regionprops_table
from skimage.segmentation import relabel_sequential

PIXEL_SIZE_UM = 0.65
BACKGROUND_SIGMA_PX = 40
NORMALIZE_PERCENTILES = [1, 99]
FLOW_THRESHOLD = 0.4
CELLPROB_THRESHOLD = 0.0
MIN_CONTRAST = 90.0           # raw intensity units (uint16), std inside mask after background subtraction
MIN_AREA_UM2 = 113.0           # circle of 12 um diameter (stated cell size 15-25 um)
MAX_AREA_UM2 = 700.0


def read_image(path: Path) -> np.ndarray:
    image = tifffile.imread(path)
    if image.ndim != 2:
        raise ValueError(f"Expected a 2D (Y, X) image, got shape {image.shape}")
    if image.dtype != np.uint16:
        raise ValueError(f"Expected uint16 image, got {image.dtype}")
    return image


def segment_cellpose(image: np.ndarray) -> np.ndarray:
    from cellpose import models
    model = models.CellposeModel(gpu=False)
    masks, _, _ = model.eval(
        image.astype(np.float32),
        normalize={"percentile": NORMALIZE_PERCENTILES},
        flow_threshold=FLOW_THRESHOLD,
        cellprob_threshold=CELLPROB_THRESHOLD,
        batch_size=4,
    )
    return masks.astype(np.int32)


def background_subtracted(image: np.ndarray) -> np.ndarray:
    data = image.astype(np.float32)
    return data - ndi.gaussian_filter(data, BACKGROUND_SIGMA_PX)


def filter_objects(masks: np.ndarray, image: np.ndarray) -> np.ndarray:
    """Keep objects with cancer-cell-like contrast and size; others are set to 0."""
    flat = background_subtracted(image)
    ids = np.arange(1, masks.max() + 1)
    std = ndi.standard_deviation(flat, masks, ids)
    area_um2 = ndi.sum(np.ones_like(flat), masks, ids) * PIXEL_SIZE_UM ** 2
    keep = (std >= MIN_CONTRAST) & (area_um2 >= MIN_AREA_UM2) & (area_um2 <= MAX_AREA_UM2)
    kept_ids = ids[keep]
    filtered = np.where(np.isin(masks, kept_ids), masks, 0)
    return relabel_sequential(filtered)[0].astype(np.int32)


def measure(labels: np.ndarray) -> pd.DataFrame:
    table = pd.DataFrame(regionprops_table(
        labels, properties=("label", "area", "axis_major_length", "axis_minor_length", "centroid")))
    return pd.DataFrame({
        "label": table["label"],
        "centroid_y_um": table["centroid-0"] * PIXEL_SIZE_UM,
        "centroid_x_um": table["centroid-1"] * PIXEL_SIZE_UM,
        "area_um2": table["area"] * PIXEL_SIZE_UM ** 2,
        "aspect_ratio": table["axis_major_length"] / table["axis_minor_length"],
    })


def main(input_path: str, labels_path: str, csv_path: str) -> None:
    image = read_image(Path(input_path))
    raw_masks = segment_cellpose(image)
    labels = filter_objects(raw_masks, image)
    tifffile.imwrite(labels_path, labels)
    measure(labels).to_csv(csv_path, index=False)
    print(f"cellpose objects: {raw_masks.max()}, cancer cells kept: {labels.max()}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
