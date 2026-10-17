"""Segment DAPI nuclei in a 2D (Y, X) image with Cellpose 4 (CellposeModel, CPU)."""
import numpy as np
import tifffile
from cellpose import models
from skimage.segmentation import relabel_sequential
from skimage.measure import regionprops

PIXEL_SIZE_UM = 0.65
DIAMETER_UM = (13.0, 17.0)                         # expected nucleus diameter range
DIAMETER_PX = None                                 # None = native scale (20-26 px is within the trained range).
                                                   # Set e.g. 23 to make Cellpose rescale by 30/23 internally.
FLOW_THRESHOLD = 0.4                               # Cellpose default
CELLPROB_THRESHOLD = 0.0                           # Cellpose default
NORMALIZE = True                                   # per-image percentile normalisation inside Cellpose
MIN_AREA_UM2 = 30.0                                # post-filter: debris smaller than this is removed


def segment(img: np.ndarray, model=None) -> np.ndarray:
    """img: 2D (Y, X) array. Returns uint32 label image, same shape, 0 = background."""
    img = np.squeeze(img)
    if img.ndim != 2:
        raise ValueError(f"Expected a 2D (Y, X) image, got shape {img.shape}")
    if model is None:
        model = models.CellposeModel(gpu=False)    # default pretrained model; weights download on first use
    masks, _flows, _styles = model.eval(
        img,
        diameter=DIAMETER_PX,
        normalize=NORMALIZE,
        flow_threshold=FLOW_THRESHOLD,
        cellprob_threshold=CELLPROB_THRESHOLD,
        batch_size=8,
    )
    assert masks.shape == img.shape, "Cellpose output is not in the input coordinate system"

    # remove tiny objects (area in physical units), then relabel 1..N
    min_px = MIN_AREA_UM2 / PIXEL_SIZE_UM ** 2
    for r in regionprops(masks):
        if r.area < min_px:
            masks[masks == r.label] = 0
    masks, _, _ = relabel_sequential(masks)
    return masks.astype(np.uint32)


if __name__ == "__main__":
    img = tifffile.imread("dapi.tif")
    print("input shape", img.shape, "dtype", img.dtype, "min/max", img.min(), img.max())
    labels = segment(img)
    tifffile.imwrite("labels.tif", labels)
    areas_um2 = np.bincount(labels.ravel())[1:] * PIXEL_SIZE_UM ** 2
    print(f"{labels.max()} nuclei; median area {np.median(areas_um2):.1f} um^2 "
          f"(expected for 13-17 um: ~{np.pi*(DIAMETER_UM[0]/2)**2:.0f}-{np.pi*(DIAMETER_UM[1]/2)**2:.0f})")
