"""Segment endothelial nuclei in a 2D DAPI image; measure area (µm²) and aspect ratio.

Reads image.tif (Y, X; uint16, 12-bit) from the working directory and writes
labels.tif, measurements.csv and debug outputs (debug/).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from skimage import filters, io, measure, morphology, segmentation

MAX_12BIT = 4095


@dataclass(frozen=True)
class Params:
    pixel_size_um: float = 0.65
    smooth_sigma_um: float = 0.65        # ~1 px Gaussian to suppress shot noise
    local_block_um: float = 35.0         # local-threshold window, > nucleus length (~16 µm)
    floor_mad_factor: float = 5.0        # global floor = median + 5 * robust sigma
    open_radius_px: int = 2              # removes thin bridges / specks
    split_h_px: float = 1.0              # h-maxima height on the distance map
    min_area_um2: float = 40.0
    max_area_um2: float = 250.0
    min_solidity: float = 0.88
    bright_factor: float = 2.5           # cancer-nucleus cut-off, x median object intensity
    keep_border: bool = False


def load_image(path: Path) -> np.ndarray:
    if not path.exists():
        raise FileNotFoundError(f"{path} not found in {Path.cwd()}")
    img = tifffile.imread(path)
    if img.ndim != 2:
        raise ValueError(f"Expected a 2D (Y, X) image, got shape {img.shape}")
    if img.dtype != np.uint16:
        raise ValueError(f"Expected uint16, got {img.dtype}")
    if img.max() > MAX_12BIT:
        raise ValueError(f"Max value {img.max()} exceeds 12-bit range ({MAX_12BIT})")
    n_saturated = int((img == MAX_12BIT).sum())
    if n_saturated:
        print(f"WARNING: {n_saturated} saturated pixels (value {MAX_12BIT}); "
              "intensity-based cancer-cell rejection is less reliable there.")
    return img


def smooth(img: np.ndarray, sigma_px: float) -> np.ndarray:
    return filters.gaussian(img.astype(np.float32), sigma=sigma_px, preserve_range=True)


def background_floor(smoothed: np.ndarray, mad_factor: float) -> float:
    median = np.median(smoothed)
    robust_sigma = 1.4826 * np.median(np.abs(smoothed - median))
    return float(median + mad_factor * robust_sigma)


def foreground_mask(smoothed: np.ndarray, p: Params) -> np.ndarray:
    block = int(round(p.local_block_um / p.pixel_size_um)) | 1  # must be odd
    local = filters.threshold_local(smoothed, block_size=block, method="gaussian")
    mask = (smoothed > local) & (smoothed > background_floor(smoothed, p.floor_mad_factor))
    mask = ndi.binary_fill_holes(mask)
    footprint = morphology.disk(p.open_radius_px)
    return ndi.binary_opening(mask, structure=footprint)


def split_touching(mask: np.ndarray, h_px: float) -> np.ndarray:
    """Watershed on the distance map; h-maxima markers avoid over-splitting ellipses."""
    distance = filters.gaussian(ndi.distance_transform_edt(mask), sigma=1.0)
    markers = measure.label(morphology.h_maxima(distance, h_px))
    return segmentation.watershed(-distance, markers, mask=mask)


def describe_objects(labels: np.ndarray, raw: np.ndarray, p: Params) -> pd.DataFrame:
    table = pd.DataFrame(measure.regionprops_table(
        labels, intensity_image=raw,
        properties=("label", "area", "solidity", "intensity_mean", "bbox")))
    px_area = p.pixel_size_um ** 2
    table["area_um2"] = table["area"] * px_area
    h, w = labels.shape
    table["touches_border"] = ((table["bbox-0"] == 0) | (table["bbox-1"] == 0)
                               | (table["bbox-2"] == h) | (table["bbox-3"] == w))
    return table


def reject_reasons(table: pd.DataFrame, p: Params) -> pd.Series:
    size_ok = table["area_um2"].between(p.min_area_um2, p.max_area_um2)
    reference = table.loc[size_ok, "intensity_mean"].median()
    reason = pd.Series("", index=table.index)
    # Later rules overwrite earlier ones, so the first rule listed has the highest priority.
    reason[table["solidity"] < p.min_solidity] = "low_solidity"
    reason[table["intensity_mean"] > p.bright_factor * reference] = "bright_cancer_like"
    if not p.keep_border:
        reason[table["touches_border"]] = "touches_border"
    reason[~size_ok] = "size"
    print(f"Reference (median) object intensity: {reference:.1f}; "
          f"cancer cut-off: {p.bright_factor * reference:.1f}")
    return reason


def measure_final(labels: np.ndarray, p: Params) -> pd.DataFrame:
    props = measure.regionprops_table(
        labels, properties=("label", "area", "major_axis_length", "minor_axis_length"))
    table = pd.DataFrame(props)
    return pd.DataFrame({
        "label": table["label"],
        "area_um2": table["area"] * p.pixel_size_um ** 2,
        "aspect_ratio": table["major_axis_length"] / table["minor_axis_length"],
    })


def save_overlay(raw: np.ndarray, accepted: np.ndarray, rejected: np.ndarray, path: Path) -> None:
    base = np.clip(raw / np.percentile(raw, 99.5), 0, 1) ** 0.5
    rgb = np.dstack([base] * 3)
    rgb[segmentation.find_boundaries(rejected > 0)] = (1, 0, 0)   # red: rejected
    rgb[segmentation.find_boundaries(accepted > 0)] = (0, 1, 0)   # green: endothelial
    io.imsave(path, (rgb * 255).astype(np.uint8), check_contrast=False)


def main() -> None:
    p = Params()
    raw = load_image(Path("image.tif"))
    debug = Path("debug")
    debug.mkdir(exist_ok=True)

    smoothed = smooth(raw, p.smooth_sigma_um / p.pixel_size_um)
    mask = foreground_mask(smoothed, p)
    candidates = split_touching(mask, p.split_h_px)
    table = describe_objects(candidates, raw, p)
    table["reject_reason"] = reject_reasons(table, p)

    accepted_ids = table.loc[table["reject_reason"] == "", "label"].to_numpy()
    accepted = np.where(np.isin(candidates, accepted_ids), candidates, 0)
    rejected = np.where((candidates > 0) & (accepted == 0), candidates, 0)
    final, _, _ = segmentation.relabel_sequential(accepted)
    if final.max() > np.iinfo(np.uint16).max:
        raise ValueError("More than 65535 objects; cannot store as uint16")

    tifffile.imwrite("labels.tif", final.astype(np.uint16))
    measure_final(final, p).to_csv("measurements.csv", index=False)
    table.to_csv(debug / "all_candidates.csv", index=False)
    tifffile.imwrite(debug / "foreground_mask.tif", (mask * 255).astype(np.uint8))
    save_overlay(raw, accepted, rejected, debug / "overlay.png")

    print(f"Candidates: {len(table)}; accepted endothelial nuclei: {final.max()}")
    print(table["reject_reason"].replace("", "accepted").value_counts().to_string())


if __name__ == "__main__":
    main()
