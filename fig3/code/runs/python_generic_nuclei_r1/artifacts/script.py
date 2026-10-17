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
