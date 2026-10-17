"""Run the Cellpose code the LLM suggested (Cellpose 3 style, as given) with the installed Cellpose, and record what happens.
A: models.Cellpose(gpu=False, model_type="nuclei")   (advice runs 1-3, 'Cellpose 3.x' example)
B: models.CellposeModel(gpu=False, model_type="nuclei") with channels=[0, 0], diameter=30   (advice run 3, 'newer Cellpose 3')"""
import io, json, logging, warnings, contextlib
import numpy as np
import tifffile
from importlib.metadata import version
log = io.StringIO()
logging.basicConfig(stream=log, level=logging.INFO)
warnings.simplefilter("always")
from cellpose import models
U = "<uploads>/"
img = tifffile.imread(U + "2453a2f8-GT_DAPI.tif")[:256, :256]
out = {"cellpose": version("cellpose")}
try:
    models.Cellpose(gpu=False, model_type="nuclei")
    out["A"] = "ran"
except Exception as e:
    out["A"] = f"{type(e).__name__}: {e}"
with warnings.catch_warnings(record=True) as w:
    m = models.CellposeModel(gpu=False, model_type="nuclei")
    masks, flows, styles = m.eval(img, diameter=30, channels=[0, 0])
    out["B"] = {"ran": True, "n_objects": int(masks.max()), "model_loaded": str(getattr(m, "pretrained_model", "")),
                "warnings": [str(x.message)[:200] for x in w]}
out["B"]["log_lines_mentioning_model_or_channels"] = [l for l in log.getvalue().splitlines() if any(k in l.lower() for k in ("model", "channel", "nuclei"))][:10]
json.dump(out, open("advice_run.json", "w"), indent=1)
print(json.dumps(out, indent=1))
