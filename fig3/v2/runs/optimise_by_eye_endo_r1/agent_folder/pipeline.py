"""Endothelial cell segmentation + shape measurement from brightfield (Cellpose-SAM, CPU).

Usage: python pipeline.py <input.tif> <labels.tif> <measurements.csv>

Steps (all parameters are constants below):
 1. Read 2D uint16 image (Y, X); validate.
 1b. Detect the seam between the two fields (left/right) and process each field separately.
 2. Flatten: subtract Gaussian background and divide by local SD (sigma 40 px).
 3. Downscale x0.5 (0.65 -> 1.3 um/px) so 25-50 um cells are ~19-38 px (Cellpose-SAM native ~30 px).
 4. Cellpose-SAM (cpsam_v2), fixed diameter (no auto size estimation), CPU.
 5. Upsample labels to the original grid (nearest neighbour), relabel connected pieces.
 6. Remove non-endothelial objects: small round objects (cancer cells), tiny fragments,
    border-touching cells (incomplete shape).
 7. Measure area (um^2) and aspect ratio (major/minor axis of the fitted ellipse) in original pixels.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from skimage import measure, segmentation, transform

PIXEL_SIZE_UM = 0.65
FLATTEN_SIGMA_PX = 40
SCALE = 0.5
CELLPOSE_MODEL = "cpsam_v2"
CELLPROB_THRESHOLD = 0.0
FLOW_THRESHOLD = 0.4
CELL_DIAMETER_PX = 30.0  # in the downscaled image (Cellpose-SAM native scale)
SEAM_MIN_RATIO = 5.0  # seam jump must exceed the next-largest column jump by this factor
MIN_AREA_UM2 = 150.0
CANCER_MAX_AREA_UM2 = 400.0
CANCER_MIN_SOLIDITY = 0.90
CANCER_MAX_ASPECT = 1.5
CANCER_TEXTURE_MIN_SD = 1.3  # SD of flattened intensity inside object (bright halo / dark rim / granular)
CANCER_TEXTURE_MAX_AREA_UM2 = 700.0


def read_image(path: str) -> np.ndarray:
    image = tifffile.imread(path)
    if image.ndim != 2:
        raise ValueError(f"Expected a 2D (Y, X) single-channel image, got shape {image.shape}")
    if image.dtype != np.uint16:
        raise ValueError(f"Expected uint16, got {image.dtype}")
    if image.max() > 4095:
        raise ValueError("Values exceed 12-bit range (4095)")
    return image


def find_field_seam(image: np.ndarray) -> int:
    """Column index where the right field starts (largest jump in column-mean intensity)."""
    jumps = np.abs(np.diff(image.astype(np.float64).mean(axis=0)))
    order = np.argsort(jumps)
    best, second = jumps[order[-1]], jumps[order[-2]]
    if best < SEAM_MIN_RATIO * second:
        raise ValueError(f"No clear seam between two fields (jump {best:.1f} vs next {second:.1f})")
    return int(order[-1]) + 1


def flatten(image: np.ndarray) -> np.ndarray:
    """Local background subtraction and contrast normalisation."""
    x = image.astype(np.float32)
    background = ndi.gaussian_filter(x, FLATTEN_SIGMA_PX)
    local_sd = np.sqrt(ndi.gaussian_filter((x - background) ** 2, FLATTEN_SIGMA_PX))
    if local_sd.min() <= 0:
        raise ValueError("Zero local contrast region; cannot normalise")
    return (x - background) / local_sd


def run_cellpose(flat: np.ndarray) -> np.ndarray:
    from cellpose import models

    small = transform.rescale(flat, SCALE, order=1, anti_aliasing=True)
    model = models.CellposeModel(gpu=False, pretrained_model=CELLPOSE_MODEL)
    labels, _, _ = model.eval(
        small,
        diameter=CELL_DIAMETER_PX,
        flow_threshold=FLOW_THRESHOLD,
        cellprob_threshold=CELLPROB_THRESHOLD,
        batch_size=1,
    )
    return labels


def upsample_labels(labels: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    big = transform.resize(labels, shape, order=0, preserve_range=True, anti_aliasing=False)
    return big.astype(np.int32)


def filter_endothelial(labels: np.ndarray, flat: np.ndarray) -> np.ndarray:
    """Drop cancer-like (small round convex, or small high-contrast), tiny and border-touching objects."""
    out = np.zeros_like(labels)
    h, w = labels.shape
    k = 0
    for r in measure.regionprops(labels):
        area = r.area * PIXEL_SIZE_UM**2
        minr, minc, maxr, maxc = r.bbox
        if minr == 0 or minc == 0 or maxr == h or maxc == w:
            continue
        if area < MIN_AREA_UM2:
            continue
        aspect = r.major_axis_length / max(r.minor_axis_length, 1e-6)
        if area < CANCER_TEXTURE_MAX_AREA_UM2 and flat[r.slice][r.image].std() > CANCER_TEXTURE_MIN_SD:
            continue
        if area < CANCER_MAX_AREA_UM2 and r.solidity > CANCER_MIN_SOLIDITY and aspect < CANCER_MAX_ASPECT:
            continue
        k += 1
        out[labels == r.label] = k
    return out


def measure_cells(labels: np.ndarray) -> pd.DataFrame:
    rows = []
    for r in measure.regionprops(labels):
        rows.append({
            "label": r.label,
            "area_um2": r.area * PIXEL_SIZE_UM**2,
            "aspect_ratio": r.major_axis_length / r.minor_axis_length,
            "centroid_y_um": r.centroid[0] * PIXEL_SIZE_UM,
            "centroid_x_um": r.centroid[1] * PIXEL_SIZE_UM,
        })
    return pd.DataFrame(rows, columns=["label", "area_um2", "aspect_ratio", "centroid_y_um", "centroid_x_um"])


def main(input_path: str, labels_path: str, csv_path: str) -> None:
    image = read_image(input_path)
    seam = find_field_seam(image)
    raw = np.zeros(image.shape, np.int32)
    labels = np.zeros(image.shape, np.int32)
    for cols in (slice(0, seam), slice(seam, image.shape[1])):  # each field is processed independently
        field = image[:, cols]
        flat = flatten(field)
        field_raw = upsample_labels(run_cellpose(flat), field.shape)
        field_labels = filter_endothelial(field_raw, flat)  # also drops cells cut by the seam
        raw[:, cols] = np.where(field_raw > 0, field_raw + raw.max(), 0)
        labels[:, cols] = np.where(field_labels > 0, field_labels + labels.max(), 0)
    tifffile.imwrite(labels_path, labels.astype(np.uint16))
    table = measure_cells(labels)
    table.to_csv(csv_path, index=False)
    stem = Path(labels_path).with_suffix("")
    tifffile.imwrite(f"{stem}_raw_cellpose.tif", raw.astype(np.uint16))
    lo, hi = np.percentile(image, [0.5, 99.5])
    rgb = np.dstack([np.clip((image - lo) / (hi - lo), 0, 1)] * 3)
    rgb[segmentation.find_boundaries(raw, mode="inner")] = (1, 0, 1)
    rgb[segmentation.find_boundaries(labels, mode="inner")] = (0, 1, 0)
    tifffile.imwrite(f"{stem}_overlay.tif", (rgb * 255).astype(np.uint8))
    print(f"{len(table)} endothelial cells (raw Cellpose objects: {raw.max()})")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
