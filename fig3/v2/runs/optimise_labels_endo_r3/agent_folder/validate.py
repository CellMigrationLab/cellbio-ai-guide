"""python validate.py <labels.tif> <annotation.tif> [overlay.png image.tif]
Scores a prediction against a manual annotation with measures tied to the biology:
count error, matched-cell F1 (IoU 0.3/0.5/0.75), area and aspect-ratio agreement."""
import sys, numpy as np, tifffile
from scipy import stats
from skimage import measure
PX = 0.65
def props(l): return {r.label: (r.area*PX**2, r.major_axis_length/max(r.minor_axis_length, 1e-6)) for r in measure.regionprops(l)}
def evaluate(pred, gt):
    ig, ip = np.unique(gt)[1:], np.unique(pred)[1:]
    ov = np.zeros((ig.max()+1, ip.max()+1), np.int64); m = (gt > 0) & (pred > 0); np.add.at(ov, (gt[m], pred[m]), 1)
    ag = np.bincount(gt.ravel(), minlength=ov.shape[0]); ap = np.bincount(pred.ravel(), minlength=ov.shape[1])
    iou = ov/(ag[:, None]+ap[None, :]-ov+1e-9); iou[:, 0] = 0
    res = {}
    for t in (0.3, 0.5, 0.75):
        pairs = [(g, iou[g].argmax()) for g in ig if iou[g].max() >= t]
        res[f'F1@IoU{t}'] = 2*len(pairs)/(len(ig)+len(ip))
        if t == 0.5: p50 = pairs
    pg, pp = props(gt), props(pred)
    ga, pa = (np.array([pg[g][0] for g, _ in p50]), np.array([pp[p][0] for _, p in p50]))
    gr, pr = (np.array([pg[g][1] for g, _ in p50]), np.array([pp[p][1] for _, p in p50]))
    res.update(n_gt=len(ig), n_pred=len(ip), count_error_pct=100*(len(ip)-len(ig))/len(ig),
      median_area_gt=np.median([v[0] for v in pg.values()]), median_area_pred=np.median([v[0] for v in pp.values()]),
      median_AR_gt=np.median([v[1] for v in pg.values()]), median_AR_pred=np.median([v[1] for v in pp.values()]),
      matched_area_rel_err_median_pct=100*np.median(np.abs(pa-ga)/ga), matched_AR_abs_err_median=np.median(np.abs(pr-gr)),
      matched_AR_spearman=stats.spearmanr(gr, pr)[0])
    return res
if __name__ == '__main__':
    pred, gt = (tifffile.imread(p).astype(np.int64) for p in sys.argv[1:3])
    for k, v in evaluate(pred, gt).items(): print(f'{k:36s}{v:.3f}')
    if len(sys.argv) == 5:
        from skimage import io, segmentation, exposure
        im = tifffile.imread(sys.argv[4]).astype(float)
        n = exposure.rescale_intensity(im, in_range=tuple(np.percentile(im, [0.5, 99.5])), out_range=(0, 1))
        ov = segmentation.mark_boundaries(np.dstack([n]*3), pred, color=(1, 0, 0), mode='inner')
        ov = segmentation.mark_boundaries(ov, gt, color=(0, 1, 0), mode='inner')
        io.imsave(sys.argv[3], (ov*255).astype('uint8'))
