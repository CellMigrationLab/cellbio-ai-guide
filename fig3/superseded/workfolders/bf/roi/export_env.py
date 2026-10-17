import sys, json, numpy as np, tifffile
from skimage import measure, exposure
from PIL import Image
import os; X0,Y0,S=int(os.environ.get('ROIX',440)),int(os.environ.get('ROIY',40)),260; OD=os.environ.get('ROIDIR','roi')
D='<work2>/'
SRC={'gt':'<uploads>/e752a357-104_2.tif',
     'default':D+'fig1/data4/BF_cellpose_sam_labels.tif','generic':'codeG/labels.tif','specific':'codeS/labels.tif',
     'advised_a':'advice/advised_a.tif','advised_b':'advice/advised_b.tif','agent':'agent/labels.tif','agent_first':'agent/first_pass_labels.tif',
     'haiku':'draw/haiku_labels.tif','sonnet':'draw/sonnet_labels.tif','opus':'draw/opus_labels.tif','sonnet_r1':'draw/sonnet_r1_labels.tif','sonnet_r2':'draw/sonnet_r2_labels.tif','sonnet_r3':'draw/sonnet_r3_labels.tif'}
def contours(L):
    c=L[Y0-2:Y0+S+2, X0-2:X0+S+2]
    out=[]
    for lab in np.unique(c):
        if lab==0: continue
        m=np.pad(c==lab,1)
        for cc in measure.find_contours(m.astype(float),0.5):
            cc=measure.approximate_polygon(cc,0.6)
            out.append([[round(float(p[1])-3,1),round(float(p[0])-3,1)] for p in cc])
    return {'contours':out,'roi':[X0,Y0,S,S]}
if 'png' in sys.argv:
    bf=tifffile.imread('agent/bf.tif').astype(float)
    lo,hi=np.percentile(bf,[0.3,99.7])
    v=np.clip((bf[Y0:Y0+S,X0:X0+S]-lo)/(hi-lo),0,1)
    Image.fromarray((v*255).astype(np.uint8)).resize((S*2,S*2),Image.LANCZOS).save(OD+'/bf_roi.png')
for k in [a for a in sys.argv[1:] if a!='png']:
    json.dump(contours(tifffile.imread(SRC[k])),open(OD+f'/{k}.json','w'))
    print(k,'ok')
