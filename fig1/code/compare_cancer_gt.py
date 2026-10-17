"""Compare StarDist cancer-cell labels (on BF) with the manual cancer-cell reference (104_2.tif)."""
import numpy as np
import tifffile
from PIL import Image
from skimage.segmentation import clear_border, find_boundaries

from common.paths import RAW as U
gt = tifffile.imread(U + "field104_cancer_cells_manual_labels.tif").astype(int)
sd = tifffile.imread(U + "field104_cancer_cells_stardist_custom_labels.tif").astype(int)
bf = tifffile.imread(U + "field104_brightfield.tif").astype(float)


def match(gt, pr, thr=0.5):
    m = (gt > 0) & (pr > 0)
    pairs = {}
    for g, p in zip(gt[m], pr[m]):
        pairs[(g, p)] = pairs.get((g, p), 0) + 1
    ga = dict(zip(*np.unique(gt[gt > 0], return_counts=True)))
    pa = dict(zip(*np.unique(pr[pr > 0], return_counts=True)))
    ious = sorted(((n / (ga[g] + pa[p] - n), g, p) for (g, p), n in pairs.items()), reverse=True)
    ug, up, matched = set(), set(), []
    for iou, g, p in ious:
        if iou >= thr and g not in ug and p not in up:
            ug.add(g); up.add(p); matched.append((g, p, iou))
    return matched, set(ga) - ug, set(pa) - up


for name, G, P in [("whole field", gt, sd), ("whole field, edge cells removed", clear_border(gt.copy()), clear_border(sd.copy()))]:
    m, fn, fp = match(G, P)
    tp = len(m)
    print(f"{name:34s} GT {len(np.unique(G))-1:3d}  StarDist {len(np.unique(P))-1:3d}  TP {tp}  FP {len(fp)}  FN {len(fn)}  "
          f"F1 {2*tp/(2*tp+len(fp)+len(fn)):.3f}  mean IoU {np.mean([x[2] for x in m]):.3f}")

X, Y, W, H = 200, 0, 210, 280
m, fn, fp = match(gt, sd)
g, s = gt[Y:Y + H, X:X + W], sd[Y:Y + H, X:X + W]
print("crop: GT objects", len(np.unique(g)) - 1, "StarDist", len(np.unique(s)) - 1,
      "| GT missed by StarDist in crop:", sorted(int(l) for l in fn if (g == l).any()),
      "| StarDist FP in crop:", sorted(int(l) for l in fp if (s == l).any()))
lo, hi = np.percentile(bf[Y:Y + H, X:X + W], [0.3, 99.7])
b = np.clip((bf[Y:Y + H, X:X + W] - lo) / (hi - lo), 0, 1)
o = np.stack([b] * 3, -1)
o[find_boundaries(g, mode="inner")] = [0.1, 0.8, 1]
o[find_boundaries(s, mode="inner")] = [1, 0.2, 0.6]
Image.fromarray((np.repeat(np.repeat(o, 3, 0), 3, 1) * 255).astype(np.uint8)).save("data4/cancer_gt_vs_stardist_crop.png")

# panel A "check" image: StarDist vs manual reference outlines on the shared crop (no error colouring), 3x nearest
from scipy import ndimage as ndi
UP = 3
up = lambda a: np.repeat(np.repeat(a, UP, 0), UP, 1)
gU, sU = up(g), up(s)
base = up(b)
o = np.stack([0.2 + 0.7 * base] * 3, -1)
missed = np.isin(gU, [l for l in fn if (g == l).any()])
extra = np.isin(sU, [l for l in fp if (s == l).any()])
thick = lambda m: ndi.binary_dilation(m, iterations=1)
o[thick(find_boundaries(gU, mode="inner"))] = [0.15, 0.78, 1.0]   # manual: cyan
o[thick(find_boundaries(sU, mode="inner"))] = [1.0, 0.24, 0.82]   # StarDist: magenta
Image.fromarray(np.round(o * 255).astype(np.uint8)).save("data4/A_check_overlay.png", optimize=True)
print("check overlay: missed in crop", int(len([l for l in fn if (g == l).any()])), "extra in crop", int(len([l for l in fp if (s == l).any()])))
