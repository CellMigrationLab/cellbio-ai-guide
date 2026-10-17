#!/usr/bin/env python3
"""Segment cancer cells sitting on an endothelial monolayer (2D brightfield).

Input : image.tif   2D (Y, X) uint16 (12-bit values), 0.65 um/pixel
Output: labels.tif          uint16 label image, 0 = background, 1..N = cancer cells
        cell_areas.csv      one row per kept cell (area in um^2 and other shape metrics)
        rejected_objects.csv  candidate objects removed by the filters, with the reason
        overlay.png         outlines of kept (green) and rejected (red) objects
        intermediate/       flat-field-normalised image and texture-energy map

Method (classical, no GPU, no model weights):
  1. Flat-field: subtract a large Gaussian background and divide by the local
     standard deviation, so the threshold is not affected by uneven illumination.
  2. Texture energy: Gaussian-smoothed |normalised intensity|. Cancer cells
     (dark rim + bright centre, strong local contrast) score high; the smooth
     endothelial monolayer scores low.
  3. Threshold, fill holes, morphological opening.
  4. Split touching cells: distance-transform watershed (objects still larger than
     max_area_um2 are split again with finer seed settings).
  5. Remove objects that are too small/large, not convex, or extremely dark/high
     contrast (debris, fragments). Every removed object is listed in
     rejected_objects.csv with its reason.

All length parameters are in micrometres and are converted to pixels with
PIXEL_SIZE_UM, so labels stay in the original pixel grid (no resampling).

Run:   python segment_cancer_cells.py image.tif
Test:  python segment_cancer_cells.py image.tif --reference manual_labels.tif
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from skimage import feature, io, measure, morphology, segmentation

# --------------------------------------------------------------------------
# Parameters (defaults are starting points tuned on ONE example image).
# --------------------------------------------------------------------------
PIXEL_SIZE_UM = 0.65


@dataclass(frozen=True)
class Params:
    pixel_size_um: float = PIXEL_SIZE_UM
    background_sigma_um: float = 26.0     # ~40 px; must be >> cell size (15-25 um)
    energy_sigma_um: float = 1.3          # smoothing of |z| (~2 px)
    energy_threshold: float = 0.9         # in units of local SD of the flat-fielded image
    opening_radius_um: float = 3.25       # ~5 px; removes thin debris/edges
    min_seed_distance_um: float = 4.5     # min distance between watershed seeds (~7 px)
    seed_smoothing_sigma_um: float = 1.0  # smoothing of the distance map
    resplit_seed_sigma_um: float = 0.5    # finer settings for objects > max_area_um2
    resplit_min_seed_distance_um: float = 3.5
    min_area_um2: float = 100.0           # smaller than a 11 um diameter disc -> debris
    max_area_um2: float = 700.0           # larger than a 30 um diameter disc -> merged cells
    min_solidity: float = 0.93            # area / convex-area; debris clumps are irregular
    max_contrast_p95: float = 5.0         # 95th pct of |z| inside object; black debris >5.5,
                                          # cells <4.5 (set from 16 hand-picked objects: re-tune!)


# --------------------------------------------------------------------------
# I/O and validation
# --------------------------------------------------------------------------
def read_brightfield(path: Path) -> np.ndarray:
    """Read a 2D single-channel image; raise if it is not (Y, X)."""
    if not path.is_file():
        raise FileNotFoundError(f"Image not found: {path}")
    image = tifffile.imread(path)
    if image.ndim != 2:
        raise ValueError(
            f"Expected a 2D (Y, X) image, got shape {image.shape}. "
            "Select the brightfield channel / plane before calling this script."
        )
    if image.dtype != np.uint16:
        raise ValueError(f"Expected uint16 data, got {image.dtype}.")
    if image.max() == image.min():
        raise ValueError("Image is constant; nothing to segment.")
    return image


def read_labels(path: Path, expected_shape: tuple[int, int]) -> np.ndarray:
    labels = tifffile.imread(path)
    if labels.shape != expected_shape:
        raise ValueError(f"Reference shape {labels.shape} != image shape {expected_shape}.")
    if not np.issubdtype(labels.dtype, np.integer):
        raise ValueError(f"Reference labels must be integers, got {labels.dtype}.")
    return labels


def um_to_px(length_um: float, pixel_size_um: float) -> float:
    return length_um / pixel_size_um


# --------------------------------------------------------------------------
# Processing steps
# --------------------------------------------------------------------------
def flat_field_normalise(image: np.ndarray, p: Params) -> np.ndarray:
    """(I - local mean) / local SD. Returns float32 'z-image' (no clipping)."""
    img = image.astype(np.float32)
    sigma = um_to_px(p.background_sigma_um, p.pixel_size_um)
    flat = img - ndi.gaussian_filter(img, sigma)
    local_sd = np.sqrt(ndi.gaussian_filter(flat**2, sigma))
    if np.any(local_sd <= 0):
        raise ValueError("Zero local standard deviation; image has flat regions.")
    return (flat / local_sd).astype(np.float32)


def texture_energy(z_image: np.ndarray, p: Params) -> np.ndarray:
    return ndi.gaussian_filter(np.abs(z_image), um_to_px(p.energy_sigma_um, p.pixel_size_um))


def foreground_mask(energy: np.ndarray, p: Params) -> np.ndarray:
    mask = energy > p.energy_threshold
    mask = ndi.binary_fill_holes(mask)
    radius = int(round(um_to_px(p.opening_radius_um, p.pixel_size_um)))
    return morphology.opening(mask, morphology.disk(radius))


def split_touching(
    mask: np.ndarray, p: Params, seed_sigma_um: float | None = None,
    min_seed_distance_um: float | None = None,
) -> np.ndarray:
    """Distance-transform watershed; returns int32 labels (seeds = distance-map maxima)."""
    sigma_um = p.seed_smoothing_sigma_um if seed_sigma_um is None else seed_sigma_um
    dist_um = p.min_seed_distance_um if min_seed_distance_um is None else min_seed_distance_um
    smooth = ndi.gaussian_filter(
        ndi.distance_transform_edt(mask), um_to_px(sigma_um, p.pixel_size_um)
    )
    peaks = feature.peak_local_max(
        smooth,
        min_distance=int(round(um_to_px(dist_um, p.pixel_size_um))),
        labels=measure.label(mask),
        exclude_border=False,
    )
    if len(peaks) == 0:
        return measure.label(mask).astype(np.int32)
    markers = np.zeros(mask.shape, dtype=np.int32)
    markers[tuple(peaks.T)] = np.arange(1, len(peaks) + 1)
    return segmentation.watershed(-smooth, markers, mask=mask).astype(np.int32)


def resplit_oversized(labels: np.ndarray, p: Params) -> np.ndarray:
    """Second, finer watershed pass on objects above max_area_um2 (merged clusters)."""
    out = labels.copy()
    next_label = int(labels.max()) + 1
    for r in measure.regionprops(labels):
        if r.area * p.pixel_size_um**2 <= p.max_area_um2:
            continue
        sub = np.zeros(labels.shape, dtype=bool)
        sub[labels == r.label] = True
        parts = split_touching(sub, p, seed_sigma_um=p.resplit_seed_sigma_um,
                               min_seed_distance_um=p.resplit_min_seed_distance_um)
        for part in np.unique(parts[parts > 0])[1:]:   # first part keeps the old label
            out[parts == part] = next_label
            next_label += 1
    return out


def filter_objects(
    labels: np.ndarray, z_image: np.ndarray, p: Params
) -> tuple[np.ndarray, pd.DataFrame, pd.DataFrame]:
    """Keep objects passing size/shape filters; relabel 1..N.

    Returns (kept label image, table of kept cells, table of rejected objects).
    """
    kept_rows, rejected_rows = [], []
    kept = np.zeros(labels.shape, dtype=np.uint16)
    next_id = 1
    for r in measure.regionprops(labels):
        area_um2 = r.area * p.pixel_size_um**2
        reason = None
        if area_um2 < p.min_area_um2:
            reason = "too_small"
        elif area_um2 > p.max_area_um2:
            reason = "too_large"
        elif r.solidity < p.min_solidity:
            reason = "low_solidity"
        contrast_p95 = float(np.percentile(np.abs(z_image[labels == r.label]), 95))
        if reason is None and contrast_p95 > p.max_contrast_p95:
            reason = "high_contrast_debris"
        row = {
            "centroid_y_um": r.centroid[0] * p.pixel_size_um,
            "centroid_x_um": r.centroid[1] * p.pixel_size_um,
            "area_um2": area_um2,
            "equivalent_diameter_um": r.equivalent_diameter_area * p.pixel_size_um,
            "solidity": r.solidity,
            "eccentricity": r.eccentricity,
            "contrast_p95": contrast_p95,
        }
        if reason is None:
            kept[labels == r.label] = next_id
            kept_rows.append({"label": next_id, **row})
            next_id += 1
        else:
            rejected_rows.append({"candidate_label": r.label, "reason": reason, **row})
    return kept, pd.DataFrame(kept_rows), pd.DataFrame(rejected_rows)


def segment(image: np.ndarray, p: Params):
    z = flat_field_normalise(image, p)
    energy = texture_energy(z, p)
    mask = foreground_mask(energy, p)
    candidates = resplit_oversized(split_touching(mask, p), p)
    kept, kept_table, rejected_table = filter_objects(candidates, z, p)
    return kept, kept_table, rejected_table, candidates, z, energy


# --------------------------------------------------------------------------
# Outputs
# --------------------------------------------------------------------------
def save_overlay(image: np.ndarray, kept: np.ndarray, candidates: np.ndarray, path: Path) -> None:
    lo, hi = np.percentile(image, [1, 99.5])
    gray = np.clip((image.astype(np.float32) - lo) / (hi - lo), 0, 1)
    rgb = np.dstack([gray] * 3)
    rejected = (candidates > 0) & (kept == 0)
    rgb[segmentation.find_boundaries(rejected, mode="outer")] = (1.0, 0.2, 0.2)
    rgb[segmentation.find_boundaries(kept, mode="outer")] = (0.1, 1.0, 0.1)
    io.imsave(path, (rgb * 255).astype(np.uint8), check_contrast=False)


# --------------------------------------------------------------------------
# Validation against a manual annotation
# --------------------------------------------------------------------------
def match_objects(pred: np.ndarray, ref: np.ndarray, iou_threshold: float = 0.5):
    """One-to-one matching by IoU. Returns list of (ref_label, pred_label, iou)."""
    matches = []
    used_pred: set[int] = set()
    for r in np.unique(ref[ref > 0]):
        r_mask = ref == r
        cand, counts = np.unique(pred[r_mask & (pred > 0)], return_counts=True)
        best_iou, best = 0.0, None
        for c, inter in zip(cand, counts):
            if c in used_pred:
                continue
            iou = inter / (r_mask.sum() + (pred == c).sum() - inter)
            if iou > best_iou:
                best_iou, best = iou, c
        if best is not None and best_iou >= iou_threshold:
            matches.append((int(r), int(best), float(best_iou)))
            used_pred.add(int(best))
    return matches


def validate(pred: np.ndarray, ref: np.ndarray, p: Params) -> dict[str, float]:
    """Measures matched to the biological question: count and area per cell."""
    n_ref, n_pred = len(np.unique(ref[ref > 0])), len(np.unique(pred[pred > 0]))
    matches = match_objects(pred, ref)
    tp = len(matches)
    precision = tp / n_pred if n_pred else float("nan")
    recall = tp / n_ref if n_ref else float("nan")
    px2 = p.pixel_size_um**2
    area_err = [
        ((pred == pl).sum() - (ref == rl).sum()) * px2 for rl, pl, _ in matches
    ]
    ref_area = [(ref == rl).sum() * px2 for rl, _, _ in matches]
    area_rel = [e / a for e, a in zip(area_err, ref_area)]
    return {
        "n_reference": n_ref,
        "n_predicted": n_pred,
        "count_relative_error": (n_pred - n_ref) / n_ref if n_ref else float("nan"),
        "matched_IoU>=0.5": tp,
        "precision": precision,
        "recall": recall,
        "median_IoU_of_matches": float(np.median([m[2] for m in matches])) if matches else float("nan"),
        "median_area_error_um2": float(np.median(area_err)) if area_err else float("nan"),
        "median_relative_area_error": float(np.median(area_rel)) if area_rel else float("nan"),
        "total_area_relative_error": float(
            ((pred > 0).sum() - (ref > 0).sum()) / max((ref > 0).sum(), 1)
        ),
    }


# Failure criteria: if any is violated the analysis should be considered failed.
FAIL_RECALL = 0.85
FAIL_PRECISION = 0.85
FAIL_COUNT_ERROR = 0.10
FAIL_MEDIAN_REL_AREA_ERROR = 0.15


def failures(metrics: dict[str, float]) -> list[str]:
    out = []
    if not metrics["recall"] >= FAIL_RECALL:
        out.append(f"recall {metrics['recall']:.2f} < {FAIL_RECALL}")
    if not metrics["precision"] >= FAIL_PRECISION:
        out.append(f"precision {metrics['precision']:.2f} < {FAIL_PRECISION}")
    if not abs(metrics["count_relative_error"]) <= FAIL_COUNT_ERROR:
        out.append(f"|count error| {abs(metrics['count_relative_error']):.2f} > {FAIL_COUNT_ERROR}")
    if not abs(metrics["median_relative_area_error"]) <= FAIL_MEDIAN_REL_AREA_ERROR:
        out.append(
            f"|median relative area error| {abs(metrics['median_relative_area_error']):.2f}"
            f" > {FAIL_MEDIAN_REL_AREA_ERROR}"
        )
    return out


# --------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("image", type=Path)
    ap.add_argument("--out-dir", type=Path, default=Path("."))
    ap.add_argument("--reference", type=Path, help="manual label image for validation")
    ap.add_argument("--pixel-size-um", type=float, default=PIXEL_SIZE_UM)
    args = ap.parse_args(argv)

    p = Params(pixel_size_um=args.pixel_size_um)
    image = read_brightfield(args.image)
    kept, kept_table, rejected_table, candidates, z, energy = segment(image, p)

    out = args.out_dir
    (out / "intermediate").mkdir(parents=True, exist_ok=True)
    tifffile.imwrite(out / "labels.tif", kept, compression="zlib")
    kept_table.to_csv(out / "cell_areas.csv", index=False)
    rejected_table.to_csv(out / "rejected_objects.csv", index=False)
    tifffile.imwrite(out / "intermediate" / "flatfield_z.tif", z)
    tifffile.imwrite(out / "intermediate" / "texture_energy.tif", energy)
    tifffile.imwrite(out / "intermediate" / "candidates_before_filter.tif", candidates.astype(np.uint16))
    save_overlay(image, kept, candidates, out / "overlay.png")

    print(f"Cancer cells kept: {len(kept_table)}; rejected candidates: {len(rejected_table)}")
    if len(kept_table):
        print(f"Median area: {kept_table.area_um2.median():.0f} um^2 "
              f"(IQR {kept_table.area_um2.quantile(.25):.0f}-{kept_table.area_um2.quantile(.75):.0f})")

    if args.reference is not None:
        ref = read_labels(args.reference, image.shape)
        metrics = validate(kept, ref, p)
        pd.Series(metrics).to_csv(out / "validation_metrics.csv", header=["value"])
        for k, v in metrics.items():
            print(f"  {k}: {v:.3f}" if isinstance(v, float) else f"  {k}: {v}")
        failed = failures(metrics)
        if failed:
            print("VALIDATION FAILED: " + "; ".join(failed))
            return 1
        print("Validation passed (on this image only).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
