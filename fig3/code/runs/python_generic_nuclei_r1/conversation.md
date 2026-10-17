# python_generic_nuclei_r1

## USER (2026-10-17T06:30:57.384Z)

Act as a helpful assistant for a cell biologist. You cannot run code. You may use the Read tool ONLY to view the image the user attached: <fig3-work>/bf3/gen_nuclei_r1/dapi_preview.png (a preview of their file dapi.tif). Do not open anything else.

The user writes: "Please write a Python script to segment the nuclei in my DAPI image." (attached: dapi.tif)

Reply as you normally would. Put the code in a single complete ```python block that reads dapi.tif and saves the label image as labels.tif.

## HARNESS NOTE (2026-10-17T06:30:57.418Z)

<system-reminder>
Your final report is delivered through SubagentHandback: when your work is complete, call SubagentHandback({message: <your full report>}). The call ends your run, so make it your last step. Only a SubagentHandback call reaches your caller as your result; plain text you write at the end is not delivered. Do not also send the report with SendMessage: your caller would get it twice.
</system-reminder>

*[tool call: Read: <fig3-work>/bf3/gen_nuclei_r1/dapi_preview.png]*

## ASSISTANT (final report)

I haven't run this script. I can't run code here, and I only looked at the preview of your image. Treat it as a starting point and check the overlay it saves.

From the preview, I can see:
- Many small, oval nuclei, roughly 15-25 px long, mostly well separated but touching in a few places.
- Brightness varies a lot. Most nuclei are dim, and there are scattered very bright, round blobs (probably mitotic or apoptotic cells, or out-of-focus nuclei), especially in clusters at the top and left.
- The background is uneven, with haze around the bright clusters.

A single global threshold would lose the dim nuclei or merge the bright clusters. So the script does the following:
1. It smooths the image and subtracts a heavily blurred copy as the background.
2. It thresholds with a local (adaptive) threshold plus a low global floor, so dim nuclei are kept and empty background is not picked up.
3. It splits touching nuclei with a distance-transform watershed.
4. It removes tiny debris and saves a 16-bit label image, plus a QC overlay so you can check the result.

```python
#!/usr/bin/env python
"""
Segment nuclei in a DAPI image.
Input : dapi.tif
Output: labels.tif  (uint16 label image, 0 = background, 1..N = nuclei)
        qc_overlay.png (outlines on the image, for visual checking)

Requires: numpy scipy scikit-image tifffile matplotlib
  pip install numpy scipy scikit-image tifffile matplotlib
"""
import numpy as np
import tifffile
from scipy import ndimage as ndi
from skimage import filters, morphology, segmentation, measure, feature

# ----------------------------- parameters ----------------------------------
INPUT = "dapi.tif"
OUTPUT = "labels.tif"
QC_OUTPUT = "qc_overlay.png"

SMOOTH_SIGMA = 1.0        # px, denoising before thresholding
BG_SIGMA = 25             # px, should be larger than a nucleus (~2x its length)
LOCAL_BLOCK = 51          # px, odd; local-threshold window (a few nuclei wide)
LOCAL_OFFSET = 0.0        # raise to make the mask tighter, lower (negative) to grow it
MIN_SIZE = 40             # px^2, smaller objects are removed as debris
MIN_DISTANCE = 5          # px, minimum distance between nucleus centres for watershed
# ---------------------------------------------------------------------------

# --- load (take first plane if the file is a stack / multichannel) ---
img = tifffile.imread(INPUT)
while img.ndim > 2:
    img = img[0]
img = img.astype(np.float32)

# --- normalise and compress the dynamic range ---
# Log transform keeps dim nuclei visible next to very bright mitotic/debris blobs.
lo, hi = np.percentile(img, (0.5, 99.9))
norm = np.clip((img - lo) / (hi - lo + 1e-9), 0, 1)
logimg = np.log1p(norm * 50) / np.log1p(50)

# --- smooth and remove uneven background ---
smooth = filters.gaussian(logimg, SMOOTH_SIGMA)
background = filters.gaussian(smooth, BG_SIGMA)
flat = smooth - background
flat -= flat.min()

# --- threshold: adaptive (local) AND a global floor ---
local_t = filters.threshold_local(flat, LOCAL_BLOCK, method="gaussian", offset=LOCAL_OFFSET)
global_floor = filters.threshold_otsu(flat) * 0.5   # rejects faint background texture
mask = (flat > local_t) & (flat > global_floor)

# --- clean the mask ---
mask = morphology.binary_opening(mask, morphology.disk(1))
mask = ndi.binary_fill_holes(mask)
mask = morphology.remove_small_objects(mask, MIN_SIZE)

# --- split touching nuclei with a distance-transform watershed ---
dist = ndi.distance_transform_edt(mask)
dist_s = filters.gaussian(dist, 1.0)
peaks = feature.peak_local_max(
    dist_s, min_distance=MIN_DISTANCE, labels=measure.label(mask), exclude_border=False
)
markers = np.zeros(mask.shape, dtype=np.int32)
markers[tuple(peaks.T)] = np.arange(1, len(peaks) + 1)
labels = segmentation.watershed(-dist_s, markers, mask=mask)

# --- remove tiny fragments created by splitting, then relabel 1..N ---
labels = morphology.remove_small_objects(labels, MIN_SIZE)
labels, _, _ = segmentation.relabel_sequential(labels)
labels = labels.astype(np.uint16)

tifffile.imwrite(OUTPUT, labels)
print(f"Saved {OUTPUT}: {labels.max()} nuclei")

# --- quick QC overlay ---
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    disp = np.clip(logimg, 0, 1)
    outlines = segmentation.find_boundaries(labels, mode="outer")
    rgb = np.dstack([disp, disp, disp])
    rgb[outlines] = [1, 0, 0]
    plt.imsave(QC_OUTPUT, rgb)
    print(f"Saved {QC_OUTPUT}")
except Exception as e:  # QC is optional
    print("Skipping QC overlay:", e)
```

**Tuning**
- **Dim nuclei missing:** lower `LOCAL_OFFSET` (for example -0.02) or lower the `0.5` factor on `global_floor`.
- **Background or haze picked up around bright clusters:** raise `LOCAL_OFFSET` or the `global_floor` factor.
- **Touching nuclei merged:** lower `MIN_DISTANCE` (try 4).
- **Single nuclei cut in two:** raise `MIN_DISTANCE` (try 7).
- **Debris counted as nuclei:** raise `MIN_SIZE`.
- **Pixel size:** the sizes above assume a nucleus is about 15-25 px long, as in your preview. If your full-resolution image has a different pixel size, scale `BG_SIGMA`, `LOCAL_BLOCK`, `MIN_SIZE` and `MIN_DISTANCE` to match.

**Bright round blobs.** The very bright round blobs will be segmented as nuclei. If you want to exclude them, for example to count only interphase nuclei, filter on mean intensity or solidity with `skimage.measure.regionprops`. I can add that if you like.

**Check the overlay.** Look at `qc_overlay.png` before using the labels for measurements.

**Alternative.** If the classical approach is not good enough on the crowded clusters, Cellpose or StarDist (pretrained nuclear models) usually do better.
