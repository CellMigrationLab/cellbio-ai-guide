"""Segment DAPI-stained endothelial nuclei (2D widefield) with Cellpose-SAM and measure areas.

Input : dapi.tif  (2D, Y x X, uint16, 12-bit values, single DAPI channel)
Output: labels.tif          label image (uint32), 0 = background, 1..N = nuclei
        nuclei_table.csv    one row per nucleus, area in um^2 plus QC flags
        overlay.tif         RGB overlay (contours on contrast-stretched DAPI) for visual QC

Processing (all explicit):
  1. Read the image; require 2D (a singleton channel axis is removed, nothing else).
  2. Convert to float32 WITHOUT rescaling the values.
  3. Cellpose-SAM (Cellpose 4), CPU, diameter=None (no resizing), per-image
     1st-99th percentile normalisation, flow_threshold=0.4, cellprob_threshold=0.0.
  4. No objects are deleted after Cellpose. Border-touching, small/large and
     very bright objects are FLAGGED in the table so the analyst decides.
  Labels are on the original pixel grid; areas are converted to um^2 with PIXEL_SIZE_UM.
"""
from importlib.metadata import version
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile
from skimage.measure import regionprops_table
from skimage.segmentation import find_boundaries

# ----------------------------- parameters ---------------------------------
INPUT_PATH = Path("dapi.tif")
LABELS_PATH = Path("labels.tif")
TABLE_PATH = Path("nuclei_table.csv")
OVERLAY_PATH = Path("overlay.tif")

PIXEL_SIZE_UM = 0.65            # um per pixel (user supplied, not read from file)
EXPECTED_DIAMETER_UM = (13.0, 17.0)
NORMALISE_PERCENTILES = (1.0, 99.0)
FLOW_THRESHOLD = 0.4            # Cellpose default
CELLPROB_THRESHOLD = 0.0        # Cellpose default
MAX_12BIT_VALUE = 4095          # expected maximum of 12-bit data
BRIGHT_FACTOR = 3.0             # flag nuclei whose mean intensity > factor * median of all
# Area range (um^2) used only for flagging: circle area of the expected diameters,
# widened by a factor 2 either way to allow for elongated nuclei.
AREA_FLAG_FACTOR = 2.0


# ----------------------------- input --------------------------------------
def read_dapi(path: Path) -> np.ndarray:
    """Read the DAPI image and return a 2D (Y, X) array, validating shape and dtype."""
    if not path.is_file():
        raise FileNotFoundError(f"Input image not found: {path.resolve()}")
    image = tifffile.imread(path)
    if image.dtype != np.uint16:
        raise ValueError(f"Expected uint16 data, got {image.dtype}.")
    squeezed = np.squeeze(image)  # removes only length-1 axes (e.g. a single channel)
    if squeezed.ndim != 2:
        raise ValueError(
            f"Expected a 2D single-channel image (Y, X); got shape {image.shape}."
        )
    if squeezed.max() == 0:
        raise ValueError("Image is completely empty (all zeros).")
    return squeezed


def report_intensity_range(image: np.ndarray) -> None:
    """Print intensity statistics and warn if values exceed the 12-bit range."""
    print(f"Image shape (Y, X): {image.shape}, min {image.min()}, "
          f"max {image.max()}, 99.9th pct {np.percentile(image, 99.9):.0f}")
    if image.max() > MAX_12BIT_VALUE:
        print(f"WARNING: values exceed {MAX_12BIT_VALUE}; data are not 12-bit as stated.")
    saturated = np.mean(image >= image.max())
    print(f"Fraction of pixels at the image maximum: {saturated:.2e}")


# ----------------------------- segmentation -------------------------------
def segment_nuclei(image: np.ndarray) -> np.ndarray:
    """Run Cellpose-SAM on a 2D image and return a label image (uint32)."""
    from cellpose import models  # imported here so that read errors surface first

    print(f"Cellpose version: {version('cellpose')}")
    model = models.CellposeModel(gpu=False)
    masks, _flows, _styles = model.eval(
        image.astype(np.float32),                     # values unchanged, no rescaling
        diameter=None,                                # no resizing; model is size-tolerant
        normalize={"percentile": list(NORMALISE_PERCENTILES)},
        flow_threshold=FLOW_THRESHOLD,
        cellprob_threshold=CELLPROB_THRESHOLD,
    )
    masks = np.asarray(masks)
    if masks.shape != image.shape:
        raise RuntimeError(f"Mask shape {masks.shape} differs from image {image.shape}.")
    if masks.max() == 0:
        raise RuntimeError("Cellpose found no nuclei; check the image and thresholds.")
    return masks.astype(np.uint32)


# ----------------------------- measurement --------------------------------
def measure_nuclei(labels: np.ndarray, image: np.ndarray) -> pd.DataFrame:
    """Return a table of per-nucleus area (um^2), shape and intensity, with QC flags."""
    props = pd.DataFrame(regionprops_table(
        labels, intensity_image=image,
        properties=("label", "area", "centroid", "eccentricity", "solidity",
                    "bbox", "intensity_mean", "intensity_max"),
    ))
    height, width = labels.shape
    props["touches_border"] = (
        (props["bbox-0"] == 0) | (props["bbox-1"] == 0)
        | (props["bbox-2"] == height) | (props["bbox-3"] == width)
    )
    props = props.drop(columns=[c for c in props.columns if c.startswith("bbox-")])

    props["area_um2"] = props["area"] * PIXEL_SIZE_UM ** 2
    min_d, max_d = EXPECTED_DIAMETER_UM
    circle_min = np.pi * (min_d / 2) ** 2
    circle_max = np.pi * (max_d / 2) ** 2
    props["flag_small"] = props["area_um2"] < circle_min / AREA_FLAG_FACTOR
    props["flag_large"] = props["area_um2"] > circle_max * AREA_FLAG_FACTOR
    props["flag_bright"] = props["intensity_mean"] > BRIGHT_FACTOR * props["intensity_mean"].median()
    props = props.rename(columns={
        "area": "area_px", "centroid-0": "centroid_y_px", "centroid-1": "centroid_x_px",
    })
    return props


def make_overlay(image: np.ndarray, labels: np.ndarray) -> np.ndarray:
    """RGB uint8 overlay: gamma-stretched DAPI (1-99.8 pct) with label boundaries in red."""
    low, high = np.percentile(image, (1, 99.8))
    stretched = np.clip((image.astype(np.float32) - low) / (high - low), 0, 1) ** 0.6
    rgb = np.stack([stretched] * 3, axis=-1)
    rgb[find_boundaries(labels, mode="inner")] = (1.0, 0.0, 0.0)
    return (rgb * 255).astype(np.uint8)


# ----------------------------- main ---------------------------------------
def main() -> None:
    image = read_dapi(INPUT_PATH)
    report_intensity_range(image)

    labels = segment_nuclei(image)
    table = measure_nuclei(labels, image)

    tifffile.imwrite(LABELS_PATH, labels)
    table.to_csv(TABLE_PATH, index=False)
    tifffile.imwrite(OVERLAY_PATH, make_overlay(image, labels), photometric="rgb")

    print(f"Nuclei found: {len(table)}")
    print(f"Median area: {table['area_um2'].median():.1f} um^2 "
          f"(expected for 13-17 um circles: "
          f"{np.pi * (EXPECTED_DIAMETER_UM[0] / 2) ** 2:.0f}-"
          f"{np.pi * (EXPECTED_DIAMETER_UM[1] / 2) ** 2:.0f} um^2)")
    for flag in ("touches_border", "flag_small", "flag_large", "flag_bright"):
        print(f"  {flag}: {int(table[flag].sum())}")
    print(f"Saved {LABELS_PATH}, {TABLE_PATH}, {OVERLAY_PATH}")


if __name__ == "__main__":
    main()
