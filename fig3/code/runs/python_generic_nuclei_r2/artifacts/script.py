#!/usr/bin/env python
"""Segment nuclei in a DAPI image: dapi.tif -> labels.tif (uint16 label image)."""

import numpy as np
import tifffile
from scipy import ndimage as ndi
from skimage import filters, measure, morphology, segmentation, feature

# ----------------------------- parameters -----------------------------
INPUT = "dapi.tif"
OUTPUT = "labels.tif"

SMOOTH_SIGMA = 1.0        # px, denoising before thresholding
BG_SIGMA = 25             # px, scale of the slowly varying background (> nucleus size)
LOCAL_BLOCK = 41          # px, odd; window for adaptive threshold (~2x nucleus length)
LOCAL_OFFSET = 0.0        # raise (e.g. 0.02) for tighter masks, lower for looser ones
MIN_AREA = 40             # px, objects smaller than this are removed (debris)
MAX_HOLE = 60             # px, holes smaller than this are filled
SEED_SMOOTH = 1.5         # px, smoothing of the distance map for watershed seeds
MIN_SEED_DIST = 5         # px, minimum distance between nuclear centres
# ---------------------------------------------------------------------

img = tifffile.imread(INPUT)
if img.ndim > 2:
    # if the file is a stack or multichannel, use the first plane; adapt as needed
    print(f"Warning: input has shape {img.shape}; using the first plane.")
    img = img.reshape(-1, *img.shape[-2:])[0]
img = img.astype(np.float32)

# 1. Compress the dynamic range so dim nuclei and very bright blobs are
#    handled together, then denoise.
logimg = np.log1p(img - img.min())
logimg = (logimg - logimg.min()) / (np.ptp(logimg) + 1e-9)
smooth = filters.gaussian(logimg, SMOOTH_SIGMA)

# 2. Remove uneven background (cytoplasmic haze, out-of-focus glow).
background = filters.gaussian(smooth, BG_SIGMA)
flat = smooth - background

# 3. Local threshold, plus a global floor so empty background is not picked up.
local_thr = filters.threshold_local(flat, LOCAL_BLOCK, method="gaussian",
                                    offset=LOCAL_OFFSET)
floor = filters.threshold_otsu(flat) * 0.5
mask = (flat > local_thr) & (flat > floor)

# 4. Clean up the mask.
mask = morphology.binary_opening(mask, morphology.disk(2))
mask = morphology.remove_small_holes(mask, MAX_HOLE)
mask = morphology.remove_small_objects(mask, MIN_AREA)

# 5. Split touching nuclei: watershed on the smoothed distance transform.
dist = ndi.distance_transform_edt(mask)
dist_s = filters.gaussian(dist, SEED_SMOOTH)
peaks = feature.peak_local_max(dist_s, min_distance=MIN_SEED_DIST,
                               labels=measure.label(mask), exclude_border=False)
markers = np.zeros(mask.shape, dtype=np.int32)
markers[tuple(peaks.T)] = np.arange(1, len(peaks) + 1)
labels = segmentation.watershed(-dist_s, markers, mask=mask)

# 6. Remove tiny fragments created by the split and relabel consecutively.
labels = morphology.remove_small_objects(labels, MIN_AREA)
labels, _, _ = segmentation.relabel_sequential(labels)

tifffile.imwrite(OUTPUT, labels.astype(np.uint16))
print(f"Saved {OUTPUT}: {labels.max()} nuclei")

# Optional quick check (uncomment to view an overlay of outlines on the image):
# import matplotlib.pyplot as plt
# fig, ax = plt.subplots(figsize=(10, 10))
# ax.imshow(np.clip(img / np.percentile(img, 99.5), 0, 1), cmap="gray")
# ax.contour(labels > 0, [0.5], colors="r", linewidths=0.5)
# ax.imshow(np.ma.masked_equal(segmentation.find_boundaries(labels), 0),
#           cmap="autumn", alpha=0.8)
# ax.axis("off"); plt.show()
