import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from skimage import filters, measure, morphology, segmentation
from cellpose import models

# ----------------------------- parameters -----------------------------
IMG_PATH = "bf.tif"
PIXEL_UM = 0.65                       # µm per pixel
PX_AREA = PIXEL_UM ** 2               # µm² per pixel

# Cancer cell size: ~15-25 µm across -> area of a circle (µm²), with some tolerance
MIN_AREA_UM2 = np.pi / 4 * 12 ** 2    # ~113 µm²  (12 µm diameter)
MAX_AREA_UM2 = np.pi / 4 * 30 ** 2    # ~707 µm²  (30 µm diameter)

MIN_SOLIDITY = 0.90                   # round, convex objects
MAX_ECCENTRICITY = 0.80               # roughly circular
MIN_RIM_RATIO = 1.5                   # rim gradient vs. typical (endothelial) gradient
# Refractile cells show a strong bright/dark halo at their edge; the flat
# endothelial monolayer has weak gradients. Raise MIN_RIM_RATIO if flat cells
# leak through, lower it if real cancer cells are lost (see features table).

# ----------------------------- load image -----------------------------
img = tifffile.imread(IMG_PATH)
img = np.squeeze(img)
assert img.ndim == 2, f"Expected 2D (Y, X) image, got shape {img.shape}"
img = img.astype(np.float32)

# ----------------------------- Cellpose -------------------------------
# Cellpose 4 (cpsam) is size-invariant; no diameter is passed, so no resizing.
model = models.CellposeModel(gpu=False)
masks, flows, styles = model.eval(
    img,
    diameter=None,            # do not rescale the image
    flow_threshold=0.4,
    cellprob_threshold=0.0,
    batch_size=1,             # light on memory for CPU
)
masks = np.asarray(masks).astype(np.int32)
print(f"Cellpose found {masks.max()} candidate objects (cancer + endothelial)")

# ------------------- keep only cancer-cell-like objects ----------------
# Gradient magnitude of the lightly smoothed image, used to measure edge/halo strength
smooth = filters.gaussian(img, sigma=1, preserve_range=True)
grad = filters.sobel(smooth)
grad_ref = np.median(grad)            # dominated by flat monolayer texture
grad_ref = max(grad_ref, 1e-6)

rows = []
keep_ids = []
for r in measure.regionprops(masks):
    area_um2 = r.area * PX_AREA
    obj = masks == r.label
    # rim = thin band straddling the cell boundary
    inner = ndi.binary_erosion(obj, iterations=2)
    outer = ndi.binary_dilation(obj, iterations=2)
    rim = outer & ~inner
    rim_ratio = grad[rim].mean() / grad_ref

    # local contrast: inside vs. a ring around the cell (excluding other labels)
    ring = ndi.binary_dilation(obj, iterations=8) & ~ndi.binary_dilation(obj, iterations=3) & (masks == 0)
    contrast = (abs(smooth[obj].mean() - smooth[ring].mean()) / (smooth[ring].std() + 1e-6)
                if ring.sum() > 10 else np.nan)

    ok = (
        MIN_AREA_UM2 <= area_um2 <= MAX_AREA_UM2
        and r.solidity >= MIN_SOLIDITY
        and r.eccentricity <= MAX_ECCENTRICITY
        and rim_ratio >= MIN_RIM_RATIO
    )
    rows.append(dict(label=r.label, area_um2=area_um2, solidity=r.solidity,
                     eccentricity=r.eccentricity, rim_ratio=rim_ratio,
                     contrast=contrast, kept=ok))
    if ok:
        keep_ids.append(r.label)

features = pd.DataFrame(rows)
features.to_csv("candidate_features.csv", index=False)  # for tuning the thresholds

# ----------------------------- final labels ---------------------------
final = np.where(np.isin(masks, keep_ids), masks, 0)
final, _, _ = segmentation.relabel_sequential(final)
final = final.astype(np.uint16)

tifffile.imwrite("labels.tif", final)

props = measure.regionprops(final)
areas = pd.DataFrame({
    "label": [p.label for p in props],
    "area_um2": [p.area * PX_AREA for p in props],
})
areas.to_csv("areas.csv", index=False)

print(f"Number of cancer cells: {len(props)}")
