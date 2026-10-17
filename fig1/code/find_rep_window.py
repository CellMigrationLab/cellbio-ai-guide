"""Find a window where StarDist vs Cellpose-SAM errors match the whole-field picture (scores and error types)."""
import json
import numpy as np
import tifffile
from skimage.measure import regionprops
from common.matching import match

from common.paths import RAW as U
from fig1_paths import CELLPOSE_LABELS
ref = tifffile.imread(U + "field104_cancer_cells_manual_labels.tif").astype(int)
sd = tifffile.imread(U + "field104_cancer_cells_stardist_custom_labels.tif").astype(int)
cp = tifffile.imread(CELLPOSE_LABELS).astype(int)
cent = lambda L: {r.label: r.centroid for r in regionprops(L)}
cr, cs, cc = cent(ref), cent(sd), cent(cp)
ms, fn_s, fp_s = match(ref, sd)
mc, fn_c, fp_c = match(ref, cp)
print("CP extras: area px (median, min, max):", np.median([np.sum(cp == l) for l in fp_c]), min(np.sum(cp == l) for l in fp_c), max(np.sum(cp == l) for l in fp_c))
print("matched ref cell area median:", np.median([np.sum(ref == g) for g, _, _ in mc]))
W_, H_ = 150, 162
res = []
for y in range(0, 1022 - H_, 6):
    for x in range(0, 1024 - W_, 6):
        inside = lambda c: y + 8 <= c[0] < y + H_ - 8 and x + 8 <= c[1] < x + W_ - 8
        nref = sum(inside(c) for c in cr.values())
        if nref < 7:
            continue
        sfn = sum(inside(cr[l]) for l in fn_s); sfp = sum(inside(cs[l]) for l in fp_s)
        cfn = sum(inside(cr[l]) for l in fn_c); cfp = sum(inside(cc[l]) for l in fp_c)
        f1 = lambda fn, fp: 2 * (nref - fn) / (2 * (nref - fn) + fn + fp)
        fs, fc = f1(sfn, sfp), f1(cfn, cfp)
        score = abs(fs - 0.86) + abs(fc - 0.78) + 0.05 * (sfn == 0) + 0.05 * (cfp == 0)
        res.append((round(score, 3), x, y, nref, sfn, sfp, cfn, cfp, round(fs, 2), round(fc, 2)))
res.sort()
keep = []
for r in res:
    if all(abs(r[1] - k[1]) > 100 or abs(r[2] - k[2]) > 100 for k in keep):
        keep.append(r)
    if len(keep) == 6:
        break
print("score, x, y, nref, SD missed, SD extra, CP missed, CP extra, F1 SD, F1 CP")
for k in keep:
    print(k)
json.dump([[float(v) for v in k] for k in keep], open("panel_c_step3/rep_windows.json", "w"))
