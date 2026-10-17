import sys,numpy as np,tifffile
sys.path.insert(0,'<fig3-work>/bf3/ref_endo/w')
from score import f1
from cellpose import models
from scipy.ndimage import gaussian_filter
b=tifffile.imread('../bf_dev.tif').astype(float);gt=tifffile.imread('../annot_dev.tif')
bg=gaussian_filter(b,40);x=b-bg
x=gaussian_filter(x,1)
lo,hi=np.percentile(x,[1,99]);x=np.clip((x-lo)/(hi-lo),0,1)
m=models.CellposeModel(gpu=False)
for d in [70,90]:
  for ct in [0.0]:
    l,_,_=m.eval(x,diameter=d,cellprob_threshold=ct,flow_threshold=0.4)
    np.save(f'l_{d}_{ct}.npy',l);print(d,ct,l.max(),f1(l,gt),flush=True)
