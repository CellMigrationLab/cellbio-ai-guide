"""Panel a on a second field: the settings shown in panel a (Cellpose-SAM default weights and settings; post-filter with
the contrast threshold 50 chosen on field 104) applied unchanged to field 209 and scored against its manual annotation.

Run from fig2/source_data (PYTHONPATH = repository root; needs Cellpose, environment/requirements-models.txt):
    python ../analysis/second_field_check.py
Writes ../analysis/second_field_check.json and ../analysis/field209_cellpose_sam_labels.tif (Cellpose output, zlib).
"""
import json
import sys

import numpy as np
import tifffile
from cellpose import models
from scipy import ndimage as ndi

sys.path.insert(0, "../code")
import postfilter as pf                                              # noqa: E402  (panel-a post-filter, same code)
from common.labels import read_labels, validate_labels               # noqa: E402
from common.matching import f1_score                                 # noqa: E402
from common.paths import raw_file                                    # noqa: E402

THRESHOLD = 50          # chosen on field 104 (fig2/README.md), not re-tuned
bf = tifffile.imread(raw_file("field209_brightfield.tif"))
ref = read_labels(raw_file("field209_cancer_cells_manual_labels.tif"), expected_shape=bf.shape)
masks = validate_labels(models.CellposeModel(gpu=False).eval(bf)[0], expected_shape=bf.shape)
tifffile.imwrite("../analysis/field209_cellpose_sam_labels.tif", masks.astype(np.uint16), compression="zlib")
pf.lsd = ndi.generic_filter(ndi.gaussian_filter(bf.astype(float), 1), np.std, size=7)   # contrast map of field 209
out = {"field": 209, "threshold": THRESHOLD, "default": f1_score(ref, masks),
       "postfilter": f1_score(ref, pf.postfilter(masks, THRESHOLD))}
json.dump(out, open("../analysis/second_field_check.json", "w"), indent=1, allow_nan=False)
print(out)
