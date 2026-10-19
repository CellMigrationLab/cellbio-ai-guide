"""Segment cancer cells in 2D brightfield images and measure area and aspect ratio.

Usage: python pipeline.py <input.tif> <labels.tif> <measurements.csv>

Steps: validate -> flatten background / local contrast normalisation (float32)
-> Cellpose (cpsam, CPU) at the native pixel size -> size/border-aware label
clean-up -> regionprops.  Labels stay in the input pixel grid (no resampling
of the output); areas are in um^2.
"""
import csv
import sys
from pathlib import Path

import numpy as np
import tifffile
from scipy import ndimage as ndi
from skimage import measure, transform

PIXEL_SIZE_UM = 0.65
DIAMETER_PX = 30.0            # ~19.5 um, middle of 15-25 um range / 0.65
BACKGROUND_SIGMA_UM = 40.0    # scale of illumination / panel-level flattening
CELLPROB_THRESHOLD = 0.0
FLOW_THRESHOLD = 0.4
MIN_AREA_UM2 = 100.0          # ~11 um diameter; removes debris
MAX_AREA_UM2 = 700.0          # ~30 um diameter; rejects endothelial cells / clumps
EDGE_SIGMA_PX = 1.5           # gaussian-gradient scale for edge strength
EDGE_CONTEXT_PX = 100         # window (px) for local median gradient (4x downsampled)
MIN_EDGE_RATIO = 2.0          # cancer cells have a strong halo/rim edge vs. local background
MIN_SOLIDITY = 0.9            # rejects merged/irregular objects
MODEL = "cpsam"


def load_image(path: Path) -> np.ndarray:
    image = tifffile.imread(path)
    if image.ndim != 2:
        raise ValueError(f"Expected a 2D (Y, X) image, got shape {image.shape}")
    if image.dtype != np.uint16:
        raise ValueError(f"Expected uint16, got {image.dtype}")
    if image.max() > 4095:
        raise ValueError("Values exceed 12-bit range (4095)")
    return image


def flatten_and_normalise(image: np.ndarray) -> np.ndarray:
    """Subtract a smooth background and divide by local contrast (std).

    The input can have panel-to-panel offsets/contrast differences, so global
    percentile scaling is not safe.  Result is float32 with ~unit local std.
    """
    img = image.astype(np.float32)
    sigma = BACKGROUND_SIGMA_UM / PIXEL_SIZE_UM
    # median-ish background: robust to cells via a large median on a 4x downsample
    small = transform.downscale_local_mean(img, (4, 4))
    bg = ndi.median_filter(small, size=int(sigma / 4) * 2 + 1, mode="reflect")
    bg = transform.resize(bg, img.shape, order=1, mode="edge")
    resid = img - bg
    var = ndi.gaussian_filter(resid ** 2, sigma)
    return (resid / np.sqrt(var + 1e-6)).astype(np.float32)


def run_cellpose(normalised: np.ndarray) -> np.ndarray:
    from cellpose import models
    model = models.CellposeModel(gpu=False, pretrained_model=MODEL)
    masks, _, _ = model.eval(
        normalised, diameter=DIAMETER_PX, normalize=True,
        flow_threshold=FLOW_THRESHOLD, cellprob_threshold=CELLPROB_THRESHOLD,
        min_size=int(MIN_AREA_UM2 / PIXEL_SIZE_UM ** 2),
    )
    return masks.astype(np.int32)


def edge_ratio_map(image: np.ndarray) -> np.ndarray:
    """Gradient magnitude divided by its local median (illumination-independent)."""
    grad = ndi.gaussian_gradient_magnitude(image.astype(np.float32), EDGE_SIGMA_PX)
    small = ndi.median_filter(grad[::4, ::4], size=EDGE_CONTEXT_PX // 4, mode="reflect")
    local = np.kron(small, np.ones((4, 4), dtype=np.float32))[: grad.shape[0], : grad.shape[1]]
    return grad / np.maximum(local, 1.0)


def clean_labels(masks: np.ndarray, edge_ratio: np.ndarray) -> np.ndarray:
    """Fill holes, keep round-ish cancer-sized objects with strong boundary edges, relabel.

    Endothelial cells (also segmented by Cellpose) have weak boundaries in
    brightfield; cancer cells are rimmed by a bright halo / dark ring.
    """
    out = np.zeros_like(masks)
    next_id = 1
    for region in measure.regionprops(masks):
        sl = region.slice
        filled = ndi.binary_fill_holes(region.image)
        area_um2 = filled.sum() * PIXEL_SIZE_UM ** 2
        if not MIN_AREA_UM2 <= area_um2 <= MAX_AREA_UM2:
            continue
        boundary = region.image ^ ndi.binary_erosion(region.image)
        if edge_ratio[sl][boundary].mean() < MIN_EDGE_RATIO:
            continue
        if measure.regionprops(filled.astype(np.uint8))[0].solidity < MIN_SOLIDITY:
            continue
        view = out[sl]
        view[filled & (view == 0)] = next_id
        next_id += 1
    return out


def measure_labels(labels: np.ndarray) -> list[dict]:
    rows = []
    h, w = labels.shape
    for r in measure.regionprops(labels):
        minr, minc, maxr, maxc = r.bbox
        minor = r.axis_minor_length
        rows.append({
            "label": r.label,
            "area_um2": round(r.area * PIXEL_SIZE_UM ** 2, 3),
            "aspect_ratio": round(r.axis_major_length / minor, 4) if minor > 0 else float("nan"),
            "centroid_y_px": round(r.centroid[0], 2),
            "centroid_x_px": round(r.centroid[1], 2),
            "touches_border": int(minr == 0 or minc == 0 or maxr == h or maxc == w),
        })
    return rows


def write_csv(rows: list[dict], path: Path) -> None:
    fields = ["label", "area_um2", "aspect_ratio", "centroid_y_px", "centroid_x_px", "touches_border"]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str]) -> None:
    if len(argv) != 4:
        raise SystemExit(__doc__)
    src, dst_labels, dst_csv = map(Path, argv[1:])
    image = load_image(src)
    masks = run_cellpose(flatten_and_normalise(image))
    labels = clean_labels(masks, edge_ratio_map(image))
    tifffile.imwrite(dst_labels, labels.astype(np.uint16), compression="zlib")
    rows = measure_labels(labels)
    write_csv(rows, dst_csv)
    print(f"{len(rows)} cells (raw cellpose objects: {masks.max()})")


if __name__ == "__main__":
    main(sys.argv)
