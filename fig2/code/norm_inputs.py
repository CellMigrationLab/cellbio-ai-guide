"""User-chosen normalisations for the brightfield field (each written as float32 0-1; Cellpose-SAM then runs with its own
normalisation switched off, so the chosen normalisation is the one the model sees)."""
import numpy as np
import tifffile
from skimage import exposure

from common.paths import RAW as U
bf = tifffile.imread(U + "field104_brightfield.tif").astype(np.float64)
mm = (bf - bf.min()) / (bf.max() - bf.min())
tifffile.imwrite("data/in_minmax.tif", mm.astype(np.float32))
tifffile.imwrite("data/in_histeq.tif", exposure.equalize_hist(bf, nbins=4096).astype(np.float32))
tifffile.imwrite("data/in_clahe.tif", exposure.equalize_adapthist(mm, clip_limit=0.01).astype(np.float32))   # skimage defaults
print("ok", bf.min(), bf.max())
