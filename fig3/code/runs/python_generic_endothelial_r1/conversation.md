# python_generic_endothelial_r1

## USER (2026-10-17T04:32:23.467Z)

Act as a helpful assistant for a cell biologist. You cannot run code. You may use the Read tool ONLY to view the image the user attached: <fig3-work>/bf2/codeG_endo/bf_preview.png (a preview of their file bf.tif). Do not open anything else.

The user writes: "Please write a Python script to segment the endothelial cells in my brightfield image." (attached: bf.tif)

Reply as you normally would. Put the code in a single complete ```python block that reads bf.tif and saves the label image as labels.tif.

## HARNESS NOTE (2026-10-17T04:32:23.535Z)

<system-reminder>
Your final report is delivered through SubagentHandback: when your work is complete, call SubagentHandback({message: <your full report>}). The call ends your run, so make it your last step. Only a SubagentHandback call reaches your caller as your result; plain text you write at the end is not delivered. Do not also send the report with SendMessage: your caller would get it twice.
</system-reminder>

*[tool call: Read: <fig3-work>/bf2/codeG_endo/bf_preview.png]*

## ASSISTANT (2026-10-17T04:32:51.556Z)

I looked at your preview. It's a confluent monolayer of flat, low-contrast endothelial cells, with many bright round cells and dark debris sitting on top. The round cells look like a different cell type, such as floating or adherent immune or tumour cells. I assumed you want those excluded, so the script masks them out.

I can't run code here, so the script is untested. The thresholds are starting points that you'll need to tune on your own image.

Thresholding won't work well on this image, because the endothelial cells have almost no intensity contrast against the background and show only faint borders. I used Cellpose, which handles this kind of image better. The script does the following:
1. Flattens the uneven background and normalises the contrast.
2. Segments the cells with Cellpose.
3. Finds the high-contrast round cells and debris and removes any label that mostly overlaps them.
4. Saves `labels.tif`.

```python
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
```

**Tuning**
- **`CELL_DIAMETER`:** In your preview the flat cells look roughly 60 to 100 px across. Measure a few in Fiji and set the value, or use `None` to let Cellpose estimate it.
- **Too many cells excluded:** Raise `CONTRAST_K` or `MAX_OVERLAP`. Lower `CONTRAST_K` if round cells and debris are still being labelled.
- **Cells merged, or too few found:** Lower `CELLPOSE_PROB`, for example to -1 or -2, or lower `CELL_DIAMETER`.
- **Cell borders are faint:** The monolayer's cell outlines are subtle in the preview. If Cellpose struggles, fine-tuning it on a few images you annotate yourself (the Cellpose GUI supports this) will help more than adjusting parameters.
- **Output:** `labels.tif` is a uint16 label image where 0 is background and each cell has its own integer ID.

If the round cells are in fact the cells you want, tell me and I'll rewrite the script to target them instead.

## ASSISTANT (final report)

I looked at the preview of bf.tif. It is a confluent monolayer of flat, low-contrast endothelial cells, with many bright round cells and dark debris on top. Those look like a different cell type (floating or adherent immune or tumour cells), so I assumed the user wants them excluded.

I could not run any code, so the script below is untested and its thresholds are starting points. Thresholding would not work here because the endothelial cells have almost no contrast against the background and only faint borders. I used Cellpose instead.

The script does the following:
1. Reads bf.tif, using the first plane of a stack and converting RGB to grey.
2. Corrects uneven illumination and normalises contrast.
3. Segments the cells with Cellpose. It uses cyto3 on Cellpose v3 and cpsam on v4.
4. Builds a mask of high-contrast round cells and debris, then drops any label that mostly overlaps it or is too small.
5. Saves labels.tif as a uint16 label image, where 0 is background and each cell has its own ID.

```python
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
```

Tuning notes for the user:
- **`CELL_DIAMETER`:** Endothelial cells in the preview look roughly 60 to 100 px across. Measure a few in Fiji and set the value, or use `None` to let Cellpose estimate it.
- **Round-cell exclusion:** Lower `CONTRAST_K` if round cells and debris are still being labelled. Raise `CONTRAST_K` or `MAX_OVERLAP` if real endothelial cells are being dropped.
- **Merged or missing cells:** Lower `CELLPOSE_PROB` (for example to -1 or -2) or lower `CELL_DIAMETER`.
- **Faint borders:** If Cellpose struggles with the faint outlines, fine-tuning it on a few images the user annotates in the Cellpose GUI will help more than adjusting parameters.
- **Wrong assumption:** If the round cells are actually the target, the script needs to be rewritten to target them instead.
