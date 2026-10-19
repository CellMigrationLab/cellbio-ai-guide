"""Compare predicted labels with annotation: python evaluate.py pred.tif annotation.tif"""
import sys, numpy as np, tifffile as t
from skimage.measure import regionprops

def match(gt, pr, thr=0.5):
    """Greedy one-to-one match by IoU. Returns list of (gt_id, pred_id, iou)."""
    pairs = {}
    m = (gt > 0) & (pr > 0)
    g, p = gt[m], pr[m]
    key = g.astype(np.int64) * (pr.max() + 1) + p
    u, c = np.unique(key, return_counts=True)
    ga = np.bincount(gt.ravel()); pa = np.bincount(pr.ravel())
    out = []
    for k, n in zip(u, c):
        gi, pi = divmod(int(k), int(pr.max() + 1))
        iou = n / (ga[gi] + pa[pi] - n)
        if iou >= thr: out.append((gi, pi, iou))  # IoU>=0.5 implies unique match
    return out

def shape(lbl, ids, px=0.65):
    d = {}
    for r in regionprops(lbl):
        if r.label in ids:
            d[r.label] = (r.area * px**2, r.axis_major_length / r.axis_minor_length)
    return d

if __name__ == "__main__":
    pr = t.imread(sys.argv[1]).astype(np.int64); gt = t.imread(sys.argv[2]).astype(np.int64)
    ng, npred = len(np.unique(gt)) - 1, len(np.unique(pr)) - 1
    mt = match(gt, pr); tp = len(mt)
    prec, rec = tp / npred, tp / ng; f1 = 2 * tp / (ng + npred)
    gs, ps = shape(gt, {a for a, _, _ in mt}), shape(pr, {b for _, b, _ in mt})
    ga = np.array([gs[a][0] for a, _, _ in mt]); pa = np.array([ps[b][0] for _, b, _ in mt])
    gr = np.array([gs[a][1] for a, _, _ in mt]); prr = np.array([ps[b][1] for _, b, _ in mt])
    print(f"GT {ng} pred {npred} count_err {100*(npred-ng)/ng:+.1f}%  TP {tp} P {prec:.3f} R {rec:.3f} F1@0.5 {f1:.3f}")
    print(f"matched mean IoU {np.mean([i for *_, i in mt]):.3f}")
    print(f"area um2: GT median {np.median(ga):.1f} pred {np.median(pa):.1f}; median rel err {100*np.median((pa-ga)/ga):+.1f}%")
    print(f"AR: GT median {np.median(gr):.2f} pred {np.median(prr):.2f}; median abs err {np.median(abs(prr-gr)):.3f}")
    # whole-population stats (all objects) 
    allg = shape(gt, set(np.unique(gt)) - {0}); allp = shape(pr, set(np.unique(pr)) - {0})
    print(f"ALL objects area median GT {np.median([v[0] for v in allg.values()]):.1f} pred {np.median([v[0] for v in allp.values()]):.1f}; AR median GT {np.median([v[1] for v in allg.values()]):.2f} pred {np.median([v[1] for v in allp.values()]):.2f}")
