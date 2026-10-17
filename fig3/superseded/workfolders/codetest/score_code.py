"""Run an LLM-written script in its own folder on the DAPI image (nuclei.tif) and score what it measured against the
manual nuclei: number of objects, object F1 (IoU >= 0.5), and the area of matched nuclei (script output vs manual)."""
import json, os, shutil, subprocess, sys
import numpy as np
import tifffile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
from matching import match

U = "<uploads>/"
PX = 0.649614
name, script = sys.argv[1], sys.argv[2]
d = os.path.join(os.path.dirname(os.path.abspath(__file__)), name)
os.makedirs(d, exist_ok=True)
shutil.copy(script, os.path.join(d, "script.py"))
tifffile.imwrite(os.path.join(d, "nuclei.tif"), tifffile.imread(U + "2453a2f8-GT_DAPI.tif"))
r = subprocess.run([sys.executable, "script.py"] + sys.argv[3:], cwd=d, capture_output=True, text=True, timeout=900)
out = {"name": name, "returncode": r.returncode, "stdout_tail": r.stdout[-1500:], "stderr_tail": r.stderr[-1500:]}
ref = tifffile.imread(U + "1add3634-104_3.tif").astype(int)
lab_path = next((os.path.join(d, f) for f in ("labels.tif", "labels.tiff", "nuclei_labels.tif") if os.path.exists(os.path.join(d, f))), None)
if lab_path:
    L = tifffile.imread(lab_path).astype(int)
    mt, fn, fp = match(ref, L, 0.5)
    out.update(n_objects=int(len(np.unique(L[L > 0]))), n_ref=int(len(np.unique(ref[ref > 0]))),
               f1=round(2 * len(mt) / (2 * len(mt) + len(fn) + len(fp)), 3))
    ra = np.array([(ref == g).sum() for g, p, _ in mt]) * PX ** 2
    la = np.array([(L == p).sum() for g, p, _ in mt]) * PX ** 2
    out.update(matched=len(mt), area_ratio_median=round(float(np.median(la / ra)), 3))
if os.path.exists(os.path.join(d, "areas.csv")):
    out["areas_csv_head"] = open(os.path.join(d, "areas.csv")).read()[:400]
json.dump(out, open(os.path.join(d, "result.json"), "w"), indent=1)
print(json.dumps({k: v for k, v in out.items() if k not in ("stdout_tail",)}, indent=1)[:2500])
