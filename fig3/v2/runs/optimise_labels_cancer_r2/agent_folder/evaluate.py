"""python evaluate.py labels.tif annotation.tif : F1@IoU0.5, count, shape agreement."""
import sys, numpy as np, tifffile
from skimage.measure import regionprops
P=0.65
def match(pred,gt,thr=0.5):
    pairs=[]
    n=np.zeros((pred.max()+1,gt.max()+1),int)
    np.add.at(n,(pred.ravel(),gt.ravel()),1)
    ap=n.sum(1);ag=n.sum(0)
    for p in np.unique(pred)[1:]:
        for g in np.unique(gt[pred==p]):
            if g==0: continue
            iou=n[p,g]/(ap[p]+ag[g]-n[p,g])
            if iou>thr: pairs.append((p,g,iou))
    return pairs
def props(l): return {r.label:(r.area*P*P,r.axis_major_length/r.axis_minor_length) for r in regionprops(l)}
if __name__=="__main__":
    pred=tifffile.imread(sys.argv[1]);gt=tifffile.imread(sys.argv[2])
    pr=props(pred);gp=props(gt);m=match(pred,gt)
    tp=len(m);fp=len(pr)-tp;fn=len(gp)-tp
    print(f"pred {len(pr)} gt {len(gp)} TP {tp} FP {fp} FN {fn} P {tp/max(len(pr),1):.2f} R {tp/len(gp):.2f} F1 {2*tp/(len(pr)+len(gp)):.2f} meanIoU {np.mean([x[2] for x in m]):.2f}")
    a=np.array([(pr[p][0],gp[g][0]) for p,g,_ in m]);r=np.array([(pr[p][1],gp[g][1]) for p,g,_ in m])
    print(f"area median rel err {np.median((a[:,0]-a[:,1])/a[:,1]):+.3f}; AR median abs err {np.median(abs(r[:,0]-r[:,1])):.3f}, AR mean pred {r[:,0].mean():.2f} gt {r[:,1].mean():.2f}")
