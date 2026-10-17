"""Panel A: StarDist (custom) vs Cellpose-SAM (generalist) against the manual cancer-cell reference, whole field."""
import json
import numpy as np
import tifffile
from skimage.measure import find_contours, approximate_polygon
from common.matching import match

from common.paths import RAW as U
from fig1_paths import CELLPOSE_LABELS
ref = tifffile.imread(U + "field104_cancer_cells_manual_labels.tif").astype(int)
models_ = {"stardist": tifffile.imread(U + "field104_cancer_cells_stardist_custom_labels.tif").astype(int),
           "cellpose": tifffile.imread(CELLPOSE_LABELS).astype(int)}
scores = {}
for k, L in models_.items():
    m, fn, fp = match(ref, L)
    tp = len(m)
    scores[k] = round(2 * tp / (2 * tp + len(fp) + len(fn)), 3)
    print(f"{k:9s} objects {len(np.unique(L))-1:3d}  TP {tp}  FP {len(fp)}  FN {len(fn)}  F1 {scores[k]}  "
          f"mean IoU {np.mean([x[2] for x in m]):.3f}")
json.dump(scores, open("panel_c_step3/A_scores.json", "w"))
X, Y, W, H = 200, 0, 210, 280
sub = models_["cellpose"][Y:Y + H, X:X + W]
out = []
for l in np.unique(sub[sub > 0]):
    msk = np.pad(sub == l, 1)
    for cnt in find_contours(msk.astype(float), 0.5):
        cnt = approximate_polygon(cnt - 1, tolerance=0.6)
        out.append([[round(float(c), 2), round(float(r), 2)] for r, c in cnt])
json.dump({"w": W, "h": H, "contours": out}, open("panel_c_step3/A_cellpose_contours.json", "w"))
print("Cellpose objects in crop:", len(np.unique(sub)) - 1, "| missed-by-both cell (183,230) Cellpose label:", int(sub[230, 183]))
