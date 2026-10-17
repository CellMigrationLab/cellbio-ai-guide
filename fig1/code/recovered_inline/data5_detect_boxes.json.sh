# Recovered verbatim from the session transcript (2026-10-16T08:53:57.536Z).
# Last shell command that wrote data5/detect_boxes.json. Paths are those of the original working folder.
cd <work2> && python3 -I -c "
import json, numpy as np
from PIL import Image
n='pos_8_frame_80_2.png'
a=np.array(Image.open('dl_deepbacs/data/image_patches/test_images/'+n).convert('L')).astype(float)
lo,hi=np.percentile(a,[0.5,99.5]); Image.fromarray((np.clip((a-lo)/(hi-lo),0,1)*255).astype(np.uint8)).save('fig1/data5/detect_input.png')
P=json.load(open('dl_deepbacs/yolo_pred.json'))[n]
json.dump({'size':256,'boxes':P}, open('fig1/data5/detect_boxes.json','w')); print(len(P),'boxes')
" && cd fig1 && python3 - <<'EOF'
p='make_fig1_page.py'; s=open(p).read()
def R(o,n):
    global s
    assert s.count(o)==1,o[:80]; s=s.replace(o,n)
R('def draw_widget(w, wx, wy):\n    """Draw one row-A-style widget (uses the global widget size WS)."""\n    g = []\n',
'''DET_COLS = ["#3b8cff", "#2fd65a", "#ff4646"]       # YOLOv2 classes: rod, dividing, microcolony


def draw_widget(w, wx, wy):
    """Draw one row-A-style widget (uses the global widget size WS)."""
    g = []
    if w[0] == "detect":                  # input | output split; predicted boxes drawn as vectors on the output half
        d = json.load(open(w[2]))
        k_ = WS / d["size"]
        cid_ = clip(wx + WS / 2, wy, WS / 2, WS, 0)
        rects = "".join(f'<rect x="{wx+x0*k_:.1f}" y="{wy+y0*k_:.1f}" width="{(x1-x0)*k_:.1f}" height="{(y1-y0)*k_:.1f}" '
                        f'stroke="{DET_COLS[c]}"/>' for x0, y0, x1, y1, cf, c in d["boxes"])
        g.append(split_widget(wx, wy, w[1], "input", "output", None))
        g.append(f'<g clip-path="url(#{cid_})" fill="none" stroke-width="1.8" inkscape:label="YOLOv2 predicted boxes (vector)">{rects}</g>')
        g.append(f'<line x1="{wx+WS/2}" y1="{wy}" x2="{wx+WS/2}" y2="{wy+WS}" stroke="#ffffff" stroke-width="2"/>')
        return "".join(g)
''')
R('     [("pending", "detection", "Detection"),','     [("detect", "data5/detect_input.png", "data5/detect_boxes.json", "Detection"),')
open(p,'w').write(s)
EOF
python3 make_fig1_page.py && sh render.sh fig1_page.svg preview_page.png 2368 && python3 -c "
from PIL import Image; Image.open('preview_page.png').crop((40,95,960,370)).save('zoom.png')"
