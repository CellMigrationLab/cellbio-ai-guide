#!/usr/bin/env python3
"""Nuclear segmentation (2D, single channel) -> labels.tif + areas.csv.

Usage:
    python segment_nuclei.py                 # runs on nuclei.tif with defaults
    python segment_nuclei.py --test          # runs the built-in synthetic test

ASSUMPTIONS TO VERIFY ON REAL DATA
1.  nuclei.tif is a single 2D plane with axes (Y, X). A stack, RGB or extra
    singleton axes are rejected rather than squeezed or guessed.
2.  The image is the DAPI channel, nuclei are brighter than background, and
    illumination is roughly flat. A global threshold fails with strong vignetting
    or uneven background; use background correction first if so.
3.  The image is not saturated and is not already normalised. Raw intensities
    are used as-is (no rescaling); only the smoothed copy used for thresholding
    is float.
4.  Pixel size is 0.65 um/px, isotropic (same in X and Y). The value is passed
    explicitly and is not read from the TIFF metadata. Check they agree.
5.  Otsu is a valid global threshold. It assumes a roughly bimodal histogram
    (background vs nuclei). Bright debris, mitotic or apoptotic cells, or
    very dim nuclei can shift it. Check overlays, and consider --threshold
    for a fixed value.
6.  Touching nuclei are split by distance-transform watershed, which assumes
    roughly convex, round-to-oval nuclei. Seeds are separated by at least
    --min-seed-distance-um (default 5 um, i.e. about half the smallest
    expected nucleus diameter). Check for over-splitting of elongated nuclei
    and under-splitting of heavily overlapping ones.
7.  Objects smaller than --min-area-um2 (default 20 um2, far below a 10 um
    diameter nucleus, about 78 um2) are treated as debris and removed.
    Check that this does not drop real small nuclei such as micronuclei or
    apoptotic fragments, if you want them.
8.  Nuclei touching the image border are kept by default, but their area is
    truncated. They are flagged in areas.csv (touches_border); decide whether
    to exclude them from statistics, or use --exclude-border to drop them.
9.  Area is the pixel count of the label times pixel_size^2. It is a 2D
    projected area, sensitive to threshold choice (the threshold sets the
    nuclear edge, so area is biased by blur and threshold level). Compare
    against a manual outline on several nuclei.
10. Labels are saved as uint16 (max 65535 objects); the script fails
    if exceeded. Label image has the same (Y, X) shape as the input, so
    coordinates are unchanged.
"""
import argparse
import csv
import sys
import tempfile
from pathlib import Path

import numpy as np
import tifffile
from scipy import ndimage as ndi
from skimage import filters, measure, segmentation, feature


def segment_nuclei(image, pixel_size_um, sigma_um=0.65, threshold=None,
                   min_seed_distance_um=5.0, min_area_um2=20.0,
                   exclude_border=False):
    """Segment nuclei in a 2D (Y, X) image.

    Parameters
    ----------
    image : ndarray, shape (Y, X), numeric
    pixel_size_um : float, um per pixel (isotropic), > 0
    sigma_um : Gaussian smoothing sigma in um, used only for thresholding and
        mask creation (intensities of the input are never modified). 0 disables.
    threshold : float or None. None -> Otsu on the smoothed image (skimage
        threshold_otsu). Otherwise a fixed value in the image's own intensity units.
    min_seed_distance_um : minimum distance between watershed seeds (um).
    min_area_um2 : objects smaller than this are removed.
    exclude_border : drop objects touching the image edge.

    Returns
    -------
    labels : int32 ndarray, shape (Y, X), 0 = background, same grid as input.
    """
    image = np.asarray(image)
    if image.ndim != 2:
        raise ValueError(f"Expected a 2D (Y, X) image, got shape {image.shape}.")
    if image.size == 0 or min(image.shape) < 3:
        raise ValueError(f"Image too small: shape {image.shape}.")
    if not (np.issubdtype(image.dtype, np.integer) or np.issubdtype(image.dtype, np.floating)):
        raise ValueError(f"Unsupported dtype {image.dtype}; need integer or float.")
    if not np.all(np.isfinite(image)):
        raise ValueError("Image contains NaN or infinite values.")
    if not (np.isfinite(pixel_size_um) and pixel_size_um > 0):
        raise ValueError(f"pixel_size_um must be a positive finite number, got {pixel_size_um}.")
    if sigma_um < 0 or min_seed_distance_um <= 0 or min_area_um2 < 0:
        raise ValueError("sigma_um must be >= 0, min_seed_distance_um > 0, min_area_um2 >= 0.")
    if image.min() == image.max():
        raise ValueError("Image is constant; nothing to segment.")

    # Smooth (preserve_range=True keeps original intensity units; no rescaling).
    sigma_px = sigma_um / pixel_size_um
    if sigma_px > 0:
        smooth = filters.gaussian(image, sigma=sigma_px, preserve_range=True)
    else:
        smooth = image.astype(np.float64)

    thr = filters.threshold_otsu(smooth) if threshold is None else float(threshold)
    mask = smooth > thr
    mask = ndi.binary_fill_holes(mask)
    if not mask.any():
        raise RuntimeError(f"No pixels above threshold {thr:.4g}; check the threshold/image.")

    # Split touching nuclei: seeds = local maxima of the distance transform.
    dist = ndi.distance_transform_edt(mask)
    min_dist_px = max(1, int(round(min_seed_distance_um / pixel_size_um)))
    peaks = feature.peak_local_max(dist, min_distance=min_dist_px,
                                   labels=measure.label(mask),
                                   exclude_border=False)
    markers = np.zeros(image.shape, dtype=np.int32)
    markers[tuple(peaks.T)] = np.arange(1, len(peaks) + 1)
    labels = segmentation.watershed(-dist, markers=markers, mask=mask)

    # Remove small objects (and optionally border objects), then relabel 1..N.
    min_area_px = min_area_um2 / pixel_size_um ** 2
    keep = np.zeros(labels.max() + 1, dtype=bool)
    h, w = image.shape
    for r in measure.regionprops(labels):
        if r.area < min_area_px:
            continue
        r0, c0, r1, c1 = r.bbox
        if exclude_border and (r0 == 0 or c0 == 0 or r1 == h or c1 == w):
            continue
        keep[r.label] = True
    labels = np.where(keep[labels], labels, 0)
    labels, _, _ = segmentation.relabel_sequential(labels)
    if labels.max() == 0:
        raise RuntimeError("No nuclei left after size/border filtering.")
    return labels.astype(np.int32)


def measure_areas(labels, pixel_size_um):
    """Return rows of (label, area_px, area_um2, touches_border)."""
    h, w = labels.shape
    rows = []
    for r in measure.regionprops(labels):
        r0, c0, r1, c1 = r.bbox
        border = int(r0 == 0 or c0 == 0 or r1 == h or c1 == w)
        rows.append((r.label, int(r.area), r.area * pixel_size_um ** 2, border))
    return rows


def run(in_path, labels_path, csv_path, pixel_size_um, **kw):
    image = tifffile.imread(in_path)
    labels = segment_nuclei(image, pixel_size_um, **kw)
    if labels.max() > np.iinfo(np.uint16).max:
        raise RuntimeError("More than 65535 objects; cannot save as uint16.")
    assert labels.shape == image.shape
    tifffile.imwrite(labels_path, labels.astype(np.uint16))
    rows = measure_areas(labels, pixel_size_um)
    with open(csv_path, "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["label", "area_px", "area_um2", "touches_border"])
        wr.writerows(rows)
    print(f"{len(rows)} nuclei; median area {np.median([r[2] for r in rows]):.1f} um2")
    return labels


def test_segmentation():
    """Two touching synthetic nuclei (radius 7.5 um) + invalid-input checks."""
    px = 0.65
    yy, xx = np.mgrid[:200, :240]
    r_px = 7.5 / px
    d1 = (yy - 100) ** 2 + (xx - 100) ** 2 <= r_px ** 2
    d2 = (yy - 100) ** 2 + (xx - 120) ** 2 <= r_px ** 2  # overlapping neighbour
    img = np.full((200, 240), 100, dtype=np.uint16)
    img[d1 | d2] = 3000
    lab = segment_nuclei(img, px)
    assert lab.shape == img.shape
    assert lab.max() == 2, f"expected 2 nuclei, got {lab.max()}"
    union_um2 = (d1 | d2).sum() * px ** 2
    total_um2 = (lab > 0).sum() * px ** 2
    assert abs(total_um2 - union_um2) / union_um2 < 0.05
    for bad in (np.zeros((5, 10, 10)), np.full((50, 50), 7, dtype=np.uint16)):
        try:
            segment_nuclei(bad, px)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid input was not rejected")
    try:
        segment_nuclei(img, 0)
    except ValueError:
        pass
    else:
        raise AssertionError("pixel size 0 was not rejected")
    # round trip through files
    with tempfile.TemporaryDirectory() as d:
        tifffile.imwrite(Path(d) / "in.tif", img)
        out = run(Path(d) / "in.tif", Path(d) / "l.tif", Path(d) / "a.csv", px)
        assert out.max() == 2 and (Path(d) / "a.csv").exists()
    print("test passed")


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--input", default="nuclei.tif")
    p.add_argument("--labels-out", default="labels.tif")
    p.add_argument("--areas-out", default="areas.csv")
    p.add_argument("--pixel-size-um", type=float, default=0.65)
    p.add_argument("--sigma-um", type=float, default=0.65)
    p.add_argument("--threshold", type=float, default=None,
                   help="fixed threshold in image intensity units (default: Otsu)")
    p.add_argument("--min-seed-distance-um", type=float, default=5.0)
    p.add_argument("--min-area-um2", type=float, default=20.0)
    p.add_argument("--exclude-border", action="store_true")
    p.add_argument("--test", action="store_true")
    a = p.parse_args()
    if a.test:
        test_segmentation()
        return
    try:
        run(a.input, a.labels_out, a.areas_out, a.pixel_size_um,
            sigma_um=a.sigma_um, threshold=a.threshold,
            min_seed_distance_um=a.min_seed_distance_um,
            min_area_um2=a.min_area_um2, exclude_border=a.exclude_border)
    except (ValueError, RuntimeError, FileNotFoundError) as e:
        sys.exit(f"ERROR: {e}")


if __name__ == "__main__":
    main()
