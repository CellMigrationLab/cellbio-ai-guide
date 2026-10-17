# Recovered verbatim from the session transcript (2026-10-16T05:58:01.289Z).
# Last shell command that wrote data/panelA_acquired_crop.png. Paths are those of the original working folder.
cd <work2>/fig1 && cat > segment_panelA.py <<'EOF'
"""Segment the panel A crop with Cellpose (Cellpose-SAM generalist model) and export matching label image."""
import time
import numpy as np
import tifffile
from PIL import Image
from importlib.metadata import version
from cellpose import models

F = ("<uploads>/"
     "14715134-MAX_2026.02.24_ECs_AsPC-1perfusion26.02.13-2.sld_-_HPMEC_ctrl_-_Position_1-1.tif")
img = tifffile.imread(F)
X0, Y0, W, H = 0, 1248, 600, 800          # figure crop (native pixels)
M = 200                                    # context margin for segmentation
sx0, sy0 = max(0, X0 - M), max(0, Y0 - M)
sx1, sy1 = min(img.shape[1], X0 + W + M), min(img.shape[0], Y0 + H + M)
region = img[sy0:sy1, sx0:sx1]

# acquired crop (display only: linear 100-600 -> 0-255)
crop = img[Y0:Y0 + H, X0:X0 + W].astype(np.float32)
Image.fromarray(np.round(np.clip((crop - 100) / 500, 0, 1) * 255).astype(np.uint8)).save("data/panelA_acquired_crop.png")
print("crop", crop.shape, "clipped fraction", float((crop > 600).mean()))

model = models.CellposeModel(gpu=False)    # default Cellpose-SAM weights
t = time.time()
masks, flows, styles = model.eval(region)  # raw uint16 in; Cellpose normalises internally (default percentiles)
print(f"cellpose {version('cellpose')} eval {time.time()-t:.1f}s, objects in region: {masks.max()}")
lab = masks[Y0 - sy0:Y0 - sy0 + H, X0 - sx0:X0 - sx0 + W]
ids = np.unique(lab[lab > 0])
print("objects in crop:", len(ids))
tifffile.imwrite("data/panelA_cellpose_labels.tif", lab.astype(np.uint16))
EOF
../cpenv/bin/python -I segment_panelA.py 2>&1 | grep -v Warning | tail -8
