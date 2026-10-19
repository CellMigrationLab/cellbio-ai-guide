"""Compare predicted labels with manual annotation. Usage: python evaluate.py pred.tif annotation.tif"""
import sys, numpy as np, tifffile
from scipy import ndimage as ndi
from skimage import measure, morphology
P = 0.65
def footprint(gt):
    return ndi.binary_fill_holes(ndi.binary_closing(np.pad(gt > 0, 20), morphology.disk(15))[20:-20, 20:-20])
def evaluate(pred, gt):
    fp = footprint(gt)
    # ignore predicted cells whose centroid lies outside the annotated region
    ids = [r.label for r in measure.regionprops(pred) if fp[int(r.centroid[0]), int(r.centroid[1])]]
    pred = np.where(np.isin(pred, ids), pred, 0)
    gl = [r.label for r in measure.regionprops(gt)]
    pairs, matched = {}, set()
    pa = {r.label: r for r in measure.regionprops(pred)}; ga = {r.label: r for r in measure.regionprops(gt)}
    ov = {}
    m = (pred > 0) & (gt > 0)
    for p, g in zip(pred[m], gt[m]): ov[(p, g)] = ov.get((p, g), 0) + 1
    for (p, g), n in ov.items():
        iou = n / (pa[p].area + ga[g].area - n)
        if iou >= 0.5: pairs[g] = (p, iou)
    tp = len(pairs); fn = len(ga) - tp; fpn = len(pa) - tp
    res = dict(n_gt=len(ga), n_pred=len(pa), tp=tp, fp=fpn, fn=fn,
               F1_iou50=2*tp/(2*tp+fpn+fn),
               count_err_pct=100*(len(pa)-len(ga))/len(ga), mean_iou_matched=np.mean([v[1] for v in pairs.values()]) if pairs else 0)
    ga_a = np.array([ga[g].area for g in pairs])*P**2; pa_a = np.array([pa[pairs[g][0]].area for g in pairs])*P**2
    ga_r = np.array([ga[g].axis_major_length/ga[g].axis_minor_length for g in pairs])
    pa_r = np.array([pa[pairs[g][0]].axis_major_length/pa[pairs[g][0]].axis_minor_length for g in pairs])
    res.update(median_area_gt=np.median([r.area for r in ga.values()])*P**2,
               median_area_pred=np.median([r.area for r in pa.values()])*P**2,
               area_median_rel_err_pct=100*np.median((pa_a-ga_a)/ga_a),
               area_pearson=np.corrcoef(ga_a, pa_a)[0,1],
               AR_median_gt=np.median([r.axis_major_length/max(r.axis_minor_length,1e-6) for r in ga.values()]),
               AR_median_pred=np.median([r.axis_major_length/max(r.axis_minor_length,1e-6) for r in pa.values()]),
               AR_matched_mae=np.mean(np.abs(pa_r-ga_r)), AR_pearson=np.corrcoef(ga_r, pa_r)[0,1])
    return res
if __name__ == "__main__":
    for k, v in evaluate(tifffile.imread(sys.argv[1]), tifffile.imread(sys.argv[2])).items(): print(f"{k}: {v:.3f}" if isinstance(v,float) else f"{k}: {v}")
