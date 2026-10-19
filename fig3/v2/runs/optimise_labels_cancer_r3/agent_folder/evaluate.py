"""python evaluate.py pred.tif annotation.tif : count error, F1@IoU0.5, area/aspect agreement."""
import sys, numpy as np, tifffile
from skimage import measure
def stats(l,px=0.65):
    r=measure.regionprops(l);return {x.label:(x.area*px*px,x.axis_major_length/max(x.axis_minor_length,1e-9)) for x in r}
p=tifffile.imread(sys.argv[1]);g=tifffile.imread(sys.argv[2])
gi=[i for i in np.unique(g) if i];pi=[i for i in np.unique(p) if i]
ov=np.zeros((g.max()+1,p.max()+1),int)
np.add.at(ov,(g.ravel(),p.ravel()),1)
ga=np.bincount(g.ravel());pa=np.bincount(p.ravel())
pairs=[]
for a in gi:
    for b in pi:
        o=ov[a,b]
        if o:
            iou=o/(ga[a]+pa[b]-o)
            if iou>=0.5: pairs.append((a,b))
tp=len(pairs);fp=len(pi)-tp;fn=len(gi)-tp
sg,sp=stats(g),stats(p)
print(f"GT {len(gi)} pred {len(pi)} count error {100*(len(pi)-len(gi))/len(gi):+.1f}%  TP{tp} FP{fp} FN{fn} F1 {2*tp/(2*tp+fp+fn):.3f}")
da=[(sp[b][0]-sg[a][0])/sg[a][0] for a,b in pairs];dr=[sp[b][1]-sg[a][1] for a,b in pairs]
print(f"matched: median area err {100*np.median(da):+.1f}% (IQR {100*np.percentile(da,25):+.1f}..{100*np.percentile(da,75):+.1f}); aspect err median {np.median(dr):+.3f} MAE {np.mean(np.abs(dr)):.3f}")
print(f"population median area GT {np.median([v[0] for v in sg.values()]):.0f} pred {np.median([v[0] for v in sp.values()]):.0f}; aspect GT {np.median([v[1] for v in sg.values()]):.2f} pred {np.median([v[1] for v in sp.values()]):.2f}")
