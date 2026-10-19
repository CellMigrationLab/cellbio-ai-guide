"""Segment cancer cells in 2D brightfield images and measure area / aspect ratio.

Usage: python pipeline.py <input.tif> <labels.tif> <measurements.csv>

Steps (all parameters in PARAMS):
 1. Read 2D uint16 image (Y, X); reject anything else.
 2. Flat-field correction: divide by a heavy Gaussian-blurred copy (removes uneven illumination).
 3. Cellpose (pretrained 'cpsam_v2', CPU), diameter in pixels, intensity normalised by Cellpose
    (1st-99th percentile) on the flat-fielded image.
 4. Post-processing: keep objects within an area window with textured interior (see
    filter_objects); labels relabelled sequentially. Border-touching cells are kept (flagged in the table).
 5. Measurements in physical units (pixel size 0.65 um): area_um2, aspect_ratio (major/minor
    axis of the equivalent ellipse).
Coordinates of the input are preserved (label image has the same shape as the input).
"""
import sys
import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from skimage import measure, segmentation

PARAMS = dict(
    pixel_size_um=0.65,
    flatfield_sigma_px=50,
    diameter_px=25.0,
    flow_threshold=0.4,
    cellprob_threshold=0.0,
    min_area_um2=120.0,          # ~12 um equivalent diameter; below stated 15-25 um size range
    min_area_border_um2=60.0,    # cells cut by the image border are legitimately smaller
    max_area_um2=700.0,          # removes endothelial cells segmented as one object
    min_texture=0.03,            # mean 5x5 local std of flat-fielded image inside object
    model="cpsam_v2",
)


def read_image(path: str) -> np.ndarray:
    img = tifffile.imread(path)
    if img.ndim != 2:
        raise ValueError(f"Expected a 2D (Y, X) image, got shape {img.shape}")
    if img.dtype != np.uint16:
        raise ValueError(f"Expected uint16, got {img.dtype}")
    if img.max() > 4095:
        raise ValueError(f"Values exceed 12-bit range (max {img.max()})")
    return img


def flatfield(img: np.ndarray, sigma_px: float) -> np.ndarray:
    """Divide by large-scale background; result has mean ~1 (float32)."""
    f = img.astype(np.float32)
    bg = ndi.gaussian_filter(f, sigma_px, mode="reflect")
    if bg.min() <= 0:
        raise ValueError("Non-positive background estimate in flat-field correction")
    return f / bg


def run_cellpose(img: np.ndarray, p: dict) -> np.ndarray:
    from cellpose import models
    model = models.CellposeModel(gpu=False, pretrained_model=p["model"])
    masks, _, _ = model.eval(
        img, diameter=p["diameter_px"], normalize=True,
        flow_threshold=p["flow_threshold"], cellprob_threshold=p["cellprob_threshold"],
        batch_size=4,
    )
    return masks.astype(np.int32)


def local_std(f: np.ndarray, size: int = 5) -> np.ndarray:
    mean = ndi.uniform_filter(f, size)
    return np.sqrt(np.maximum(ndi.uniform_filter(f * f, size) - mean ** 2, 0))


def filter_objects(labels: np.ndarray, corrected: np.ndarray, p: dict) -> np.ndarray:
    """Keep cancer-cell-like objects: area window and textured interior.

    Endothelial cells are large and smooth; debris is small. Thresholds were set on
    image.tif only (see log.txt).
    """
    h, w = labels.shape
    px2 = p["pixel_size_um"] ** 2
    texture = local_std(corrected)
    keep = np.zeros(labels.max() + 1, bool)
    for r in measure.regionprops(labels):
        minr, minc, maxr, maxc = r.bbox
        border = minr == 0 or minc == 0 or maxr == h or maxc == w
        area = r.area * px2
        min_area = p["min_area_border_um2"] if border else p["min_area_um2"]
        tex = texture[tuple(r.coords.T)].mean()
        keep[r.label] = min_area <= area <= p["max_area_um2"] and tex >= p["min_texture"]
    out = np.where(keep[labels], labels, 0)
    out, _, _ = segmentation.relabel_sequential(out)
    return out.astype(np.int32)


def measure_cells(labels: np.ndarray, pixel_size_um: float) -> pd.DataFrame:
    h, w = labels.shape
    rows = []
    for r in measure.regionprops(labels):
        minr, minc, maxr, maxc = r.bbox
        minor = r.axis_minor_length
        if minor <= 0:
            raise ValueError(f"Degenerate object {r.label}: zero minor axis")
        rows.append(dict(
            label=r.label,
            area_um2=r.area * pixel_size_um ** 2,
            aspect_ratio=r.axis_major_length / minor,
            centroid_y_um=r.centroid[0] * pixel_size_um,
            centroid_x_um=r.centroid[1] * pixel_size_um,
            touches_border=bool(minr == 0 or minc == 0 or maxr == h or maxc == w),
        ))
    return pd.DataFrame(rows, columns=["label", "area_um2", "aspect_ratio",
                                       "centroid_y_um", "centroid_x_um", "touches_border"])


def segment(img: np.ndarray, p: dict = PARAMS) -> np.ndarray:
    corrected = flatfield(img, p["flatfield_sigma_px"])
    # Cellpose can normalise its input in place; pass a copy so `corrected` stays intact
    labels = run_cellpose(corrected.copy(), p)
    return filter_objects(labels, corrected, p)


def main(inp: str, out_labels: str, out_csv: str) -> None:
    img = read_image(inp)
    labels = segment(img)
    tifffile.imwrite(out_labels, labels, compression="zlib")
    table = measure_cells(labels, PARAMS["pixel_size_um"])
    table.to_csv(out_csv, index=False)
    print(f"{len(table)} cells; median area {table.area_um2.median():.1f} um2; "
          f"median aspect {table.aspect_ratio.median():.2f}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
