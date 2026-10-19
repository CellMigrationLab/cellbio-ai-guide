"""Segment cancer cells in 2D brightfield images (on an endothelial monolayer) and measure them.

Usage: python pipeline.py <input.tif> <labels.tif> <measurements.csv>

Steps (all parameters are constants below):
 1. Read the 2D uint16 image (Y, X); reject anything else.
 2. Flatten illumination: subtract a large-sigma Gaussian background (float).
 3. Cellpose-SAM (cpsam) on CPU, diameter-matched (no rescale needed: cells ~23-38 px).
 4. Post-process: remove objects outside the plausible size range, relabel.
 5. Measure area (um^2) and aspect ratio (major/minor axis of fitted ellipse).
Labels are in the original pixel grid (no resampling of the output).
"""
import sys
import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from skimage import measure, morphology, segmentation

PIXEL_SIZE_UM = 0.65
BACKGROUND_SIGMA_PX = 50          # illumination flattening scale (>> cell size)
SMOOTH_SIGMA_PX = 1.0             # light denoising before cellpose
CELLPOSE_DIAMETER_PX = 30.0       # ~19.5 um; cpsam is trained around 30 px
FLOW_THRESHOLD = 0.4
CELLPROB_THRESHOLD = -2.0         # permissive: faint cancer cells; endothelium removed by rim filter
MIN_DIAMETER_UM = 10.0            # smaller objects are debris / not cancer cells
MAX_DIAMETER_UM = 35.0            # larger are clumps / artefacts
MIN_SOLIDITY = 0.90
MIN_RIM_GRADIENT = 26.0           # raw-intensity gradient (uint16 units) on the object rim;
                                  # cancer cells have a refractile rim, endothelium does not
RIM_GRADIENT_SIGMA_PX = 1.5
RIM_WIDTH_PX = 3
TAIL_OPENING_RADIUS_PX = 6        # removes polygon tails where a mask leaks into endothelium


def read_image(path: str) -> np.ndarray:
    img = tifffile.imread(path)
    if img.ndim != 2:
        raise ValueError(f"Expected a 2D (Y, X) image, got shape {img.shape}")
    if img.dtype != np.uint16:
        raise ValueError(f"Expected uint16, got {img.dtype}")
    return img


def preprocess(img: np.ndarray) -> np.ndarray:
    """Flatten illumination and smooth; returns float32 (cellpose normalises by percentiles)."""
    f = img.astype(np.float32)
    f -= ndi.gaussian_filter(f, BACKGROUND_SIGMA_PX)
    return ndi.gaussian_filter(f, SMOOTH_SIGMA_PX).astype(np.float32)


def run_cellpose(image: np.ndarray) -> np.ndarray:
    from cellpose import models
    model = models.CellposeModel(gpu=False)
    masks, _, _ = model.eval(
        image, diameter=CELLPOSE_DIAMETER_PX, flow_threshold=FLOW_THRESHOLD,
        cellprob_threshold=CELLPROB_THRESHOLD, normalize=True, batch_size=4)
    return masks.astype(np.int32)


def remove_tails(labels: np.ndarray) -> np.ndarray:
    """Morphological opening per object; keeps the largest remaining component."""
    footprint = morphology.disk(TAIL_OPENING_RADIUS_PX)
    out = np.zeros_like(labels)
    for r in measure.regionprops(labels):
        y0, x0, y1, x1 = r.bbox
        pad = TAIL_OPENING_RADIUS_PX + 1
        sl = (slice(max(y0 - pad, 0), y1 + pad), slice(max(x0 - pad, 0), x1 + pad))
        mask = labels[sl] == r.label
        opened = ndi.binary_opening(np.pad(mask, pad), footprint)[pad:-pad, pad:-pad]
        cc, n = ndi.label(opened)
        if n == 0:
            continue
        keep = cc == (np.argmax(np.bincount(cc.ravel())[1:]) + 1)
        out[sl][keep] = r.label
    return out


def rim_gradient(labels: np.ndarray, img: np.ndarray) -> dict:
    grad = ndi.gaussian_gradient_magnitude(img.astype(np.float32), RIM_GRADIENT_SIGMA_PX)
    result = {}
    for r in measure.regionprops(labels):
        mask = labels == r.label
        rim = mask & ~ndi.binary_erosion(mask, iterations=RIM_WIDTH_PX)
        result[r.label] = float(grad[rim].mean())
    return result


def filter_objects(labels: np.ndarray, img: np.ndarray) -> np.ndarray:
    labels = remove_tails(labels)
    rim = rim_gradient(labels, img)
    min_area = np.pi / 4 * (MIN_DIAMETER_UM / PIXEL_SIZE_UM) ** 2
    max_area = np.pi / 4 * (MAX_DIAMETER_UM / PIXEL_SIZE_UM) ** 2
    out = np.zeros_like(labels)
    for r in measure.regionprops(labels):
        if (min_area <= r.area <= max_area and r.solidity >= MIN_SOLIDITY
                and rim[r.label] >= MIN_RIM_GRADIENT):
            out[labels == r.label] = r.label
    out, _, _ = segmentation.relabel_sequential(out)
    return out.astype(np.int32)


def measure_cells(labels: np.ndarray) -> pd.DataFrame:
    h, w = labels.shape
    rows = []
    for r in measure.regionprops(labels):
        y0, x0, y1, x1 = r.bbox
        rows.append({
            "label": r.label,
            "area_um2": r.area * PIXEL_SIZE_UM ** 2,
            "aspect_ratio": r.axis_major_length / r.axis_minor_length,
            "centroid_y_um": r.centroid[0] * PIXEL_SIZE_UM,
            "centroid_x_um": r.centroid[1] * PIXEL_SIZE_UM,
            "touches_border": bool(y0 == 0 or x0 == 0 or y1 == h or x1 == w),
        })
    return pd.DataFrame(rows, columns=["label", "area_um2", "aspect_ratio",
                                       "centroid_y_um", "centroid_x_um", "touches_border"])


def main(inp: str, out_labels: str, out_csv: str) -> None:
    img = read_image(inp)
    labels = filter_objects(run_cellpose(preprocess(img)), img)
    tifffile.imwrite(out_labels, labels, compression="zlib")
    table = measure_cells(labels)
    table.to_csv(out_csv, index=False)
    print(f"{len(table)} cells; median area {table.area_um2.median():.0f} um2")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
