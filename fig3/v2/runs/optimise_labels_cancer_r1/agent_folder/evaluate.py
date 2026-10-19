"""Compare predicted labels to annotation: detection F1@IoU0.5, count error, area/AR agreement."""
import sys
import numpy as np
import tifffile
from skimage import measure, segmentation, io
from pipeline import measure_cells


def match(gt, pr, thr=0.5):
    gl, pl = np.unique(gt)[1:], np.unique(pr)[1:]
    pairs = {}
    both = (gt > 0) & (pr > 0)
    g, p = gt[both], pr[both]
    ga = np.bincount(gt.ravel()); pa = np.bincount(pr.ravel())
    key, cnt = np.unique(np.stack([g, p]), axis=1, return_counts=True)
    m = []
    for (a, b), c in zip(key.T, cnt):
        iou = c / (ga[a] + pa[b] - c)
        if iou >= thr:
            m.append((a, b, iou))
    return m, len(gl), len(pl)


def report(gt, pr):
    m, ng, npred = match(gt, pr)
    tp = len(m); f1 = 2 * tp / (ng + npred)
    gt_t, pr_t = measure_cells(gt).set_index("label"), measure_cells(pr).set_index("label")
    ga = np.array([gt_t.area_um2[a] for a, _, _ in m]); pa = np.array([pr_t.area_um2[b] for _, b, _ in m])
    gr = np.array([gt_t.aspect_ratio[a] for a, _, _ in m]); pr_ = np.array([pr_t.aspect_ratio[b] for _, b, _ in m])
    res = dict(n_gt=ng, n_pred=npred, tp=tp, F1=f1, precision=tp / max(npred, 1), recall=tp / ng,
               count_err_pct=100 * (npred - ng) / ng,
               area_bias_pct=100 * np.median((pa - ga) / ga), area_MAPE=100 * np.mean(abs(pa - ga) / ga),
               AR_bias=np.median(pr_ - gr), AR_MAE=np.mean(abs(pr_ - gr)),
               median_area_gt_all=gt_t.area_um2.median(), median_area_pred_all=pr_t.area_um2.median(),
               median_AR_gt_all=gt_t.aspect_ratio.median(), median_AR_pred_all=pr_t.aspect_ratio.median())
    return res


if __name__ == "__main__":
    gt = tifffile.imread(sys.argv[1]); pr = tifffile.imread(sys.argv[2])
    for k, v in report(gt, pr).items():
        print(f"{k:22s} {v:.3f}" if isinstance(v, float) else f"{k:22s} {v}")
