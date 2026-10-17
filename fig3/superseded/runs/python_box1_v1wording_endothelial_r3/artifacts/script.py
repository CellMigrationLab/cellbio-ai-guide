#!/usr/bin/env python
"""Segment endothelial cells in a single-channel 2D brightfield image with Cellpose.

Usage: python segment_endothelial.py bf.tif labels.tif areas.csv
"""
import argparse
import sys
from importlib.metadata import version

import numpy as np
import pandas as pd
import tifffile
from skimage.measure import regionprops_table
from skimage.segmentation import relabel_sequential

EXPECTED_CELLPOSE = "4.2.1.1"


def validate_image(img, pixel_size_um):
    if not isinstance(img, np.ndarray) or img.ndim != 2:
        raise ValueError(f"Expected a 2D (Y, X) image, got shape {getattr(img, 'shape', None)}. "
                         "Not squeezing or picking channels automatically.")
    if img.dtype != np.uint16:
        raise ValueError(f"Expected 16-bit (uint16) image, got {img.dtype}.")
    if img.size == 0 or img.min() == img.max():
        raise ValueError("Image is empty or constant; nothing to segment.")
    if not (pixel_size_um > 0):
        raise ValueError("pixel_size_um must be > 0.")


def segment(img, pixel_size_um=0.65, diameter_um=37.5, flow_threshold=0.4,
            cellprob_threshold=0.0, min_size=15, min_diam_um=25.0,
            max_circularity=None, exclude_border=False, model_name=None):
    """Return (labels, table). labels has the same shape as img (uint32, 0 = background).

    diameter_um: expected endothelial cell diameter; 0 or None -> no diameter rescaling.
    """
    validate_image(img, pixel_size_um)
    from cellpose import models

    installed = version("cellpose")
    if installed != EXPECTED_CELLPOSE:
        print(f"WARNING: cellpose {installed} installed, script written for {EXPECTED_CELLPOSE}",
              file=sys.stderr)

    diameter_px = float(diameter_um) / pixel_size_um if diameter_um else None
    kwargs = {"gpu": False}
    if model_name:
        kwargs["pretrained_model"] = model_name  # otherwise library default
    model = models.CellposeModel(**kwargs)
    print(f"cellpose {installed}; model: {getattr(model, 'pretrained_model', 'unknown')}; "
          f"diameter_px={diameter_px}", file=sys.stderr)

    masks, _flows, _styles = model.eval(
        img,
        diameter=diameter_px,
        flow_threshold=flow_threshold,
        cellprob_threshold=cellprob_threshold,
        min_size=min_size,
        normalize=True,   # library default: 1st-99th percentile, done inside Cellpose
        resample=True,    # library default: dynamics at original size
    )
    masks = np.asarray(masks)
    if masks.shape != img.shape:
        raise RuntimeError(f"Output shape {masks.shape} != input shape {img.shape}.")

    # Post-filter in physical units (Cellpose cannot exclude the round cancer cells itself)
    props = pd.DataFrame(regionprops_table(
        masks, properties=("label", "area", "perimeter", "centroid", "bbox")))
    props["area_um2"] = props["area"] * pixel_size_um ** 2
    props["equiv_diam_um"] = 2 * np.sqrt(props["area_um2"] / np.pi)
    props["circularity"] = 4 * np.pi * props["area"] / np.maximum(props["perimeter"], 1) ** 2
    h, w = img.shape
    props["touches_border"] = ((props["bbox-0"] == 0) | (props["bbox-1"] == 0) |
                               (props["bbox-2"] == h) | (props["bbox-3"] == w))
    drop = props["equiv_diam_um"] < min_diam_um
    if max_circularity is not None:
        drop |= props["circularity"] > max_circularity
    if exclude_border:
        drop |= props["touches_border"]
    print(f"Cellpose objects: {len(props)}; removed by filters: {int(drop.sum())}", file=sys.stderr)

    masks = masks.astype(np.uint32)
    masks[np.isin(masks, props.loc[drop, "label"].to_numpy())] = 0
    masks, _, _ = relabel_sequential(masks)
    masks = masks.astype(np.uint32)

    kept = props.loc[~drop].reset_index(drop=True)
    table = pd.DataFrame({
        "label": np.arange(1, len(kept) + 1),
        "area_px": kept["area"].astype(int),
        "area_um2": kept["area_um2"],
        "centroid_y_px": kept["centroid-0"],
        "centroid_x_px": kept["centroid-1"],
        "touches_border": kept["touches_border"],
    })
    return masks, table


def main():
    p = argparse.ArgumentParser()
    p.add_argument("image", nargs="?", default="bf.tif")
    p.add_argument("labels", nargs="?", default="labels.tif")
    p.add_argument("areas", nargs="?", default="areas.csv")
    p.add_argument("--pixel-size", type=float, default=0.65, help="um per pixel")
    p.add_argument("--diameter-um", type=float, default=37.5,
                   help="expected cell diameter in um; 0 = no rescaling")
    p.add_argument("--flow-threshold", type=float, default=0.4)
    p.add_argument("--cellprob-threshold", type=float, default=0.0)
    p.add_argument("--min-size", type=int, default=15, help="Cellpose min_size (px)")
    p.add_argument("--min-diam-um", type=float, default=25.0,
                   help="drop objects with smaller equivalent diameter (cancer-cell filter)")
    p.add_argument("--max-circularity", type=float, default=None)
    p.add_argument("--exclude-border", action="store_true")
    p.add_argument("--model", default=None, help="pretrained_model; default = library default")
    a = p.parse_args()

    img = tifffile.imread(a.image)
    labels, table = segment(img, a.pixel_size, a.diameter_um, a.flow_threshold,
                            a.cellprob_threshold, a.min_size, a.min_diam_um,
                            a.max_circularity, a.exclude_border, a.model)
    tifffile.imwrite(a.labels, labels)
    table.to_csv(a.areas, index=False)
    print(f"{len(table)} endothelial cells; median area {table['area_um2'].median():.0f} um2"
          if len(table) else "0 cells found")


if __name__ == "__main__":
    main()
