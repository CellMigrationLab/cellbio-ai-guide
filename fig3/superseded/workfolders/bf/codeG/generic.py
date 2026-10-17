import numpy as np
import tifffile
from scipy import ndimage as ndi
from skimage import filters, morphology, measure, segmentation, feature

# ---- parameters to tune (pixels, for a ~1024x1024 image) ----
TEXTURE_SIGMA = 3      # scale of local-contrast window
MIN_AREA      = 250    # smaller objects = debris
MAX_AREA      = 2500   # larger objects = merged clumps / artifacts
MIN_SOLIDITY  = 0.85   # rejects ragged debris clumps
MIN_DISTANCE  = 9      # min spacing between cell centres for splitting

# ---- load (take first plane/channel if multi-dimensional) ----
img = tifffile.imread("bf.tif")
while img.ndim > 2:
    img = img[0]
img = img.astype(np.float32)
img = (img - img.min()) / (img.max() - img.min() + 1e-8)

# ---- flatten uneven illumination ----
img = img - filters.gaussian(img, sigma=50)

# ---- local standard deviation: high on round refractile cells, low on monolayer ----
m  = filters.gaussian(img, sigma=TEXTURE_SIGMA)
m2 = filters.gaussian(img**2, sigma=TEXTURE_SIGMA)
texture = np.sqrt(np.clip(m2 - m**2, 0, None))

# ---- foreground mask ----
mask = texture > filters.threshold_otsu(texture)
mask = morphology.binary_closing(mask, morphology.disk(3))
mask = ndi.binary_fill_holes(mask)
mask = morphology.binary_opening(mask, morphology.disk(3))
mask = morphology.remove_small_objects(mask, MIN_AREA)

# ---- split touching cells with a distance-transform watershed ----
dist = ndi.distance_transform_edt(mask)
dist = filters.gaussian(dist, sigma=1.5)
peaks = feature.peak_local_max(dist, min_distance=MIN_DISTANCE,
                               labels=measure.label(mask), exclude_border=False)
markers = np.zeros(mask.shape, dtype=np.int32)
markers[tuple(peaks.T)] = np.arange(1, len(peaks) + 1)
labels = segmentation.watershed(-dist, markers, mask=mask)

# ---- filter by size and shape, then relabel ----
out = np.zeros_like(labels, dtype=np.uint16)
k = 0
for r in measure.regionprops(labels):
    if MIN_AREA <= r.area <= MAX_AREA and r.solidity >= MIN_SOLIDITY:
        k += 1
        out[labels == r.label] = k

tifffile.imwrite("labels.tif", out)
print(f"Saved labels.tif with {k} cells")
