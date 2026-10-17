"""python evaluate.py <labels.tif> <annotation.tif>  -- F1@IoU0.5 (inside annotated hull), count, area, aspect ratio.
FAIL criteria printed at the end."""
import sys
import numpy as np, tifffile
from skimage.measure import regionprops
from skimage.morphology import convex_hull_image
PX = 0.65
def match(gt, pr, thr=0.5):
    roi = convex_hull_image(gt > 0); pr = np.where(roi, pr, 0)
    pairs = np.stack([gt[roi], pr[roi]], 1); pairs = pairs[(pairs > 0).all(1)]
    ids, n = np.unique(pairs, axis=0, return_counts=True)
    ga, pa = np.bincount(gt[roi]), np.bincount(pr[roi])
    iou = n / (ga[ids[:, 0]] + pa[ids[:, 1]] - n)
    tp = int((iou > thr).sum())
    ngt, npr = len(np.unique(gt[gt > 0])), len(np.unique(pr[pr > 0]))
    return tp, ngt, npr, ids[iou > thr]
def med(l, ids=None):
    r = [x for x in regionprops(l) if ids is None or x.label in ids]
    return (np.array([x.area for x in r]) * PX**2, np.array([x.axis_major_length / x.axis_minor_length for x in r]))
pr = tifffile.imread(sys.argv[1]); gt = tifffile.imread(sys.argv[2])
tp, ngt, npr, pairs = match(gt, pr)
f1 = 2 * tp / (ngt + npr)
a_gt, r_gt = med(gt); a_pr, r_pr = med(pr)
print(f"F1@0.5={f1:.3f} TP={tp} FP={npr-tp} FN={ngt-tp} | count pred/gt={npr}/{ngt}")
print(f"median area um2 pred/gt={np.median(a_pr):.0f}/{np.median(a_gt):.0f}; median AR pred/gt={np.median(r_pr):.2f}/{np.median(r_gt):.2f}")
# paired per-cell error on matched cells
ga = {x.label: (x.area*PX**2, x.axis_major_length/x.axis_minor_length) for x in regionprops(gt)}
pp = {x.label: (x.area*PX**2, x.axis_major_length/x.axis_minor_length) for x in regionprops(pr)}
d = np.array([[pp[p][0]/ga[g][0]-1, pp[p][1]/ga[g][1]-1] for g, p in pairs])
print(f"matched cells: median rel. area error={np.median(d[:,0]):+.2f}, median |area err|={np.median(abs(d[:,0])):.2f}, median |AR err|={np.median(abs(d[:,1])):.2f}")
fail = f1 < 0.6 or abs(npr/ngt-1) > 0.2 or abs(np.median(a_pr)/np.median(a_gt)-1) > 0.2
print("ANALYSIS FAILED (F1<0.6, count off >20%, or median area off >20%)" if fail else "passes minimal criteria")
