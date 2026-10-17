# segment_cancer.py
"""Segment cancer cells in a single-channel 2D brightfield image (Y, X).

Library: Cellpose 4.x (cpsam), CPU.
Parameters that matter:
  - diameter=None        -> NO resizing; cells expected ~23-38 px (15-25 um / 0.65), model mean is 30 px
  - normalize=True       -> Cellpose default: per-image 1st-99th percentile rescale (internal only)
  - flow_threshold=0.4, cellprob_threshold=0.0 (Cellpose defaults, set explicitly)
  - resample=True        -> dynamics run at higher resolution; masks returned at input size
  - min_size=15 px       -> Cellpose default, drops tiny masks
  - post-filter: equivalent diameter must lie in [MIN_DIAM_UM, MAX_DIAM_UM]
Output: uint32 label image, same (Y, X) shape as input, 0 = background.
"""
import sys
import numpy as np
import tifffile
from skimage.measure import regionprops
from cellpose import models

PIXEL_UM = 0.65
MIN_DIAM_UM = 10.0   # wider than 15-25 um on purpose; tighten after inspecting overlays
MAX_DIAM_UM = 35.0
FLOW_THRESHOLD = 0.4
CELLPROB_THRESHOLD = 0.0


def load_image(path):
    img = np.squeeze(tifffile.imread(path))
    if img.ndim != 2:
        raise ValueError(f"Expected a single-channel 2D (Y, X) image, got shape {img.shape}")
    return img.astype(np.float32)  # dtype cast only; no intensity rescaling here


def filter_by_size(labels, pixel_um=PIXEL_UM, min_d=MIN_DIAM_UM, max_d=MAX_DIAM_UM):
    """Drop objects whose equivalent diameter (um) is outside [min_d, max_d]; relabel 1..N."""
    out = np.zeros(labels.shape, dtype=np.uint32)
    new_id = 0
    for rp in regionprops(labels):
        d_um = rp.equivalent_diameter_area * pixel_um
        if min_d <= d_um <= max_d:
            new_id += 1
            out[labels == rp.label] = new_id
    return out


def segment(img, model=None):
    if model is None:
        model = models.CellposeModel(gpu=False)
    masks, _flows, _styles = model.eval(
        img,
        diameter=None,
        normalize=True,
        flow_threshold=FLOW_THRESHOLD,
        cellprob_threshold=CELLPROB_THRESHOLD,
        resample=True,
        min_size=15,
    )
    assert masks.shape == img.shape, "mask shape must equal input shape"
    return filter_by_size(masks.astype(np.uint32))


if __name__ == "__main__":
    in_path = sys.argv[1] if len(sys.argv) > 1 else "bf.tif"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "labels.tif"
    image = load_image(in_path)
    labels = segment(image)
    tifffile.imwrite(out_path, labels)
    areas_um2 = np.bincount(labels.ravel())[1:] * PIXEL_UM ** 2
    print(f"{labels.max()} cells; median area {np.median(areas_um2):.0f} um^2" if labels.max()
          else "0 cells found")
