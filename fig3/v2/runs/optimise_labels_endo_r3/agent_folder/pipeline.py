"""Segment endothelial cells in a 2D brightfield monolayer and measure shape.

Usage: python pipeline.py <input.tif> <labels.tif> <measurements.csv>

Stages (each a separate function, parameters in the CONFIG block):
 1. load + validate (2D, uint16, no silent channel/axis guessing)
 2. flatten illumination: (I - gaussian(I)) / local SD   [handles tile steps / vignetting]
 3. downscale to ~CELLPOSE_SCALE (cells ~25-50 um = 38-77 px at 0.65 um/px; the
    cpsam model was trained around 30 px objects, so 0.5x brings them to 19-38 px)
 4. Cellpose-SAM (cpsam, pretrained, CPU) instance segmentation
 5. upsample labels (nearest) back to the original pixel grid
 6. remove cancer cells sitting on top (round, very high-contrast rim)
 7. expand remaining labels into the confluent monolayer (bounded distance)
 8. drop tiny fragments, relabel, measure in um (area, aspect ratio)
Outputs: label image (int32, same shape/pixel grid as input, 0 = background) and CSV.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from skimage import measure, segmentation, transform

# ---------------------------------------------------------------- CONFIG
PIXEL_SIZE_UM = 0.65          # um / px, given by the user (not in the file metadata)
EXPECTED_DTYPE = np.uint16
FLATTEN_SIGMA_PX = 40         # gaussian sigma for background / local SD estimation
CELLPOSE_SCALE = 0.5          # image downscale factor before Cellpose
FLOW_THRESHOLD = 0.8          # Cellpose; raised from 0.4 default to keep irregular flat cells
CELLPROB_THRESHOLD = -1.0     # Cellpose; lowered from 0.0 default to recover faint cells
CANCER_RING_STD_MIN = 1.2     # objects whose boundary ring SD (flattened units) >= this are cancer cells
RING_WIDTH_PX = 3             # half-width of the boundary ring used for the feature above
EXPAND_PX = 8                 # max growth of each label (full-res px) to fill the monolayer
MIN_AREA_UM2 = 100.0          # fragments smaller than this are removed
# ----------------------------------------------------------------------


def load_image(path: Path) -> np.ndarray:
    image = tifffile.imread(path)
    if image.ndim != 2:
        raise ValueError(f"{path}: expected a 2D (Y, X) image, got shape {image.shape}")
    if image.dtype != EXPECTED_DTYPE:
        raise ValueError(f"{path}: expected dtype {np.dtype(EXPECTED_DTYPE)}, got {image.dtype}")
    if image.max() == image.min():
        raise ValueError(f"{path}: image is constant")
    return image


def flatten_illumination(image: np.ndarray, sigma: float = FLATTEN_SIGMA_PX) -> np.ndarray:
    """Zero-mean, unit-local-SD image (float32); removes slow gradients and tile offsets."""
    img = image.astype(np.float32)
    background = ndi.gaussian_filter(img, sigma)
    local_sd = np.sqrt(ndi.gaussian_filter((img - background) ** 2, sigma))
    return ((img - background) / np.maximum(local_sd, 1e-6)).astype(np.float32)


def run_cellpose(flat: np.ndarray, scale: float = CELLPOSE_SCALE) -> np.ndarray:
    """Pretrained cpsam on a downscaled image; returns labels on the ORIGINAL grid."""
    from cellpose import models  # imported here so that other stages are testable without it

    small = transform.rescale(flat, scale, order=1, anti_aliasing=True).astype(np.float32)
    model = models.CellposeModel(gpu=False)
    labels_small, _, _ = model.eval(
        small,
        diameter=None,
        flow_threshold=FLOW_THRESHOLD,
        cellprob_threshold=CELLPROB_THRESHOLD,
        normalize={"normalize": True},
    )
    return transform.resize(
        labels_small, flat.shape, order=0, preserve_range=True, anti_aliasing=False
    ).astype(np.int32)


def boundary_ring_sd(labels: np.ndarray, flat: np.ndarray, width: int = RING_WIDTH_PX) -> dict:
    """SD of flattened intensity in a ring straddling each object's boundary.
    Cancer cells (phase-bright halo + dark rim) score high; flat endothelium scores low."""
    out = {}
    pad = width + 2
    for region in measure.regionprops(labels):
        window = tuple(
            slice(max(s.start - pad, 0), s.stop + pad) for s in region.slice
        )
        mask = labels[window] == region.label
        ring = ndi.binary_dilation(mask, iterations=width) & ~ndi.binary_erosion(mask, iterations=width)
        out[region.label] = float(flat[window][ring].std())
    return out


def remove_cancer_cells(labels: np.ndarray, flat: np.ndarray, threshold: float = CANCER_RING_STD_MIN) -> np.ndarray:
    ring_sd = boundary_ring_sd(labels, flat)
    drop = [lab for lab, sd in ring_sd.items() if sd >= threshold]
    result = labels.copy()
    result[np.isin(labels, drop)] = 0
    return result


def fill_monolayer(labels: np.ndarray, distance_px: int = EXPAND_PX) -> np.ndarray:
    return segmentation.expand_labels(labels, distance=distance_px)


def remove_small(labels: np.ndarray, min_area_um2: float = MIN_AREA_UM2) -> np.ndarray:
    min_px = min_area_um2 / PIXEL_SIZE_UM**2
    counts = np.bincount(labels.ravel())
    small = np.flatnonzero(counts < min_px)
    small = small[small != 0]
    result = labels.copy()
    result[np.isin(labels, small)] = 0
    relabeled, _, _ = segmentation.relabel_sequential(result)
    return relabeled.astype(np.int32)


def measure_cells(labels: np.ndarray) -> pd.DataFrame:
    """Area (um^2) and aspect ratio (major/minor axis of the equivalent ellipse)."""
    rows = []
    height, width = labels.shape
    for r in measure.regionprops(labels):
        y0, x0, y1, x1 = r.bbox
        rows.append({
            "label": r.label,
            "area_um2": r.area * PIXEL_SIZE_UM**2,
            "aspect_ratio": r.major_axis_length / max(r.minor_axis_length, 1e-6),
            "centroid_y_um": r.centroid[0] * PIXEL_SIZE_UM,
            "centroid_x_um": r.centroid[1] * PIXEL_SIZE_UM,
            "touches_border": bool(y0 == 0 or x0 == 0 or y1 == height or x1 == width),
        })
    return pd.DataFrame(rows, columns=["label", "area_um2", "aspect_ratio", "centroid_y_um",
                                       "centroid_x_um", "touches_border"])


def postprocess(raw_labels: np.ndarray, flat: np.ndarray) -> np.ndarray:
    labels = remove_cancer_cells(raw_labels, flat)
    labels = fill_monolayer(labels)
    return remove_small(labels)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("input_tif", type=Path)
    parser.add_argument("labels_tif", type=Path)
    parser.add_argument("measurements_csv", type=Path)
    args = parser.parse_args(argv)

    image = load_image(args.input_tif)
    flat = flatten_illumination(image)
    raw_labels = run_cellpose(flat)
    labels = postprocess(raw_labels, flat)
    if labels.max() == 0:
        raise RuntimeError("No cells found; refusing to write empty outputs")

    table = measure_cells(labels)
    tifffile.imwrite(args.labels_tif, labels.astype(np.int32))
    table.to_csv(args.measurements_csv, index=False)
    print(f"{len(table)} cells ({int(table.touches_border.sum())} touch the border); "
          f"median area {table.area_um2.median():.0f} um^2, median aspect ratio {table.aspect_ratio.median():.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
