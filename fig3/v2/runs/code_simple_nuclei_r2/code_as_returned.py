import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from skimage import filters, measure, morphology, segmentation, feature

# ---- parameters (tune these) ----
PIXEL_SIZE_UM = 0.65        # fallback if not found in TIFF metadata; CHECK THIS
SMOOTH_SIGMA = 1.5          # px
BLOCK_SIZE = 51             # px, local threshold window (odd); > nucleus diameter
LOCAL_OFFSET = 0.0          # raise to be stricter
MIN_AREA_UM2 = 30.0         # drop debris
MAX_AREA_UM2 = 400.0        # drop large merged blobs / clumps
SEED_MIN_DIST = 6           # px, watershed seed spacing (~ nucleus minor radius)
BRIGHT_FACTOR = 2.0         # objects brighter than this x tile median = cancer cell
N_TILES_X = 2               # image is two stitched tiles with different brightness


def get_pixel_size(path, default):
    """Read pixel size (µm) from TIFF metadata if available."""
    with tifffile.TiffFile(path) as tf:
        page = tf.pages[0]
        try:
            xres = page.tags["XResolution"].value
            unit = page.tags["ResolutionUnit"].value  # 1 none, 2 inch, 3 cm
            res = xres[0] / xres[1]
            md = tf.imagej_metadata or {}
            md_unit = md.get("unit", "")
            if res > 0 and md_unit in ("um", "µm", "micron"):
                return 1.0 / res
            if res > 0 and unit == 3 and res != 1:
                return 1e4 / res
        except (KeyError, ZeroDivisionError):
            pass
    print(f"Pixel size not in metadata; using {default} µm/px")
    return default


img = tifffile.imread("image.tif").astype(np.float32)
if img.ndim > 2:  # take first channel/plane if stack
    img = img[0] if img.shape[0] < 10 else img.max(axis=0)
px = get_pixel_size("image.tif", PIXEL_SIZE_UM)

# ---- foreground ----
smooth = filters.gaussian(img, SMOOTH_SIGMA, preserve_range=True)
# remove slowly varying background (haze from out-of-focus cells)
bg = ndi.minimum_filter(smooth, size=41)
bg = filters.gaussian(bg, 20, preserve_range=True)
corr = np.clip(smooth - bg, 0, None)

local = filters.threshold_local(corr, BLOCK_SIZE, method="gaussian", offset=LOCAL_OFFSET)
# floor per tile so noise in dark regions isn't picked up
mask = np.zeros_like(corr, bool)
w = corr.shape[1]
edges = np.linspace(0, w, N_TILES_X + 1).astype(int)
for a, b in zip(edges[:-1], edges[1:]):
    tile = corr[:, a:b]
    floor = filters.threshold_otsu(tile) * 0.35
    mask[:, a:b] = (tile > local[:, a:b]) & (tile > floor)

mask = morphology.remove_small_objects(mask, 20)
mask = ndi.binary_fill_holes(morphology.binary_opening(mask, morphology.disk(2)))

# ---- split touching nuclei ----
dist = ndi.distance_transform_edt(mask)
dist = filters.gaussian(dist, 1)
peaks = feature.peak_local_max(dist, min_distance=SEED_MIN_DIST, labels=measure.label(mask),
                               exclude_border=False)
markers = np.zeros_like(mask, int)
markers[tuple(peaks.T)] = np.arange(1, len(peaks) + 1)
labels = segmentation.watershed(-dist, markers, mask=mask)

# ---- filter: size, then remove bright cancer nuclei ----
props = measure.regionprops(labels, intensity_image=corr)
area_um2 = {p.label: p.area * px**2 for p in props}
keep = {l for l, a in area_um2.items() if MIN_AREA_UM2 <= a <= MAX_AREA_UM2}

for a, b in zip(edges[:-1], edges[1:]):
    tile_props = [p for p in props if p.label in keep and a <= p.centroid[1] < b]
    if not tile_props:
        continue
    med = np.median([p.mean_intensity for p in tile_props])
    for p in tile_props:
        if p.mean_intensity > BRIGHT_FACTOR * med:
            keep.discard(p.label)

out = np.where(np.isin(labels, list(keep)), labels, 0)
out, _, _ = segmentation.relabel_sequential(out)

# ---- measure ----
rows = []
for p in measure.regionprops(out):
    ar = p.major_axis_length / p.minor_axis_length if p.minor_axis_length > 0 else np.nan
    rows.append({"label": p.label, "area_um2": p.area * px**2, "aspect_ratio": ar})

tifffile.imwrite("labels.tif", out.astype(np.uint16))
pd.DataFrame(rows).to_csv("measurements.csv", index=False)
print(f"{len(rows)} endothelial nuclei; pixel size {px:.4f} µm")
