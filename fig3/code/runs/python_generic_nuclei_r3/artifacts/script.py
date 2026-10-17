#!/usr/bin/env python3
"""Segment nuclei in dapi.tif and save an integer label image as labels.tif.

Requires: numpy, scipy, scikit-image, tifffile
    pip install numpy scipy scikit-image tifffile
"""
import numpy as np
import tifffile
from scipy import ndimage as ndi
from skimage import filters, morphology, segmentation, measure, feature

# ----------------------- parameters to tune -----------------------
INPUT = "dapi.tif"
OUTPUT = "labels.tif"

SIGMA = 1.0            # Gaussian smoothing (px) to suppress noise
BG_RADIUS = 25         # px; should be larger than a nucleus (radius ~10 px here)
LOCAL_BLOCK = 51       # odd; neighbourhood for the local threshold (a few nuclei wide)
LOCAL_OFFSET = 0.0     # raise (e.g. 0.01) to shrink masks / be stricter, lower to be looser
MIN_AREA = 40          # px; objects smaller than this are removed (debris)
MAX_AREA = 1500        # px; larger objects are removed (set None to disable)
MIN_DISTANCE = 6       # px; minimum distance between nucleus centres for the split
SPLIT_SMOOTH = 1.5     # smoothing of the distance map; higher = fewer splits
# -------------------------------------------------------------------

# 1. Load, keep a single 2D plane, scale to 0-1
img = tifffile.imread(INPUT)
img = np.squeeze(img)
if img.ndim > 2:  # e.g. a z-stack or multichannel file: use a max projection
    img = img.max(axis=0)
img = img.astype(np.float32)
img = (img - img.min()) / (np.ptp(img) + 1e-9)

# 2. Smooth, then subtract the uneven background (rolling-ball-like)
smooth = filters.gaussian(img, sigma=SIGMA)
background = morphology.opening(smooth, morphology.disk(BG_RADIUS))
corrected = smooth - background

# 3. Foreground mask: local threshold (handles dim and bright nuclei in the same
#    field) combined with a global Otsu floor so empty background is not picked up.
local_thr = filters.threshold_local(corrected, block_size=LOCAL_BLOCK,
                                    method="gaussian", offset=LOCAL_OFFSET)
global_floor = 0.5 * filters.threshold_otsu(corrected[corrected > 0])
mask = (corrected > local_thr) & (corrected > global_floor * 0.25)

mask = morphology.remove_small_objects(mask, MIN_AREA)
mask = ndi.binary_fill_holes(mask)
mask = morphology.binary_opening(mask, morphology.disk(1))

# 4. Split touching nuclei: watershed on the smoothed distance transform
dist = ndi.distance_transform_edt(mask)
dist_s = filters.gaussian(dist, sigma=SPLIT_SMOOTH)
peaks = feature.peak_local_max(dist_s, min_distance=MIN_DISTANCE,
                               labels=measure.label(mask), exclude_border=False)
markers = np.zeros(mask.shape, dtype=np.int32)
markers[tuple(peaks.T)] = np.arange(1, len(peaks) + 1)
labels = segmentation.watershed(-dist_s, markers, mask=mask)

# 5. Clean up: drop tiny / huge objects and relabel consecutively
areas = np.bincount(labels.ravel())
remove = areas < MIN_AREA
if MAX_AREA is not None:
    remove |= areas > MAX_AREA
remove[0] = False
labels[remove[labels]] = 0
labels, _, _ = segmentation.relabel_sequential(labels)

# 6. Save
labels = labels.astype(np.uint16)
tifffile.imwrite(OUTPUT, labels)
print(f"Segmented {labels.max()} nuclei -> {OUTPUT}")
print(f"Median area: {np.median(np.bincount(labels.ravel())[1:]):.0f} px")
