"""Panel d row 2: grayscale split tiles for the ROI (left half predicted, right half acquired), one per channel.
Each half is stretched to its own 0.3-99.7th percentiles (predicted and acquired are in different units)."""
import json
import numpy as np
import tifffile
from PIL import Image

from common.paths import RAW as U
R = json.load(open("panels/roi.json"))
X, Y, W, H = R["x"], R["y"], R["w"], R["h"]


def lin(a):
    lo, hi = np.percentile(a, [0.3, 99.7])
    return np.clip((a - lo) / (hi - lo), 0, 1)


for key, acq, prd in [("dapi", "field104_dapi.tif", "field104_pix2pix_predicted_dapi.tif"), ("pecam", "field104_pecam1.tif", "field104_pix2pix_predicted_pecam1.tif")]:
    a = lin(tifffile.imread(U + acq).astype(float)[Y:Y + H, X:X + W])
    p = lin(tifffile.imread(U + prd)[1:1023].astype(float)[Y:Y + H, X:X + W])
    s = np.concatenate([p[:, :W // 2], a[:, W // 2:]], 1)
    Image.fromarray(np.round(np.repeat(np.repeat(s, 2, 0), 2, 1) * 255).astype(np.uint8)).save(f"panels/roi_{key}_split.png")
print("ok")
