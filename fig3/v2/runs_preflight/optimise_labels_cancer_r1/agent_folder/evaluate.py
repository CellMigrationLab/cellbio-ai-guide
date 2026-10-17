"""Compare predicted labels to a reference label image.
Usage: python evaluate.py <pred.tif> <ref.tif>
Reports detection F1@IoU0.5 (count accuracy), and area / aspect-ratio agreement on matched cells."""
import sys
import numpy as np
import tifffile
from skimage.measure import regionprops

PIXEL_UM = 0.65


def match(pred, ref, thr=0.5):
    p_ids = np.unique(pred)[1:]
    r_ids = np.unique(ref)[1:]
    pairs = []
    both = (pred > 0) & (ref > 0)
    pi, ri = pred[both], ref[both]
    keys, counts = np.unique(np.stack([pi, ri]), axis=1, return_counts=True)
    p_area = dict(zip(*np.unique(pred, return_counts=True)))
    r_area = dict(zip(*np.unique(ref, return_counts=True)))
    for (p, r), c in zip(keys.T, counts):
        iou = c / (p_area[p] + r_area[r] - c)
        if iou >= thr:
            pairs.append((p, r, iou))
    return p_ids, r_ids, pairs


def main(pred_path, ref_path):
    pred, ref = tifffile.imread(pred_path), tifffile.imread(ref_path)
    assert pred.shape == ref.shape, "shape mismatch"
    p_ids, r_ids, pairs = match(pred, ref)
    tp = len(pairs)
    fp, fn = len(p_ids) - tp, len(r_ids) - tp
    f1 = 2 * tp / (2 * tp + fp + fn)
    print(f"pred={len(p_ids)} ref={len(r_ids)} TP={tp} FP={fp} FN={fn} F1@0.5={f1:.3f} count_err={100*(len(p_ids)-len(r_ids))/len(r_ids):+.1f}%")
    pr = {r.label: r for r in regionprops(pred)}
    rr = {r.label: r for r in regionprops(ref)}
    pa = np.array([pr[p].area for p, _, _ in pairs]) * PIXEL_UM**2
    ra = np.array([rr[r].area for _, r, _ in pairs]) * PIXEL_UM**2
    par = np.array([pr[p].axis_major_length / pr[p].axis_minor_length for p, _, _ in pairs])
    rar = np.array([rr[r].axis_major_length / rr[r].axis_minor_length for _, r, _ in pairs])
    print(f"mean IoU (matched)={np.mean([i for *_, i in pairs]):.3f}")
    print(f"area: median rel err={100*np.median((pa-ra)/ra):+.1f}%  median |rel err|={100*np.median(abs(pa-ra)/ra):.1f}%  Pearson r={np.corrcoef(pa,ra)[0,1]:.3f}")
    print(f"AR: median err={np.median(par-rar):+.3f}  median |err|={np.median(abs(par-rar)):.3f}  Pearson r={np.corrcoef(par,rar)[0,1]:.3f}  mean AR pred={par.mean():.3f} ref={rar.mean():.3f}")
    return f1


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
