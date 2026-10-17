import sys,warnings;warnings.filterwarnings('ignore');sys.path.insert(0,'/tmp/claude-0/-home-user-sessions-v2-preflight-v004/e87ee74b-7a0c-4d9a-9fa4-25ce888c2151/scratchpad')
import numpy as np,tifffile as t
from scipy import ndimage as ndi
from cellpose import models
from ev import *
a=t.imread('image.tif').astype(np.float32);gt=t.imread('annotation.tif')
def prep(sig_bg,smooth,lp):
    x=a-ndi.gaussian_filter(a,sig_bg)
    if smooth: x=ndi.gaussian_filter(x,smooth)
    lo,hi=np.percentile(x,[lp,100-lp]);return (x-lo)/(hi-lo)
m=models.CellposeModel(gpu=False)
for d,ft,cp,sm in [(70,0.4,0,0),(90,0.4,0,0),(50,0.4,-2,0),(50,0.4,0,2),(70,0.4,-2,2),(70,0.8,-2,0)]:
    lab,_,_=m.eval(prep(50,sm,1),diameter=d,flow_threshold=ft,cellprob_threshold=cp)
    print(d,ft,cp,sm,f1(gt,lab),stats(lab),flush=True)
