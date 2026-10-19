"""Compare predicted labels with a manual annotation: python evaluate.py pred.tif annotation.tif"""
import sys
import numpy as np, tifffile
from skimage.measure import regionprops

PIXEL_UM = 0.65

def match(gt, pr, thr=0.5):
    """Greedy IoU matching; returns list of (gt_id, pred_id, iou)."""
    ng, npr = gt.max() + 1, pr.max() + 1
    inter = np.bincount(gt.ravel().astype(np.int64) * npr + pr.ravel(), minlength=ng * npr).reshape(ng, npr)[1:, 1:]
    ag, ap = inter.sum(1), inter.sum(0)  # placeholder, replaced below
    ag = np.bincount(gt.ravel(), minlength=ng)[1:]
    ap = np.bincount(pr.ravel(), minlength=npr)[1:]
    iou = inter / (ag[:, None] + ap[None, :] - inter + 1e-9)
    out = []
    for g, p in zip(*np.where(iou > thr)):  # IoU>0.5 is unique per object
        out.append((g + 1, p + 1, iou[g, p]))
    return out

def shape(lab):
    d = {}
    for r in regionprops(lab):
        d[r.label] = (r.area * PIXEL_UM**2, r.axis_major_length / max(r.axis_minor_length, 1e-9))
    return d

def report(gt, pr):
    from skimage.segmentation import relabel_sequential
    gt = relabel_sequential(gt)[0]; pr = relabel_sequential(pr)[0]
    m = match(gt, pr); tp = len(m); ng, npr = gt.max(), pr.max()
    f1 = 2 * tp / (ng + npr)
    sg, sp = shape(gt), shape(pr)
    ga = np.array([sg[g][0] for g, _, _ in m]); pa = np.array([sp[p][0] for _, p, _ in m])
    gr = np.array([sg[g][1] for g, _, _ in m]); pr_ = np.array([sp[p][1] for _, p, _ in m])
    res = dict(n_gt=ng, n_pred=npr, count_ratio=npr / ng, TP=tp, F1_iou50=f1,
               mean_iou_matched=float(np.mean([i for *_, i in m])) if m else 0,
               median_area_gt=np.median([v[0] for v in sg.values()]), median_area_pred=np.median([v[0] for v in sp.values()]) if sp else 0,
               median_AR_gt=np.median([v[1] for v in sg.values()]), median_AR_pred=np.median([v[1] for v in sp.values()]) if sp else 0,
               matched_area_relerr_median=float(np.median(np.abs(pa - ga) / ga)) if tp else np.nan,
               matched_AR_relerr_median=float(np.median(np.abs(pr_ - gr) / gr)) if tp else np.nan,
               matched_AR_spearman=float(__import__('scipy.stats').stats.spearmanr(gr, pr_)[0]) if tp > 2 else np.nan,
               fg_frac_gt=float((gt > 0).mean()), fg_frac_pred=float((pr > 0).mean()))
    return res

if __name__ == "__main__":
    for k, v in report(tifffile.imread(sys.argv[2]), tifffile.imread(sys.argv[1])).items():
        print(f"{k:28s} {v:.3f}" if isinstance(v, float) else f"{k:28s} {v}")
