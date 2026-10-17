"""SQUIRREL (NanoPyx implementation, nanopyx.methods.squirrel.calculate_error_map) on the super-resolution example:
the diffraction-limited low-res image is the reference; the RCAN prediction and the acquired high-res image are each
compared with it. Outputs the error maps and RSE / RSP."""
import json, time, warnings
import numpy as np
import tifffile
from importlib.metadata import version
warnings.filterwarnings("ignore")
from nanopyx.methods.squirrel import calculate_error_map

from common.paths import RAW as U
lr = tifffile.imread(U + "biosr_er_lowres_input.tif").astype(np.float32)
pr = tifffile.imread(U + "biosr_er_rcan_prediction.tif").astype(np.float32)
hr = tifffile.imread(U + "biosr_er_highres_reference.tif").astype(np.float32)
out = {"nanopyx": version("nanopyx")}
for name, sr in [("predicted", pr), ("high_res", hr)]:
    t0 = time.time()
    em, rse, rsp = calculate_error_map(lr, sr)
    tifffile.imwrite(f"panels/squirrel_{name}.tif", em)
    out[name] = {"RSE": round(float(rse), 3), "RSP": round(float(rsp), 4), "map_shape": list(em.shape), "s": round(time.time() - t0)}
    print(name, out[name], flush=True)
json.dump(out, open("panels/squirrel.json", "w"), indent=1)
