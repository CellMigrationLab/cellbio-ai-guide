"""Segment cancer cells in 2D brightfield (uint16, 12-bit) and measure area / aspect ratio.

Usage: python pipeline.py <input.tif> <labels.tif> <measurements.csv>

Steps (all parameters in PARAMS):
 1. Load + validate (2D, uint16, 12-bit). The raw file is never modified.
 2. Flat-field: divide by a heavy Gaussian background (uneven illumination), then rescale the
    1st-99th percentiles to 0..1 (explicit; Cellpose's own normalisation is switched off).
 3. Cellpose (pretrained 'cpsam_v2', CPU; model file in ~/.cellpose/models) at original pixel
    size; diameter_px makes Cellpose rescale internally, masks come back at original resolution.
    It segments endothelial cells too, so:
 4. Keep only cancer-cell-like objects: area in [min,max] um^2 and internal texture (std of
    the normalised intensity inside the mask) above a threshold. Border cells are kept, flagged.
 5. Write int32 label image (same shape as input) and CSV (area_um2, aspect_ratio, ...).
"""
import sys
import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from skimage import measure

PIXEL_SIZE_UM = 0.65
PARAMS = dict(
    model="cpsam_v2",
    background_sigma_px=40.0,     # flat-field Gaussian sigma (>> cell size of ~25 px)
    diameter_px=25.0,             # expected cell diameter (~16 um)
    flow_threshold=0.4,
    cellprob_threshold=0.0,
    min_area_um2=60.0,            # smaller objects = debris
    max_area_um2=600.0,           # larger = clumps / endothelial cells
    min_texture_std=0.15,         # endothelial cells are smooth (std~0.07), cancer cells ~0.35
)


def load_image(path: str) -> np.ndarray:
    img = tifffile.imread(path)
    if img.ndim != 2:
        raise ValueError(f"Expected 2D (Y, X) image, got shape {img.shape}")
    if img.dtype != np.uint16:
        raise ValueError(f"Expected uint16, got {img.dtype}")
    if img.max() > 4095:
        raise ValueError(f"Values exceed 12-bit range: max={img.max()}")
    return img


def flatfield_normalise(img: np.ndarray, sigma_px: float, pct=(1.0, 99.0)) -> np.ndarray:
    """Divide by smoothed background, then rescale percentiles to 0..1 (float32)."""
    x = img.astype(np.float32)
    background = ndi.gaussian_filter(x, sigma_px, mode="reflect")
    flat = x / background
    lo, hi = np.percentile(flat, pct)
    if hi <= lo:
        raise ValueError("Image has no contrast after flat-field correction")
    return ((flat - lo) / (hi - lo)).astype(np.float32)


def run_cellpose(norm: np.ndarray, p: dict) -> np.ndarray:
    from cellpose import models
    model = models.CellposeModel(gpu=False, pretrained_model=p["model"])
    masks, _, _ = model.eval(
        norm, diameter=p["diameter_px"], normalize=False,
        flow_threshold=p["flow_threshold"], cellprob_threshold=p["cellprob_threshold"],
        min_size=15,
    )
    return masks.astype(np.int32)


def filter_cancer_cells(labels: np.ndarray, norm: np.ndarray, p: dict, px_um: float) -> np.ndarray:
    """Keep objects with plausible area and enough internal texture; relabel 1..N."""
    out = np.zeros_like(labels)
    keep = 0
    for r in measure.regionprops(labels, intensity_image=norm):
        area = r.area * px_um ** 2
        texture = float(norm[tuple(r.coords.T)].std())
        if p["min_area_um2"] <= area <= p["max_area_um2"] and texture >= p["min_texture_std"]:
            keep += 1
            out[labels == r.label] = keep
    return out


def segment(img: np.ndarray, p: dict = PARAMS) -> np.ndarray:
    norm = flatfield_normalise(img, p["background_sigma_px"])
    raw = run_cellpose(norm, p)
    return filter_cancer_cells(raw, norm, p, PIXEL_SIZE_UM)


def measure_cells(labels: np.ndarray, px_um: float = PIXEL_SIZE_UM) -> pd.DataFrame:
    """Area (um^2) and aspect ratio = major/minor axis of the fitted ellipse (>=1)."""
    h, w = labels.shape
    rows = []
    for r in measure.regionprops(labels):
        minr, minc, maxr, maxc = r.bbox
        rows.append(dict(
            label=r.label,
            area_um2=r.area * px_um ** 2,
            aspect_ratio=r.axis_major_length / r.axis_minor_length if r.axis_minor_length > 0 else np.nan,
            centroid_y_um=r.centroid[0] * px_um,
            centroid_x_um=r.centroid[1] * px_um,
            touches_border=bool(minr == 0 or minc == 0 or maxr == h or maxc == w),
        ))
    return pd.DataFrame(rows, columns=["label", "area_um2", "aspect_ratio", "centroid_y_um",
                                       "centroid_x_um", "touches_border"])


def main(argv):
    if len(argv) != 4:
        raise SystemExit(__doc__)
    inp, out_labels, out_csv = argv[1:]
    img = load_image(inp)
    labels = segment(img)
    tifffile.imwrite(out_labels, labels, compression="zlib")
    table = measure_cells(labels)
    table.to_csv(out_csv, index=False)
    print(f"{labels.max()} cells -> {out_labels}, {out_csv}")


if __name__ == "__main__":
    main(sys.argv)
