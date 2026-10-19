"""Segment endothelial cells in a brightfield monolayer and measure area / aspect ratio.

Usage: python pipeline.py <input.tif> <labels.tif> <measurements.csv>

Steps (all parameters are constants below):
 1. Load 2D uint16 image (a singleton channel axis is squeezed; anything else is an error).
 2. Correct a step in background brightness between image tiles (detected, reported).
 3. Percentile-normalise (1-99 %) to [0, 1].
 4. Downscale by SCALE (cells are ~50 px across at 0.65 um/px; Cellpose-SAM works best near 30 px).
 5. Cellpose-SAM ("cpsam_v2") on CPU, masks computed with flow/cellprob thresholds.
 6. Upscale labels (nearest neighbour) back to the original pixel grid.
 7. Remove cancer cells: round objects with a strong dark-ring/bright-halo (high-contrast pixels).
 8. Grow the remaining labels by GROW_PX to close the gaps of the confluent monolayer.
 9. Remove tiny fragments, relabel 1..N, measure in um (original pixel grid).
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from skimage import measure, segmentation
from skimage.transform import rescale, resize

PIXEL_SIZE_UM = 0.65
MODEL_NAME = "cpsam_v2"      # pinned (also the Cellpose 4.2 default); older "cpsam" misses ~half the cells here
SCALE = 0.5                   # working-resolution factor given to Cellpose
PERCENTILES = (1, 99)         # intensity normalisation
SEAM_LOG_RATIO = 0.08         # |log(right/left)| of 32-column means that counts as a tile seam
SEAM_WIDTH = 32
FLOW_THRESHOLD = 0.4
CELLPROB_THRESHOLD = 0.0
HIGHPASS_SIGMA = 15           # px, background removal for contrast feature
CONTRAST_Z = 4.0              # |high-pass| in robust SDs counted as "high contrast"
CANCER_FRACTION = 0.12        # objects with more than this fraction of high-contrast pixels are removed
GROW_PX = 7                   # label growth on the original grid (~4.5 um)
MIN_AREA_UM2 = 100.0


def load_image(path: Path) -> np.ndarray:
    image = tifffile.imread(path)
    if image.ndim == 3 and 1 in image.shape:
        image = image.reshape([n for n in image.shape if n != 1] or [1])
    if image.ndim != 2:
        raise ValueError(f"Expected a 2D single-channel image (Y, X), got shape {image.shape}")
    if image.dtype != np.uint16:
        raise ValueError(f"Expected uint16 data, got {image.dtype}")
    return image.astype(np.float32)


def correct_vertical_seam(image: np.ndarray) -> np.ndarray:
    """Equalise the two sides of the strongest vertical brightness step (tile seam), if larger than
    SEAM_LOG_RATIO. Each side is mapped affinely so its PERCENTILES match the mean of both sides'."""
    cols = image.mean(axis=0)
    csum = np.concatenate([[0], np.cumsum(cols)])
    xs = np.arange(SEAM_WIDTH, image.shape[1] - SEAM_WIDTH + 1)
    left = (csum[xs] - csum[xs - SEAM_WIDTH]) / SEAM_WIDTH
    right = (csum[xs + SEAM_WIDTH] - csum[xs]) / SEAM_WIDTH
    ratio = np.log(right / left)
    best = int(np.argmax(np.abs(ratio)))
    if abs(ratio[best]) < SEAM_LOG_RATIO:
        print("seam correction: none needed")
        return image
    x = int(xs[best])
    sides = (image[:, :x], image[:, x:])
    ranges = [np.percentile(side, PERCENTILES) for side in sides]
    target = np.mean(ranges, axis=0)
    print(f"seam correction: step at x={x}, percentiles per side {np.round(ranges, 0).tolist()} -> {np.round(target, 0).tolist()}")
    corrected = image.copy()
    for sl, (lo, hi) in zip((np.s_[:, :x], np.s_[:, x:]), ranges):
        corrected[sl] = (image[sl] - lo) / (hi - lo) * (target[1] - target[0]) + target[0]
    return corrected


def normalise(image: np.ndarray) -> np.ndarray:
    lo, hi = np.percentile(image, PERCENTILES)
    if hi <= lo:
        raise ValueError("Image has no intensity range")
    return np.clip((image - lo) / (hi - lo), 0, 1).astype(np.float32)


def run_cellpose(image01: np.ndarray) -> np.ndarray:
    """Cellpose-SAM on a downscaled copy; labels are returned on the original pixel grid."""
    from cellpose import models
    small = rescale(image01, SCALE, order=1, anti_aliasing=True)
    model = models.CellposeModel(gpu=False, pretrained_model=MODEL_NAME)
    masks = model.eval(small, flow_threshold=FLOW_THRESHOLD, cellprob_threshold=CELLPROB_THRESHOLD)[0]
    return resize(masks, image01.shape, order=0, preserve_range=True, anti_aliasing=False).astype(np.int32)


def highpass_z(image: np.ndarray) -> np.ndarray:
    hp = image - ndi.gaussian_filter(image, HIGHPASS_SIGMA)
    return hp / (1.4826 * np.median(np.abs(hp - np.median(hp))))


def remove_cancer_cells(labels: np.ndarray, image: np.ndarray) -> np.ndarray:
    high = np.abs(highpass_z(image)) > CONTRAST_Z
    ids = np.unique(labels)[1:]
    fraction = ndi.mean(high, labels, ids)
    drop = ids[np.asarray(fraction) > CANCER_FRACTION]
    print(f"removed {len(drop)} of {len(ids)} objects as high-contrast (cancer cells / debris)")
    return np.where(np.isin(labels, drop), 0, labels)


def finalise(labels: np.ndarray) -> np.ndarray:
    grown = segmentation.expand_labels(labels, GROW_PX)
    min_px = MIN_AREA_UM2 / PIXEL_SIZE_UM ** 2
    ids, counts = np.unique(grown, return_counts=True)
    small = ids[(counts < min_px) & (ids > 0)]
    grown[np.isin(grown, small)] = 0
    return segmentation.relabel_sequential(grown)[0].astype(np.int32)


def measure_cells(labels: np.ndarray) -> pd.DataFrame:
    rows = []
    h, w = labels.shape
    for r in measure.regionprops(labels):
        y0, x0, y1, x1 = r.bbox
        rows.append(dict(
            label=r.label,
            area_um2=r.area * PIXEL_SIZE_UM ** 2,
            aspect_ratio=r.axis_major_length / r.axis_minor_length,
            centroid_y_um=r.centroid[0] * PIXEL_SIZE_UM,
            centroid_x_um=r.centroid[1] * PIXEL_SIZE_UM,
            touches_border=bool(y0 == 0 or x0 == 0 or y1 == h or x1 == w),
        ))
    return pd.DataFrame(rows)


def save_overlay(image01: np.ndarray, labels: np.ndarray, path: Path) -> None:
    import skimage.io
    rgb = segmentation.mark_boundaries(np.dstack([image01] * 3), labels, color=(1, 0, 0))
    skimage.io.imsave(path, (rgb * 255).astype(np.uint8), check_contrast=False)


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("input", type=Path)
    p.add_argument("labels", type=Path)
    p.add_argument("measurements", type=Path)
    args = p.parse_args(argv)

    image = correct_vertical_seam(load_image(args.input))
    image01 = normalise(image)
    raw = run_cellpose(image01)
    print(f"cellpose objects: {raw.max()}")
    labels = finalise(remove_cancer_cells(raw, image))
    if labels.max() == 0:
        raise RuntimeError("No endothelial cells found")
    table = measure_cells(labels)
    tifffile.imwrite(args.labels, labels)
    table.to_csv(args.measurements, index=False)
    save_overlay(image01, labels, args.labels.with_name(args.labels.stem + "_overlay.png"))
    print(f"endothelial cells: {len(table)} ({int(table.touches_border.sum())} touch the image border); "
          f"median area {table.area_um2.median():.0f} um2, median aspect ratio {table.aspect_ratio.median():.2f}")


if __name__ == "__main__":
    main()
