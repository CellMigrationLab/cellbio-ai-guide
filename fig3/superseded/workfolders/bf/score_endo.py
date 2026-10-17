"""Object F1 (IoU >= 0.5, greedy one-to-one) of a label image against the manual endothelial annotation (annotator 1,
outlines drawn on the acquired PECAM-1 image of the same field). As in Fig. 2: border cells and slivers < 150 px removed
from the reference; border objects are also removed from the prediction."""
import sys, json, numpy as np, tifffile
sys.path.insert(0, '<work2>/fig2')
from matching import match
from skimage.measure import label
from skimage.segmentation import clear_border, expand_labels
U = "<uploads>/"
def lines_to_cells(lines):
    lab = expand_labels(label(~lines, connectivity=1), 2)
    lab = clear_border(lab)
    sizes = np.bincount(lab.ravel()); lab[np.isin(lab, np.where(sizes < 150)[0])] = 0
    return lab
def gt(which=1):
    return lines_to_cells(tifffile.imread(U + ("6151ff66-104.tif" if which == 1 else "b7199d2f-104_1.tif")) > 0)
def score(L, G=None):
    G = gt() if G is None else G
    P = clear_border(L.astype(int))
    mt, fn, fp = match(G, P, 0.5)
    tp = len(mt); f1 = 2 * tp / (2 * tp + len(fn) + len(fp)) if tp else 0.0
    return dict(n_ref=int(len(np.unique(G)) - 1), n_pred=int(len(np.unique(P)) - 1), tp=tp, fn=len(fn), fp=len(fp), f1=round(f1, 3))
if __name__ == "__main__":
    print(json.dumps(score(tifffile.imread(sys.argv[1]))))
