"""Segment endothelial cells in a brightfield monolayer and measure shape.

Input : image.tif (working directory)
Output: labels.tif        label image (endothelial cells only)
        measurements.csv  label, area_um2, aspect_ratio

Requires: pip install "cellpose>=4" scikit-image tifffile scipy pandas numpy
"""
import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from skimage import filters, measure, morphology
from cellpose import models

# ---------------- parameters ----------------
PIXEL_SIZE_UM = 0.65       # µm per pixel. SET THIS from your microscope/objective.
CELL_DIAMETER_PX = None    # None = let Cellpose estimate; set e.g. 60 if results are off
MIN_AREA_UM2 = 100         # drop tiny fragments
CANCER_OVERLAP = 0.3       # drop an endothelial label if >30% of it lies on a cancer cell
HALO_Z = 3.0               # |z| above this counts as cancer-cell halo (lower = more sensitive)
CANCER_MIN_SOLIDITY = 0.85 # cancer cells are round; debris is irregular
CANCER_MIN_AREA_PX = 150
DROP_BORDER_CELLS = True   # cut-off cells would bias area / aspect ratio
# --------------------------------------------

img = tifffile.imread("image.tif").astype(np.float32)
if img.ndim == 3:                      # RGB or multichannel -> grayscale
    img = img.mean(axis=-1) if img.shape[-1] <= 4 else img[0]


def normalise_halves(im):
    """Flatten background and z-score each half (the two halves have different illumination)."""
    out = np.zeros_like(im)
    mid = im.shape[1] // 2
    for sl in (slice(0, mid), slice(mid, im.shape[1])):
        part = im[:, sl]
        bg = ndi.gaussian_filter(part, 50)
        flat = part - bg
        med = np.median(flat)
        mad = np.median(np.abs(flat - med)) * 1.4826 + 1e-6
        out[:, sl] = (flat - med) / mad
    return out


norm = normalise_halves(img)

# ---------- cancer-cell mask (bright/dark halo ring, filled, round) ----------
ring = np.abs(filters.gaussian(norm, 1)) > HALO_Z
ring = morphology.binary_closing(ring, morphology.disk(2))
filled = ndi.binary_fill_holes(ring)
filled = morphology.binary_opening(filled, morphology.disk(4))
cancer = np.zeros_like(filled)
for r in measure.regionprops(measure.label(filled)):
    if r.area >= CANCER_MIN_AREA_PX and r.solidity >= CANCER_MIN_SOLIDITY:
        cancer[tuple(r.coords.T)] = True
cancer = morphology.binary_dilation(cancer, morphology.disk(2))

# ---------- endothelial segmentation with Cellpose ----------
# Rescale to a sane 0-1 range for the model after normalisation
lo, hi = np.percentile(norm, (1, 99))
model_in = np.clip((norm - lo) / (hi - lo), 0, 1)

model = models.CellposeModel(gpu=True)   # falls back to CPU if no GPU
masks, _, _ = model.eval(model_in, diameter=CELL_DIAMETER_PX)

# ---------- filter labels ----------
keep = np.zeros_like(masks, dtype=np.int32)
rows = []
new_id = 0
min_area_px = MIN_AREA_UM2 / PIXEL_SIZE_UM**2
h, w = masks.shape

for r in measure.regionprops(masks):
    if r.area < min_area_px:
        continue
    if cancer[tuple(r.coords.T)].mean() > CANCER_OVERLAP:
        continue
    y0, x0, y1, x1 = r.bbox
    if DROP_BORDER_CELLS and (y0 == 0 or x0 == 0 or y1 == h or x1 == w):
        continue
    new_id += 1
    keep[tuple(r.coords.T)] = new_id
    minor = max(r.minor_axis_length, 1e-6)
    rows.append({
        "label": new_id,
        "area_um2": r.area * PIXEL_SIZE_UM**2,
        "aspect_ratio": r.major_axis_length / minor,
    })

tifffile.imwrite("labels.tif", keep.astype(np.uint16))
pd.DataFrame(rows, columns=["label", "area_um2", "aspect_ratio"]).to_csv(
    "measurements.csv", index=False)
print(f"{new_id} endothelial cells kept "
      f"({masks.max()} Cellpose objects, cancer-cell mask covers {cancer.mean():.1%} of image)")
