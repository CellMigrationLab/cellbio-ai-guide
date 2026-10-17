"""Error-map tile for panel e: same crop as the super-resolution tiles, inferno colour map, 0 to the 99.5th percentile
of the whole map."""
import numpy as np, tifffile, json
from PIL import Image
from matplotlib import colormaps
em = tifffile.imread("panels/squirrel_predicted.tif")
y, x, n = 160, 600, 140
hi = float(np.percentile(em, 99.5))
rgb = (colormaps["inferno"](np.clip(em[y:y + n, x:x + n] / hi, 0, 1))[..., :3] * 255).astype(np.uint8)
Image.fromarray(np.repeat(np.repeat(rgb, 3, 0), 3, 1)).save("panels/sr_squirrel.png")
cb = (colormaps["inferno"](np.linspace(0, 1, 256))[None, :, :3] * 255).astype(np.uint8).repeat(8, 0)
Image.fromarray(cb).save("panels/inferno_bar.png")
print("ok", hi)
