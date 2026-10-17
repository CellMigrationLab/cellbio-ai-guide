"""StarDist nuclei on predicted DAPI vs manual nuclei reference (104_3.tif, drawn on acquired DAPI)."""
import numpy as np
import tifffile
from skimage.segmentation import clear_border
from common.matching import match

from common.paths import RAW as U
gt = tifffile.imread(U + "field104_endothelial_nuclei_manual_labels.tif").astype(int)
sd = tifffile.imread(U + "field104_pix2pix_dapi_stardist_nuclei_labels.tif")[1:1023].astype(int)   # row 0 = Pix2Pix padding
cancer = tifffile.imread(U + "field104_cancer_cells_manual_labels.tif") > 0

for name, G, P in [("whole field", gt, sd), ("edge cells removed", clear_border(gt.copy()), clear_border(sd.copy()))]:
    m, fn, fp = match(G, P)
    tp = len(m)
    print(f"{name:20s} manual {len(np.unique(G))-1}  StarDist(pred) {len(np.unique(P))-1}  TP {tp}  FP {len(fp)}  FN {len(fn)}  "
          f"F1 {2*tp/(2*tp+len(fp)+len(fn)):.3f}  mean IoU {np.mean([x[2] for x in m]):.3f}")
# do the manual nuclei / StarDist objects sit on cancer cells?
def on_cancer(L):
    ids = np.unique(L[L > 0])
    frac = np.array([cancer[L == i].mean() for i in ids])
    return int((frac > 0.5).sum()), len(ids)
print("manual nuclei mostly inside cancer cells:", on_cancer(gt), "| StarDist(pred):", on_cancer(sd))
m, fn, fp = match(gt, sd)
fp_c = sum(cancer[sd == i].mean() > 0.5 for i in fp)
fn_c = sum(cancer[gt == i].mean() > 0.5 for i in fn)
print(f"of {len(fp)} extra StarDist objects, {fp_c} lie on cancer cells; of {len(fn)} missed manual nuclei, {fn_c} lie on cancer cells")

# split the error: drop objects lying mostly on cancer cells from both sets, then re-score
def drop_on_cancer(L):
    L = L.copy()
    for i in np.unique(L[L > 0]):
        if cancer[L == i].mean() > 0.5:
            L[L == i] = 0
    return L
G2, P2 = drop_on_cancer(gt), drop_on_cancer(sd)
m, fn, fp = match(G2, P2)
tp = len(m)
print(f"excluding cancer-cell objects: manual {len(np.unique(G2))-1}  StarDist {len(np.unique(P2))-1}  TP {tp}  FP {len(fp)}  "
      f"FN {len(fn)}  F1 {2*tp/(2*tp+len(fp)+len(fn)):.3f}")
