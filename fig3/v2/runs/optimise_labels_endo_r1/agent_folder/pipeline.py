"""Segment endothelial cells in a brightfield monolayer image and measure area and aspect ratio.

Usage: python pipeline.py <input.tif> <labels.tif> <measurements.csv>

Steps (all parameters are in the CONFIG block below):
  1. load + validate a single-channel 2D image (Y, X) of 12-bit data stored as uint16
  2. flatten background (coarse median filter) and clip to +-CLIP robust-scale units
  3. pass 1: Cellpose-SAM (cellpose 4.x, pretrained 'cpsam'; diameter hint = CELL_DIAMETER_PX,
     low cellprob threshold) only to locate cancer cells (small, sharp-edged, bright-ring objects)
  4. inpaint the (dilated) cancer cells in the normalised image, pass 2: Cellpose on the inpainted
     image; remaining cancer-like masks are dropped and endothelial labels grow (bounded) into the
     freed area and small gaps
  5. measure area (um^2) and aspect ratio (major/minor axis of the equivalent ellipse)
Outputs: int32 label image (0 = background, same Y/X grid as the input), CSV, and
<labels stem>_overlay.png (outlines on the contrast-stretched input) for visual checking.
"""
import argparse
import csv
import sys
import warnings
from pathlib import Path

import numpy as np
import tifffile
from scipy import ndimage as ndi
from skimage import io, measure, morphology, segmentation

# ---------------------------------------------------------------- CONFIG
PIXEL_SIZE_UM = 0.65            # um per pixel (user-provided; not read from metadata)
MAX_VALUE_12BIT = 4095          # data are 12-bit in uint16
CELL_DIAMETER_PX = 35.0         # Cellpose diameter hint (cells are ~25-50 um = ~40-75 px; see log.txt)
BG_DOWNSAMPLE = 4               # background estimated on a 4x downsampled image
BG_MEDIAN_SIZE = 15             # median window on the downsampled image (= 60 px = ~39 um)
SCALE_PERCENTILE = 75           # robust scale = 1.5 * this percentile of |image - background|
CLIP = 3.0                      # clip normalised image to [-CLIP, CLIP]
FLOW_THRESHOLD = 1.0            # Cellpose flow-error threshold (high = permissive, monolayer is confluent)
CELLPROB_THRESHOLD = -6.0       # Cellpose cell-probability threshold (low = fill the confluent layer)
MIN_SIZE_PX = 100               # discard Cellpose masks smaller than this
CANCER_GRADIENT_MIN = 25.0      # mean gaussian-gradient magnitude (sigma 1.5, raw counts) within a mask
CANCER_AREA_MAX_PX = 1500       # cancer-cell candidates must also be smaller than this (~630 um^2)
INPAINT_DILATION_PX = 4         # dilation of cancer masks before inpainting
FILL_MAX_DISTANCE_PX = 8        # maximum growth of endothelial labels into freed/empty space
# ---------------------------------------------------------------------


def load_image(path: Path) -> np.ndarray:
    """Read a single-channel 2D image and return it as float32 (Y, X)."""
    image = tifffile.imread(path)
    image = np.squeeze(image)
    if image.ndim != 2:
        raise ValueError(f"{path}: expected a single-channel 2D image (Y, X), got shape {tifffile.imread(path).shape}")
    if image.dtype != np.uint16:
        raise ValueError(f"{path}: expected uint16 data, got {image.dtype}")
    if image.max() > MAX_VALUE_12BIT:
        raise ValueError(f"{path}: maximum {image.max()} exceeds the 12-bit range ({MAX_VALUE_12BIT})")
    return image.astype(np.float32)


def flatten_and_clip(image: np.ndarray) -> np.ndarray:
    """Subtract a coarse median background and scale by a robust global amplitude, clipped to +-CLIP.

    This removes the illumination steps/gradients and limits the influence of the very bright
    and dark halos of cancer cells and debris."""
    small = image[::BG_DOWNSAMPLE, ::BG_DOWNSAMPLE]
    background = ndi.median_filter(small, size=BG_MEDIAN_SIZE, mode="reflect")
    background = ndi.zoom(background, BG_DOWNSAMPLE, order=1)[: image.shape[0], : image.shape[1]]
    residual = image - background
    scale = 1.5 * np.percentile(np.abs(residual), SCALE_PERCENTILE)
    if scale <= 0:
        raise ValueError("image has no contrast after background subtraction")
    return np.clip(residual / scale, -CLIP, CLIP).astype(np.float32)


def cellpose_labels(normalised: np.ndarray) -> np.ndarray:
    """Run pretrained Cellpose-SAM on CPU; returns int32 labels at the input resolution."""
    import torch
    from cellpose import dynamics, models

    model = models.CellposeModel(gpu=False)  # default pretrained model: cpsam
    _, flows, _ = model.eval(normalised, diameter=CELL_DIAMETER_PX, compute_masks=False)
    dP, cellprob = flows[1], flows[2]
    labels = dynamics.compute_masks(
        dP, cellprob, cellprob_threshold=CELLPROB_THRESHOLD, flow_threshold=FLOW_THRESHOLD,
        min_size=MIN_SIZE_PX, device=torch.device("cpu"))
    return labels.astype(np.int32)


def find_cancer_labels(labels: np.ndarray, image: np.ndarray) -> np.ndarray:
    """Ids of masks that look like cancer cells: small and with a sharp, high-gradient edge ring."""
    gradient = ndi.gaussian_gradient_magnitude(image, 1.5)
    ids = []
    for region in measure.regionprops(labels, intensity_image=gradient):
        if region.area < CANCER_AREA_MAX_PX and region.mean_intensity > CANCER_GRADIENT_MIN:
            ids.append(region.label)
    return np.array(ids, dtype=np.int32)


def inpaint_cancer(normalised: np.ndarray, labels: np.ndarray, cancer_ids: np.ndarray) -> np.ndarray:
    """Replace dilated cancer-cell masks by the nearest surrounding value, smoothed (sigma 3 px)."""
    mask = ndi.binary_dilation(np.isin(labels, cancer_ids), morphology.disk(INPAINT_DILATION_PX))
    nearest = ndi.distance_transform_edt(mask, return_distances=False, return_indices=True)
    filled = normalised[tuple(nearest)]
    return np.where(mask, ndi.gaussian_filter(filled, 3), normalised).astype(np.float32)


def remove_and_fill(labels: np.ndarray, cancer_ids: np.ndarray) -> np.ndarray:
    """Delete cancer masks, then grow the remaining endothelial labels into the freed space.

    Growth is limited to FILL_MAX_DISTANCE_PX so that true background stays unlabelled."""
    kept = labels.copy()
    kept[np.isin(kept, cancer_ids)] = 0
    grown = segmentation.expand_labels(kept, distance=FILL_MAX_DISTANCE_PX)
    return grown


def relabel_and_clean(labels: np.ndarray) -> np.ndarray:
    """Keep the largest connected component per label, drop tiny ones, renumber 1..N."""
    out = np.zeros_like(labels)
    next_id = 1
    for region in measure.regionprops(labels):
        sl = region.slice
        mask = region.image
        comp, n = ndi.label(mask)
        if n > 1:
            sizes = np.bincount(comp.ravel())[1:]
            mask = comp == (np.argmax(sizes) + 1)
        if mask.sum() < MIN_SIZE_PX:
            continue
        out[sl][mask] = next_id
        next_id += 1
    return out


def measure_cells(labels: np.ndarray) -> list[dict]:
    """Area (um^2), aspect ratio and border flag per label."""
    rows = []
    height, width = labels.shape
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # fail loudly rather than silently produce NaN shapes
        for r in measure.regionprops(labels):
            y0, x0, y1, x1 = r.bbox
            rows.append({
                "label": r.label,
                "area_um2": r.area * PIXEL_SIZE_UM ** 2,
                "aspect_ratio": r.axis_major_length / r.axis_minor_length,
                "centroid_y_um": r.centroid[0] * PIXEL_SIZE_UM,
                "centroid_x_um": r.centroid[1] * PIXEL_SIZE_UM,
                "touches_border": int(y0 == 0 or x0 == 0 or y1 == height or x1 == width),
            })
    return rows


def save_overlay(image: np.ndarray, labels: np.ndarray, path: Path) -> None:
    lo, hi = np.percentile(image, [0.5, 99.5])
    gray = np.clip((image - lo) / (hi - lo), 0, 1)
    rgb = segmentation.mark_boundaries(np.dstack([gray] * 3), labels, color=(1, 0, 0))
    io.imsave(path, (rgb * 255).astype(np.uint8), check_contrast=False)


def run(input_path: Path, labels_path: Path, csv_path: Path) -> None:
    image = load_image(input_path)
    normalised = flatten_and_clip(image)
    first_pass = cellpose_labels(normalised)
    inpainted = inpaint_cancer(normalised, first_pass, find_cancer_labels(first_pass, image))
    raw = cellpose_labels(inpainted)
    cancer_ids = find_cancer_labels(raw, image)
    labels = relabel_and_clean(remove_and_fill(raw, cancer_ids))
    rows = measure_cells(labels)
    if not rows:
        raise RuntimeError("no endothelial cells found")
    tifffile.imwrite(labels_path, labels.astype(np.int32))
    with open(csv_path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    save_overlay(image, labels, labels_path.with_name(labels_path.stem + "_overlay.png"))
    print(f"raw masks (pass 2): {raw.max()}, removed as cancer: {len(cancer_ids)}, endothelial cells: {len(rows)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", type=Path)
    parser.add_argument("labels", type=Path)
    parser.add_argument("measurements", type=Path)
    args = parser.parse_args()
    if not args.input.is_file():
        sys.exit(f"input not found: {args.input}")
    run(args.input, args.labels, args.measurements)
