import numpy as np
import tifffile
from scipy import ndimage as ndi
from skimage import (filters, morphology, measure, segmentation,
                     feature, exposure, io, color)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

# ---------------- User parameters (tune these) ----------------
IMG_PATH       = "nuclei.tif"
PIXEL_SIZE_UM  = None      # set e.g. 0.65 to get areas in um^2
SIGMA          = 1.0       # smoothing (px)
BG_SIGMA       = 25        # large-scale background estimate (px)
LOCAL_BLOCK    = 51        # odd; should be > ~2-3x nucleus diameter
LOCAL_OFFSET   = 0.0       # raise to be stricter, lower (negative) to be more permissive
MIN_AREA       = 30        # px; removes debris
MAX_AREA       = 2000      # px; flag very large objects (merged clumps)
MIN_DIST       = 4         # px; min distance between nucleus centres (~ radius)
H_MAXIMA       = 0.7       # smoothing of the distance map to avoid over-splitting
# --------------------------------------------------------------

# 1. Load and make 2D float
img = tifffile.imread(IMG_PATH)
if img.ndim > 2:
    print(f"Image has shape {img.shape}; using a max projection over the first axis. "
          "Adjust this if it is a multichannel stack.")
    img = img.max(axis=0)
img = img.astype(np.float32)

# 2. Normalise and compress dynamic range (dim and bright nuclei coexist)
p1, p995 = np.percentile(img, (1, 99.5))
norm = np.clip((img - p1) / (p995 - p1 + 1e-9), 0, 1)
logimg = np.log1p(50 * norm) / np.log1p(50)          # log-like transform

# 3. Smooth and subtract background
smooth = filters.gaussian(logimg, SIGMA)
bg = filters.gaussian(smooth, BG_SIGMA)
flat = smooth - bg

# 4. Foreground: local threshold, plus a global Otsu floor to reject empty background
loc = filters.threshold_local(flat, LOCAL_BLOCK, method="gaussian", offset=LOCAL_OFFSET)
global_floor = filters.threshold_otsu(flat) * 0.5
mask = (flat > loc) & (flat > global_floor)

mask = morphology.remove_small_objects(mask, MIN_AREA)
mask = morphology.binary_opening(mask, morphology.disk(1))
mask = ndi.binary_fill_holes(mask)

# 5. Split touching nuclei: distance transform + intensity, seeded watershed
dist = ndi.distance_transform_edt(mask)
dist_s = filters.gaussian(dist, 1)
combined = dist_s / (dist_s.max() + 1e-9) + 0.3 * smooth / (smooth.max() + 1e-9)

hmax = morphology.h_maxima(dist_s, H_MAXIMA)
seeds, _ = ndi.label(hmax & mask)
# fall back on peak_local_max if h-maxima gives too few seeds
if seeds.max() < 10:
    pk = feature.peak_local_max(combined, min_distance=MIN_DIST,
                                labels=measure.label(mask), exclude_border=False)
    seeds = np.zeros_like(mask, dtype=int)
    seeds[tuple(pk.T)] = np.arange(1, len(pk) + 1)

labels = segmentation.watershed(-combined, seeds, mask=mask)

# 6. Clean up: drop tiny fragments and objects touching nothing meaningful
labels = morphology.remove_small_objects(labels, MIN_AREA)
labels, _, _ = segmentation.relabel_sequential(labels)

# 7. Measurements
scale = PIXEL_SIZE_UM if PIXEL_SIZE_UM else 1.0
unit = "um" if PIXEL_SIZE_UM else "px"
props = measure.regionprops_table(
    labels, intensity_image=img,
    properties=("label", "area", "centroid", "eccentricity", "solidity",
                "mean_intensity", "max_intensity"))
df = pd.DataFrame(props)
df["area"] = df["area"] * scale**2
df = df.rename(columns={"area": f"area_{unit}2"})
df["possible_merge"] = (df["solidity"] < 0.85) | (df[f"area_{unit}2"] > MAX_AREA * scale**2)
df.to_csv("nuclei_measurements.csv", index=False)

print(f"Nuclei detected: {labels.max()}")
print(f"Median area: {df[f'area_{unit}2'].median():.1f} {unit}^2")
print(f"Objects flagged as possible merges (low solidity / very large): {df['possible_merge'].sum()}")

# 8. Save label image and QC overlay
tifffile.imwrite("nuclei_labels.tif", labels.astype(np.uint16))

fig, ax = plt.subplots(1, 2, figsize=(16, 8))
disp = exposure.equalize_adapthist(norm, clip_limit=0.02)
ax[0].imshow(disp, cmap="gray"); ax[0].set_title("Input (contrast enhanced)")
ax[1].imshow(segmentation.mark_boundaries(np.dstack([disp] * 3), labels,
                                          color=(1, 0.2, 0.2), mode="inner"))
ax[1].set_title(f"Segmentation: {labels.max()} nuclei")
for a in ax: a.axis("off")
plt.tight_layout()
plt.savefig("nuclei_segmentation_QC.png", dpi=150)
