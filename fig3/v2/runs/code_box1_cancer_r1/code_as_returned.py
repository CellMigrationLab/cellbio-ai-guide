"""Segment cancer cells in a 2D brightfield image made of two side-by-side fields.

Input : image.tif (Y, X), uint16 (12-bit), 0.65 um/px; left/right halves = separate fields
Output: labels.tif (uncut cells only), labels_all_cells.tif, labels_unfiltered.tif,
        overlay.png, measurements.csv
"""
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile
from skimage import exposure, io, measure, segmentation

PIXEL_SIZE_UM = 0.65
MAX_12BIT = 4095
N_FIELDS = 2  # side by side along X

# Diameter 10 um -> ~79 um^2. Upper limit 600 um^2 (~27.6 um diameter) is above a
# 25 um cell (491 um^2) but rejects most merged touching pairs; rejects are reported.
MIN_AREA_UM2 = 80.0
MAX_AREA_UM2 = 600.0

FLOW_THRESHOLD = 0.4        # Cellpose default
CELLPROB_THRESHOLD = 0.0    # Cellpose default
DIAMETER_PX = None          # no rescaling; cells ~23-38 px vs model scale ~30 px


def load_image(path: Path) -> np.ndarray:
    if not path.exists():
        raise FileNotFoundError(f"{path} not found in working directory")
    image = tifffile.imread(path)
    if image.ndim != 2:
        raise ValueError(f"Expected 2D (Y, X) image, got shape {image.shape}")
    if image.dtype != np.uint16:
        raise ValueError(f"Expected uint16, got {image.dtype}")
    if image.max() > MAX_12BIT:
        raise ValueError(f"Max value {image.max()} exceeds 12-bit range ({MAX_12BIT})")
    return image


def split_fields(image: np.ndarray) -> list[np.ndarray]:
    """Split into side-by-side fields (views, original pixel grid)."""
    width = image.shape[1]
    if width % N_FIELDS != 0:
        raise ValueError(f"Width {width} not divisible by {N_FIELDS} fields")
    return np.split(image, N_FIELDS, axis=1)


def segment_field(model, field: np.ndarray) -> np.ndarray:
    """Cellpose-SAM on one field; Cellpose normalises 1st-99th percentile per field."""
    masks, _flows, _styles = model.eval(
        field.astype(np.float32),
        diameter=DIAMETER_PX,
        flow_threshold=FLOW_THRESHOLD,
        cellprob_threshold=CELLPROB_THRESHOLD,
        normalize=True,
    )
    return masks.astype(np.int32)


def filter_by_area(labels: np.ndarray, field_name: str) -> np.ndarray:
    """Drop objects outside the area range (keeping original label ids); report rejects."""
    kept = labels.copy()
    for r in measure.regionprops(labels):
        area_um2 = r.area * PIXEL_SIZE_UM**2
        if not MIN_AREA_UM2 <= area_um2 <= MAX_AREA_UM2:
            kept[labels == r.label] = 0
            print(f"  [{field_name}] rejected label {r.label}: {area_um2:.0f} um^2 "
                  f"at (y={r.centroid[0]:.0f}, x={r.centroid[1]:.0f})")
    return kept


def cut_labels(labels: np.ndarray) -> set[int]:
    """Labels touching any edge of this field (including the seam to the other field)."""
    edge = np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]])
    return set(np.unique(edge[edge > 0]).tolist())


def combine_fields(per_field: list[np.ndarray]) -> np.ndarray:
    """Re-assemble fields; give labels unique ids across the whole image."""
    offset, parts = 0, []
    for labels in per_field:
        shifted = np.where(labels > 0, labels + offset, 0)
        parts.append(shifted)
        offset += labels.max()
    return np.concatenate(parts, axis=1)


def measure_cells(labels: np.ndarray, field_of_label: dict[int, str]) -> pd.DataFrame:
    """Area (um^2) and aspect ratio (ellipse major/minor axis, >= 1)."""
    rows = []
    for r in measure.regionprops(labels):
        if r.minor_axis_length == 0:
            raise ValueError(f"Label {r.label} has zero minor axis; degenerate object")
        rows.append({
            "label": r.label,
            "field": field_of_label[r.label],
            "area_um2": r.area * PIXEL_SIZE_UM**2,
            "aspect_ratio": r.major_axis_length / r.minor_axis_length,
        })
    return pd.DataFrame(rows, columns=["label", "field", "area_um2", "aspect_ratio"])


def save_overlay(image: np.ndarray, uncut: np.ndarray, cut: np.ndarray, path: Path) -> None:
    """Per-field contrast stretch (display only). Red = measured, blue = cut by an edge."""
    stretched = [
        exposure.rescale_intensity(f.astype(np.float32),
                                   in_range=tuple(np.percentile(f, (1, 99.5))),
                                   out_range=(0, 1))
        for f in split_fields(image)
    ]
    display = np.concatenate(stretched, axis=1)
    rgb = np.dstack([display] * 3)
    rgb[segmentation.find_boundaries(cut, mode="outer")] = (0, 0.4, 1)
    rgb[segmentation.find_boundaries(uncut, mode="outer")] = (1, 0, 0)
    io.imsave(path, (rgb * 255).astype(np.uint8), check_contrast=False)


def main() -> None:
    from cellpose import models

    image = load_image(Path("image.tif"))
    model = models.CellposeModel(gpu=False)

    unfiltered, filtered, uncut_per_field, field_names = [], [], [], []
    for i, field in enumerate(split_fields(image)):
        name = f"field{i + 1}"
        raw = segment_field(model, field)
        print(f"{name}: Cellpose found {len(np.unique(raw)) - 1} objects")
        kept = filter_by_area(raw, name)
        cut = cut_labels(kept)
        uncut = np.where(np.isin(kept, list(cut)), 0, kept)
        unfiltered.append(raw); filtered.append(kept); uncut_per_field.append(uncut)
        field_names.append(name)

    all_cells = combine_fields(filtered)
    uncut_cells = combine_fields(
        [np.where(u > 0, f, 0) for u, f in zip(uncut_per_field, filtered)]
    )
    # Map combined label ids to field names (same offsets as combine_fields)
    field_of_label, offset = {}, 0
    for name, f in zip(field_names, filtered):
        for lab in np.unique(f[f > 0]):
            field_of_label[int(lab) + offset] = name
        offset += f.max()

    tifffile.imwrite("labels_unfiltered.tif", combine_fields(unfiltered).astype(np.uint16))
    tifffile.imwrite("labels_all_cells.tif", all_cells.astype(np.uint16))
    tifffile.imwrite("labels.tif", uncut_cells.astype(np.uint16))
    only_cut = np.where(uncut_cells > 0, 0, all_cells)
    save_overlay(image, uncut_cells, only_cut, Path("overlay.png"))

    table = measure_cells(uncut_cells, field_of_label)
    table.to_csv("measurements.csv", index=False)
    print(f"All cells after filter: {len(np.unique(all_cells)) - 1}; "
          f"uncut (measured): {len(table)}")
    print(table.groupby("field").size().to_string())


if __name__ == "__main__":
    main()
