import sys;sys.path.insert(0,'/tmp/claude-0/-home-user-sessions-v2-preflight-v004/e87ee74b-7a0c-4d9a-9fa4-25ce888c2151/scratchpad')
import numpy as np,tifffile as t,time
from scipy import ndimage as ndi
from cellpose import models
from ev import *
a=t.imread('image.tif').astype(np.float32);gt=t.imread('annotation.tif')
bg=ndi.gaussian_filter(a,50);x=a-bg
lo,hi=np.percentile(x,[1,99]);x=(x-lo)/(hi-lo)
m=models.CellposeModel(gpu=False)
for d in [50]:
    t0=time.time()
    lab,_,_=m.eval(x,diameter=d,flow_threshold=0.4,cellprob_threshold=0.0)
    print(d,time.time()-t0,f1(gt,lab),stats(lab),stats(gt))
    np.save(f'/tmp/claude-0/-home-user-sessions-v2-preflight-v004/e87ee74b-7a0c-4d9a-9fa4-25ce888c2151/scratchpad/lab{d}.npy',lab)
