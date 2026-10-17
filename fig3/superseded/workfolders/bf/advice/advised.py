"""The advice, implemented as given: Cellpose 4 (cpsam), grayscale, diameter calibrated by measuring cells (the advice's
example: 15-20 µm cells ~23-31 px; we use 27 px), flow 0.4. (a) cell probability 0 (default); (b) the advice's fix for
false positives on the endothelium: cell probability raised to 2, plus a size filter (10-30 µm equivalent diameter)."""
import numpy as np, tifffile
from cellpose import models
from skimage.measure import regionprops
img = tifffile.imread("<uploads>/cccf774d-BF.tif")
m = models.CellposeModel(gpu=False)
for tag, cp in (("a", 0.0), ("b", 2.0)):
    L, _, _ = m.eval(img, diameter=27, flow_threshold=0.4, cellprob_threshold=cp)
    if tag == "b":
        for r in regionprops(L):
            d = 2 * np.sqrt(r.area / np.pi) * 0.65
            if d < 10 or d > 30:
                L[L == r.label] = 0
    tifffile.imwrite(f"advised_{tag}.tif", L.astype(np.uint16)); print(tag, L.max(), flush=True)
