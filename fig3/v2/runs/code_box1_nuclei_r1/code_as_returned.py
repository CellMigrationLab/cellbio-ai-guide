"""Segment endothelial nuclei in a widefield DAPI image and measure shape.

Reads image.tif; writes labels.tif, measurements.csv and debug outputs.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from skimage import filters, io, measure, morphology, segmentation


@dataclass(frozen=True)
class Params:
    pixel_size_um: float = 0.65
    max_value: int = 4095               # 12-bit data stored in uint16
    smooth_sigma_px: float = 1.0        # ~0.65 um denoising
    local_block_px: int = 51            # ~33 um local-threshold window
    local_offset_log: float = 0.10      # pixel must exceed local mean by this (ln units)
    noise_floor_mads: float = 3.0       # also > median + k * MAD of the image
    opening_radius_px: int = 2
    split_dist_sigma_px: float = 1.0
    split_h_px: float = 1.0             # h-maxima height on distance map; lower = more splits
    min_area_um2: float = 30.0
    max_area_um2: float = 250.0
    cancer_intensity_ratio: float = 2.0  # object mean > ratio * median object mean => cancer


def load_image(path: Path, p: Params) -> np.ndarray:
    if not path.exists():
        raise FileNotFoundError(f"{path} not found in {Path.cwd()}")
    img = tifffile.imread(path)
    if img.ndim != 2:
        raise ValueError(f"Expected a 2D (Y, X) image, got shape {img.shape}")
    if img.dtype != np.uint16:
        raise ValueError(f"Expected uint16, got {img.dtype}")
    if img.max() == 0:
        raise ValueError("Image is empty (all zeros)")
    if img.max() > p.max_value:
        raise ValueError(f"Max value {img.max()} exceeds {p.max_value}; data is not 12-bit as stated")
    return img


def smooth_image(img: np.ndarray, p: Params) -> np.ndarray:
    return filters.gaussian(img.astype(np.float32), p.smooth_sigma_px, preserve_range=True)


def foreground_mask(smooth: np.ndarray, p: Params) -> np.ndarray:
    median = np.median(smooth)
    mad = 1.4826 * np.median(np.abs(smooth - median))
    above_floor = smooth > median + p.noise_floor_mads * mad
    log_img = np.log1p(smooth)
    local = filters.threshold_local(log_img, p.local_block_px, method="gaussian",
                                    offset=-p.local_offset_log)
    mask = (log_img > local) & above_floor
    mask = morphology.binary_opening(mask, morphology.disk(p.opening_radius_px))
    mask = ndi.binary_fill_holes(mask)
    return mask


def split_touching(mask: np.ndarray, p: Params) -> np.ndarray:
    dist = filters.gaussian(ndi.distance_transform_edt(mask), p.split_dist_sigma_px)
    markers = measure.label(morphology.h_maxima(dist, p.split_h_px))
    return segmentation.watershed(-dist, markers, mask=mask)


def classify_objects(labels: np.ndarray, smooth: np.ndarray, p: Params) -> pd.DataFrame:
    """One row per candidate object with a 'verdict' column."""
    px_area = p.pixel_size_um ** 2
    props = measure.regionprops(labels, intensity_image=smooth)
    if not props:
        raise RuntimeError("No candidate objects found; check thresholds")
    table = pd.DataFrame({
        "label": [r.label for r in props],
        "area_um2": [r.area * px_area for r in props],
        "mean_intensity": [r.intensity_mean for r in props],
    })
    bright_cut = p.cancer_intensity_ratio * table["mean_intensity"].median()
    verdict = np.full(len(table), "endothelial", dtype=object)
    verdict[(table["area_um2"] < p.min_area_um2) | (table["area_um2"] > p.max_area_um2)] = "bad_size"
    verdict[table["mean_intensity"] > bright_cut] = "cancer_bright"  # overrides size
    table["verdict"] = verdict
    return table


def measure_objects(labels: np.ndarray, p: Params) -> pd.DataFrame:
    """Area (um^2) and aspect ratio (major/minor axis, >= 1) for each label."""
    px_area = p.pixel_size_um ** 2
    rows = []
    for r in measure.regionprops(labels):
        if r.minor_axis_length == 0:
            raise ValueError(f"Label {r.label} has zero minor axis; object is degenerate")
        y0, x0, y1, x1 = r.bbox
        rows.append({
            "label": r.label,
            "area_um2": r.area * px_area,
            "aspect_ratio": r.major_axis_length / r.minor_axis_length,
            "touches_border": bool(y0 == 0 or x0 == 0 or y1 == labels.shape[0] or x1 == labels.shape[1]),
        })
    return pd.DataFrame(rows)


def save_overlay(img: np.ndarray, kept: np.ndarray, rejected: np.ndarray, path: Path) -> None:
    disp = np.clip(img / np.percentile(img, 99.5), 0, 1) ** 0.5
    rgb = np.dstack([disp] * 3)
    rgb[segmentation.find_boundaries(rejected, mode="inner")] = (1, 0, 0)  # red: rejected
    rgb[segmentation.find_boundaries(kept, mode="inner")] = (0, 1, 0)      # green: kept
    io.imsave(path, (rgb * 255).astype(np.uint8), check_contrast=False)


def main() -> None:
    p = Params()
    img = load_image(Path("image.tif"), p)
    smooth = smooth_image(img, p)
    candidates = split_touching(foreground_mask(smooth, p), p)
    table = classify_objects(candidates, smooth, p)

    keep_ids = table.loc[table["verdict"] == "endothelial", "label"].to_numpy()
    if keep_ids.size == 0:
        raise RuntimeError("All objects were rejected; check classification parameters")
    kept = np.where(np.isin(candidates, keep_ids), candidates, 0)
    rejected = np.where(kept == 0, candidates, 0)
    labels, _, _ = segmentation.relabel_sequential(kept)
    if labels.max() > np.iinfo(np.uint16).max:
        raise ValueError("Too many objects for a uint16 label image")
    labels = labels.astype(np.uint16)

    tifffile.imwrite("labels.tif", labels)
    measure_objects(labels, p).to_csv("measurements.csv", index=False)
    table.to_csv("debug_candidates.csv", index=False)       # every candidate and its verdict
    tifffile.imwrite("debug_rejected.tif", rejected.astype(np.uint16))
    save_overlay(img, labels, rejected, Path("debug_overlay.png"))

    print(f"candidates: {len(table)}\n{table['verdict'].value_counts().to_string()}")
    print(f"endothelial nuclei kept: {labels.max()}")


if __name__ == "__main__":
    main()
