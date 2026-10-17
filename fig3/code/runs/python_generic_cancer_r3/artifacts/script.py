#!/usr/bin/env python
"""Segment round (rounded-up) cancer cells in a brightfield image.

Input : bf.tif      Output: labels.tif (uint16 label image, 0 = background)
Requires: numpy scipy scikit-image tifffile
"""
import numpy as np
import tifffile
from scipy import ndimage as ndi
from skimage import filters, morphology, measure, segmentation, feature

# ----------------------- parameters to tune --------------------------------
BG_SIGMA      = 25     # px, scale of the illumination background to remove
EDGE_SIGMA    = 1.5    # px, smoothing for rim detection
K_THRESH      = 3.0    # threshold = median + K * MAD of the contrast map; lower = more sensitive
MIN_DIAMETER  = 14     # px, smaller objects (debris) are removed
MAX_DIAMETER  = 60     # px, larger single objects are removed (set None to disable)
MIN_SOLIDITY  = 0.85   # removes ragged debris clusters
SPLIT_MIN_DIST = 7     # px, min distance between cell centres when splitting touching cells
# ---------------------------------------------------------------------------

# 1. Load and reduce to a single 2D float image
img = tifffile.imread("bf.tif")
img = np.squeeze(img)
if img.ndim == 3:
    # RGB(A) image -> mean of colour channels; otherwise a z/time stack -> first plane
    img = img[..., :3].mean(-1) if img.shape[-1] in (3, 4) else img[0]
img = img.astype(np.float32)

# 2. Flatten uneven illumination
bg = ndi.gaussian_filter(img, BG_SIGMA)
flat = img - bg

# 3. Contrast map: cells have a strong dark rim and bright halo, while the flat
#    adherent cells and background have weak local variation.
smooth = ndi.gaussian_filter(flat, EDGE_SIGMA)
grad = ndi.gaussian_gradient_magnitude(flat, EDGE_SIGMA)
contrast = ndi.gaussian_filter(grad + np.abs(smooth), 1.5)

med = np.median(contrast)
mad = np.median(np.abs(contrast - med)) + 1e-6
mask = contrast > med + K_THRESH * 1.4826 * mad

# 4. Turn rims into filled discs
mask = morphology.binary_closing(mask, morphology.disk(3))
mask = ndi.binary_fill_holes(mask)
mask = morphology.binary_opening(mask, morphology.disk(3))
min_area = np.pi * (MIN_DIAMETER / 2) ** 2
mask = morphology.remove_small_objects(mask, int(min_area))

# 5. Split touching cells (distance transform + watershed)
dist = ndi.distance_transform_edt(mask)
dist_s = ndi.gaussian_filter(dist, 1.0)
peaks = feature.peak_local_max(dist_s, min_distance=SPLIT_MIN_DIST,
                               labels=measure.label(mask), exclude_border=False)
markers = np.zeros(mask.shape, dtype=np.int32)
markers[tuple(peaks.T)] = np.arange(1, len(peaks) + 1)
labels = segmentation.watershed(-dist_s, markers, mask=mask)

# 6. Filter objects by size and shape (removes debris and clumps)
out = np.zeros_like(labels, dtype=np.uint16)
k = 0
for r in measure.regionprops(labels):
    d_eq = r.equivalent_diameter
    if d_eq < MIN_DIAMETER:
        continue
    if MAX_DIAMETER is not None and d_eq > MAX_DIAMETER:
        continue
    if r.solidity < MIN_SOLIDITY:
        continue
    k += 1
    out[labels == r.label] = k

print(f"Segmented {k} cells")
tifffile.imwrite("labels.tif", out)
