#!/usr/bin/env python
"""Segment round refractile cancer cells in a brightfield image with Cellpose 4 (CPU).

Reads bf.tif (single-channel 2D uint16), writes labels.tif (uint32, same Y,X as input)
and areas.csv (areas in um^2). All consequential parameters are CLI arguments.
"""
import argparse
import sys

import numpy as np
import pandas as pd
import tifffile
from skimage import measure
from skimage.segmentation import relabel_sequential


def validate_image(img):
    if not isinstance(img, np.ndarray):
        raise TypeError("image must be a numpy array")
    if img.ndim != 2:
        raise ValueError(f"expected a 2D (Y, X) image, got shape {img.shape}. "
                         "Multi-page, multi-channel or RGB files are not accepted.")
    if img.dtype != np.uint16:
        raise ValueError(f"expected uint16 input, got {img.dtype}")
    if min(img.shape) < 64:
        raise ValueError(f"image too small: {img.shape}")
    if img.min() == img.max():
        raise ValueError("image is constant; nothing to segment")


def segment_cancer_cells(img, pixel_size_um=0.65, diameter=None,
                         flow_threshold=0.4, cellprob_threshold=0.0,
                         min_size=15, niter=None, resample=True,
                         tile_overlap=0.1, batch_size=8,
                         min_eq_diam_um=10.0, max_eq_diam_um=35.0,
                         min_contrast=None, pretrained_model=None, gpu=False):
    """Return (labels uint32 same shape as img, features DataFrame, log dict)."""
    validate_image(img)
    if not pixel_size_um > 0:
        raise ValueError("pixel_size_um must be > 0")
    if diameter is not None and not diameter > 0:
        raise ValueError("diameter must be None or > 0 (pixels)")
    if not (0 < min_eq_diam_um < max_eq_diam_um):
        raise ValueError("need 0 < min_eq_diam_um < max_eq_diam_um")

    from cellpose import models  # imported late so validation errors come first

    kw = {"gpu": gpu}
    if pretrained_model is not None:  # otherwise the library default model is used
        kw["pretrained_model"] = pretrained_model
    model = models.CellposeModel(**kw)
    model_used = pretrained_model or str(getattr(model, "pretrained_model", "library default"))

    masks, _flows, _styles = model.eval(
        img,                              # uint16 passed unchanged (no resize, no own normalisation)
        diameter=diameter,                # None -> no rescaling
        normalize=True,                   # Cellpose internal 1-99 percentile normalisation
        flow_threshold=flow_threshold,
        cellprob_threshold=cellprob_threshold,
        min_size=min_size,
        niter=niter,
        resample=resample,
        tile_overlap=tile_overlap,
        batch_size=batch_size,
    )
    masks = np.asarray(masks)
    if masks.shape != img.shape:
        raise RuntimeError(f"Cellpose returned shape {masks.shape}, expected {img.shape}; "
                           "refusing to continue (coordinate system would be wrong).")

    # Robust global intensity spread, used only for the contrast feature.
    f = img.astype(np.float64)
    sigma = 1.4826 * np.median(np.abs(f - np.median(f)))
    if sigma == 0:
        sigma = f.std() or 1.0

    px_area = pixel_size_um ** 2
    rows, keep = [], []
    n_raw = int(masks.max())
    rej_size = rej_contrast = 0
    H, W = img.shape
    for r in measure.regionprops(masks):
        area_um2 = r.area * px_area
        eq_d = 2.0 * np.sqrt(area_um2 / np.pi)
        vals = f[tuple(r.coords.T)]
        contrast = float(vals.std() / sigma)
        r0, c0, r1, c1 = r.bbox
        rows.append(dict(raw_label=r.label, area_px=int(r.area), area_um2=area_um2,
                         eq_diam_um=eq_d, centroid_y_px=r.centroid[0],
                         centroid_x_px=r.centroid[1], contrast=contrast,
                         touches_border=bool(r0 == 0 or c0 == 0 or r1 == H or c1 == W)))
        if not (min_eq_diam_um <= eq_d <= max_eq_diam_um):
            rej_size += 1
        elif min_contrast is not None and contrast < min_contrast:
            rej_contrast += 1
        else:
            keep.append(r.label)

    out = np.where(np.isin(masks, keep), masks, 0)
    out, _, _ = relabel_sequential(out)
    out = out.astype(np.uint32)

    df = pd.DataFrame(rows)
    df = df[df.raw_label.isin(keep)].reset_index(drop=True)
    df.insert(0, "label", np.arange(1, len(df) + 1))  # order preserved by regionprops, matches relabel
    df = df.drop(columns="raw_label")

    log = dict(model=model_used, n_cellpose=n_raw, rejected_size=rej_size,
               rejected_contrast=rej_contrast, n_final=len(df))
    return out, df, log


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--image", default="bf.tif")
    p.add_argument("--labels-out", default="labels.tif")
    p.add_argument("--areas-out", default="areas.csv")
    p.add_argument("--pixel-size-um", type=float, default=0.65)
    p.add_argument("--diameter", type=float, default=None,
                   help="pixels; default None = no rescaling (cells ~31 px already)")
    p.add_argument("--flow-threshold", type=float, default=0.4)
    p.add_argument("--cellprob-threshold", type=float, default=0.0)
    p.add_argument("--min-size", type=int, default=15)
    p.add_argument("--min-eq-diam-um", type=float, default=10.0)
    p.add_argument("--max-eq-diam-um", type=float, default=35.0)
    p.add_argument("--min-contrast", type=float, default=None,
                   help="optional; drop objects whose intensity std / image robust std is below this")
    p.add_argument("--pretrained-model", default=None, help="default: library default model")
    a = p.parse_args(argv)

    img = tifffile.imread(a.image)
    labels, df, log = segment_cancer_cells(
        img, pixel_size_um=a.pixel_size_um, diameter=a.diameter,
        flow_threshold=a.flow_threshold, cellprob_threshold=a.cellprob_threshold,
        min_size=a.min_size, min_eq_diam_um=a.min_eq_diam_um,
        max_eq_diam_um=a.max_eq_diam_um, min_contrast=a.min_contrast,
        pretrained_model=a.pretrained_model)
    tifffile.imwrite(a.labels_out, labels)
    df.to_csv(a.areas_out, index=False)
    print(log)
    print(f"cells: {log['n_final']}  mean area: {df.area_um2.mean():.1f} um^2" if len(df)
          else "no cells kept")
    print("NOTE: objects touching the border are included; their areas are underestimated "
          "(see touches_border column).")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, TypeError, RuntimeError, FileNotFoundError) as e:
        sys.exit(f"ERROR: {e}")
