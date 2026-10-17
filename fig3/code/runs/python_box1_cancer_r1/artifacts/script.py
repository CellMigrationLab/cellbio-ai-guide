"""Segment cancer cells in a single-channel 2D brightfield image (Y, X) with Cellpose-SAM.

Input : bf.tif  (2D, axes Y,X)
Output: labels.tif (int32, same Y,X shape as input, 0 = background)

Parameters and transformations (all stated here on purpose):
  * Pixel size 0.65 um/px. Expected cell diameter 15-25 um = ~23-38 px,
    near the ~30 px scale Cellpose works at, so NO diameter is passed
    (diameter=None) and NO resizing is done by this script.
  * Cellpose-SAM tiles internally (bsize 256, tile_overlap 0.1) and returns masks
    at the input resolution, so labels are already in the original Y,X frame.
  * Normalisation: cellpose's own per-image percentile normalisation (1st-99th
    percentile -> 0-1). I only cast the image to float32; no other scaling.
  * flow_threshold=0.4, cellprob_threshold=0.0 (documented defaults).
  * Post-filter (mine, not Cellpose): remove objects whose equivalent diameter is
    outside [MIN_DIAM_UM, MAX_DIAM_UM]; labels are then renumbered 1..N.
"""
import numpy as np
import tifffile
from skimage.measure import regionprops
from skimage.segmentation import relabel_sequential
from cellpose import models

PIXEL_UM = 0.65
MIN_DIAM_UM = 8.0    # below this: debris / fragments (cells are 15-25 um)
MAX_DIAM_UM = 40.0   # above this: merged clusters or flat background cells
FLOW_THRESHOLD = 0.4
CELLPROB_THRESHOLD = 0.0


def load_image(path):
    img = np.squeeze(tifffile.imread(path))
    if img.ndim != 2:
        raise ValueError(f"Expected a 2D Y,X image, got shape {img.shape}")
    return img.astype(np.float32)  # only a dtype cast; cellpose normalises


def size_filter(labels, pixel_um=PIXEL_UM, min_d=MIN_DIAM_UM, max_d=MAX_DIAM_UM):
    min_area = np.pi * (min_d / 2 / pixel_um) ** 2
    max_area = np.pi * (max_d / 2 / pixel_um) ** 2
    out = labels.copy()
    for r in regionprops(labels):
        if r.area < min_area or r.area > max_area:
            out[labels == r.label] = 0
    out, _, _ = relabel_sequential(out)
    return out.astype(np.int32)


def segment(img, model=None):
    """img: 2D float array (Y, X). Returns int32 labels with the same shape."""
    if model is None:
        model = models.CellposeModel(gpu=False)  # default pretrained 'cpsam_v2'
    masks, flows, styles = model.eval(
        img,
        diameter=None,                          # no rescaling; model is size-invariant
        normalize={"percentile": [1, 99]},      # per-image 1-99 percentile normalisation
        flow_threshold=FLOW_THRESHOLD,
        cellprob_threshold=CELLPROB_THRESHOLD,
    )
    assert masks.shape == img.shape, "mask not in original coordinate system"
    return size_filter(masks)


if __name__ == "__main__":
    image = load_image("bf.tif")
    labels = segment(image)
    tifffile.imwrite("labels.tif", labels)
    areas = np.bincount(labels.ravel())[1:] * PIXEL_UM ** 2
    print(f"{labels.max()} cells; median area {np.median(areas):.0f} um^2")
