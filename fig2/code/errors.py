"""Error types against the manual reference: missed, false, merged, split; F1 at IoU>=0.5; mean IoU of matched objects.

The four categories are illustrative heuristics, not standard definitions, and differ from the IoU rule used for F1:
- merged prediction: covers >= 50% of the area of each of at least two reference objects;
- split reference object: at least two predictions each have >= 50% of their own area inside it;
- missed: an unmatched reference object that is not part of a merge or split;
- false: an unmatched prediction that is not a merge and does not lie mostly (>= 50%) inside a split reference object.
The categories are computed independently of the matching: a part covering exactly half of a split object (IoU 0.5)
is also a true positive.
Tested on synthetic cases in fig2/tests/test_error_categories.py."""
import json, sys
import numpy as np
import tifffile
from skimage.measure import regionprops
from common.matching import match

from common.paths import RAW as U
REF = tifffile.imread(U + "field104_cancer_cells_manual_labels.tif").astype(int)


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
    for name, path in [("stardist", U + "field104_cancer_cells_stardist_custom_labels.tif"), ("cellpose_default", "../../fig1/source_data/full_field_labels/cellpose_sam_labels.tif")] + \
            [(a, f"panels/cp_{a}.tif") for a in sys.argv[1:]]:
        s, ids = errors(tifffile.imread(path).astype(int))
        out[name] = s
        json.dump(ids, open(f"panels/err_ids_{name}.json", "w"))
        print(name, s)
    json.dump(out, open("panels/error_summary.json", "w"), indent=1)
