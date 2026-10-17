"""Intensity linearity of the CARE example against the high-SNR acquisition (exploratory; not in the final Fig 2).

Per nucleus, background-subtracted mean intensity in three images of the same field (0.6337 um/px):
  noisy     = care_denoising_acquired.tif   (low-SNR acquisition, the model input)
  restored  = care_denoising_restored.tif   (CARE output)
  high_snr  = care_denoising_highsnr_reference.tif  (high-SNR acquisition = reference)
Pairs compared: noisy vs high_snr, restored vs high_snr, noisy vs restored (the comparison in Fig 2c).

Nuclei are segmented on the high-SNR image (independent of the model); as a sensitivity check, also on the restored
image with exactly the Fig 2c procedure. Background = median intensity outside the nuclear mask, per image.
For each pair (x -> y): Pearson r, Spearman rho, least-squares line y = a x + b with R^2, the log-log slope
(1 = proportional response; < 1 compresses bright nuclei, > 1 expands them) and the Spearman correlation between the
ratio y/x and x (0 = constant gain; a trend = intensity-dependent gain, i.e. non-linearity).

Usage (from fig2/analysis, PYTHONPATH = repository root; needs matplotlib):  python care_linearity.py
Writes care_linearity.json and care_linearity.png next to this script.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import tifffile
from scipy import ndimage as ndi
from scipy import stats
from skimage import feature, filters, measure, morphology, segmentation

from common.paths import raw_file

HERE = Path(__file__).resolve().parent
IMAGES = {"noisy": "care_denoising_acquired.tif", "restored": "care_denoising_restored.tif",
          "high_snr": "care_denoising_highsnr_reference.tif"}
PAIRS = [("noisy", "high_snr"), ("restored", "high_snr"), ("noisy", "restored")]
MIN_NUCLEUS_PX = 30          # as Fig 2c
PEAK_MIN_DISTANCE = 5        # as Fig 2c


def segment_nuclei(image: np.ndarray) -> np.ndarray:
    """Fig 2c procedure: Otsu threshold, opening (disk 1), remove < 30 px, distance-transform watershed."""
    mask = image > filters.threshold_otsu(image)
    mask = morphology.remove_small_objects(morphology.binary_opening(mask, morphology.disk(1)), MIN_NUCLEUS_PX)
    dist = ndi.distance_transform_edt(mask)
    peaks = feature.peak_local_max(dist, min_distance=PEAK_MIN_DISTANCE, labels=measure.label(mask), exclude_border=False)
    markers = np.zeros(mask.shape, int)
    markers[tuple(peaks.T)] = np.arange(1, len(peaks) + 1)
    return segmentation.watershed(-dist, markers, mask=mask)


def nucleus_intensities(labels: np.ndarray, image: np.ndarray) -> np.ndarray:
    """Background-subtracted mean intensity of each nucleus (background = median outside all nuclei)."""
    background = float(np.median(image[labels == 0]))
    means = ndi.mean(image, labels=labels, index=np.arange(1, labels.max() + 1))
    return np.asarray(means) - background


def compare(x: np.ndarray, y: np.ndarray) -> dict:
    """Agreement and linearity statistics for y as a function of x (nuclei with positive signal in both)."""
    keep = (x > 0) & (y > 0)
    x, y = x[keep], y[keep]
    fit = stats.linregress(x, y)
    loglog = stats.linregress(np.log(x), np.log(y))
    return {"n": int(keep.sum()), "pearson_r": round(float(fit.rvalue), 3),
            "spearman_rho": round(float(stats.spearmanr(x, y).statistic), 3),
            "slope": round(float(fit.slope), 3), "intercept": round(float(fit.intercept), 1),
            "r2": round(float(fit.rvalue ** 2), 3), "loglog_slope": round(float(loglog.slope), 3),
            "loglog_slope_ci95": [round(float(loglog.slope - 1.96 * loglog.stderr), 3),
                                  round(float(loglog.slope + 1.96 * loglog.stderr), 3)],
            "gain_median": round(float(np.median(y / x)), 3),
            "gain_vs_intensity_rho": round(float(stats.spearmanr(x, y / x).statistic), 3)}


def analyse(mask_source: str, images: dict) -> tuple[dict, dict]:
    """Segment on one image, measure all three, compare every pair."""
    labels = segment_nuclei(images[mask_source])
    values = {name: nucleus_intensities(labels, image) for name, image in images.items()}
    results = {f"{x}_vs_{y}": compare(values[x], values[y]) for x, y in PAIRS}
    return {"mask_from": mask_source, "n_nuclei": int(labels.max()), "pairs": results}, values


def plot(values: dict, results: dict, path: Path) -> None:
    """Three scatter panels (one per pair) with the least-squares line; shared style, one colour."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 3, figsize=(12, 4), constrained_layout=True)
    for ax, (x, y) in zip(axes, PAIRS):
        r = results["pairs"][f"{x}_vs_{y}"]
        xv, yv = values[x], values[y]
        keep = (xv > 0) & (yv > 0)
        ax.scatter(xv[keep], yv[keep], s=9, color="#2a6fb0", alpha=0.6, linewidths=0)
        xs = np.linspace(0, xv[keep].max(), 50)
        ax.plot(xs, r["slope"] * xs + r["intercept"], color="#444444", lw=1.5)
        ax.set_xlabel(f"{x.replace('_', '-')} (background-subtracted mean)")
        ax.set_ylabel(f"{y.replace('_', '-')}")
        ax.set_title(f"{x} vs {y}\nr = {r['pearson_r']}, log-log slope = {r['loglog_slope']}, "
                     f"gain trend rho = {r['gain_vs_intensity_rho']}", fontsize=9)
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(color="#e5e5e5", lw=0.6)
    fig.suptitle(f"CARE example: per-nucleus intensity (n = {results['n_nuclei']} nuclei, mask from {results['mask_from']})",
                 fontsize=10)
    fig.savefig(path, dpi=150)


def main() -> None:
    images = {name: tifffile.imread(raw_file(file)).astype(float) for name, file in IMAGES.items()}
    shapes = {name: im.shape for name, im in images.items()}
    if len(set(shapes.values())) != 1:
        raise ValueError(f"Images differ in shape: {shapes}")
    primary, values = analyse("high_snr", images)
    sensitivity, _ = analyse("restored", images)
    out = {"primary": primary, "sensitivity_mask_from_restored": sensitivity}
    (HERE / "care_linearity.json").write_text(json.dumps(out, indent=1))
    plot(values, primary, HERE / "care_linearity.png")
    for block in (primary, sensitivity):
        print(f"mask from {block['mask_from']} (n={block['n_nuclei']})")
        for pair, r in block["pairs"].items():
            print(f"  {pair:22s} r={r['pearson_r']} rho={r['spearman_rho']} slope={r['slope']} R2={r['r2']} "
                  f"loglog={r['loglog_slope']} {r['loglog_slope_ci95']} gain={r['gain_median']} gain~I rho={r['gain_vs_intensity_rho']}")


if __name__ == "__main__":
    main()
