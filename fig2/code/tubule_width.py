"""ER tubule width (FWHM) at the same locations in the low-res input (bilinear-upsampled to the 2x grid), the prediction and
the higher-resolution reference.

Locations (revised 17 Oct 2026 after the code audit; the earlier rule sampled every 12th image row and so over-weighted
horizontal tubules): simple line points (no ends, no branches) of the skeleton of the thresholded REFERENCE, away from the
image border, thinned to a minimum Euclidean spacing of SPACING_PX in a fixed order (row, then column), so the sampling
density along a tubule does not depend on its orientation. The reference defines where tubules are; whether the
prediction has a tubule there is recorded separately (a prediction line point within MATCH_PX).

At each location the profile is taken perpendicular to the local tubule direction (structure tensor of the reference),
3 px wide, in every image. A location is used only if the FWHM is defined in all four profiles; every exclusion is
counted per reason. Noise floor: the reference measured at the same point and 2 px (62.6 nm) further along the tubule.
"""
from __future__ import annotations

import json

import numpy as np
import tifffile
from scipy import ndimage as ndi
from skimage import feature, filters, morphology

from common.metadata import BIOSR_GRID_PX_NM as PX   # nm per pixel on the 2x grid (low-res 62.6 nm, 2x grid 31.3 nm)
from common.paths import RAW as U
from common.stats import finite_values

BORDER_PX = 20
SPACING_PX = 12          # minimum distance between sampled locations (same value as the former row step)
MATCH_PX = 3             # a prediction line point within this distance = the prediction has a tubule here
PROFILE_T = np.arange(-12, 12.5, 0.5)
IMAGES = ("low_res", "predicted", "reference", "reference_2px")


def line_points(im: np.ndarray) -> np.ndarray:
    """Simple skeleton points (exactly two neighbours) of the Otsu-thresholded, Gaussian-smoothed image."""
    gi = filters.gaussian(im, 1)
    sk = morphology.skeletonize(gi > filters.threshold_otsu(gi))
    nb = ndi.convolve(sk.astype(int), np.ones((3, 3)), mode="constant") - 1
    return sk & (nb == 2)


def sample_min_distance(points: np.ndarray, spacing: float) -> np.ndarray:
    """Keep points (N x 2, row/col) in row-then-column order, skipping any closer than `spacing` to a kept point."""
    order = np.lexsort((points[:, 1], points[:, 0]))
    kept: list[np.ndarray] = []
    grid: dict[tuple[int, int], list[np.ndarray]] = {}
    cell = spacing
    for p in points[order]:
        gy, gx = int(p[0] // cell), int(p[1] // cell)
        near = [q for dy in (-1, 0, 1) for dx in (-1, 0, 1) for q in grid.get((gy + dy, gx + dx), [])]
        if all(np.hypot(*(p - q)) >= spacing for q in near):
            kept.append(p)
            grid.setdefault((gy, gx), []).append(p)
    return np.array(kept, dtype=int).reshape(-1, 2)


def fwhm(p: np.ndarray) -> float:
    """Full width at half maximum (in samples) of the peak nearest the profile centre; NaN if undefined."""
    p = p - p.min()
    if p.max() <= 0:
        return np.nan
    c = len(p) // 2
    pk = c - 3 + int(np.argmax(p[c - 3:c + 4]))
    half = p[pk] / 2
    left = pk
    while left > 0 and p[left] > half:
        left -= 1
    right = pk
    while right < len(p) - 1 and p[right] > half:
        right += 1
    if left == 0 or right == len(p) - 1:
        return np.nan
    lx = left + (half - p[left]) / (p[left + 1] - p[left])            # linear interpolation at half maximum
    rx = right - 1 + (p[right - 1] - half) / (p[right - 1] - p[right])
    return rx - lx


def profile(im: np.ndarray, y: float, x: float, ny: float, nx: float) -> np.ndarray:
    """Mean of three parallel profiles (offsets -1, 0, 1 px) across the tubule."""
    return np.mean([ndi.map_coordinates(im, [y + PROFILE_T * ny + o * nx, x + PROFILE_T * nx - o * ny], order=1)
                    for o in (-1, 0, 1)], 0)


def summary(values) -> dict:
    v = finite_values(values, name="widths")
    return {"median_nm": round(float(np.median(v)), 1), "q25": round(float(np.percentile(v, 25)), 1),
            "q75": round(float(np.percentile(v, 75)), 1)}


def main() -> None:
    lr = tifffile.imread(U + "biosr_er_lowres_input.tif").astype(float)
    pr = tifffile.imread(U + "biosr_er_rcan_prediction.tif").astype(float)
    hr = tifffile.imread(U + "biosr_er_highres_reference.tif").astype(float)
    if pr.shape != hr.shape or lr.shape != (hr.shape[0] // 2, hr.shape[1] // 2):
        raise ValueError(f"unexpected shapes: low-res {lr.shape}, prediction {pr.shape}, reference {hr.shape}")
    lr2 = ndi.zoom(lr, 2, order=1)[:hr.shape[0], :hr.shape[1]]
    images = {"low_res": lr2, "predicted": pr, "reference": hr, "reference_2px": hr}

    ref_pts = np.argwhere(line_points(hr))
    inside = ((ref_pts[:, 0] > BORDER_PX) & (ref_pts[:, 0] < hr.shape[0] - BORDER_PX)
              & (ref_pts[:, 1] > BORDER_PX) & (ref_pts[:, 1] < hr.shape[1] - BORDER_PX))
    sampled = sample_min_distance(ref_pts[inside], SPACING_PX)
    pred_near = ndi.distance_transform_edt(~line_points(pr)) <= MATCH_PX

    Arr, Arc, Acc = feature.structure_tensor(filters.gaussian(hr, 1), sigma=3, order="rc")
    out = {k: [] for k in IMAGES}
    out["prediction_has_tubule"] = []
    failed = {k: 0 for k in IMAGES}
    for y, x in sampled:
        w, v = np.linalg.eigh(np.array([[Arr[y, x], Arc[y, x]], [Arc[y, x], Acc[y, x]]]))
        ny, nx = v[:, 1]                                   # largest-eigenvalue direction = across the tubule
        ay, ax = v[:, 0]                                   # along the tubule
        vals = {k: fwhm(profile(images[k], y + (2 * ay if k == "reference_2px" else 0),
                                x + (2 * ax if k == "reference_2px" else 0), ny, nx)) * 0.5 * PX for k in IMAGES}
        for k in IMAGES:
            failed[k] += int(not np.isfinite(vals[k]))
        if all(np.isfinite(v_) for v_ in vals.values()):
            for k in IMAGES:
                out[k].append(round(float(vals[k]), 1))
            out["prediction_has_tubule"].append(bool(pred_near[y, x]))

    res = {k: summary(out[k]) for k in IMAGES}
    res["n_locations"] = len(out["reference"])
    d = np.array(out["predicted"]) - np.array(out["reference"])
    dn = np.array(out["reference_2px"]) - np.array(out["reference"])
    res["pred_minus_ref"] = {**summary(d), "median_abs_nm": round(float(np.median(np.abs(d))), 1)}
    res["noise_floor_ref_vs_ref_2px"] = {"median_nm": round(float(np.median(dn)), 1),
                                         "median_abs_nm": round(float(np.median(np.abs(dn))), 1)}
    has = np.array(out["prediction_has_tubule"])
    res["pred_minus_ref_where_prediction_has_tubule"] = {**summary(d[has]), "n": int(has.sum())}
    res["sampling"] = {"rule": f"reference line points, border {BORDER_PX} px, minimum spacing {SPACING_PX} px",
                       "reference_line_points": int(len(ref_pts)), "inside_border": int(inside.sum()),
                       "sampled": int(len(sampled)), "fwhm_undefined_by_image": failed,
                       "used_all_four_defined": res["n_locations"],
                       "prediction_has_tubule_within_px": MATCH_PX,
                       "fraction_with_prediction_tubule": round(float(has.mean()), 3)}
    res["px_nm_assumed"] = PX
    json.dump({"summary": res, "values": out}, open("panels/tubule_width.json", "w"), allow_nan=False)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
