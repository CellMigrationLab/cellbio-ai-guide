# code_generic_prompt

## USER (2026-10-16T18:00:46.865Z)

Act as a helpful assistant for a cell biologist. You cannot run code. You may use the Read tool ONLY to view the image the user attached: <fig3-work>/v3/codeB/nuclei_preview.png (a preview of their file nuclei.tif). Do not open anything else.

The user writes: "Please analyse this image and segment the nuclei." (attached: nuclei.tif)

Reply as you normally would. If you provide code, put it in a single complete ```python block.

## HARNESS NOTE (2026-10-16T18:00:46.893Z)

<system-reminder>
Your final report is delivered through SubagentHandback: when your work is complete, call SubagentHandback({message: <your full report>}). The call ends your run, so make it your last step. Only a SubagentHandback call reaches your caller as your result; plain text you write at the end is not delivered. Do not also send the report with SendMessage: your caller would get it twice.
</system-reminder>

*[tool call: Read: <fig3-work>/v3/codeB/nuclei_preview.png]*

## ASSISTANT (final report)

I can't run code, so I haven't segmented anything. Below is what I see in the preview and a script for you to run. The parameters are starting guesses that you'll need to check against your own image.

**What the image shows (from the 512x512 preview only)**
- It looks like a single-channel fluorescence image of a nuclear stain such as DAPI or Hoechst, with a dense field of hundreds of nuclei.
- Most nuclei are dim, oval and about 10-16 px long in the preview. The real tif may be higher resolution, so check the size in your file.
- A second population is much brighter and rounder, often in clumps. These could be mitotic or condensed nuclei, pyknotic or dead cells, or out-of-focus or overlapping cells. A few tiny, very bright specks are probably debris.
- There is a hazy, uneven background, especially around the bright clusters and at the edges.
- Many nuclei touch or nearly touch.
- The dim and bright nuclei differ in intensity by an order of magnitude or more. A single global threshold would either miss the dim ones or merge the bright clumps. That is why the script uses a log transform with a local threshold, followed by a watershed to split touching nuclei.

**Segmentation script (classical approach: scikit-image, SciPy, tifffile)**

```python
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
```

**How to check and tune it**
1. Open `nuclei_segmentation_QC.png` and zoom into a dense area and a bright clump.
2. If dim nuclei are missing, lower `LOCAL_OFFSET` (for example to -0.02) or lower the `0.5` factor on the Otsu floor.
3. If background haze is picked up, raise `LOCAL_OFFSET` or the Otsu factor.
4. If nuclei are over-split, raise `H_MAXIMA` or `MIN_AREA`. If clumps stay merged, lower `H_MAXIMA` to about 0.3-0.5.
5. Check that the pixel size and the `MIN_AREA` and `MAX_AREA` values match your real nucleus size. I estimated them from a downsampled preview.

**Decisions for you**
- **Bright blobs:** decide whether to keep them. If they are mitotic or dead cells, you may want to count them separately. The CSV has `mean_intensity`, and you could split on a threshold such as the 90th percentile.
- **Dense clumps:** the bright clumps (for example near the top left and around x=360, y=370 in the preview) will be the hardest to split with any classical method. Treat counts there with caution.
- **Cellpose:** if the QC overlay is not good enough, a deep-learning model usually handles dense, variable-intensity nuclei better. The call is `cellpose.models.CellposeModel(model_type="nuclei")` with `diameter` set to your nucleus diameter in px, or StarDist's `2D_versatile_fluo`. I can write that version if you want it.

If you tell me the pixel size, the stain, and whether you want the bright cells counted, I can tune the parameters. If you run the script and send me the QC image or the console output, I can help refine it.
