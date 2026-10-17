import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from skimage import filters, morphology, measure, segmentation, util

# ---------------- parameters (tune these) ----------------
PIXEL_SIZE_UM = None        # set e.g. 0.65 if the TIFF has no calibration metadata
DIAMETER_PX = None          # None = let Cellpose decide; ~50-70 px for this image if needed
BACKGROUND_SIGMA = 50       # px, flat-field correction
CONTRAST_SIGMA = 2          # px, smoothing of the contrast map for the cancer-cell mask
CANCER_THRESH = None        # None = Otsu on the contrast map; or set a number
CANCER_MIN_AREA = 250       # px, removes small debris from the cancer mask
CANCER_DILATE = 3           # px
MAX_CANCER_OVERLAP = 0.3    # drop endothelial cells overlapping the mask more than this
MIN_AREA_UM2 = 100          # drop tiny fragments
REMOVE_BORDER = True        # edge-touching cells have truncated shapes
# ----------------------------------------------------------


def read_pixel_size_um(path):
    """Return um/pixel from TIFF/ImageJ metadata, or None."""
    with tifffile.TiffFile(path) as tf:
        page = tf.pages[0]
        tags = page.tags
        if "XResolution" not in tags:
            return None
        num, den = tags["XResolution"].value
        if num == 0:
            return None
        px_per_unit = num / den
        unit = tags["ResolutionUnit"].value if "ResolutionUnit" in tags else 1
        ij = tf.imagej_metadata or {}
        ij_unit = ij.get("unit", "")
        if ij_unit in ("um", "µm", "micron", "microns"):
            return 1.0 / px_per_unit
        if int(unit) == 3:      # centimetre
            return 1e4 / px_per_unit
        if int(unit) == 2:      # inch
            return 25400 / px_per_unit
        return None


img = tifffile.imread("image.tif")
if img.ndim > 2:
    img = img[..., 0] if img.shape[-1] in (3, 4) else img[0]
img = img.astype(np.float32)

pix = PIXEL_SIZE_UM or read_pixel_size_um("image.tif")
if pix is None:
    raise SystemExit("No pixel size found in image.tif; set PIXEL_SIZE_UM at the top of the script.")
print(f"Pixel size: {pix:.4f} um/px")

# --- flat-field correct and normalise ---
flat = img - ndi.gaussian_filter(img, BACKGROUND_SIGMA)
flat /= flat.std()

# --- segment all cells with Cellpose ---
from cellpose import models

model = models.CellposeModel(gpu=True)   # Cellpose >= 4 (default model: cpsam)
masks, _, _ = model.eval(flat, diameter=DIAMETER_PX)[:3]
masks = masks.astype(np.int32)

# --- cancer cell mask: round objects with strong dark rim / bright halo ---
contrast = ndi.gaussian_filter(np.abs(flat), CONTRAST_SIGMA)
thr = CANCER_THRESH if CANCER_THRESH is not None else filters.threshold_otsu(contrast)
cancer = contrast > thr
cancer = morphology.binary_closing(cancer, morphology.disk(3))
cancer = ndi.binary_fill_holes(cancer)
cancer = morphology.remove_small_objects(cancer, CANCER_MIN_AREA)
cancer = morphology.binary_dilation(cancer, morphology.disk(CANCER_DILATE))

# --- keep endothelial cells only ---
keep = np.zeros_like(masks)
for r in measure.regionprops(masks):
    rr, cc = r.coords[:, 0], r.coords[:, 1]
    if cancer[rr, cc].mean() > MAX_CANCER_OVERLAP:
        continue
    if r.area * pix**2 < MIN_AREA_UM2:
        continue
    keep[rr, cc] = r.label

if REMOVE_BORDER:
    keep = segmentation.clear_border(keep)

labels, _, _ = segmentation.relabel_sequential(keep)
tifffile.imwrite("labels.tif", labels.astype(np.uint16))

# --- measurements ---
rows = []
for r in measure.regionprops(labels):
    minor = max(r.minor_axis_length, 1e-6)
    rows.append({
        "label": r.label,
        "area_um2": r.area * pix**2,
        "aspect_ratio": r.major_axis_length / minor,
    })
df = pd.DataFrame(rows)
df.to_csv("measurements.csv", index=False)

print(f"Endothelial cells counted: {len(df)}")
print(df[["area_um2", "aspect_ratio"]].describe().loc[["mean", "50%", "std"]])

# optional QC overlay (check this before trusting the numbers)
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.imshow(img, cmap="gray")
    ax.contour(cancer, [0.5], colors="red", linewidths=0.6)
    ax.imshow(np.ma.masked_equal(segmentation.find_boundaries(labels), 0),
              cmap="autumn", alpha=0.9)
    ax.axis("off")
    fig.savefig("qc_overlay.png", dpi=150, bbox_inches="tight")
except ImportError:
    pass
