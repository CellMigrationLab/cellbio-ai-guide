"""Score a nuclei label image against the manual endothelial nuclei of the DAPI field. Predicted objects that lie mostly
(>30% of their area) on annotated cancer cells are ignored, because the manual annotation covers endothelial nuclei only.
Reports object F1 (IoU >= 0.5, one-to-one), counts and median area ratio of matched nuclei (prediction / manual)."""
import json, sys
import numpy as np
import tifffile
sys.path.insert(0, "<work>/fig3")
from matching import match
U = "<uploads>/"
REF = tifffile.imread(U + "1add3634-104_3.tif").astype(int)
CANC = tifffile.imread(U + "e752a357-104_2.tif") > 0


def score(L):
    L = L.astype(int).copy()
    ids, cnt = np.unique(L[L > 0], return_counts=True)
    on_c = dict(zip(*np.unique(L[(L > 0) & CANC], return_counts=True)))
    drop = [i for i, c in zip(ids, cnt) if on_c.get(i, 0) > 0.3 * c]
    L[np.isin(L, drop)] = 0
    m, fn, fp = match(REF, L, 0.5)
    ra = [(REF == g).sum() for g, p, _ in m]; la = [(L == p).sum() for g, p, _ in m]
    return {"n_pred": int(len(np.unique(L[L > 0]))), "n_ref": int(len(np.unique(REF[REF > 0]))), "tp": len(m), "fn": len(fn), "fp": len(fp),
            "f1": round(2 * len(m) / (2 * len(m) + len(fn) + len(fp)), 3), "area_ratio_median": round(float(np.median(np.array(la) / np.array(ra))), 3)}


if __name__ == "__main__":
    r = score(tifffile.imread(sys.argv[1]))
    print(json.dumps(r))
