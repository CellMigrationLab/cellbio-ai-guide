"""Score each Cellpose-SAM variant against the reference (whole field) and export its outlines for the panel a tiles."""
import json, os
from errors import errors
from export_window import export
from common.labels import read_labels

X, Y, W, H = 240, 40, 240, 260
runs = {"default": "../../fig1/source_data/full_field_labels/cellpose_sam_labels.tif", "down4": "panels/cp_down4.tif", "down2": "panels/cp_down2.tif",
        "nonorm": "panels/cp_nonorm.tif", "cellprob2": "panels/cp_cellprob2.tif", "postfilter": "panels/cp_postfilter.tif",
        "up2": "panels/cp_up2.tif", "file_minmax": "panels/cp_file_minmax.tif", "file_histeq": "panels/cp_file_histeq.tif",
        "file_clahe": "panels/cp_file_clahe.tif", "flow0.8": "panels/cp_flow0.8.tif"}
missing = [p for p in runs.values() if not os.path.exists(p)]
if missing:
    raise FileNotFoundError(f"Cellpose variant labels missing (run cellpose_perturb.py / postfilter.py 50): {missing}")
out, summ = {}, json.load(open("panels/error_summary.json"))   # written by errors.py, which must run first
for k, p in runs.items():
    L = read_labels(p)
    s, _ = errors(L)
    out[k] = s["f1"]
    summ["cellpose_" + k] = s
    export(L, X, Y, W, H, f"panels/ts_cp_{k}.json")
    print(k, s)
json.dump(out, open("panels/perturb_scores.json", "w"), indent=1)
json.dump(summ, open("panels/error_summary.json", "w"), indent=1)
