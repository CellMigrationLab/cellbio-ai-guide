"""Fig. 2 troubleshooting: Cellpose-SAM (default cpsam weights, CPU) on the brightfield cancer-cell field,
with one setting changed at a time. Labels are written at native resolution for scoring against the reference."""
import re, sys, time
import numpy as np
import tifffile
from importlib.metadata import version
from cellpose import models

from common.paths import RAW as U
bf = tifffile.imread(U + "field104_brightfield.tif")
RUN_NAME = re.compile(r"^(down\d+|up\d+|file_(minmax|histeq|clahe)|nonorm|pecam|flow\d*\.?\d+|cellprob-?\d*\.?\d+)$")
runs = sys.argv[1:]
if not runs:
    raise SystemExit("usage: python cellpose_perturb.py RUN [RUN ...]  (e.g. down4 up2 file_minmax nonorm flow0.8 cellprob2)")
unknown = [r for r in runs if not RUN_NAME.match(r)]
if unknown:
    raise ValueError(f"unknown run name(s) {unknown}; expected one of down<f>, up<f>, file_<minmax|histeq|clahe>, "
                     "nonorm, pecam, flow<threshold>, cellprob<threshold>")
model = models.CellposeModel(gpu=False)
for r in runs:
    t0 = time.time()
    if r.startswith("down"):
        f = int(r[4:])
        H, W = (bf.shape[0] // f) * f, (bf.shape[1] // f) * f
        small = bf[:H, :W].astype(np.float32).reshape(H // f, f, W // f, f).mean((1, 3))      # f x f block mean
        m, _, _ = model.eval(small)
        m = np.pad(np.repeat(np.repeat(m, f, 0), f, 1), ((0, bf.shape[0] - H), (0, bf.shape[1] - W)))  # back to native grid
    elif r.startswith("up"):
        import torch
        f = int(r[2:])
        big = torch.nn.functional.interpolate(torch.from_numpy(bf.astype(np.float32))[None, None], scale_factor=f,
                                              mode="bilinear", align_corners=False)[0, 0].numpy()          # bilinear upsampling
        m, _, _ = model.eval(big)
        m = m[f // 2::f, f // 2::f][:bf.shape[0], :bf.shape[1]]                                           # back to native grid
    elif r.startswith("file_"):                  # pre-normalised input (0-1 float), Cellpose normalisation off
        m, _, _ = model.eval(tifffile.imread(f"panels/in_{r[5:]}.tif"), normalize=False)
    elif r == "nonorm":
        m, _, _ = model.eval(bf.astype(np.float32), normalize=False)
    elif r == "pecam":                          # acquired PECAM-1 (HUVEC junctions), default settings
        m, _, _ = model.eval(tifffile.imread(U + "field104_pecam1.tif"))
    elif r.startswith("flow"):
        m, _, _ = model.eval(bf, flow_threshold=float(r[4:]))
    elif r.startswith("cellprob"):
        m, _, _ = model.eval(bf, cellprob_threshold=float(r[8:]))
    else:   # unreachable after the check above; kept so a stale mask can never be written
        raise ValueError(f"unhandled run {r!r}")
    if m.shape != bf.shape:
        raise ValueError(f"{r}: mask shape {m.shape} differs from the image {bf.shape}")
    tifffile.imwrite(f"panels/cp_{r}.tif", m.astype(np.uint16), compression="zlib")  # lossless, as stored
    print(f"cellpose {version('cellpose')} {r}: {m.max()} objects in {time.time()-t0:.0f}s", flush=True)
