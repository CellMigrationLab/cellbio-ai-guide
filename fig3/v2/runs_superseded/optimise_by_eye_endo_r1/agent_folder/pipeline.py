"""Segment endothelial cells in a brightfield monolayer and measure area / aspect ratio.

Usage: python pipeline.py <input.tif> <labels.tif> <measurements.csv>

Steps (all parameters are constants below):
 1. Load 2D uint16 image (Y, X), no resampling of the output; labels share the input grid.
 2. Flat-field: subtract Gaussian background, divide by local SD, light smoothing.
 3. Cellpose (cpsam_v2, CPU) with diameter hint -> internal rescale to 30 px cells.
 4. Cancer-cell / debris mask from local texture (high-pass local SD) on raw image.
 5. Drop labels mostly covered by that mask, labels touching the border, and tiny labels.
 6. Relabel sequentially, measure area (um^2) and aspect ratio (major/minor axis, ellipse fit).
Overlay (<labels>_overlay.png) is written next to the label file for inspection.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from skimage import io, measure, morphology, segmentation

PIXEL_SIZE_UM = 0.65
BACKGROUND_SIGMA_PX = 60          # flat-field scale (>> cell size)
SMOOTH_SIGMA_PX = 1.0
CELL_DIAMETER_PX = 70.0           # ~45 um; Cellpose rescales by 30/70
FLOW_THRESHOLD = 0.4
CELLPROB_THRESHOLD = 0.0
TEXTURE_HP_SIGMA_PX = 25          # high-pass for texture map
TEXTURE_SD_SIGMA_PX = 4
TEXTURE_THRESHOLD = 90.0          # raw intensity units (uint16 counts, 12-bit data)
CANCER_OPEN_RADIUS_PX = 9
CANCER_MIN_AREA_PX = 300
MAX_CANCER_OVERLAP = 0.5          # drop label if more of it than this is cancer/debris mask
MIN_AREA_UM2 = 150.0


def load_image(path: str) -> np.ndarray:
    image = tifffile.imread(path)
    if image.ndim != 2:
        raise ValueError(f"Expected 2D (Y, X) image, got shape {image.shape}")
    if image.dtype != np.uint16:
        raise ValueError(f"Expected uint16 image, got {image.dtype}")
    return image.astype(np.float32)


def flatten_background(image: np.ndarray) -> np.ndarray:
    centred = image - ndi.gaussian_filter(image, BACKGROUND_SIGMA_PX)
    local_sd = np.sqrt(ndi.gaussian_filter(centred ** 2, BACKGROUND_SIGMA_PX))
    return ndi.gaussian_filter(centred / local_sd, SMOOTH_SIGMA_PX)


def run_cellpose(prepared: np.ndarray) -> np.ndarray:
    from cellpose import models
    model = models.CellposeModel(gpu=False, pretrained_model="cpsam_v2")
    labels, _, _ = model.eval(prepared, diameter=CELL_DIAMETER_PX,
                              flow_threshold=FLOW_THRESHOLD,
                              cellprob_threshold=CELLPROB_THRESHOLD)
    return labels


def cancer_debris_mask(image: np.ndarray) -> np.ndarray:
    high_pass = image - ndi.gaussian_filter(image, TEXTURE_HP_SIGMA_PX)
    texture = np.sqrt(ndi.gaussian_filter(high_pass ** 2, TEXTURE_SD_SIGMA_PX))
    mask = ndi.binary_fill_holes(texture > TEXTURE_THRESHOLD)
    mask = morphology.opening(mask, morphology.disk(CANCER_OPEN_RADIUS_PX))
    return morphology.remove_small_objects(mask, max_size=CANCER_MIN_AREA_PX)


def filter_labels(labels: np.ndarray, mask: np.ndarray) -> np.ndarray:
    border = np.unique(np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]]))
    drop = set(border.tolist())
    for region in measure.regionprops(labels, intensity_image=mask.astype(np.float32)):
        too_small = region.area * PIXEL_SIZE_UM ** 2 < MIN_AREA_UM2
        if too_small or region.mean_intensity > MAX_CANCER_OVERLAP:
            drop.add(region.label)
    kept = labels.copy()
    kept[np.isin(labels, list(drop))] = 0
    return segmentation.relabel_sequential(kept)[0].astype(np.int32)


def measure_cells(labels: np.ndarray, mask: np.ndarray) -> pd.DataFrame:
    rows = []
    for r in measure.regionprops(labels, intensity_image=mask.astype(np.float32)):
        rows.append({"label": r.label,
                     "area_um2": r.area * PIXEL_SIZE_UM ** 2,
                     "aspect_ratio": r.major_axis_length / r.minor_axis_length,
                     "centroid_y_um": r.centroid[0] * PIXEL_SIZE_UM,
                     "centroid_x_um": r.centroid[1] * PIXEL_SIZE_UM,
                     "cancer_debris_overlap": r.mean_intensity})
    return pd.DataFrame(rows, columns=["label", "area_um2", "aspect_ratio", "centroid_y_um",
                                       "centroid_x_um", "cancer_debris_overlap"])


def save_overlay(image: np.ndarray, labels: np.ndarray, path: Path) -> None:
    flat = np.clip((image - ndi.gaussian_filter(image, 40)) / 700 + 0.5, 0, 1)
    rgb = np.dstack([flat] * 3)
    rgb[segmentation.find_boundaries(labels, mode="inner")] = (1, 1, 0)
    io.imsave(path, (rgb * 255).astype(np.uint8), check_contrast=False)


def main(input_path: str, labels_path: str, csv_path: str) -> None:
    image = load_image(input_path)
    raw_labels = run_cellpose(flatten_background(image))
    mask = cancer_debris_mask(image)
    labels = filter_labels(raw_labels, mask)
    table = measure_cells(labels, mask)
    tifffile.imwrite(labels_path, labels)
    table.to_csv(csv_path, index=False)
    save_overlay(image, labels, Path(labels_path).with_name(Path(labels_path).stem + "_overlay.png"))
    print(f"cellpose labels: {raw_labels.max()}, kept endothelial cells: {len(table)}")
    print(table[["area_um2", "aspect_ratio"]].describe().round(2))


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
