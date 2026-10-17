"""Post-processing for Cellpose-SAM: drop flat, low-contrast objects (the endothelial monolayer), keep rounded cancer cells.
Contrast = mean local s.d. (7 px window) of the Gaussian-smoothed (sigma 1) brightfield inside each object."""
import sys
import numpy as np
import tifffile
from scipy import ndimage as ndi
from skimage.measure import regionprops
from errors import errors

from common.paths import RAW as U
bf = tifffile.imread(U + "field104_brightfield.tif").astype(float)
lsd = ndi.generic_filter(ndi.gaussian_filter(bf, 1), np.std, size=7)


def postfilter(L, thr):
    keep = [r.label for r in regionprops(L, intensity_image=lsd) if r.intensity_mean >= thr]
    return np.where(np.isin(L, keep), L, 0)


if __name__ == "__main__":
    L = tifffile.imread("../../fig1/source_data/full_field_labels/cellpose_sam_labels.tif").astype(int)
    for thr in [30, 40, 50, 60, 70]:
        print(thr, errors(postfilter(L, thr))[0])
    if len(sys.argv) > 1:
        thr = float(sys.argv[1])
        tifffile.imwrite("panels/cp_postfilter.tif", postfilter(L, thr).astype(np.uint16))
