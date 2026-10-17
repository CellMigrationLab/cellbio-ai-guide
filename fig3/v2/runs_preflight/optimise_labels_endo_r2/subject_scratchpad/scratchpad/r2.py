import sys,warnings;warnings.filterwarnings('ignore');sys.path.insert(0,'/tmp/claude-0/-home-user-sessions-v2-preflight-v004/e87ee74b-7a0c-4d9a-9fa4-25ce888c2151/scratchpad')
import numpy as np,tifffile as t
from scipy import ndimage as ndi
from cellpose import models
a=t.imread('image.tif').astype(np.float32)
x=a-ndi.gaussian_filter(a,50);lo,hi=np.percentile(x,[1,99]);x=(x-lo)/(hi-lo)
m=models.CellposeModel(gpu=False)
lab,_,_=m.eval(x,diameter=70,flow_threshold=0.4,cellprob_threshold=0)
np.save(sys.argv[1],lab)
