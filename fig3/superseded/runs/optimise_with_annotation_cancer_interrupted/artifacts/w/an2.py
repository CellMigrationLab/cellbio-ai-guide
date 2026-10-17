import numpy as np,tifffile as t
from skimage.measure import regionprops
from skimage.morphology import binary_dilation,disk
from skimage.filters import sobel,gaussian
a=t.imread('bf_dev.tif').astype(float);g=t.imread('annot_dev.tif');p=t.imread('w/cp30.tif')
gm=sobel(gaussian(a,1))
for r in regionprops(p):
    m=p==r.label
    if r.area>900 and a[m].std()<100: continue
    ov=np.bincount(g[m]).copy();ov[0]=0
    gl=ov.argmax();iou=ov.max()/(m.sum()+(g==gl).sum()-ov.max()) if ov.max() else 0
    ring=binary_dilation(m,disk(6))&~binary_dilation(m,disk(1))&(p==0)
    bd=m&~binary_dilation(~m,disk(2))
    bd=binary_dilation(m,disk(1))&~m|bd
    print('TP' if iou>=.5 else 'FP',int(r.area),'std%d'%a[m].std(),'grad%d'%gm[bd].mean(),'ringstd%d'%a[ring].std() if ring.any() else '', 'cont%d'%(a[m].mean()-a[ring].mean()) if ring.any() else '', 'bord' if r.bbox[0]==0 or r.bbox[1]==0 or r.bbox[2]>=1022 or r.bbox[3]>=512 else '')
