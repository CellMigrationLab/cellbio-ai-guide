"""Panel a on two fields: F1 of every Cellpose-SAM variant on field 104 (shown before) and field 209, and their mean.

Field 104 labels: panels/cp_<variant>.tif and the Fig. 1 default; field 209: panels/field209/cp_<variant>.tif (made by
norm_inputs.py, cellpose_perturb.py and postfilter.py with --field 209). The post-filter threshold (50) was chosen on
field 104 and is not re-tuned. Field-104 values must equal panels/perturb_scores.json (checked here).
Writes panels/perturb_scores_fields.json: {variant: {"104": f1, "209": f1, "mean": f1}}.
"""
import json

from common.labels import read_labels
from common.paths import RAW as U
from errors import errors

VARIANTS = ["default", "nonorm", "file_minmax", "file_histeq", "file_clahe", "down4", "down2", "up2", "cellprob2",
            "flow0.8", "postfilter"]


def label_path(field: int, variant: str) -> str:
    if field == 104:
        return ("../../fig1/source_data/full_field_labels/cellpose_sam_labels.tif" if variant == "default"
                else f"panels/cp_{variant}.tif")
    return f"panels/field{field}/cp_{variant}.tif"


def main() -> None:
    published = json.load(open("panels/perturb_scores.json"))
    out = {}
    refs = {f: read_labels(U + f"field{f}_cancer_cells_manual_labels.tif") for f in (104, 209)}
    for v in VARIANTS:
        f1 = {str(f): errors(read_labels(label_path(f, v), expected_shape=refs[f].shape), refs[f])[0]["f1"] for f in refs}
        if f1["104"] != published[v]:
            raise ValueError(f"{v}: field-104 F1 {f1['104']} differs from the published {published[v]}")
        out[v] = {**f1, "mean": round((f1["104"] + f1["209"]) / 2, 3)}
        print(v, out[v])
    json.dump(out, open("panels/perturb_scores_fields.json", "w"), indent=1, allow_nan=False)


if __name__ == "__main__":
    main()
