"""Segment endothelial cells in a brightfield monolayer and measure shape.

Reads image.tif, writes labels.tif and measurements.csv.
Requires: pip install cellpose scikit-image tifffile pandas scipy numpy
"""
import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from skimage import filters, measure, morphology, segmentation
from cellpose import models

# ---- parameters -----------------------------------------------------------
PIXEL_SIZE_UM = None       # µm per pixel; read from the TIFF tags if None
CELL_DIAMETER_PX = None    # None = let Cellpose estimate; else e.g. 50
CANCER_Z = 3.0             # |local z-score| above which a pixel is "very high contrast"
CANCER_MIN_AREA_PX = 150   # smallest cancer-cell blob to keep
CANCER_OVERLAP = 0.3       # drop endothelial labels covered more than this by cancer cells
MIN_AREA_UM2 = 100         # drop tiny fragments
# ----------------------------------------------------------------------------


def get_pixel_size(path):
    with tifffile.TiffFile(path) as tf:
        page = tf.pages[0]
        tags = page.tags
        if "XResolution" in tags:
            num, den = tags["XResolution"].value
            res = num / den  # pixels per unit
            unit = tags["ResolutionUnit"].value if "ResolutionUnit" in tags else 1
            unit = getattr(unit, "name", unit)
            to_um = {"INCH": 25400.0, "CENTIMETER": 1e4, 2: 25400.0, 3: 1e4}.get(unit)
            if to_um and res > 0:
                return to_um / res
    return None


img = tifffile.imread("image.tif")
if img.ndim == 3:  # RGB or multichannel -> grey
    img = img.mean(axis=-1) if img.shape[-1] in (3, 4) else img[0]
img = img.astype(np.float32)

px = PIXEL_SIZE_UM or get_pixel_size("image.tif")
if px is None:
    raise SystemExit("Pixel size unknown: set PIXEL_SIZE_UM at the top of the script.")
print(f"Pixel size: {px:.4f} µm/px")

# ---- local contrast normalisation (handles dark/bright halves) ------------
bg = filters.gaussian(img, 30)
norm = img - bg
sd = np.sqrt(filters.gaussian(norm ** 2, 30))
norm = norm / (sd + 1e-6)

# ---- cancer cells: round, bright halo / dark rim, much stronger than endothelium
extreme = np.abs(filters.gaussian(norm, 1)) > CANCER_Z
extreme = morphology.closing(extreme, morphology.disk(3))
extreme = ndi.binary_fill_holes(extreme)
extreme = morphology.opening(extreme, morphology.disk(3))
extreme = morphology.remove_small_objects(extreme, CANCER_MIN_AREA_PX)
cancer = morphology.dilation(extreme, morphology.disk(3))

# ---- endothelial segmentation with Cellpose -------------------------------
model = models.CellposeModel(gpu=True)  # falls back to CPU if no GPU
masks, _, _ = model.eval(norm, diameter=CELL_DIAMETER_PX)

# ---- clean up -------------------------------------------------------------
masks = segmentation.clear_border(masks)  # border cells are truncated
out = np.zeros_like(masks, dtype=np.int32)
rows = []
new_id = 0
for r in measure.regionprops(masks):
    area_um2 = r.area * px ** 2
    if area_um2 < MIN_AREA_UM2:
        continue
    if cancer[masks == r.label].mean() > CANCER_OVERLAP:
        continue
    if r.minor_axis_length == 0:
        continue
    new_id += 1
    out[masks == r.label] = new_id
    rows.append({
        "label": new_id,
        "area_um2": area_um2,
        "aspect_ratio": r.major_axis_length / r.minor_axis_length,
    })

tifffile.imwrite("labels.tif", out.astype(np.uint16))
pd.DataFrame(rows, columns=["label", "area_um2", "aspect_ratio"]).to_csv(
    "measurements.csv", index=False)
print(f"{new_id} endothelial cells written")
