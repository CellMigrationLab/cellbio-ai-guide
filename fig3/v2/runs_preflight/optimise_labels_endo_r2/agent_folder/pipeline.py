"""Segment endothelial cells in a brightfield monolayer and measure area / aspect ratio.

Usage: python pipeline.py <input.tif> <labels.tif> <measurements.csv>

Steps (all parameters are constants below):
 1. Read 2D uint16 image (Y, X), validate.
 2. Flat-field: subtract Gaussian-blurred background (sigma 50 px), rescale 1-99th percentile -> [0, 1].
 3. Cellpose 4 (cpsam, pretrained, CPU) with diameter hint 70 px, native pixel size (no resampling).
 4. Remove objects smaller than MIN_AREA_UM2 (cancer cells on top, debris) and objects touching the
    image border (truncated cells bias area / aspect ratio).
 5. Relabel consecutively, write label image (same Y, X grid as input) and CSV in physical units.
Also writes <labels>_overlay.png for visual checking.
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from skimage import io, segmentation
from skimage.measure import regionprops_table

PIXEL_SIZE_UM = 0.65
BACKGROUND_SIGMA_PX = 50
NORM_PERCENTILES = (1, 99)
CELLPOSE_DIAMETER_PX = 70          # ~45 um; chosen on image.tif (50: F1 .63, 70: .68, 90: .66)
FLOW_THRESHOLD = 0.4
CELLPROB_THRESHOLD = 0.0
MIN_AREA_UM2 = 450.0               # ~ area of a 24 um circle; lower bound of stated cell size
REMOVE_BORDER_OBJECTS = True


def read_image(path: Path) -> np.ndarray:
    image = tifffile.imread(path)
    if image.ndim != 2:
        raise ValueError(f"Expected a 2D (Y, X) image, got shape {image.shape}")
    if image.dtype != np.uint16:
        raise ValueError(f"Expected uint16 image, got {image.dtype}")
    if image.max() == image.min():
        raise ValueError("Image is constant; nothing to segment")
    return image


def normalise(image: np.ndarray) -> np.ndarray:
    """Background-subtract and rescale to ~[0, 1] (float32)."""
    flat = image.astype(np.float32)
    flat -= ndi.gaussian_filter(flat, BACKGROUND_SIGMA_PX)
    low, high = np.percentile(flat, NORM_PERCENTILES)
    return (flat - low) / (high - low)


def run_cellpose(image: np.ndarray) -> np.ndarray:
    from cellpose import models  # imported here: slow import, and needs model weights
    model = models.CellposeModel(gpu=False)
    labels, _, _ = model.eval(
        image, diameter=CELLPOSE_DIAMETER_PX,
        flow_threshold=FLOW_THRESHOLD, cellprob_threshold=CELLPROB_THRESHOLD)
    return labels


def remove_border_labels(labels: np.ndarray) -> np.ndarray:
    """Zero every label that touches the image edge (per label id, not per connected blob)."""
    edge = np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]])
    touching = np.zeros(labels.max() + 1, dtype=bool)
    touching[np.unique(edge)] = True
    touching[0] = False
    return np.where(touching[labels], 0, labels)


def filter_objects(labels: np.ndarray) -> np.ndarray:
    """Drop small objects and (optionally) border-touching objects; relabel 1..N."""
    min_area_px = MIN_AREA_UM2 / PIXEL_SIZE_UM ** 2
    areas = np.bincount(labels.ravel())
    remove = areas < min_area_px
    remove[0] = False
    out = np.where(remove[labels], 0, labels)
    if REMOVE_BORDER_OBJECTS:
        out = remove_border_labels(out)
    return segmentation.relabel_sequential(out)[0].astype(np.int32)


def measure(labels: np.ndarray) -> pd.DataFrame:
    props = pd.DataFrame(regionprops_table(
        labels, properties=("label", "area", "axis_major_length", "axis_minor_length", "centroid")))
    return pd.DataFrame({
        "label": props["label"],
        "centroid_y_um": props["centroid-0"] * PIXEL_SIZE_UM,
        "centroid_x_um": props["centroid-1"] * PIXEL_SIZE_UM,
        "area_um2": props["area"] * PIXEL_SIZE_UM ** 2,
        "aspect_ratio": props["axis_major_length"] / props["axis_minor_length"],
    })


def save_overlay(image: np.ndarray, labels: np.ndarray, path: Path) -> None:
    low, high = np.percentile(image, (0.5, 99.5))
    grey = np.clip((image.astype(float) - low) / (high - low), 0, 1)
    overlay = segmentation.mark_boundaries(np.dstack([grey] * 3), labels, color=(0, 1, 0))
    io.imsave(path, (overlay * 255).astype(np.uint8), check_contrast=False)


def main(input_path: str, labels_path: str, csv_path: str) -> None:
    warnings.filterwarnings("ignore", category=UserWarning, module="cellpose")
    image = read_image(Path(input_path))
    labels = filter_objects(run_cellpose(normalise(image)))
    if labels.max() == 0:
        raise RuntimeError("No endothelial cells remained after segmentation/filtering")
    tifffile.imwrite(labels_path, labels, metadata=None)
    table = measure(labels)
    table.to_csv(csv_path, index=False)
    save_overlay(image, labels, Path(labels_path).with_name(Path(labels_path).stem + "_overlay.png"))
    print(f"{labels.max()} cells; median area {table.area_um2.median():.0f} um2; "
          f"median aspect ratio {table.aspect_ratio.median():.2f}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
