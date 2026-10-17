"""Run the generalist Cellpose-SAM model (default weights) on the whole brightfield field, for comparison with StarDist."""
import time
import numpy as np
import tifffile
from importlib.metadata import version
from cellpose import models

from common.paths import RAW as U
bf = tifffile.imread(U + "field104_brightfield.tif")
model = models.CellposeModel(gpu=False)          # default Cellpose-SAM weights (cpsam), no retraining
t0 = time.time()
masks, _, _ = model.eval(bf)                     # default settings
print(f"cellpose {version('cellpose')}: {masks.max()} objects in {time.time()-t0:.0f}s")
tifffile.imwrite("panel_c_step3/BF_cellpose_sam_labels.tif", masks.astype(np.uint16))
