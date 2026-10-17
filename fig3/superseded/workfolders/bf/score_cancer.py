"""Object F1 (IoU >= 0.5, greedy one-to-one) of a label image against the 124 manually annotated cancer cells in the
brightfield field (same reference and matching as Fig. 1c and Fig. 2a). Also reports the median area ratio of matched cells."""
import json, sys
import numpy as np
import tifffile
sys.path.insert(0, "<work>/fig3")
from matching import match
REF = tifffile.imread("<uploads>/e752a357-104_2.tif").astype(int)


def score(L):
    L = L.astype(int)
    m, fn, fp = match(REF, L, 0.5)
    ar = [(L == p).sum() / (REF == g).sum() for g, p, _ in m]
    return {"n_pred": int(len(np.unique(L[L > 0]))), "tp": len(m), "fn": len(fn), "fp": len(fp),
            "f1": round(2 * len(m) / (2 * len(m) + len(fn) + len(fp)), 3), "area_ratio_median": round(float(np.median(ar)), 3) if ar else None}


if __name__ == "__main__":
    print(json.dumps(score(tifffile.imread(sys.argv[1]))))
