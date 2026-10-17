"""Segment endothelial nuclei in a DAPI widefield image and measure area and aspect ratio.

Input : image.tif (Y, X), uint16 with 12-bit values, 0.65 um/pixel
Output: labels.tif            endothelial nuclei only, 0 = background
        measurements.csv      label, area_um2, aspect_ratio, touches_border
        all_objects_labels.tif / all_objects.csv   every segmented object, for QC and tuning
        overlay.png           green = kept endothelial, red = rejected (bright / small)
"""
from __future__ import annotations

import logging
from importlib.metadata import version
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile
from skimage import measure, segmentation, io as skio

PIXEL_SIZE_UM = 0.65
MAX_12BIT = 4095
EXPECTED_DIAMETER_UM = (13.0, 17.0)

# Cellpose settings (diameter=None: no rescaling, the model is used at native resolution).
FLOW_THRESHOLD = 0.4
CELLPROB_THRESHOLD = 0.0
BATCH_SIZE = 8

# Object filters. CANCER_INTENSITY_RATIO_MAX is an UNVALIDATED starting value: tune on your annotation.
CANCER_INTENSITY_RATIO_MAX = 2.0   # object mean intensity / median object mean intensity
MIN_AREA_UM2 = 30.0                # removes debris / fragments

IMAGE_PATH = Path("image.tif")

log = logging.getLogger("nuclei")


def load_image(path: Path) -> np.ndarray:
    if not path.exists():
        raise FileNotFoundError(f"{path} not found in {Path.cwd()}")
    image = tifffile.imread(path)
    if image.ndim != 2:
        raise ValueError(f"Expected a 2D (Y, X) image, got shape {image.shape}")
    if image.dtype != np.uint16:
        raise ValueError(f"Expected uint16, got {image.dtype}")
    if image.max() > MAX_12BIT:
        raise ValueError(f"Max value {image.max()} exceeds 12-bit range ({MAX_12BIT}); check the data")
    log.info("Image %s, intensity range %d-%d, %d saturated px",
             image.shape, image.min(), image.max(), int((image == MAX_12BIT).sum()))
    return image


def segment_all_nuclei(image: np.ndarray) -> np.ndarray:
    """Cellpose-SAM instance segmentation of every nucleus (endothelial and cancer)."""
    from cellpose import models

    major = int(version("cellpose").split(".")[0])
    if major < 4:
        raise RuntimeError(f"Cellpose >= 4 (Cellpose-SAM) required, found {version('cellpose')}")
    model = models.CellposeModel(gpu=False)
    masks, _, _ = model.eval(
        image.astype(np.float32),
        diameter=None,
        flow_threshold=FLOW_THRESHOLD,
        cellprob_threshold=CELLPROB_THRESHOLD,
        batch_size=BATCH_SIZE,
    )
    if masks.max() == 0:
        raise RuntimeError("Cellpose found no objects")
    log.info("Cellpose found %d objects", int(masks.max()))
    return masks.astype(np.int32)


def object_table(labels: np.ndarray, image: np.ndarray) -> pd.DataFrame:
    """Per-object area, mean intensity and intensity ratio to the population median."""
    table = pd.DataFrame(measure.regionprops_table(
        labels, intensity_image=image, properties=("label", "area", "mean_intensity")))
    table["area_um2"] = table["area"] * PIXEL_SIZE_UM**2
    table["mean_intensity_ratio"] = table["mean_intensity"] / table["mean_intensity"].median()
    return table


def flag_endothelial(table: pd.DataFrame) -> pd.DataFrame:
    table = table.copy()
    table["too_bright"] = table["mean_intensity_ratio"] > CANCER_INTENSITY_RATIO_MAX
    table["too_small"] = table["area_um2"] < MIN_AREA_UM2
    table["kept"] = ~(table["too_bright"] | table["too_small"])
    log.info("Kept %d; rejected %d too bright (cancer?), %d too small",
             int(table["kept"].sum()), int(table["too_bright"].sum()), int(table["too_small"].sum()))
    if not table["kept"].any():
        raise RuntimeError("All objects were rejected; check the filter parameters")
    return table


def keep_labels(labels: np.ndarray, kept_ids: np.ndarray) -> np.ndarray:
    filtered = np.where(np.isin(labels, kept_ids), labels, 0)
    relabelled, _, _ = segmentation.relabel_sequential(filtered)
    return relabelled.astype(np.int32)


def measure_shape(labels: np.ndarray) -> pd.DataFrame:
    rows = []
    for region in measure.regionprops(labels):
        if region.minor_axis_length == 0:
            raise ValueError(f"Label {region.label} has zero minor axis; cannot compute aspect ratio")
        min_r, min_c, max_r, max_c = region.bbox
        rows.append({
            "label": region.label,
            "area_um2": region.area * PIXEL_SIZE_UM**2,
            "aspect_ratio": region.major_axis_length / region.minor_axis_length,
            "touches_border": min_r == 0 or min_c == 0
                              or max_r == labels.shape[0] or max_c == labels.shape[1],
        })
    return pd.DataFrame(rows)


def check_plausibility(measurements: pd.DataFrame) -> None:
    """Warn (never silently adjust) if object size disagrees with the expected 13-17 um."""
    equivalent_diameter = 2 * np.sqrt(measurements["area_um2"] / np.pi)
    median = float(equivalent_diameter.median())
    log.info("Median equivalent diameter %.1f um (expected size %s um, probably the long axis)",
             median, EXPECTED_DIAMETER_UM)
    if not 0.5 * EXPECTED_DIAMETER_UM[0] <= median <= 1.5 * EXPECTED_DIAMETER_UM[1]:
        log.warning("Median diameter is far from the expected range; segmentation is suspect")


def save_overlay(image: np.ndarray, all_labels: np.ndarray, kept: np.ndarray, path: Path) -> None:
    base = np.clip(image / np.percentile(image, 99.5), 0, 1)
    rgb = np.dstack([base] * 3)
    boundaries = segmentation.find_boundaries(all_labels, mode="inner")
    is_kept = np.isin(all_labels, kept)
    rgb[boundaries & is_kept] = (0, 1, 0)
    rgb[boundaries & ~is_kept & (all_labels > 0)] = (1, 0, 0)
    skio.imsave(path, (rgb * 255).astype(np.uint8), check_contrast=False)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    image = load_image(IMAGE_PATH)
    all_labels = segment_all_nuclei(image)
    flags = flag_endothelial(object_table(all_labels, image))

    labels = keep_labels(all_labels, flags.loc[flags["kept"], "label"].to_numpy())
    measurements = measure_shape(labels)
    check_plausibility(measurements)

    tifffile.imwrite("all_objects_labels.tif", all_labels)
    flags[["label", "area_um2", "mean_intensity_ratio", "too_bright", "too_small", "kept"]] \
        .to_csv("all_objects.csv", index=False)
    tifffile.imwrite("labels.tif", labels)
    measurements.to_csv("measurements.csv", index=False)
    save_overlay(image, all_labels, flags.loc[flags["kept"], "label"].to_numpy(), Path("overlay.png"))
    log.info("Endothelial nuclei: %d (%d touch the border)",
             len(measurements), int(measurements["touches_border"].sum()))


if __name__ == "__main__":
    main()
