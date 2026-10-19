"""Segment endothelial cells in a brightfield monolayer and measure area and aspect ratio.

Input : image.tif (2D, uint16 holding 12-bit values), pixel size 0.65 um, made of
        N_FIELDS fields placed side by side (left to right), each processed independently.
Output: labels.tif, measurements.csv, intermediates/ (flat-field, raw labels, cancer mask, overlay).
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from skimage import io, measure, morphology, segmentation

MAX_12BIT = 4095


@dataclass(frozen=True)
class Params:
    pixel_size_um: float = 0.65
    n_fields: int = 2                         # fields side by side, equal width
    expected_cell_diameter_um: float = 40.0   # passed to Cellpose as diameter (converted to px)
    background_sigma_um: float = 65.0         # flat-field scale; must exceed cell size
    clip_percentiles: tuple[float, float] = (1.0, 99.0)  # contrast stretch to [0, 1]
    flow_threshold: float = 0.4               # Cellpose default
    cellprob_threshold: float = 0.0           # Cellpose default
    min_area_um2: float = 200.0               # drop fragments (checked after cancer-region fill)
    max_area_um2: float = 6000.0              # drop merged cells / background blobs
    # cancer-cell heuristic
    edge_sigma_um: float = 1.0
    edge_robust_z: float = 6.0                # edge strength in robust z-scores
    ring_close_radius_um: float = 1.5
    cancer_min_area_um2: float = 100.0
    cancer_max_area_um2: float = 1200.0
    cancer_min_solidity: float = 0.85
    cancer_label_fraction: float = 0.5        # Cellpose label with more than this inside the cancer mask = cancer cell
    fill_max_distance_um: float = 25.0        # max reach when assigning cancer-covered pixels to a neighbour


# ---------- input ----------
def read_image(path: Path) -> np.ndarray:
    if not path.exists():
        raise FileNotFoundError(f"{path} not found in working directory")
    image = np.squeeze(tifffile.imread(path))
    if image.ndim != 2:
        raise ValueError(f"Expected a 2D (Y, X) image, got shape {image.shape}")
    if image.dtype != np.uint16:
        raise ValueError(f"Expected uint16, got {image.dtype}")
    if image.max() > MAX_12BIT:
        raise ValueError(f"Max value {image.max()} exceeds 12-bit range ({MAX_12BIT})")
    if image.min() == image.max():
        raise ValueError("Image is constant")
    return image


def split_fields(array: np.ndarray, n_fields: int) -> list[np.ndarray]:
    """Split into n_fields equal-width fields along X (left to right)."""
    if array.shape[1] % n_fields != 0:
        raise ValueError(f"Width {array.shape[1]} is not divisible by n_fields={n_fields}")
    return np.split(array, n_fields, axis=1)


def stitch_labels(fields: list[np.ndarray]) -> np.ndarray:
    """Concatenate per-field label images along X, offsetting ids so they stay unique."""
    out, offset = [], 0
    for field in fields:
        shifted = np.where(field > 0, field + offset, 0)
        offset += int(field.max())
        out.append(shifted)
    return np.hstack(out).astype(np.int32)


# ---------- preprocessing ----------
def flat_field(image: np.ndarray, p: Params) -> np.ndarray:
    """Divide by a heavily blurred copy (removes slow illumination change), then
    stretch the p1-p99 range to [0, 1]. Output float32, same shape as input."""
    img = image.astype(np.float32)
    background = ndi.gaussian_filter(img, p.background_sigma_um / p.pixel_size_um, mode="reflect")
    if background.min() <= 0:
        raise ValueError("Non-positive background estimate; cannot flat-field")
    relative = img / background
    low, high = np.percentile(relative, p.clip_percentiles)
    if high <= low:
        raise ValueError("Degenerate contrast range after flat-fielding")
    return np.clip((relative - low) / (high - low), 0, 1).astype(np.float32)


# ---------- segmentation ----------
def load_cellpose():
    import cellpose
    from cellpose import models

    print(f"cellpose version: {getattr(cellpose, 'version', 'unknown')}")
    return models.CellposeModel(gpu=False)


def run_cellpose(model, flat: np.ndarray, p: Params) -> np.ndarray:
    masks, _, _ = model.eval(
        flat,
        diameter=p.expected_cell_diameter_um / p.pixel_size_um,
        normalize=False,  # already scaled to [0, 1] above
        flow_threshold=p.flow_threshold,
        cellprob_threshold=p.cellprob_threshold,
    )
    if masks.shape != flat.shape:
        raise RuntimeError(f"Cellpose returned shape {masks.shape}, expected {flat.shape}")
    return masks.astype(np.int32)


def detect_cancer_cells(flat: np.ndarray, p: Params) -> np.ndarray:
    """Heuristic boolean mask of round cells with a strong halo (cancer cells on top)."""
    edge = ndi.gaussian_gradient_magnitude(flat, p.edge_sigma_um / p.pixel_size_um)
    median = np.median(edge)
    mad = np.median(np.abs(edge - median))
    if mad == 0:
        raise ValueError("Edge MAD is zero; cannot normalise edge strength")
    strong = (edge - median) / (1.4826 * mad) > p.edge_robust_z
    radius = max(1, round(p.ring_close_radius_um / p.pixel_size_um))
    disk = morphology.disk(radius)
    closed = ndi.binary_dilation(strong, disk)
    filled = ndi.binary_erosion(ndi.binary_fill_holes(closed), disk)

    px_area = p.pixel_size_um ** 2
    mask = np.zeros_like(filled)
    for region in measure.regionprops(measure.label(filled)):
        area_um2 = region.area * px_area
        if (p.cancer_min_area_um2 <= area_um2 <= p.cancer_max_area_um2
                and region.solidity >= p.cancer_min_solidity):
            mask[tuple(region.coords.T)] = True
    return mask


# ---------- label editing (each step reports what it changed) ----------
def _remove(labels: np.ndarray, ids: np.ndarray) -> np.ndarray:
    out = labels.copy()
    out[np.isin(out, ids)] = 0
    return out


def drop_border_labels(labels: np.ndarray) -> tuple[np.ndarray, int]:
    edge_ids = np.unique(np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]]))
    edge_ids = edge_ids[edge_ids > 0]
    return _remove(labels, edge_ids), len(edge_ids)


def drop_cancer_labels(labels: np.ndarray, cancer: np.ndarray, min_fraction: float) -> tuple[np.ndarray, int]:
    """Remove labels that are mostly inside the cancer mask (i.e. the cancer cells themselves)."""
    n = labels.max() + 1
    inside = np.bincount(labels[cancer], minlength=n)
    area = np.bincount(labels.ravel(), minlength=n)
    ids = np.flatnonzero(inside / np.maximum(area, 1) > min_fraction)
    ids = ids[ids > 0]
    return _remove(labels, ids), len(ids)


def fill_under_cancer(labels: np.ndarray, cancer: np.ndarray, max_distance_px: float) -> tuple[np.ndarray, int]:
    """Give unlabelled cancer-covered pixels to the nearest endothelial label (within max_distance_px).
    Heuristic: assumes cells continue under the cancer cell and split it by nearest distance.
    Returns the new labels and the number of cancer-covered pixels left unassigned."""
    expanded = segmentation.expand_labels(labels, distance=max_distance_px)
    to_fill = cancer & (labels == 0)
    out = labels.copy()
    out[to_fill] = expanded[to_fill]
    return out, int((out[cancer] == 0).sum())


def drop_by_area(labels: np.ndarray, min_px: float, max_px: float) -> tuple[np.ndarray, int]:
    area = np.bincount(labels.ravel())
    ids = np.flatnonzero((area < min_px) | (area > max_px))
    ids = ids[(ids > 0) & (area[ids] > 0)]
    return _remove(labels, ids), len(ids)


# ---------- per-field pipeline ----------
def segment_field(image: np.ndarray, model, p: Params, name: str):
    flat = flat_field(image, p)
    raw = run_cellpose(model, flat, p)
    cancer = detect_cancer_cells(flat, p)
    px_area = p.pixel_size_um ** 2

    labels, n_cancer = drop_cancer_labels(raw, cancer, p.cancer_label_fraction)
    labels, n_unassigned = fill_under_cancer(labels, cancer, p.fill_max_distance_um / p.pixel_size_um)
    labels, n_border = drop_border_labels(labels)
    labels, n_size = drop_by_area(labels, p.min_area_um2 / px_area, p.max_area_um2 / px_area)
    labels = segmentation.relabel_sequential(labels)[0]
    print(f"[{name}] cellpose objects={len(np.unique(raw)) - 1}; removed as cancer={n_cancer}, "
          f"border={n_border}, area range={n_size}; cancer pixels left unassigned={n_unassigned}; "
          f"cells kept={labels.max()}")
    return flat, raw, cancer, labels


# ---------- measurement and outputs ----------
def measure_cells(labels: np.ndarray, pixel_size_um: float) -> pd.DataFrame:
    rows = []
    for r in measure.regionprops(labels):
        if r.minor_axis_length == 0:
            raise ValueError(f"Label {r.label} has zero minor axis; cannot compute aspect ratio")
        rows.append({
            "label": r.label,
            "area_um2": r.area * pixel_size_um ** 2,
            "aspect_ratio": r.major_axis_length / r.minor_axis_length,
        })
    return pd.DataFrame(rows, columns=["label", "area_um2", "aspect_ratio"])


def save_overlay(flat: np.ndarray, labels: np.ndarray, cancer: np.ndarray, path: Path) -> None:
    rgb = np.repeat((flat[..., None] * 255).astype(np.uint8), 3, axis=2)
    rgb[segmentation.find_boundaries(labels, mode="inner")] = (0, 255, 0)   # endothelial = green
    rgb[segmentation.find_boundaries(cancer, mode="inner")] = (255, 0, 0)   # cancer mask = red
    io.imsave(path, rgb, check_contrast=False)


def analyse(image_path: Path, p: Params, out_dir: Path, inter_dir: Path) -> None:
    inter_dir.mkdir(exist_ok=True)
    image = read_image(image_path)
    model = load_cellpose()

    results = [segment_field(f, model, p, f"field {i + 1}")
               for i, f in enumerate(split_fields(image, p.n_fields))]
    flat = np.hstack([r[0] for r in results])
    raw = stitch_labels([r[1] for r in results])
    cancer = np.hstack([r[2] for r in results])
    labels = stitch_labels([r[3] for r in results])
    if labels.max() > np.iinfo(np.uint16).max:
        raise ValueError("Too many labels for uint16")

    table = measure_cells(labels, p.pixel_size_um)
    tifffile.imwrite(out_dir / "labels.tif", labels.astype(np.uint16))
    table.to_csv(out_dir / "measurements.csv", index=False)
    tifffile.imwrite(inter_dir / "flat_field.tif", flat)
    tifffile.imwrite(inter_dir / "labels_raw.tif", raw.astype(np.uint16))
    tifffile.imwrite(inter_dir / "cancer_mask.tif", cancer.astype(np.uint8))
    save_overlay(flat, labels, cancer, inter_dir / "overlay.png")

    print(f"Total endothelial cells: {len(table)}; labelled fraction of image: {(labels > 0).mean():.2f}")
    print(table[["area_um2", "aspect_ratio"]].describe().round(2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", type=Path, default=Path("image.tif"))
    ap.add_argument("--pixel-size-um", type=float, default=0.65)
    ap.add_argument("--diameter-um", type=float, default=40.0)
    ap.add_argument("--n-fields", type=int, default=2)
    a = ap.parse_args()
    params = Params(pixel_size_um=a.pixel_size_um, expected_cell_diameter_um=a.diameter_um, n_fields=a.n_fields)
    analyse(a.image, params, Path("."), Path("intermediates"))
