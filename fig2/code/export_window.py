"""Vector contours of a label image inside a window (full-field px), in window-pixel coordinates."""
import json
import numpy as np
import tifffile
from skimage.measure import find_contours, approximate_polygon


def contours(L, X, Y, W, H, keep=None):
    sub = L.astype(int)[Y:Y + H, X:X + W]
    out = []
    for l in np.unique(sub[sub > 0]):
        if keep is not None and int(l) not in keep:
            continue
        for c in find_contours(np.pad(sub == l, 1).astype(float), 0.5):
            c = approximate_polygon(c - 1, tolerance=0.6)
            out.append([[round(float(v[1]), 2), round(float(v[0]), 2)] for v in c])
    return out


def export(L, X, Y, W, H, path, keep=None):
    json.dump({"w": W, "h": H, "contours": contours(L, X, Y, W, H, keep)}, open(path, "w"))


def centroids(L, ids, X, Y, W, H):
    """Centroids (window px) of the listed labels whose centroid falls inside the window."""
    pts = []
    for l in ids:
        yy, xx = np.nonzero(L == l)
        if len(yy) == 0:
            continue
        cy, cx = yy.mean() - Y, xx.mean() - X
        if 0 <= cx < W and 0 <= cy < H:
            pts.append([round(float(cx), 1), round(float(cy), 1)])
    return pts
