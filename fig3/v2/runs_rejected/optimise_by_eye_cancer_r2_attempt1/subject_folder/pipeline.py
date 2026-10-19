"""Segment cancer cells in 2D brightfield images (Cellpose-SAM) and measure area / aspect ratio.

Usage: python pipeline.py <input.tif> <labels.tif> <measurements.csv>
"""
import csv
import sys
from pathlib import Path

import numpy as np
import tifffile
from scipy import ndimage as ndi
from skimage import measure, morphology

PIXEL_SIZE_UM = 0.65
BACKGROUND_SIGMA_PX = 60          # flat-field: divide by heavily blurred image
LOCAL_STD_SIGMA_PX = 60           # local contrast equalisation (images have regions of differing contrast)
CELL_DIAMETER_PX = 20.0           # Cellpose diameter hint (image upscaled 1.5x); 30 missed isolated halo-ringed cells
MODEL_NAME = "cpsam_v2"           # Cellpose 4.2 default; weights in ~/.cellpose/models
FLOW_THRESHOLD = 0.4
CELLPROB_THRESHOLD = 0.0
MIN_DIAMETER_UM = 10.0            # smaller objects are debris
MAX_DIAMETER_UM = 30.0
MIN_SOLIDITY = 0.9
MIN_RIM_CONTRAST = 0.1            # (p95-p5) of flat-fielded intensity in boundary band; endothelial cells < ~0.1
RIM_BAND_PX = 3
OPENING_RADIUS_PX = 5             # removes thin tails where a mask leaks into the endothelium
NEIGHBOUR_EXCLUSION_PX = 4        # ignore band pixels near other objects when scoring rim contrast


def load_image(path: Path) -> np.ndarray:
    image = np.squeeze(tifffile.imread(path))
    if image.ndim != 2:
        raise ValueError(f"Expected a single-channel 2D image (Y, X); got shape {image.shape}")
    if image.dtype != np.uint16:
        raise ValueError(f"Expected uint16 input; got {image.dtype}")
    return image


def flat_field(image: np.ndarray) -> np.ndarray:
    img = image.astype(np.float32)
    return img / ndi.gaussian_filter(img, BACKGROUND_SIGMA_PX, mode="reflect") - 1.0


def preprocess(image: np.ndarray) -> np.ndarray:
    """Flat-field + local contrast normalisation -> float32 roughly zero-mean, unit-std."""
    img = image.astype(np.float32)
    background = ndi.gaussian_filter(img, BACKGROUND_SIGMA_PX, mode="reflect")
    flat = img / background - 1.0
    local_std = np.sqrt(ndi.gaussian_filter(flat ** 2, LOCAL_STD_SIGMA_PX, mode="reflect"))
    return (flat / local_std).astype(np.float32)


def run_cellpose(prepared: np.ndarray) -> np.ndarray:
    from cellpose import models
    model = models.CellposeModel(gpu=False, pretrained_model=MODEL_NAME)
    masks, _, _ = model.eval(
        prepared, diameter=CELL_DIAMETER_PX, normalize=True,
        flow_threshold=FLOW_THRESHOLD, cellprob_threshold=CELLPROB_THRESHOLD,
        batch_size=4,
    )
    return masks.astype(np.int32)


def open_objects(masks: np.ndarray) -> np.ndarray:
    """Per-object morphological opening; keep the largest remaining component."""
    out = np.zeros_like(masks)
    footprint = morphology.disk(OPENING_RADIUS_PX)
    for region in measure.regionprops(masks):
        pad = OPENING_RADIUS_PX + 1
        obj = np.pad(region.image, pad)
        opened = ndi.binary_opening(obj, footprint)
        comp, n = ndi.label(opened)
        if n == 0:
            continue
        sizes = ndi.sum(opened, comp, range(1, n + 1))
        keep = (comp == (1 + int(np.argmax(sizes))))[pad:-pad, pad:-pad]
        view = out[region.slice]
        view[keep] = region.label
    return out


def rim_contrast(flat: np.ndarray, masks: np.ndarray, label: int, region_slice) -> float:
    """(p95 - p5) of flat-fielded intensity in a band around the object boundary, excluding other objects."""
    band_se = morphology.disk(RIM_BAND_PX)
    r = NEIGHBOUR_EXCLUSION_PX + RIM_BAND_PX + 2
    sl = tuple(slice(max(0, s.start - r), s.stop + r) for s in region_slice)
    sub = masks[sl]
    mine = sub == label
    band = ndi.binary_dilation(mine, band_se) & ~ndi.binary_erosion(mine, band_se)
    others = ndi.binary_dilation((sub > 0) & ~mine, morphology.disk(NEIGHBOUR_EXCLUSION_PX))
    values = flat[sl][band & ~others]
    if values.size < 10:
        return 0.0
    return float(np.percentile(values, 95) - np.percentile(values, 5))


def filter_objects(masks: np.ndarray, flat: np.ndarray) -> np.ndarray:
    """Keep round, cancer-cell-sized objects with a strong halo; relabel consecutively."""
    out = np.zeros_like(masks)
    next_id = 1
    for region in measure.regionprops(masks):
        diameter_um = region.equivalent_diameter_area * PIXEL_SIZE_UM
        if not (MIN_DIAMETER_UM <= diameter_um <= MAX_DIAMETER_UM):
            continue
        if region.solidity < MIN_SOLIDITY:
            continue
        if rim_contrast(flat, masks, region.label, region.slice) < MIN_RIM_CONTRAST:
            continue
        out[masks == region.label] = next_id
        next_id += 1
    return out


def fill_holes_per_label(masks: np.ndarray) -> np.ndarray:
    out = np.zeros_like(masks)
    for region in measure.regionprops(masks):
        sl = region.slice
        filled = ndi.binary_fill_holes(region.image)
        view = out[sl]
        view[filled & (view == 0)] = region.label
    return out


def measure_cells(labels: np.ndarray):
    rows = []
    for r in measure.regionprops(labels):
        minor = r.axis_minor_length
        rows.append({
            "label": r.label,
            "area_um2": r.area * PIXEL_SIZE_UM ** 2,
            "aspect_ratio": r.axis_major_length / minor if minor > 0 else float("nan"),
            "centroid_y_um": r.centroid[0] * PIXEL_SIZE_UM,
            "centroid_x_um": r.centroid[1] * PIXEL_SIZE_UM,
        })
    return rows


def main(argv):
    if len(argv) != 4:
        raise SystemExit(__doc__)
    inp, out_labels, out_csv = map(Path, argv[1:])
    image = load_image(inp)
    masks = run_cellpose(preprocess(image))
    labels = filter_objects(open_objects(fill_holes_per_label(masks)), flat_field(image))
    tifffile.imwrite(out_labels, labels.astype(np.uint16), compression="zlib")
    rows = measure_cells(labels)
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["label", "area_um2", "aspect_ratio", "centroid_y_um", "centroid_x_um"])
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} cells")


if __name__ == "__main__":
    main(sys.argv)
