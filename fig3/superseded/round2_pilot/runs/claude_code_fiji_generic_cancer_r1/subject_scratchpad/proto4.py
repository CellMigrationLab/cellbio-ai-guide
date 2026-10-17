import tifffile,numpy as np,warnings,sys;warnings.filterwarnings('ignore')
from scipy import ndimage as ndi
from skimage import measure,morphology,segmentation,io,feature
a=tifffile.imread('/home/user/sessions/s002/image.tif').astype(np.float32)
f=a-ndi.gaussian_filter(a,40)
g=ndi.gaussian_filter(f,1)
m=ndi.uniform_filter(g,7); sd=np.sqrt(np.maximum(ndi.uniform_filter(g*g,7)-m*m,0))
T=float(sys.argv[1]);S=float(sys.argv[2]);MINA=int(sys.argv[3])
mask=sd>T
mask=morphology.binary_closing(mask,morphology.disk(3))
mask=ndi.binary_fill_holes(mask)
mask=morphology.binary_opening(mask,morphology.disk(5))
sm=ndi.gaussian_filter(sd,S)
dist=ndi.distance_transform_edt(mask)
comb=ndi.gaussian_filter(dist,2)*1.0+sm/sm.max()*0  # shape-based
pk=feature.peak_local_max(sm,min_distance=9,labels=measure.label(mask),exclude_border=False)
mk=np.zeros(mask.shape,int)
for i,(y,x) in enumerate(pk):mk[y,x]=i+1
lab=segmentation.watershed(-sm,mk,mask=mask)
out=np.zeros_like(lab);n=0
for r in measure.regionprops(lab,intensity_image=sd):
    if r.area<MINA or r.solidity<0.8 or r.mean_intensity<T*1.3: continue
    n+=1;out[lab==r.label]=n
print(n,sorted(int(r.area) for r in measure.regionprops(out)))
im=(a-a.min())/(a.max()-a.min());b=segmentation.find_boundaries(out)
rgb=np.dstack([im]*3);rgb[b]=[1,0,0];io.imsave('ov4.png',(rgb*255).astype(np.uint8))
tifffile.imwrite('lab4.tif',out.astype(np.uint16))
