"""Post-processing for Cellpose-SAM: drop flat, low-contrast objects (the endothelial monolayer), keep rounded cancer cells.
Contrast = mean local s.d. (7 px window) of the Gaussian-smoothed (sigma 1) brightfield inside each object."""
import argparse
import numpy as np
import tifffile
from scipy import ndimage as ndi
from skimage.measure import regionprops
from errors import errors

from common.paths import RAW as U
from common.labels import read_labels
bf = tifffile.imread(U + "field104_brightfield.tif").astype(float)
lsd = ndi.generic_filter(ndi.gaussian_filter(bf, 1), np.std, size=7)


def postfilter(L, thr):
    keep = [r.label for r in regionprops(L, intensity_image=lsd) if r.intensity_mean >= thr]
    return np.where(np.isin(L, keep), L, 0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Filter Cellpose-SAM objects by local contrast.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--threshold", type=float, help="write panels/cp_postfilter.tif with this contrast threshold (figure: 50)")
    mode.add_argument("--scan", action="store_true", help="print error counts for thresholds 30-70; writes nothing")
    args = parser.parse_args()
    L = read_labels("../../fig1/source_data/full_field_labels/cellpose_sam_labels.tif")
    if args.scan:
        for thr in [30, 40, 50, 60, 70]:
            print(thr, errors(postfilter(L, thr))[0])
    else:
        out = postfilter(L, args.threshold)
        print(args.threshold, errors(out)[0])
        tifffile.imwrite("panels/cp_postfilter.tif", out.astype(np.uint16), compression="zlib")  # lossless, as stored
