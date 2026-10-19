import sys,time,numpy as np,tifffile
from cellpose import models
from skimage import transform, filters, measure, morphology
import scipy.ndimage as ndi
a=tifffile.imread('image.tif').astype(np.float32)
p1=tifffile.imread('work/b06.tif')
cancer=np.zeros(a.shape,bool)
for r in measure.regionprops(p1):
    if r.area*0.65**2<700 and r.solidity>0.9: cancer[p1==r.label]=True
print('cancer objs',len(np.unique(p1[cancer])))
cancer=morphology.binary_dilation(cancer,morphology.disk(4))
bg=filters.gaussian(a,40); sd=np.sqrt(filters.gaussian((a-bg)**2,40)); n=(a-bg)/sd
# normalised convolution fill
w=(~cancer).astype(np.float32)
fill=filters.gaussian(n*w,6)/np.maximum(filters.gaussian(w,6),1e-3)
n2=np.where(cancer,fill,n)
tifffile.imwrite('work/n2.tif',n2.astype(np.float32))
s=float(sys.argv[1])
x=transform.rescale(n2,s,order=1,anti_aliasing=True).astype(np.float32)
mod=models.CellposeModel(gpu=False)
t=time.time()
m,flows,_=mod.eval(x,normalize=True,flow_threshold=0.4,cellprob_threshold=0.0)
print('time',time.time()-t,m.max())
np.savez('work/flows_%s.npz'%sys.argv[1],dP=flows[1],cp=flows[2])
m=transform.resize(m,a.shape,order=0,preserve_range=True,anti_aliasing=False).astype(np.int32)
tifffile.imwrite('work/e1.tif',m)
