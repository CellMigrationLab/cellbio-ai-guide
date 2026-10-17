"""Score each Cellpose-SAM variant against the reference (whole field) and export its outlines for the panel b window."""
import json, os
import tifffile
from errors import errors
from export_window import export

X, Y, W, H = 240, 40, 240, 260
runs = {"default": "../../fig1/source_data/full_field/cellpose_sam_labels.tif", "down4": "data/cp_down4.tif", "down2": "data/cp_down2.tif",
        "nonorm": "data/cp_nonorm.tif", "cellprob2": "data/cp_cellprob2.tif", "postfilter": "data/cp_postfilter.tif",
        "up2": "data/cp_up2.tif", "file_minmax": "data/cp_file_minmax.tif", "file_histeq": "data/cp_file_histeq.tif",
        "file_clahe": "data/cp_file_clahe.tif", "flow0.8": "data/cp_flow0.8.tif"}
out, summ = {}, json.load(open("data/error_summary.json"))
for k, p in runs.items():
    if not os.path.exists(p):
        out[k] = None
        continue
    L = tifffile.imread(p).astype(int)
    s, _ = errors(L)
    out[k] = s["f1"]
    summ["cellpose_" + k] = s
    export(L, X, Y, W, H, f"data/ts_cp_{k}.json")
    print(k, s)
json.dump(out, open("data/perturb_scores.json", "w"), indent=1)
json.dump(summ, open("data/error_summary.json", "w"), indent=1)
