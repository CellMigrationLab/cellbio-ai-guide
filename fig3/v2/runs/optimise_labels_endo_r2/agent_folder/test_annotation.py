"""python test_annotation.py <labels.tif> <annotation.tif>
Scores prediction vs manual annotation (only cells whose centroid lies in the annotated region)."""
import sys, numpy as np, tifffile as t
from scipy import ndimage as ndi
from skimage import measure, morphology
pr, gt = t.imread(sys.argv[1]), t.imread(sys.argv[2])
roi = ndi.binary_fill_holes(morphology.binary_closing(gt > 0, morphology.disk(25)))
for r in measure.regionprops(pr):
    if not roi[tuple(int(c) for c in r.centroid)]: pr = np.where(pr == r.label, 0, pr)
m = (gt > 0) & (pr > 0)
pairs, c = np.unique(np.stack([gt[m], pr[m]]), axis=1, return_counts=True)
ga = dict(zip(*np.unique(gt, return_counts=True))); pa = dict(zip(*np.unique(pr, return_counts=True)))
mt = [(g, p) for (g, p), i in zip(pairs.T, c) if i / (ga[g] + pa[p] - i) >= 0.5]
ng, npr, tp = len(ga) - 1, len(pa) - 1, len(mt)
G = {r.label: r for r in measure.regionprops(gt)}; P = {r.label: r for r in measure.regionprops(pr)}
f1 = 2 * tp / (ng + npr)
cnt = npr / ng
am = np.median([P[p].area for _, p in mt]) / np.median([G[g].area for g, _ in mt])
ard = np.median([P[p].axis_major_length / P[p].axis_minor_length - G[g].axis_major_length / G[g].axis_minor_length for g, p in mt])
print(f"GT {ng} pred {npr} matched {tp}  F1@IoU0.5 {f1:.3f}  count ratio {cnt:.2f}  matched area ratio {am:.2f}  matched AR diff {ard:+.2f}")
ok = f1 >= 0.65 and 0.8 <= cnt <= 1.2 and 0.85 <= am <= 1.15 and abs(ard) <= 0.2
print("PASS" if ok else "FAIL (F1<0.65, count off >20%, area bias >15%, or AR bias >0.2)")
