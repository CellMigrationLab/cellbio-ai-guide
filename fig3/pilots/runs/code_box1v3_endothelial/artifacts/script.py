#!/usr/bin/env python
"""Segment endothelial cells in a 2D brightfield image (Cellpose-SAM) and
measure their areas.

Input : bf.tif   (Y, X), uint16 (12-bit), 0.65 um/pixel
Output: labels.tif            uint16/uint32 label image, 0 = background
        endothelial_areas.csv one row per label, area in um^2
        flatfield.tif, overlay.tif  intermediate outputs for inspection

Processing steps (nothing else is applied):
 1. validate input
 2. flat-field correction (Gaussian background subtraction), float32
 3. Cellpose-SAM; Cellpose's own normalisation (1st-99th percentile per
    channel); diameter given in pixels derived from um; masks come back at
    the original image size, so the coordinate system is unchanged
 4. remove objects smaller than --min-area-um2 and relabel sequentially
 5. measure areas; flag cells touching the image border
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile
from scipy import ndimage as ndi
from skimage import measure, segmentation

EXPECTED_MAX_12BIT = 4095


def load_brightfield(path: Path) -> np.ndarray:
    """Read a single-channel 2D uint16 image; raise on anything else."""
    if not path.is_file():
        raise FileNotFoundError(f"Input image not found: {path}")
    image = tifffile.imread(path)
    if image.ndim != 2:
        raise ValueError(
            f"Expected a 2D (Y, X) image, got shape {image.shape}. "
            "Squeeze singleton axes or select one channel explicitly."
        )
    if image.dtype != np.uint16:
        raise ValueError(f"Expected uint16 data, got {image.dtype}.")
    if image.max() == image.min():
        raise ValueError("Image is constant; nothing to segment.")
    if image.max() > EXPECTED_MAX_12BIT:
        raise ValueError(
            f"Max value {image.max()} exceeds the 12-bit range "
            f"({EXPECTED_MAX_12BIT}); check the bit depth before continuing."
        )
    return image


def flatfield_correct(image: np.ndarray, sigma_px: float) -> np.ndarray:
    """Subtract a heavily blurred copy (uneven illumination), keep the mean."""
    img = image.astype(np.float32)
    background = ndi.gaussian_filter(img, sigma=sigma_px)
    return img - background + float(img.mean())


def segment_cellpose(
    image: np.ndarray,
    diameter_px: float,
    flow_threshold: float,
    cellprob_threshold: float,
) -> np.ndarray:
    """Run Cellpose-SAM (CPU) on a single-channel image; return int labels."""
    from cellpose import models  # imported here: slow import, fail late

    # cpsam uses the first 3 channels; unused channels are set to zero.
    rgb = np.zeros((*image.shape, 3), dtype=np.float32)
    rgb[..., 0] = image
    model = models.CellposeModel(gpu=False)
    masks, _flows, _styles = model.eval(
        rgb,
        channel_axis=2,
        diameter=diameter_px,
        flow_threshold=flow_threshold,
        cellprob_threshold=cellprob_threshold,
        normalize=True,  # per-channel 1st-99th percentile (Cellpose default)
    )
    masks = np.asarray(masks)
    if masks.shape != image.shape:
        raise RuntimeError(
            f"Cellpose returned shape {masks.shape}, expected {image.shape}."
        )
    return masks


def remove_small_objects(labels: np.ndarray, min_area_px: int) -> np.ndarray:
    """Drop labels smaller than min_area_px and relabel 1..N."""
    areas = np.bincount(labels.ravel())
    too_small = areas < min_area_px
    too_small[0] = False
    cleaned = labels.copy()
    cleaned[too_small[labels]] = 0
    relabeled, _, _ = segmentation.relabel_sequential(cleaned)
    return relabeled


def measure_areas(labels: np.ndarray, pixel_size_um: float) -> pd.DataFrame:
    """Per-cell area in um^2 and a border-touching flag."""
    rows = []
    height, width = labels.shape
    for region in measure.regionprops(labels):
        min_r, min_c, max_r, max_c = region.bbox
        touches_border = (
            min_r == 0 or min_c == 0 or max_r == height or max_c == width
        )
        rows.append(
            {
                "label": region.label,
                "area_px": int(region.area),
                "area_um2": float(region.area) * pixel_size_um**2,
                "centroid_y_um": region.centroid[0] * pixel_size_um,
                "centroid_x_um": region.centroid[1] * pixel_size_um,
                "touches_border": touches_border,
            }
        )
    return pd.DataFrame(
        rows,
        columns=[
            "label", "area_px", "area_um2",
            "centroid_y_um", "centroid_x_um", "touches_border",
        ],
    )


def make_overlay(image: np.ndarray, labels: np.ndarray) -> np.ndarray:
    """RGB uint8 overlay: grayscale image with red label boundaries."""
    lo, hi = np.percentile(image, (1, 99))
    gray = np.clip((image.astype(np.float32) - lo) / (hi - lo), 0, 1)
    rgb = np.stack([gray] * 3, axis=-1)
    rgb[segmentation.find_boundaries(labels, mode="inner")] = (1, 0, 0)
    return (rgb * 255).astype(np.uint8)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("bf.tif"))
    parser.add_argument("--output", type=Path, default=Path("labels.tif"))
    parser.add_argument("--pixel-size-um", type=float, default=0.65)
    parser.add_argument("--diameter-um", type=float, default=40.0,
                        help="Typical endothelial cell diameter (um).")
    parser.add_argument("--flow-threshold", type=float, default=0.4)
    parser.add_argument("--cellprob-threshold", type=float, default=0.0)
    parser.add_argument("--background-sigma-um", type=float, default=100.0)
    parser.add_argument("--min-area-um2", type=float, default=150.0,
                        help="Objects smaller than this are removed.")
    args = parser.parse_args()

    if args.pixel_size_um <= 0 or args.diameter_um <= 0:
        raise ValueError("Pixel size and diameter must be positive.")

    outdir = args.output.parent
    image = load_brightfield(args.input)

    corrected = flatfield_correct(
        image, sigma_px=args.background_sigma_um / args.pixel_size_um
    )
    tifffile.imwrite(outdir / "flatfield.tif", corrected)

    labels = segment_cellpose(
        corrected,
        diameter_px=args.diameter_um / args.pixel_size_um,
        flow_threshold=args.flow_threshold,
        cellprob_threshold=args.cellprob_threshold,
    )
    min_area_px = int(round(args.min_area_um2 / args.pixel_size_um**2))
    labels = remove_small_objects(labels, min_area_px)

    dtype = np.uint16 if labels.max() <= np.iinfo(np.uint16).max else np.uint32
    tifffile.imwrite(args.output, labels.astype(dtype))
    tifffile.imwrite(outdir / "overlay.tif", make_overlay(image, labels),
                     photometric="rgb")

    table = measure_areas(labels, args.pixel_size_um)
    table.to_csv(outdir / "endothelial_areas.csv", index=False)

    interior = table[~table["touches_border"]]
    print(f"Cells: {len(table)} ({len(interior)} not touching the border)")
    if len(interior):
        print(f"Median area (non-border): {interior['area_um2'].median():.0f} um^2")
    else:
        print("WARNING: no non-border cells found; inspect overlay.tif.")


if __name__ == "__main__":
    main()
