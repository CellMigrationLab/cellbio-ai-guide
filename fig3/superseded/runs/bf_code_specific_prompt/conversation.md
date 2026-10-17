# bf_code_specific_prompt

## USER (2026-10-16T18:37:26.390Z)

Act as a helpful coding assistant for a cell biologist. Do not use any tools (no files, no code execution).

The user writes: "Please write a Python script to segment the cancer cells in bf.tif using Cellpose (I have Cellpose 4 installed, CPU only). The image is a single-channel 2D brightfield image (Y, X), 16-bit, pixel size 0.65 µm. The cancer cells are round, refractile cells, about 15–25 µm across, sitting on top of a flat endothelial monolayer; the endothelial cells must NOT be segmented. Do not resize the image. Save the label image as labels.tif and the cancer-cell areas in µm² as areas.csv, and print the number of cancer cells. Available packages: numpy, scipy, scikit-image, tifffile, pandas, cellpose."

Reply with one complete script in a single ```python block and nothing else.

## HARNESS NOTE (2026-10-16T18:37:26.432Z)

<system-reminder>
Your final report is delivered through SubagentHandback: when your work is complete, call SubagentHandback({message: <your full report>}). The call ends your run, so make it your last step. Only a SubagentHandback call reaches your caller as your result; plain text you write at the end is not delivered. Do not also send the report with SendMessage: your caller would get it twice.
</system-reminder>

## ASSISTANT (final report)

```python
import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from skimage import measure, morphology, segmentation
from cellpose import models

# ------------------------- parameters -------------------------
IMG_PATH = "bf.tif"
PIXEL_SIZE_UM = 0.65

# Expected cancer-cell size (15-25 um diameter), with some tolerance
MIN_DIAM_UM = 12.0
MAX_DIAM_UM = 30.0

# Shape filters (cancer cells are round; endothelial cells are flat/elongated)
MIN_SOLIDITY = 0.90
MAX_ECCENTRICITY = 0.85

# Refractility filter: cancer cells have strong local contrast (dark rim /
# bright halo) compared with the flat endothelial monolayer.
# Ratio of local texture inside the object to the typical monolayer texture.
MIN_CONTRAST_RATIO = 1.5
LOCAL_STD_SIGMA_PX = 2.0
BACKGROUND_SIGMA_PX = 60.0   # illumination flattening

EXCLUDE_BORDER_CELLS = False  # set True to drop cells cut by the image edge
# --------------------------------------------------------------

img = tifffile.imread(IMG_PATH).astype(np.float32)
if img.ndim != 2:
    img = np.squeeze(img)
assert img.ndim == 2, "Expected a single-channel 2D image (Y, X)"

# Flatten uneven illumination (no resizing)
bg = ndi.gaussian_filter(img, BACKGROUND_SIGMA_PX)
flat = img - bg

# Cellpose 4 (CPU). Do not set a diameter: no rescaling of the image.
model = models.CellposeModel(gpu=False)
masks, flows, styles = model.eval(
    flat,
    diameter=None,
    flow_threshold=0.4,
    cellprob_threshold=0.0,
)
masks = np.asarray(masks).astype(np.int32)
print(f"Cellpose raw objects: {masks.max()}")

# Local texture / contrast map
m1 = ndi.gaussian_filter(flat, LOCAL_STD_SIGMA_PX)
m2 = ndi.gaussian_filter(flat ** 2, LOCAL_STD_SIGMA_PX)
local_std = np.sqrt(np.clip(m2 - m1 ** 2, 0, None))

# Reference texture of the flat monolayer: pixels outside all detected objects
outside = ndi.binary_erosion(masks == 0, iterations=3)
ref_pixels = local_std[outside] if outside.sum() > 100 else local_std.ravel()
ref_texture = np.median(ref_pixels) + 1e-6

min_area_um2 = np.pi * (MIN_DIAM_UM / 2) ** 2
max_area_um2 = np.pi * (MAX_DIAM_UM / 2) ** 2
h, w = masks.shape

keep = np.zeros_like(masks)
areas_um2 = []
new_id = 0
for r in measure.regionprops(masks):
    area_um2 = r.area * PIXEL_SIZE_UM ** 2
    if not (min_area_um2 <= area_um2 <= max_area_um2):
        continue
    if r.solidity < MIN_SOLIDITY or r.eccentricity > MAX_ECCENTRICITY:
        continue

    minr, minc, maxr, maxc = r.bbox
    if EXCLUDE_BORDER_CELLS and (minr == 0 or minc == 0 or maxr == h or maxc == w):
        continue

    # Contrast of the object plus a thin rim (captures the refractile edge)
    obj = masks == r.label
    zone = ndi.binary_dilation(obj, iterations=3)
    contrast_ratio = local_std[zone].mean() / ref_texture
    if contrast_ratio < MIN_CONTRAST_RATIO:
        continue

    new_id += 1
    keep[obj] = new_id
    areas_um2.append(area_um2)

# Fill holes inside each cell and relabel sequentially
final = np.zeros_like(keep)
for lab in range(1, new_id + 1):
    filled = ndi.binary_fill_holes(keep == lab)
    final[filled & (final == 0)] = lab
final, _, _ = segmentation.relabel_sequential(final)
final = final.astype(np.uint16)

# Recompute areas from the final labels
props = measure.regionprops(final)
df = pd.DataFrame({
    "label": [p.label for p in props],
    "area_um2": [p.area * PIXEL_SIZE_UM ** 2 for p in props],
})

tifffile.imwrite("labels.tif", final)
df.to_csv("areas.csv", index=False)

print(f"Number of cancer cells: {len(df)}")
```
