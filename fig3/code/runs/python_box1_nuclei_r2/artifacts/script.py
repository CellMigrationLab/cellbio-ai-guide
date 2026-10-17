"""Segment DAPI nuclei in a single 2D (Y, X) image with Cellpose-SAM (Cellpose 4.x).

Input : dapi.tif  (2D, Y X)
Output: labels.tif (uint16, same Y X shape; 0 = background)
        nuclei_measurements.csv (label, area_px, area_um2, centroid, touches_border)
"""
import sys
import numpy as np
import pandas as pd
import tifffile
from skimage.measure import regionprops_table
from skimage.segmentation import relabel_sequential
from cellpose import models

# ---- parameters -------------------------------------------------------------
PIXEL_SIZE_UM = 0.65
MIN_AREA_UM2 = 20.0          # reject debris; a 13 um nucleus is ~130 um2
FLOW_THRESHOLD = 0.4         # Cellpose default
CELLPROB_THRESHOLD = 0.0     # Cellpose default
DIAMETER = None              # None = no rescaling (nuclei ~20-26 px, within training range)
NORMALIZE = True             # Cellpose default per-image percentile normalisation
USE_GPU = False              # CPU only


def load_2d(path):
    img = tifffile.imread(path)
    img = np.squeeze(img)
    if img.ndim != 2:
        raise ValueError(f"Expected a 2D (Y, X) image, got shape {img.shape}")
    return img


def segment(img, model=None):
    """Return int32 label image with the same (Y, X) shape as img."""
    if model is None:
        model = models.CellposeModel(gpu=USE_GPU)
    # float32 copy only; no manual resizing or rescaling of intensities here.
    masks, flows, styles = model.eval(
        img.astype(np.float32),
        diameter=DIAMETER,
        normalize=NORMALIZE,
        flow_threshold=FLOW_THRESHOLD,
        cellprob_threshold=CELLPROB_THRESHOLD,
    )
    masks = np.asarray(masks)
    assert masks.shape == img.shape, (masks.shape, img.shape)

    # Remove small debris by physical area, then relabel 1..N
    min_px = MIN_AREA_UM2 / PIXEL_SIZE_UM ** 2
    areas = np.bincount(masks.ravel())
    small = np.where(areas < min_px)[0]
    small = small[small != 0]
    masks = masks.copy()
    masks[np.isin(masks, small)] = 0
    masks, _, _ = relabel_sequential(masks)
    return masks.astype(np.int32)


def measure(labels):
    props = pd.DataFrame(regionprops_table(
        labels, properties=("label", "area", "centroid", "bbox")))
    h, w = labels.shape
    props["touches_border"] = (
        (props["bbox-0"] == 0) | (props["bbox-1"] == 0) |
        (props["bbox-2"] == h) | (props["bbox-3"] == w))
    props = props.rename(columns={"area": "area_px",
                                  "centroid-0": "centroid_y_px",
                                  "centroid-1": "centroid_x_px"})
    props["area_um2"] = props["area_px"] * PIXEL_SIZE_UM ** 2
    return props.drop(columns=["bbox-0", "bbox-1", "bbox-2", "bbox-3"])


def main(in_path="dapi.tif", out_path="labels.tif"):
    img = load_2d(in_path)
    model = models.CellposeModel(gpu=USE_GPU)
    print("pretrained model:", getattr(model, "pretrained_model", "unknown"))
    labels = segment(img, model)
    tifffile.imwrite(out_path, labels.astype(np.uint16))
    df = measure(labels)
    df.to_csv("nuclei_measurements.csv", index=False)
    print(f"{labels.max()} nuclei; median area {df.area_um2.median():.1f} um2 "
          f"({df.touches_border.sum()} touch the border)")


if __name__ == "__main__":
    main(*sys.argv[1:3])
