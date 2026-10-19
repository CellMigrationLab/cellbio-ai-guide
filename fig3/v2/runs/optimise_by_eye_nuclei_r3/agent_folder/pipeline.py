"""Endothelial nucleus segmentation and shape measurement (DAPI, widefield, 2D).

Usage: python pipeline.py <input.tif> <labels.tif> <measurements.csv>

Steps
1. Load and validate a single-channel 2D uint16 image (Y, X).
2. Cellpose-SAM ('cpsam', no rescaling) on percentile-normalised intensities.
3. Refine each outline at the half-maximum between local background and nucleus
   (Cellpose outlines are loose on blurred nuclei).
4. Remove cancer cells / debris: bright (relative to the image's nuclei),
   small, or non-convex objects.
5. Relabel, save label image (same Y, X grid as input) and measurements.
Pixel size is fixed by PIXEL_SIZE_UM (the image carries no usable calibration).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from skimage import measure, morphology

PIXEL_SIZE_UM = 0.65
NORM_PERCENTILES = (1.0, 99.5)      # intensity normalisation for Cellpose
CELLPOSE_MODEL = "cpsam"            # Cellpose-SAM; diameter=None -> no rescaling
FLOW_THRESHOLD = 0.4
CELLPROB_THRESHOLD = 0.0
REFINE_MAX_SHIFT_PX = 4             # outline may move at most this far
REFINE_HALF_MAX_FRACTION = 0.5
REFINE_SMOOTH_SIGMA_PX = 1.5        # smoothing used only for the refinement threshold
RING_INNER_PX, RING_OUTER_PX = 2, 7
MIN_AREA_UM2 = 70.0
MAX_AREA_UM2 = 700.0
MAX_REL_INTENSITY = 1.6             # object mean / median object mean (cancer cells are brighter)
BRIGHT_MAX_AREA_UM2 = 200.0        # large bright objects are kept (big endothelial nuclei)
MIN_SOLIDITY = 0.85


def load_image(path: Path) -> np.ndarray:
    """Read a 2D single-channel uint16 image; raise on anything else."""
    image = tifffile.imread(path)
    if image.ndim != 2:
        raise ValueError(f"Expected 2D (Y, X) image, got shape {image.shape}")
    if image.dtype != np.uint16:
        raise ValueError(f"Expected uint16, got {image.dtype}")
    return image


def normalise(image: np.ndarray) -> np.ndarray:
    lo, hi = np.percentile(image, NORM_PERCENTILES)
    if hi <= lo:
        raise ValueError("Image has no intensity range")
    return np.clip((image.astype(np.float32) - lo) / (hi - lo), 0, 1)


def run_cellpose(normalised: np.ndarray) -> np.ndarray:
    from cellpose import models
    model = models.CellposeModel(gpu=False, pretrained_model=CELLPOSE_MODEL)
    masks, _, _ = model.eval(normalised, diameter=None, batch_size=4,
                             flow_threshold=FLOW_THRESHOLD,
                             cellprob_threshold=CELLPROB_THRESHOLD,
                             normalize=False)
    return masks.astype(np.int32)


def _largest_overlapping_component(mask: np.ndarray, core: np.ndarray) -> np.ndarray:
    comp, n = ndi.label(mask)
    if n == 0:
        return mask
    overlap = np.bincount(comp[core], minlength=n + 1)
    overlap[0] = 0
    return comp == overlap.argmax()


def refine_labels(image: np.ndarray, labels: np.ndarray) -> np.ndarray:
    """Re-threshold each object at half-max between ring background and core."""
    img = ndi.gaussian_filter(image.astype(np.float32), REFINE_SMOOTH_SIGMA_PX)
    out = np.zeros_like(labels)
    footprint_out = morphology.disk(RING_OUTER_PX)
    for prop in measure.regionprops(labels):
        r0, c0, r1, c1 = prop.bbox
        pad = RING_OUTER_PX + 1
        sl = (slice(max(r0 - pad, 0), r1 + pad), slice(max(c0 - pad, 0), c1 + pad))
        lab, im = labels[sl], img[sl]
        mine = lab == prop.label
        others = (lab > 0) & ~mine
        core = ndi.binary_erosion(mine, iterations=2)
        if core.sum() < 5:
            core = mine
        ring = ndi.binary_dilation(mine, footprint_out) & ~ndi.binary_dilation(
            mine, iterations=RING_INNER_PX) & ~others
        if ring.sum() < 10:
            continue
        bg = np.percentile(im[ring], 10)
        fg = np.median(im[core])
        if fg <= bg:
            continue
        thr = bg + REFINE_HALF_MAX_FRACTION * (fg - bg)
        allowed = ndi.binary_dilation(mine, iterations=REFINE_MAX_SHIFT_PX) & ~others
        new = _largest_overlapping_component(allowed & (im > thr), core)
        new = ndi.binary_fill_holes(new)
        new = ndi.binary_opening(new, morphology.disk(2))
        new = _largest_overlapping_component(new, core) if new.any() else new
        view = out[sl]
        view[new & (view == 0)] = prop.label
    return out


def object_features(image: np.ndarray, labels: np.ndarray) -> pd.DataFrame:
    img = image.astype(np.float32)
    rows = []
    for p in measure.regionprops(labels, intensity_image=img):
        mine = labels == p.label
        ring = ndi.binary_dilation(mine, iterations=6) & ~ndi.binary_dilation(
            mine, iterations=2) & (labels == 0)
        bg = np.percentile(img[ring], 10) if ring.sum() >= 10 else np.nan
        rows.append(dict(label=p.label,
                         area_um2=p.area * PIXEL_SIZE_UM ** 2,
                         aspect_ratio=p.axis_major_length / max(p.axis_minor_length, 1e-6),
                         solidity=p.solidity, mean_intensity=p.intensity_mean,
                         signal_to_bg=p.intensity_mean / bg if bg and bg > 0 else np.nan,
                         centroid_y_px=p.centroid[0], centroid_x_px=p.centroid[1]))
    return pd.DataFrame(rows)


def classify(features: pd.DataFrame) -> pd.DataFrame:
    """Flag objects that are not endothelial nuclei (reason recorded)."""
    f = features.copy()
    f["rel_intensity"] = f.mean_intensity / f.mean_intensity.median()
    reason = pd.Series("", index=f.index)
    reason[f.area_um2 < MIN_AREA_UM2] = "small"
    reason[(f.area_um2 > MAX_AREA_UM2) & (reason == "")] = "large"
    reason[(f.rel_intensity > MAX_REL_INTENSITY) & (f.area_um2 < BRIGHT_MAX_AREA_UM2) & (reason == "")] = "bright"
    reason[(f.solidity < MIN_SOLIDITY) & (reason == "")] = "non_convex"
    f["rejected"] = reason
    return f


def build_outputs(image: np.ndarray, raw_labels: np.ndarray):
    refined = refine_labels(image, raw_labels)
    feats = classify(object_features(image, refined))
    keep = feats[feats.rejected == ""].copy()
    final = np.zeros_like(refined)
    for new_id, old_id in enumerate(keep.label, start=1):
        final[refined == old_id] = new_id
    keep["label"] = np.arange(1, len(keep) + 1)
    table = keep[["label", "area_um2", "aspect_ratio", "centroid_y_px", "centroid_x_px"]]
    return final, table, refined, feats


def main(argv: list[str]) -> None:
    if len(argv) != 4:
        raise SystemExit(__doc__)
    src, dst_labels, dst_csv = map(Path, argv[1:])
    image = load_image(src)
    raw = run_cellpose(normalise(image))
    final, table, _, _ = build_outputs(image, raw)
    tifffile.imwrite(dst_labels, final.astype(np.uint16), compression="zlib")
    table.to_csv(dst_csv, index=False)
    print(f"{len(table)} endothelial nuclei; median area "
          f"{table.area_um2.median():.1f} um2, median AR {table.aspect_ratio.median():.2f}")


if __name__ == "__main__":
    main(sys.argv)
