"""Segment cancer cells in 2D brightfield images (on an endothelial monolayer) and measure them.

Usage: python pipeline.py <input.tif> <labels.tif> <measurements.csv>

Steps: validate -> flat-field + percentile normalisation -> Cellpose-SAM (cpsam) ->
size/shape filtering -> relabel -> measure (area um^2, aspect ratio). Labels are in the
input pixel grid (no resampling of the output); pixel size is a constant below.
"""
import csv
import sys

import numpy as np
import tifffile
from scipy import ndimage as ndi
from skimage import measure, segmentation

PIXEL_SIZE_UM = 0.65
EXPECTED_MAX_VALUE = 4095          # 12-bit data stored in uint16
BACKGROUND_SIGMA_PX = 50           # flat-field: gaussian sigma for illumination estimate
NORM_PERCENTILES = (1.0, 99.0)
CELLPOSE_DIAMETER_PX = None        # None: cpsam default (no rescaling)
FLOW_THRESHOLD = 0.4
CELLPROB_THRESHOLD = 0.0
MIN_AREA_UM2 = 100.0
MAX_AREA_UM2 = 700.0
MIN_SOLIDITY = 0.90
MIN_TEXTURE_RATIO = 2.5            # object intensity SD / robust background SD (flat-fielded); rejects smooth endothelium


def load_image(path: str) -> np.ndarray:
    img = tifffile.imread(path)
    if img.ndim != 2:
        raise ValueError(f"Expected a 2D (Y, X) image, got shape {img.shape}")
    if img.dtype != np.uint16:
        raise ValueError(f"Expected uint16, got {img.dtype}")
    if img.max() > EXPECTED_MAX_VALUE:
        raise ValueError(f"Max value {img.max()} exceeds 12-bit range {EXPECTED_MAX_VALUE}")
    return img


def flat_fielded(img: np.ndarray) -> np.ndarray:
    x = img.astype(np.float32)
    return x - ndi.gaussian_filter(x, BACKGROUND_SIGMA_PX)


def normalise(img: np.ndarray) -> np.ndarray:
    """Subtract slowly varying illumination, then scale robust percentiles to [0, 1]."""
    x = flat_fielded(img)
    lo, hi = np.percentile(x, NORM_PERCENTILES)
    if hi <= lo:
        raise ValueError("Image has no contrast after normalisation")
    return np.clip((x - lo) / (hi - lo), 0, 1).astype(np.float32)


def run_cellpose(x: np.ndarray) -> np.ndarray:
    from cellpose import models
    model = models.CellposeModel(gpu=False)
    masks, _, _ = model.eval(
        x, diameter=CELLPOSE_DIAMETER_PX, flow_threshold=FLOW_THRESHOLD,
        cellprob_threshold=CELLPROB_THRESHOLD, normalize=False)
    return masks.astype(np.int32)


def filter_objects(labels: np.ndarray, img: np.ndarray) -> np.ndarray:
    """Keep cancer-cell-like objects: expected size, convex, and strongly textured
    (bright rim / dark edge) relative to the background noise of the image."""
    ff = flat_fielded(img)
    noise = 1.4826 * np.median(np.abs(ff - np.median(ff)))
    out = labels.copy()
    for r in measure.regionprops(labels, intensity_image=ff):
        area = r.area * PIXEL_SIZE_UM ** 2
        texture = r.image_intensity[r.image].std() / noise
        if (not (MIN_AREA_UM2 <= area <= MAX_AREA_UM2) or r.solidity < MIN_SOLIDITY
                or texture < MIN_TEXTURE_RATIO):
            out[labels == r.label] = 0
    return segmentation.relabel_sequential(out)[0].astype(np.int32)


def measure_cells(labels: np.ndarray) -> list[dict]:
    rows = []
    for r in measure.regionprops(labels):
        rows.append({
            "label": r.label,
            "area_um2": r.area * PIXEL_SIZE_UM ** 2,
            "aspect_ratio": r.axis_major_length / r.axis_minor_length,
            "centroid_y_px": r.centroid[0],
            "centroid_x_px": r.centroid[1],
            "touches_border": int(r.bbox[0] == 0 or r.bbox[1] == 0
                                  or r.bbox[2] == labels.shape[0] or r.bbox[3] == labels.shape[1]),
        })
    return rows


def main(inp: str, out_labels: str, out_csv: str) -> None:
    img = load_image(inp)
    labels = filter_objects(run_cellpose(normalise(img)), img)
    tifffile.imwrite(out_labels, labels)
    rows = measure_cells(labels)
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["label", "area_um2", "aspect_ratio",
                                          "centroid_y_px", "centroid_x_px", "touches_border"])
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} cells")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
