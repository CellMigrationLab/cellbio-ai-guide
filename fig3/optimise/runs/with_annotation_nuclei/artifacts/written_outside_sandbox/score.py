import numpy as np,tifffile,sys
D="<fig3-work>/bf3/ref_nuclei"
def score(pred, thr=0.5):
    gt=tifffile.imread(D+'/annot_dev.tif'); cm=tifffile.imread(D+'/cancer_mask_dev.tif')>0
    ids=[i for i in np.unique(pred) if i]
    keep=[i for i in ids if (cm[pred==i].mean()<=0.3)]
    p=np.where(np.isin(pred,keep),pred,0)
    gi=[i for i in np.unique(gt) if i]
    # contingency
    from collections import Counter
    m=(p>0)&(gt>0); c=Counter(zip(p[m],gt[m]))
    pa=Counter(p[p>0]); ga=Counter(gt[gt>0])
    cand=sorted(((n/(pa[a]+ga[b]-n),a,b) for (a,b),n in c.items()),reverse=True)
    up=set();ug=set();tp=0
    for iou,a,b in cand:
        if iou<thr: break
        if a in up or b in ug: continue
        up.add(a);ug.add(b);tp+=1
    fp=len(keep)-tp;fn=len(gi)-tp
    return 2*tp/(2*tp+fp+fn),tp,fp,fn
if __name__=="__main__":
    print(score(tifffile.imread(sys.argv[1])))
