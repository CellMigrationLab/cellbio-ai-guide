"""Row B example tiles: a window whose local scores match the whole field (find_rep_window.py)."""
import json
import numpy as np
import tifffile
from PIL import Image
from skimage.measure import find_contours, approximate_polygon

from common.paths import RAW as U
X, Y, W, H = 240, 40, 240, 260          # full-field px; local F1 StarDist 0.86, Cellpose-SAM 0.80 (whole field 0.86 / 0.78)
bf = tifffile.imread(U + "field104_brightfield.tif").astype(float)[Y:Y + H, X:X + W]
lo, hi = np.percentile(bf, [0.3, 99.7])
Image.fromarray(np.repeat(np.repeat(np.round(np.clip((bf - lo) / (hi - lo), 0, 1) * 255).astype(np.uint8), 2, 0), 2, 1)).save("panel_c_step3/B_rep_bf.png")
for name, L in [("ref", tifffile.imread(U + "field104_cancer_cells_manual_labels.tif")), ("stardist", tifffile.imread(U + "field104_cancer_cells_stardist_custom_labels.tif")),
                ("cellpose", tifffile.imread("panel_c_step3/BF_cellpose_sam_labels.tif"))]:
    sub = L.astype(int)[Y:Y + H, X:X + W]
    out = []
    for l in np.unique(sub[sub > 0]):
        m = np.pad(sub == l, 1)
        for c in find_contours(m.astype(float), 0.5):
            c = approximate_polygon(c - 1, tolerance=0.6)
            out.append([[round(float(v[1]), 2), round(float(v[0]), 2)] for v in c])
    json.dump({"w": W, "h": H, "contours": out}, open(f"panel_c_step3/B_rep_{name}.json", "w"))
print("ok")
