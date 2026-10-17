"""A real, logged agent-style optimisation: Cellpose-SAM on acquired DAPI (HUVEC nuclei), scored against manual annotation.

Development region: rows 0-511 (left half of field); held-out test region: rows 510-1021, never used while tuning.
Metric: F1 at IoU >= 0.5 (one-to-one matching). Each configuration is logged with its code change.
"""
import json, time
import numpy as np
import tifffile
from cellpose import models
from importlib.metadata import version
from common.matching import match

from common.paths import RAW as U
dapi = tifffile.imread(U + "field104_dapi.tif")
ref = tifffile.imread(U + "field104_endothelial_nuclei_manual_labels.tif").astype(int)
DEV = (slice(0, 512), slice(0, 512))
TEST = (slice(510, 1022), slice(512, 1024))
model = models.CellposeModel(gpu=False)
log = {"cellpose": version("cellpose"), "dev": "rows 0-511, cols 0-511", "test": "rows 510-1021, cols 512-1023", "runs": []}


def f1(region, kw):
    t0 = time.time()
    m, _, _ = model.eval(dapi[region], **kw)
    mt, fn, fp = match(ref[region], m.astype(int))
    tp = len(mt)
    return 2 * tp / (2 * tp + len(fn) + len(fp)), m, time.time() - t0, (tp, len(fn), len(fp))


configs = [("defaults", {}),
           ("diameter=30 (expected nucleus size)", {"diameter": 30}),
           ("diameter=30, flow_threshold=0.6", {"diameter": 30, "flow_threshold": 0.6}),
           ("diameter=30, cellprob_threshold=-1", {"diameter": 30, "cellprob_threshold": -1.0})]
best = None
for name, kw in configs:
    sc, m, dt, c = f1(DEV, kw)
    log["runs"].append({"set": "development", "change": name, "kw": kw, "f1": round(sc, 3), "tp_fn_fp": c, "s": round(dt)})
    print(name, round(sc, 3), c, f"{dt:.0f}s", flush=True)
    if best is None or sc > best[0]:
        best = (sc, name, kw, m)
sc, m, dt, c = f1(TEST, best[2])
log["frozen"] = best[1]
log["runs"].append({"set": "held-out test", "change": "frozen: " + best[1], "kw": best[2], "f1": round(sc, 3), "tp_fn_fp": c, "s": round(dt)})
print("TEST", best[1], round(sc, 3), c, flush=True)
tifffile.imwrite("panel_c_step5/test_masks.tif", m.astype(np.uint16))
tifffile.imwrite("panel_c_step5/dev_masks_best.tif", best[3].astype(np.uint16))
json.dump(log, open("panel_c_step5/agent_log.json", "w"), indent=1)
