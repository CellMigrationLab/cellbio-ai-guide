# segment_nuclei.py
import numpy as np
import tifffile
from cellpose import models

PIXEL_SIZE_UM = 0.65
# Expected nucleus diameter 13-17 um -> ~20-26 px (mean ~23 px).
# diameter=None: no resizing; native scale is within cpsam's training range (7.5-120 px).
DIAMETER = None
FLOW_THRESHOLD = 0.4       # Cellpose default
CELLPROB_THRESHOLD = 0.0   # Cellpose default
MIN_SIZE_PX = 15           # Cellpose default (very permissive; see assumptions)


def segment(image, model=None):
    """image: 2D array (Y, X). Returns uint32 label image, same shape, 0 = background."""
    if image.ndim != 2:
        raise ValueError(f"Expected 2D (Y, X) image, got shape {image.shape}")
    if model is None:
        model = models.CellposeModel(gpu=False)  # default pretrained model: cpsam
    masks, flows, styles = model.eval(
        image,
        diameter=DIAMETER,
        normalize=True,              # per-image 1st-99th percentile -> 0-1
        flow_threshold=FLOW_THRESHOLD,
        cellprob_threshold=CELLPROB_THRESHOLD,
        min_size=MIN_SIZE_PX,
        batch_size=8,
        resample=True,               # dynamics at original resolution
    )
    masks = np.asarray(masks)
    assert masks.shape == image.shape, "labels must match input shape"
    return masks.astype(np.uint32)


if __name__ == "__main__":
    img = tifffile.imread("dapi.tif")
    print("input", img.shape, img.dtype, "min/max", img.min(), img.max())
    labels = segment(img)
    n = int(labels.max())
    print(f"{n} nuclei; median area "
          f"{np.median(np.bincount(labels.ravel())[1:]) * PIXEL_SIZE_UM**2:.1f} um^2")
    tifffile.imwrite("labels.tif", labels)
