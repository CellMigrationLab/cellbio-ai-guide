"""Segment endothelial cells in a brightfield monolayer and measure area / aspect ratio.

Usage: python pipeline.py <input.tif> <labels.tif> <measurements.csv>

Steps (all parameters are constants below):
 1. Read 2D uint16 image (Y, X), validate.
 2. Flatten background: subtract a large Gaussian-smoothed copy (removes illumination
    gradients and tile-to-tile offsets), then clip robustly to [p1, p99.5] -> float32 [0, 1].
 3. Rescale to the pixel size the model was trained for (TARGET_UM_PER_PX).
 4. Cellpose (cpsam, Cellpose 4.x) instance segmentation on CPU.
 5. Upsample labels back to the original grid (nearest neighbour), clean up, relabel.
 6. Measure area (um^2) and aspect ratio (major/minor axis of the fitted ellipse).
Labels stay in the original pixel grid; physical units use PIXEL_SIZE_UM.
"""
import sys
import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from skimage import measure, transform, morphology

PIXEL_SIZE_UM = 0.65
TARGET_UM_PER_PX = 1.1        # ~ cells of 25-50 um become ~23-45 px (cpsam trained around 30 px)
BACKGROUND_SIGMA_UM = 60.0    # larger than any cell
CLIP_PERCENTILES = (1.0, 99.5)
FLOW_THRESHOLD = 0.4
CELLPROB_THRESHOLD = 0.0
MIN_AREA_UM2 = 100.0          # drop fragments smaller than any plausible cell
BORDER_EXCLUDE = False        # keep border-touching cells (flagged in the table)


def read_image(path: str) -> np.ndarray:
    image = tifffile.imread(path)
    if image.ndim != 2:
        raise ValueError(f"Expected 2D (Y, X) image, got shape {image.shape}")
    if image.dtype != np.uint16:
        raise ValueError(f"Expected uint16, got {image.dtype}")
    if image.max() > 4095:
        raise ValueError(f"Values exceed 12-bit range: max {image.max()}")
    return image


def preprocess(image: np.ndarray) -> np.ndarray:
    """Background-flattened, robustly rescaled float32 image in [0, 1]."""
    img = image.astype(np.float32)
    background = ndi.gaussian_filter(img, BACKGROUND_SIGMA_UM / PIXEL_SIZE_UM, mode="reflect")
    flat = img - background
    lo, hi = np.percentile(flat, CLIP_PERCENTILES)
    if hi <= lo:
        raise ValueError("Image has no contrast after background subtraction")
    return np.clip((flat - lo) / (hi - lo), 0, 1).astype(np.float32)


def rescale_image(img: np.ndarray) -> np.ndarray:
    scale = PIXEL_SIZE_UM / TARGET_UM_PER_PX
    return transform.rescale(img, scale, order=1, anti_aliasing=True).astype(np.float32)


_MODEL = None


def run_cellpose(img: np.ndarray) -> np.ndarray:
    global _MODEL
    from cellpose import models
    if _MODEL is None:
        _MODEL = models.CellposeModel(gpu=False)  # default pretrained model: cpsam
    masks, _, _ = _MODEL.eval(
        img, diameter=None, flow_threshold=FLOW_THRESHOLD,
        cellprob_threshold=CELLPROB_THRESHOLD, normalize=False, batch_size=4)
    return masks


def labels_to_original_grid(masks: np.ndarray, shape: tuple) -> np.ndarray:
    return transform.resize(masks, shape, order=0, preserve_range=True,
                            anti_aliasing=False).astype(np.int32)


def clean_labels(labels: np.ndarray) -> np.ndarray:
    min_px = int(MIN_AREA_UM2 / PIXEL_SIZE_UM ** 2)
    out = np.zeros_like(labels)
    k = 0
    for region in measure.regionprops(labels):
        if region.area < min_px:
            continue
        k += 1
        sl = region.slice
        out[sl][region.image] = k
    return out


def segment(image: np.ndarray) -> np.ndarray:
    small = rescale_image(preprocess(image))
    masks = run_cellpose(small)
    return clean_labels(labels_to_original_grid(masks, image.shape))


def measure_cells(labels: np.ndarray) -> pd.DataFrame:
    rows = []
    h, w = labels.shape
    for r in measure.regionprops(labels):
        minr, minc, maxr, maxc = r.bbox
        rows.append({
            "label": r.label,
            "area_um2": r.area * PIXEL_SIZE_UM ** 2,
            "aspect_ratio": r.major_axis_length / max(r.minor_axis_length, 1e-6),
            "centroid_y_um": r.centroid[0] * PIXEL_SIZE_UM,
            "centroid_x_um": r.centroid[1] * PIXEL_SIZE_UM,
            "touches_border": bool(minr == 0 or minc == 0 or maxr == h or maxc == w),
        })
    return pd.DataFrame(rows, columns=["label", "area_um2", "aspect_ratio",
                                       "centroid_y_um", "centroid_x_um", "touches_border"])


def main(argv: list) -> None:
    if len(argv) != 4:
        raise SystemExit(__doc__)
    in_path, labels_path, csv_path = argv[1:]
    image = read_image(in_path)
    labels = segment(image)
    tifffile.imwrite(labels_path, labels.astype(np.int32))
    table = measure_cells(labels)
    table.to_csv(csv_path, index=False)
    print(f"{len(table)} cells; median area {table.area_um2.median():.0f} um2; "
          f"median aspect {table.aspect_ratio.median():.2f}")


if __name__ == "__main__":
    main(sys.argv)
