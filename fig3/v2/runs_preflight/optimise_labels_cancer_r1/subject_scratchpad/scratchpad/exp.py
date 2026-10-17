import sys, numpy as np, tifffile, time
from scipy import ndimage as ndi
from skimage import filters
from cellpose import models
S='/tmp/claude-0/-home-user-sessions-v2-preflight-v009/698ddfa1-fd23-4860-bfed-5d5bd47f935b/scratchpad/'
img=tifffile.imread('image.tif').astype(np.float32)
bg=ndi.gaussian_filter(img,40); flat=img-bg
lo,hi=np.percentile(flat,[1,99]); 
m=models.CellposeModel(gpu=False)
for name,x,diam in [('raw',img,None),('flat',flat,None)]:
  for rescale in [1.0,0.66]:
    t=time.time()
    masks,flows,_=m.eval(x,diameter=None,rescale=rescale,normalize={'percentile':[1,99]},flow_threshold=0.4,cellprob_threshold=0.0,batch_size=4)
    tifffile.imwrite(f'{S}{name}_{rescale}.tif',masks.astype(np.int32))
    np.save(f'{S}{name}_{rescale}_prob.npy',flows[2] if len(flows)>2 else 0)
    print(name,rescale,masks.max(),time.time()-t,flush=True)
