import numpy as np
import pandas as pd
import tifffile
from skimage import measure, filters, segmentation
from scipy import ndimage as ndi
from cellpose import models

# ----------------------------- parameters ---------------------------------
IMG_PATH = "bf.tif"
PIXEL_SIZE_UM = 0.65            # µm per pixel
PX_AREA_UM2 = PIXEL_SIZE_UM ** 2

# Size limits (µm). Endothelial cells ~25-50 µm, cancer cells ~15-25 µm.
MIN_AREA_UM2 = 150.0            # discard small fragments / debris
CANCER_MAX_DIAM_UM = 30.0       # round objects up to this diameter are candidate cancer cells
CANCER_MIN_CIRC = 0.80          # circularity 4*pi*A/P^2 (1 = perfect circle)
CANCER_MIN_SOLIDITY = 0.92
# Refractile (bright halo / dark rim) test: fraction of pixels in the region
# that deviate strongly from the monolayer background intensity.
EXTREME_Z = 2.5
CANCER_MIN_EXTREME_FRAC = 0.15

# ----------------------------- load image ---------------------------------
img = tifffile.imread(IMG_PATH)
img = np.squeeze(img)
if img.ndim != 2:
    raise ValueError(f"Expected a 2D (Y, X) image, got shape {img.shape}")
img = img.astype(np.float32)

# Percentile normalisation (robust for 16-bit data); no resizing is done.
lo, hi = np.percentile(img, (1, 99))
img_n = np.clip((img - lo) / max(hi - lo, 1e-6), 0, 1).astype(np.float32)

# ----------------------------- Cellpose 4 ---------------------------------
# Cellpose 4 (cpsam) is size-agnostic, so no `diameter` is passed and the
# image is processed at its native resolution (no rescaling).
model = models.CellposeModel(gpu=False)
masks, flows, styles = model.eval(
    img_n,
    batch_size=4,
    diameter=80,               # ONLY CHANGE (test): diameter as in the generic-prompt script
    flow_threshold=0.4,
    cellprob_threshold=0.0,
)
masks = np.asarray(masks).astype(np.int32)
print(f"Cellpose raw objects: {masks.max()}")

# ------------- remove round, refractile cancer cells (filtering) ----------
# Background (monolayer) statistics from the whole image, robust to outliers.
med = np.median(img_n)
mad = np.median(np.abs(img_n - med)) * 1.4826 + 1e-6
z = np.abs(img_n - med) / mad                      # robust z-score map
extreme = z > EXTREME_Z                            # very bright or very dark pixels

props = measure.regionprops(masks)
keep_ids, rejected = [], {"small": 0, "cancer": 0}
for p in props:
    area_um2 = p.area * PX_AREA_UM2
    if area_um2 < MIN_AREA_UM2:
        rejected["small"] += 1
        continue
    perim = p.perimeter if p.perimeter > 0 else 1.0
    circ = min(4 * np.pi * p.area / perim ** 2, 1.0)
    diam_um = p.equivalent_diameter * PIXEL_SIZE_UM
    sl = p.slice
    region = p.image
    ext_frac = extreme[sl][region].mean()

    round_small = (diam_um <= CANCER_MAX_DIAM_UM and
                   circ >= CANCER_MIN_CIRC and
                   p.solidity >= CANCER_MIN_SOLIDITY)
    refractile_round = (ext_frac >= CANCER_MIN_EXTREME_FRAC and
                        circ >= CANCER_MIN_CIRC and
                        p.solidity >= CANCER_MIN_SOLIDITY and
                        diam_um <= 1.3 * CANCER_MAX_DIAM_UM)
    if round_small or refractile_round:
        rejected["cancer"] += 1
        continue
    keep_ids.append(p.label)

filtered = np.where(np.isin(masks, keep_ids), masks, 0)
filtered, _, _ = segmentation.relabel_sequential(filtered)
filtered = filtered.astype(np.uint16)

# ----------------------------- outputs ------------------------------------
tifffile.imwrite("labels.tif", filtered)

final_props = measure.regionprops(filtered)
df = pd.DataFrame({
    "label": [p.label for p in final_props],
    "area_um2": [p.area * PX_AREA_UM2 for p in final_props],
})
df.to_csv("areas.csv", index=False)

print(f"Removed as small fragments: {rejected['small']}")
print(f"Removed as round/refractile (cancer) cells: {rejected['cancer']}")
print(f"Number of endothelial cells: {len(df)}")
