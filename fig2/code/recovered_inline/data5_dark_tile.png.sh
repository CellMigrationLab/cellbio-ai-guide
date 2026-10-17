# Recovered verbatim from the session transcript (2026-10-16T08:40:55.703Z).
# Last shell command that wrote data5/dark_tile.png. Paths are those of the original working folder.
cd <work2>/fig1 && python3 -c "
from PIL import Image; Image.new('RGB',(100,135),(20,24,31)).save('data5/dark_tile.png')" && cp make_fig1_page.py make_fig1_page_v11.py && cp fig1_page.svg fig1_page_v11.svg && python3 - <<'EOF'
p='make_fig1_page.py'; s=open(p).read()
def R(o,n,c=1):
    global s
    assert s.count(o)==c,(o[:90],s.count(o)); s=s.replace(o,n)
# ---------- icons: proper U-Net and a pix2pix (conditional GAN) schematic
R('def check_badge(', r'''def unet2(cx, cy, col):
    """U-Net: contracting path (left), bottleneck, expanding path (right), skip connections across."""
    g = []
    lv = [(-54, -22, 30), (-34, 2, 20), (0, 22, 12)]     # (x offset, y centre, block height) per level
    for i, (dx, dy, h) in enumerate(lv):
        for sgn in ((-1, 1) if i < 2 else (1,)):
            x = cx + sgn * dx - (5 if i < 2 else 9)
            w = 10 if i < 2 else 18
            g.append(f'<rect x="{x:.1f}" y="{cy+dy-h/2:.1f}" width="{w}" height="{h}" rx="2" fill="{col}"/>')
    m = col.strip("#")
    # down (left) and up (right) between levels
    for (x1, y1, x2, y2) in [(-54, -7, -38, -6), (-34, 12, -14, 18), (14, 18, 34, 12), (38, -6, 54, -7)]:
        g.append(f'<line x1="{cx+x1}" y1="{cy+y1}" x2="{cx+x2}" y2="{cy+y2}" stroke="{col}" stroke-width="1.8" marker-end="url(#ah-{m})"/>')
    # skip connections
    for (dx, dy) in [(54, -22), (34, 2)]:
        g.append(f'<line x1="{cx-dx+7}" y1="{cy+dy}" x2="{cx+dx-9}" y2="{cy+dy}" stroke="{col}" stroke-width="1.5" '
                 f'stroke-dasharray="3 2.5" marker-end="url(#ah-{m})"/>')
    return '<g inkscape:label="U-Net icon">' + "".join(g) + "</g>"


def gan(cx, cy, col):
    """pix2pix: conditional GAN = generator G (image -> image) + discriminator D (real or predicted?)."""
    m = col.strip("#")
    g = [f'<path d="M{cx-58},{cy-22} L{cx-22},{cy-10} L{cx-22},{cy+10} L{cx-58},{cy+22} Z" fill="{col}"/>',
         t(cx - 44, cy + 5, "G", 14, "bold", "#ffffff", "middle"),
         f'<line x1="{cx-18}" y1="{cy}" x2="{cx+12}" y2="{cy}" stroke="{col}" stroke-width="2" marker-end="url(#ah-{m})"/>',
         f'<path d="M{cx+18},{cy-22} L{cx+58},{cy-6} L{cx+58},{cy+6} L{cx+18},{cy+22} Z" fill="none" stroke="{col}" stroke-width="2.4" stroke-linejoin="round"/>',
         t(cx + 33, cy + 5, "D", 14, "bold", col, "middle")]
    return '<g inkscape:label="pix2pix (conditional GAN) icon">' + "".join(g) + "</g>"


def check_badge(''')
# ---------- pipeline: larger images, compact model box, DL wording
i=s.index('    ct += (hc - 360) / 2'); j=s.index('    return p', i)
s=s[:i]+'''    ct += (hc - 400) / 2                    # centre the pipeline (designed for 400) in taller rows
    p.append(box_title(176, ct + 26, "Acquired image", "brightfield"))
    p.append(real_image(56, ct + 62, IMW, IMH, "data3/A_bf.png", PX, 210, 50, f"{col} acquired brightfield (real)", "#111111"))
    p.append(arrow(300, ct + 222, 318, ct + 222, k["accent"]))
    p.append(rrect(322, ct + 152, 130, 140, 12, k["tint"], k["tintstroke"]))
    p.append(t(387, ct + 177, "DL model", 17, "bold", INK, "middle"))
    p.append(gan(387, ct + 224, k["accent"]) if ai_lines == ["pix2pix"] else unet2(387, ct + 224, k["accent"]))
    p.append(t(387, ct + 278, ai_lines, 15, fill=INK, anchor="middle"))
    p.append(arrow(456, ct + 222, 474, ct + 222, k["accent"]))
    p.append(box_title(598, ct + 26, right_lbl[0], right_lbl[1]))
    p.append(real_image(478, ct + 62, IMW, IMH, right_png, PX, right_w, 50, f"{col} output (real)", right_bar))
'''+s[j:]
R('IMW, IMH = 210, 280           # main image size','IMW, IMH = 240, 320           # main image size')
R('("AI output", "cancer-cell labels")','("Output", "cancer-cell labels")')
R('("AI output", "predicted DAPI + PECAM")','("Output", "predicted DAPI + PECAM")')
# ---------- font sizes
R('def halo(x, y, txt, anchor="start", size=11.5):','def halo(x, y, txt, anchor="start", size=13):')
R('                 + halo(x + WS - 8 - bar[0] / 2, y + WS - 14, bar[1], "middle", 10.5))','                 + halo(x + WS - 8 - bar[0] / 2, y + WS - 14, bar[1], "middle", 12))')
R('''            + t(x + 28, y + 4.5, label, 12.5, fill=BODY))''','''            + t(x + 28, y + 5, label, 14, fill=BODY))''')
R('''    return (t(x, y, label, 13, fill=BODY)''','''    return (t(x, y, label, 14, fill=BODY)''')
R('''            + t(x + w + 6, y + 15.5, value_txt or f"{v:.2f}", 12.5, "bold", INK))''','''            + t(x + w + 6, y + 16, value_txt or f"{v:.2f}", 14, "bold", INK))''')
R('''y="{y + 32 + k_ * 13.6}" font-size="9"''','''y="{y + 30 + k_ * 15.5}" font-size="10.5"''')
R('            + t(x + 20, y + 48, text_lines, 12.5, fill=INK, lh=15.5))','            + t(x + 20, y + 52, text_lines, 14, fill=INK, lh=18))')
R('        g.append(t(wx + WS / 2, CT + 231, w[-1], 14, "bold", INK, "middle"))','        g.append(t(wx + WS / 2, CT + 231, w[-1], 15, "bold", INK, "middle"))')
R('        b.append(t(cx, yb + 96, nm, 13.5, fill=INK, anchor="middle"))','        b.append(t(cx, yb + 96, nm, 14.5, fill=INK, anchor="middle"))')
R('''            + t(x + w - 8 - bar / 2, y + h - 13, f"{bar_um:g} µm", 11.5, "bold" if bar_col != "#ffffff" else "normal", bar_col, "middle") + "</g>")''',
  '''            + t(x + w - 8 - bar / 2, y + h - 13, f"{bar_um:g} µm", 13, "bold", bar_col, "middle") + "</g>")''')
# ---------- row A: input / output corner labels; LLM badges drawn on top
for a_,b_ in [('"acquired", "labels", (20 / (480','"input", "output", (20 / (480'),('"acquired", "labels", (50 / (210','"input", "output", (50 / (210'),
              ('"acquired", "denoised"','"input", "output"'),('"acquired", "super-resolved"','"input", "output"'),('"acquired", "predicted", (50','"input", "output", (50')]:
    R(a_,b_)
R('''        if key == "C" and j < 2:              # flow badge in the gap: prompt -> code -> output
            bx_, by_ = wx + WS + GAP / 2, wy + WS / 2
            g.append(''','''        if key == "C" and j < 2:              # flow badge in the gap: prompt -> code -> output (drawn after widgets)
            bx_, by_ = wx + WS + GAP / 2, wy + WS / 2
            badges.append(''')
R('''    o.append(group(f"overview card {ttl}", "".join(g)))''','''    o.append(group(f"overview card {ttl}", "".join(g) + "".join(badges)))''')
R('''    for j, w in enumerate(widgets):
        wx, wy =''','''    badges = []
    for j, w in enumerate(widgets):
        wx, wy =''')
# ---------- row B score card: field-of-view score only
R('''         [("Test set", 0.933, "#8a94a3", None), ("This field", A_SC["stardist"], cA["accent"], None)]),''','''         [("Field of view", A_SC["stardist"], cA["accent"], None)]),''')
R('''         [("This field", A_SC["cellpose"], cA["accent"], None)])]):''','''         [("Field of view", A_SC["cellpose"], cA["accent"], None)])]):''')
# ---------- row C score card: outlines only, both annotators, field-of-view scores
R('''     [("data3/B_annotator1_contours.json", "annotator 1 (vector)", REF, DASH), ("data3/B_cells_contours.json", "Cellpose on predicted PECAM (vector)", MODEL, None)],
     [("Human agreement", 0.897, "#8a94a3", None), ("This field, annotator 1", 0.781, cB["accent"], None),
      ("This field, annotator 2", 0.746, cB["accent"], None)], "acquired PECAM"),''',
  '''     [("data3/B_annotator1_contours.json", "annotator 1 (vector)", REF, DASH), ("data3/B_annotator2_contours.json", "annotator 2 (vector)", REF2, DASH),
      ("data3/B_cells_contours.json", "Cellpose on predicted PECAM (vector)", MODEL, None)],
     [("Human agreement", 0.897, "#8a94a3", None), ("Field of view, annotator 1", 0.781, cB["accent"], None),
      ("Field of view, annotator 2", 0.746, cB["accent"], None)], None),''')
R('''     [("Test set", 0.976, "#8a94a3", None), ("This field", 0.828, cB["accent"], None)], "acquired DAPI"),''','''     [("Field of view", 0.828, cB["accent"], None)], None),''')
R('''     [("This field, DAPI", 0.891, cB["accent"], None), ("This field, PECAM", 0.243, cB["accent"], None)], None),''','''     [("Field of view, DAPI", 0.891, cB["accent"], None), ("Field of view, PECAM", 0.243, cB["accent"], None)], None),''')
R('''        tl.append(real_image(tx_, ry, TWb, THb, png, PX, 100, 20, f"C example {name}"))
        for path, lbl, colr, dash in layers:
            tl.append(vector_outlines_l(tx_, ry, TWb, THb, path, lbl, colr, 1.4, dash))
        tl.append(halo(tx_ + 6, ry + 16, cap))''','''        tl.append(real_image(tx_, ry, TWb, THb, "data5/dark_tile.png", PX, 100, 20, f"C example {name} (outlines only)"))
        for path, lbl, colr, dash in layers:
            tl.append(vector_outlines_l(tx_, ry, TWb, THb, path, lbl, colr, 1.6, dash))''')
R('    b.append(group(f"example {name}", score_row(x1, ry + THb + 4, tl, bars_, tx_, 130, 33)))','    b.append(group(f"example {name}", score_row(x1, ry + THb + 4, tl, bars_, tx_, 130, 36)))')
open(p,'w').write(s)
EOF
python3 make_fig1_page.py && H=$(grep -o 'height="[0-9.]*" viewBox' fig1_page.svg | head -1 | grep -o '[0-9]*' | head -1) && echo H=$H && sh render.sh fig1_page.svg preview_page.png $H
