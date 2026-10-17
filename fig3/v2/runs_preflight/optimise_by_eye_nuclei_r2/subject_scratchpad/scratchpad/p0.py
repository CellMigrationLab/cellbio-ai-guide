import tifffile as t,numpy as np,time,pickle
from cellpose import models
a=t.imread('image.tif').astype(np.float32)
m=models.CellposeModel(gpu=False)
t0=time.time()
lab,flow,_=m.eval(a,diameter=None,normalize={'percentile':[1,99]},flow_threshold=0.4,cellprob_threshold=0.0)
print(time.time()-t0,lab.max())
np.save('/tmp/claude-0/-home-user-sessions-v2-preflight-v006/8199e61d-e8ba-45a2-9fd6-cb7009967f28/scratchpad/lab0.npy',lab)
