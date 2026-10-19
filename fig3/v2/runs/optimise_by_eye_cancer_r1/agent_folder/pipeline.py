"""Segment cancer cells in 2D brightfield images and measure area / aspect ratio.

Usage: python pipeline.py <input.tif> <labels.tif> <measurements.csv>

Steps (all parameters are constants below):
 1. Load 2D uint16 image (12-bit), validate.
 2. Normalise: the image is two 512-px-wide tiles with different offsets, so each
    tile is flat-fielded separately (subtract heavy Gaussian background, divide by
    local robust std), then clipped to [-4, 4] sigma.  Float32, no resampling.
 3. Cellpose-SAM (cpsam) on CPU at native resolution (diameter set so objects ~30 px).
 4. Post-process: fill holes; keep objects with high intensity contrast
    (cancer cells have a dark rim and bright halo, endothelial cells do not); trim thin leaks by
    opening; drop too small/large/low-solidity objects; relabel. Border-touching
    cells are kept but flagged in the table.
 5. Measure area (um^2) and aspect ratio (major/minor axis of fitted ellipse).
"""
import sys
import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from skimage import measure, morphology

PIXEL_SIZE_UM = 0.65
TILE_WIDTH_PX = 512            # stitched tiles: seam in intensity at x=512
BACKGROUND_SIGMA_PX = 40.0
CLIP_SIGMA = 4.0
CELLPOSE_DIAMETER_PX = 30.0    # ~19.5 um; cpsam default training diameter
FLOW_THRESHOLD = 0.4
CELLPROB_THRESHOLD = 0.0
MIN_DIAMETER_UM = 8.0          # equivalent diameter limits for a cancer cell
MAX_DIAMETER_UM = 40.0
MIN_SOLIDITY = 0.85
MIN_INTERIOR_STD = 1.0       # std of normalised intensity within a mask
OPEN_RADIUS_PX = 3             # trims thin leaks into the endothelium


def load_image(path: str) -> np.ndarray:
    img = tifffile.imread(path)
    if img.ndim != 2:
        raise ValueError(f"Expected 2D (Y, X) image, got shape {img.shape}")
    if img.dtype != np.uint16:
        raise ValueError(f"Expected uint16, got {img.dtype}")
    if img.max() > 4095:
        raise ValueError(f"Values exceed 12-bit range: max {img.max()}")
    return img


def flatten_tile(tile: np.ndarray) -> np.ndarray:
    background = ndi.gaussian_filter(tile, BACKGROUND_SIGMA_PX, mode="reflect")
    resid = tile - background
    mad = np.median(np.abs(resid - np.median(resid)))
    scale = 1.4826 * mad
    if scale <= 0:
        raise ValueError("Tile has zero contrast; cannot normalise")
    return np.clip(resid / scale, -CLIP_SIGMA * 3, CLIP_SIGMA * 3) / 3.0


def normalise(img: np.ndarray) -> np.ndarray:
    x = img.astype(np.float32)
    out = np.empty_like(x)
    for x0 in range(0, x.shape[1], TILE_WIDTH_PX):
        out[:, x0:x0 + TILE_WIDTH_PX] = flatten_tile(x[:, x0:x0 + TILE_WIDTH_PX])
    return out


def run_cellpose(norm: np.ndarray) -> np.ndarray:
    from cellpose import models
    model = models.CellposeModel(gpu=False, pretrained_model="cpsam")
    masks, _, _ = model.eval(
        norm, diameter=CELLPOSE_DIAMETER_PX, normalize=False,
        flow_threshold=FLOW_THRESHOLD, cellprob_threshold=CELLPROB_THRESHOLD,
        batch_size=4)
    return masks.astype(np.int32)


def trim_leaks(masks: np.ndarray) -> np.ndarray:
    """Morphological opening per object; keep the largest remaining component."""
    out = np.zeros_like(masks)
    footprint = morphology.disk(OPEN_RADIUS_PX)
    for r in measure.regionprops(masks):
        padded = np.pad(r.image, OPEN_RADIUS_PX + 1)
        opened = ndi.binary_opening(padded, structure=footprint)
        comp, n = ndi.label(opened)
        if n == 0:
            continue
        sizes = ndi.sum(opened, comp, range(1, n + 1))
        best = comp == (1 + int(np.argmax(sizes)))
        best = best[OPEN_RADIUS_PX + 1:-(OPEN_RADIUS_PX + 1),
                    OPEN_RADIUS_PX + 1:-(OPEN_RADIUS_PX + 1)]
        out[r.slice][best] = r.label
    return out


def filter_by_contrast(masks: np.ndarray, norm: np.ndarray) -> np.ndarray:
    """Keep cells with the strong dark-rim/bright-halo contrast of cancer cells.

    Measured as the std of the normalised intensity inside the mask: cancer cells
    >= ~1.5, endothelial cells and leaks into them <= ~0.7.
    """
    keep = [r.label for r in measure.regionprops(masks, intensity_image=norm)
            if r.image_intensity[r.image].std() >= MIN_INTERIOR_STD]
    return np.where(np.isin(masks, keep), masks, 0)


def filter_objects(masks: np.ndarray) -> np.ndarray:
    keep = np.zeros_like(masks)
    min_area = np.pi / 4 * (MIN_DIAMETER_UM / PIXEL_SIZE_UM) ** 2
    max_area = np.pi / 4 * (MAX_DIAMETER_UM / PIXEL_SIZE_UM) ** 2
    n = 0
    for r in measure.regionprops(masks):
        if not (min_area <= r.area <= max_area) or r.solidity < MIN_SOLIDITY:
            continue
        n += 1
        keep[masks == r.label] = n
    return keep


def fill_and_clean(masks: np.ndarray) -> np.ndarray:
    out = np.zeros_like(masks)
    for r in measure.regionprops(masks):
        sl = r.slice
        filled = ndi.binary_fill_holes(r.image)
        out[sl][filled & (out[sl] == 0)] = r.label
    return out


def measure_cells(labels: np.ndarray) -> pd.DataFrame:
    h, w = labels.shape
    rows = []
    for r in measure.regionprops(labels):
        y0, x0, y1, x1 = r.bbox
        rows.append(dict(
            label=r.label,
            area_um2=r.area * PIXEL_SIZE_UM ** 2,
            aspect_ratio=r.axis_major_length / r.axis_minor_length,
            centroid_y_um=r.centroid[0] * PIXEL_SIZE_UM,
            centroid_x_um=r.centroid[1] * PIXEL_SIZE_UM,
            touches_border=bool(y0 == 0 or x0 == 0 or y1 == h or x1 == w),
        ))
    return pd.DataFrame(rows, columns=["label", "area_um2", "aspect_ratio",
                                       "centroid_y_um", "centroid_x_um",
                                       "touches_border"])


def main(inp: str, out_labels: str, out_csv: str) -> None:
    img = load_image(inp)
    norm = normalise(img)
    masks = run_cellpose(norm)
    labels = filter_by_contrast(fill_and_clean(masks), norm)
    labels = filter_objects(trim_leaks(labels))
    tifffile.imwrite(out_labels, labels.astype(np.uint16))
    table = measure_cells(labels)
    table.to_csv(out_csv, index=False)
    print(f"{len(table)} cells; median area {table.area_um2.median():.0f} um2")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
