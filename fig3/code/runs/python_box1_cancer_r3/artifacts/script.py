# segment.py  -- cancer cell segmentation from 2D brightfield (Y, X)
import numpy as np
import tifffile
from scipy import ndimage as ndi
from skimage.measure import regionprops
from skimage.segmentation import relabel_sequential
from cellpose import models

PIXEL_UM = 0.65
DIAMETER_UM = (10.0, 30.0)   # accepted equivalent diameter (expected 15-25 um, with margin)
MIN_SOLIDITY = 0.85          # heuristic to drop ragged debris; adjust on real data
FLATFIELD = False            # optional background subtraction before Cellpose
FLATFIELD_SIGMA_PX = 50


def run_cellpose(img):
    """img: 2D (Y, X) array. Returns int label image of the same shape."""
    img = img.astype(np.float32)
    if FLATFIELD:
        img = img - ndi.gaussian_filter(img, FLATFIELD_SIGMA_PX)
    model = models.CellposeModel(gpu=False)  # default pretrained weights of the installed version
    masks, flows, styles = model.eval(
        img,
        diameter=None,            # no rescaling; 15-25 um = 23-38 px, close to 30 px training mean
        normalize=True,           # per-image 1-99 percentile scaling (Cellpose default)
        flow_threshold=0.4,
        cellprob_threshold=0.0,
        min_size=15,
        batch_size=8,
    )
    return masks


def filter_cells(masks, pixel_um=PIXEL_UM, d_um=DIAMETER_UM, min_solidity=MIN_SOLIDITY):
    area_lo = np.pi / 4 * (d_um[0] / pixel_um) ** 2
    area_hi = np.pi / 4 * (d_um[1] / pixel_um) ** 2
    keep = np.zeros(masks.max() + 1, dtype=bool)
    for r in regionprops(masks):
        if area_lo <= r.area <= area_hi and r.solidity >= min_solidity:
            keep[r.label] = True
    out = np.where(keep[masks], masks, 0)
    out, _, _ = relabel_sequential(out)
    dtype = np.uint16 if out.max() < 65535 else np.uint32
    return out.astype(dtype)


def segment(img):
    return filter_cells(run_cellpose(np.asarray(img)))


if __name__ == "__main__":
    img = tifffile.imread("bf.tif")
    if img.ndim != 2:
        raise ValueError(f"Expected 2D (Y, X) image, got shape {img.shape}")
    labels = segment(img)
    assert labels.shape == img.shape
    tifffile.imwrite("labels.tif", labels)
    areas_um2 = np.bincount(labels.ravel())[1:] * PIXEL_UM ** 2
    print(f"{labels.max()} cells; median area {np.median(areas_um2):.0f} um^2")
