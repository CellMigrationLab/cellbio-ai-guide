"""Segment endothelial cells in a brightfield monolayer and measure shape.

Reads image.tif, writes labels.tif and measurements.csv.
Requires: pip install cellpose scikit-image tifffile pandas scipy numpy
"""
import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from skimage import filters, measure, morphology, segmentation, io
from cellpose import models

# ---- Parameters to set/tune -------------------------------------------------
PIXEL_SIZE_UM = 0.65       # µm per pixel. SET THIS from your microscope/objective.
CELL_DIAMETER_PX = 50      # approx. endothelial cell diameter in pixels (used by Cellpose v3)
CANCER_STD_SIGMA = 4       # window for local texture
CANCER_STD_THRESH = None   # None = automatic (Otsu); otherwise set a number
CANCER_MIN_AREA_PX = 150   # ignore smaller bright/dark specks (debris)
CANCER_DILATE_PX = 4       # grow cancer mask to cover the halo
MAX_CANCER_OVERLAP = 0.3   # drop endothelial objects overlapping cancer cells more than this
MIN_AREA_UM2 = 100         # drop tiny fragments
# -----------------------------------------------------------------------------

img = tifffile.imread("image.tif").astype(np.float32)
if img.ndim > 2:                     # RGB or stack: use first channel/plane
    img = img[..., 0] if img.shape[-1] in (3, 4) else img[0]

# Flatten uneven illumination and normalise
bg = filters.gaussian(img, sigma=50)
flat = img - bg
flat = (flat - np.percentile(flat, 1)) / (np.percentile(flat, 99) - np.percentile(flat, 1))
flat = np.clip(flat, 0, 1)

# --- 1. Cancer cells: strong local contrast (dark rim + bright halo) ---------
local_mean = filters.gaussian(flat, CANCER_STD_SIGMA)
local_std = np.sqrt(np.clip(filters.gaussian(flat**2, CANCER_STD_SIGMA) - local_mean**2, 0, None))
thr = CANCER_STD_THRESH if CANCER_STD_THRESH is not None else filters.threshold_otsu(local_std)
cancer = local_std > thr
cancer = ndi.binary_fill_holes(morphology.binary_closing(cancer, morphology.disk(3)))
cancer = morphology.remove_small_objects(cancer, CANCER_MIN_AREA_PX)
cancer = morphology.binary_dilation(cancer, morphology.disk(CANCER_DILATE_PX))

# Replace cancer cells with background level so Cellpose doesn't segment them
flat_in = flat.copy()
flat_in[cancer] = np.median(flat[~cancer])

# --- 2. Endothelial segmentation with Cellpose -------------------------------
model = models.CellposeModel(gpu=True)   # cpsam in Cellpose 4, cyto3 in Cellpose 3
masks = model.eval(flat_in, diameter=CELL_DIAMETER_PX, channels=[0, 0])[0]

# --- 3. Filter objects -------------------------------------------------------
masks = segmentation.clear_border(masks)          # truncated cells give wrong shape
for r in measure.regionprops(masks):
    cm = cancer[tuple(r.coords.T)]
    if cm.mean() > MAX_CANCER_OVERLAP or r.area * PIXEL_SIZE_UM**2 < MIN_AREA_UM2:
        masks[masks == r.label] = 0
masks, _, _ = segmentation.relabel_sequential(masks)
masks = masks.astype(np.uint16)

# --- 4. Measure --------------------------------------------------------------
rows = [
    dict(
        label=r.label,
        area_um2=r.area * PIXEL_SIZE_UM**2,
        aspect_ratio=r.major_axis_length / max(r.minor_axis_length, 1e-9),
    )
    for r in measure.regionprops(masks)
]
pd.DataFrame(rows).to_csv("measurements.csv", index=False)
tifffile.imwrite("labels.tif", masks)

# QC overlay: endothelial outlines in yellow, excluded cancer cells in red
overlay = np.dstack([flat] * 3)
overlay[segmentation.find_boundaries(masks)] = (1, 1, 0)
overlay[segmentation.find_boundaries(cancer)] = (1, 0, 0)
io.imsave("qc_overlay.png", (overlay * 255).astype(np.uint8))

print(f"{len(rows)} endothelial cells measured")
