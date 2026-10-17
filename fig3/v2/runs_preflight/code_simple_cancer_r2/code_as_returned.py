"""Segment cancer cells in a brightfield image and measure area and aspect ratio.

Reads image.tif from the working directory and writes labels.tif and measurements.csv.
"""
import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from skimage import filters, measure, morphology, segmentation, color

# ---- parameters to tune -------------------------------------------------
PIXEL_SIZE_UM = None      # µm per pixel; None = read from TIFF metadata, else must be set here
MIN_DIAMETER_UM = 8.0     # smaller objects are treated as debris
EXCLUDE_BORDER = True     # drop cells cut by the image edge (their shape is biased)
EDGE_SIGMA = 1.5          # smoothing before the gradient (px)
SPLIT_SMOOTH = 2.0        # smoothing of the distance map used to split touching cells
# --------------------------------------------------------------------------


def read_pixel_size(path):
    """Return µm/px from TIFF tags (ImageJ or plain resolution tags), or None."""
    with tifffile.TiffFile(path) as tf:
        page = tf.pages[0]
        xres = page.tags.get("XResolution")
        if xres is None:
            return None
        num, den = xres.value
        if num == 0:
            return None
        px = den / num  # length unit per pixel
        unit = (tf.imagej_metadata or {}).get("unit", "")
        if unit in ("micron", "µm", "um", "\u00b5m"):
            return px
        res_unit = page.tags.get("ResolutionUnit")
        res_unit = res_unit.value if res_unit is not None else 1
        if res_unit == 3:        # centimetre
            return px * 1e4
        if res_unit == 2:        # inch
            return px * 25400
        return None


img = tifffile.imread("image.tif")
if img.ndim == 3:
    img = color.rgb2gray(img) if img.shape[-1] in (3, 4) else img[0]
img = img.astype(float)

pixel_size = PIXEL_SIZE_UM or read_pixel_size("image.tif")
if not pixel_size:
    raise SystemExit("No pixel size found in image.tif: set PIXEL_SIZE_UM at the top of the script.")
print(f"Pixel size: {pixel_size:.4f} µm/px")

# 1. Flatten the uneven illumination and normalise contrast
img = (img - img.min()) / (np.ptp(img) + 1e-9)
flat = img - filters.gaussian(img, 40)

# 2. Cells have a strong dark rim / bright halo; the endothelium is low contrast.
#    Use gradient magnitude as an "edge" map and threshold it.
grad = filters.sobel(filters.gaussian(flat, EDGE_SIGMA))
edges = grad > filters.threshold_otsu(grad)

# 3. Close the rims and fill the cell interiors
min_area_px = int(np.pi * (MIN_DIAMETER_UM / 2 / pixel_size) ** 2)
mask = morphology.binary_closing(edges, morphology.disk(3))
mask = ndi.binary_fill_holes(mask)
mask = morphology.binary_opening(mask, morphology.disk(4))
mask = morphology.remove_small_objects(mask, min_area_px)

# 4. Split touching cells with a distance-transform watershed
dist = filters.gaussian(ndi.distance_transform_edt(mask), SPLIT_SMOOTH)
markers = measure.label(morphology.h_maxima(dist, 0.5) & mask)
labels = segmentation.watershed(-dist, markers, mask=mask)

# 5. Clean up: drop small fragments and (optionally) border-touching cells
labels = morphology.remove_small_objects(labels, min_area_px)
if EXCLUDE_BORDER:
    labels = segmentation.clear_border(labels)
labels, _, _ = segmentation.relabel_sequential(labels)

# 6. Measure
rows = []
for r in measure.regionprops(labels):
    minor = r.minor_axis_length
    rows.append({
        "label": r.label,
        "area_um2": r.area * pixel_size ** 2,
        "aspect_ratio": r.major_axis_length / minor if minor > 0 else np.nan,
    })
df = pd.DataFrame(rows, columns=["label", "area_um2", "aspect_ratio"])

tifffile.imwrite("labels.tif", labels.astype(np.uint16))
df.to_csv("measurements.csv", index=False)
print(f"{len(df)} cells; median area {df.area_um2.median():.1f} µm², "
      f"median aspect ratio {df.aspect_ratio.median():.2f}")
