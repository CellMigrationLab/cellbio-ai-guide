"""Segment endothelial nuclei in a 2D DAPI widefield image and measure shape.

Usage: python pipeline.py <input.tif> <labels.tif> <measurements.csv>

Steps (all parameters are constants below):
 1. Load 2D uint16 image (Y, X); validate.
 2. Background subtraction: Gaussian(1 px) -> grey opening (disk 20 px) -> Gaussian(10 px);
    subtract and clip at 0. Removes cytoplasmic haze / out-of-focus glow.
 3. Intensity scaling: divide by the 99th percentile, clip to [0, 1.5], gamma 1.5
    (suppresses dim haze that Cellpose otherwise segments as cell bodies).
 4. Cellpose-SAM ('cpsam', Cellpose 4.x), no resizing (nuclei ~20-40 px, close to training scale),
    internal normalisation off, default flow/cellprob thresholds.
 5. Remove debris (< MIN_AREA_UM2) and cancer cells (bright AND round, see classify).
 6. Write label image (same pixel grid as input) + table in physical units (um).
Extra outputs next to the label file: <labels>_overlay.png, <labels>_all_objects.csv (incl. rejected, with reason).
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from skimage import filters, io, measure, morphology, segmentation

PIXEL_SIZE_UM = 0.65
BG_SMOOTH_SIGMA_PX = 1.0
BG_OPENING_RADIUS_PX = 20      # > half of the largest nucleus minor axis (~26 px)
BG_FINAL_SIGMA_PX = 10.0
SCALE_PERCENTILE = 99.0
SCALE_CLIP_MAX = 1.5
GAMMA = 1.5
CELLPOSE_MODEL = "cpsam"
MIN_AREA_UM2 = 40.0            # ~95 px; smaller objects are debris / fragments
CANCER_INTENSITY_RATIO = 2.0   # mean intensity > ratio * median of all objects ...
CANCER_MAX_ASPECT = 1.35       # ... and round -> cancer cell on top
CANCER_VERY_BRIGHT_RATIO = 3.5 # very bright objects rejected regardless of shape


def load_image(path: Path) -> np.ndarray:
    image = tifffile.imread(path)
    if image.ndim != 2:
        raise ValueError(f"Expected a 2D (Y, X) image, got shape {image.shape}")
    if image.dtype != np.uint16:
        raise ValueError(f"Expected uint16 image, got {image.dtype}")
    if image.max() == 0:
        raise ValueError("Image is empty (all zeros)")
    return image


def subtract_background(image: np.ndarray) -> np.ndarray:
    smooth = filters.gaussian(image.astype(np.float32), BG_SMOOTH_SIGMA_PX, preserve_range=True)
    background = morphology.opening(smooth, morphology.disk(BG_OPENING_RADIUS_PX))
    background = filters.gaussian(background, BG_FINAL_SIGMA_PX, preserve_range=True)
    return np.clip(image.astype(np.float32) - background, 0, None)


def scale_for_cellpose(corrected: np.ndarray) -> np.ndarray:
    top = np.percentile(corrected, SCALE_PERCENTILE)
    if top <= 0:
        raise ValueError("Background-corrected image has no signal at the scaling percentile")
    return np.clip(corrected / top, 0, SCALE_CLIP_MAX) ** GAMMA


def run_cellpose(scaled: np.ndarray) -> np.ndarray:
    from cellpose import models
    model = models.CellposeModel(gpu=False, pretrained_model=CELLPOSE_MODEL)
    labels = model.eval(scaled, batch_size=4, normalize=False)[0]
    return labels.astype(np.int32)


def measure_objects(labels: np.ndarray, image: np.ndarray) -> pd.DataFrame:
    props = measure.regionprops_table(
        labels, image,
        properties=("label", "area", "centroid", "axis_major_length", "axis_minor_length",
                    "intensity_mean", "bbox"))
    table = pd.DataFrame(props)
    h, w = labels.shape
    table["area_um2"] = table["area"] * PIXEL_SIZE_UM ** 2
    table["aspect_ratio"] = table["axis_major_length"] / table["axis_minor_length"]
    table["centroid_y_um"] = table["centroid-0"] * PIXEL_SIZE_UM
    table["centroid_x_um"] = table["centroid-1"] * PIXEL_SIZE_UM
    table["touches_border"] = ((table["bbox-0"] == 0) | (table["bbox-1"] == 0)
                               | (table["bbox-2"] == h) | (table["bbox-3"] == w))
    return table


def classify(table: pd.DataFrame) -> pd.DataFrame:
    """Add 'reject_reason' ('' = kept endothelial nucleus)."""
    median_intensity = table["intensity_mean"].median()
    ratio = table["intensity_mean"] / median_intensity
    reason = pd.Series("", index=table.index)
    reason[table["area_um2"] < MIN_AREA_UM2] = "debris"
    bright_round = (ratio > CANCER_INTENSITY_RATIO) & (table["aspect_ratio"] < CANCER_MAX_ASPECT)
    reason[(reason == "") & (bright_round | (ratio > CANCER_VERY_BRIGHT_RATIO))] = "cancer_cell"
    table = table.copy()
    table["intensity_ratio"] = ratio
    table["reject_reason"] = reason
    return table


def save_overlay(image, labels, path: Path) -> None:
    base = np.clip(image / np.percentile(image, 99.8), 0, 1) ** 0.6
    rgb = segmentation.mark_boundaries(np.dstack([base] * 3), labels, color=(1, 0, 0), mode="inner")
    io.imsave(path, (rgb * 255).astype(np.uint8), check_contrast=False)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("input", type=Path)
    parser.add_argument("labels", type=Path)
    parser.add_argument("measurements", type=Path)
    args = parser.parse_args(argv)
    if not args.input.is_file():
        raise FileNotFoundError(args.input)

    image = load_image(args.input)
    raw_labels = run_cellpose(scale_for_cellpose(subtract_background(image)))
    table = classify(measure_objects(raw_labels, image))

    kept = table[table["reject_reason"] == ""]
    lut = np.zeros(raw_labels.max() + 1, dtype=np.int32)
    lut[kept["label"].to_numpy()] = np.arange(1, len(kept) + 1)
    final = lut[raw_labels]
    kept = kept.assign(label=np.arange(1, len(kept) + 1))

    tifffile.imwrite(args.labels, final.astype(np.uint16), compression="zlib")
    out_cols = ["label", "area_um2", "aspect_ratio", "centroid_y_um", "centroid_x_um",
                "intensity_mean", "touches_border"]
    kept[out_cols].to_csv(args.measurements, index=False)
    stem = args.labels.with_suffix("")
    table.drop(columns=[c for c in table if c.startswith("bbox")]).to_csv(
        f"{stem}_all_objects.csv", index=False)
    save_overlay(image, final, Path(f"{stem}_overlay.png"))
    print(f"cellpose objects: {len(table)}; rejected: "
          f"{table['reject_reason'].value_counts().drop('', errors='ignore').to_dict()}; "
          f"endothelial nuclei: {len(kept)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
