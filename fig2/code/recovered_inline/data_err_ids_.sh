# Recovered verbatim from the session transcript (2026-10-16T12:03:57.753Z).
# Last shell command that wrote data/err_ids_. Paths are those of the original working folder.
cd <work2>/fig2; cp ../fig1/compare_cancer_gt_lib.py matching.py; cat > errors.py <<'EOF'
"""Error types against the manual reference: missed, false, merged, split; F1 at IoU>=0.5; mean IoU of matched objects."""
import json, sys
import numpy as np
import tifffile
from skimage.measure import regionprops
from matching import match

U = "<uploads>/"
REF = tifffile.imread(U + "e752a357-104_2.tif").astype(int)


def errors(pr, ref=REF):
    matched, fn, fp = match(ref, pr, 0.5)
    m = (ref > 0) & (pr > 0)
    ov = {}
    for g, p in zip(ref[m], pr[m]):
        ov[(g, p)] = ov.get((g, p), 0) + 1
    ga = dict(zip(*np.unique(ref[ref > 0], return_counts=True)))
    pa = dict(zip(*np.unique(pr[pr > 0], return_counts=True)))
    merged_p = {p for p in pa if sum(1 for (g, q), n in ov.items() if q == p and n >= 0.5 * ga[g]) >= 2}
    split_g = {g for g in ga if sum(1 for (h, p), n in ov.items() if h == g and n >= 0.5 * pa[p]) >= 2}
    merged_g = {g for (g, p), n in ov.items() if p in merged_p and n >= 0.5 * ga[g]}
    missed = set(fn) - merged_g - split_g
    false = {p for p in fp if p not in merged_p and not any(q == p and n >= 0.5 * pa[p] for (g, q), n in ov.items() if g in split_g)}
    tp = len(matched)
    return dict(n_ref=len(ga), n_pred=len(pa), tp=tp, fn=len(fn), fp=len(fp),
                f1=round(2 * tp / (2 * tp + len(fn) + len(fp)), 3),
                missed=len(missed), false=len(false), merges=len(merged_p), splits=len(split_g),
                mean_iou_matched=round(float(np.mean([i for _, _, i in matched])), 3)), \
        dict(missed=sorted(map(int, missed)), false=sorted(map(int, false)), merged=sorted(map(int, merged_p)), split=sorted(map(int, split_g)))


if __name__ == "__main__":
    out = {}
    for name, path in [("stardist", U + "76c6cb98-Cancer_cell_seg.tif"), ("cellpose_default", "../fig1/data4/BF_cellpose_sam_labels.tif")] + \
            [(a, f"data/cp_{a}.tif") for a in sys.argv[1:]]:
        s, ids = errors(tifffile.imread(path).astype(int))
        out[name] = s
        json.dump(ids, open(f"data/err_ids_{name}.json", "w"))
        print(name, s)
    json.dump(out, open("data/error_summary.json", "w"), indent=1)
EOF
python3 errors.py; python3 - <<'EOF'
import numpy as np, tifffile
from skimage.measure import regionprops
U="<uploads>/"
ref=tifffile.imread(U+"e752a357-104_2.tif").astype(int)
cp=tifffile.imread("../fig1/data4/BF_cellpose_sam_labels.tif").astype(int)
for nm,L in [("ref",ref),("cp",cp)]:
    rp=regionprops(L); a=np.array([r.area for r in rp]); s=np.array([r.solidity for r in rp]); e=np.array([r.eccentricity for r in rp])
    print(nm, len(a), "area pct", np.percentile(a,[1,5,50,95,99]).round(), "solidity", np.percentile(s,[1,5,50]).round(3), "ecc", np.percentile(e,[50,95,99]).round(2))
EOF
