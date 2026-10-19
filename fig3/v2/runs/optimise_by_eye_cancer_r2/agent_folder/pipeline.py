"""Segment rounded cancer cells in brightfield images and measure area / aspect ratio.

Usage: python pipeline.py <input.tif> <labels.tif> <measurements.csv>
"""
import csv
import sys

import numpy as np
import tifffile
from scipy import ndimage as ndi
from skimage import measure, segmentation

PIXEL_SIZE_UM = 0.65
CELLPOSE_DIAMETER_PX = 30.0       # ~19.5 um; cpsam training mean diameter
CELLPROB_THRESHOLD = -1.0          # permissive: recovers faint/isolated cells; false positives removed by filter_objects
FLOW_THRESHOLD = 0.0               # 0 disables the flow-error check (it dropped valid cells)
MIN_AREA_UM2 = 100.0              # below this: debris / fragments (~11 um equiv. diameter)
MAX_AREA_UM2 = 700.0              # above this: clumps / flat endothelial cells (~30 um equiv. diameter)
MIN_HALO_SCORE = 0.25             # normalised-intensity units; separates rounded refractile cells from flat endothelium
MIN_SOLIDITY = 0.90               # rounded cells are convex; rejects ragged debris / irregular endothelium
HALO_BAND_PX = 3                  # inner boundary band width
HALO_RING_PX = (3, 8)             # outside reference ring (distance from mask)
SEAM_JUMP_FRACTION = 0.05         # column-median step (relative) treated as tile seam
NORM_PERCENTILES = (1.0, 99.0)


def load_image(path: str) -> np.ndarray:
    image = tifffile.imread(path)
    if image.ndim != 2:
        raise ValueError(f"Expected a 2D (Y, X) image, got shape {image.shape}")
    if image.dtype != np.uint16:
        raise ValueError(f"Expected uint16 input, got {image.dtype}")
    return image


def find_seams(image: np.ndarray) -> list[int]:
    """Columns where the column-median brightness steps abruptly (stitched tiles)."""
    col = np.median(image.astype(np.float64), axis=0)
    step = np.abs(np.diff(col)) / np.median(col)
    return [int(i) + 1 for i in np.flatnonzero(step > SEAM_JUMP_FRACTION)]


def normalise_by_segment(image: np.ndarray, seams: list[int]) -> np.ndarray:
    """Percentile-normalise each seam-delimited column block independently (float32)."""
    out = np.empty(image.shape, np.float32)
    edges = [0, *seams, image.shape[1]]
    for x0, x1 in zip(edges[:-1], edges[1:]):
        block = image[:, x0:x1].astype(np.float32)
        lo, hi = np.percentile(block, NORM_PERCENTILES)
        out[:, x0:x1] = (block - lo) / (hi - lo)
    return out


def run_cellpose(image: np.ndarray) -> np.ndarray:
    from cellpose import models
    model = models.CellposeModel(gpu=False, pretrained_model="cpsam")
    masks, _, _ = model.eval(
        image, diameter=CELLPOSE_DIAMETER_PX, normalize=False,
        flow_threshold=FLOW_THRESHOLD, cellprob_threshold=CELLPROB_THRESHOLD,
        batch_size=4)
    return masks.astype(np.int32)


def halo_score(norm: np.ndarray, masks: np.ndarray, region) -> float:
    """Optical halo strength of a rounded cell: max(bright rim - background, background - dark rim).

    Rounded, refractile cancer cells have a strong bright/dark rim in brightfield;
    flat endothelial cells do not. Computed in a padded bounding box.
    """
    pad = HALO_RING_PX[1] + 1
    y0, x0, y1, x1 = region.bbox
    sl = (slice(max(y0 - pad, 0), y1 + pad), slice(max(x0 - pad, 0), x1 + pad))
    inside = masks[sl] == region.label
    dist_in = ndi.distance_transform_edt(inside)
    dist_out = ndi.distance_transform_edt(~inside)
    band = inside & (dist_in <= HALO_BAND_PX)
    ring = (~inside) & (dist_out > HALO_RING_PX[0]) & (dist_out <= HALO_RING_PX[1])
    if ring.sum() < 10:
        return 0.0
    img = norm[sl]
    background = np.median(img[ring])
    return float(max(np.percentile(img[band], 90) - background, background - np.percentile(img[band], 10)))


def filter_objects(norm: np.ndarray, masks: np.ndarray) -> np.ndarray:
    """Keep objects in the cancer-cell area range with a strong rim; relabel 1..N."""
    out = masks.copy()
    for r in measure.regionprops(masks):
        area_um2 = r.area * PIXEL_SIZE_UM ** 2
        if not MIN_AREA_UM2 <= area_um2 <= MAX_AREA_UM2 or r.solidity < MIN_SOLIDITY \
                or halo_score(norm, masks, r) < MIN_HALO_SCORE:
            out[masks == r.label] = 0
    return segmentation.relabel_sequential(out)[0].astype(np.int32)


def measure_cells(labels: np.ndarray) -> list[dict]:
    h, w = labels.shape
    rows = []
    for r in measure.regionprops(labels):
        y0, x0, y1, x1 = r.bbox
        rows.append({
            "label": r.label,
            "area_um2": round(r.area * PIXEL_SIZE_UM ** 2, 3),
            "aspect_ratio": round(r.axis_major_length / max(r.axis_minor_length, 1e-9), 4),
            "centroid_y_um": round(r.centroid[0] * PIXEL_SIZE_UM, 2),
            "centroid_x_um": round(r.centroid[1] * PIXEL_SIZE_UM, 2),
            "touches_border": int(y0 == 0 or x0 == 0 or y1 == h or x1 == w),
        })
    return rows


def main(inp: str, out_labels: str, out_csv: str) -> None:
    image = load_image(inp)
    seams = find_seams(image)
    print(f"seams at columns: {seams}")
    norm = normalise_by_segment(image, seams)
    raw_masks = run_cellpose(norm)
    labels = filter_objects(norm, raw_masks)
    rows = measure_cells(labels)
    tifffile.imwrite(out_labels, labels.astype(np.uint16))
    fields = ["label", "area_um2", "aspect_ratio", "centroid_y_um", "centroid_x_um", "touches_border"]
    with open(out_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"cellpose objects: {raw_masks.max()}, kept: {len(rows)}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
