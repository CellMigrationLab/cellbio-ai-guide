import numpy as np,tifffile as t
from skimage.measure import regionprops
a=t.imread('bf_dev.tif').astype(float);g=t.imread('annot_dev.tif');p=t.imread('w/cp30.tif')
for r in regionprops(p,intensity_image=a):
    m=p==r.label;ov=np.bincount(g[m]).copy();ov[0]=0
    gl=ov.argmax();iou=ov.max()/(m.sum()+(g==gl).sum()-ov.max()) if ov.max() else 0
    print(r.label,int(r.area),round(r.solidity,2),round(r.eccentricity,2),round(r.intensity_mean),round(a[m].std()),round(iou,2),'TP' if iou>=.5 else 'FP', int(r.centroid[1]),int(r.centroid[0]))
