"""Panel c tiles: brightfield window plus reference / StarDist / filtered Cellpose-SAM outlines and error markers."""
import json
import numpy as np
import tifffile
from PIL import Image
from export_window import export, centroids
from errors import errors

from common.paths import RAW as U
X, Y, W, H = 40, 40, 240, 260
bf = tifffile.imread(U + "field104_brightfield.tif").astype(float)
lo, hi = np.percentile(bf, [0.3, 99.7])
g = np.round(np.clip((bf[Y:Y + H, X:X + W] - lo) / (hi - lo), 0, 1) * 255).astype(np.uint8)
Image.fromarray(np.repeat(np.repeat(g, 2, 0), 2, 1)).save("data/err_bf.png")
ref = tifffile.imread(U + "field104_cancer_cells_manual_labels.tif").astype(int)
sd = tifffile.imread(U + "field104_cancer_cells_stardist_custom_labels.tif").astype(int)
cp = tifffile.imread("data/cp_postfilter.tif").astype(int)
export(ref, X, Y, W, H, "data/err_ref.json")
export(sd, X, Y, W, H, "data/err_stardist.json")
export(cp, X, Y, W, H, "data/err_cellpose_filtered.json")
_, ids_sd = errors(sd)
_, ids_cp = errors(cp)
json.dump({"stardist": {"missed": centroids(ref, ids_sd["missed"], X, Y, W, H), "false": centroids(sd, ids_sd["false"], X, Y, W, H)},
           "cellpose_filtered": {"missed": centroids(ref, ids_cp["missed"], X, Y, W, H), "false": centroids(cp, ids_cp["false"], X, Y, W, H)}},
          open("data/err_markers.json", "w"), indent=1)
print(json.load(open("data/err_markers.json")))
