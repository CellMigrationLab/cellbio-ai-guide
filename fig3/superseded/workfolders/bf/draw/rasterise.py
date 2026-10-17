"""Rasterise LLM-drawn ellipses (pixel coordinates of the 1024 x 1022 preview, identical to the field's pixel grid) into a
label image (later ellipses do not overwrite earlier ones), and score with object F1 against the manual cancer cells."""
import json, sys
import numpy as np
import tifffile
from skimage.draw import ellipse
sys.path.insert(0, "..")
from score_cancer import score
H, W = 1022, 1024
for m in sys.argv[1:]:
    E = json.load(open(f"{m}.json"))["cells"]
    L = np.zeros((H, W), np.int32)
    for i, e in enumerate(E, 1):
        rr, cc = ellipse(e["y"], e["x"], max(e["ry"], 1), max(e["rx"], 1), shape=(H, W), rotation=-np.deg2rad(e["angle_deg"]))
        free = L[rr, cc] == 0
        L[rr[free], cc[free]] = i
    tifffile.imwrite(f"{m}_labels.tif", L.astype(np.uint16))
    s = score(L); s["n_drawn"] = len(E); json.dump(s, open(f"{m}_score.json", "w")); print(m, s)
