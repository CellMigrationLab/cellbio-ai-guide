"""Segment endothelial DAPI nuclei (excluding bright cancer-cell nuclei) and measure shape.

Usage: python pipeline.py <input.tif> <labels.tif> <measurements.csv>

Steps (all parameters are constants below):
 1. Read 2D uint16 image (12-bit range checked); no resampling, native 0.65 um/px.
 2. Cellpose 4.2 'cpsam_v2' (pre-trained generalist, CPU), diameter=None (no rescaling),
    percentile 1-99 normalisation, flow_threshold 0.4, cellprob_threshold 0.0.
 3. Remove debris (< MIN_AREA_UM2).
 4. Remove cancer-cell nuclei: markedly brighter than the endothelial population
    (mean intensity > CANCER_INTENSITY_FACTOR x median of the dim population,
    where dim/bright are split by Otsu on log intensity).
 5. Relabel consecutively, write labels (same shape as input, uint16) and CSV.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile
from skimage.filters import threshold_otsu
from skimage.measure import regionprops_table
from skimage.segmentation import relabel_sequential

PIXEL_SIZE_UM = 0.65
MAX_12BIT = 4095
MODEL_NAME = "cpsam_v2"
FLOW_THRESHOLD = 0.4
CELLPROB_THRESHOLD = 0.0
NORM_PERCENTILES = [1, 99]
MIN_AREA_UM2 = 50.0
CANCER_INTENSITY_FACTOR = 1.6


def read_image(path: Path) -> np.ndarray:
    image = tifffile.imread(path)
    if image.ndim != 2:
        raise ValueError(f"Expected a 2D (Y, X) image, got shape {image.shape}")
    if image.dtype != np.uint16:
        raise ValueError(f"Expected uint16 data, got {image.dtype}")
    if image.max() > MAX_12BIT:
        raise ValueError(f"Values up to {image.max()} exceed the 12-bit range")
    return image


def segment_nuclei(image: np.ndarray) -> np.ndarray:
    """Cellpose instance segmentation of all nuclei (endothelial and cancer)."""
    from cellpose import models  # imported here: slow import

    model = models.CellposeModel(gpu=False, pretrained_model=MODEL_NAME)
    labels, _, _ = model.eval(
        image.astype(np.float32),
        diameter=None,
        normalize={"percentile": NORM_PERCENTILES},
        flow_threshold=FLOW_THRESHOLD,
        cellprob_threshold=CELLPROB_THRESHOLD,
    )
    return labels.astype(np.int32)


def object_table(labels: np.ndarray, image: np.ndarray) -> pd.DataFrame:
    props = regionprops_table(
        labels, intensity_image=image,
        properties=("label", "area", "axis_major_length", "axis_minor_length",
                    "intensity_mean", "bbox"),
    )
    table = pd.DataFrame(props)
    table["area_um2"] = table["area"] * PIXEL_SIZE_UM ** 2
    table["aspect_ratio"] = table["axis_major_length"] / table["axis_minor_length"]
    h, w = labels.shape
    table["touches_border"] = ((table["bbox-0"] == 0) | (table["bbox-1"] == 0)
                               | (table["bbox-2"] == h) | (table["bbox-3"] == w))
    return table


def remove_labels(labels: np.ndarray, drop: np.ndarray) -> np.ndarray:
    out = labels.copy()
    out[np.isin(out, drop)] = 0
    return out


def cancer_labels(table: pd.DataFrame) -> np.ndarray:
    """Labels of objects much brighter than the endothelial (dim) population."""
    log_i = np.log(table["intensity_mean"].to_numpy())
    dim = log_i < threshold_otsu(log_i)
    reference = np.median(table["intensity_mean"][dim])
    cutoff = CANCER_INTENSITY_FACTOR * reference
    print(f"endothelial reference intensity {reference:.0f}; cancer cutoff {cutoff:.0f}")
    return table["label"][table["intensity_mean"] > cutoff].to_numpy()


def main(input_path: str, labels_path: str, csv_path: str) -> None:
    image = read_image(Path(input_path))
    labels = segment_nuclei(image)
    print(f"cellpose objects: {labels.max()}")
    if labels.max() == 0:
        raise RuntimeError("Cellpose found no nuclei")

    table = object_table(labels, image)
    small = table["label"][table["area_um2"] < MIN_AREA_UM2].to_numpy()
    labels = remove_labels(labels, small)
    print(f"removed {len(small)} debris objects")

    table = object_table(labels, image)
    cancer = cancer_labels(table)
    labels = remove_labels(labels, cancer)
    print(f"removed {len(cancer)} bright (cancer) objects")

    labels, _, _ = relabel_sequential(labels)
    labels = labels.astype(np.uint16)
    table = object_table(labels, image)
    out = table[["label", "area_um2", "aspect_ratio", "intensity_mean", "touches_border"]]
    tifffile.imwrite(labels_path, labels)
    out.to_csv(csv_path, index=False)
    print(f"endothelial nuclei: {len(out)}; median area {out.area_um2.median():.1f} um2; "
          f"median aspect ratio {out.aspect_ratio.median():.2f}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
