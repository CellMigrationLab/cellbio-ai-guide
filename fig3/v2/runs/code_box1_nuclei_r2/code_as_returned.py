"""Segment endothelial nuclei in a 2D widefield DAPI image and measure their shape.

Input : image.tif (Y, X), uint16 holding 12-bit values
Output: labels.tif, measurements.csv, qc/ (intermediates and overlays)
All lengths are converted from micrometres to pixels with --pixel-size-um (default 0.65).
Labels stay on the original pixel grid: no resizing or resampling.
"""
from __future__ import annotations

import argparse
import warnings
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from skimage import filters, io as skio, measure, morphology, segmentation

MAX_12BIT = 4095


@dataclass(frozen=True)
class Params:
    pixel_size_um: float = 0.65
    smooth_sigma_um: float = 0.65        # light denoising (1 px)
    background_radius_um: float = 13.0   # top-hat disk; must exceed nucleus half-length (~8 um)
    local_block_um: float = 33.0         # local threshold window (~2 nucleus lengths)
    min_area_um2: float = 30.0           # smaller objects: debris
    max_area_um2: float = 400.0          # larger objects: merged clumps (17 um round nucleus ~ 230)
    split_h_px: float = 1.0              # h-maxima height on smoothed distance map; lower = more splits
    bright_factor: float = 2.0           # reject objects whose mean intensity > factor * median (cancer proxy)

    def px(self, um: float) -> int:
        return max(1, int(round(um / self.pixel_size_um)))


def load_image(path: Path) -> np.ndarray:
    if not path.exists():
        raise FileNotFoundError(f"{path} not found in the working directory")
    img = np.squeeze(tifffile.imread(path))  # drops singleton channel/z axes only
    if img.ndim != 2:
        raise ValueError(f"Expected a 2D (Y, X) image, got shape {img.shape} after squeezing")
    if img.dtype != np.uint16:
        raise ValueError(f"Expected uint16, got {img.dtype}")
    if img.max() > MAX_12BIT:
        warnings.warn(f"Max value {img.max()} exceeds 12-bit range ({MAX_12BIT}); data may be rescaled")
    saturated = float(np.mean(img >= MAX_12BIT))
    if saturated > 0:
        print(f"Saturated pixels (>= {MAX_12BIT}): {saturated:.4%}")
    return img


def smooth_and_subtract_background(img: np.ndarray, p: Params) -> tuple[np.ndarray, np.ndarray]:
    """Gaussian smoothing, then white top-hat. Intensities stay in raw camera units (no normalisation)."""
    smoothed = filters.gaussian(img.astype(np.float32), sigma=p.smooth_sigma_um / p.pixel_size_um,
                                preserve_range=True)
    tophat = morphology.white_tophat(smoothed, morphology.disk(p.px(p.background_radius_um)))
    return smoothed, tophat


def foreground_mask(smoothed: np.ndarray, tophat: np.ndarray, p: Params) -> tuple[np.ndarray, float]:
    """Local (Gaussian-weighted mean) threshold AND a global minimum contrast (triangle on top-hat)."""
    block = p.px(p.local_block_um) | 1  # odd
    local_thr = filters.threshold_local(smoothed, block_size=block, method="gaussian", offset=0)
    min_contrast = float(filters.threshold_triangle(tophat))
    mask = (smoothed > local_thr) & (tophat > min_contrast)
    mask = ndi.binary_fill_holes(mask)
    mask = morphology.binary_opening(mask, morphology.disk(1))
    mask = morphology.remove_small_objects(mask, min_size=int(p.min_area_um2 / p.pixel_size_um**2))
    return mask, min_contrast


def split_touching(mask: np.ndarray, p: Params) -> np.ndarray:
    dist = filters.gaussian(ndi.distance_transform_edt(mask), sigma=1.0)
    markers = measure.label(morphology.h_maxima(dist, p.split_h_px))
    labels = segmentation.watershed(-dist, markers, mask=mask)
    unlabeled = int(np.sum(mask & (labels == 0)))
    if unlabeled:
        warnings.warn(f"{unlabeled} mask pixels got no watershed label (components without a marker)")
    return labels


def classify_objects(labels: np.ndarray, tophat: np.ndarray, p: Params) -> tuple[pd.DataFrame, float]:
    """Assign each object 'kept' / 'too_small' / 'too_large' / 'too_bright'."""
    table = pd.DataFrame(measure.regionprops_table(
        labels, intensity_image=tophat, properties=("label", "area", "intensity_mean")))
    table["area_um2"] = table["area"] * p.pixel_size_um**2
    size_ok = table["area_um2"].between(p.min_area_um2, p.max_area_um2)
    reference = float(table.loc[size_ok, "intensity_mean"].median())
    table["reason"] = np.select(
        [table["area_um2"] < p.min_area_um2,
         table["area_um2"] > p.max_area_um2,
         table["intensity_mean"] > p.bright_factor * reference],
        ["too_small", "too_large", "too_bright"], default="kept")
    return table, reference


def measure_final(labels: np.ndarray, p: Params) -> pd.DataFrame:
    t = pd.DataFrame(measure.regionprops_table(
        labels, properties=("label", "area", "major_axis_length", "minor_axis_length", "bbox")))
    if (t["minor_axis_length"] <= 0).any():
        raise ValueError("Object with zero minor axis; cannot compute aspect ratio")
    h, w = labels.shape
    out = pd.DataFrame({
        "label": t["label"],
        "area_um2": t["area"] * p.pixel_size_um**2,
        "aspect_ratio": t["major_axis_length"] / t["minor_axis_length"],  # moment-based ellipse
        "touches_border": (t["bbox-0"] == 0) | (t["bbox-1"] == 0) | (t["bbox-2"] == h) | (t["bbox-3"] == w),
    })
    return out


def make_overlay(img: np.ndarray, kept: np.ndarray, rejected: np.ndarray) -> np.ndarray:
    disp = np.clip(img.astype(np.float32) / np.percentile(img, 99.5), 0, 1) ** 0.5  # display only
    rgb = np.stack([disp] * 3, axis=-1)
    rgb[segmentation.find_boundaries(rejected, mode="inner")] = (1, 0, 0)  # red: rejected
    rgb[segmentation.find_boundaries(kept, mode="inner")] = (0, 1, 0)      # green: endothelial
    return (rgb * 255).astype(np.uint8)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, default=Path("image.tif"))
    d = Params()
    ap.add_argument("--pixel-size-um", type=float, default=d.pixel_size_um)
    ap.add_argument("--bright-factor", type=float, default=d.bright_factor)
    ap.add_argument("--split-h-px", type=float, default=d.split_h_px)
    ap.add_argument("--min-area-um2", type=float, default=d.min_area_um2)
    ap.add_argument("--max-area-um2", type=float, default=d.max_area_um2)
    a = ap.parse_args()
    p = Params(pixel_size_um=a.pixel_size_um, bright_factor=a.bright_factor, split_h_px=a.split_h_px,
               min_area_um2=a.min_area_um2, max_area_um2=a.max_area_um2)
    print(p)

    qc = Path("qc"); qc.mkdir(exist_ok=True)
    img = load_image(a.input)
    smoothed, tophat = smooth_and_subtract_background(img, p)
    mask, min_contrast = foreground_mask(smoothed, tophat, p)
    all_labels = split_touching(mask, p)
    table, reference = classify_objects(all_labels, tophat, p)
    print(f"min contrast (triangle) = {min_contrast:.1f}; median object mean intensity = {reference:.1f}; "
          f"bright cutoff = {p.bright_factor * reference:.1f}")
    print(table["reason"].value_counts().to_string())

    keep_ids = table.loc[table["reason"] == "kept", "label"].to_numpy()
    kept = np.where(np.isin(all_labels, keep_ids), all_labels, 0)
    rejected = np.where(kept == 0, all_labels, 0)
    labels, _, _ = segmentation.relabel_sequential(kept)
    labels = labels.astype(np.uint16)

    measurements = measure_final(labels, p)
    measurements.to_csv("measurements.csv", index=False)
    tifffile.imwrite("labels.tif", labels)

    tifffile.imwrite(qc / "tophat.tif", tophat.astype(np.float32))
    tifffile.imwrite(qc / "mask.tif", (mask * 255).astype(np.uint8))
    tifffile.imwrite(qc / "all_objects.tif", all_labels.astype(np.uint16))
    table.to_csv(qc / "object_classification.csv", index=False)
    skio.imsave(qc / "overlay.png", make_overlay(img, labels, rejected), check_contrast=False)
    n_border = int(measurements["touches_border"].sum())
    print(f"{len(measurements)} endothelial nuclei ({n_border} touch the image border)")


if __name__ == "__main__":
    main()
