"""Compare predicted labels with annotation: object F1@IoU0.5, count, area/aspect agreement."""
import sys, numpy as np, tifffile
from skimage import measure
def stats(l):
    return {r.label:(r.area*0.65**2, r.axis_major_length/r.axis_minor_length) for r in measure.regionprops(l)}
def main(pred_p, gt_p="annotation.tif"):
    p=tifffile.imread(pred_p); g=tifffile.imread(gt_p)
    ps,gs=stats(p),stats(g)
    pairs=[]
    for gi in gs:
        m=g==gi; ids,c=np.unique(p[m],return_counts=True)
        for i,n in zip(ids,c):
            if i==0: continue
            iou=n/(m.sum()+(p==i).sum()-n)
            if iou>=0.5: pairs.append((gi,i,iou))
    tp=len(pairs); fp=len(ps)-tp; fn=len(gs)-tp
    print(f"GT {len(gs)} pred {len(ps)} TP {tp} FP {fp} FN {fn} P {tp/max(len(ps),1):.3f} R {tp/len(gs):.3f} F1 {2*tp/(len(ps)+len(gs)):.3f} meanIoU {np.mean([x[2] for x in pairs]):.3f}")
    ga=np.array([gs[a][0] for a,_,_ in pairs]); pa=np.array([ps[b][0] for _,b,_ in pairs])
    gr=np.array([gs[a][1] for a,_,_ in pairs]); pr=np.array([ps[b][1] for _,b,_ in pairs])
    print(f"matched area: median rel err {np.median((pa-ga)/ga):+.3f}; aspect: median abs err {np.median(abs(pr-gr)):.3f}; median AR gt {np.median(gr):.3f} pred {np.median(pr):.3f}")
    print(f"all-cell medians: area gt {np.median([v[0] for v in gs.values()]):.0f} pred {np.median([v[0] for v in ps.values()]):.0f}")
main(*sys.argv[1:])
