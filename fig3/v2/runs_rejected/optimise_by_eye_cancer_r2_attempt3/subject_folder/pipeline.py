"""Segment cancer cells in 2D brightfield images (on an endothelial monolayer) with Cellpose-SAM.

Usage: python pipeline.py <input.tif> <labels.tif> <measurements.csv>

Steps (all parameters are module constants below):
 1. read single-channel 2D image (Y, X), uint16 -> float32; pixel size fixed in PIXEL_SIZE_UM
 2. flatten illumination: subtract a large-scale median background and divide by a local robust
    contrast (handles uneven illumination and tile seams with intensity steps)
 3. Cellpose (cpsam) at native scale (cells ~30 px = what the model was trained for; no resizing)
 4. post-processing: drop small objects, flag border-touching objects
 5. write label image (same Y,X grid as input, uint16) and a CSV of area (um^2) and aspect ratio
"""
import sys
import numpy as np
import csv
import tifffile
from scipy import ndimage as ndi
from skimage import filters, measure, segmentation, transform

PIXEL_SIZE_UM = 0.65
BACKGROUND_SIGMA_PX = 60        # scale of illumination flattening (>> cell size ~30 px)
CELLPOSE_MODEL = "cpsam_v2"      # must exist in ~/.cellpose/models
DIAMETER_PX = None               # None: no rescaling; cells ~15-25 um = 23-38 px, close to 30 px
FLOW_THRESHOLD = 0.4
CELLPROB_THRESHOLD = 0.0
MIN_AREA_UM2 = 60.0              # ~ 8.7 um equivalent diameter; below = debris
MAX_AREA_UM2 = 600.0             # ~ 28 um equivalent diameter; above = not a single cancer cell
RIM_WIDTH_PX = 2
MIN_RIM_GRADIENT = 2.4           # mean Sobel gradient of flattened image on mask rim (endothelial < 2.3)
MIN_INTERNAL_STD = 4.3           # std of flattened intensity inside mask
MIN_SOLIDITY = 0.9               # merged/odd shapes are removed rather than mis-measured


def read_image(path: str) -> np.ndarray:
    img = tifffile.imread(path)
    if img.ndim != 2:
        raise ValueError(f"Expected a 2D (Y, X) single-channel image, got shape {img.shape}")
    if img.dtype != np.uint16:
        raise ValueError(f"Expected uint16, got {img.dtype}")
    return img.astype(np.float32)


def flatten_illumination(img: np.ndarray) -> np.ndarray:
    """Subtract local median background (computed on a 4x downsample for speed) and scale by local MAD."""
    f = 4
    small = transform.downscale_local_mean(img, (f, f))
    bg = ndi.median_filter(small, size=int(2 * BACKGROUND_SIGMA_PX / f) | 1, mode="reflect")
    resid = small - bg
    scale = ndi.median_filter(np.abs(resid), size=int(2 * BACKGROUND_SIGMA_PX / f) | 1, mode="reflect")
    bg_full = transform.resize(bg, img.shape, order=1, mode="edge")
    sc_full = transform.resize(scale, img.shape, order=1, mode="edge")
    if np.any(sc_full <= 0):
        raise ValueError("Local contrast estimate is zero somewhere; image is constant there")
    return (img - bg_full) / sc_full


def segment(flat: np.ndarray) -> np.ndarray:
    from cellpose import models
    model = models.CellposeModel(gpu=False, pretrained_model=CELLPOSE_MODEL)
    masks, _, _ = model.eval(flat, diameter=DIAMETER_PX, flow_threshold=FLOW_THRESHOLD,
                             cellprob_threshold=CELLPROB_THRESHOLD, normalize=True, batch_size=4)
    return masks.astype(np.int32)


def classify_cancer_cells(masks: np.ndarray, flat: np.ndarray) -> np.ndarray:
    """Keep objects that look like rounded cancer cells; drop endothelial cells and debris.

    Cancer cells are phase-bright/dark rimmed spheres: strong edge gradient on the mask rim and
    high internal contrast. Endothelial cells are flat, low-contrast and get large polygonal masks.
    """
    px_area = PIXEL_SIZE_UM ** 2
    grad = filters.sobel(ndi.gaussian_filter(flat, 1))
    keep = np.zeros_like(masks)
    for r in measure.regionprops(masks):
        area = r.area * px_area
        m = masks == r.label
        rim = m & ~ndi.binary_erosion(m, iterations=RIM_WIDTH_PX)
        if (MIN_AREA_UM2 <= area <= MAX_AREA_UM2 and grad[rim].mean() >= MIN_RIM_GRADIENT
                and flat[m].std() >= MIN_INTERNAL_STD and r.solidity >= MIN_SOLIDITY):
            keep[m] = r.label
    relabeled, _, _ = segmentation.relabel_sequential(keep)
    return relabeled.astype(np.uint16)


def measure_objects(labels: np.ndarray) -> list[dict]:
    h, w = labels.shape
    rows = []
    for r in measure.regionprops(labels):
        y0, x0, y1, x1 = r.bbox
        rows.append(dict(
            label=r.label,
            centroid_y_um=round(r.centroid[0] * PIXEL_SIZE_UM, 3),
            centroid_x_um=round(r.centroid[1] * PIXEL_SIZE_UM, 3),
            area_um2=round(r.area * PIXEL_SIZE_UM ** 2, 3),
            aspect_ratio=round(r.axis_major_length / r.axis_minor_length, 4),
            touches_border=bool(y0 == 0 or x0 == 0 or y1 == h or x1 == w),
        ))
    return rows


def write_table(rows: list[dict], path: str) -> None:
    fields = ["label", "centroid_y_um", "centroid_x_um", "area_um2", "aspect_ratio", "touches_border"]
    with open(path, "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=fields)
        wr.writeheader()
        wr.writerows(rows)


def main(inp: str, out_labels: str, out_csv: str) -> None:
    img = read_image(inp)
    flat = flatten_illumination(img)
    labels = classify_cancer_cells(segment(flat), flat)
    tifffile.imwrite(out_labels, labels, compression="zlib")
    rows = measure_objects(labels)
    write_table(rows, out_csv)
    print(f"{len(rows)} cells ({sum(r['touches_border'] for r in rows)} touch border)")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
