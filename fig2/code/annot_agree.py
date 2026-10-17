"""Panel a, reference agreement: two people's cell outlines (drawn on the acquired PECAM-1 image) compared with each
other. Outline drawings are turned into cell instances by common/annotations.lines_to_cells:
regions enclosed by the lines, line pixels returned to neighbours, border cells and slivers < 150 px removed.
Scores: object F1 at IoU >= 0.5 (greedy one-to-one); biological result: cell count and mean cell area."""
import json, os
import numpy as np
import tifffile
from common.matching import match
from export_window import export

from common.annotations import lines_to_cells
from common.stats import finite_values
from common.paths import RAW as U
from common.metadata import FOLLAIN_PX_UM as PX




a1 = lines_to_cells(tifffile.imread(U + "field104_endothelial_junctions_annotator1.tif") > 0)
a2 = lines_to_cells(tifffile.imread(U + "field104_endothelial_junctions_annotator2.tif") > 0)
src = {"annotator 1": a1, "annotator 2": a2}
# Model comparison (Cellpose on acquired PECAM-1, panels/cp_pecam.tif) was dropped from the final figure and its labels
# are not stored; the two annotators are compared only. Fail if the file appears, so the outputs are not changed silently.
if os.path.exists("panels/cp_pecam.tif"):
    raise RuntimeError("panels/cp_pecam.tif is present: the published annot_agree.json compares the annotators only")


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
    areas = finite_values(areas, name=f"{k} areas")
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
