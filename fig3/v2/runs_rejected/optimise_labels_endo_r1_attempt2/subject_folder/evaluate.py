"""Compare predicted labels with annotation: count, F1@IoU0.5, area/aspect-ratio agreement."""
import sys, numpy as np, tifffile as t
from skimage import measure, segmentation, io
PX = 0.65

def match(gt, pr, thr=0.5):
    ids_g, ids_p = np.unique(gt)[1:], np.unique(pr)[1:]
    pair = {}
    m = (gt > 0) & (pr > 0)
    g, p = gt[m], pr[m]
    keys, cnt = np.unique(np.stack([g, p]), axis=1, return_counts=True)
    ag = dict(zip(*np.unique(gt, return_counts=True))); ap = dict(zip(*np.unique(pr, return_counts=True)))
    matches = []
    for (gi, pi), c in zip(keys.T, cnt):
        iou = c / (ag[gi] + ap[pi] - c)
        if iou >= thr: matches.append((gi, pi, iou))
    return ids_g, ids_p, matches

def props(lab):
    return {r.label: (r.area * PX**2, r.major_axis_length / max(r.minor_axis_length, 1e-9)) for r in measure.regionprops(lab)}

def evaluate(gt, pr):
    ig, ip, mt = match(gt, pr)
    tp = len(mt); f1 = 2 * tp / (len(ig) + len(ip))
    pg, pp = props(gt), props(pr)
    out = dict(n_gt=len(ig), n_pred=len(ip), tp=tp, F1_iou50=round(f1, 3),
               mean_iou_matched=round(float(np.mean([m[2] for m in mt])), 3) if mt else 0)
    for name, k in (('area', 0), ('AR', 1)):
        gv = np.array([pg[m[0]][k] for m in mt]); pv = np.array([pp[m[1]][k] for m in mt])
        out[f'{name}_median_gt_all'] = round(float(np.median([v[k] for v in pg.values()])), 2)
        out[f'{name}_median_pred_all'] = round(float(np.median([v[k] for v in pp.values()])), 2)
        out[f'{name}_matched_median_relerr'] = round(float(np.median(np.abs(pv - gv) / gv)), 3) if mt else None
        out[f'{name}_matched_spearman'] = round(float(__import__('scipy.stats').stats.spearmanr(gv, pv)[0]), 3) if len(mt) > 2 else None
    return out

if __name__ == '__main__':
    gt = t.imread(sys.argv[1]); pr = t.imread(sys.argv[2]) if sys.argv[2].endswith('.tif') else np.load(sys.argv[2])
    for k, v in evaluate(gt, pr).items(): print(k, v)
