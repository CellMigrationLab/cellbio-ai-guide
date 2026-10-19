"""Endothelial nuclei segmentation + shape measurement (DAPI, 2D widefield).

Usage: python pipeline.py <input.tif> <labels.tif> <measurements.csv>

Steps (all parameters are constants below):
 1. Read 2D uint16 image (Y, X); input file is never modified.
 2. Normalise: clip to per-image [1, 99.8] percentiles, scale to 0-1 (Cellpose input only).
 3. Cellpose-SAM (cpsam, Cellpose 4.x), CPU, diameter=None (model default; tested vs 23 px, no gain),
    flow_threshold=0.4, cellprob_threshold=0. Native pixel grid: no resizing, labels keep input coordinates.
 4. Remove cancer-cell nuclei (bright, on top of the monolayer) and debris:
    - keep objects whose median raw intensity < BRIGHT_FACTOR * (median over all objects of the object median)
      (relative to the image, so it adapts to exposure; assumes endothelial nuclei are the majority)
    - keep objects with area >= MIN_AREA_UM2
 5. Relabel consecutively; measure area (um^2) and aspect ratio (major/minor axis of the ellipse with the
    same second moments, skimage regionprops).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile
from skimage import measure, segmentation

PIXEL_SIZE_UM = 0.65
PERCENTILES = (1.0, 99.8)
FLOW_THRESHOLD = 0.4
CELLPROB_THRESHOLD = 0.0
BRIGHT_FACTOR = 1.45     # object median intensity cutoff, x image-wide median of object medians
MIN_AREA_UM2 = 90.0      # below this: debris / fragments (annotated nuclei: 5th percentile 120 um^2)
EXPECTED_MAX_VALUE = 4095  # 12-bit data


def read_image(path: str) -> np.ndarray:
    img = np.squeeze(tifffile.imread(path))
    if img.ndim != 2:
        raise ValueError(f"Expected a 2D single-channel image (Y, X), got shape {img.shape}")
    if img.dtype != np.uint16:
        raise ValueError(f"Expected uint16, got {img.dtype}")
    if img.max() > EXPECTED_MAX_VALUE:
        raise ValueError(f"Max value {img.max()} exceeds 12-bit range; check the image")
    if img.max() == img.min():
        raise ValueError("Image is constant")
    return img


def normalise(img: np.ndarray) -> np.ndarray:
    lo, hi = np.percentile(img, PERCENTILES)
    return np.clip((img.astype(np.float32) - lo) / (hi - lo), 0, 1)


def run_cellpose(norm: np.ndarray) -> np.ndarray:
    from cellpose import models
    model = models.CellposeModel(gpu=False)
    masks = model.eval(norm, diameter=None, flow_threshold=FLOW_THRESHOLD,
                       cellprob_threshold=CELLPROB_THRESHOLD, batch_size=4)[0]
    return masks.astype(np.int32)


def object_medians(img: np.ndarray, labels: np.ndarray) -> dict[int, float]:
    return {r.label: float(np.median(img[r.slice][r.image])) for r in measure.regionprops(labels)}


def filter_endothelial(img: np.ndarray, labels: np.ndarray) -> np.ndarray:
    """Drop bright (cancer) nuclei and small debris. Returns labels (not yet relabelled)."""
    medians = object_medians(img, labels)
    if not medians:
        raise RuntimeError("Cellpose found no objects")
    cutoff = BRIGHT_FACTOR * float(np.median(list(medians.values())))
    min_px = MIN_AREA_UM2 / PIXEL_SIZE_UM ** 2
    areas = {r.label: r.area for r in measure.regionprops(labels)}
    keep = [l for l, m in medians.items() if m < cutoff and areas[l] >= min_px]
    print(f"objects {len(medians)}, intensity cutoff {cutoff:.0f}, kept {len(keep)}")
    return np.where(np.isin(labels, keep), labels, 0)


def measure_labels(labels: np.ndarray) -> pd.DataFrame:
    rows = [{"label": r.label,
             "area_um2": r.area * PIXEL_SIZE_UM ** 2,
             "aspect_ratio": r.axis_major_length / r.axis_minor_length,
             "centroid_y_px": r.centroid[0], "centroid_x_px": r.centroid[1]}
            for r in measure.regionprops(labels)]
    return pd.DataFrame(rows, columns=["label", "area_um2", "aspect_ratio", "centroid_y_px", "centroid_x_px"])


def main(inp: str, out_labels: str, out_csv: str) -> None:
    img = read_image(inp)
    raw = run_cellpose(normalise(img))
    labels = filter_endothelial(img, raw)
    labels, _, _ = segmentation.relabel_sequential(labels)
    labels = labels.astype(np.int32)
    tifffile.imwrite(out_labels, labels)
    measure_labels(labels).to_csv(out_csv, index=False)
    print(f"{labels.max()} endothelial nuclei -> {out_labels}, {out_csv}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
