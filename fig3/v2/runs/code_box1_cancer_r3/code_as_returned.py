"""Segment cancer cells in a 2D brightfield image made of two side-by-side fields,
and measure area and aspect ratio.

Reads  image.tif (Y, X; uint16, 12-bit) from the working directory.
Writes labels.tif, measurements.csv, plus intermediates:
  normalised.tif, overlay.png, rejected.csv

Pipeline:
  1. load + validate
  2. split into fields (equal-width, side by side); everything below runs per field
  3. local contrast normalisation (model input only)
  4. Cellpose segmentation (no resizing)
  5. filtering: area, solidity, max area (each rejection logged)
  6. measurement in um; objects touching a field edge are flagged, not removed
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile
from skimage import io as skio
from skimage.filters import gaussian
from skimage.measure import regionprops_table
from skimage.segmentation import find_boundaries, relabel_sequential


@dataclass(frozen=True)
class Config:
    input_path: Path = Path("image.tif")
    pixel_size_um: float = 0.65
    max_value: int = 4095                 # 12-bit data stored in uint16
    n_fields: int = 2                     # equal-width fields side by side
    norm_sigma_px: float = 64.0           # ~42 um; scale of local mean/std estimate
    cellpose_diameter_px: float | None = None  # None = no rescaling (model is size-tolerant)
    flow_threshold: float = 0.4           # Cellpose default
    cellprob_threshold: float = 0.0       # Cellpose default; lower -> more/larger cells
    min_area_um2: float = 80.0            # interior cells, ~10 um diameter. TUNE on annotation
    min_area_border_um2: float = 20.0     # cut cells are smaller; only removes slivers. TUNE
    max_area_um2: float = 900.0           # ~34 um diameter; removes merged clumps
    min_solidity: float = 0.85            # irregular debris clumps have low solidity


# ---------- 1. load ----------
def load_image(path: Path, max_value: int) -> np.ndarray:
    if not path.exists():
        raise FileNotFoundError(f"{path.resolve()} not found")
    img = tifffile.imread(path)
    if img.ndim != 2:
        raise ValueError(f"Expected 2D (Y, X) image, got shape {img.shape}")
    if img.dtype != np.uint16:
        raise TypeError(f"Expected uint16, got {img.dtype}")
    if img.max() > max_value:
        raise ValueError(f"Max value {img.max()} exceeds {max_value}: not 12-bit data as stated")
    return img


# ---------- 2. split ----------
def split_fields(img: np.ndarray, n_fields: int) -> list[np.ndarray]:
    if img.shape[1] % n_fields != 0:
        raise ValueError(f"Width {img.shape[1]} not divisible into {n_fields} equal fields")
    return np.split(img, n_fields, axis=1)


# ---------- 3. normalise ----------
def normalise_local(img: np.ndarray, sigma_px: float) -> np.ndarray:
    """(img - local mean) / local std, float32. Model input only; no resampling."""
    f = img.astype(np.float32)
    mean = gaussian(f, sigma=sigma_px, preserve_range=True)
    var = gaussian((f - mean) ** 2, sigma=sigma_px, preserve_range=True)
    return ((f - mean) / np.sqrt(var + 1e-6)).astype(np.float32)


# ---------- 4. segment ----------
def load_model():
    import cellpose
    from cellpose.models import CellposeModel

    print(f"cellpose {getattr(cellpose, '__version__', 'unknown')}, CPU")
    return CellposeModel(gpu=False)  # installed version's default pretrained model


def segment_cellpose(model, norm: np.ndarray, cfg: Config) -> np.ndarray:
    masks, _flows, _styles = model.eval(
        norm,
        diameter=cfg.cellpose_diameter_px,
        flow_threshold=cfg.flow_threshold,
        cellprob_threshold=cfg.cellprob_threshold,
        normalize=True,  # Cellpose default 1-99 percentile, on the locally normalised field
    )
    return masks.astype(np.int32)


# ---------- 5. filter ----------
def edge_labels(labels: np.ndarray) -> set[int]:
    """Labels with at least one pixel on the image edge."""
    edge = np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]])
    return {int(v) for v in np.unique(edge)} - {0}


def _props(labels: np.ndarray, pixel_size_um: float) -> pd.DataFrame:
    t = pd.DataFrame(regionprops_table(
        labels, properties=("label", "area", "solidity", "major_axis_length", "minor_axis_length")))
    if (t["minor_axis_length"] <= 0).any():
        raise ValueError("Degenerate object (zero minor axis); check segmentation")
    t["area_um2"] = t["area"] * pixel_size_um**2
    t["aspect_ratio"] = t["major_axis_length"] / t["minor_axis_length"]
    return t


def filter_objects(labels: np.ndarray, cfg: Config) -> tuple[np.ndarray, pd.DataFrame]:
    """Remove debris/merged objects; returns relabelled uint16 labels and rejection log."""
    if labels.max() == 0:
        return labels.astype(np.uint16), pd.DataFrame(columns=["label", "reason", "area_um2", "solidity"])
    border = edge_labels(labels)
    keep = labels.copy()
    rejected: list[dict] = []
    for _, r in _props(labels, cfg.pixel_size_um).iterrows():
        lab = int(r.label)
        min_area = cfg.min_area_border_um2 if lab in border else cfg.min_area_um2
        if r.area_um2 < min_area:
            reason = "too_small"
        elif r.area_um2 > cfg.max_area_um2:
            reason = "too_large"
        elif r.solidity < cfg.min_solidity:
            reason = "low_solidity"
        else:
            continue
        rejected.append({"label": lab, "reason": reason, "area_um2": r.area_um2, "solidity": r.solidity})
        keep[keep == lab] = 0
    keep, _, _ = relabel_sequential(keep)
    return keep.astype(np.uint16), pd.DataFrame(rejected, columns=["label", "reason", "area_um2", "solidity"])


# ---------- 6. measure ----------
def measure(labels: np.ndarray, pixel_size_um: float) -> pd.DataFrame:
    """Area (um^2), aspect ratio = major/minor axis of the moment-equivalent ellipse,
    and touches_border (touches an edge of the array passed in)."""
    cols = ["label", "area_um2", "aspect_ratio", "touches_border"]
    if labels.max() == 0:
        return pd.DataFrame(columns=cols)
    t = _props(labels, pixel_size_um)
    border = edge_labels(labels)
    t["touches_border"] = t["label"].isin(border)
    return t[cols]


# ---------- outputs ----------
def save_overlay(img: np.ndarray, labels: np.ndarray, border_labels: set[int], path: Path) -> None:
    """Red outlines = interior cells (used for statistics); yellow = cells touching a field edge."""
    lo, hi = np.percentile(img, (1, 99))  # display only
    gray = np.clip((img.astype(np.float32) - lo) / (hi - lo), 0, 1)
    rgb = np.stack([gray] * 3, axis=-1)
    is_border = np.isin(labels, list(border_labels))
    outline = find_boundaries(labels, mode="inner")
    rgb[outline & ~is_border] = (1, 0, 0)
    rgb[outline & is_border] = (1, 1, 0)
    skio.imsave(path, (rgb * 255).astype(np.uint8), check_contrast=False)


def process_field(model, field: np.ndarray, cfg: Config) -> tuple[np.ndarray, pd.DataFrame, np.ndarray]:
    norm = normalise_local(field, cfg.norm_sigma_px)
    raw = segment_cellpose(model, norm, cfg)
    labels, rejected = filter_objects(raw, cfg)
    return labels, rejected, norm


def main() -> None:
    cfg = Config()
    img = load_image(cfg.input_path, cfg.max_value)
    model = load_model()

    label_fields, norm_fields, tables, rejects, border_all = [], [], [], [], set()
    offset = 0
    for i, field in enumerate(split_fields(img, cfg.n_fields)):
        labels, rejected, norm = process_field(model, field, cfg)
        table = measure(labels, cfg.pixel_size_um)
        table.insert(1, "field", i)
        rejected.insert(1, "field", i)
        # offset labels so they are unique across fields
        labels_off = np.where(labels > 0, labels.astype(np.int64) + offset, 0)
        table["label"] += offset
        border_all |= {int(l) + offset for l in table.loc[table.touches_border, "label"] - offset}
        offset += int(labels.max())
        label_fields.append(labels_off); norm_fields.append(norm)
        tables.append(table); rejects.append(rejected)
        print(f"field {i}: kept {len(table)} (interior {(~table.touches_border).sum()}), rejected {len(rejected)}")

    if offset > np.iinfo(np.uint16).max:
        raise ValueError("Too many objects for uint16 label image")
    labels_all = np.concatenate(label_fields, axis=1).astype(np.uint16)
    table_all = pd.concat(tables, ignore_index=True)
    rejected_all = pd.concat(rejects, ignore_index=True)

    tifffile.imwrite("normalised.tif", np.concatenate(norm_fields, axis=1))
    tifffile.imwrite("labels.tif", labels_all, resolution=(1 / cfg.pixel_size_um,) * 2,
                     metadata={"unit": "um"})
    table_all.to_csv("measurements.csv", index=False)
    rejected_all.to_csv("rejected.csv", index=False)
    save_overlay(img, labels_all, border_all, Path("overlay.png"))

    interior = table_all[~table_all.touches_border]
    print(f"Total cells counted (incl. border-touching): {len(table_all)}")
    print(f"Interior cells used for shape statistics: {len(interior)}; "
          f"median area {interior.area_um2.median():.0f} um2, median aspect ratio {interior.aspect_ratio.median():.2f}")
    if len(rejected_all):
        print(rejected_all["reason"].value_counts().to_string())


if __name__ == "__main__":
    sys.exit(main())
