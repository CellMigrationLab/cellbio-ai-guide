import sys,numpy as np,tifffile
from skimage import exposure,filters
def run(path,out,diam=80,flow=0.4,cp=0.0,minarea=300):
    from cellpose import models
    img=tifffile.imread(path).astype(np.float32)
    bg=filters.gaussian(img,50)
    x=img-bg
    lo,hi=np.percentile(x,[0.5,99.5]);x=np.clip((x-lo)/(hi-lo),0,1)
    m=models.CellposeModel(gpu=False)
    lab=m.eval(x,diameter=diam,flow_threshold=flow,cellprob_threshold=cp)[0]
    from skimage.measure import regionprops
    for r in regionprops(lab):
        if r.area<minarea: lab[lab==r.label]=0
    tifffile.imwrite(out,lab.astype(np.uint16))
    return lab
if __name__=='__main__':
    run(sys.argv[1],sys.argv[2])
