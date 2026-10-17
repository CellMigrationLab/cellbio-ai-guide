# Recovered verbatim from the session transcript (2026-10-17T07:05:18.364Z).
# Last shell command that wrote fig_assets/dapi_full.png. Paths are those of the original working folder.
mkdir -p <fig3-work>/bf3/fig_assets && cd <fig3-work>/bf3 && python3 - <<'E'
import sys, numpy as np, tifffile
from PIL import Image
sys.path.insert(0, '../bf')
from score_endo import gt
U = '<uploads>/'
def gray(a, lo=0.5, hi=99.7):
    l, h = np.percentile(a, [lo, hi]); return (np.clip((a - l) / (h - l), 0, 1) * 255).astype(np.uint8)
def labels_rgb(L, seed=3):
    rng = np.random.default_rng(seed); n = int(L.max())
    col = (rng.uniform(0.25, 1.0, (n + 1, 3)) * 255).astype(np.uint8); col[0] = (18, 22, 30)
    return col[L]
dapi = tifffile.imread(U + '2453a2f8-GT_DAPI.tif').astype(float)
bf = tifffile.imread(U + 'cccf774d-BF.tif').astype(float) if False else tifffile.imread('../bf/agent/bf.tif').astype(float)
Image.fromarray(gray(dapi)).save('fig_assets/dapi_full.png')
Image.fromarray(gray(bf)).save('fig_assets/bf_full.png')
for name, L in [('nuclei', tifffile.imread(U + '1add3634-104_3.tif')), ('cancer', tifffile.imread(U + 'e752a357-104_2.tif')), ('endo', gt())]:
    Image.fromarray(labels_rgb(L.astype(int))).save(f'fig_assets/labels_{name}.png'); print(name, int(len(np.unique(L)) - 1))
E
