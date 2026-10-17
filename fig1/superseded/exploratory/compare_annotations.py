"""Turn the two annotators' PECAM outlines into cell instances and compare them with Cellpose-on-predicted-PECAM."""
import numpy as np
import tifffile
from scipy import ndimage as ndi
from skimage.measure import label
from skimage.segmentation import clear_border, expand_labels

from common.paths import RAW as U
a1 = tifffile.imread(U + "field104_endothelial_junctions_annotator1.tif") > 0
a2 = tifffile.imread(U + "field104_endothelial_junctions_annotator2.tif") > 0
cp = tifffile.imread(U + "field104_pix2pix_pecam1_cellpose_cell_labels.tif")[1:1023].astype(int)   # Cellpose on predicted PECAM (row 0 = padding)


def lines_to_cells(lines):
    lab = label(~lines, connectivity=1)          # regions enclosed by the drawn lines
    lab = expand_labels(lab, 2)                  # give the line pixels back to the neighbouring cells
    lab = clear_border(lab)                      # drop cells cut by the image edge
    sizes = np.bincount(lab.ravel())
    small = np.isin(lab, np.where(sizes < 150)[0])  # drop slivers between double-drawn lines (< 63 um^2)
    lab[small] = 0
    return lab


def match(gt, pr, thr=0.5):
    """Greedy one-to-one matching on IoU; returns TP, FP, FN, F1, mean IoU of matches."""
    g_ids, p_ids = np.unique(gt[gt > 0]), np.unique(pr[pr > 0])
    pairs = {}
    m = (gt > 0) & (pr > 0)
    for g, p in zip(gt[m], pr[m]):
        pairs[(g, p)] = pairs.get((g, p), 0) + 1
    ga = dict(zip(*np.unique(gt[gt > 0], return_counts=True)))
    pa = dict(zip(*np.unique(pr[pr > 0], return_counts=True)))
    ious = sorted(((inter / (ga[g] + pa[p] - inter), g, p) for (g, p), inter in pairs.items()), reverse=True)
    used_g, used_p, matched = set(), set(), []
    for iou, g, p in ious:
        if iou < thr:
            break
        if g not in used_g and p not in used_p:
            used_g.add(g); used_p.add(p); matched.append(iou)
    tp = len(matched); fp = len(p_ids) - tp; fn = len(g_ids) - tp
    return tp, fp, fn, 2 * tp / (2 * tp + fp + fn), float(np.mean(matched)) if matched else 0.0


L1, L2 = lines_to_cells(a1), lines_to_cells(a2)
CP = clear_border(cp.copy())
# compare only where both annotators drew cells (their annotated area)


print("cells: annotator 1", len(np.unique(L1)) - 1, "| annotator 2", len(np.unique(L2)) - 1, "| Cellpose", len(np.unique(CP)) - 1)
for name, gt, pr in [("annotator 2 vs annotator 1", L1, L2), ("Cellpose(pred) vs annotator 1", L1, CP),
                     ("Cellpose(pred) vs annotator 2", L2, CP)]:
    tp, fp, fn, f1, miou = match(gt, pr)
    print(f"{name:32s} TP {tp:4d} FP {fp:4d} FN {fn:4d}  F1@IoU0.5 {f1:.3f}  mean IoU of matches {miou:.3f}")
np.save("panel_c_step3/L1.npy", L1); np.save("panel_c_step3/L2.npy", L2)
