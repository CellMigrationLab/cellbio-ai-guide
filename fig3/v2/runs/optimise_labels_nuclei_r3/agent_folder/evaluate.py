"""Compare predicted labels to a reference: python evaluate.py pred.tif annotation.tif [image.tif]"""
import sys, numpy as np, tifffile as t
from skimage import measure
PX=0.65
def match(gt,pr,thr=0.5):
    ng,npr=gt.max(),pr.max()
    ids_g,ids_p=gt.ravel(),pr.ravel(); m=(ids_g>0)&(ids_p>0)
    inter=np.zeros((ng+1,npr+1),np.int64); np.add.at(inter,(ids_g[m],ids_p[m]),1)
    ag=np.bincount(ids_g,minlength=ng+1); ap=np.bincount(ids_p,minlength=npr+1)
    iou=inter/(ag[:,None]+ap[None,:]-inter+1e-9)
    pairs={}
    for g,p in zip(*np.where(iou>thr)):
        if g and p: pairs[g]=p
    return pairs
def props(l):
    return {r.label:(r.area*PX**2,r.axis_major_length/max(r.axis_minor_length,1e-9)) for r in measure.regionprops(l)}
def main(pp,gp):
    pr=t.imread(pp);gt=t.imread(gp)
    pr=measure.label(pr,connectivity=1,background=0) if False else pr
    pairs=match(gt,pr);tp=len(pairs);ngt=len(np.unique(gt))-1;npr=len(np.unique(pr))-1
    print(f"GT {ngt} pred {npr} TP@0.5 {tp} FP {npr-tp} FN {ngt-tp} precision {tp/max(npr,1):.3f} recall {tp/ngt:.3f} F1 {2*tp/(ngt+npr):.3f}")
    pg,pp_=props(gt),props(pr)
    A=np.array([(pg[g][0],pp_[p][0]) for g,p in pairs.items()]);R=np.array([(pg[g][1],pp_[p][1]) for g,p in pairs.items()])
    print(f"count error {100*(npr-ngt)/ngt:+.1f}%")
    print(f"area median GT {np.median(A[:,0]):.1f} pred {np.median(A[:,1]):.1f} um2; per-object median rel err {100*np.median((A[:,1]-A[:,0])/A[:,0]):+.1f}%, MAPE {100*np.median(abs(A[:,1]-A[:,0])/A[:,0]):.1f}%")
    print(f"AR median GT {np.median(R[:,0]):.2f} pred {np.median(R[:,1]):.2f}; median abs err {np.median(abs(R[:,1]-R[:,0])):.3f}; Pearson r {np.corrcoef(R[:,0],R[:,1])[0,1]:.2f}")
    return tp/ngt
if __name__=="__main__": main(*sys.argv[1:3])
