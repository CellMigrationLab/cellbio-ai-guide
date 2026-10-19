import sys,time,numpy as np,tifffile,torch
sys.path.insert(0,'work')
from prep import *
from cellpose import models
model=sys.argv[1]; out=sys.argv[2]
a=tifffile.imread('image.tif'); n=down(flatten(a))
mod=models.CellposeModel(gpu=False,pretrained_model=model,use_bfloat16=False)
t=time.time()
m,flows,_=mod.eval(n,normalize=True,flow_threshold=0.4,cellprob_threshold=0.0,min_size=30)
print('time',time.time()-t,m.max())
np.savez(out.replace('.tif','_flows.npz'),dP=flows[1],cp=flows[2])
m=transform.resize(m,a.shape,order=0,preserve_range=True,anti_aliasing=False).astype(np.int32)
tifffile.imwrite(out,m)
