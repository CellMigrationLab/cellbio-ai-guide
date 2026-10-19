"""Segment cancer cells in brightfield image.tif and measure area and aspect ratio.

Outputs: labels.tif, measurements.csv (label, area_um2, aspect_ratio), qc_overlay.png
"""
import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from skimage import filters, morphology, measure, segmentation, feature, color, io

# ---- parameters to tune ------------------------------------------------
PIXEL_SIZE_UM = None      # µm per pixel; if None, read from TIFF tags
FALLBACK_PIXEL_SIZE_UM = 0.65   # PLACEHOLDER: set to your microscope's value
BG_SIGMA = 50             # px, illumination correction scale
EDGE_WIN = 5              # px, window for local contrast
EDGE_THRESH_SCALE = 1.0   # multiply Otsu threshold; raise to be stricter
MIN_AREA_UM2 = 80         # drop debris smaller than this
MIN_SOLIDITY = 0.85       # drop irregular debris/clumps
CELL_RADIUS_UM = 7        # approx. cancer cell radius, sets watershed seed spacing
# -------------------------------------------------------------------------


def get_pixel_size(path):
    if PIXEL_SIZE_UM:
        return PIXEL_SIZE_UM
    with tifffile.TiffFile(path) as tf:
        page = tf.pages[0]
        xres = page.tags.get("XResolution")
        unit = page.tags.get("ResolutionUnit")
        if xres is not None:
            num, den = xres.value
            res = num / den  # pixels per unit
            unit = getattr(unit.value, "name", str(unit.value)) if unit else ""
            if res > 0:
                if "CENTIMETER" in unit.upper():
                    return 1e4 / res
                if "INCH" in unit.upper():
                    return 25400 / res
                # ImageJ files: unit stored in description
                desc = page.tags.get("ImageDescription")
                if desc is not None and "unit=micron" in desc.value or \
                   desc is not None and "unit=µm" in desc.value:
                    return 1 / res
    print(f"WARNING: no usable pixel size in metadata; using {FALLBACK_PIXEL_SIZE_UM} µm/px")
    return FALLBACK_PIXEL_SIZE_UM


img = tifffile.imread("image.tif").astype(float)
if img.ndim == 3:                      # RGB(A) or channel-last -> grayscale
    img = img[..., :3].mean(axis=-1)
px = get_pixel_size("image.tif")

# 1. Illumination correction: relative intensity, so dark and bright regions match
norm = img / (filters.gaussian(img, BG_SIGMA) + 1e-6)
sm = filters.gaussian(norm, 1)

# 2. Local contrast (std in a small window): high on the cell rim/halo,
#    low on the endothelial monolayer
mean = ndi.uniform_filter(sm, EDGE_WIN)
sq = ndi.uniform_filter(sm ** 2, EDGE_WIN)
contrast = np.sqrt(np.clip(sq - mean ** 2, 0, None))

# 3. Rim mask -> closed rings -> filled discs
rim = contrast > filters.threshold_otsu(contrast) * EDGE_THRESH_SCALE
rim = morphology.binary_closing(rim, morphology.disk(2))
mask = ndi.binary_fill_holes(rim)
mask = morphology.binary_opening(mask, morphology.disk(3))   # also removes seam line
min_px = MIN_AREA_UM2 / px ** 2
mask = morphology.remove_small_objects(mask, int(min_px))

# 4. Split touching cells with a distance-transform watershed
dist = filters.gaussian(ndi.distance_transform_edt(mask), 1)
min_dist = max(3, int(0.7 * CELL_RADIUS_UM / px))
peaks = feature.peak_local_max(dist, min_distance=min_dist, labels=measure.label(mask),
                               exclude_border=False)
markers = np.zeros(mask.shape, int)
markers[tuple(peaks.T)] = np.arange(1, len(peaks) + 1)
labels = segmentation.watershed(-dist, markers, mask=mask)

# 5. Remove small/irregular objects (debris), then relabel
for r in measure.regionprops(labels):
    if r.area < min_px or r.solidity < MIN_SOLIDITY:
        labels[labels == r.label] = 0
labels, _, _ = segmentation.relabel_sequential(labels)

# 6. Measurements
rows = [
    dict(label=r.label,
         area_um2=r.area * px ** 2,
         aspect_ratio=r.major_axis_length / max(r.minor_axis_length, 1e-6))
    for r in measure.regionprops(labels)
]
pd.DataFrame(rows, columns=["label", "area_um2", "aspect_ratio"]).to_csv("measurements.csv", index=False)
tifffile.imwrite("labels.tif", labels.astype(np.uint16))

# QC overlay
disp = (img - img.min()) / (np.ptp(img) + 1e-9)
overlay = segmentation.mark_boundaries(color.gray2rgb(norm / norm.max()), labels, color=(1, 0, 0))
io.imsave("qc_overlay.png", (overlay * 255).astype(np.uint8), check_contrast=False)

print(f"{labels.max()} cells; pixel size {px:.3f} µm/px")
