"""Segment endothelial nuclei in a 2D DAPI widefield image and measure shape.

Reads image.tif (Y, X; uint16, 12-bit). Writes labels.tif, measurements.csv and
intermediate outputs in ./debug/. Pixel size and all parameters are explicit below.
"""
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from skimage import filters, measure, morphology, segmentation, io as skio


@dataclass(frozen=True)
class Params:
    pixel_size_um: float = 0.65
    max_value: int = 4095               # 12-bit data stored in uint16
    smooth_sigma_um: float = 0.65       # Gaussian smoothing for segmentation only
    background_radius_um: float = 13.0  # white top-hat radius; > nucleus half-width (~8.5 um)
    dist_smooth_sigma_px: float = 1.0
    split_h_px: float = 1.0             # h-maxima height on distance map (watershed seeds)
    min_area_um2: float = 60.0          # ~ smallest plausible nucleus (nominal 13x17 um ~ 175 um2)
    max_area_um2: float = 450.0         # larger = merged clump or out-of-focus blob -> rejected
    bright_factor: float = 2.5          # reject objects brighter than this x median object intensity


def read_image(path: Path, p: Params) -> np.ndarray:
    if not path.exists():
        raise FileNotFoundError(f"{path} not found in {Path.cwd()}")
    image = tifffile.imread(path)
    if image.ndim != 2:
        raise ValueError(f"Expected 2D (Y, X) image, got shape {image.shape}")
    if image.dtype != np.uint16:
        raise ValueError(f"Expected uint16, got {image.dtype}")
    if image.max() > p.max_value:
        raise ValueError(f"Max value {image.max()} exceeds 12-bit range {p.max_value}")
    saturated = np.mean(image == p.max_value)
    if saturated > 0.001:
        print(f"WARNING: {saturated:.3%} of pixels are saturated; bright-object filtering may be affected")
    return image


def subtract_background(image: np.ndarray, p: Params) -> tuple[np.ndarray, np.ndarray]:
    """Return (smoothed image, background-subtracted smoothed image), in original intensity units."""
    smoothed = filters.gaussian(image.astype(np.float32), sigma=p.smooth_sigma_um / p.pixel_size_um,
                                preserve_range=True)
    radius_px = int(round(p.background_radius_um / p.pixel_size_um))
    tophat = morphology.white_tophat(smoothed, morphology.disk(radius_px))
    return smoothed, tophat


def foreground_mask(tophat: np.ndarray) -> np.ndarray:
    """Otsu on log intensity so dim endothelial nuclei are not dominated by bright cancer nuclei."""
    log_tophat = np.log1p(tophat)
    mask = log_tophat > filters.threshold_otsu(log_tophat)
    mask = ndi.binary_fill_holes(mask)
    return morphology.binary_opening(mask, morphology.disk(2))


def split_touching(mask: np.ndarray, p: Params) -> np.ndarray:
    """Distance-transform watershed with h-maxima seeds."""
    distance = filters.gaussian(ndi.distance_transform_edt(mask), sigma=p.dist_smooth_sigma_px)
    seeds = measure.label(morphology.h_maxima(distance, p.split_h_px))
    return segmentation.watershed(-distance, seeds, mask=mask)


def select_endothelial(labels: np.ndarray, smoothed: np.ndarray, p: Params) -> tuple[np.ndarray, pd.DataFrame]:
    """Keep objects with plausible area and intensity; return filtered labels and a per-object report."""
    px_area = p.pixel_size_um ** 2
    props = measure.regionprops(labels, intensity_image=smoothed)
    if not props:
        raise RuntimeError("No objects found after segmentation; check thresholds/image.")
    report = pd.DataFrame({
        "label": [r.label for r in props],
        "area_um2": [r.area * px_area for r in props],
        "median_intensity": [float(np.median(smoothed[labels == r.label])) for r in props],
    })
    reference = report["median_intensity"].median()
    report["too_small"] = report["area_um2"] < p.min_area_um2
    report["too_large"] = report["area_um2"] > p.max_area_um2
    report["too_bright"] = report["median_intensity"] > p.bright_factor * reference
    report["kept"] = ~(report["too_small"] | report["too_large"] | report["too_bright"])
    kept_ids = report.loc[report["kept"], "label"].to_numpy()
    filtered = np.where(np.isin(labels, kept_ids), labels, 0)
    return measurements_relabel(filtered), report


def measurements_relabel(labels: np.ndarray) -> np.ndarray:
    relabeled, _, _ = segmentation.relabel_sequential(labels)
    return relabeled.astype(np.uint16)


def measure_shapes(labels: np.ndarray, p: Params) -> pd.DataFrame:
    """Area in um2; aspect ratio = major/minor axis of the moment-equivalent ellipse (>= 1)."""
    rows = []
    for r in measure.regionprops(labels):
        if r.axis_minor_length == 0:
            raise ValueError(f"Label {r.label} has zero minor axis")
        rows.append({
            "label": r.label,
            "area_um2": r.area * p.pixel_size_um ** 2,
            "aspect_ratio": r.axis_major_length / r.axis_minor_length,
            "touches_border": bool(r.bbox[0] == 0 or r.bbox[1] == 0
                                   or r.bbox[2] == labels.shape[0] or r.bbox[3] == labels.shape[1]),
        })
    return pd.DataFrame(rows)


def save_overlay(image: np.ndarray, labels: np.ndarray, path: Path) -> None:
    display = np.clip(image / np.percentile(image, 99.5), 0, 1)  # display only
    overlay = segmentation.mark_boundaries(display, labels, color=(1, 0, 0), mode="inner")
    skio.imsave(path, (overlay * 255).astype(np.uint8), check_contrast=False)


def main() -> None:
    p = Params()
    image = read_image(Path("image.tif"), p)
    debug = Path("debug"); debug.mkdir(exist_ok=True)

    smoothed, tophat = subtract_background(image, p)
    mask = foreground_mask(tophat)
    candidates = split_touching(mask, p)
    labels, report = select_endothelial(candidates, smoothed, p)
    table = measure_shapes(labels, p)

    tifffile.imwrite("labels.tif", labels)
    table.to_csv("measurements.csv", index=False)
    tifffile.imwrite(debug / "tophat.tif", tophat.astype(np.float32))
    tifffile.imwrite(debug / "candidates_all.tif", measurements_relabel(candidates))
    report.to_csv(debug / "candidate_report.csv", index=False)
    save_overlay(image, labels, debug / "overlay_kept.png")
    save_overlay(image, np.where(np.isin(candidates, report.loc[~report["kept"], "label"]), candidates, 0),
                 debug / "overlay_rejected.png")
    print(f"Candidates: {len(report)}, kept: {len(table)}, rejected: {int((~report['kept']).sum())} "
          f"(small {int(report['too_small'].sum())}, large {int(report['too_large'].sum())}, "
          f"bright {int(report['too_bright'].sum())})")


if __name__ == "__main__":
    main()
