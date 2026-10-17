#!/usr/bin/env python3
"""Segment round cancer cells in a 2D single-channel brightfield image with Cellpose 4.

Usage: python segment.py bf.tif --pixel-size 0.65
Outputs: labels.tif (uint16/uint32 label image, same Y,X as input), areas.csv (area in um^2).
Not covered: tuning, 3D, multi-channel, time series.
"""
import argparse
import sys

import numpy as np
import pandas as pd
import tifffile
from skimage.measure import regionprops
from skimage.segmentation import relabel_sequential


def validate_image(img: np.ndarray) -> None:
    if img.ndim != 2:
        raise ValueError(f"Expected a 2D single-channel image (Y, X); got shape {img.shape}.")
    if min(img.shape) < 32:
        raise ValueError(f"Image too small to segment: {img.shape}.")
    if not (np.issubdtype(img.dtype, np.integer) or np.issubdtype(img.dtype, np.floating)):
        raise ValueError(f"Unsupported dtype {img.dtype}.")
    if np.issubdtype(img.dtype, np.floating) and not np.isfinite(img).all():
        raise ValueError("Image contains NaN or Inf.")
    if img.min() == img.max():
        raise ValueError("Image is constant; nothing to segment.")


def segment_cancer_cells(
    img,
    pixel_size_um,
    model_name=None,          # None = library default model (printed at run time)
    diameter=None,            # library default: no rescaling
    normalize=True,           # library default
    flow_threshold=0.4,       # library default
    cellprob_threshold=0.0,   # library default
    min_size=15,              # library default (Cellpose internal, in px)
    niter=None,               # library default
    batch_size=8,             # library default
    tile_overlap=0.1,         # library default
    resample=True,            # library default
    augment=False,            # library default
    min_area_um2=100.0,       # NOT a library setting: my post-filter
    max_area_um2=800.0,       # NOT a library setting: my post-filter
    min_solidity=0.85,        # NOT a library setting: my post-filter
):
    """Return (labels, table). labels has the same shape as img (original coordinates)."""
    if not pixel_size_um > 0:
        raise ValueError("pixel_size_um must be > 0.")
    if not 0 <= min_solidity <= 1:
        raise ValueError("min_solidity must be in [0, 1].")
    if min_area_um2 >= max_area_um2:
        raise ValueError("min_area_um2 must be < max_area_um2.")
    validate_image(img)

    from cellpose import models  # imported late so input errors appear first

    kwargs = {"gpu": False}
    if model_name is not None:
        kwargs["pretrained_model"] = model_name
    model = models.CellposeModel(**kwargs)
    print(f"Cellpose model: {model_name or 'library default'}", file=sys.stderr)

    # Image passed unchanged (no resizing, no dtype change, no channel handling).
    masks, _flows, _styles = model.eval(
        img,
        diameter=diameter,
        normalize=normalize,
        flow_threshold=flow_threshold,
        cellprob_threshold=cellprob_threshold,
        min_size=min_size,
        niter=niter,
        batch_size=batch_size,
        tile_overlap=tile_overlap,
        resample=resample,
        augment=augment,
        channel_axis=None,
        z_axis=None,
        do_3D=False,
    )
    masks = np.asarray(masks)
    if masks.shape != img.shape:
        raise RuntimeError(f"Output shape {masks.shape} != input shape {img.shape}.")
    n_raw = int(masks.max())

    # Post-filter on physical size and shape (my own step, reported, not silent).
    px_area = pixel_size_um ** 2
    keep = np.zeros(int(masks.max()) + 1, dtype=bool)
    removed = {"too_small": 0, "too_large": 0, "low_solidity": 0}
    for rp in regionprops(masks):
        a = rp.area * px_area
        if a < min_area_um2:
            removed["too_small"] += 1
        elif a > max_area_um2:
            removed["too_large"] += 1
        elif rp.solidity < min_solidity:
            removed["low_solidity"] += 1
        else:
            keep[rp.label] = True
    filtered = np.where(keep[masks], masks, 0)
    filtered, _, _ = relabel_sequential(filtered)
    filtered = filtered.astype(np.uint16 if filtered.max() < 65535 else np.uint32)

    print(f"Cellpose objects: {n_raw}; removed {removed}; kept: {int(filtered.max())}",
          file=sys.stderr)

    rows = [
        {
            "label": rp.label,
            "area_px": int(rp.area),
            "area_um2": rp.area * px_area,
            "centroid_y_px": rp.centroid[0],
            "centroid_x_px": rp.centroid[1],
        }
        for rp in regionprops(filtered)
    ]
    table = pd.DataFrame(rows, columns=["label", "area_px", "area_um2",
                                        "centroid_y_px", "centroid_x_px"])
    return filtered, table


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("image", nargs="?", default="bf.tif")
    p.add_argument("--pixel-size", type=float, default=0.65, help="um per pixel")
    p.add_argument("--model", default=None, help="pretrained_model name; default = library default")
    p.add_argument("--diameter", type=float, default=None, help="None = no rescaling (library default)")
    p.add_argument("--flow-threshold", type=float, default=0.4)
    p.add_argument("--cellprob-threshold", type=float, default=0.0)
    p.add_argument("--min-size", type=int, default=15)
    p.add_argument("--no-normalize", action="store_true")
    p.add_argument("--min-area-um2", type=float, default=100.0)
    p.add_argument("--max-area-um2", type=float, default=800.0)
    p.add_argument("--min-solidity", type=float, default=0.85)
    p.add_argument("--out-labels", default="labels.tif")
    p.add_argument("--out-areas", default="areas.csv")
    a = p.parse_args()

    img = tifffile.imread(a.image)
    labels, table = segment_cancer_cells(
        img, a.pixel_size, model_name=a.model, diameter=a.diameter,
        normalize=not a.no_normalize, flow_threshold=a.flow_threshold,
        cellprob_threshold=a.cellprob_threshold, min_size=a.min_size,
        min_area_um2=a.min_area_um2, max_area_um2=a.max_area_um2,
        min_solidity=a.min_solidity,
    )
    tifffile.imwrite(a.out_labels, labels)
    table.to_csv(a.out_areas, index=False)
    print(f"Cells: {len(table)}; mean area {table.area_um2.mean():.1f} um^2"
          if len(table) else "No cells found.")


if __name__ == "__main__":
    main()
