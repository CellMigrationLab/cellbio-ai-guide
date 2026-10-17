"""The four pieces of advice (replies/advice{G,S}_{cancer,endo}.txt), implemented by us as literally as possible with the
installed Cellpose 4.2.1.1. Where the advice gives a range, the value in the middle of the range is used; where it says
'raise if X happens' and X happens with the defaults (endothelium picked up as cancer cells), the raised value is used.
Fine-tuning, which every reply recommended, is not done (it needs annotated training images).

G cancer : Cellpose-SAM; flatten background (large Gaussian); diameter measured on a few cells (30 px); cellprob raised
           to 1.25 (advised range 0.5-2) because the endothelium is picked up; filter by size (12-30 um, as given for
           cancer cells 15-30 um with tolerance) and solidity (>= 0.85; no value advised).
S cancer : cpsam_v2; diameter unset; no pre-processing; cellprob raised to 2 (advised +1 to +3); min area 175 px
           (advised 150-200 px).
G endo   : Cellpose-SAM; flatten background; diameter 70 px (advised 60-80); flow 0.4; cellprob 0; min_size 400 px
           (advised 300-500); cancer cells segmented separately (G cancer) and excluded (> 50 % overlap).
S endo   : cpsam_v2; diameter unset; defaults (flow 0.4, cellprob 0); size filter (400 px, no value advised); cancer
           cells segmented separately (S cancer) and excluded (> 50 % overlap).
"""
import sys, numpy as np, tifffile
from scipy import ndimage as ndi
from skimage import measure
from cellpose import models
v = sys.argv[1]
img = tifffile.imread('../bf/agent/bf.tif').astype(np.float32)
flat = img - ndi.gaussian_filter(img, 60)
m = models.CellposeModel(gpu=False, pretrained_model='cpsam_v2')
def relabel(L, keep):
    out = np.zeros_like(L); k = 0
    for r in measure.regionprops(L):
        if keep(r): k += 1; out[L == r.label] = k
    return out.astype(np.int32)
if v == 'G_cancer':
    L = m.eval(flat, diameter=30, flow_threshold=0.4, cellprob_threshold=1.25)[0]
    L = relabel(L, lambda r: 12 <= r.equivalent_diameter_area * 0.65 <= 30 and r.solidity >= 0.85)
elif v == 'S_cancer':
    L = m.eval(img, flow_threshold=0.4, cellprob_threshold=2.0)[0]
    L = relabel(L, lambda r: r.area >= 175)
else:
    ref = tifffile.imread(f'advice{v[0]}_cancer/labels.tif') > 0
    if v == 'G_endo':
        L = m.eval(flat, diameter=70, flow_threshold=0.4, cellprob_threshold=0.0)[0]
    else:
        L = m.eval(img, flow_threshold=0.4, cellprob_threshold=0.0)[0]
    L = relabel(L, lambda r: r.area >= 400 and ref[tuple(r.coords.T)].mean() <= 0.5)
tifffile.imwrite(f'advice{v[0]}_{v[2:]}/labels.tif', L)
print(v, L.max())
