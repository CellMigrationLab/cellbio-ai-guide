"""Segment endothelial nuclei (DAPI, 2D widefield) and measure area / aspect ratio.

Usage: python pipeline.py <input.tif> <labels.tif> <measurements.csv>

Steps (all parameters are constants below):
 1. Load a 2D uint16 image (Y, X); reject anything else.
 2. Normalise: clip to the 1st..99.5th percentile of the image, scale to 0..1.
 3. Cellpose 4 (cpsam, CPU) with diameter = NUCLEUS_DIAMETER_UM / PIXEL_SIZE_UM px,
    flow_threshold 0.4, cellprob_threshold 0.0, no resizing of the output (labels are in
    the input pixel grid).
 4. Reject non-endothelial objects (bright round cancer cells, debris, fragments):
    mean intensity > MAX_REL_INTENSITY x median object mean intensity, or area outside
    [MIN_AREA_UM2, MAX_AREA_UM2]. Surviving labels are renumbered 1..N.
 5. Write labels (uint16), CSV (label, area_um2, aspect_ratio, centroid, mean intensity),
    and an outline overlay PNG next to the labels file.
Aspect ratio = major / minor axis length of the ellipse with the same second moments.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile
from skimage.measure import regionprops_table
from skimage.segmentation import find_boundaries, relabel_sequential
import skimage.io

PIXEL_SIZE_UM = 0.65
NUCLEUS_DIAMETER_UM = 15.0
NORM_PERCENTILES = (1.0, 99.5)
FLOW_THRESHOLD = 0.4
CELLPROB_THRESHOLD = 0.0
MAX_REL_INTENSITY = 1.5   # x median of per-object mean intensity (cancer cells are brighter)
MIN_AREA_UM2 = 100.0
MAX_AREA_UM2 = 420.0


def load_image(path: str) -> np.ndarray:
    image = tifffile.imread(path)
    if image.ndim != 2:
        raise ValueError(f"Expected a 2D (Y, X) single-channel image, got shape {image.shape}")
    if image.dtype != np.uint16:
        raise ValueError(f"Expected uint16 image, got {image.dtype}")
    if image.max() == image.min():
        raise ValueError("Image is constant; cannot normalise")
    return image


def normalise(image: np.ndarray) -> np.ndarray:
    lo, hi = np.percentile(image, NORM_PERCENTILES)
    if hi <= lo:
        raise ValueError("Degenerate intensity percentiles")
    return np.clip((image.astype(np.float32) - lo) / (hi - lo), 0, 1)


def run_cellpose(image01: np.ndarray) -> np.ndarray:
    from cellpose import models
    diameter_px = NUCLEUS_DIAMETER_UM / PIXEL_SIZE_UM
    model = models.CellposeModel(gpu=False)  # default pretrained model (cpsam)
    labels, _, _ = model.eval(image01, diameter=diameter_px,
                              flow_threshold=FLOW_THRESHOLD,
                              cellprob_threshold=CELLPROB_THRESHOLD)
    return labels.astype(np.int32)


def object_table(labels: np.ndarray, image: np.ndarray) -> pd.DataFrame:
    t = pd.DataFrame(regionprops_table(
        labels, intensity_image=image.astype(np.float32),
        properties=("label", "area", "axis_major_length", "axis_minor_length",
                    "centroid", "intensity_mean")))
    t["area_um2"] = t["area"] * PIXEL_SIZE_UM ** 2
    t["aspect_ratio"] = t["axis_major_length"] / t["axis_minor_length"]
    return t


def select_endothelial(labels: np.ndarray, image: np.ndarray) -> np.ndarray:
    t = object_table(labels, image)
    if t.empty:
        raise RuntimeError("Cellpose found no objects")
    max_int = MAX_REL_INTENSITY * t["intensity_mean"].median()
    keep = (t["intensity_mean"] <= max_int) & t["area_um2"].between(MIN_AREA_UM2, MAX_AREA_UM2)
    if not keep.any():
        raise RuntimeError("All objects were rejected by the filters")
    out = np.where(np.isin(labels, t.loc[keep, "label"].to_numpy()), labels, 0)
    return relabel_sequential(out)[0].astype(np.uint16)


def save_overlay(image: np.ndarray, labels: np.ndarray, path: Path) -> None:
    g = np.clip(image / np.percentile(image, 99.8), 0, 1) ** 0.5
    rgb = np.dstack([g] * 3)
    rgb[find_boundaries(labels)] = (1, 0, 0)
    skimage.io.imsave(str(path), (rgb * 255).astype(np.uint8), check_contrast=False)


def main(inp: str, out_labels: str, out_csv: str) -> None:
    image = load_image(inp)
    raw = run_cellpose(normalise(image))
    labels = select_endothelial(raw, image)
    table = object_table(labels, image).rename(
        columns={"centroid-0": "centroid_y_px", "centroid-1": "centroid_x_px",
                 "intensity_mean": "mean_intensity"})
    table[["label", "area_um2", "aspect_ratio", "centroid_y_px", "centroid_x_px",
           "mean_intensity"]].to_csv(out_csv, index=False)
    tifffile.imwrite(out_labels, labels)
    save_overlay(image, labels, Path(out_labels).with_suffix(".overlay.png"))
    print(f"Cellpose objects: {raw.max()}; endothelial nuclei kept: {labels.max()}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
