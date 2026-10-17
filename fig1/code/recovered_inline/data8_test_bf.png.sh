# Recovered verbatim from the session transcript (2026-10-16T10:53:43.664Z).
# Last shell command that wrote data8/test_bf.png. Paths are those of the original working folder.
cd <work2>/fig1 && grep -n "data4/B_rep_bf.png" make_fig1_v5.py | head; python3 -I -c "
import json, numpy as np, tifffile
from PIL import Image
from skimage.measure import find_contours, approximate_polygon
U='<uploads>/'
X,Y,W,H=600,620,240,260     # a different area of the field from the reference-annotation tile (240-480, 40-300)
bf=tifffile.imread(U+'cccf774d-BF.tif').astype(float)[Y:Y+H,X:X+W]; lo,hi=np.percentile(bf,[0.3,99.7])
Image.fromarray(np.repeat(np.repeat((np.clip((bf-lo)/(hi-lo),0,1)*255).astype(np.uint8),2,0),2,1)).save('data8/test_bf.png')
for name,f in [('ref','e752a357-104_2.tif'),('stardist','76c6cb98-Cancer_cell_seg.tif')]:
    sub=tifffile.imread(U+f).astype(int)[Y:Y+H,X:X+W]; out=[]
    for l in np.unique(sub[sub>0]):
        for c in find_contours(np.pad(sub==l,1).astype(float),0.5):
            c=approximate_polygon(c-1,0.6); out.append([[round(float(v[1]),2),round(float(v[0]),2)] for v in c])
    json.dump({'w':W,'h':H,'contours':out},open(f'data8/test_{name}.json','w')); print(name,len(np.unique(sub))-1)
"
