"""SQUIRREL (NanoPyx implementation, nanopyx.methods.squirrel.calculate_error_map) on the super-resolution example:
the diffraction-limited low-res image is the reference; the RCAN prediction and the acquired high-res image are each
compared with it. Outputs the error maps and RSE / RSP."""
import json, time, warnings
import numpy as np
import tifffile
from importlib.metadata import version
with warnings.catch_warnings(record=True) as import_warnings:   # recorded and printed, not hidden
    warnings.simplefilter("always")
    from nanopyx.methods.squirrel import calculate_error_map
for w in import_warnings:
    print(f"warning while importing NanoPyx: {w.category.__name__}: {w.message}")

from common.paths import RAW as U
lr = tifffile.imread(U + "biosr_er_lowres_input.tif").astype(np.float32)
pr = tifffile.imread(U + "biosr_er_rcan_prediction.tif").astype(np.float32)
hr = tifffile.imread(U + "biosr_er_highres_reference.tif").astype(np.float32)
out = {"nanopyx": version("nanopyx")}
for name, sr in [("predicted", pr), ("high_res", hr)]:
    t0 = time.time()
    with warnings.catch_warnings(record=True) as run_warnings:
        warnings.simplefilter("always")
        em, rse, rsp = calculate_error_map(lr, sr)
    for w in run_warnings:
        print(f"warning in SQUIRREL ({name}): {w.category.__name__}: {w.message}")
    tifffile.imwrite(f"panels/squirrel_{name}.tif", em)
    out[name] = {"RSE": round(float(rse), 3), "RSP": round(float(rsp), 4), "map_shape": list(em.shape)}
    print(name, out[name], f"{time.time() - t0:.0f} s", flush=True)   # runtime is logged, not stored with the results
json.dump(out, open("panels/squirrel.json", "w"), indent=1)
