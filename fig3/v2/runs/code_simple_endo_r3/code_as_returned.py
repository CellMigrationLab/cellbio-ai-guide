"""Segment endothelial cells in a brightfield monolayer; measure area and aspect ratio.

Reads image.tif from the working directory; writes labels.tif and measurements.csv.
Requires: numpy scipy scikit-image tifffile pandas cellpose (>=4, Cellpose-SAM)
"""
import sys

import numpy as np
import pandas as pd
import tifffile
from cellpose import models
from scipy import ndimage as ndi
from skimage import measure, morphology, segmentation

# µm per pixel. Leave None to read it from the TIFF tags; the script stops if it's missing.
PIXEL_SIZE_UM = None

MIN_AREA_PX = 300      # drop debris and fragments
CANCER_OVERLAP = 0.4   # drop a label if this fraction lies on the cancer-cell mask
CANCER_Z = 2.5         # |local z-score| marking the dark-edge / bright-halo of cancer cells


def read_pixel_size(path):
    with tifffile.TiffFile(path) as tf:
        page = tf.pages[0]
        xres = page.tags.get("XResolution")
        if xres is None or xres.value[0] == 0:
            return None
        px_per_unit = xres.value[0] / xres.value[1]
        unit = page.tags.get("ResolutionUnit")
        unit = getattr(unit.value, "name", str(unit.value)).upper() if unit else "INCH"
        if "CENTIMETER" in unit:
            return 1e4 / px_per_unit
        if "INCH" in unit:
            return 25400.0 / px_per_unit
        # ImageJ-style files (unit "NONE") keep the unit in the description
        desc = page.tags.get("ImageDescription")
        if desc is not None and ("unit=micron" in desc.value or "unit=µm" in desc.value):
            return 1.0 / px_per_unit
        return None


def load_gray(path):
    img = tifffile.imread(path).astype(np.float32)
    if img.ndim == 3:  # RGB or channel-first: average over the small axis
        img = img.mean(axis=int(np.argmin(img.shape)))
    return img


def local_normalize(img, sigma=25):
    """Remove brightness and contrast differences across the field, including the seam."""
    mean = ndi.gaussian_filter(img, sigma)
    var = ndi.gaussian_filter((img - mean) ** 2, sigma)
    return (img - mean) / np.sqrt(var + 1e-6)


def cancer_cell_mask(norm):
    ring = np.abs(ndi.gaussian_filter(norm, 1)) > CANCER_Z
    ring = morphology.binary_closing(ring, morphology.disk(3))
    filled = ndi.binary_fill_holes(ring)
    filled = morphology.remove_small_objects(filled, 150)
    return morphology.binary_dilation(filled, morphology.disk(2))


def main():
    img = load_gray("image.tif")

    px = PIXEL_SIZE_UM or read_pixel_size("image.tif")
    if not px:
        sys.exit("No pixel size in image.tif; set PIXEL_SIZE_UM at the top of the script.")

    norm = local_normalize(img)
    lo, hi = np.percentile(norm, [1, 99])
    net_in = np.clip((norm - lo) / (hi - lo), 0, 1)

    model = models.CellposeModel(gpu=True)  # set gpu=False if you have no GPU
    masks = model.eval(net_in, flow_threshold=0.4, cellprob_threshold=0.0)[0]

    # Remove labels that are really cancer cells sitting on top
    cancer = cancer_cell_mask(norm)
    for r in measure.regionprops(masks):
        rr, cc = r.coords[:, 0], r.coords[:, 1]
        if cancer[rr, cc].mean() > CANCER_OVERLAP:
            masks[rr, cc] = 0

    # Drop small fragments and cells cut by the border (their shape would be biased)
    keep = np.zeros_like(masks)
    for r in measure.regionprops(masks):
        minr, minc, maxr, maxc = r.bbox
        touches = minr == 0 or minc == 0 or maxr == masks.shape[0] or maxc == masks.shape[1]
        if r.area >= MIN_AREA_PX and not touches:
            keep[masks == r.label] = r.label
    labels = segmentation.relabel_sequential(keep)[0].astype(np.uint16)

    rows = [
        {
            "label": r.label,
            "area_um2": r.area * px ** 2,
            "aspect_ratio": r.major_axis_length / max(r.minor_axis_length, 1e-6),
        }
        for r in measure.regionprops(labels)
    ]
    pd.DataFrame(rows).to_csv("measurements.csv", index=False)
    tifffile.imwrite("labels.tif", labels)
    print(f"{len(rows)} endothelial cells; pixel size {px:.4f} µm/px")


if __name__ == "__main__":
    main()
