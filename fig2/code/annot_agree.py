"""Panel b: two people's cell outlines (drawn on the acquired PECAM-1 image) vs each other and vs Cellpose-SAM run on the
same acquired image. Outline drawings are turned into cell instances as in Fig. 1 work (compare_annotations.py):
regions enclosed by the lines, line pixels returned to neighbours, border cells and slivers < 150 px removed.
Scores: object F1 at IoU >= 0.5 (greedy one-to-one); biological result: cell count and mean cell area."""
import json, os
import numpy as np
import tifffile
from skimage.measure import label
from skimage.segmentation import clear_border, expand_labels
from common.matching import match
from export_window import export

from common.paths import RAW as U
PX = 0.649614


def lines_to_cells(lines):
    lab = expand_labels(label(~lines, connectivity=1), 2)
    lab = clear_border(lab)
    sizes = np.bincount(lab.ravel())
    lab[np.isin(lab, np.where(sizes < 150)[0])] = 0
    return lab


a1 = lines_to_cells(tifffile.imread(U + "field104_endothelial_junctions_annotator1.tif") > 0)
a2 = lines_to_cells(tifffile.imread(U + "field104_endothelial_junctions_annotator2.tif") > 0)
src = {"annotator 1": a1, "annotator 2": a2}
if os.path.exists("panels/cp_pecam.tif"):
    m = clear_border(tifffile.imread("panels/cp_pecam.tif").astype(int))
    src["model"] = m


def f1(g, p):
    mt, fn, fp = match(g, p, 0.5)
    return round(2 * len(mt) / (2 * len(mt) + len(fn) + len(fp)), 3)


out = {"pairs": {}, "bio": {}}
names = list(src)
for i in range(len(names)):
    for j in range(i + 1, len(names)):
        out["pairs"][f"{names[i]} vs {names[j]}"] = f1(src[names[i]], src[names[j]])
for k, L in src.items():
    ids, areas = np.unique(L[L > 0], return_counts=True)
    out["bio"][k] = {"count": int(len(ids)), "mean_area_um2": round(float(areas.mean() * PX ** 2), 1)}
json.dump(out, open("panels/annot_agree.json", "w"), indent=1)
print(out)
# tile window with clear junctions (full-field px)
X, Y, W, H = 200, 0, 260, 280
g = tifffile.imread(U + "field104_pecam1.tif").astype(float)
lo, hi = np.percentile(g[Y:Y + H, X:X + W], [0.3, 99.7])
from PIL import Image
t = np.clip((g[Y:Y + H, X:X + W] - lo) / (hi - lo), 0, 1)
rgb = np.stack([t * 0.15, t, t * 0.3], -1)
Image.fromarray(np.round(np.repeat(np.repeat(rgb, 2, 0), 2, 1) * 255).astype(np.uint8)).save("panels/pecam_tile.png")
for k, L in src.items():
    export(L, X, Y, W, H, f"panels/pecam_{k.replace(' ', '')}.json")
