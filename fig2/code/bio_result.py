"""The biological result each segmentation gives (whole field): cell count and mean cell area in µm², vs the manual reference."""
import json
import numpy as np
import tifffile

from common.paths import RAW as U
PX = 0.649614
labs = {"reference": U + "field104_cancer_cells_manual_labels.tif", "custom_trained": U + "field104_cancer_cells_stardist_custom_labels.tif",
        "generalist_default": "../../fig1/source_data/full_field/cellpose_sam_labels.tif", "generalist_postfilter": "data/cp_postfilter.tif"}
out = {}
for k, p in labs.items():
    L = tifffile.imread(p).astype(int)
    ids, areas = np.unique(L[L > 0], return_counts=True)
    out[k] = {"count": int(len(ids)), "mean_area_um2": round(float(areas.mean() * PX ** 2), 1)}
for k in out:
    out[k]["count_vs_ref_pct"] = round(100 * (out[k]["count"] / out["reference"]["count"] - 1), 1)
    out[k]["area_vs_ref_pct"] = round(100 * (out[k]["mean_area_um2"] / out["reference"]["mean_area_um2"] - 1), 1)
json.dump(out, open("data/bio_result.json", "w"), indent=1)
for k, v in out.items():
    print(k, v)
