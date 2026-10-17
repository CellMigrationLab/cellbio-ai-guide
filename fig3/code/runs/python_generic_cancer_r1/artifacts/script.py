#!/usr/bin/env python3
"""
Segment round, phase-bright cancer cells in a brightfield image.

Input : bf.tif
Output: labels.tif  (uint16 label image, 0 = background, 1..N = cells)

Requirements: pip install numpy scipy scikit-image tifffile

Strategy (classical, no training):
  1. Flat-field / background removal (the illumination is uneven).
  2. Local-contrast map: round cancer cells have a strong dark rim and bright
     halo, while the flat monolayer underneath has weak contrast.
  3. Threshold, fill holes, clean up.
  4. Split touching cells with a distance-transform watershed.
  5. Reject debris (too small), saturated blobs and non-round objects.
"""

import numpy as np
import tifffile
from scipy import ndimage as ndi
from skimage import color, filters, measure, morphology, segmentation, feature

# ----------------------------- PARAMETERS ---------------------------------
IN_FILE  = "bf.tif"
OUT_FILE = "labels.tif"

BG_SIGMA        = 40     # px, scale of illumination background (>> cell size)
CONTRAST_SIGMA  = 2.0    # px, smoothing of the local-contrast map
THRESH_FACTOR   = 1.0    # multiply Otsu threshold; lower = more sensitive
CLOSE_RADIUS    = 3      # px, closes gaps in the dark rim
OPEN_RADIUS     = 3      # px, removes thin debris / filaments
MIN_AREA        = 200    # px^2, smaller objects are debris
MAX_AREA        = 2500   # px^2, larger objects are clumps/artefacts
MIN_DIST        = 9      # px, min distance between cell centres in watershed
MIN_SOLIDITY    = 0.85   # reject ragged, non-round objects (debris clusters)
MAX_ECCENTRICITY = 0.9   # reject very elongated objects
SATURATION_FRAC = 0.30   # reject objects with >30% near-saturated pixels
# ---------------------------------------------------------------------------


def load_gray(path):
    img = tifffile.imread(path)
    img = np.squeeze(img)
    if img.ndim == 3:
        if img.shape[-1] in (3, 4):          # RGB(A) image
            img = color.rgb2gray(img[..., :3])
        else:                                # z/time stack: use first plane
            print(f"Stack of shape {img.shape} detected, using first plane.")
            img = img[0]
    img = img.astype(np.float32)
    lo, hi = np.percentile(img, (0.5, 99.5))
    return np.clip((img - lo) / (hi - lo + 1e-9), 0, 1)


def main():
    img = load_gray(IN_FILE)

    # 1. Remove uneven illumination
    bg = filters.gaussian(img, BG_SIGMA)
    flat = img - bg

    # 2. Local-contrast map: magnitude of deviation from background plus
    #    local gradient magnitude, both emphasise the rim/halo of round cells.
    dev = np.abs(flat)
    grad = filters.sobel(filters.gaussian(img, 1.0))
    contrast = filters.gaussian(dev + 2.0 * grad, CONTRAST_SIGMA)

    # 3. Threshold and build a foreground mask
    t = filters.threshold_otsu(contrast) * THRESH_FACTOR
    mask = contrast > t
    mask = morphology.binary_closing(mask, morphology.disk(CLOSE_RADIUS))
    mask = ndi.binary_fill_holes(mask)
    mask = morphology.binary_opening(mask, morphology.disk(OPEN_RADIUS))
    mask = morphology.remove_small_objects(mask, MIN_AREA)

    # 4. Split touching cells (watershed on the distance transform)
    dist = ndi.distance_transform_edt(mask)
    dist = filters.gaussian(dist, 1.0)
    peaks = feature.peak_local_max(
        dist, min_distance=MIN_DIST, labels=measure.label(mask),
        exclude_border=False,
    )
    markers = np.zeros(mask.shape, dtype=np.int32)
    markers[tuple(peaks.T)] = np.arange(1, len(peaks) + 1)
    ws = segmentation.watershed(-dist, markers, mask=mask)

    # 5. Filter objects: size, roundness, saturated blobs
    sat = img > 0.98
    out = np.zeros(ws.shape, dtype=np.uint16)
    n = 0
    for r in measure.regionprops(ws):
        if not (MIN_AREA <= r.area <= MAX_AREA):
            continue
        if r.solidity < MIN_SOLIDITY or r.eccentricity > MAX_ECCENTRICITY:
            continue
        rr, cc = r.coords[:, 0], r.coords[:, 1]
        if sat[rr, cc].mean() > SATURATION_FRAC:
            continue
        n += 1
        out[rr, cc] = n

    tifffile.imwrite(OUT_FILE, out)
    print(f"Saved {n} cells to {OUT_FILE}")


if __name__ == "__main__":
    main()
