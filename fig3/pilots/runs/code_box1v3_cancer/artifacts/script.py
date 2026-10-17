"""Segment cancer cells on an endothelial monolayer (brightfield) with Cellpose 4.

Input : bf.tif   2D (Y, X), uint16 (12-bit values), 0.65 um/px
Output: labels.tif          uint16/int32 label image (0 = background)
        cell_areas.csv      one row per candidate (kept and rejected) with reasons
        overlay.tif         RGB overlay of kept (green) and rejected (red) outlines
        flattened.tif       illumination-flattened image passed to Cellpose

Run: python analyze_bf.py
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from skimage import measure, segmentation

# --------------------------------------------------------------------------
# Parameters (all explicit)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Params:
    input_path: Path = Path("bf.tif")
    labels_path: Path = Path("labels.tif")
    table_path: Path = Path("cell_areas.csv")
    overlay_path: Path = Path("overlay.tif")
    flat_path: Path = Path("flattened.tif")

    pixel_size_um: float = 0.65          # given by user; isotropic in Y and X
    max_valid_value: int = 4095          # 12-bit data stored in uint16

    # Illumination flattening: subtract a heavily smoothed copy of the image.
    # Sigma must be much larger than a cell (~38 px) -> 100 px (65 um).
    flatten_sigma_px: float = 100.0

    # Cellpose (v4, cpsam). No rescaling: cells are ~23-38 px vs native ~30 px.
    cellpose_diameter: float | None = None
    flow_threshold: float = 0.4          # Cellpose default
    cellprob_threshold: float = 0.0      # Cellpose default; lower -> more/larger masks
    min_size_px: int = 15                # Cellpose default (pixels)

    # Post-filters on Cellpose candidates (physical units).
    min_area_um2: float = 80.0           # ~10 um equivalent diameter
    max_area_um2: float = 900.0          # ~34 um; larger is probably a merged cluster
    min_solidity: float = 0.85           # rejects ragged debris / endothelial outlines
    # Rim contrast = mean gradient magnitude on the object boundary, in units of
    # the flattened, percentile-normalised image. None = filter OFF.
    # Calibrate with calibrate_rim_contrast against your annotation before use.
    min_rim_contrast: float | None = None


# --------------------------------------------------------------------------
# I/O and validation
# --------------------------------------------------------------------------


def load_brightfield(path: Path, max_valid_value: int) -> np.ndarray:
    """Read a single-channel 2D brightfield image; raise on anything unexpected."""
    if not path.is_file():
        raise FileNotFoundError(f"Input image not found: {path.resolve()}")
    image = tifffile.imread(path)
    if image.dtype != np.uint16:
        raise ValueError(f"Expected uint16 image, got {image.dtype}.")
    squeezed = np.squeeze(image)
    if squeezed.ndim != 2:
        raise ValueError(
            f"Expected a 2D single-channel image (Y, X); got shape {image.shape}."
        )
    if squeezed.max() > max_valid_value:
        raise ValueError(
            f"Max value {squeezed.max()} exceeds 12-bit range ({max_valid_value}); "
            "the data type/bit depth does not match what was described."
        )
    return squeezed


def validate_params(p: Params) -> None:
    if p.pixel_size_um <= 0:
        raise ValueError("pixel_size_um must be positive.")
    if p.min_area_um2 >= p.max_area_um2:
        raise ValueError("min_area_um2 must be smaller than max_area_um2.")


# --------------------------------------------------------------------------
# Processing steps
# --------------------------------------------------------------------------


def flatten_illumination(image: np.ndarray, sigma_px: float) -> np.ndarray:
    """Subtract a large-scale Gaussian background. Returns float32, ~zero-centred.

    This changes intensities only; geometry and pixel size are untouched.
    """
    img = image.astype(np.float32)
    background = ndi.gaussian_filter(img, sigma=sigma_px, mode="reflect")
    return img - background


def normalise_percentile(image: np.ndarray, low=1.0, high=99.0) -> np.ndarray:
    """Map the given percentiles to 0 and 1 (no clipping), as Cellpose does."""
    lo, hi = np.percentile(image, [low, high])
    if hi <= lo:
        raise ValueError("Image has no intensity range after flattening.")
    return ((image - lo) / (hi - lo)).astype(np.float32)


def run_cellpose(flat: np.ndarray, p: Params) -> np.ndarray:
    """Run Cellpose-SAM on CPU; return an integer label image (same Y, X)."""
    from cellpose import models  # imported here so --help-style use stays light

    model = models.CellposeModel(gpu=False)  # default pretrained model (cpsam)
    masks, _flows, _styles = model.eval(
        flat,
        diameter=p.cellpose_diameter,
        flow_threshold=p.flow_threshold,
        cellprob_threshold=p.cellprob_threshold,
        min_size=p.min_size_px,
        normalize=True,  # 1st-99th percentile, per Cellpose default
    )
    masks = np.asarray(masks)
    if masks.shape != flat.shape:
        raise RuntimeError(
            f"Cellpose returned shape {masks.shape}, expected {flat.shape}."
        )
    return masks.astype(np.int32)


def boundary_gradient(norm_image: np.ndarray) -> np.ndarray:
    """Gradient magnitude (sigma = 1 px) of the normalised image."""
    return ndi.gaussian_gradient_magnitude(norm_image, sigma=1.0)


def measure_candidates(
    labels: np.ndarray, norm_image: np.ndarray, p: Params
) -> pd.DataFrame:
    """One row per Cellpose object with area, shape and contrast features."""
    grad = boundary_gradient(norm_image)
    boundaries = segmentation.find_boundaries(labels, mode="inner")
    height, width = labels.shape
    pixel_area = p.pixel_size_um**2

    rows = []
    for region in measure.regionprops(labels):
        rr, cc = region.coords[:, 0], region.coords[:, 1]
        on_rim = boundaries[rr, cc]
        min_r, min_c, max_r, max_c = region.bbox
        rows.append(
            {
                "cellpose_label": region.label,
                "centroid_y_um": region.centroid[0] * p.pixel_size_um,
                "centroid_x_um": region.centroid[1] * p.pixel_size_um,
                "area_px": int(region.area),
                "area_um2": region.area * pixel_area,
                "solidity": region.solidity,
                "eccentricity": region.eccentricity,
                "rim_contrast": float(grad[rr, cc][on_rim].mean()),
                "touches_border": bool(
                    min_r == 0 or min_c == 0 or max_r == height or max_c == width
                ),
            }
        )
    if not rows:
        raise RuntimeError("Cellpose found no objects; check the image and parameters.")
    return pd.DataFrame(rows)


def apply_filters(table: pd.DataFrame, p: Params) -> pd.DataFrame:
    """Add 'kept' and 'reject_reason' columns. Never deletes rows."""
    reasons = pd.Series("", index=table.index, dtype=object)

    def mark(mask: pd.Series, text: str) -> None:
        reasons[mask & (reasons == "")] = text

    mark(table.area_um2 < p.min_area_um2, "too_small")
    mark(table.area_um2 > p.max_area_um2, "too_large_possible_cluster")
    mark(table.solidity < p.min_solidity, "low_solidity")
    if p.min_rim_contrast is not None:
        mark(table.rim_contrast < p.min_rim_contrast, "low_rim_contrast")

    out = table.copy()
    out["reject_reason"] = reasons
    out["kept"] = reasons == ""
    return out


def build_output_labels(labels: np.ndarray, table: pd.DataFrame) -> tuple[np.ndarray, pd.DataFrame]:
    """Relabel kept objects 1..N and add the final 'label' column to the table."""
    kept = table[table.kept].reset_index(drop=True)
    out = np.zeros(labels.shape, dtype=np.int32)
    final_ids = np.arange(1, len(kept) + 1)
    for final_id, old_id in zip(final_ids, kept.cellpose_label):
        out[labels == old_id] = final_id
    kept = kept.assign(label=final_ids)
    result = table.merge(
        kept[["cellpose_label", "label"]], on="cellpose_label", how="left"
    )
    result["label"] = result["label"].fillna(0).astype(int)
    return out, result


def make_overlay(norm_image: np.ndarray, labels: np.ndarray, table: pd.DataFrame) -> np.ndarray:
    """RGB uint8: kept outlines green, rejected outlines red."""
    gray = np.clip((norm_image + 0.5) / 2.0, 0, 1)
    rgb = np.stack([gray] * 3, axis=-1)
    kept_ids = set(table.loc[table.kept, "cellpose_label"])
    kept_mask = np.isin(labels, list(kept_ids))
    outline = segmentation.find_boundaries(labels, mode="inner")
    rgb[outline & kept_mask] = (0, 1, 0)
    rgb[outline & ~kept_mask & (labels > 0)] = (1, 0, 0)
    return (rgb * 255).astype(np.uint8)


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------


def main() -> None:
    p = Params()
    validate_params(p)

    image = load_brightfield(p.input_path, p.max_valid_value)
    flat = flatten_illumination(image, p.flatten_sigma_px)
    tifffile.imwrite(p.flat_path, flat)
    norm = normalise_percentile(flat)

    raw_labels = run_cellpose(flat, p)
    table = measure_candidates(raw_labels, norm, p)
    table = apply_filters(table, p)
    final_labels, table = build_output_labels(raw_labels, table)

    max_label = int(final_labels.max())
    dtype = np.uint16 if max_label < np.iinfo(np.uint16).max else np.int32
    tifffile.imwrite(p.labels_path, final_labels.astype(dtype))
    tifffile.imwrite(p.overlay_path, make_overlay(norm, raw_labels, table))
    table.to_csv(p.table_path, index=False)

    kept = table[table.kept]
    print(f"Cellpose candidates: {len(table)}; kept: {len(kept)}")
    print(table.reject_reason.value_counts().to_string())
    print(f"Kept area (um^2): median {kept.area_um2.median():.0f}, "
          f"IQR {kept.area_um2.quantile(.25):.0f}-{kept.area_um2.quantile(.75):.0f}")
    print(f"Kept objects touching the border (area truncated): {int(kept.touches_border.sum())}")
    if p.min_rim_contrast is None:
        print("WARNING: rim-contrast filter is OFF; endothelial cells may be included.")


if __name__ == "__main__":
    main()
