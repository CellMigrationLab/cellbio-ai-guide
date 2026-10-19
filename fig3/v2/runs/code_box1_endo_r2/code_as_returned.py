"""Segment endothelial cells in brightfield monolayers (two fields side by side) and
measure area / aspect ratio.

Usage (from the folder containing image.tif):
    python analyse_endothelial.py
    python analyse_endothelial.py --annotation manual_labels.tif

Requires: cellpose>=4, tifffile, scikit-image, scipy, pandas, numpy
Outputs: labels.tif, measurements.csv, measurements_qc.csv, overlay.png,
         cancer_mask.tif, preprocessed.tif, (with --annotation) evaluation.json
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from scipy.optimize import linear_sum_assignment
from skimage import io as skio
from skimage import measure, morphology, segmentation


@dataclass(frozen=True)
class Params:
    pixel_size_um: float = 0.65
    n_fields: int = 2                   # fields placed side by side along X
    diameter_um: float = 37.5           # middle of the 25-50 um range
    background_sigma_px: float = 100.0  # large-scale illumination removal, per field
    percentile_low: float = 1.0
    percentile_high: float = 99.0
    flow_threshold: float = 0.4         # Cellpose default
    cellprob_threshold: float = 0.0     # Cellpose default; lower -> larger/more masks
    min_area_um2: float = 100.0         # drop fragments
    cancer_z: float = 6.0               # robust z of |flattened intensity| for halos/debris
    cancer_close_radius_px: int = 4
    cancer_min_area_px: int = 150
    cancer_overlap_max: float = 0.5     # drop labels that are mostly cancer cell
    max_bit_value: int = 4095           # 12-bit data stored in uint16


# ---------- input ----------
def read_image(path: Path, params: Params) -> np.ndarray:
    if not path.exists():
        raise FileNotFoundError(f"{path} not found in the working directory")
    image = np.squeeze(tifffile.imread(path))
    if image.ndim != 2:
        raise ValueError(f"Expected a 2D (Y, X) single-channel image, got shape {image.shape}")
    if image.dtype != np.uint16:
        raise ValueError(f"Expected uint16, got {image.dtype}")
    if image.max() > params.max_bit_value:
        raise ValueError(
            f"Max value {image.max()} exceeds 12-bit range ({params.max_bit_value}); "
            "check the bit depth before continuing"
        )
    return image


def read_labels(path: Path, shape: tuple[int, ...]) -> np.ndarray:
    labels = np.squeeze(tifffile.imread(path))
    if labels.shape != shape:
        raise ValueError(f"Annotation shape {labels.shape} != image shape {shape}")
    if labels.min() < 0:
        raise ValueError("Annotation contains negative labels")
    return labels.astype(np.int32)


def field_slices(shape: tuple[int, ...], n_fields: int) -> list[tuple[slice, slice]]:
    """Equal-width column slices, one per field."""
    width = shape[1]
    if width % n_fields != 0:
        raise ValueError(f"Image width {width} is not divisible into {n_fields} equal fields")
    step = width // n_fields
    return [(slice(None), slice(i * step, (i + 1) * step)) for i in range(n_fields)]


# ---------- preprocessing (per field) ----------
def flatten_background(image: np.ndarray, params: Params) -> np.ndarray:
    """Subtract a large Gaussian background (float32, zero-centred)."""
    img = image.astype(np.float32)
    return img - ndi.gaussian_filter(img, params.background_sigma_px)


def scale_percentiles(flat: np.ndarray, params: Params) -> np.ndarray:
    low, high = np.percentile(flat, [params.percentile_low, params.percentile_high])
    if high <= low:
        raise ValueError("Field has no contrast between the chosen percentiles")
    return ((flat - low) / (high - low)).astype(np.float32)


# ---------- cancer cell / debris mask ----------
def detect_cancer_mask(flat: np.ndarray, params: Params) -> np.ndarray:
    """Strong halos and dark debris -> filled blobs. Heuristic: check overlay.png."""
    median = np.median(flat)
    mad = np.median(np.abs(flat - median))
    if mad == 0:
        raise ValueError("MAD of the field is zero; cannot compute robust z-score")
    z = np.abs(flat - median) / (1.4826 * mad)
    mask = z > params.cancer_z
    mask = morphology.binary_closing(mask, morphology.disk(params.cancer_close_radius_px))
    mask = ndi.binary_fill_holes(mask)
    return morphology.remove_small_objects(mask, params.cancer_min_area_px)


# ---------- segmentation ----------
def load_model():
    import cellpose
    from cellpose import models

    print(f"cellpose version: {getattr(cellpose, '__version__', 'unknown')}")
    return models.CellposeModel(gpu=False)  # library default pretrained model


def segment_cellpose(model, scaled: np.ndarray, params: Params) -> np.ndarray:
    diameter_px = params.diameter_um / params.pixel_size_um
    masks, _, _ = model.eval(
        scaled,
        diameter=diameter_px,
        normalize=False,  # already normalised above
        flow_threshold=params.flow_threshold,
        cellprob_threshold=params.cellprob_threshold,
    )
    if masks.max() == 0:
        raise RuntimeError("Cellpose found no objects in a field; check preprocessing and diameter")
    return masks.astype(np.int32)


# ---------- filtering ----------
def touches_border(region, shape) -> bool:
    min_r, min_c, max_r, max_c = region.bbox
    return min_r == 0 or min_c == 0 or max_r == shape[0] or max_c == shape[1]


def filter_labels(labels: np.ndarray, cancer_mask: np.ndarray | None, params: Params
                  ) -> tuple[np.ndarray, dict[str, int]]:
    """Drop border-touching, tiny, and mostly-cancer labels; relabel sequentially.

    Operates on ONE field (borders are field borders, including the seam).
    """
    min_area_px = params.min_area_um2 / params.pixel_size_um**2
    removed = {"border": 0, "too_small": 0, "mostly_cancer": 0}
    out = np.zeros_like(labels)
    for region in measure.regionprops(labels):
        if touches_border(region, labels.shape):
            removed["border"] += 1
        elif region.area < min_area_px:
            removed["too_small"] += 1
        elif cancer_mask is not None and \
                cancer_mask[tuple(region.coords.T)].mean() > params.cancer_overlap_max:
            removed["mostly_cancer"] += 1
        else:
            out[tuple(region.coords.T)] = region.label
    out, _, _ = segmentation.relabel_sequential(out)
    return out, removed


def stitch_labels(per_field: list[np.ndarray], slices, shape) -> np.ndarray:
    """Place per-field label images in the full frame with globally unique labels."""
    full = np.zeros(shape, dtype=np.int32)
    offset = 0
    for labels, sl in zip(per_field, slices):
        full[sl] = np.where(labels > 0, labels + offset, 0)
        offset += int(labels.max())
    return full


def filter_reference(ref: np.ndarray, slices, params: Params) -> np.ndarray:
    """Apply the same per-field border / size rules to the manual annotation."""
    per_field = []
    for sl in slices:
        sub, _, _ = segmentation.relabel_sequential(ref[sl])
        per_field.append(filter_labels(sub, None, params)[0])
    return stitch_labels(per_field, slices, ref.shape)


# ---------- measurement ----------
def measure_cells(labels: np.ndarray, params: Params) -> pd.DataFrame:
    rows = []
    for region in measure.regionprops(labels):
        if region.minor_axis_length <= 0:
            raise ValueError(f"Label {region.label} has zero minor axis; degenerate mask")
        rows.append({
            "label": region.label,
            "area_um2": region.area * params.pixel_size_um**2,
            "aspect_ratio": region.major_axis_length / region.minor_axis_length,
        })
    return pd.DataFrame(rows, columns=["label", "area_um2", "aspect_ratio"])


def cancer_overlap_table(labels: np.ndarray, cancer_mask: np.ndarray, params: Params) -> pd.DataFrame:
    """QC: field index and fraction of each cell inside the cancer mask."""
    field_width = labels.shape[1] / params.n_fields
    rows = []
    for region in measure.regionprops(labels):
        rows.append({
            "label": region.label,
            "field": int(region.centroid[1] // field_width),
            "cancer_overlap_fraction": float(cancer_mask[tuple(region.coords.T)].mean()),
        })
    return pd.DataFrame(rows, columns=["label", "field", "cancer_overlap_fraction"])


# ---------- evaluation against manual annotation ----------
def iou_matrix(ref: np.ndarray, pred: np.ndarray) -> np.ndarray:
    """IoU between every reference (rows) and predicted (columns) label; both sequential."""
    n_ref, n_pred = int(ref.max()), int(pred.max())
    inter = np.bincount((ref.ravel().astype(np.int64) * (n_pred + 1) + pred.ravel()),
                        minlength=(n_ref + 1) * (n_pred + 1)).reshape(n_ref + 1, n_pred + 1)
    area_ref, area_pred = inter.sum(1), inter.sum(0)
    union = area_ref[:, None] + area_pred[None, :] - inter
    return (inter / np.maximum(union, 1))[1:, 1:]


def evaluate(pred: np.ndarray, ref: np.ndarray, cancer_mask: np.ndarray, params: Params,
             iou_min: float = 0.5) -> dict:
    """Both `pred` and `ref` must already be filtered and sequentially labelled."""
    if ref.max() == 0:
        raise ValueError("Annotation has no objects after border/size filtering")
    iou = iou_matrix(ref, pred)
    rows, cols = linear_sum_assignment(-iou)
    keep = iou[rows, cols] >= iou_min
    rows, cols = rows[keep], cols[keep]
    tp, n_ref, n_pred = len(rows), int(ref.max()), int(pred.max())

    ref_table = measure_cells(ref, params).set_index("label")
    ref_m = ref_table.loc[rows + 1]
    pred_m = measure_cells(pred, params).set_index("label").loc[cols + 1]

    ref_overlap = cancer_overlap_table(ref, cancer_mask, params).set_index("label")
    covered = ref_overlap.cancer_overlap_fraction.values > 0.1  # ref cell partly under cancer
    matched = np.zeros(n_ref, dtype=bool)
    matched[rows] = True

    def recall(mask: np.ndarray) -> float:
        return float(matched[mask].mean()) if mask.any() else float("nan")

    result = {
        "n_reference": n_ref, "n_predicted": n_pred, "tp": tp,
        "fp": n_pred - tp, "fn": n_ref - tp,
        "precision": tp / n_pred if n_pred else 0.0,
        "recall": tp / n_ref,
        "f1": 2 * tp / (n_ref + n_pred),
        "count_error_pct": 100 * (n_pred - n_ref) / n_ref,
        "median_area_ratio_pred_over_ref":
            float(np.median(pred_m.area_um2.values / ref_m.area_um2.values)) if tp else float("nan"),
        "median_abs_aspect_ratio_diff":
            float(np.median(np.abs(pred_m.aspect_ratio.values - ref_m.aspect_ratio.values)))
            if tp else float("nan"),
        "median_aspect_ratio_ref": float(ref_m.aspect_ratio.median()) if tp else float("nan"),
        "median_aspect_ratio_pred": float(pred_m.aspect_ratio.median()) if tp else float("nan"),
        "n_ref_under_cancer": int(covered.sum()),
        "recall_ref_under_cancer": recall(covered),
        "recall_ref_not_under_cancer": recall(~covered),
    }
    result["failures"] = failure_reasons(result)
    return result


def failure_reasons(r: dict) -> list[str]:
    """Pass/fail thresholds are my suggestions: adjust to your required precision."""
    reasons = []
    if r["f1"] < 0.7:
        reasons.append(f"F1@IoU0.5 = {r['f1']:.2f} < 0.70")
    if abs(r["count_error_pct"]) > 10:
        reasons.append(f"count error {r['count_error_pct']:.1f}% outside +-10%")
    ratio = r["median_area_ratio_pred_over_ref"]
    if not 0.9 <= ratio <= 1.1:
        reasons.append(f"median area ratio {ratio:.2f} outside 0.90-1.10")
    if r["median_abs_aspect_ratio_diff"] > 0.2:
        reasons.append(f"median |aspect ratio diff| {r['median_abs_aspect_ratio_diff']:.2f} > 0.20")
    under = r["recall_ref_under_cancer"]
    if r["n_ref_under_cancer"] >= 5 and under < 0.5:
        reasons.append(f"recall for cells under cancer cells = {under:.2f} < 0.50")
    return reasons


# ---------- outputs ----------
def save_overlay(scaled, labels, cancer_mask, path: Path, ref: np.ndarray | None = None) -> None:
    gray = np.clip(scaled, 0, 1)
    rgb = np.stack([gray] * 3, axis=-1)
    rgb[segmentation.find_boundaries(cancer_mask, mode="inner")] = (1, 0, 0)  # cancer: red
    rgb[segmentation.find_boundaries(labels, mode="inner")] = (0, 1, 0)        # prediction: green
    if ref is not None:
        rgb[segmentation.find_boundaries(ref, mode="inner")] = (1, 0, 1)       # annotation: magenta
    skio.imsave(path, (rgb * 255).astype(np.uint8), check_contrast=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=Path, default=Path("image.tif"))
    parser.add_argument("--annotation", type=Path, default=None)
    parser.add_argument("--diameter-um", type=float, default=Params.diameter_um)
    parser.add_argument("--cellprob-threshold", type=float, default=Params.cellprob_threshold)
    args = parser.parse_args()
    params = replace(Params(), diameter_um=args.diameter_um,
                     cellprob_threshold=args.cellprob_threshold)
    print(f"parameters: {params}")

    image = read_image(args.image, params)
    slices = field_slices(image.shape, params.n_fields)
    model = load_model()

    scaled_full = np.zeros(image.shape, dtype=np.float32)
    cancer_full = np.zeros(image.shape, dtype=bool)
    per_field_labels = []
    for i, sl in enumerate(slices):
        flat = flatten_background(image[sl], params)
        scaled_full[sl] = scale_percentiles(flat, params)
        cancer_full[sl] = detect_cancer_mask(flat, params)
        raw = segment_cellpose(model, scaled_full[sl], params)
        filtered, removed = filter_labels(raw, cancer_full[sl], params)
        print(f"field {i}: Cellpose objects {int(raw.max())}; removed {removed}; "
              f"kept {int(filtered.max())}")
        per_field_labels.append(filtered)

    labels = stitch_labels(per_field_labels, slices, image.shape)
    if labels.max() == 0:
        raise RuntimeError("All objects were filtered out")

    table = measure_cells(labels, params)
    qc = cancer_overlap_table(labels, cancer_full, params)
    tifffile.imwrite("labels.tif", labels.astype(np.uint16))  # same pixel grid as input
    table.to_csv("measurements.csv", index=False)
    qc.to_csv("measurements_qc.csv", index=False)
    tifffile.imwrite("preprocessed.tif", scaled_full)
    tifffile.imwrite("cancer_mask.tif", cancer_full.astype(np.uint8))

    ref = None
    if args.annotation is not None:
        ref = filter_reference(read_labels(args.annotation, image.shape), slices, params)
        result = evaluate(labels, ref, cancer_full, params)
        Path("evaluation.json").write_text(json.dumps(result, indent=2))
        print(json.dumps(result, indent=2))
        print("ANALYSIS FAILED" if result["failures"] else "Analysis passed the checks")
    save_overlay(scaled_full, labels, cancer_full, Path("overlay.png"), ref)


if __name__ == "__main__":
    main()
