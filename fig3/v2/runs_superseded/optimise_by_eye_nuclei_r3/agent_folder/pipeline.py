"""Segment endothelial nuclei (DAPI, widefield, 2D) and measure area and aspect ratio.

Usage: python pipeline.py <input.tif> <labels.tif> <measurements.csv>

Steps (all parameters are constants below):
 1. Read a 2D uint16 image (Y, X); validate.
 2. Scale intensities to [0, 1] with the 1st-99.5th percentile of the image.
 3. Cellpose 4 (cpsam_v2, CPU), no rescaling (nuclei ~20-26 px, within the model's range).
 4. Remove objects < MIN_AREA_UM2 (debris/fragments).
 5. Remove bright objects (mean raw intensity > CANCER_MEAN_INTENSITY): the cancer
    cell nuclei on top are much brighter and rounder than endothelial nuclei, except
    large elongated moderately bright ones (rescue rule).
 6. Relabel consecutively, write labels (same Y, X grid as input) and measurements.
Border-touching nuclei are kept but flagged (touches_border) as their shape is truncated.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile
from skimage import measure, segmentation

PIXEL_SIZE_UM = 0.65
PERCENTILES = (1.0, 99.5)
MIN_AREA_UM2 = 50.0
CANCER_MEAN_INTENSITY = 650.0  # raw counts (12-bit); valley of the bimodal mean-intensity histogram
# Large, elongated, moderately bright objects are kept as (S/G2 or overlapped) endothelial nuclei
RESCUE_MIN_AREA_UM2 = 210.0
RESCUE_MIN_ASPECT = 1.35
RESCUE_MAX_MEAN_INTENSITY = 900.0
FLOW_THRESHOLD = 0.4
CELLPROB_THRESHOLD = 0.0


def read_image(path: Path) -> np.ndarray:
    """Read and validate a single-channel 2D image."""
    image = tifffile.imread(path)
    if image.ndim != 2:
        raise ValueError(f"Expected a 2D (Y, X) single-channel image, got shape {image.shape}")
    if image.dtype != np.uint16:
        raise ValueError(f"Expected uint16, got {image.dtype}")
    return image


def normalise(image: np.ndarray) -> np.ndarray:
    """Percentile-scale to [0, 1] as float32."""
    low, high = np.percentile(image, PERCENTILES)
    if high <= low:
        raise ValueError("Image has no intensity range; cannot normalise")
    return np.clip((image.astype(np.float32) - low) / (high - low), 0, 1)


def run_cellpose(scaled: np.ndarray) -> np.ndarray:
    """Segment with Cellpose-SAM on CPU; returns an instance label image."""
    from cellpose import models

    model = models.CellposeModel(gpu=False, pretrained_model="cpsam_v2")
    labels, _, _ = model.eval(
        scaled, batch_size=4, normalize=False, flow_threshold=FLOW_THRESHOLD,
        cellprob_threshold=CELLPROB_THRESHOLD,
    )
    return labels.astype(np.int32)


def drop_labels(labels: np.ndarray, to_drop: list[int]) -> np.ndarray:
    out = labels.copy()
    out[np.isin(out, to_drop)] = 0
    return out


def is_cancer_like(region) -> bool:
    """Bright object, unless large, elongated and not extremely bright."""
    if region.intensity_mean <= CANCER_MEAN_INTENSITY:
        return False
    rescued = (
        region.area * PIXEL_SIZE_UM**2 >= RESCUE_MIN_AREA_UM2
        and region.axis_major_length / region.axis_minor_length >= RESCUE_MIN_ASPECT
        and region.intensity_mean <= RESCUE_MAX_MEAN_INTENSITY
    )
    return not rescued


def select_endothelial(labels: np.ndarray, image: np.ndarray) -> np.ndarray:
    """Remove small debris and bright (cancer) nuclei."""
    min_px = MIN_AREA_UM2 / PIXEL_SIZE_UM**2
    drop = [
        r.label for r in measure.regionprops(labels, intensity_image=image)
        if r.area < min_px or is_cancer_like(r)
    ]
    relabelled, _, _ = segmentation.relabel_sequential(drop_labels(labels, drop))
    return relabelled.astype(np.int32)


def measure_nuclei(labels: np.ndarray, image: np.ndarray) -> pd.DataFrame:
    """Area (um^2), aspect ratio (major/minor axis of the fitted ellipse) per label."""
    rows = []
    height, width = labels.shape
    for r in measure.regionprops(labels, intensity_image=image):
        y0, x0, y1, x1 = r.bbox
        rows.append({
            "label": r.label,
            "area_um2": r.area * PIXEL_SIZE_UM**2,
            "aspect_ratio": r.axis_major_length / r.axis_minor_length,
            "centroid_y_um": r.centroid[0] * PIXEL_SIZE_UM,
            "centroid_x_um": r.centroid[1] * PIXEL_SIZE_UM,
            "mean_intensity": r.intensity_mean,
            "touches_border": bool(y0 == 0 or x0 == 0 or y1 == height or x1 == width),
        })
    return pd.DataFrame(rows)


def main(input_path: str, labels_path: str, csv_path: str) -> None:
    image = read_image(Path(input_path))
    all_labels = run_cellpose(normalise(image))
    labels = select_endothelial(all_labels, image)
    table = measure_nuclei(labels, image)
    tifffile.imwrite(labels_path, labels, compression="zlib")
    table.to_csv(csv_path, index=False)
    print(f"Cellpose objects: {all_labels.max()}; endothelial nuclei kept: {len(table)}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
