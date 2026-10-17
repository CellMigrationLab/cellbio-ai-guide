"""Segment endothelial cells in a single-channel 2D brightfield image (Y, X).
Cellpose 4.x (CellposeModel, CPU). Reads bf.tif, writes labels.tif."""
import numpy as np
import tifffile
from scipy import ndimage as ndi
from skimage import measure, segmentation
from cellpose import models

PIXEL_UM = 0.65
DIAMETER_PX = 58.0          # ~37.5 um mean of the 25-50 um range
MIN_AREA_UM2 = 200.0        # drop debris and small round cells (assumption)
BG_SIGMA_PX = 100.0         # background flattening scale
FLOW_THRESHOLD = 0.4        # Cellpose default
CELLPROB_THRESHOLD = 0.0    # Cellpose default


def segment(img):
    if img.ndim != 2:
        raise ValueError(f"Expected 2D (Y, X) image, got shape {img.shape}")
    x = img.astype(np.float32)
    x = x - ndi.gaussian_filter(x, BG_SIGMA_PX, mode="reflect")  # flatten illumination

    model = models.CellposeModel(gpu=False)
    masks, flows, styles = model.eval(
        x,
        diameter=DIAMETER_PX,
        normalize=True,                 # Cellpose default percentile normalisation
        flow_threshold=FLOW_THRESHOLD,
        cellprob_threshold=CELLPROB_THRESHOLD,
        do_3D=False,
    )
    if masks.shape != img.shape:
        raise RuntimeError(f"Mask shape {masks.shape} != image shape {img.shape}")

    # area filter, then consecutive relabelling
    min_px = MIN_AREA_UM2 / PIXEL_UM**2
    areas = np.bincount(masks.ravel())
    keep = areas >= min_px
    keep[0] = False
    masks = np.where(keep[masks], masks, 0)
    masks, _, _ = segmentation.relabel_sequential(masks)
    return masks.astype(np.uint32)


if __name__ == "__main__":
    img = tifffile.imread("bf.tif")
    labels = segment(img)
    tifffile.imwrite("labels.tif", labels)
    areas_um2 = np.array([r.area for r in measure.regionprops(labels)]) * PIXEL_UM**2
    print(f"{labels.max()} cells; median area {np.median(areas_um2):.0f} um^2")
