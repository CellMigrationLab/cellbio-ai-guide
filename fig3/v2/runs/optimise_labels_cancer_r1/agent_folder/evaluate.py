"""Compare pipeline output with manual annotation. Usage: python evaluate.py <pred.tif> <ann.tif> [pred.csv]"""
import sys
import numpy as np, tifffile
from skimage import measure

def match(pred, ann, thr=0.5):
    ids_p, ids_a = np.unique(pred)[1:], np.unique(ann)[1:]
    pairs = {}
    inter = np.zeros((pred.max()+1, ann.max()+1), np.int64)
    np.add.at(inter, (pred.ravel(), ann.ravel()), 1)
    ap, aa = inter.sum(1), inter.sum(0)
    out = []
    for p in ids_p:
        a = inter[p, 1:].argmax()+1
        iou = inter[p, a]/(ap[p]+aa[a]-inter[p, a])
        if iou >= thr: out.append((p, a, iou))
    return out, len(ids_p), len(ids_a)

def report(pred, ann, px=0.65):
    m, npred, nann = match(pred, ann)
    tp = len(m); prec = tp/max(npred,1); rec = tp/nann; f1 = 2*tp/(npred+nann)
    rp = {r.label: r for r in measure.regionprops(pred)}; ra = {r.label: r for r in measure.regionprops(ann)}
    ae = [(rp[p].area-ra[a].area)*px**2 for p,a,_ in m]
    ar = [rp[p].axis_major_length/rp[p].axis_minor_length - ra[a].axis_major_length/ra[a].axis_minor_length for p,a,_ in m]
    med_a = np.median([r.area for r in ra.values()])*px**2
    print(f"pred={npred} ann={nann} TP={tp} precision={prec:.3f} recall={rec:.3f} F1@0.5={f1:.3f} count_err={100*(npred-nann)/nann:+.1f}%")
    print(f"matched: mean IoU={np.mean([i for *_,i in m]):.3f}; area bias={np.mean(ae):+.1f} um2 (MAE {np.mean(np.abs(ae)):.1f}, ref median {med_a:.0f}); "
          f"AR bias={np.mean(ar):+.3f} (MAE {np.mean(np.abs(ar)):.3f})")
    return f1

if __name__ == "__main__":
    report(tifffile.imread(sys.argv[1]).astype(np.int64), tifffile.imread(sys.argv[2]).astype(np.int64))
