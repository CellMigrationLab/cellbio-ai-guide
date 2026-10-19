"""Segment cancer cells in 2D brightfield (Y, X) uint16 images with Cellpose-SAM and measure shape.

Usage: python pipeline.py <input.tif> <labels.tif> <measurements.csv>

Steps (all explicit):
 1. Read image; require 2D, uint16.
 2. Flatten illumination: divide by Gaussian-blurred background (sigma = BG_SIGMA_PX), centre on 1.
 3. Cellpose 'cpsam_v2' (CPU), diameter = DIAMETER_PX (cell-size rescaling done by Cellpose),
    normalize 1-99 percentile, flow_threshold / cellprob_threshold as below.
 4. Reject non-cancer objects (endothelial cells, debris): area outside [MIN,MAX]_AREA_UM2,
    solidity < MIN_SOLIDITY, or flattened-intensity std < MIN_TEXTURE_STD.
 5. Relabel consecutively, measure area (um^2) and aspect ratio (major/minor axis of fitted ellipse).
Labels are in the original pixel grid (no resampling of the output).
"""
import csv
import json
import sys
from pathlib import Path

import numpy as np
import tifffile
from scipy import ndimage as ndi
from skimage.measure import regionprops
from skimage.segmentation import relabel_sequential

PIXEL_SIZE_UM = 0.65
BG_SIGMA_PX = 40.0
DIAMETER_PX = 25.0
FLOW_THRESHOLD = 0.4
CELLPROB_THRESHOLD = 0.0
MIN_AREA_UM2 = 80.0
MAX_AREA_UM2 = 450.0
MIN_SOLIDITY = 0.90
MIN_TEXTURE_STD = 0.04
MODEL_NAME = "cpsam_v2"


def read_image(path: str) -> np.ndarray:
    image = tifffile.imread(path)
    if image.ndim != 2:
        raise ValueError(f"Expected a 2D (Y, X) image, got shape {image.shape}")
    if image.dtype != np.uint16:
        raise ValueError(f"Expected uint16, got {image.dtype}")
    return image


def flatten_illumination(image: np.ndarray) -> np.ndarray:
    """Divide by large-scale background; output float32 with background ~1."""
    img = image.astype(np.float32)
    background = ndi.gaussian_filter(img, BG_SIGMA_PX, mode="reflect")
    if background.min() <= 0:
        raise ValueError("Non-positive background estimate; cannot flatten")
    return img / background


def run_cellpose(flat: np.ndarray) -> np.ndarray:
    from cellpose import models

    model = models.CellposeModel(gpu=False, pretrained_model=MODEL_NAME)
    masks, _, _ = model.eval(
        flat.copy(),  # copy: Cellpose may normalise its input in place
        diameter=DIAMETER_PX,
        normalize={"normalize": True, "percentile": [1, 99]},
        flow_threshold=FLOW_THRESHOLD,
        cellprob_threshold=CELLPROB_THRESHOLD,
        do_3D=False,
    )
    return masks.astype(np.int32)


def filter_objects(masks: np.ndarray, flat: np.ndarray) -> np.ndarray:
    min_px = MIN_AREA_UM2 / PIXEL_SIZE_UM**2
    max_px = MAX_AREA_UM2 / PIXEL_SIZE_UM**2
    out = masks.copy()
    for r in regionprops(masks):
        std = flat[masks == r.label].std()
        if not (min_px <= r.area <= max_px) or r.solidity < MIN_SOLIDITY or std < MIN_TEXTURE_STD:
            out[masks == r.label] = 0
    relabeled, _, _ = relabel_sequential(out)
    return relabeled.astype(np.int32)


def measure(labels: np.ndarray) -> list[dict]:
    rows = []
    for r in regionprops(labels):
        minor = r.axis_minor_length
        if minor <= 0:
            raise ValueError(f"Label {r.label} has zero minor axis length")
        rows.append({
            "label": r.label,
            "area_um2": r.area * PIXEL_SIZE_UM**2,
            "aspect_ratio": r.axis_major_length / minor,
            "centroid_y_um": r.centroid[0] * PIXEL_SIZE_UM,
            "centroid_x_um": r.centroid[1] * PIXEL_SIZE_UM,
        })
    return rows


def write_csv(rows: list[dict], path: str) -> None:
    fields = ["label", "area_um2", "aspect_ratio", "centroid_y_um", "centroid_x_um"]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def segment(image: np.ndarray) -> np.ndarray:
    flat = flatten_illumination(image)
    return filter_objects(run_cellpose(flat), flat)


def main(argv: list[str]) -> None:
    if len(argv) != 4:
        raise SystemExit(__doc__)
    inp, out_labels, out_csv = argv[1:]
    labels = segment(read_image(inp))
    tifffile.imwrite(out_labels, labels, compression="zlib")
    write_csv(measure(labels), out_csv)
    print(f"{labels.max()} cells written")


if __name__ == "__main__":
    main(sys.argv)
