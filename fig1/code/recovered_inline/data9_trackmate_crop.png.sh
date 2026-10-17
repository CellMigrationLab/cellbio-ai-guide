# Recovered verbatim from the session transcript (2026-10-16T11:32:40.039Z).
# Last shell command that wrote data9/trackmate_crop.png. Paths are those of the original working folder.
cd <work2>/fig1 && python3 -I -c "
import tifffile
from PIL import Image
c=tifffile.imread('<uploads>/fab3a3d9-TrackMate_capture_of_Merged2.tif')
y,x,n=520,200,280
Image.fromarray(c[y:y+n,x:x+n]).resize((472,472),Image.LANCZOS).save('data9/trackmate_crop.png')" && python3 - <<'EOF'
p='<work2>/fig1/make_fig1_v11.py'; s=open(p).read()
def R(o,n):
    global s
    assert s.count(o)==1,o[:70]; s=s.replace(o,n)
R('"data9/trackmate_crop.png", 1.31483, 420, 100,','"data9/trackmate_crop.png", 1.31483, 280, 100,')
R('''          f'<circle cx="{cx0+52}" cy="{cy0+58}" r="34" fill="{k["tint"]}"/>',
          group(f"icon {nm}", ico(nm, cx0 + 52, cy0 + 58, k["accent"])),''',
  '''          f'<circle cx="{cx0+64}" cy="{cy0+CHu/2}" r="46" fill="{k["tint"]}"/>',
          f'<g transform="translate({cx0+64} {cy0+CHu/2}) scale(1.35) translate({-(cx0+64)} {-(cy0+CHu/2)})">' + group(f"icon {nm}", ico(nm, cx0 + 64, cy0 + CHu / 2, k["accent"])) + "</g>",''')
R('''          t(cx0 + 104, cy0 + 34, ttl, 17, "bold", INK),
          t(cx0 + 104, cy0 + 58, what, 13.5, fill=BODY, lh=17),
          f'<line x1="{cx0+104}" y1="{cy0+CHu-80}" x2="{cx0+CWu-18}" y2="{cy0+CHu-80}" stroke="{k["tintstroke"]}" stroke-width="1"/>',
          t(cx0 + 104, cy0 + CHu - 60, "Check", 13, "bold", k["accent"]),
          t(cx0 + 154, cy0 + CHu - 60, chk, 13, fill=INK, lh=16.5)]''',
  '''          t(cx0 + 130, cy0 + 40, ttl, 20, "bold", INK),
          t(cx0 + 130, cy0 + 68, what, 15, fill=BODY, lh=19),
          f'<line x1="{cx0+130}" y1="{cy0+CHu-90}" x2="{cx0+CWu-18}" y2="{cy0+CHu-90}" stroke="{k["tintstroke"]}" stroke-width="1"/>',
          t(cx0 + 130, cy0 + CHu - 66, "Check", 15, "bold", k["accent"]),
          t(cx0 + 190, cy0 + CHu - 66, chk, 15, fill=INK, lh=19)]''')
R('t(gx0 + 14, gy + 19, "more of the analysis delegated to the LLM  →  more decisions hidden", 14, "bold", "#ffffff"))',
  't(gx0 + 14, gy + 19, "more of the analysis delegated to the LLM  →  more decisions hidden", 15, "bold", "#ffffff"))')
open(p,'w').write(s)
EOF
cd <work2>/fig1 && python3 make_fig1_v11.py && sh render.sh fig1_v11.svg preview_v11.png 1048
