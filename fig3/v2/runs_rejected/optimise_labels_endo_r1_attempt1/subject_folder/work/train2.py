"""Fine-tune last K ViT blocks + neck + out of cpsam on cached frozen-trunk tokens (CPU-feasible)."""
import sys,time,numpy as np,tifffile,torch,fastremap
sys.path.insert(0,'work')
from prep import *
from cellpose import models, dynamics
from cellpose.train import _loss_fn_seg
torch.set_num_threads(4)
y_end=int(sys.argv[1]); ncrop=int(sys.argv[2]); steps=int(sys.argv[3]); K=int(sys.argv[4]); out=sys.argv[5]
rng=np.random.default_rng(0); torch.manual_seed(0)
a=tifffile.imread('image.tif'); gt=tifffile.imread('annotation.tif')
n=down(flatten(a)); l=down_lbl(gt); ye=round(y_end*SCALE)
n=n[:ye]; l=l[:ye]
lo,hi=np.percentile(n,[1,99]); print('norm',lo,hi,flush=True)
mod=models.CellposeModel(gpu=False,use_bfloat16=False); net=mod.net; net.eval()
nb=len(net.encoder.blocks)
def trunk(x):
    with torch.no_grad():
        x=torch.nn.functional.conv2d(x,net.encoder.patch_embed.proj.weight[:,:x.shape[1]],bias=net.encoder.patch_embed.proj.bias,stride=net.ps).permute(0,2,3,1)
        x=x+net.encoder.pos_embed
        for b in net.encoder.blocks[:nb-K]: x=b(x)
    return x
def head(x):
    for b in net.encoder.blocks[nb-K:]: x=b(x)
    x=net.encoder.neck(x.permute(0,3,1,2)); x=net.out(x)
    return torch.nn.functional.conv_transpose2d(x,net.W2,stride=net.ps)
t=time.time(); feats=[]; tg=[]
for i in range(ncrop):
    y0=rng.integers(0,n.shape[0]-256+1); x0=rng.integers(0,n.shape[1]-256+1)
    im=n[y0:y0+256,x0:x0+256].copy(); lb=l[y0:y0+256,x0:x0+256].copy()
    k=rng.integers(4); im=np.rot90(im,k); lb=np.rot90(lb,k)
    if rng.random()<.5: im=im[:,::-1]; lb=lb[:,::-1]
    im=(im-lo)/(hi-lo); im=im*rng.uniform(.85,1.15)+rng.uniform(-.1,.1)
    lb=fastremap.renumber(np.ascontiguousarray(lb),in_place=False)[0]
    vec=dynamics.masks_to_flows_gpu(lb.astype(int),device=net.device)[0]
    tg.append(np.concatenate([lb[None],(lb[None]>0),vec]).astype(np.float32))
    feats.append(trunk(torch.from_numpy(np.ascontiguousarray(im[None,None]).astype(np.float32))))
    print('cached',i,time.time()-t,flush=True)
feats=torch.cat(feats); tg=torch.from_numpy(np.stack(tg))
for p in net.parameters(): p.requires_grad=False
params=[]
for m_ in list(net.encoder.blocks[nb-K:])+[net.encoder.neck,net.out]:
    for p in m_.parameters(): p.requires_grad=True; params.append(p)
opt=torch.optim.AdamW(params,lr=1e-4,weight_decay=0.01); net.train()
for s in range(steps):
    idx=rng.choice(ncrop,4,replace=False)
    lr=1e-4*min(1,(s+1)/10)
    for g in opt.param_groups: g['lr']=lr
    y=head(feats[idx]); loss=_loss_fn_seg(tg[idx],y,net.device)
    opt.zero_grad(); loss.backward(); opt.step()
    if s%10==0: print('step',s,float(loss),time.time()-t,flush=True)
net.eval(); net.save_model(out); print('saved',out,time.time()-t)
