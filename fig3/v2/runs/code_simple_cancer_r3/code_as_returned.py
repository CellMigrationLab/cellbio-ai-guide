#!/usr/bin/env python
"""Segment cancer cells in brightfield (on an endothelial monolayer) and measure
area (µm²) and aspect ratio. Reads image.tif, writes labels.tif, measurements.csv
and qc_overlay.png."""
import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from skimage import filters, morphology, measure, segmentation, feature, io

# ---------------- parameters ----------------
PIXEL_SIZE_UM = None      # µm/pixel; None = try TIFF metadata. SET THIS if metadata is missing.
CELL_DIAMETER_PX = 25     # typical cancer-cell diameter in pixels (~25 in the example)
MIN_AREA_UM2 = None       # None -> 30% of a typical cell area
MAX_AREA_UM2 = None       # None -> 4x a typical cell area
MIN_SOLIDITY = 0.85       # rejects ragged debris
EXCLUDE_BORDER = True     # cut-off cells give wrong area/aspect ratio
# --------------------------------------------


def get_pixel_size(path):
    with tifffile.TiffFile(path) as tf:
        page = tf.pages[0]
        xr = page.tags.get("XResolution")
        unit = page.tags.get("ResolutionUnit")
        if xr is None:
            return None
        num, den = xr.value
        if num == 0:
            return None
        per_unit = num / den                      # pixels per unit
        unit = getattr(unit.value, "name", str(unit.value)) if unit else "INCH"
        um_per_unit = {"CENTIMETER": 1e4, "INCH": 25400.0, "NONE": None}.get(unit.upper())
        if um_per_unit is None:
            return None
        px = um_per_unit / per_unit
        return px if px != 25400.0 else None      # 1 px/inch = default placeholder


def to_gray(img):
    img = np.squeeze(img)
    if img.ndim == 3:
        ch_axis = int(np.argmin(img.shape))
        img = img.mean(axis=ch_axis)
    return img.astype(float)


def find_seam(g):
    """Detect a vertical stitching seam (abrupt brightness jump between column blocks)."""
    col = ndi.uniform_filter1d(g.mean(axis=0), 3)
    jump = np.abs(col[5:] - col[:-5])
    x = int(np.argmax(jump)) + 3
    return x if jump.max() > 5 * np.median(jump) + 1e-6 and jump.max() > 0.1 * g.std() else None


def local_normalise(g, sigma=40):
    bg = filters.gaussian(g, sigma, mode="reflect")
    d = g - bg
    sd = np.sqrt(filters.gaussian(d ** 2, sigma, mode="reflect"))
    return d / (sd + 1e-6)


def normalise(g):
    seam = find_seam(g)
    if seam is None:
        return local_normalise(g)
    print(f"Detected seam at x={seam}; normalising each side separately")
    out = np.empty_like(g)
    out[:, :seam] = local_normalise(g[:, :seam])
    out[:, seam:] = local_normalise(g[:, seam:])
    return out


def segment(g):
    n = normalise(g)
    # Cancer cells have a strong dark rim + bright halo -> large |deviation| from local background.
    edge = filters.gaussian(np.abs(n), 1)
    mask = edge > filters.threshold_otsu(edge)
    mask = morphology.binary_closing(mask, morphology.disk(2))
    mask = ndi.binary_fill_holes(mask)                       # fill the cell interior inside the rim
    mask = morphology.binary_opening(mask, morphology.disk(CELL_DIAMETER_PX // 6))
    mask = morphology.remove_small_objects(mask, int(0.15 * np.pi * (CELL_DIAMETER_PX / 2) ** 2))

    # split touching cells
    dist = filters.gaussian(ndi.distance_transform_edt(mask), 1)
    peaks = feature.peak_local_max(dist, min_distance=max(3, CELL_DIAMETER_PX // 3),
                                   threshold_abs=CELL_DIAMETER_PX / 6, labels=measure.label(mask))
    markers = np.zeros_like(mask, dtype=np.int32)
    markers[tuple(peaks.T)] = np.arange(1, len(peaks) + 1)
    return segmentation.watershed(-dist, markers, mask=mask)


def main():
    raw = tifffile.imread("image.tif")
    g = to_gray(raw)

    px = PIXEL_SIZE_UM or get_pixel_size("image.tif")
    if px is None:
        raise SystemExit("No pixel size found in image.tif. Set PIXEL_SIZE_UM at the top of the script.")
    print(f"Pixel size: {px:.4f} µm/px")

    lab = segment(g)

    typ_area = np.pi * (CELL_DIAMETER_PX * px / 2) ** 2
    lo = MIN_AREA_UM2 if MIN_AREA_UM2 is not None else 0.3 * typ_area
    hi = MAX_AREA_UM2 if MAX_AREA_UM2 is not None else 4 * typ_area

    keep = np.zeros_like(lab, dtype=np.uint16)
    rows, new_id = [], 0
    h, w = lab.shape
    for r in measure.regionprops(lab):
        area = r.area * px ** 2
        minr, minc, maxr, maxc = r.bbox
        on_border = minr == 0 or minc == 0 or maxr == h or maxc == w
        if not (lo <= area <= hi) or r.solidity < MIN_SOLIDITY:
            continue
        if EXCLUDE_BORDER and on_border:
            continue
        new_id += 1
        keep[lab == r.label] = new_id
        rows.append({"label": new_id, "area_um2": area,
                     "aspect_ratio": r.major_axis_length / max(r.minor_axis_length, 1e-9)})

    tifffile.imwrite("labels.tif", keep)
    pd.DataFrame(rows, columns=["label", "area_um2", "aspect_ratio"]).to_csv("measurements.csv", index=False)
    print(f"{new_id} cells written")

    # QC overlay
    disp = (g - np.percentile(g, 1)) / (np.percentile(g, 99) - np.percentile(g, 1))
    ov = segmentation.mark_boundaries(np.clip(disp, 0, 1), keep, color=(1, 0, 0))
    io.imsave("qc_overlay.png", (ov * 255).astype(np.uint8), check_contrast=False)


if __name__ == "__main__":
    main()
