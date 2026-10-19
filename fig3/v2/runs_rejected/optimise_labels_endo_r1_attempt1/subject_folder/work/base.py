import sys,time,numpy as np,tifffile
from cellpose import models
from skimage import transform, filters
a=tifffile.imread('image.tif').astype(np.float32)
scale=float(sys.argv[1]); 
bg=filters.gaussian(a,40); sd=np.sqrt(filters.gaussian((a-bg)**2,40))
n=(a-bg)/sd
if scale!=1: n=transform.rescale(n,scale,order=1,anti_aliasing=True)
mod=models.CellposeModel(gpu=False)
t=time.time()
m,_,_=mod.eval(n.astype(np.float32),normalize=True,flow_threshold=0.4,cellprob_threshold=float(sys.argv[2]))
print('time',time.time()-t,m.max())
if scale!=1: m=transform.resize(m,a.shape,order=0,preserve_range=True,anti_aliasing=False).astype(np.int32)
tifffile.imwrite(sys.argv[3],m.astype(np.int32))
