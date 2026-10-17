# Recovered verbatim from the session transcript (2026-10-16T11:10:05.474Z).
# Last shell command that wrote data4/A_scores.json. Paths are those of the original working folder.
cd <work2>/fig1 && cat > classical_seg.py <<'EOF'
"""Classical candidate for the reference-test-set comparison: local-contrast threshold pipeline on brightfield."""
import json
import numpy as np
import tifffile
from scipy import ndimage as ndi
from skimage import filters, morphology, segmentation, measure, feature
from compare_cancer_gt_lib import match

U = "<uploads>/"
bf = tifffile.imread(U + "cccf774d-BF.tif").astype(float)
ref = tifffile.imread(U + "e752a357-104_2.tif").astype(int)
g = filters.gaussian(bf, 1)
lv = ndi.generic_filter(g, np.std, size=7)                      # local standard deviation (texture of rounded cells)
m = lv > filters.threshold_otsu(lv)
m = morphology.binary_closing(m, morphology.disk(3))
m = ndi.binary_fill_holes(m)
m = morphology.remove_small_objects(m, 250)
m = morphology.binary_opening(m, morphology.disk(4))
d = ndi.distance_transform_edt(m)
pk = feature.peak_local_max(d, min_distance=12, labels=measure.label(m))
mk = np.zeros_like(d, int); mk[tuple(pk.T)] = np.arange(1, len(pk) + 1)
lab = segmentation.watershed(-d, mk, mask=m)
mt, fn, fp = match(ref, lab)
tp = len(mt); f1 = 2 * tp / (2 * tp + len(fn) + len(fp))
print("classical: objects", lab.max(), "TP", tp, "FN", len(fn), "FP", len(fp), "F1", round(f1, 3))
tifffile.imwrite("data8/classical_labels.tif", lab.astype(np.uint16))
sc = json.load(open("data4/A_scores.json")); sc["classical"] = round(f1, 3); json.dump(sc, open("data4/A_scores.json", "w"))
X, Y, W, H = 240, 40, 240, 260
sub = lab[Y:Y + H, X:X + W]; out = []
for l in np.unique(sub[sub > 0]):
    for c in measure.find_contours(np.pad(sub == l, 1).astype(float), 0.5):
        c = measure.approximate_polygon(c - 1, 0.6); out.append([[round(float(v[1]), 2), round(float(v[0]), 2)] for v in c])
json.dump({"w": W, "h": H, "contours": out}, open("data8/rep_classical.json", "w"))
EOF
timeout 600 python3 classical_seg.py
