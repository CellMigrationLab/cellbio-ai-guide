from scipy import ndimage as ndi
import numpy as np, tifffile, pandas as pd
from skimage import measure, segmentation, morphology, io, filters
from cellpose import models
UM=0.65
a=tifffile.imread('bf.tif').astype(float)
bg=filters.gaussian(a,50)
n=a-bg
n_raw=n.copy()
n=(n-np.percentile(n,0.5))/(np.percentile(n,99.5)-np.percentile(n,0.5))
n=np.clip(n,0,1)
import os
if os.path.exists('raw_masks.tif'):      # cache of the Cellpose output (delete to recompute from scratch)
    lab=tifffile.imread('raw_masks.tif')
else:
    m=models.CellposeModel(gpu=False)
    lab=m.eval(n,diameter=30,flow_threshold=0.4,cellprob_threshold=0.0)[0]
    tifffile.imwrite('raw_masks.tif',lab.astype(np.uint16))
# filter: remove small debris, border-truncated tiny pieces
out=np.zeros_like(lab);k=0
for r in measure.regionprops(lab):
    if r.area<250: continue          # ~ <10 um diameter = debris
    if r.area>1300: continue         # >~ 1300 px (~550 um2): endothelial cells (cancer cells are round, 300-1100 px)
    if r.solidity<0.9: continue
    msk=lab==r.label
    # cancer cells are textured/refractile with a dark rim; flat polygonal endothelial leftovers are not
    rim=msk&~ndi.binary_erosion(msk,iterations=3)
    if n_raw[msk].std()<90 and n_raw[rim].min()>-300: continue
    k+=1; out[msk]=k
lab=out
tifffile.imwrite('labels.tif',lab.astype(np.uint16))
rp=measure.regionprops(lab)
pd.DataFrame({'label':[r.label for r in rp],'area_px':[r.area for r in rp],'area_um2':[r.area*UM**2 for r in rp],
 'centroid_y':[r.centroid[0] for r in rp],'centroid_x':[r.centroid[1] for r in rp]}).to_csv('areas.csv',index=False)
b=segmentation.mark_boundaries(np.dstack([n]*3),lab,color=(1,0,0))
io.imsave('overlay.png',(b*255).astype('uint8'))
print(k, np.median([r.area for r in rp]))
