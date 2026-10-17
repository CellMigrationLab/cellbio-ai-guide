"""Segment endothelial cells in a brightfield monolayer and measure shape.

Reads image.tif, writes labels.tif and measurements.csv, plus overlay.png for QC.
Requires: pip install cellpose tifffile scikit-image scipy pandas matplotlib
(written for Cellpose >= 4, "cpsam"; for Cellpose 3 see the note in segment()).
"""
import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from skimage import filters, measure, morphology, segmentation

# ---- parameters to adjust ---------------------------------------------------
PIXEL_SIZE_UM = None     # µm per pixel; if None, read from the TIFF tags, else error
DIAMETER_PX = None       # expected endothelial cell diameter in px (None = automatic)
RIM_K = 4.0              # how far (in robust SDs) below background a pixel must be
                         # to count as a dark cancer-cell rim
MIN_CANCER_AREA_PX = 300 # smallest filled blob treated as a cancer cell/debris
OVERLAP_DROP = 0.3       # drop a label if more than this fraction lies in that mask
MIN_CELL_AREA_PX = 400   # discard small fragments
# -----------------------------------------------------------------------------


def get_pixel_size(path):
    if PIXEL_SIZE_UM is not None:
        return PIXEL_SIZE_UM
    with tifffile.TiffFile(path) as tf:
        page = tf.pages[0]
        xres = page.tags.get("XResolution")
        unit = page.tags.get("ResolutionUnit")
        if xres is not None:
            num, den = xres.value
            per_unit = num / den
            u = unit.value if unit is not None else 2
            um_per_unit = {1: None, 2: 25400.0, 3: 10000.0}.get(int(u))
            if um_per_unit and per_unit > 0:
                return um_per_unit / per_unit
    try:  # ImageJ-style metadata
        with tifffile.TiffFile(path) as tf:
            ij = tf.imagej_metadata or {}
            if ij.get("unit") in ("micron", "um", "µm") and "spacing" not in ij:
                pass
    except Exception:
        pass
    raise SystemExit("No pixel size found in image.tif: set PIXEL_SIZE_UM at the top.")


def load_gray(path):
    img = tifffile.imread(path).astype(np.float32)
    if img.ndim == 3:  # RGB or channel-first stack -> take mean over the small axis
        axis = int(np.argmin(img.shape))
        img = img.mean(axis=axis)
    return img


def flatten(img):
    """Remove uneven illumination, normalise to ~1 at background."""
    bg = filters.gaussian(img, sigma=50, preserve_range=True)
    return img / np.maximum(bg, 1e-6)


def cancer_and_debris_mask(flat):
    """High-contrast objects: dark rims of round cancer cells, debris, bright glare."""
    med = np.median(flat)
    mad = np.median(np.abs(flat - med)) * 1.4826
    dark = flat < med - RIM_K * mad
    bright = flat > med + RIM_K * mad * 1.5
    strong = morphology.binary_closing(dark | bright, morphology.disk(2))
    filled = ndi.binary_fill_holes(morphology.binary_closing(strong, morphology.disk(4)))
    filled = morphology.remove_small_objects(filled, MIN_CANCER_AREA_PX)
    return morphology.binary_dilation(filled, morphology.disk(3))


def segment(flat):
    from cellpose import models
    model = models.CellposeModel(gpu=True)
    # Cellpose 3 instead: models.Cellpose(model_type="cyto3", gpu=True)
    #   and model.eval(..., channels=[0, 0])
    lo, hi = np.percentile(flat, [1, 99])
    norm = np.clip((flat - lo) / (hi - lo), 0, 1)
    masks, _, _ = model.eval(norm, diameter=DIAMETER_PX)
    return masks


def main():
    path = "image.tif"
    px = get_pixel_size(path)
    img = load_gray(path)
    flat = flatten(img)

    masks = segment(flat)
    exclude = cancer_and_debris_mask(flat)

    keep = np.zeros_like(masks)
    new_id = 0
    for r in measure.regionprops(masks):
        if r.area < MIN_CELL_AREA_PX:
            continue
        rr, cc = r.coords[:, 0], r.coords[:, 1]
        if exclude[rr, cc].mean() > OVERLAP_DROP:
            continue
        new_id += 1
        keep[rr, cc] = new_id

    labels = measure.label(keep > 0, connectivity=1) if False else keep  # keep ids as assigned
    tifffile.imwrite("labels.tif", labels.astype(np.uint16))

    rows = []
    for r in measure.regionprops(labels):
        minor = max(r.minor_axis_length, 1e-6)
        rows.append({
            "label": r.label,
            "area_um2": r.area * px**2,
            "aspect_ratio": r.major_axis_length / minor,
        })
    pd.DataFrame(rows).to_csv("measurements.csv", index=False)
    print(f"{len(rows)} endothelial cells; pixel size {px:.4f} µm")

    # QC overlay: cell outlines in yellow, excluded mask in red
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.imshow(img, cmap="gray")
    ax.contour(exclude, levels=[0.5], colors="red", linewidths=0.5)
    ax.imshow(np.ma.masked_equal(segmentation.find_boundaries(labels), 0),
              cmap="autumn", alpha=0.9)
    ax.axis("off")
    fig.savefig("overlay.png", dpi=150, bbox_inches="tight")


if __name__ == "__main__":
    main()
