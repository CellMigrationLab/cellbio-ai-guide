import numpy as np,tifffile,sys
from skimage import filters
from cellpose import models
from score import f1
g=tifffile.imread('annot_dev.tif')
img=tifffile.imread('bf_dev.tif').astype(np.float32)
m=models.CellposeModel(gpu=False)
def prep(sig_bg,sm):
    x=img-filters.gaussian(img,sig_bg)
    if sm: x=filters.gaussian(x,sm)
    lo,hi=np.percentile(x,[0.5,99.5]);return np.clip((x-lo)/(hi-lo),0,1)
for name,(sb,sm,d) in {'d40':(50,0,40),'d70':(50,0,70),'smooth2_d60':(50,2,60),'d90':(50,0,90)}.items():
    x=prep(sb,sm)
    for cp in (-2,0):
        l=m.eval(x,diameter=d,flow_threshold=0.4,cellprob_threshold=cp)[0]
        print(name,cp,f1(l,g),flush=True)
