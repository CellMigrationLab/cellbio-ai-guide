"""Extract TrackMate tracks (vector polylines) from the exported plot PDF->SVG, smooth them for display, save as JSON."""
import json
import re
import numpy as np

s = open("data6/tracksB.svg").read()
tracks = []
for m in re.finditer(r'<path ([^>]*)>', s):
    a = m.group(1)
    col = re.search(r'stroke="rgb\(([\d.]+)%, ([\d.]+)%, ([\d.]+)%\)"', a)
    d = re.search(r' d="([^"]+)"', a)
    if not col or not d or d.group(1).count(" L ") < 20:
        continue
    rgb = [float(c) / 100 for c in col.groups()]
    if max(rgb) < 0.15:                     # skip the black axes and frame (grey is a track colour)
        continue
    pts = np.array([[float(v) for v in p.split()] for p in re.findall(r'[ML] ([\d.\-]+ [\d.\-]+)', d.group(1))])
    pts[:, 1] = 576 - pts[:, 1]              # undo the cairo group transform matrix(1, 0, 0, -1, 0, 576)
    tracks.append((rgb, pts))
print("tracks:", len(tracks))
# crop window (page points; 300-dpi raster crop x 650-2350, y 370-2070 px -> /300*72)
x0, y0, n = 650 * 72 / 300, 370 * 72 / 300, 1700 * 72 / 300
W = 7                                        # moving-average window (points) for display smoothing
out = []
for rgb, p in tracks:
    if len(p) > W:
        k = np.ones(W) / W
        sm = np.column_stack([np.convolve(np.pad(p[:, i], (W // 2, W // 2), mode="edge"), k, mode="valid") for i in (0, 1)])
    else:
        sm = p
    q = (sm - [x0, y0]) / n                  # normalised to the crop window
    if ((q > -0.05) & (q < 1.05)).all(1).any():
        out.append({"rgb": "#%02x%02x%02x" % tuple(int(round(c * 255)) for c in rgb), "pts": np.round(q, 4).tolist()})
json.dump(out, open("panel_a/tracks_smoothed.json", "w"))
print("tracks in window:", len(out), "| smoothing window:", W, "points")
