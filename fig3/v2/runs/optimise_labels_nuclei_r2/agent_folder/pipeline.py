#!/usr/bin/env python
"""Endothelial nucleus segmentation + shape measurement from a 2D widefield DAPI image.

Usage: python pipeline.py <input.tif> <labels.tif> <measurements.csv>

Method (classical, deterministic, ~seconds on CPU):
  1. validate input (2D, single channel, uint16)
  2. Gaussian smoothing (sigma 1 px) of intensity clipped at CLIP_MAX
  3. local (Gaussian-weighted) adaptive threshold -> foreground, opening, hole fill
  4. distance-transform watershed to split touching nuclei
  5. classify objects: endothelial nuclei are medium-intensity, cancer nuclei on top are much
     brighter, debris is dim/small. Thresholds are RELATIVE to the median object mean intensity
     of the image (so exposure changes do not shift them) and an absolute minimum area.
  6. write label image (0 = background, 1..N endothelial nuclei) and CSV (area um^2, aspect ratio).
Cellpose was evaluated and rejected (see log.txt); no model files are needed.
Pixel size is the constant PIXEL_SIZE_UM (0.65 um, edit if your images differ); no resampling is done, so label
coordinates equal image coordinates.
"""
import argparse
import csv
import sys
import numpy as np
import tifffile
from scipy import ndimage as ndi
from skimage import feature, filters, measure, morphology, segmentation

PIXEL_SIZE_UM = 0.65
CLIP_MAX = 1000.0         # raw-intensity clip before smoothing (bright cancer nuclei otherwise dominate local threshold)
SMOOTH_SIGMA = 1.0        # px
LOCAL_BLOCK = 51          # px, adaptive threshold window (~33 um, > 2x nucleus diameter)
OPEN_RADIUS = 3           # px
DIST_SMOOTH_SIGMA = 1.5   # px, smoothing of distance map before peak detection
MIN_PEAK_DISTANCE = 6     # px (~4 um)
MIN_AREA_UM2 = 100.0      # smaller objects = debris / fragments
REL_MAX_INTENSITY = 1.5   # object mean > this x median object mean -> cancer nucleus, removed
REL_MIN_INTENSITY = 0.5   # object mean < this x median object mean -> out-of-focus/background, removed


def load_image(path: str) -> np.ndarray:
    image = tifffile.imread(path)
    if image.ndim != 2:
        raise ValueError(f"Expected a 2D (Y, X) single-channel image, got shape {image.shape}")
    if image.dtype != np.uint16:
        raise ValueError(f"Expected uint16 image, got {image.dtype}")
    if image.max() == 0:
        raise ValueError("Image is empty (all zeros)")
    return image.astype(np.float32)


def foreground_mask(image: np.ndarray) -> np.ndarray:
    smooth = filters.gaussian(np.minimum(image, CLIP_MAX), SMOOTH_SIGMA, preserve_range=True)
    local = filters.threshold_local(smooth, block_size=LOCAL_BLOCK, method="gaussian")
    mask = smooth > local
    mask = ndi.binary_opening(mask, morphology.disk(OPEN_RADIUS))
    mask = ndi.binary_fill_holes(mask)
    return morphology.remove_small_objects(mask, max_size=int(MIN_AREA_UM2 / PIXEL_SIZE_UM**2 / 3))


def split_touching(mask: np.ndarray) -> np.ndarray:
    dist = filters.gaussian(ndi.distance_transform_edt(mask), DIST_SMOOTH_SIGMA, preserve_range=True)
    peaks = feature.peak_local_max(dist, min_distance=MIN_PEAK_DISTANCE,
                                   labels=measure.label(mask), exclude_border=False)
    markers = np.zeros(mask.shape, dtype=np.int32)
    markers[tuple(peaks.T)] = np.arange(1, len(peaks) + 1)
    return segmentation.watershed(-dist, markers, mask=mask)


def select_endothelial(labels: np.ndarray, image: np.ndarray) -> np.ndarray:
    ids = np.arange(1, labels.max() + 1)
    if len(ids) == 0:
        raise RuntimeError("No candidate objects found; check image / parameters")
    mean = ndi.mean(image, labels, ids)
    area_um2 = ndi.sum(np.ones_like(image), labels, ids) * PIXEL_SIZE_UM**2
    ref = np.median(mean)
    keep = (mean <= REL_MAX_INTENSITY * ref) & (mean >= REL_MIN_INTENSITY * ref) & (area_um2 >= MIN_AREA_UM2)
    if keep.sum() == 0:
        raise RuntimeError("All objects were rejected by intensity/area filters")
    lut = np.zeros(labels.max() + 1, dtype=np.int32)
    lut[1:][keep] = np.arange(1, keep.sum() + 1)
    return lut[labels]


def measure_table(labels: np.ndarray) -> list[dict]:
    rows = []
    for r in measure.regionprops(labels):
        rows.append({"label": r.label,
                     "area_um2": r.area * PIXEL_SIZE_UM**2,
                     "aspect_ratio": r.axis_major_length / r.axis_minor_length,
                     "centroid_y_px": r.centroid[0], "centroid_x_px": r.centroid[1]})
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input"); parser.add_argument("labels"); parser.add_argument("csv")
    args = parser.parse_args()
    image = load_image(args.input)
    candidates = split_touching(foreground_mask(image))
    labels = select_endothelial(candidates, image)
    tifffile.imwrite(args.labels, labels.astype(np.int32))
    table = measure_table(labels)
    with open(args.csv, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(table[0].keys()))
        writer.writeheader()
        writer.writerows(table)
    print(f"{len(table)} endothelial nuclei (from {candidates.max()} candidates); "
          f"median area {np.median([r['area_um2'] for r in table]):.1f} um2, "
          f"median AR {np.median([r['aspect_ratio'] for r in table]):.2f}")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError, OSError) as e:
        sys.exit(f"ERROR: {e}")
