import numpy as np,tifffile as t,sys
def f1(gt,pr,thr=.5):
    g=np.unique(gt)[1:];p=np.unique(pr)[1:]
    if len(p)==0:return 0,0,0,len(g)
    gi={v:i for i,v in enumerate(g)};pi={v:i for i,v in enumerate(p)}
    m=np.zeros((len(g),len(p)),int)
    a=gt.ravel();b=pr.ravel();k=(a>0)&(b>0)
    np.add.at(m,([gi[v] for v in a[k]],[pi[v] for v in b[k]]),1)
    ga=m.sum(1)*0;
    ga=np.bincount(a,minlength=a.max()+1)[g];pa=np.bincount(b,minlength=b.max()+1)[p]
    iou=m/(ga[:,None]+pa[None]-m)
    tp=int((iou>=thr).sum())  # IoU>=.5 implies unique
    P=tp/len(p);R=tp/len(g);return 2*P*R/(P+R+1e-9),P,R,tp
if __name__=='__main__':
    print(f1(t.imread(sys.argv[1]),t.imread(sys.argv[2])))
