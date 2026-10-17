"""User-chosen normalisations for the brightfield field (each written as float32 0-1; Cellpose-SAM then runs with its own
normalisation switched off, so the chosen normalisation is the one the model sees).
Usage: python norm_inputs.py [--field N]   (default field 104 -> panels/; other fields -> panels/fieldN/)"""
import sys
from pathlib import Path

import numpy as np
import tifffile
from skimage import exposure

from common.paths import RAW as U
FIELD = int(sys.argv[2]) if sys.argv[1:2] == ["--field"] else 104
OUT = Path("panels") if FIELD == 104 else Path("panels") / f"field{FIELD}"
OUT.mkdir(exist_ok=True)
bf = tifffile.imread(U + f"field{FIELD}_brightfield.tif").astype(np.float64)
if bf.max() <= bf.min():
    raise ValueError("constant image: min-max normalisation undefined")
mm = (bf - bf.min()) / (bf.max() - bf.min())
tifffile.imwrite(OUT / "in_minmax.tif", mm.astype(np.float32))
tifffile.imwrite(OUT / "in_histeq.tif", exposure.equalize_hist(bf, nbins=4096).astype(np.float32))
tifffile.imwrite(OUT / "in_clahe.tif", exposure.equalize_adapthist(mm, clip_limit=0.01).astype(np.float32))   # skimage defaults
print("ok", bf.min(), bf.max())
