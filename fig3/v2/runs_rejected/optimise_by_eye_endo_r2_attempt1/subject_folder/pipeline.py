"""Segment endothelial cells in a brightfield monolayer and measure area / aspect ratio.

Usage: python pipeline.py <input.tif> <labels.tif> <measurements.csv>

Steps (all parameters are constants below):
 1. read 2D uint16 image, validate
 2. detect a vertical stitching seam (step in column medians) and flatten the
    background of each side independently (median-filtered, smoothed background
    subtracted), then light Gaussian smoothing and percentile normalisation
 3. Cellpose-SAM (cpsam, Cellpose 4) on CPU, diameter given in pixels
 4. remove non-endothelial objects (cancer cells / debris: strong fine-scale
    texture mask overlapping the Cellpose object) using the flattened image
 5. write label image (original pixel grid, uint16) and a CSV (area in um^2,
    aspect ratio = major/minor axis of the equivalent ellipse) plus QC flags
Output labels are in the original pixel grid; nothing is cropped or resampled.
"""
import csv
import sys
from pathlib import Path

import numpy as np
import tifffile
from scipy import ndimage as ndi
from skimage import measure, morphology, segmentation, transform

PIXEL_SIZE_UM = 0.65
EXPECTED_DTYPE = np.uint16
MAX_12BIT = 4095

# --- seam detection / flattening
SEAM_MIN_STEP = 100.0          # counts; step in column medians to call a seam
SEAM_STEP_OVER_MEDIAN = 10.0   # step must exceed this multiple of median |step|
BG_DOWNSAMPLE = 4
BG_MEDIAN_SIZE = 15            # at downsampled scale (60 px full-res)
BG_SIGMA = 8                   # at downsampled scale (32 px full-res)
SMOOTH_SIGMA_PX = 1.0
NORM_PERCENTILES = (1, 99)

# --- Cellpose
DIAMETER_PX = 55               # ~36 um, centre of the 25-50 um range
FLOW_THRESHOLD = 0.4
CELLPROB_THRESHOLD = -1.0
MIN_SIZE_PX = 300

# --- cancer-cell / debris filter (on cellpose objects)
DOG_SIGMAS = (1, 4)
ENERGY_SIGMA = 3
CANCER_ENERGY_FRACTION = 0.75   # x per-region 90th percentile of fine-scale energy
CANCER_MASK_MIN_AREA_PX = 250
CANCER_OVERLAP_FRACTION = 0.5   # drop label if this fraction lies in the texture mask
CANCER_SMALL_OVERLAP_FRACTION = 0.25
ENDOTHELIAL_MIN_AREA_PX = 1150  # 25 um diameter circle at 0.65 um/px
TOUCH_DILATION_PX = 3


def read_image(path: Path) -> np.ndarray:
    image = tifffile.imread(path)
    if image.ndim != 2:
        raise ValueError(f"expected a 2D (Y, X) image, got shape {image.shape}")
    if image.dtype != EXPECTED_DTYPE:
        raise ValueError(f"expected uint16 image, got {image.dtype}")
    if image.max() > MAX_12BIT:
        raise ValueError(f"values exceed 12-bit range: max {image.max()}")
    return image


def find_seam(image: np.ndarray):
    """Return the column index where a second region starts, or None if no seam."""
    steps = np.abs(np.diff(np.median(image.astype(np.float32), axis=0)))
    peak = int(np.argmax(steps))
    if steps[peak] > SEAM_MIN_STEP and steps[peak] > SEAM_STEP_OVER_MEDIAN * np.median(steps):
        return peak + 1
    return None


def flatten_region(region: np.ndarray) -> np.ndarray:
    small = region[::BG_DOWNSAMPLE, ::BG_DOWNSAMPLE]
    bg = ndi.gaussian_filter(ndi.median_filter(small, size=BG_MEDIAN_SIZE, mode="reflect"),
                             BG_SIGMA, mode="reflect")
    bg = transform.resize(bg, region.shape, order=1, mode="edge")
    return region - bg


def preprocess(image: np.ndarray, seam) -> np.ndarray:
    """Flatten background per region, smooth, scale to robust ~[0,1] range."""
    img = image.astype(np.float32)
    if seam is None:
        flat = flatten_region(img)
    else:
        flat = np.concatenate([flatten_region(img[:, :seam]), flatten_region(img[:, seam:])], axis=1)
    flat = ndi.gaussian_filter(flat, SMOOTH_SIGMA_PX)
    lo, hi = np.percentile(flat, NORM_PERCENTILES)
    return ((flat - lo) / (hi - lo)).astype(np.float32)


def run_cellpose(flat: np.ndarray) -> np.ndarray:
    from cellpose import models
    model = models.CellposeModel(gpu=False, pretrained_model="cpsam")
    masks, _, _ = model.eval(flat, diameter=DIAMETER_PX, flow_threshold=FLOW_THRESHOLD,
                             cellprob_threshold=CELLPROB_THRESHOLD, normalize=True,
                             min_size=MIN_SIZE_PX)
    return masks.astype(np.int32)


def cancer_texture_mask(flat: np.ndarray, seam) -> np.ndarray:
    """Mask of strongly textured objects (cancer-cell rims/halos, debris).

    Fine-scale energy = smoothed RMS of a difference-of-Gaussians; thresholded per
    region at CANCER_ENERGY_FRACTION x its 90th percentile because the two sides of
    the stitched image differ in contrast.
    """
    dog = ndi.gaussian_filter(flat, DOG_SIGMAS[0]) - ndi.gaussian_filter(flat, DOG_SIGMAS[1])
    energy = np.sqrt(ndi.gaussian_filter(dog ** 2, ENERGY_SIGMA))
    bounds = [0, flat.shape[1]] if seam is None else [0, seam, flat.shape[1]]
    mask = np.zeros(flat.shape, bool)
    for x0, x1 in zip(bounds[:-1], bounds[1:]):
        region = energy[:, x0:x1]
        mask[:, x0:x1] = region > CANCER_ENERGY_FRACTION * np.percentile(region, 90)
    mask = ndi.binary_closing(mask, morphology.disk(3))
    mask = ndi.binary_fill_holes(mask)
    mask = ndi.binary_opening(mask, morphology.disk(5))
    return morphology.remove_small_objects(mask, max_size=CANCER_MASK_MIN_AREA_PX)


def classify_cancer(labels: np.ndarray, texture_mask: np.ndarray) -> np.ndarray:
    """Cellpose labels to drop: mostly textured, or textured and smaller than an endothelial cell."""
    ids = np.arange(1, labels.max() + 1)
    overlap = ndi.mean(texture_mask, labels=labels, index=ids)
    area = ndi.sum(np.ones_like(labels), labels=labels, index=ids)
    drop = (overlap >= CANCER_OVERLAP_FRACTION) | \
           ((overlap >= CANCER_SMALL_OVERLAP_FRACTION) & (area < ENDOTHELIAL_MIN_AREA_PX))
    return ids[drop]


def build_rows(labels: np.ndarray, cancer_mask: np.ndarray) -> list:
    near_cancer = ndi.binary_dilation(cancer_mask, iterations=TOUCH_DILATION_PX)
    rows = []
    for rp in measure.regionprops(labels):
        r0, c0, r1, c1 = rp.bbox
        on_border = r0 == 0 or c0 == 0 or r1 == labels.shape[0] or c1 == labels.shape[1]
        rows.append({
            "label": rp.label,
            "area_um2": round(rp.area * PIXEL_SIZE_UM ** 2, 2),
            "aspect_ratio": round(rp.axis_major_length / max(rp.axis_minor_length, 1e-6), 3),
            "centroid_y_um": round(rp.centroid[0] * PIXEL_SIZE_UM, 2),
            "centroid_x_um": round(rp.centroid[1] * PIXEL_SIZE_UM, 2),
            "touches_image_border": on_border,
            "touches_cancer_cell": bool(near_cancer[labels == rp.label].any()),
        })
    return rows


def write_csv(rows: list, path: str) -> None:
    fields = ["label", "area_um2", "aspect_ratio", "centroid_y_um", "centroid_x_um",
              "touches_image_border", "touches_cancer_cell"]
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def save_overlay(flat: np.ndarray, labels: np.ndarray, removed: np.ndarray, path: str) -> None:
    base = np.dstack([np.clip(flat * 0.5 + 0.4, 0, 1)] * 3)
    over = segmentation.mark_boundaries(base, labels, color=(0, 0.8, 0))
    over = segmentation.mark_boundaries(over, removed, color=(1, 0, 0))
    tifffile.imwrite(path, (over * 255).astype(np.uint8), compression="zlib")


def main(input_path: str, labels_path: str, csv_path: str, debug_dir: str = None) -> None:
    image = read_image(Path(input_path))
    seam = find_seam(image)
    print(f"seam column: {seam}")
    flat = preprocess(image, seam)
    raw = run_cellpose(flat)
    texture = cancer_texture_mask(flat, seam)
    dropped = classify_cancer(raw, texture)
    removed = np.where(np.isin(raw, dropped), raw, 0)
    kept = np.where(np.isin(raw, dropped), 0, raw)
    labels = segmentation.relabel_sequential(kept)[0].astype(np.uint16)
    rows = build_rows(labels, texture)
    tifffile.imwrite(labels_path, labels, compression="zlib")
    write_csv(rows, csv_path)
    print(f"cellpose objects {raw.max()}, removed as cancer/debris {len(dropped)}, "
          f"endothelial {len(rows)}")
    if debug_dir:
        Path(debug_dir).mkdir(exist_ok=True)
        save_overlay(flat, labels, removed, str(Path(debug_dir) / "overlay.tif"))
        np.save(Path(debug_dir) / "flat.npy", flat)
        np.save(Path(debug_dir) / "raw.npy", raw)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
