import numpy as np, tifffile, csv
from PIL import Image
from scipy import ndimage as ndi
from cellpose import models
UM=0.65
img=tifffile.imread('nuclei.tif').astype(np.float32)
# background flatten + normalise
bg=ndi.gaussian_filter(ndi.minimum_filter(ndi.gaussian_filter(img,2),41),20)
x=img-bg; x=np.clip(x/np.percentile(x,99.8),0,1.5)
model=models.CellposeModel(gpu=False)
lab=model.eval(x,diameter=20,flow_threshold=0.4,cellprob_threshold=-1.0)[0]
# cleanup: fill holes, drop debris < 95 px (~40 um2)
out=np.zeros(lab.shape,np.int32); k=0
objs=ndi.find_objects(lab)
for l,sl in enumerate(objs,1):
    if sl is None: continue
    m=ndi.binary_fill_holes(lab[sl]==l)
    if m.sum()<95: continue
    k+=1; o=out[sl]; o[m&(o==0)]=k
lab=out
tifffile.imwrite('labels.tif',lab)
cnt=np.bincount(lab.ravel())[1:]
with open('areas.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(['label','area_px','area_um2'])
    for i,c in enumerate(cnt,1): w.writerow([i,int(c),round(c*UM*UM,2)])
a=cnt*UM*UM
print(len(a),a.mean(),np.median(a),a.min(),a.max())
v=(np.clip(img/np.percentile(img,99.8),0,1)**0.6*255).astype('uint8')
ov=np.dstack([v]*3)
edge=lab>0
edge&=(ndi.maximum_filter(lab,3)!=ndi.minimum_filter(lab,3))|(ndi.minimum_filter(lab,3)==0)
ov[edge]=[255,0,0]
Image.fromarray(ov).save('overlay.png')
