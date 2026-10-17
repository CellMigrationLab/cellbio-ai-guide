import numpy as np
import tifffile
from scipy import ndimage as ndi
from skimage import filters, morphology, measure, segmentation, feature, io

# ----------------- parameters to tune -----------------
CELL_DIAMETER = 30      # approx. diameter of a cancer cell in PIXELS of bf.tif
                        # (measure one in Fiji; scale this if your tif is larger
                        # than the preview, e.g. 2x larger image -> ~60)
MIN_SOLIDITY  = 0.85    # reject irregular objects (debris); lower = more permissive
TEXTURE_SCALE = 1.0     # multiply Otsu threshold: <1 = more sensitive, >1 = stricter
# -------------------------------------------------------

r = CELL_DIAMETER / 2.0
min_area = 0.25 * np.pi * r**2
max_area = 3.0 * np.pi * r**2

# 1. Load, reduce to a single 2D float image
img = np.squeeze(tifffile.imread("bf.tif")).astype(np.float32)
if img.ndim == 3:                      # RGB or stack: use first plane / mean of channels
    img = img.mean(axis=-1) if img.shape[-1] in (3, 4) else img[0]
img = (img - img.min()) / (np.ptp(img) + 1e-9)

# 2. Flatten uneven illumination
flat = img - filters.gaussian(img, sigma=CELL_DIAMETER * 2)

# 3. Local texture (standard deviation) highlights the rim/halo of round cells
win = max(3, int(CELL_DIAMETER / 4))
mean = ndi.uniform_filter(flat, win)
sq_mean = ndi.uniform_filter(flat**2, win)
texture = np.sqrt(np.clip(sq_mean - mean**2, 0, None))
texture = filters.gaussian(texture, sigma=CELL_DIAMETER / 10)

# 4. Threshold, clean up, fill the cell interior
mask = texture > filters.threshold_otsu(texture) * TEXTURE_SCALE
mask = morphology.binary_closing(mask, morphology.disk(max(1, int(r / 4))))
mask = ndi.binary_fill_holes(mask)
mask = morphology.binary_opening(mask, morphology.disk(max(1, int(r / 3))))
mask = morphology.remove_small_objects(mask, min_size=int(min_area))

# 5. Split touching cells (distance-transform watershed)
dist = ndi.distance_transform_edt(mask)
dist_s = filters.gaussian(dist, sigma=2)
peaks = feature.peak_local_max(
    dist_s, min_distance=max(3, int(r * 0.6)),
    threshold_abs=r * 0.4, labels=measure.label(mask), exclude_border=False)
markers = np.zeros(mask.shape, dtype=np.int32)
markers[tuple(peaks.T)] = np.arange(1, len(peaks) + 1)
labels = segmentation.watershed(-dist_s, markers, mask=mask)

# 6. Keep only round, cell-sized objects (removes debris and blobs)
out = np.zeros_like(labels, dtype=np.uint16)
n = 0
for p in measure.regionprops(labels):
    if min_area <= p.area <= max_area and p.solidity >= MIN_SOLIDITY:
        n += 1
        out[labels == p.label] = n

print(f"Segmented {n} cells")
tifffile.imwrite("labels.tif", out)

# Quick-look overlay for checking the result
overlay = np.dstack([img] * 3)
overlay[segmentation.find_boundaries(out)] = [1, 0, 0]
io.imsave("overlay_check.png", (overlay * 255).astype(np.uint8))
