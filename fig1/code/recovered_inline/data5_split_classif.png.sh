# Recovered verbatim from the session transcript (2026-10-16T08:59:58.093Z).
# Last shell command that wrote data5/split_classif.png. Paths are those of the original working folder.
cd <work2>/fig1 && python3 -I -c "
from PIL import Image
g=Image.open('data5/classif_gallery.png'); inp=Image.open('data5/classif_input.png')
out=Image.new('RGB',(400,400),(0,0,0))
out.paste(inp.crop((60,0,260,400)),(0,0))
for r in range(4):
    for c in range(2):
        tile=g.crop((c*100+ (0 if c==0 else 0), r*100, c*100+96, r*100+96)).resize((98,98),Image.LANCZOS)
        out.paste(tile,(201+c*100, r*100+1))
out.save('data5/split_classif.png')" && python3 - <<'EOF'
p='<work2>/fig1/make_fig1_page.py'; s=open(p).read()
def R(o,n):
    global s
    assert s.count(o)==1,o[:80]; s=s.replace(o,n)
R('    if w[0] == "detect":','''    if w[0] == "classify":                # input field | per-class gallery of cells (rows = predicted class)
        g.append(split_widget(wx, wy, w[1], "input", "output", None))
        for r_, nm in enumerate(w[2]):
            g.append(halo(wx + WS / 2 + 4, wy + (r_ + 1) * WS / 4 - 5, nm, "start", 10.5))
        g.append(f'<line x1="{wx+WS/2}" y1="{wy+WS/4*1}" x2="{wx+WS}" y2="{wy+WS/4*1}" stroke="#ffffff" stroke-width="0.8" opacity="0.6"/>'
                 f'<line x1="{wx+WS/2}" y1="{wy+WS/2}" x2="{wx+WS}" y2="{wy+WS/2}" stroke="#ffffff" stroke-width="0.8" opacity="0.6"/>'
                 f'<line x1="{wx+WS/2}" y1="{wy+WS*3/4}" x2="{wx+WS}" y2="{wy+WS*3/4}" stroke="#ffffff" stroke-width="0.8" opacity="0.6"/>')
        return "".join(g)
    if w[0] == "detect":''')
R('      ("pending", "classification", "Classification"),','      ("classify", "data5/split_classif.png", ["Control", "Mecillinam", "Nalidixate", "Rifampicin"], "Classification"),')
open(p,'w').write(s)
EOF
cd <work2>/fig1 && python3 make_fig1_page.py && sh render.sh fig1_page.svg preview_page.png 2368 && python3 -c "
from PIL import Image; Image.open('preview_page.png').crop((40,95,960,370)).save('zoom.png')"
