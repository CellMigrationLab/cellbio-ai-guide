"""Segment endothelial nuclei (DAPI) and measure area and aspect ratio.

Reads image.tif, writes labels.tif and measurements.csv.
Requires: numpy, scipy, scikit-image, pandas, tifffile
"""
import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
from skimage import filters, measure, morphology, segmentation, feature

# ---- parameters -------------------------------------------------------------
PIXEL_SIZE_UM = 0.65        # um/pixel; used only if not found in the TIFF metadata. CHECK THIS.
NUC_DIAMETER_PX = 16        # approximate endothelial nucleus short-axis diameter (pixels)
MIN_AREA_UM2 = 30           # discard debris smaller than this
MAX_AREA_UM2 = 400          # discard large merged blobs
BRIGHT_FACTOR = 1.8         # objects this much brighter than their neighbours = cancer nuclei
NEIGHBOUR_RADIUS_PX = 120   # neighbourhood used to judge "brighter than neighbours"
# -----------------------------------------------------------------------------


def get_pixel_size(path, default):
    """Pixel size in um from TIFF resolution tags (if in micron/cm units)."""
    with tifffile.TiffFile(path) as tif:
        page = tif.pages[0]
        try:
            xres = page.tags["XResolution"].value
            unit = page.tags["ResolutionUnit"].value  # 2 = inch, 3 = cm
            ppu = xres[0] / xres[1]
            md = tif.imagej_metadata or {}
            if md.get("unit") in ("micron", "um", "µm") and ppu > 0:
                return 1.0 / ppu
            if unit == 3 and ppu > 1:
                return 1e4 / ppu
        except (KeyError, ZeroDivisionError):
            pass
    return default


img = tifffile.imread("image.tif").astype(np.float32)
if img.ndim > 2:  # take first plane / average channels if a stack was saved
    img = img[0] if img.shape[0] < 10 else img.mean(axis=-1)
px = get_pixel_size("image.tif", PIXEL_SIZE_UM)
print(f"Pixel size used: {px:.4f} um/px")

# ---- preprocessing ----------------------------------------------------------
smooth = filters.gaussian(img, sigma=1.5, preserve_range=True)
# remove out-of-focus haze / uneven background
bg = filters.gaussian(
    ndi.minimum_filter(smooth, size=3 * NUC_DIAMETER_PX), sigma=2 * NUC_DIAMETER_PX,
    preserve_range=True)
flat = smooth - bg
# log transform compresses the dim endothelial vs. bright cancer nuclei range and
# evens out brightness differences between the two image halves
logimg = np.log1p(np.clip(flat, 0, None))

# ---- foreground -------------------------------------------------------------
local_thr = filters.threshold_local(logimg, block_size=4 * NUC_DIAMETER_PX + 1, offset=0)
fg = (logimg > local_thr) & (logimg > filters.threshold_otsu(logimg) * 0.6)
fg = morphology.remove_small_objects(fg, 20)
fg = ndi.binary_fill_holes(morphology.binary_opening(fg, morphology.disk(2)))

# ---- split touching nuclei (distance-transform watershed) -------------------
dist = ndi.distance_transform_edt(fg)
dist = filters.gaussian(dist, sigma=1)
peaks = feature.peak_local_max(
    dist, min_distance=NUC_DIAMETER_PX // 2, labels=measure.label(fg), exclude_border=False)
markers = np.zeros(img.shape, dtype=np.int32)
markers[tuple(peaks.T)] = np.arange(1, len(peaks) + 1)
labels = segmentation.watershed(-dist, markers, mask=fg)

# ---- filter objects ---------------------------------------------------------
props = measure.regionprops(labels, intensity_image=flat)
min_px, max_px = MIN_AREA_UM2 / px**2, MAX_AREA_UM2 / px**2
centroids = np.array([p.centroid for p in props])
mean_int = np.array([p.mean_intensity for p in props])
tree = cKDTree(centroids)

keep = []
for i, p in enumerate(props):
    if not (min_px <= p.area <= max_px):
        continue
    # cancer nuclei: much brighter than the local population of nuclei
    idx = tree.query_ball_point(centroids[i], NEIGHBOUR_RADIUS_PX)
    if mean_int[i] > BRIGHT_FACTOR * np.median(mean_int[idx]):
        continue
    keep.append(p.label)

labels = segmentation.relabel_sequential(np.where(np.isin(labels, keep), labels, 0))[0]
labels = labels.astype(np.uint16)

# ---- measurements -----------------------------------------------------------
rows = []
for p in measure.regionprops(labels):
    minor = max(p.minor_axis_length, 1e-6)
    rows.append({
        "label": p.label,
        "area_um2": p.area * px**2,
        "aspect_ratio": p.major_axis_length / minor,
    })
pd.DataFrame(rows).to_csv("measurements.csv", index=False)
tifffile.imwrite("labels.tif", labels)
print(f"Saved {len(rows)} nuclei to labels.tif and measurements.csv")
