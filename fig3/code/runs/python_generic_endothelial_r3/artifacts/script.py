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
