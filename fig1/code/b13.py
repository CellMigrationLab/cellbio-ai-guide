# 2 x 2 grid: one card per use, each with an example prompt and the kind of reply it returns
MONO = "font-family:'DejaVu Sans Mono',Menlo,Consolas,monospace"
uses = [("advise", "Ask for advice", "tools, parameters, strategies",
         ["Which tools can segment touching nuclei", "in 2D fluorescence images, and which", "parameters matter most?"],
         ("text", ["StarDist or Cellpose; check the", "probability threshold and object size."])),
        ("code", "Ask for code", "e.g. Python, Fiji macro",
         ["Write a Python script that segments", "nuclei and measures their area in µm².", "Do not silently resize or normalise."],
         ("mono", ["labels = segment(img)", "area_um2 = area_px * px_um**2"])),
        ("run", "Let an agent run it", "runs and optimises the workflow",
         ["Optimise the nuclei segmentation on", "the training folder and report the F1.", "Do not open the held-out folder."],
         ("mono", ["run 1   F1 0.62", "run 4   F1 0.81   saved"])),
        ("answer", "Ask for the answer", "multimodal model, direct answer",
         ["How many nuclei are", "in this image?"],
         ("text", ["There are 7 nuclei."]))]
G2 = 12
gx_, gy_ = xB + 14, YO + 70
cw2 = (WB - 28 - G2) / 2
ch2 = (YO + HTOP - 16 - gy_ - G2) / 2
def petal(cx, cy, s=0.5, col=INK):
    return "".join(f'<rect x="{cx-6.5*s}" y="{cy-17*s}" width="{13*s}" height="{28*s}" rx="{6.5*s}" fill="none" stroke="{col}" '
                   f'stroke-width="2" transform="rotate({q*60} {cx} {cy})"/>' for q in range(6))
def bubble(x, y, w, h, fill, stroke, tail):          # tail: "br" (prompt, user side) or "bl" (reply, LLM side)
    tx = x + w - 34 if tail == "br" else x + 34
    d = (f'M{x+10},{y} h{w-20} a10,10 0 0 1 10,10 v{h-20} a10,10 0 0 1 -10,10 '
         + (f'H{tx+12} l2,12 l-14,-12 ' if tail == "br" else f'H{tx+12} l-14,12 l2,-12 ')
         + f'H{x+10} a10,10 0 0 1 -10,-10 v-{h-20} a10,10 0 0 1 10,-10 z')
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>'
for q, (nm, ttl, sub, prm, (rk, rep)) in enumerate(uses):
    x0, y0 = gx_ + (q % 2) * (cw2 + G2), gy_ + (q // 2) * (ch2 + G2)
    g = [rrect(x0, y0, cw2, ch2, 12, k["tint"], k["tintstroke"], 1.3),
         f'<circle cx="{x0+22}" cy="{y0+24}" r="12" fill="{kc}"/>' + t(x0 + 22, y0 + 29, str(q + 1), 13.5, "bold", "#fff", "middle"),
         f'<g transform="translate({x0+cw2-48} {y0+36}) scale(0.9) translate({-(x0+cw2-48)} {-(y0+36)})">' + ico(nm, x0 + cw2 - 48, y0 + 36, kc) + "</g>",
         t(x0 + 44, y0 + 31, ttl, 19, "bold", "#6b2c87"),
         t(x0 + 44, y0 + 54, sub, 14.5, fill=BODY)]
    bx_ = x0 + 18
    if nm == "answer":
        IA = ch2 - 76 - 16
        g.append(real_image(bx_, y0 + 74, IA, IA, "panel_b/panelA_acquired_crop.png", 0.158436, 600, 20, "attached image"))
        bx_ += IA + 16
    bw_ = x0 + cw2 - 18 - bx_
    ph = 26 + 21 * len(prm)
    py0 = y0 + 74
    g.append(bubble(bx_, py0, bw_, ph, "#ffffff", kc, "br"))
    g.append(t(bx_ + 16, py0 + 26, ["“" + prm[0]] + prm[1:-1] + [prm[-1] + "”"] if len(prm) > 1 else ["“" + prm[0] + "”"], 15.5, fill=INK, lh=21))
    ry0 = py0 + ph + 24
    rh = ch2 - (ry0 - y0) - 16
    rx0 = bx_ + 40
    g.append(f'<g inkscape:label="LLM icon">{petal(bx_ + 14, ry0 + 20, 0.62, kc)}</g>')
    g.append(bubble(rx0, ry0, x0 + cw2 - 18 - rx0, rh, "#ffffff", k["tintstroke"], "bl"))
    yy = ry0 + rh / 2 - 10.5 * (len(rep) - 1) + 5
    if rk == "mono":
        g.append(t(rx0 + 16, yy, rep, 14, fill=INK, lh=21, style=MONO))
    else:
        g.append(t(rx0 + 16, yy, ["“" + rep[0]] + rep[1:-1] + [rep[-1] + "”"] if len(rep) > 1 else ["“" + rep[0] + "”"], 15.5, fill=INK, lh=21))
    b.append(group(f"LLM use {q+1}", "".join(g)))
add(group("Panel B LLM uses", "".join(b)))
