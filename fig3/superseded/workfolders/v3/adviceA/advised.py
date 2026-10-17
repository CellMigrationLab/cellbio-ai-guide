"""Settings recommended in the advice replies (Cellpose, diameter ~20 px, flow 0.4, cellprob 0, 'nuclei' model), run with
the installed Cellpose 4.2.1.1."""
import tifffile
from cellpose import models
img = tifffile.imread("../codeB/nuclei.tif")
m = models.CellposeModel(gpu=False, model_type="nuclei")
masks, _, _ = m.eval(img, diameter=20, flow_threshold=0.4, cellprob_threshold=0.0)
tifffile.imwrite("advised_labels.tif", masks.astype("uint16"))
print("objects", masks.max())
