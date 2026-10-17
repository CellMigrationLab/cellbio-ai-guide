# segment.py
import numpy as np
import tifffile
from skimage.measure import regionprops
from skimage.segmentation import relabel_sequential
from cellpose import models

PIXEL_SIZE_UM = 0.65
CELL_DIAMETER_UM = 37.5            # midpoint of the 25-50 um range
DIAMETER_PX = CELL_DIAMETER_UM / PIXEL_SIZE_UM   # ~57.7 px; Cellpose rescales so cells ~30 px
FLOW_THRESHOLD = 0.4               # Cellpose default
CELLPROB_THRESHOLD = 0.0           # Cellpose default
MIN_AREA_UM2 = 100.0               # my post-filter; not a Cellpose parameter


def segment(img_yx: np.ndarray) -> np.ndarray:
    """img_yx: 2D (Y, X) array. Returns uint32 labels with the same (Y, X) shape."""
    assert img_yx.ndim == 2, f"expected (Y, X), got {img_yx.shape}"
    img = img_yx.astype(np.float32)    # no other preprocessing; Cellpose normalises (1-99 percentile)
    model = models.CellposeModel(gpu=False)          # default pretrained model (cpsam)
    masks, _flows, _styles = model.eval(
        img,
        diameter=DIAMETER_PX,
        flow_threshold=FLOW_THRESHOLD,
        cellprob_threshold=CELLPROB_THRESHOLD,
        normalize=True,                # default
    )
    assert masks.shape == img_yx.shape, "labels must be in the original coordinate system"

    # remove labels below the minimum area, then relabel 1..N
    min_px = MIN_AREA_UM2 / PIXEL_SIZE_UM ** 2
    out = masks.astype(np.int64)
    for r in regionprops(out):
        if r.area < min_px:
            out[out == r.label] = 0
    out, _, _ = relabel_sequential(out)
    return out.astype(np.uint32)


if __name__ == "__main__":
    img = tifffile.imread("bf.tif")
    labels = segment(img)
    tifffile.imwrite("labels.tif", labels)
    areas_um2 = np.bincount(labels.ravel())[1:] * PIXEL_SIZE_UM ** 2
    print(f"{labels.max()} objects; median area {np.median(areas_um2):.0f} um^2")
