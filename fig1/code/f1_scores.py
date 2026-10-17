"""Recompute the panel c F1 scores: object-level F1 against the manual annotation,
greedy one-to-one matching at IoU >= 0.5 (common/matching.py), over the whole field."""
import json
import tifffile
from common.matching import match

from common.paths import raw_file

F = "full_field/"  # derived label images, relative to fig1/source_data (run from there)
ref = tifffile.imread(raw_file("field104_cancer_cells_manual_labels.tif")).astype(int)
out = {}
for key, fn in [("classical", "threshold_labels.tif"), ("cellpose", "cellpose_sam_labels.tif"), ("stardist", None)]:
    pr = tifffile.imread(raw_file("field104_cancer_cells_stardist_custom_labels.tif") if fn is None else F + fn).astype(int)
    tp, fn_, fp = (len(s) for s in match(ref, pr, 0.5))
    out[key] = round(2 * tp / (2 * tp + fp + fn_), 3)
    print(f"{key:10s} TP {tp:4d}  FN {fn_:4d}  FP {fp:4d}  F1 {out[key]:.3f}")
print(out)
