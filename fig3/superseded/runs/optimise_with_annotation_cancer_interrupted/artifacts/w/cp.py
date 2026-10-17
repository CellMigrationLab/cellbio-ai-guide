import numpy as np,tifffile as t
from cellpose import models
a=t.imread('bf_dev.tif').astype(np.float32)
m=models.CellposeModel(gpu=False)
for d in (30,):
    l,_,_=m.eval(a,diameter=d)
    t.imwrite('w/cp%d.tif'%d,l.astype(np.int32));print(d,l.max())
