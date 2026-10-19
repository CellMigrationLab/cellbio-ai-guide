"""Segment endothelial nuclei (DAPI, 2D widefield) and measure area / aspect ratio.

Usage: python pipeline.py <input.tif> <labels.tif> <measurements.csv>

Steps (all parameters are constants below):
 1. Read 2D uint16 image; percentile-normalise to [0, 1] (1st-99.5th percentile).
 2. Cellpose-SAM (pretrained, no rescaling, diameter=None) -> instance masks.
 3. Per-object boundary tightening: keep pixels above background + FRACTION*(peak - background)
    (Cellpose masks include out-of-focus halo/cytoplasm haze on the dim, hazy fields).
 4. Remove small debris (< MIN_AREA_PX).
 5. Remove cancer nuclei: bright, round nuclei on top of the monolayer, detected as
    objects whose mean intensity exceeds CANCER_RATIO x the median of their
    N_NEIGHBOURS nearest objects (local reference, robust to field-to-field brightness).
 6. Relabel 1..N, write labels (uint16, same YX grid as input, so coordinates preserved)
    and measurements (area in um^2, aspect ratio = major/minor axis of fitted ellipse).
"""
import csv
import sys

import numpy as np
import tifffile
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
from skimage import measure, segmentation

PIXEL_SIZE_UM = 0.65
MODEL_NAME = "cpsam_v2"        # Cellpose 4.2 default pretrained model
NORM_PERCENTILES = (1.0, 99.5)
SMOOTH_SIGMA_PX = 1.0
FRACTION = 0.4                 # boundary threshold between local background and object peak
RING_PX = 6                    # width of ring used to estimate local background
MIN_AREA_PX = 120              # ~51 um^2; below this = debris / fragments
CANCER_RATIO = 1.5             # mean intensity / local median; endothelial ~1.0, cancer >=1.6
N_NEIGHBOURS = 40


def read_image(path: str) -> np.ndarray:
    img = np.squeeze(tifffile.imread(path))
    if img.ndim != 2:
        raise ValueError(f"Expected a single-channel 2D (Y, X) image, got shape {img.shape}")
    if img.dtype != np.uint16:
        raise ValueError(f"Expected uint16 input, got {img.dtype}")
    return img


def normalise(img: np.ndarray) -> np.ndarray:
    lo, hi = np.percentile(img, NORM_PERCENTILES)
    if hi <= lo:
        raise ValueError("Image has no intensity range; cannot normalise")
    return np.clip((img.astype(np.float32) - lo) / (hi - lo), 0, 1)


def run_cellpose(norm: np.ndarray) -> np.ndarray:
    from cellpose import models
    model = models.CellposeModel(gpu=False, pretrained_model=MODEL_NAME)
    masks = model.eval(norm, diameter=None, batch_size=4, normalize=False)[0]
    return masks.astype(np.int32)


def tighten_object(labels, smooth, region):
    """Return boolean full-size-bbox crop (slices, mask) of the tightened object, or None."""
    pad = RING_PX + 2
    r0, c0, r1, c1 = region.bbox
    sl = (slice(max(r0 - pad, 0), min(r1 + pad, labels.shape[0])),
          slice(max(c0 - pad, 0), min(c1 + pad, labels.shape[1])))
    own = labels[sl] == region.label
    sm = smooth[sl]
    ring = ndi.binary_dilation(own, iterations=RING_PX) & (labels[sl] == 0)
    if ring.sum() < 10:
        return None
    background = np.percentile(sm[ring], 20)
    peak = np.percentile(sm[own], 90)
    mask = ndi.binary_fill_holes(own & (sm > background + FRACTION * (peak - background)))
    comp, n = ndi.label(mask)
    if n == 0:
        return None
    if n > 1:
        mask = comp == (1 + int(np.argmax(ndi.sum(mask, comp, range(1, n + 1)))))
    return sl, mask


def tighten_labels(labels: np.ndarray, img: np.ndarray) -> np.ndarray:
    smooth = ndi.gaussian_filter(img.astype(np.float32), SMOOTH_SIGMA_PX)
    out = np.zeros_like(labels)
    for region in measure.regionprops(labels):
        res = tighten_object(labels, smooth, region)
        if res is not None:
            sl, mask = res
            out[sl][mask] = region.label
    return out


def remove_small(labels: np.ndarray) -> np.ndarray:
    areas = np.bincount(labels.ravel())
    small = areas < MIN_AREA_PX
    small[0] = False
    out = labels.copy()
    out[small[labels]] = 0
    return out


def cancer_ratio(regions) -> np.ndarray:
    centroids = np.array([r.centroid for r in regions])
    means = np.array([r.intensity_mean for r in regions])
    k = min(N_NEIGHBOURS, len(regions))
    _, idx = cKDTree(centroids).query(centroids, k=k)
    return means / np.median(means[idx], axis=1)


def remove_cancer(labels: np.ndarray, img: np.ndarray) -> np.ndarray:
    regions = measure.regionprops(labels, img)
    if not regions:
        raise RuntimeError("No objects found after segmentation")
    ratio = cancer_ratio(regions)
    out = labels.copy()
    for r, q in zip(regions, ratio):
        if q > CANCER_RATIO:
            out[labels == r.label] = 0
    return out


def measure_table(labels: np.ndarray, img: np.ndarray) -> list[dict]:
    rows = []
    h, w = labels.shape
    for r in measure.regionprops(labels, img):
        r0, c0, r1, c1 = r.bbox
        rows.append({
            "label": r.label,
            "centroid_y_um": r.centroid[0] * PIXEL_SIZE_UM,
            "centroid_x_um": r.centroid[1] * PIXEL_SIZE_UM,
            "area_um2": r.area * PIXEL_SIZE_UM ** 2,
            "aspect_ratio": r.axis_major_length / r.axis_minor_length,
            "mean_intensity": r.intensity_mean,
            "touches_border": bool(r0 == 0 or c0 == 0 or r1 == h or c1 == w),
        })
    return rows


def write_csv(rows: list[dict], path: str) -> None:
    fields = ["label", "centroid_y_um", "centroid_x_um", "area_um2", "aspect_ratio",
              "mean_intensity", "touches_border"]
    with open(path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main(inp: str, out_labels: str, out_csv: str) -> None:
    img = read_image(inp)
    raw = run_cellpose(normalise(img))
    tight = remove_small(tighten_labels(raw, img))
    kept = remove_cancer(tight, img)
    final, _, _ = segmentation.relabel_sequential(kept)
    final = final.astype(np.uint16)
    tifffile.imwrite(out_labels, final)
    table = measure_table(final, img)
    write_csv(table, out_csv)
    print(f"cellpose objects {raw.max()}, after tighten/size filter {len(np.unique(tight)) - 1}, "
          f"endothelial kept {len(table)}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
