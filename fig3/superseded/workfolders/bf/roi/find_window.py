"""Pick the 260 x 260 window whose local F1 values best match the whole-field F1 of every result shown (as Fig. 1)."""
import sys, json, numpy as np, tifffile
sys.path.insert(0, '.'); sys.path.insert(0, '<work2>/fig2')
from matching import match
from score_endo import gt
from skimage.segmentation import clear_border
B = '../bf2/'
GC = tifffile.imread('<uploads>/e752a357-104_2.tif'); GE = gt()
S = json.load(open(B + 'all_scores.json'))
R = {'cancer': {'adviceG_cancer': 'adviceG_cancer/labels.tif', 'adviceS_cancer': 'adviceS_cancer/labels.tif', 'codeG_cancer': 'codeG_cancer/labels.tif',
                'codeS_cancer': 'codeS_cancer/labels.tif', 'agent_cancer': 'agent_cancer/labels.tif', 'draw_cancer_r2': 'draw/draw_cancer_r2_labels.tif'},
     'endo': {'adviceG_endo': 'adviceG_endo/labels.tif', 'adviceS_endo': 'adviceS_endo/labels.tif', 'codeG_endo': 'codeG_endo/labels.tif',
              'codeS_endo': 'codeS_endo/labels.tif', 'agent_endo': 'agent_endo/labels.tif', 'draw_endo_r3': 'draw/draw_endo_r3_labels.tif'}}
L = {k: tifffile.imread(B + p) for d in R.values() for k, p in d.items()}
def f1w(G, P, y, x):
    g = G[y:y+260, x:x+260]; p = P[y:y+260, x:x+260]
    mt, fn, fp = match(g, p, 0.5); tp = len(mt)
    return 2*tp/(2*tp+len(fn)+len(fp)) if (tp+len(fn)+len(fp)) else 1.0
best = []
for y in range(0, 1022-260, 40):
    for x in range(0, 1024-260, 40):
        err = []
        for tg, G in [('cancer', GC), ('endo', GE)]:
            for k in R[tg]:
                err.append(abs(f1w(G, L[k], y, x) - S[k]['f1']))
        nc = len(np.unique(GC[y:y+260, x:x+260])) - 1
        best.append((np.mean(err), max(err), y, x, nc))
best.sort()
for b in best[:8]: print('mean err %.3f max %.3f  y %d x %d  cancer cells %d' % b)
