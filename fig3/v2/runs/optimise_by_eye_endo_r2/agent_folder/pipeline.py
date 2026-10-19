"""Segment endothelial cells in a brightfield monolayer and measure area / aspect ratio.

Usage: python pipeline.py <input.tif> <labels.tif> <measurements.csv>

Steps (all parameters are module constants below):
 1. Read a single-channel 2D image (Y, X); reject anything else.
 2. Detect a vertical stitching seam (abrupt brightness step between tiles) and
    flatten each side independently: subtract a Gaussian background, then rescale
    the 1-99th percentile range to 0-1. No resampling of the saved output.
 3. Cellpose (cpsam_v2, CPU) with an explicit diameter; Cellpose rescales internally
    and returns labels at the original pixel grid.
 4. Remove non-endothelial objects (cancer cells, debris: small objects), and
    endothelial cells that are cropped by the image border or partially covered
    by a cancer cell (their area/shape would be biased).
 5. Write relabelled sequential label image, measurement table and a QC overlay
    (<labels>_overlay.png).
"""
import argparse
import csv
import sys
from pathlib import Path

import numpy as np
import tifffile
from scipy import ndimage as ndi
from skimage import io, measure, segmentation

PIXEL_SIZE_UM = 0.65
CELLPOSE_MODEL = "cpsam_v2"
DIAMETER_PX = 50.0            # typical endothelial diameter (~32 um) in pixels
FLOW_THRESHOLD = 0.4
CELLPROB_THRESHOLD = 0.0
BACKGROUND_SIGMA_PX = 40.0
PERCENTILES = (1.0, 99.0)
SEAM_JUMP_FACTOR = 10.0       # seam jump must exceed this x the median column jump ...
SEAM_MIN_REL_STEP = 0.03      # ... and this fraction of the median image level
MIN_CELL_AREA_PX = 1100       # ~ circle of 25 um diameter (lower bound of stated size)
CANCER_CONTACT_FRACTION = 0.10  # max fraction of cell's rim touching small objects
RIM_PX = 3


def read_image(path: Path) -> np.ndarray:
    """Read a 2D single-channel image as float32."""
    img = tifffile.imread(path)
    if img.ndim != 2:
        raise ValueError(f"{path}: expected 2D (Y, X) image, got shape {img.shape}")
    if not np.issubdtype(img.dtype, np.integer):
        raise ValueError(f"{path}: expected integer pixel data, got {img.dtype}")
    return img.astype(np.float32)


def find_vertical_seam(img: np.ndarray) -> int | None:
    """Return the column index where a tile seam starts, or None if there is none."""
    col_mean = img.mean(axis=0)
    jumps = np.abs(np.diff(col_mean))
    idx = int(jumps.argmax())
    level = float(np.median(col_mean))
    if jumps[idx] > SEAM_JUMP_FACTOR * np.median(jumps) and jumps[idx] > SEAM_MIN_REL_STEP * level:
        return idx + 1
    return None


def flatten_and_scale(tile: np.ndarray) -> np.ndarray:
    """Subtract smooth background and scale percentile range to 0-1."""
    flat = tile - ndi.gaussian_filter(tile, BACKGROUND_SIGMA_PX)
    lo, hi = np.percentile(flat, PERCENTILES)
    if hi <= lo:
        raise ValueError("image tile has no contrast")
    return np.clip((flat - lo) / (hi - lo), 0, 1).astype(np.float32)


def preprocess(img: np.ndarray) -> np.ndarray:
    seam = find_vertical_seam(img)
    if seam is None:
        print("preprocess: no tile seam detected")
        return flatten_and_scale(img)
    print(f"preprocess: tile seam detected at column {seam}; tiles normalised separately")
    return np.concatenate([flatten_and_scale(img[:, :seam]), flatten_and_scale(img[:, seam:])], axis=1)


def run_cellpose(x: np.ndarray) -> np.ndarray:
    from cellpose import models
    model = models.CellposeModel(gpu=False, pretrained_model=CELLPOSE_MODEL)
    masks, _, _ = model.eval(
        x, diameter=DIAMETER_PX, normalize=False,
        flow_threshold=FLOW_THRESHOLD, cellprob_threshold=CELLPROB_THRESHOLD)
    return masks.astype(np.int32)


def touches_border(mask_bbox: tuple, shape: tuple) -> bool:
    r0, c0, r1, c1 = mask_bbox
    return r0 == 0 or c0 == 0 or r1 == shape[0] or c1 == shape[1]


def filter_endothelial(labels: np.ndarray) -> tuple[np.ndarray, dict]:
    """Keep complete, unoccluded endothelial cells; return filtered labels + exclusion counts."""
    props = measure.regionprops(labels)
    small = {p.label for p in props if p.area < MIN_CELL_AREA_PX}
    small_mask = np.isin(labels, list(small))
    kept = np.zeros_like(labels)
    counts = {"total": len(props), "small_nonendothelial": len(small), "border": 0, "occluded": 0}
    structure = ndi.generate_binary_structure(2, 1)
    for p in props:
        if p.label in small:
            continue
        if touches_border(p.bbox, labels.shape):
            counts["border"] += 1
            continue
        r0, c0, r1, c1 = p.bbox
        pad = RIM_PX + 1
        r0, c0 = max(r0 - pad, 0), max(c0 - pad, 0)
        r1, c1 = min(r1 + pad, labels.shape[0]), min(c1 + pad, labels.shape[1])
        own = labels[r0:r1, c0:c1] == p.label
        rim = ndi.binary_dilation(own, structure, iterations=RIM_PX) & ~own
        if (rim & small_mask[r0:r1, c0:c1]).sum() / max(rim.sum(), 1) > CANCER_CONTACT_FRACTION:
            counts["occluded"] += 1
            continue
        kept[labels == p.label] = p.label
    counts["kept"] = len(np.unique(kept)) - 1
    return kept, counts


def measure_cells(labels: np.ndarray) -> list[dict]:
    rows = []
    for p in measure.regionprops(labels):
        if p.axis_minor_length == 0:
            raise ValueError(f"label {p.label} is degenerate (zero minor axis)")
        cy, cx = p.centroid
        rows.append({
            "label": p.label,
            "area_um2": round(p.area * PIXEL_SIZE_UM ** 2, 2),
            "aspect_ratio": round(p.axis_major_length / p.axis_minor_length, 3),
            "centroid_x_px": round(cx, 1),
            "centroid_y_px": round(cy, 1),
        })
    return rows


def save_overlay(x: np.ndarray, labels: np.ndarray, raw: np.ndarray, path: Path) -> None:
    rgb = np.dstack([x] * 3)
    rgb[segmentation.find_boundaries(raw, mode="inner")] = [1, 0.6, 0]   # excluded: orange
    rgb[segmentation.find_boundaries(labels, mode="inner")] = [0, 1, 0]  # kept: green
    io.imsave(path, (rgb * 255).astype(np.uint8), check_contrast=False)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path)
    ap.add_argument("labels", type=Path)
    ap.add_argument("measurements", type=Path)
    args = ap.parse_args()

    img = read_image(args.input)
    x = preprocess(img)
    raw = run_cellpose(x)
    kept, counts = filter_endothelial(raw)
    print("filter:", counts)
    final = segmentation.relabel_sequential(kept)[0]
    rows = measure_cells(final)
    tifffile.imwrite(args.labels, final.astype(np.uint16 if final.max() < 65535 else np.uint32))
    with open(args.measurements, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["label", "area_um2", "aspect_ratio", "centroid_x_px", "centroid_y_px"])
        w.writeheader()
        w.writerows(rows)
    save_overlay(x, final, raw, args.labels.with_name(args.labels.stem + "_overlay.png"))
    print(f"wrote {len(rows)} endothelial cells")


if __name__ == "__main__":
    sys.exit(main())
