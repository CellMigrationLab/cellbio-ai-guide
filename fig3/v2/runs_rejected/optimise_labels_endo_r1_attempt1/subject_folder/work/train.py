import sys,time,logging,numpy as np,tifffile,torch
sys.path.insert(0,'work')
from prep import *
from cellpose import models, train
logging.basicConfig(level=logging.INFO,stream=sys.stdout)
y_end=int(sys.argv[1]); epochs=int(sys.argv[2]); nper=int(sys.argv[3]); name=sys.argv[4]; nfree=int(sys.argv[5])
a=tifffile.imread('image.tif'); gt=tifffile.imread('annotation.tif')
n=down(flatten(a)); l=down_lbl(gt)
ye=round(y_end*SCALE)
mod=models.CellposeModel(gpu=False); net=mod.net
for p in net.parameters(): p.requires_grad=False
for b in net.encoder.blocks[-nfree:]:
    for p in b.parameters(): p.requires_grad=True
for p in list(net.encoder.neck.parameters())+list(net.out.parameters()): p.requires_grad=True
t=time.time()
train.train_seg(net,train_data=[n[:ye]],train_labels=[l[:ye]],batch_size=2,n_epochs=epochs,nimg_per_epoch=nper,
   learning_rate=1e-4,weight_decay=0.01,bsize=256,scale_range=0.25,rescale=False,save_path='work',model_name=name,min_train_masks=1)
print('train time',time.time()-t)
