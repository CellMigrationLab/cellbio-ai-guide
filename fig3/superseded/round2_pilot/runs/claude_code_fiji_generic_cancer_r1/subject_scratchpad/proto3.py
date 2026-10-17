import tifffile,numpy as np,warnings,sys;warnings.filterwarnings('ignore')
from scipy import ndimage as ndi
from skimage import measure,morphology,segmentation,io
a=tifffile.imread('/home/user/sessions/s002/image.tif').astype(np.float32)
f=a-ndi.gaussian_filter(a,40)
g=ndi.gaussian_filter(f,1)
print(np.std(g),np.percentile(g,[1,5,50,95,99]))
K=float(sys.argv[1])
dark=g<-K
dark=morphology.binary_closing(dark,morphology.disk(2))
mask=ndi.binary_fill_holes(dark)
mask=morphology.binary_opening(mask,morphology.disk(5))
dist=ndi.gaussian_filter(ndi.distance_transform_edt(mask),1)
mk=measure.label(morphology.h_maxima(dist,1.0))
lab=segmentation.watershed(-dist,mk,mask=mask)
out=np.zeros_like(lab);n=0
for r in measure.regionprops(lab):
    if r.area<250 or r.solidity<0.8: continue
    n+=1;out[lab==r.label]=n
print(n,sorted(int(r.area) for r in measure.regionprops(out)))
im=(a-a.min())/(a.max()-a.min());b=segmentation.find_boundaries(out)
rgb=np.dstack([im]*3);rgb[b]=[1,0,0];io.imsave('ov3.png',(rgb*255).astype(np.uint8))
