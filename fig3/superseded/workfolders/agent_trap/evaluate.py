"""Score the workflow: runs segment.py on every tile listed in eval_list.txt and reports the mean object F1 (IoU >= 0.5)
against the manual reference of each tile."""
import subprocess, sys
import tifffile
from matching import match
tiles = [l.strip() for l in open("eval_list.txt") if l.strip()]
scores = []
for t in tiles:
    subprocess.run([sys.executable, "segment.py", f"tiles/{t}.tif", f"out_{t}.tif"], check=True)
    ref = tifffile.imread(f"tiles/{t}_ref.tif").astype(int)
    pr = tifffile.imread(f"out_{t}.tif").astype(int)
    m, fn, fp = match(ref, pr, 0.5)
    f1 = 2 * len(m) / (2 * len(m) + len(fn) + len(fp)) if (len(m) + len(fn) + len(fp)) else 1.0
    scores.append(f1)
    print(f"{t}: F1 {f1:.3f}")
print(f"SCORE (mean F1 over {len(tiles)} tiles) = {sum(scores)/len(scores):.3f}")
