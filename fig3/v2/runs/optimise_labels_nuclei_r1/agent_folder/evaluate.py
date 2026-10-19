"""Compare pipeline output with a manual annotation.
Usage: python evaluate.py <labels.tif> <annotation.tif>
Reports detection (F1 @ IoU 0.5), count error, and errors in area / aspect ratio of matched nuclei.
FAIL criteria (for this image): F1<0.80, |count error|>10%, median |area error|>10%, median |AR error|>0.1.
"""
import sys
import numpy as np, tifffile
from skimage.measure import regionprops

PX = 0.65

def match(pred, gt):
    pairs = []
    for g in regionprops(gt):
        sl = g.slice; m = gt[sl] == g.label
        ids, c = np.unique(pred[sl][m], return_counts=True)
        ok = ids > 0
        if not ok.any(): continue
        ids, c = ids[ok], c[ok]; p = ids[c.argmax()]
        iou = c.max() / (g.area + (pred == p).sum() - c.max())
        if iou > 0.5: pairs.append((g.label, p, iou))
    return pairs

def main(pred_path, gt_path):
    pred, gt = tifffile.imread(pred_path), tifffile.imread(gt_path)
    if pred.shape != gt.shape: raise ValueError("shape mismatch")
    n_p, n_g = len(np.unique(pred)) - 1, len(np.unique(gt)) - 1
    pairs = match(pred, gt); tp = len(pairs)
    prec, rec = tp / n_p, tp / n_g; f1 = 2 * prec * rec / (prec + rec)
    rp = {r.label: r for r in regionprops(pred)}; rg = {r.label: r for r in regionprops(gt)}
    ae = np.array([(rp[p].area - rg[g].area) / rg[g].area for g, p, _ in pairs])
    ar = lambda r: r.axis_major_length / r.axis_minor_length
    are = np.array([ar(rp[p]) - ar(rg[g]) for g, p, _ in pairs])
    print(f"pred {n_p} gt {n_g} count error {100*(n_p-n_g)/n_g:+.1f}%  P {prec:.3f} R {rec:.3f} F1 {f1:.3f}")
    print(f"matched mean IoU {np.mean([i for *_, i in pairs]):.3f}")
    print(f"area rel error: median {np.median(ae):+.3f}, median abs {np.median(abs(ae)):.3f}")
    print(f"AR error: median {np.median(are):+.3f}, median abs {np.median(abs(are)):.3f}")
    print(f"GT median area {np.median([r.area for r in rg.values()])*PX**2:.1f} um2, pred {np.median([r.area for r in rp.values()])*PX**2:.1f}; "
          f"GT median AR {np.median([ar(r) for r in rg.values()]):.3f}, pred {np.median([ar(r) for r in rp.values()]):.3f}")
    fail = f1 < .8 or abs(n_p-n_g)/n_g > .1 or np.median(abs(ae)) > .1 or np.median(abs(are)) > .1
    print("RESULT:", "FAIL" if fail else "PASS")

if __name__ == "__main__":
    main(*sys.argv[1:3])
