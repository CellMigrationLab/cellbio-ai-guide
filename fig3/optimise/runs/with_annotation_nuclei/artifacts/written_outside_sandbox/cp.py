import tifffile,numpy as np
from cellpose import models
img=tifffile.imread("<fig3-work>/bf3/ref_nuclei/dapi_dev.tif").astype(np.float32)
m=models.CellposeModel(gpu=False)
for d in [23]:
    l,_,_=m.eval(img,diameter=d,flow_threshold=0.4,cellprob_threshold=0.0)
    tifffile.imwrite("cp_%d.tif"%d,l.astype(np.int32))
