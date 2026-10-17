"""Panel c step-3 F1 scores: object-level F1 against the manual annotation, greedy one-to-one matching at IoU >= 0.5
(common/matching.py), over the whole field. The only writer of panel_c_step3/A_scores.json (key order as published)."""
import json

from common.matching import match

from common.paths import raw_file
from fig1_paths import CELLPOSE_LABELS, THRESHOLD_LABELS  # relative to fig1/source_data (run from there)
from common.labels import read_labels

ref = read_labels(raw_file("field104_cancer_cells_manual_labels.tif"))
out = {}
for key, fn in [("classical", THRESHOLD_LABELS), ("cellpose", CELLPOSE_LABELS), ("stardist", None)]:
    pr = read_labels(raw_file("field104_cancer_cells_stardist_custom_labels.tif") if fn is None else fn)
    tp, fn_, fp = (len(s) for s in match(ref, pr, 0.5))
    out[key] = round(2 * tp / (2 * tp + fp + fn_), 3)
    print(f"{key:10s} TP {tp:4d}  FN {fn_:4d}  FP {fp:4d}  F1 {out[key]:.3f}")
print(out)
scores = {k: out[k] for k in ("stardist", "cellpose", "classical")}
json.dump(scores, open("panel_c_step3/A_scores.json", "w"))
