import tifffile,numpy as np,warnings;warnings.filterwarnings('ignore')
from scipy import ndimage as ndi
from skimage import measure,morphology,segmentation,io
a=tifffile.imread('/home/user/sessions/s002/image.tif').astype(np.float32)
f=a-ndi.gaussian_filter(a,50)
g=ndi.gaussian_filter(f,1)
m=ndi.uniform_filter(g,7); sd=np.sqrt(np.maximum(ndi.uniform_filter(g*g,7)-m*m,0))
mask=sd>90
mask=morphology.binary_closing(mask,morphology.disk(3))
mask=ndi.binary_fill_holes(mask)
mask=morphology.binary_opening(mask,morphology.disk(6))
dist=ndi.gaussian_filter(ndi.distance_transform_edt(mask),1)
mk=measure.label(morphology.h_maxima(dist,1.5))
lab=segmentation.watershed(-dist,mk,mask=mask)
out=np.zeros_like(lab);n=0
for r in measure.regionprops(lab):
    if r.area<300 or r.solidity<0.85: continue
    n+=1;out[lab==r.label]=n
print(n,sorted(int(r.area) for r in measure.regionprops(out)))
im=(a-a.min())/(a.max()-a.min());b=segmentation.find_boundaries(out)
rgb=np.dstack([im]*3);rgb[b]=[1,0,0];io.imsave('ov2.png',(rgb*255).astype(np.uint8))
