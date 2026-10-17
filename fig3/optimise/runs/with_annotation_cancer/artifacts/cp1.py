import numpy as np, tifffile, sys
from cellpose import models
img=tifffile.imread('bf_dev.tif').astype(np.float32)
m=models.CellposeModel(gpu=False)
for name,kw in [('d30',dict(diameter=30)),('d30_ft',dict(diameter=30,flow_threshold=0.6,cellprob_threshold=-1))]:
    lab,_,_=m.eval(img,**kw)
    tifffile.imwrite(f'/tmp/cp_{name}.tif',lab.astype(np.int32)); print(name,lab.max(),flush=True)
