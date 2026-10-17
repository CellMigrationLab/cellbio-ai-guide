"""Figure 3 assets: (b) one DAPI region with nuclei from the vague-prompt and Box-1-prompt code and the manual nuclei;
(c) the development / held-out split of the DAPI field; (d) example count crops."""
import json, sys
import numpy as np
import tifffile
from PIL import Image
sys.path.insert(0, "<work2>/fig2")
from export_window import export

U = "<uploads>/"
dapi = tifffile.imread(U + "2453a2f8-GT_DAPI.tif").astype(float)
ref = tifffile.imread(U + "1add3634-104_3.tif").astype(int)
cancer = tifffile.imread(U + "e752a357-104_2.tif").astype(int)
lo, hi = np.percentile(dapi, [0.3, 99.7])
# (b) region of HUVEC nuclei without cancer cells, with touching nuclei
best = None
for y in range(0, 1022 - 200, 20):
    for x in range(0, 1024 - 200, 20):
        if (cancer[y:y + 200, x:x + 200] > 0).any():
            continue
        n = len(np.unique(ref[y:y + 200, x:x + 200])) - 1
        if best is None or n > best[0]:
            best = (n, y, x)
n, Y, X = best
W = 200
g = np.clip((dapi[Y:Y + W, X:X + W] - lo) / (hi - lo), 0, 1)
Image.fromarray(np.round(np.repeat(np.repeat(g, 2, 0), 2, 1) * 255).astype(np.uint8)).save("assets/code_dapi.png")
for name, path in [("manual", None), ("vague", "codetest/vague/labels.tif"), ("box1", "codetest/box1/labels.tif")]:
    L = ref if path is None else tifffile.imread(path).astype(int)
    export(L, X, Y, W, W, f"assets/code_{name}.json")
json.dump({"y": Y, "x": X, "w": W, "n_manual": int(n)}, open("assets/code_roi.json", "w"))
print("code roi", Y, X, n)
# (c) whole DAPI field (dev = top half, held-out = bottom half)
G = np.clip((dapi - lo) / (hi - lo), 0, 1)
Image.fromarray((G * 255).astype(np.uint8)).resize((512, 511), Image.LANCZOS).save("assets/agent_field.png")
