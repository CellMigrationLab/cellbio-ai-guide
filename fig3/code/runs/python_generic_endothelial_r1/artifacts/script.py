"""
Segment endothelial cells in a brightfield image (bf.tif) -> labels.tif

Requirements:  pip install cellpose tifffile scikit-image scipy numpy
(Works with Cellpose v3 and v4. A GPU is optional but makes it much faster.)

Tune the parameters in the PARAMETERS block, then check the result by
overlaying labels.tif on bf.tif in Fiji/napari.
"""
import numpy as np
import tifffile
from scipy import ndimage as ndi
from skimage import filters, morphology, measure, segmentation, exposure

# ---------------- PARAMETERS ----------------
IN_FILE = "bf.tif"
OUT_FILE = "labels.tif"

CELL_DIAMETER = 80        # approx. endothelial cell diameter in pixels (None = auto-estimate)
BG_SIGMA = 50             # Gaussian sigma for flat-field/background correction
MIN_AREA = 800            # discard labels smaller than this (pixels)
FLOW_THRESHOLD = 0.4      # Cellpose: higher = more permissive
CELLPOSE_PROB = 0.0       # Cellpose cellprob_threshold; lower = bigger/more cells

# Exclusion of the bright round cells / debris sitting on the monolayer
CONTRAST_K = 4.0          # local-contrast threshold in robust SDs; lower = excludes more
ROUND_MIN_AREA = 150      # smallest blob (px) counted as round cell/debris
ROUND_DILATE = 4          # grow the exclusion mask by this many px
MAX_OVERLAP = 0.5         # drop endothelial labels with more than this fraction covered
# --------------------------------------------


def load_gray(path):
    img = tifffile.imread(path)
    img = np.squeeze(img)
    if img.ndim == 3:
        # RGB (last axis 3/4) -> gray; otherwise take the first plane of a stack
        if img.shape[-1] in (3, 4):
            img = img[..., :3].mean(axis=-1)
        else:
            print(f"Stack with shape {img.shape}: using the first plane only.")
            img = img[0]
    return img.astype(np.float32)


def flatten(img, sigma):
    """Remove uneven illumination and normalise contrast."""
    bg = filters.gaussian(img, sigma=sigma, preserve_range=True)
    flat = img - bg
    lo, hi = np.percentile(flat, (0.5, 99.5))
    flat = np.clip((flat - lo) / (hi - lo + 1e-9), 0, 1)
    return flat.astype(np.float32)


def round_cell_mask(img, k, min_area, dilate):
    """Mask of high-contrast objects (round cells, debris, bright halos)."""
    local = img - filters.gaussian(img, sigma=15, preserve_range=True)
    absdev = filters.gaussian(np.abs(local), sigma=2, preserve_range=True)
    med = np.median(absdev)
    mad = np.median(np.abs(absdev - med)) * 1.4826 + 1e-9
    mask = absdev > med + k * mad
    mask = morphology.remove_small_objects(mask, min_area)
    mask = ndi.binary_fill_holes(mask)   # round cells have a dark rim + bright centre
    mask = morphology.binary_dilation(mask, morphology.disk(dilate))
    return mask


def run_cellpose(img):
    from cellpose import models
    try:
        import torch
        gpu = torch.cuda.is_available()
    except Exception:
        gpu = False

    if hasattr(models, "Cellpose"):          # Cellpose v3
        model = models.Cellpose(model_type="cyto3", gpu=gpu)
        masks, *_ = model.eval(
            img, diameter=CELL_DIAMETER, channels=[0, 0],
            flow_threshold=FLOW_THRESHOLD, cellprob_threshold=CELLPOSE_PROB,
        )
    else:                                     # Cellpose v4 (cpsam)
        model = models.CellposeModel(gpu=gpu)
        masks, *_ = model.eval(
            img, diameter=CELL_DIAMETER,
            flow_threshold=FLOW_THRESHOLD, cellprob_threshold=CELLPOSE_PROB,
        )
    return masks.astype(np.int32)


def main():
    raw = load_gray(IN_FILE)
    img = flatten(raw, BG_SIGMA)

    masks = run_cellpose(img)
    print(f"Cellpose found {masks.max()} objects")

    # Remove labels that are really round cells / debris
    excl = round_cell_mask(img, CONTRAST_K, ROUND_MIN_AREA, ROUND_DILATE)
    keep = np.zeros(masks.max() + 1, dtype=bool)
    for r in measure.regionprops(masks):
        rr, cc = r.coords[:, 0], r.coords[:, 1]
        overlap = excl[rr, cc].mean()
        keep[r.label] = (r.area >= MIN_AREA) and (overlap <= MAX_OVERLAP)
    keep[0] = False
    masks = masks * keep[masks]

    # Make sure the exclusion mask does not leave stray fragments inside labels
    masks[excl & (masks > 0)] = 0
    masks = morphology.remove_small_objects(masks, MIN_AREA)

    masks, _, _ = segmentation.relabel_sequential(masks)
    print(f"Kept {masks.max()} endothelial cells")

    tifffile.imwrite(OUT_FILE, masks.astype(np.uint16))
    print(f"Saved {OUT_FILE}")


if __name__ == "__main__":
    main()
