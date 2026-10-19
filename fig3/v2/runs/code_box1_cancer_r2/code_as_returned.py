"""Segment cancer cells in a side-by-side pair of 2D brightfield fields; measure area and aspect ratio.

Input : image.tif (2D, uint16, 12-bit; left half = field 1, right half = field 2)
Output: labels.tif (complete cells only), labels_with_border_objects.tif,
        measurements.csv, normalised.tif, overlay.png
"""
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from skimage import io as skio
from skimage import measure, segmentation

INPUT_PATH = Path("image.tif")
LABELS_PATH = Path("labels.tif")
LABELS_WITH_BORDER_PATH = Path("labels_with_border_objects.tif")
TABLE_PATH = Path("measurements.csv")
NORMALISED_PATH = Path("normalised.tif")
OVERLAY_PATH = Path("overlay.png")

PIXEL_SIZE_UM = 0.65
MAX_12BIT_VALUE = 4095
N_FIELDS = 2                 # fields placed side by side, equal width
LOCAL_NORM_SIGMA_PX = 40.0   # ~26 um; applied within each field only
LOCAL_NORM_EPS = 1e-3        # avoids division by ~0 in flat regions (image scaled to 0-1)
FLOW_THRESHOLD = 0.4         # Cellpose default
CELLPROB_THRESHOLD = 0.0     # Cellpose default
MIN_AREA_UM2 = 80.0          # ~10 um diameter; removes debris (expected cells: 15-25 um)


def load_image(path: Path) -> np.ndarray:
    """Read and validate a 2D uint16 12-bit image."""
    if not path.exists():
        raise FileNotFoundError(f"{path.resolve()} not found")
    image = tifffile.imread(path)
    if image.ndim != 2:
        raise ValueError(f"Expected 2D (Y, X) image, got shape {image.shape}")
    if image.dtype != np.uint16:
        raise ValueError(f"Expected uint16, got {image.dtype}")
    if image.max() > MAX_12BIT_VALUE:
        raise ValueError(f"Max value {image.max()} exceeds 12-bit range ({MAX_12BIT_VALUE})")
    return image


def field_slices(width: int) -> list[slice]:
    """Column slices of the side-by-side fields."""
    if width % N_FIELDS != 0:
        raise ValueError(f"Width {width} is not divisible into {N_FIELDS} equal fields")
    step = width // N_FIELDS
    return [slice(i * step, (i + 1) * step) for i in range(N_FIELDS)]


def local_normalise(field: np.ndarray) -> np.ndarray:
    """Scale to 0-1, then subtract local mean and divide by local std (Gaussian window)."""
    scaled = field.astype(np.float32) / MAX_12BIT_VALUE
    mean = ndi.gaussian_filter(scaled, LOCAL_NORM_SIGMA_PX)
    variance = ndi.gaussian_filter((scaled - mean) ** 2, LOCAL_NORM_SIGMA_PX)
    return ((scaled - mean) / (np.sqrt(variance) + LOCAL_NORM_EPS)).astype(np.float32)


def segment_field(model, normalised: np.ndarray) -> np.ndarray:
    """Instance segmentation of one field with Cellpose-SAM. No rescaling (diameter=None)."""
    masks, _, _ = model.eval(
        normalised,
        diameter=None,
        flow_threshold=FLOW_THRESHOLD,
        cellprob_threshold=CELLPROB_THRESHOLD,
    )
    if masks.shape != normalised.shape:
        raise RuntimeError(f"Mask shape {masks.shape} != field shape {normalised.shape}")
    return masks.astype(np.int32)


def normalise_and_segment(image: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Process each field independently; return (normalised image, merged labels)."""
    import cellpose
    from cellpose import models

    print(f"cellpose version: {getattr(cellpose, '__version__', 'unknown')}")
    model = models.CellposeModel(gpu=False)
    normalised = np.zeros(image.shape, dtype=np.float32)
    labels = np.zeros(image.shape, dtype=np.int32)
    offset = 0
    for index, columns in enumerate(field_slices(image.shape[1])):
        normalised[:, columns] = local_normalise(image[:, columns])
        field_labels = segment_field(model, normalised[:, columns])
        print(f"field {index + 1}: {field_labels.max()} objects before filtering")
        field_labels[field_labels > 0] += offset
        labels[:, columns] = field_labels
        offset += int(field_labels.max() - offset) if field_labels.max() > offset else 0
    return normalised, labels


def remove_small_objects(labels: np.ndarray) -> np.ndarray:
    """Drop objects below MIN_AREA_UM2 and relabel sequentially."""
    min_area_px = MIN_AREA_UM2 / PIXEL_SIZE_UM**2
    areas = np.bincount(labels.ravel())
    too_small = np.flatnonzero(areas < min_area_px)
    too_small = too_small[too_small != 0]
    print(f"removed {too_small.size} objects < {MIN_AREA_UM2} um^2")
    labels = labels.copy()
    labels[np.isin(labels, too_small)] = 0
    relabelled, _, _ = segmentation.relabel_sequential(labels)
    return relabelled


def drop_border_objects(labels: np.ndarray) -> np.ndarray:
    """Remove objects touching the edge of any field (the seam counts as an edge)."""
    cleaned = labels.copy()
    for columns in field_slices(labels.shape[1]):
        field = labels[:, columns]
        edge_ids = np.unique(np.concatenate([field[0], field[-1], field[:, 0], field[:, -1]]))
        cleaned[np.isin(cleaned, edge_ids[edge_ids != 0])] = 0
    relabelled, _, _ = segmentation.relabel_sequential(cleaned)
    return relabelled


def measure_cells(labels: np.ndarray) -> pd.DataFrame:
    """One row per object: label, area_um2, aspect_ratio (major/minor ellipse axis)."""
    rows = []
    for region in measure.regionprops(labels):
        if region.minor_axis_length <= 0:
            raise ValueError(f"Label {region.label} has zero minor axis; cannot compute aspect ratio")
        rows.append({
            "label": region.label,
            "area_um2": region.area * PIXEL_SIZE_UM**2,
            "aspect_ratio": region.major_axis_length / region.minor_axis_length,
        })
    return pd.DataFrame(rows, columns=["label", "area_um2", "aspect_ratio"])


def save_overlay(image: np.ndarray, complete: np.ndarray, with_border: np.ndarray, path: Path) -> None:
    """Percentile-stretched image per field; red = measured cells, yellow = excluded border cells."""
    gray = np.zeros(image.shape, dtype=np.float32)
    for columns in field_slices(image.shape[1]):
        low, high = np.percentile(image[:, columns], (1, 99))
        gray[:, columns] = np.clip((image[:, columns].astype(np.float32) - low) / (high - low), 0, 1)
    rgb = np.stack([gray] * 3, axis=-1)
    rgb[segmentation.find_boundaries(with_border, mode="inner")] = (1.0, 1.0, 0.0)
    rgb[segmentation.find_boundaries(complete, mode="inner")] = (1.0, 0.0, 0.0)
    skio.imsave(path, (rgb * 255).astype(np.uint8), check_contrast=False)


def main() -> None:
    image = load_image(INPUT_PATH)
    normalised, raw_labels = normalise_and_segment(image)
    tifffile.imwrite(NORMALISED_PATH, normalised)

    with_border = remove_small_objects(raw_labels)
    if with_border.max() == 0:
        raise RuntimeError("No objects found; check normalised.tif and parameters")
    complete = drop_border_objects(with_border)
    if complete.max() == 0:
        raise RuntimeError("All objects touch a border")
    if with_border.max() > np.iinfo(np.uint16).max:
        raise RuntimeError("Too many labels for uint16")

    table = measure_cells(complete)
    tifffile.imwrite(LABELS_WITH_BORDER_PATH, with_border.astype(np.uint16))
    tifffile.imwrite(LABELS_PATH, complete.astype(np.uint16))
    table.to_csv(TABLE_PATH, index=False)
    save_overlay(image, complete, with_border, OVERLAY_PATH)
    print(f"{with_border.max()} cells in total; {len(table)} complete cells measured "
          f"({with_border.max() - len(table)} border cells excluded)")
    print(table[["area_um2", "aspect_ratio"]].describe())


if __name__ == "__main__":
    main()
