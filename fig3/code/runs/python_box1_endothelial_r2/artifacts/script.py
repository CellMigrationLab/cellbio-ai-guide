"""segment_endothelium.py -- 2D brightfield (Y, X) -> labels.tif using Cellpose 4 (CPU)."""
import numpy as np
import tifffile
from scipy import ndimage as ndi
from skimage import measure, segmentation

# ---------------- parameters ----------------
PIXEL_SIZE_UM = 0.65
DIAMETER_UM = 37.5          # midpoint of 25-50 um -> 57.7 px
FLATFIELD_SIGMA_UM = 100.0  # background estimate scale, much larger than a cell
FLOW_THRESHOLD = 0.4        # Cellpose default
CELLPROB_THRESHOLD = 0.0    # Cellpose default; lower -> more/larger masks
MIN_SIZE_PX = 15            # Cellpose default (tiny-mask removal)
# Post-hoc filter on equivalent diameter (um). Deliberately looser than 25-50 um
# so real cells are not clipped; it mainly removes small round cells and debris.
KEEP_DIAM_UM = (20.0, 70.0)


def flatten(img, sigma_px):
    """Divide by a heavy Gaussian blur to remove uneven illumination (float32)."""
    img = img.astype(np.float32)
    bg = ndi.gaussian_filter(img, sigma_px, mode="reflect")
    return img / np.maximum(bg, 1e-6)


def segment(img, model=None):
    """img: 2D (Y, X) array. Returns uint32 labels with the same (Y, X) shape."""
    if img.ndim != 2:
        raise ValueError(f"Expected 2D (Y, X) image, got shape {img.shape}")
    if model is None:
        from cellpose import models
        model = models.CellposeModel(gpu=False)  # default pretrained model of 4.2.1.1
        print("Cellpose model:", model)

    diameter_px = DIAMETER_UM / PIXEL_SIZE_UM
    x = flatten(img, FLATFIELD_SIGMA_UM / PIXEL_SIZE_UM)

    # Cellpose internally: per-image intensity normalisation (normalize=True),
    # rescale by 30/diameter_px (~0.52, i.e. downsample), run network, then
    # resample flows/masks back to the input size (resample=True).
    masks, _flows, _styles = model.eval(
        x,
        diameter=diameter_px,
        normalize=True,
        flow_threshold=FLOW_THRESHOLD,
        cellprob_threshold=CELLPROB_THRESHOLD,
        min_size=MIN_SIZE_PX,
    )
    assert masks.shape == img.shape, "Cellpose output not in original coordinates"

    # Size filter (um, via equivalent diameter), then relabel 1..N
    out = np.zeros(masks.shape, np.uint32)
    for r in measure.regionprops(masks):
        d_um = r.equivalent_diameter_area * PIXEL_SIZE_UM
        if KEEP_DIAM_UM[0] <= d_um <= KEEP_DIAM_UM[1]:
            out[masks == r.label] = r.label
    out, _, _ = segmentation.relabel_sequential(out)
    return out.astype(np.uint32)


if __name__ == "__main__":
    img = tifffile.imread("bf.tif")
    labels = segment(img)
    tifffile.imwrite("labels.tif", labels)
    print(f"{labels.max()} cells kept; labels.tif shape {labels.shape}")
