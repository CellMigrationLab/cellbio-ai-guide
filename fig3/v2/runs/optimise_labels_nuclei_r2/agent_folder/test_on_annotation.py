"""Usage: python test_on_annotation.py <pred_labels.tif> <annotation.tif>
Matches predicted to manual nuclei (IoU>0.5) and reports detection and shape-measurement agreement.
FAIL if: F1<0.85, |median area bias|>10%, |median aspect-ratio bias|>10%, or |count error|>10%."""
import sys, numpy as np, tifffile
from skimage import measure
from skimage.segmentation import relabel_sequential as rs
pred, gt = (rs(tifffile.imread(p))[0] for p in sys.argv[1:3])
n, m = gt.max() + 1, pred.max() + 1
full = np.bincount(gt.ravel().astype(np.int64) * m + pred.ravel(), minlength=n * m).reshape(n, m)
iou = full[1:, 1:] / np.maximum(full.sum(1)[1:, None] + full.sum(0)[None, 1:] - full[1:, 1:], 1)
gi, pi = np.where(iou > 0.5)
tp = len(gi); fp = pred.max() - tp; fn = gt.max() - tp; f1 = 2 * tp / (2 * tp + fp + fn)
rg, rp = measure.regionprops(gt), measure.regionprops(pred)
ar = lambda r: r.axis_major_length / r.axis_minor_length
area_b = np.median([rp[p].area / rg[g].area - 1 for g, p in zip(gi, pi)])
ar_b = np.median([ar(rp[p]) / ar(rg[g]) - 1 for g, p in zip(gi, pi)])
cnt = (pred.max() - gt.max()) / gt.max()
print(f"GT {gt.max()} pred {pred.max()} TP {tp} FP {fp} FN {fn} F1 {f1:.3f} medianIoU {np.median(iou[gi, pi]):.3f}")
print(f"matched-pair median area bias {area_b:+.3f}, aspect-ratio bias {ar_b:+.3f}, count error {cnt:+.3f}")
print(f"population: mean AR gt {np.mean([ar(r) for r in rg]):.3f} pred {np.mean([ar(r) for r in rp]):.3f}")
ok = f1 >= 0.85 and abs(area_b) <= .10 and abs(ar_b) <= .10 and abs(cnt) <= .10
print("PASS" if ok else "FAIL"); sys.exit(0 if ok else 1)
