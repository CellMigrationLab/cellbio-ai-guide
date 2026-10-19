import numpy as np
import pandas as pd
from skimage import io, filters, measure, morphology, segmentation, feature, color
from scipy import ndimage as ndi

# ---- parameters ----
PIXEL_SIZE_UM = 0.65     # PLACEHOLDER: set to your image's µm/pixel
TOPHAT_RADIUS = 15       # px; must be larger than half the longest nucleus
LOCAL_BLOCK = 51         # px; odd, local threshold window
MIN_AREA_UM2 = 30        # remove debris
MAX_AREA_UM2 = 400
BRIGHT_FACTOR = 2.5      # objects brighter than this x median object intensity = cancer nuclei
MIN_DISTANCE = 5         # px; min spacing between nucleus centres for splitting

# ---- load ----
img = io.imread("image.tif")
img = np.squeeze(img)
if img.ndim == 3:                      # multichannel / RGB: take first channel (DAPI)
    img = img[..., 0] if img.shape[-1] <= 4 else img[0]
img = img.astype(float)

# ---- foreground ----
smooth = filters.gaussian(img, 1)
flat = morphology.white_tophat(smooth, morphology.disk(TOPHAT_RADIUS))  # removes background / seam offset
noise = 1.4826 * np.median(np.abs(flat - np.median(flat)))
floor = np.median(flat) + 3 * noise
mask = (flat > filters.threshold_local(flat, LOCAL_BLOCK)) & (flat > floor)
mask = morphology.remove_small_objects(mask, 20)
mask = ndi.binary_fill_holes(morphology.binary_opening(mask, morphology.disk(1)))

# ---- split touching nuclei ----
dist = filters.gaussian(ndi.distance_transform_edt(mask), 1)
peaks = feature.peak_local_max(dist, min_distance=MIN_DISTANCE, labels=measure.label(mask),
                               exclude_border=False)
markers = np.zeros(img.shape, int)
markers[tuple(peaks.T)] = np.arange(1, len(peaks) + 1)
labels = segmentation.watershed(-dist, markers, mask=mask)

# ---- filter objects ----
props = measure.regionprops(labels, intensity_image=flat)
med_int = np.median([p.mean_intensity for p in props])
min_px = MIN_AREA_UM2 / PIXEL_SIZE_UM**2
max_px = MAX_AREA_UM2 / PIXEL_SIZE_UM**2
keep = []
for p in props:
    r0, c0, r1, c1 = p.bbox
    touches_border = r0 == 0 or c0 == 0 or r1 == img.shape[0] or c1 == img.shape[1]
    if (min_px <= p.area <= max_px
            and p.mean_intensity < BRIGHT_FACTOR * med_int   # drop bright cancer nuclei
            and not touches_border):
        keep.append(p.label)
print(f"{len(props)} objects -> {len(keep)} endothelial nuclei kept")

labels = measure.label(np.isin(labels, keep) * labels, connectivity=1) if False else \
         np.where(np.isin(labels, keep), labels, 0)
labels, _, _ = segmentation.relabel_sequential(labels)

# ---- measure ----
rows = [{"label": p.label,
         "area_um2": p.area * PIXEL_SIZE_UM**2,
         "aspect_ratio": p.major_axis_length / p.minor_axis_length}
        for p in measure.regionprops(labels)]
pd.DataFrame(rows).to_csv("measurements.csv", index=False)
io.imsave("labels.tif", labels.astype(np.uint16), check_contrast=False)

# ---- QC overlay (check this by eye) ----
disp = np.clip(img / np.percentile(img, 99.5), 0, 1)
overlay = segmentation.mark_boundaries(color.gray2rgb(disp), labels, color=(1, 0, 0))
io.imsave("qc_overlay.png", (overlay * 255).astype(np.uint8), check_contrast=False)
