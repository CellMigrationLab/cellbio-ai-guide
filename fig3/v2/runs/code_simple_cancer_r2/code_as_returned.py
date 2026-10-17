"""Segment and measure cancer cells in a brightfield image (image.tif).

Outputs (in the working directory):
    labels.tif        uint16 label image
    measurements.csv  label, area_um2, aspect_ratio
"""
import sys

import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from skimage import color, filters, measure, morphology, segmentation, feature

# ---- parameters -------------------------------------------------------------
PIXEL_SIZE_UM = None      # µm per pixel; if None, read from TIFF metadata
CELL_DIAMETER_PX = 30     # typical cancer cell diameter in pixels (adjust!)
MIN_SOLIDITY = 0.85       # rejects ragged debris
MIN_AREA_FRAC = 0.25      # min area as fraction of a typical cell
MAX_AREA_FRAC = 3.0       # max area as fraction of a typical cell
# -----------------------------------------------------------------------------


def read_pixel_size_um(path):
    """Try to get µm/pixel from ImageJ or standard TIFF resolution tags."""
    with tifffile.TiffFile(path) as tif:
        page = tif.pages[0]
        ij = tif.imagej_metadata or {}
        xres = page.tags.get("XResolution")
        if xres is None:
            return None
        num, den = xres.value
        if num == 0:
            return None
        px = den / num  # length unit per pixel
        unit = str(ij.get("unit", "")).replace("micron", "µm")
        res_unit = page.tags["ResolutionUnit"].value if "ResolutionUnit" in page.tags else 1
        if unit in ("µm", "um"):
            return px
        if unit == "nm":
            return px / 1000
        if unit == "mm":
            return px * 1000
        if int(res_unit) == 3:      # centimetre
            return px * 1e4
        if int(res_unit) == 2:      # inch
            return px * 25400
        return None


img = tifffile.imread("image.tif")
if img.ndim == 3:
    if img.shape[-1] in (3, 4):
        img = color.rgb2gray(img[..., :3])
    else:
        img = img[0]
img = img.astype(float)
img = (img - img.min()) / (np.ptp(img) + 1e-9)

pixel_um = PIXEL_SIZE_UM or read_pixel_size_um("image.tif")
if not pixel_um:
    sys.exit("Pixel size not found in image.tif: set PIXEL_SIZE_UM at the top of the script.")
print(f"Pixel size: {pixel_um:.4f} µm")

# 1. Flatten uneven illumination
flat = img - filters.gaussian(img, sigma=CELL_DIAMETER_PX * 2)

# 2. Local contrast: cells have a strong dark rim + bright centre, while the
#    endothelial monolayer is low-contrast texture
smooth = filters.gaussian(flat, sigma=1)
win = max(3, int(CELL_DIAMETER_PX / 5)) | 1
mean = ndi.uniform_filter(smooth, win)
sq = ndi.uniform_filter(smooth ** 2, win)
local_std = np.sqrt(np.clip(sq - mean ** 2, 0, None))

# 3. Threshold, close the rim, fill the cell interior
mask = local_std > filters.threshold_otsu(local_std)
mask = morphology.binary_closing(mask, morphology.disk(max(2, CELL_DIAMETER_PX // 8)))
mask = ndi.binary_fill_holes(mask)
mask = morphology.binary_opening(mask, morphology.disk(max(2, CELL_DIAMETER_PX // 6)))

typical_area = np.pi * (CELL_DIAMETER_PX / 2) ** 2
mask = morphology.remove_small_objects(mask, int(MIN_AREA_FRAC * typical_area))

# 4. Split touching cells with a distance-transform watershed
dist = filters.gaussian(ndi.distance_transform_edt(mask), sigma=2)
peaks = feature.peak_local_max(
    dist, min_distance=int(CELL_DIAMETER_PX * 0.4), labels=measure.label(mask),
    exclude_border=False,
)
markers = np.zeros(mask.shape, int)
markers[tuple(peaks.T)] = np.arange(1, len(peaks) + 1)
labels = segmentation.watershed(-dist, markers, mask=mask)

# 5. Remove debris / merged blobs by size and shape, then relabel
keep = np.zeros_like(labels)
n = 0
for r in measure.regionprops(labels):
    if not (MIN_AREA_FRAC * typical_area <= r.area <= MAX_AREA_FRAC * typical_area):
        continue
    if r.solidity < MIN_SOLIDITY:
        continue
    n += 1
    keep[labels == r.label] = n
labels = keep

# 6. Measure
rows = [
    dict(
        label=r.label,
        area_um2=r.area * pixel_um ** 2,
        aspect_ratio=r.major_axis_length / max(r.minor_axis_length, 1e-9),
    )
    for r in measure.regionprops(labels)
]
pd.DataFrame(rows).to_csv("measurements.csv", index=False)
tifffile.imwrite("labels.tif", labels.astype(np.uint16))
print(f"{n} cells segmented")
