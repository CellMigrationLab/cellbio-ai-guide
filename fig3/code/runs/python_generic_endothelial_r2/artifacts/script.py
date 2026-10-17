#!/usr/bin/env python
"""
Segment flat endothelial cells in a brightfield / phase-like image.

Input : bf.tif
Output: labels.tif  (uint16 label image, 0 = background, 1..N = cells)

Requirements:  pip install cellpose tifffile scikit-image scipy numpy
(A GPU is optional but makes Cellpose much faster.)

Pipeline
  1. Read the image, reduce it to 2D, flatten uneven illumination.
  2. Find the small, round, high-contrast (refractile) cells and debris that
     sit on top of the monolayer, so they can be excluded.
  3. Run Cellpose on the flattened image to segment the flat endothelial cells.
  4. Drop labels that mostly overlap the round cells/debris or are too small,
     clean up the rest, relabel and save.
"""
import numpy as np
import tifffile
from scipy import ndimage as ndi
from skimage import filters, morphology, measure, segmentation

# ----------------------------- parameters ---------------------------------
INPUT = "bf.tif"
OUTPUT = "labels.tif"

DIAMETER = 60          # typical endothelial cell diameter in pixels (adjust!)
FLOW_THRESHOLD = 0.4   # Cellpose: raise to keep more (looser) cells
CELLPROB_THRESHOLD = -1.0  # Cellpose: lower = more/larger cells (faint cells need < 0)
BG_SIGMA = 50          # gaussian sigma (px) for illumination flattening
HIGH_CONTRAST_K = 4.0  # robust z-score above which a pixel counts as "refractile"
MIN_AREA = 400         # px; smaller labels are discarded
MAX_OVERLAP = 0.30     # discard labels with > this fraction covered by round cells/debris
REMOVE_ROUND_CELLS = True
USE_GPU = True
# ---------------------------------------------------------------------------


def load_2d(path):
    img = tifffile.imread(path)
    img = np.squeeze(img)
    if img.ndim == 3:
        # (C,Y,X) or (Y,X,C) or a z-stack: pick the smallest axis as channel/z and average
        ax = int(np.argmin(img.shape))
        print(f"Image has shape {img.shape}; averaging over axis {ax}")
        img = img.mean(axis=ax)
    return img.astype(np.float32)


def flatten(img):
    """Remove uneven illumination and normalise to a roughly unit-variance image."""
    bg = filters.gaussian(img, sigma=BG_SIGMA, preserve_range=True)
    flat = img - bg
    lo, hi = np.percentile(flat, (0.5, 99.5))
    flat = np.clip(flat, lo, hi)
    return (flat - flat.mean()) / (flat.std() + 1e-6)


def refractile_mask(flat):
    """Mask of the strongly contrasted round cells and debris (very bright or very dark)."""
    med = np.median(flat)
    mad = np.median(np.abs(flat - med)) * 1.4826 + 1e-6
    z = np.abs(flat - med) / mad
    m = z > HIGH_CONTRAST_K
    m = morphology.remove_small_objects(m, 15)
    m = morphology.binary_closing(m, morphology.disk(4))
    m = ndi.binary_fill_holes(m)
    m = morphology.binary_dilation(m, morphology.disk(2))
    return m


def run_cellpose(img):
    from cellpose import models
    model = models.CellposeModel(gpu=USE_GPU)   # works for Cellpose 3.x and 4.x
    masks, _, _ = model.eval(
        img,
        diameter=DIAMETER,
        flow_threshold=FLOW_THRESHOLD,
        cellprob_threshold=CELLPROB_THRESHOLD,
    )
    return masks


def main():
    raw = load_2d(INPUT)
    flat = flatten(raw)

    masks = run_cellpose(flat)
    print(f"Cellpose found {masks.max()} objects")

    if REMOVE_ROUND_CELLS:
        bad = refractile_mask(flat)
    else:
        bad = np.zeros_like(masks, dtype=bool)

    out = np.zeros_like(masks, dtype=np.int32)
    keep = 0
    for r in measure.regionprops(masks):
        if r.area < MIN_AREA:
            continue
        sl = r.slice
        region = masks[sl] == r.label
        overlap = bad[sl][region].mean()
        if overlap > MAX_OVERLAP:
            continue
        # remove the pixels covered by round cells from kept labels, fill small holes
        region_clean = region & ~bad[sl]
        region_clean = morphology.binary_opening(region_clean, morphology.disk(2))
        if region_clean.sum() < MIN_AREA:
            continue
        keep += 1
        out[sl][region_clean] = keep

    # make sure each label is one connected component, then relabel sequentially
    out = measure.label(out > 0, connectivity=1) * 0 + out  # keep ids
    out, _, _ = segmentation.relabel_sequential(out)
    print(f"Kept {out.max()} endothelial cells")

    tifffile.imwrite(OUTPUT, out.astype(np.uint16))
    print(f"Saved {OUTPUT}")


if __name__ == "__main__":
    main()
