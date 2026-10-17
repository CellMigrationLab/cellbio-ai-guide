import tifffile,numpy as np,warnings,sys;warnings.filterwarnings('ignore')
from scipy import ndimage as ndi
from skimage import measure,morphology,segmentation,io,feature
a=tifffile.imread('/home/user/sessions/s002/image.tif').astype(np.float32)
f=a-ndi.gaussian_filter(a,40)
g=ndi.gaussian_filter(f,1)
# ring-correlation: dark ring at radius R (width ~2) minus bright halo outside
def ring(R,w=1.5):
    r=int(R+6);y,x=np.mgrid[-r:r+1,-r:r+1];d=np.hypot(x,y)
    k=np.exp(-0.5*((d-R)/w)**2)          # ring
    k-=k.mean()                           # zero mean
    k/=np.abs(k).sum()
    return k
resp=np.max([ndi.correlate(-g,ring(R)) for R in range(8,17,2)],axis=0)
print(np.percentile(resp,[50,90,99,99.9]))
np.save('resp.npy',resp)
H=float(sys.argv[1]);TH=float(sys.argv[2])
pk=feature.peak_local_max(ndi.gaussian_filter(resp,1.5),min_distance=10,threshold_abs=TH,exclude_border=False)
print(len(pk))
im=(a-a.min())/(a.max()-a.min());rgb=np.dstack([im]*3)
for y,x in pk:
    rr,cc=np.ogrid[:a.shape[0],:a.shape[1]];ring_=np.abs(np.hypot(rr-y,cc-x)-12)<1
    rgb[ring_]=[1,0,0]
io.imsave('ov5.png',(rgb*255).astype(np.uint8))
