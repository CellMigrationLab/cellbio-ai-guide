import sys, numpy as np, tifffile
from scipy import ndimage as ndi
from skimage import filters, morphology, segmentation, measure, feature
SIGMA=1.0; BG=40; BLOCK=101; OFFSET=0.0; MIN_AREA=80; SEED_SIGMA=3.0; MIN_DIST=6
img=tifffile.imread(sys.argv[1]).astype(float)
g=filters.gaussian(img,SIGMA)
bg=filters.gaussian(img,BG)
l=np.log1p(g)
t=filters.threshold_otsu(l)
loc=filters.threshold_local(l,BLOCK,offset=OFFSET)
m=(l>t-0.0)&(l>loc)
m=morphology.remove_small_objects(m,MIN_AREA); m=ndi.binary_fill_holes(morphology.binary_opening(m,morphology.disk(2)))
d=ndi.distance_transform_edt(m)
s=filters.gaussian(d,1)+ 0*filters.gaussian(img,SEED_SIGMA)
pk=feature.peak_local_max(s,min_distance=MIN_DIST,labels=measure.label(m),exclude_border=False)
mk=np.zeros(img.shape,int); mk[tuple(pk.T)]=np.arange(1,len(pk)+1)
lab=segmentation.watershed(-s,mk,mask=m)
lab=morphology.remove_small_objects(lab,MIN_AREA)
lab,_,_=segmentation.relabel_sequential(lab)
tifffile.imwrite(sys.argv[2],lab.astype(np.int32))
