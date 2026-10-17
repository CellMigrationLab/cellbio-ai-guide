# python_generic_endothelial_r3

## USER (2026-10-17T05:57:40.354Z)

Act as a helpful assistant for a cell biologist. You cannot run code. You may use the Read tool ONLY to view the image the user attached: <fig3-work>/bf3/gen_endo_r3/bf_preview.png (a preview of their file bf.tif). Do not open anything else.

The user writes: "Please write a Python script to segment the endothelial cells in my brightfield image." (attached: bf.tif)

Reply as you normally would. Put the code in a single complete ```python block that reads bf.tif and saves the label image as labels.tif.

## HARNESS NOTE (2026-10-17T05:57:40.395Z)

<system-reminder>
Your final report is delivered through SubagentHandback: when your work is complete, call SubagentHandback({message: <your full report>}). The call ends your run, so make it your last step. Only a SubagentHandback call reaches your caller as your result; plain text you write at the end is not delivered. Do not also send the report with SendMessage: your caller would get it twice.
</system-reminder>

*[tool call: Read: <fig3-work>/bf3/gen_endo_r3/bf_preview.png]*

## ASSISTANT (final report)

I looked at your preview. It is a confluent, low-contrast monolayer of flat polygonal endothelial cells, with faint borders and textured nuclei. On top of it sit many small round, bright-rimmed cells (probably loosely attached or suspension cells) plus dark debris. Simple thresholding will not work on this kind of image, because the endothelial cells have almost no intensity contrast against the background. I would use a pretrained deep-learning segmenter (Cellpose) after flat-field correction, then drop the round cells and debris. I could not run any code here, so the script below is untested.

```python
"""
Segment endothelial cells in a brightfield image (bf.tif) -> labels.tif

Requirements:  pip install cellpose tifffile scikit-image scipy numpy
Works with Cellpose 3 and 4. A GPU is strongly recommended but not required.
"""
import numpy as np
import tifffile
from scipy import ndimage as ndi
from skimage import exposure, filters, morphology, measure, segmentation
from cellpose import models

# ---------------- parameters to tune ----------------
INPUT = "bf.tif"
OUTPUT = "labels.tif"
DIAMETER = 70          # typical endothelial cell diameter in PIXELS (measure a few in Fiji)
FLOW_THRESHOLD = 0.4
CELLPROB_THRESHOLD = -1.0   # lower = more/larger cells, higher = stricter
MIN_AREA = 800         # px; remove small fragments
REMOVE_ROUND_CELLS = True   # exclude the bright, round, loosely attached cells
USE_GPU = True
# ----------------------------------------------------

# 1. Load (take first plane if it is a stack / has channels)
img = tifffile.imread(INPUT).astype(np.float32)
while img.ndim > 2:
    img = img[0] if img.shape[0] < 5 or img.ndim > 3 else img.mean(axis=0)
print("Image shape:", img.shape)

# 2. Flat-field correction (removes uneven illumination) and contrast boost
background = filters.gaussian(img, sigma=100, preserve_range=True)
flat = img - background
flat = (flat - np.percentile(flat, 0.5)) / (np.percentile(flat, 99.5) - np.percentile(flat, 0.5))
flat = np.clip(flat, 0, 1)
flat = exposure.equalize_adapthist(flat, kernel_size=128, clip_limit=0.02)

# 3. Cellpose segmentation
model = models.CellposeModel(gpu=USE_GPU)
masks, flows, styles = model.eval(
    flat,
    diameter=DIAMETER,
    flow_threshold=FLOW_THRESHOLD,
    cellprob_threshold=CELLPROB_THRESHOLD,
)
masks = np.asarray(masks).astype(np.int32)
print("Cellpose objects:", masks.max())

# 4. Optionally mask out the small round, high-contrast cells sitting on the monolayer.
#    They have much stronger local contrast (dark rim + bright halo) than the flat endothelium.
if REMOVE_ROUND_CELLS:
    local_sd = np.sqrt(np.maximum(
        filters.gaussian(flat**2, 3) - filters.gaussian(flat, 3) ** 2, 0))
    strong = local_sd > filters.threshold_otsu(local_sd) * 1.3
    strong = morphology.binary_closing(strong, morphology.disk(3))
    strong = ndi.binary_fill_holes(strong)
    strong = morphology.remove_small_objects(strong, 150)
    # keep only compact, roughly round blobs of the right size (round cells ~ 20-45 px)
    blob_lbl = measure.label(strong)
    round_mask = np.zeros_like(strong)
    for r in measure.regionprops(blob_lbl):
        if 150 < r.area < 3000 and r.solidity > 0.85 and r.eccentricity < 0.8:
            round_mask[blob_lbl == r.label] = True
    round_mask = morphology.binary_dilation(round_mask, morphology.disk(4))

    # remove endothelial labels that are mostly covered by round cells
    for r in measure.regionprops(masks):
        sl = masks == r.label
        if round_mask[sl].mean() > 0.5:
            masks[sl] = 0
    # cut round-cell footprints out of the remaining labels
    masks[round_mask] = 0

# 5. Clean up: remove tiny pieces, fill holes, keep one connected piece per label
clean = np.zeros_like(masks)
new_id = 1
for r in measure.regionprops(masks):
    m = masks == r.label
    m = ndi.binary_fill_holes(m)
    lab, n = ndi.label(m)
    if n > 1:
        sizes = ndi.sum(m, lab, range(1, n + 1))
        m = lab == (np.argmax(sizes) + 1)
    if m.sum() >= MIN_AREA:
        clean[m & (clean == 0)] = new_id
        new_id += 1

clean, _, _ = segmentation.relabel_sequential(clean)
print("Final endothelial cells:", clean.max())

# 6. Save
tifffile.imwrite(OUTPUT, clean.astype(np.uint16))
print("Saved", OUTPUT)
```

What to check and tune:
- **DIAMETER** is the most important setting. From your preview the endothelial cells look roughly 60-90 px across. Measure a few in Fiji and set it. If you leave it as `None`, Cellpose estimates it.
- **Under- or over-segmentation.** If cells merge, raise `CELLPROB_THRESHOLD` (for example to 0) or lower `DIAMETER`. If cells are missed or cut off, lower `CELLPROB_THRESHOLD` (for example to -2).
- **Round cells.** The filter that removes them is a heuristic based on local contrast and shape. Check the result visually. If it removes real endothelial cells or misses round ones, set `REMOVE_ROUND_CELLS = False`, or adjust the `1.3` threshold factor and the size limits.
- **Accuracy.** Borders in this image are very faint, so expect imperfect outlines. If the pretrained model is not good enough, fine-tune it on 5-10 images you correct by hand in the Cellpose GUI. Alternatively, a nuclear or junction-stain channel (VE-cadherin, for example), if you have one, would segment much more reliably than brightfield.
- **Preview.** Overlay `labels.tif` on `bf.tif` in Fiji or napari to check the result.

Preview image examined: <fig3-work>/bf3/gen_endo_r3/bf_preview.png
