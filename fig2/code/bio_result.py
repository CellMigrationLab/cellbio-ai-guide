"""The biological result each segmentation gives (whole field): cell count and mean cell area in µm², vs the manual reference."""
import json
import numpy as np

from common.paths import RAW as U
from common.metadata import FOLLAIN_PX_UM as PX
from common.labels import read_labels
labs = {"reference": U + "field104_cancer_cells_manual_labels.tif", "custom_trained": U + "field104_cancer_cells_stardist_custom_labels.tif",
        "generalist_default": "../../fig1/source_data/full_field_labels/cellpose_sam_labels.tif", "generalist_postfilter": "panels/cp_postfilter.tif"}
out = {}
for k, p in labs.items():
    L = read_labels(p)
    ids, areas = np.unique(L[L > 0], return_counts=True)
    if not len(ids):
        raise ValueError(f"{k}: no objects in {p}")
    out[k] = {"count": int(len(ids)), "mean_area_um2": float(areas.mean() * PX ** 2)}
ref_count, ref_area = out["reference"]["count"], out["reference"]["mean_area_um2"]
for k in out:   # comparisons from unrounded values; rounded only for the output
    out[k]["count_vs_ref_pct"] = round(100 * (out[k]["count"] / ref_count - 1), 1)
    out[k]["area_vs_ref_pct"] = round(100 * (out[k]["mean_area_um2"] / ref_area - 1), 1)
    out[k]["mean_area_um2"] = round(out[k]["mean_area_um2"], 1)
json.dump(out, open("panels/bio_result.json", "w"), indent=1)
for k, v in out.items():
    print(k, v)
