"""Generate Fig. 2 (segmentation and artificial labelling: is the output good enough?) as an editable SVG.

Everything is plain SVG: text stays as <text>, panels are named groups (Inkscape layers/labels),
microscopy thumbnails are procedurally drawn vector placeholders (seeded, so reproducible).
"""
import math
import base64
import json
import numpy as np
import os
import random
from xml.sax.saxutils import escape

W, H = 1840, 2334
AUDIT = os.environ.get("AUDIT", "1") == "1"  # audited wording is the default; AUDIT=0 restores the original


def V(orig, audited):
    """Original figure wording vs. wording tuned against the article text."""
    return audited if AUDIT else orig

FONT = "Arial, Helvetica, 'Liberation Sans', sans-serif"
INK = "#14223a"
BODY = "#2b3442"

C = {   # validated categorical accents (dataviz validator): extract blue, predict teal, LLM purple; neutral slate
    "A": dict(accent="#2563a8", bg="#eef4fb", stroke="#c9daef", inner="#ffffff", innerstroke="#d6e3f2",
              val="#e3edf8", tint="#e6effa", tintstroke="#a9c4e6"),
    "B": dict(accent="#1f8a70", bg="#ecf7f3", stroke="#c3e3d8", inner="#ffffff", innerstroke="#d2eae1",
              val="#dff1ea", tint="#e3f3ed", tintstroke="#9fd2c1"),
    "N": dict(accent="#34495e", bg="#f7f9fb", stroke="#dde3ea", inner="#ffffff", innerstroke="#e3e8ee",
              val="#eef2f6", tint="#f1f4f8", tintstroke="#cfd8e2"),
    "C": dict(accent="#8e44ad", bg="#f6effa", stroke="#e1cdea", inner="#ffffff", innerstroke="#ead9f1",
              val="#efe3f5", tint="#f3e9f8", tintstroke="#d2b3e0"),
}


out = []
defs = []


def add(s):
    out.append(s)


def t(x, y, s, size=17, weight="normal", fill=BODY, anchor="start", lh=None, style="", extra=""):
    """Text; s may be a str or list of lines."""
    lines = s if isinstance(s, list) else [s]
    lh = lh or size * 1.22
    st = f' font-style="{style}"' if style else ""
    if len(lines) == 1:
        return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
                f'text-anchor="{anchor}"{st}{extra}>{escape(lines[0])}</text>')
    spans = "".join(
        f'<tspan x="{x:.1f}" dy="{0 if i == 0 else lh:.1f}">{escape(l)}</tspan>' for i, l in enumerate(lines))
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
            f'text-anchor="{anchor}"{st}{extra}>{spans}</text>')


def rrect(x, y, w, h, rx=10, fill="none", stroke="none", sw=1.5, extra=""):
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{sw}"{extra}/>')


def arrow(x1, y1, x2, y2, color, sw=3, marker=None):
    m = marker or color.strip("#")
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="{sw}" '
            f'marker-end="url(#ah-{m})"/>')


def group(label, body):
    gid = label.lower().replace(" ", "-").replace("/", "").replace("(", "").replace(")", "").replace(",", "")
    return f'<g id="{gid}" inkscape:label="{escape(label)}">{body}</g>'


for col in ["#1f6fc5", "#2f9a43", "#d6336c", "#4a5568", "#1f4e8c"] + [v["accent"] for v in C.values()]:  # noqa
    m = col.strip("#")
    defs.append(f'<marker id="ah-{m}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="4.2" markerHeight="4.2" '
                f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{col}"/></marker>')

defs.append('<marker id="ah-white" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="3.6" markerHeight="3.6" '
            'orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#ffffff" stroke="#111111" stroke-width="1"/></marker>')
defs.append('<filter id="noise" x="0" y="0" width="1" height="1"><feTurbulence type="fractalNoise" '
            'baseFrequency="0.85" numOctaves="2" seed="7"/><feColorMatrix type="saturate" values="0"/>'
            '<feComponentTransfer><feFuncA type="table" tableValues="0 0.32"/></feComponentTransfer></filter>')
defs.append('<filter id="blur3"><feGaussianBlur stdDeviation="3"/></filter>')
defs.append('<filter id="blur1"><feGaussianBlur stdDeviation="0.8"/></filter>')
defs.append('<filter id="glow"><feGaussianBlur stdDeviation="1.6" result="b"/><feMerge><feMergeNode in="b"/>'
            '<feMergeNode in="SourceGraphic"/></feMerge></filter>')
defs.append('<radialGradient id="nucGrad" cx="45%" cy="40%" r="65%"><stop offset="0" stop-color="#d9d9d9"/>'
            '<stop offset="0.7" stop-color="#9b9b9b"/><stop offset="1" stop-color="#6d6d6d"/></radialGradient>')
defs.append('<radialGradient id="nucGradRaw" cx="50%" cy="50%" r="60%"><stop offset="0" stop-color="#b4b4b4"/>'
            '<stop offset="1" stop-color="#6e6e6e"/></radialGradient>')
defs.append('<radialGradient id="nucGradPred" cx="50%" cy="50%" r="60%"><stop offset="0" stop-color="#bdbdbd"/>'
            '<stop offset="0.75" stop-color="#8a8a8a"/><stop offset="1" stop-color="#f2f2f2"/></radialGradient>')

clip_n = [0]


def clip(x, y, w, h, rx=2):
    clip_n[0] += 1
    cid = f"clip{clip_n[0]}"
    defs.append(f'<clipPath id="{cid}"><rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}"/></clipPath>')
    return cid


def place_nuclei(x, y, w, h, n, seed, rmin, rmax):
    rng = random.Random(seed)
    pts = []
    tries = 0
    while len(pts) < n and tries < 4000:
        tries += 1
        r = rng.uniform(rmin, rmax)
        cx, cy = rng.uniform(x - r * 0.3, x + w + r * 0.3), rng.uniform(y - r * 0.3, y + h + r * 0.3)
        if all(math.hypot(cx - px, cy - py) > (r + pr) * 0.92 for px, py, pr, *_ in pts):
            pts.append((cx, cy, r, rng.uniform(0.72, 1.0), rng.uniform(0, 180), rng.random()))
    return pts


LABEL_COLS = ["#ff4fa3", "#ffd23f", "#3ec1ff", "#7b5cff", "#2ee59d", "#ff7a3d", "#c86bff", "#ff3d5a",
              "#44e0d6", "#a8f03e", "#ffa1d0", "#5a8bff"]


def micro(x, y, w, h, seed, mode="raw", n=11, rmin=None, rmax=None, scalebar=None, label=""):
    """Vector stand-in for a fluorescence image. modes: raw, pred, labels, outline_raw, outline_clean, blur, sharp"""
    rmin = rmin or min(w, h) * 0.12
    rmax = rmax or min(w, h) * 0.165
    cid = clip(x, y, w, h)
    rng = random.Random(seed * 31 + 5)
    g = [f'<g clip-path="url(#{cid})">', rrect(x, y, w, h, 2, "#0b0b0b")]
    nuc = place_nuclei(x, y, w, h, n, seed, rmin, rmax)
    for i, (cx, cy, r, asp, rot, u) in enumerate(nuc):
        tr = f'transform="rotate({rot:.0f} {cx:.1f} {cy:.1f})"'
        if mode in ("raw", "blur"):
            g.append(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{r:.1f}" ry="{r*asp:.1f}" fill="url(#nucGradRaw)" '
                     f'opacity="{0.55+0.35*u:.2f}" {tr}/>')
        elif mode in ("pred", "sharp"):
            g.append(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{r:.1f}" ry="{r*asp:.1f}" fill="url(#nucGradPred)" '
                     f'stroke="#f5f5f5" stroke-width="{max(0.8, r*0.08):.1f}" opacity="{0.8+0.2*u:.2f}" {tr}/>')
        elif mode == "labels":
            g.append(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{r:.1f}" ry="{r*asp:.1f}" '
                     f'fill="{LABEL_COLS[i % len(LABEL_COLS)]}" {tr}/>')
        elif mode in ("outline_raw", "outline_clean"):
            pts = []
            k = 9
            for j in range(k):
                a = 2 * math.pi * j / k
                rr = r * 1.6 * rng.uniform(0.75, 1.15)
                pts.append((cx + rr * math.cos(a), cy + rr * asp * math.sin(a)))
            d = "M" + " L".join(f"{px:.1f},{py:.1f}" for px, py in pts) + " Z"
            op = "0.55" if mode == "outline_raw" else "0.95"
            g.append(f'<path d="{d}" fill="#1c1c1c" stroke="#d8d8d8" stroke-width="1.6" stroke-linejoin="round" '
                     f'opacity="{op}"/>')
            g.append(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{r*0.55:.1f}" ry="{r*0.5:.1f}" fill="none" '
                     f'stroke="#bbbbbb" stroke-width="1.2" opacity="{op}"/>')
        # nuclear texture
        if mode in ("raw", "pred", "sharp", "blur"):
            for _ in range(int(3 + r / 3)):
                a, d = rng.uniform(0, 2 * math.pi), rng.uniform(0, r * 0.65)
                sx, sy = cx + d * math.cos(a), cy + d * math.sin(a) * asp
                col = "#ffffff" if mode in ("pred", "sharp") else "#bdbdbd"
                g.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="{rng.uniform(0.6, 1.7):.1f}" fill="{col}" '
                         f'opacity="{rng.uniform(0.25, 0.6):.2f}"/>')
    g.append("</g>")
    body = "".join(g)
    if mode == "blur":
        body = f'<g filter="url(#blur3)">{body}</g>'
    if mode in ("raw", "outline_raw", "blur"):
        body += f'<g clip-path="url(#{cid})"><rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" filter="url(#noise)"/></g>'
    if scalebar:
        body += (f'<line x1="{x+w-8-w*0.28:.1f}" y1="{y+h-8:.1f}" x2="{x+w-8:.1f}" y2="{y+h-8:.1f}" stroke="#fff" stroke-width="2.5"/>'
                 + t(x + w - 8 - w * 0.14, y + h - 13, scalebar, 11.5, "normal", "#ffffff", "middle"))
    return f'<g inkscape:label="image {escape(label)}">{body}</g>'


def real_image(x, y, w, h, png, um_per_px, img_w_px, bar_um, label, bar_col="#ffffff"):
    """Embed a real microscopy crop (PNG exported at native pixels, linear display range) with a calibrated scale bar."""
    cid = clip(x, y, w, h)
    data = base64.b64encode(open(png, "rb").read()).decode()
    bar = bar_um / (img_w_px * um_per_px) * w  # scale-bar length in figure units
    return (f'<g inkscape:label="image {escape(label)}"><g clip-path="url(#{cid})">'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#000"/>'
            f'<image x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid slice" '
            f'xlink:href="data:image/png;base64,{data}"/></g>'
            + ("</g>" if bar_um == 0 else "") + (
            f'<line x1="{x+w-8-bar:.2f}" y1="{y+h-8}" x2="{x+w-8}" y2="{y+h-8}" stroke="{bar_col}" stroke-width="2.5" '
            f'inkscape:label="scale bar {bar_um} um"/>'
            + t(x + w - 8 - bar / 2, y + h - 13, f"{bar_um:g} µm", 13, "bold", bar_col, "middle") + "</g>" if bar_um else ""))


def network(cx, cy, col, scale=1.0):
    layers = [[-22, 0, 22], [-30, -10, 10, 30], [-22, 0, 22], [0]]
    xs = [-42, -14, 14, 42]
    pts = [[(cx + xs[i] * scale, cy + v * scale) for v in L] for i, L in enumerate(layers)]
    s = []
    for a, b in zip(pts, pts[1:]):
        for p in a:
            for q in b:
                s.append(f'<line x1="{p[0]:.1f}" y1="{p[1]:.1f}" x2="{q[0]:.1f}" y2="{q[1]:.1f}" stroke="{col}" '
                         f'stroke-width="1.2" opacity="0.7"/>')
    for L in pts:
        for p in L:
            s.append(f'<circle cx="{p[0]:.1f}" cy="{p[1]:.1f}" r="{5.2*scale:.1f}" fill="{col}"/>')
    return '<g inkscape:label="network icon">' + "".join(s) + "</g>"


def unet(cx, cy, col, label="U-Net icon"):
    """Encoder-decoder (U-Net-like) schematic: contracting path, bottleneck, expanding path, skip connections."""
    m = col.strip("#")
    # (x left, y top, width, height) relative to centre: encoder 0, encoder 1, bottleneck, decoder 1, decoder 0
    bars = [(-60, -38, 13, 32), (-40, -2, 13, 22), (-11, 26, 22, 14), (27, -2, 13, 22), (47, -38, 13, 32)]
    s = []
    for i, (x, y, w, h) in enumerate(bars):
        s.append(f'<rect x="{cx+x:.1f}" y="{cy+y:.1f}" width="{w}" height="{h}" rx="2.5" fill="{col}" '
                 f'opacity="{1 if i != 2 else 0.75}"/>')
    # down-sampling (encoder) and up-sampling (decoder) steps
    steps = [((-53.5, -6), (-33.5, -2)), ((-33.5, 20), (-6, 26)), ((6, 26), (33.5, 20)), ((33.5, -2), (53.5, -6))]
    for (x1, y1), (x2, y2) in steps:
        s.append(f'<line x1="{cx+x1:.1f}" y1="{cy+y1+2:.1f}" x2="{cx+x2:.1f}" y2="{cy+y2-1:.1f}" stroke="{col}" '
                 f'stroke-width="1.8" marker-end="url(#ah-{m})"/>')
    # skip connections (copy and concatenate)
    for y, x1, x2 in [(-22, -47, 46), (9, -27, 26)]:
        s.append(f'<line x1="{cx+x1:.1f}" y1="{cy+y:.1f}" x2="{cx+x2:.1f}" y2="{cy+y:.1f}" stroke="{col}" '
                 f'stroke-width="1.6" stroke-dasharray="4 3" marker-end="url(#ah-{m})"/>')
    return f'<g inkscape:label="{label}">' + "".join(s) + "</g>"


def unet2(cx, cy, col):
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


def check_badge(cx, cy, col, r=22):
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{col}"/>'
            f'<path d="M{cx-10},{cy+1} L{cx-3},{cy+8} L{cx+11},{cy-8}" fill="none" stroke="#fff" stroke-width="4.5" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')


def bullets(x, y, items, size=15.5, lh=19.5, gap=5, col=BODY):
    s, yy = [], y
    for lines in items:
        s.append(f'<circle cx="{x-10}" cy="{yy-5}" r="2.6" fill="{col}"/>')
        s.append(t(x, yy, lines, size, fill=col, lh=lh))
        yy += lh * len(lines) + gap
    return "".join(s)


def validate_box(x, y, w, h, key, items, size=15.5, lh=19.5):
    c = C[key]
    return group(f"Validate {key}", rrect(x, y, w, h, 12, c["val"]) + check_badge(x + 40, y + 38, c["accent"])
                 + t(x + 76, y + 44, "Validate", 20, "bold", INK)
                 + bullets(x + 92, y + 72, items, size, lh, 3))


def panel_header(x, letter, title, desc, key, desc_size=16.5):
    c = C[key]
    return (rrect(x, 96, {"A": 616, "B": 568, "C": 584}[key], 892, 16, c["bg"], c["stroke"], 2)
            + f'<circle cx="{x+44}" cy="142" r="23" fill="{c["accent"]}"/>'
            + t(x + 44, 151, letter, 26, "bold", "#fff", "middle")
            + t(x + 82, 150, title, 24, "bold", INK)
            + t(x + 82, 180, desc, desc_size, fill=BODY, lh=20))


def step_pill(x, y, num, label, col):
    return (rrect(x, y, 26 + 8.6 * len(label), 24, 12, col)
            + f'<circle cx="{x+12}" cy="{y+12}" r="8.5" fill="#ffffff"/>'
            + t(x + 12, y + 16.5, str(num), 12.5, "bold", col, "middle")
            + t(x + 27, y + 17, label, 13.5, "bold", "#ffffff"))


def caution(cx, cy, col="#d98a00"):
    return (f'<path d="M{cx},{cy-10} L{cx+11},{cy+9} L{cx-11},{cy+9} Z" fill="{col}" stroke="{col}" '
            f'stroke-width="2" stroke-linejoin="round"/>' + t(cx, cy + 6.5, "!", 13, "bold", "#ffffff", "middle"))


def vector_outlines(x, y, w, h, path, col="#ff3dd2", sw=1.0):
    d = json.load(open(path))
    sx, sy = w / d["w"], h / d["h"]
    cid = clip(x, y, w, h)
    paths = "".join(
        '<polyline points="' + " ".join(f"{x+px*sx:.1f},{y+py*sy:.1f}" for px, py in c) + '"/>' for c in d["contours"])
    return (f'<g clip-path="url(#{cid})" fill="none" stroke="{col}" stroke-width="{sw}" stroke-linejoin="round" '
            f'opacity="0.95" inkscape:label="cell outlines (Cellpose on predicted PECAM, vector)">{paths}</g>')


def gear(cx, cy, r, teeth=8):
    s = []
    for k in range(teeth * 2):
        a0 = math.pi * k / teeth
        rr = r if k % 2 == 0 else r * 0.78
        for da in (-0.17, 0.17):
            s.append((cx + rr * math.cos(a0 + da), cy + rr * math.sin(a0 + da)))
    d = "M" + " L".join(f"{p:.1f},{q:.1f}" for p, q in s) + " Z"
    return (f'<path d="{d}" fill="{icol}"/><circle cx="{cx}" cy="{cy}" r="{r*0.32:.1f}" fill="{cC["tint"]}"/>')

def chevron(x, y, col="#1f4e8c"):
    return f'<path d="M{x},{y-14} L{x+22},{y} L{x},{y+14} L{x+8},{y} Z" fill="{col}"/>' \
           f'<line x1="{x-28}" y1="{y}" x2="{x+4}" y2="{y}" stroke="{col}" stroke-width="3.5"/>'


def vector_outlines_l(x, y, w, h, path, label, col, sw=1.0, dash=None):
    g = vector_outlines(x, y, w, h, path, col, sw)
    g = g.replace('inkscape:label="cell outlines (Cellpose on predicted PECAM, vector)"', f'inkscape:label="{escape(label)}"')
    return g.replace('opacity="0.95"', f'opacity="0.95"{f" stroke-dasharray=\"{dash}\"" if dash else ""}')


def validate_col(x, y, w, h, key, items, size=15.5, lh=19.5):
    c = C[key]
    return group(f"Validate {key}", rrect(x, y, w, h, 12, c["val"]) + check_badge(x + 36, y + 36, c["accent"], 20)
                 + t(x + 66, y + 43, "Validate", 20, "bold", INK) + bullets(x + 40, y + 82, items, size, lh, 7))


def row(y, h, key, letter, title, desc):
    c = C[key]
    return (rrect(28, y, 1784, h, 16, c["bg"], c["stroke"], 2)
            + f'<circle cx="70" cy="{y+38}" r="22" fill="{c["accent"]}"/>' + t(70, y + 47, letter, 25, "bold", "#fff", "middle")
            + t(106, y + 46, title, 24, "bold", INK))            # description line removed (author request)


HH = 66                       # row header height


PX = 0.649614
cA, cB, cC = C["A"], C["B"], C["C"]
icol = cC["accent"]

# figure title and subtitle moved to the legend


HC = 400                      # content height of the segmentation row
IMW, IMH = 240, 320           # main image size


def image_pipeline(ct, col, left_lbl, right_lbl, right_png, right_w, ai_lines, right_bar, hc=None):
    """Acquired image -> AI model (U-Net) -> output image, shared by panels A and B (same geometry, aligned columns)."""
    k = C[col]
    hc = hc or HC
    p = [rrect(44, ct, 700, hc, 12, k["inner"], k["innerstroke"])]
    ct += (hc - 400) / 2                    # centre the pipeline (designed for 400) in taller rows
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
    return p


MONO = 'font-family="Liberation Mono, Courier New, monospace"'


VH = 88                       # validation strip height


def validate_strip(y, key, items, cols_x=(276, 784, 1292), size=17, lh=21):
    c = C[key]
    g = [rrect(44, y, 1752, VH, 12, c["val"]), check_badge(82, y + VH / 2, c["accent"], 22),
         t(114, y + VH / 2 + 8, "Validate", 23, "bold", INK)]
    for x, lines in zip(cols_x, items):
        g.append(f'<circle cx="{x-11}" cy="{y+21}" r="3" fill="{BODY}"/>' + t(x, y + 27, lines, size, fill=BODY, lh=lh))
    return group(f"Validate {key}", "".join(g))


def box_title(cx, y, title, sub=None):
    return t(cx, y, title, 16.5, "bold", INK, "middle") + (t(cx, y + 20, sub, 14.5, fill=BODY, anchor="middle") if sub else "")


# outline code used throughout A and B: model = solid magenta, manual reference = cyan dashed, second annotator = yellow dashed
MODEL, REF, REF2, DASH = "#ff3dd2", "#26c7ff", "#ffd23f", "4 2.5"
COL2, COL3 = (764, 380), (1160, 636)          # column grid for rows B and C: application (narrow), example (wide)
COL2D, COL3D = (764, 572), (1352, 444)        # column grid for row D


def key_item(x, y, colr, label, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<line x1="{x}" y1="{y}" x2="{x+22}" y2="{y}" stroke="{colr}" stroke-width="3"{d}/>'
            + t(x + 28, y + 5, label, 14, fill=BODY))


def bar(x, y, w, v, colr, label, value_txt=None):
    return (t(x, y, label, 14, fill=BODY)
            + f'<rect x="{x}" y="{y+5}" width="{w}" height="12" rx="3" fill="#e4e8ee"/>'
            + f'<rect x="{x}" y="{y+5}" width="{w*v:.1f}" height="12" rx="3" fill="{colr}"/>'
            + t(x + w + 6, y + 16, value_txt or f"{v:.2f}", 14, "bold", INK))


def vector_outlines_sub(x, y, w, h, path, label, col, sw, dash, sub):
    """Outlines from a full-crop contour file, shown for a sub-region (sx, sy, sw, sh in crop pixels) scaled into w x h."""
    d = json.load(open(path))
    sx0, sy0, sw0, sh0 = sub
    k = w / sw0
    cid = clip(x, y, w, h)
    paths = "".join('<polyline points="' + " ".join(f"{x+(px-sx0)*k:.1f},{y+(py-sy0)*k:.1f}" for px, py in c) + '"/>'
                    for c in d["contours"])
    da = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<g clip-path="url(#{cid})" fill="none" stroke="{col}" stroke-width="{sw}" stroke-linejoin="round"{da} '
            f'inkscape:label="{escape(label)}">{paths}</g>')


def score_row(x1, ry, tiles, bars_, bx, bw=150, gap=36):
    """One example row of a score card: image tile(s) with outlines, then bars (grey = benchmark, colour = this field)."""
    g = []
    for tl in tiles:
        g.append(tl)
    for i, (lbl, v, colr, txt) in enumerate(bars_):
        g.append(bar(bx, ry + 16 + i * gap, bw, v, colr, lbl, txt))
    return "".join(g)


def b_icon(name, cx, cy, col):
    """Small line icons for the uses of a predicted image."""
    st_ = f'fill="none" stroke="{col}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"'
    if name == "visualise":
        return (f'<path d="M{cx-22},{cy} Q{cx},{cy-18} {cx+22},{cy} Q{cx},{cy+18} {cx-22},{cy} Z" {st_}/>'
                f'<circle cx="{cx}" cy="{cy}" r="6.5" fill="{col}"/>')
    if name == "segment":
        return (f'<circle cx="{cx-9}" cy="{cy}" r="12" {st_}/><circle cx="{cx+11}" cy="{cy-2}" r="11" {st_} stroke-dasharray="4 3"/>')
    if name == "detect":
        c = [f'<circle cx="{cx}" cy="{cy}" r="7" fill="{col}"/>']
        for sx, sy in [(-1, -1), (1, -1), (1, 1), (-1, 1)]:
            c.append(f'<path d="M{cx+sx*18},{cy+sy*8} V{cy+sy*18} H{cx+sx*8}" {st_}/>')
        return "".join(c)
    if name == "register":
        return (f'<rect x="{cx-20}" y="{cy-16}" width="24" height="24" rx="2" {st_}/>'
                f'<rect x="{cx-6}" y="{cy-6}" width="24" height="24" rx="2" {st_} stroke-dasharray="4 3"/>')
    if name == "intensity":
        return "".join(f'<rect x="{cx-20+i*10}" y="{cy+16-h}" width="7" height="{h}" rx="1.5" fill="{col}"/>'
                       for i, h in enumerate([10, 22, 32, 18]))
    if name == "abundance":
        return "".join(f'<circle cx="{cx+dx}" cy="{cy+dy}" r="5" fill="{col}"/>'
                       for dx, dy in [(-12, 12), (0, 12), (12, 12), (-6, 1), (6, 1), (0, -10)])
    if name == "localisation":
        return (f'<circle cx="{cx}" cy="{cy}" r="17" {st_}/><circle cx="{cx}" cy="{cy}" r="8" {st_}/>'
                f'<circle cx="{cx}" cy="{cy}" r="2.8" fill="{col}"/>')
    return ""


def halo(x, y, txt, anchor="start", size=13):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="bold" fill="#ffffff" text-anchor="{anchor}" '
            f'stroke="#000000" stroke-width="2.6" stroke-opacity="0.55" paint-order="stroke">{escape(txt)}</text>')


def split_widget(x, y, png, left_lbl, right_lbl, bar=None):
    """Before/after widget: left half input, right half AI output, slider-style divider."""
    cid = clip(x, y, WS, WS, 9)
    data = base64.b64encode(open(png, "rb").read()).decode()
    g = [f'<g clip-path="url(#{cid})"><image x="{x}" y="{y}" width="{WS}" height="{WS}" preserveAspectRatio="none" '
         f'xlink:href="data:image/png;base64,{data}"/></g>',
         f'<line x1="{x+WS/2}" y1="{y}" x2="{x+WS/2}" y2="{y+WS}" stroke="#ffffff" stroke-width="2"/>',
         halo(x + 6, y + 15, left_lbl), halo(x + WS - 6, y + 15, right_lbl, "end"),
         rrect(x, y, WS, WS, 9, "none", "#ffffff", 1.2)]
    if bar:                                   # (bar length in units, label)
        g.append(f'<line x1="{x+WS-8-bar[0]:.1f}" y1="{y+WS-9}" x2="{x+WS-8}" y2="{y+WS-9}" stroke="#ffffff" stroke-width="2.5"/>'
                 + halo(x + WS - 8 - bar[0] / 2, y + WS - 14, bar[1], "middle", 12))
    return "".join(g)


def split_widget_r(x, y, w, h, png, left_lbl, right_lbl):
    cid = clip(x, y, w, h, 2)
    data = base64.b64encode(open(png, "rb").read()).decode()
    return (f'<g clip-path="url(#{cid})"><image x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="none" '
            f'xlink:href="data:image/png;base64,{data}"/></g>'
            f'<line x1="{x+w/2}" y1="{y}" x2="{x+w/2}" y2="{y+h}" stroke="#ffffff" stroke-width="2"/>'
            + halo(x + 6, y + 16, left_lbl) + halo(x + w - 6, y + 16, right_lbl, "end"))



NN = C["N"]
F1C, RC = "#4c5fa8", "#d08a1f"                  # one colour per metric, as in Fig. 1


def frame(x, y, w, h, L, title, key="N"):
    k = C[key]
    return (rrect(x, y, w, h, 16, NN["bg"], NN["stroke"], 1.4)
            + f'<circle cx="{x+42}" cy="{y+38}" r="22" fill="{k["accent"]}"/>' + t(x + 42, y + 47, L, 25, "bold", "#fff", "middle")
            + t(x + 78, y + 46, title, 24, "bold", INK))

# ======================================================================= FIGURE 2 BODY
# ======================================================================= FIGURE 3 BODY: four ways to use an LLM, real runs
LL = C["C"]                                   # LLM purple, as in Fig. 1b
ACC = LL["accent"]
MONO = ' font-family="DejaVu Sans Mono, Menlo, Consolas, monospace"'
OKF, OKS = "#eef8f1", "#b9e0c5"
NOF, NOS, NOC = "#fdf0ef", "#efc2be", "#c8423b"
MCOL = {"haiku": "#56b4e9", "sonnet": "#e69f00", "opus": "#cc79a7"}   # Okabe-Ito, one colour per model
YO = 20


def petal(cx, cy, s=0.55, col=ACC):
    return "".join(f'<rect x="{cx-6.5*s:.1f}" y="{cy-17*s:.1f}" width="{13*s:.1f}" height="{28*s:.1f}" rx="{6.5*s:.1f}" fill="none" '
                   f'stroke="{col}" stroke-width="2" transform="rotate({q*60} {cx} {cy})"/>' for q in range(6))


def person(cx, cy, col=INK):
    return (f'<circle cx="{cx}" cy="{cy-7}" r="6.5" fill="none" stroke="{col}" stroke-width="2"/>'
            f'<path d="M{cx-11},{cy+12} a11,11 0 0 1 22,0" fill="none" stroke="{col}" stroke-width="2"/>')


def bubble(x, y, w, h, fill, stroke, side):
    tx = x + w - 30 if side == "r" else x + 30
    d = (f'M{x+10},{y} h{w-20} a10,10 0 0 1 10,10 v{h-20} a10,10 0 0 1 -10,10 '
         + (f'H{tx+10} l2,11 l-13,-11 ' if side == "r" else f'H{tx+10} l-13,11 l2,-11 ')
         + f'H{x+10} a10,10 0 0 1 -10,-10 v-{h-20} a10,10 0 0 1 10,-10 z')
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="1.4"/>'


def prompt(x, y, w, lines, size=14):
    h = 18 + 18 * len(lines)
    return (bubble(x + 30, y, w - 30, h, "#ffffff", "#b8c2d0", "l") + f'<g>{person(x + 12, y + h / 2)}</g>'
            + t(x + 46, y + 22, lines, size, fill=INK, lh=18)), h + 12


def reply(x, y, w, lines, size=13, mono=True, title=None):
    h = 16 + 17 * len(lines) + (18 if title else 0)
    g = [bubble(x, y, w - 30, h, LL["tint"], LL["tintstroke"], "r"), f'<g>{petal(x + w - 12, y + h / 2)}</g>']
    yy = y + 20
    if title:
        g.append(t(x + 12, yy, title, 12.5, "bold", "#6b2c87")); yy += 18
    g.append(t(x + 12, yy, lines, size, fill=INK, lh=17, extra=MONO if mono else ""))
    return "".join(g), h + 12


def terminal(x, y, w, lines, size=12.5):
    h = 30 + 17 * len(lines)
    g = [rrect(x, y, w, h, 8, "#1b2230", "none"),
         "".join(f'<circle cx="{x+14+i*13}" cy="{y+12}" r="4" fill="{c}"/>' for i, c in enumerate(["#ff5f57", "#febc2e", "#28c840"]))]
    yy = y + 32
    for ln, col in lines:
        g.append(t(x + 10, yy, ln, size, fill=col, extra=MONO)); yy += 17
    return "".join(g), h + 12


def check_box(x, y, w, lines):
    h = 22 + 18 * len(lines)
    return (rrect(x, y, w, h, 10, OKF, OKS, 1.4)
            + check_badge(x + 20, y + h / 2, "#1f8a70", 10).replace('stroke-width="4.5"', 'stroke-width="2.6"')
            .replace(f"M{x+10},{y+h/2+1} L{x+17},{y+h/2+8} L{x+31},{y+h/2-8}", f"M{x+15},{y+h/2} L{x+19},{y+h/2+4} L{x+26},{y+h/2-4}")
            + t(x + 38, y + 20, lines, 13.5, fill=INK, lh=18))


def note(x, y, lines, col=NOC):
    return t(x, y, lines, 13.5, "bold", col, lh=18)


# ---------------------------------------------------------------- delegation gradient across the four columns
gid = "llmgrad"
defs.append(f'<linearGradient id="{gid}" x1="0" x2="1"><stop offset="0" stop-color="#c7b3e0"/><stop offset="1" stop-color="{ACC}"/></linearGradient>')
add(group("delegation gradient", f'<path d="M28,{YO} H1796 L1812,{YO+15} L1796,{YO+30} H28 Z" fill="url(#{gid})"/>'
          + t(44, YO + 21, "more of the analysis delegated to the LLM  →  more decisions hidden", 15, "bold", "#ffffff")))
CY = YO + 42
CW = (1784 - 3 * 10) / 4
CH = 850
cols = [28 + i * (CW + 10) for i in range(4)]


def col_frame(i, title, sub):
    x = cols[i]
    return (rrect(x, CY, CW, CH, 16, NN["bg"], NN["stroke"], 1.4)
            + f'<circle cx="{x+36}" cy="{CY+36}" r="20" fill="{ACC}"/>' + t(x + 36, CY + 44, "abcd"[i], 22, "bold", "#fff", "middle")
            + t(x + 66, CY + 34, title, 20, "bold", INK) + t(x + 66, CY + 55, sub, 13.5, fill=BODY))


IN = 16                                       # inner padding
# ================================================================ a: ask for advice
x = cols[0]; w = CW - 2 * IN; xi = x + IN
g = [col_frame(0, "Ask for advice", "software, parameters, approaches")]
y = CY + 82
s, h = prompt(xi, y, w, ["How should I segment nuclei in 2D", "DAPI images with Cellpose in Python?"]); g.append(s); y += h
s, h = reply(xi, y, w, ['model = models.Cellpose(', '    model_type="nuclei")', 'masks, flows, styles, diams = \\', '    model.eval(img, channels=[0, 0])'],
             title="LLM reply, first code example (3/3 runs)"); g.append(s); y += h + 6
g.append(t(xi, y + 4, "Run as given with the installed Cellpose (4.2.1.1):", 13.5, "bold", INK)); y += 14
s, h = terminal(xi, y, w, [(">>> models.Cellpose(model_type='nuclei')", "#d5dbe5"),
                           ("AttributeError: module 'cellpose.models'", "#ff8a80"), ("  has no attribute 'Cellpose'", "#ff8a80")]); g.append(s); y += h
g.append(t(xi, y + 6, "Variant suggested in the same reply:", 13.5, "bold", INK)); y += 16
s, h = terminal(xi, y, w, [(">>> models.CellposeModel(model_type='nuclei')", "#d5dbe5"),
                           ("WARNING model_type argument is not used", "#ffd166"), ("  in v4.0.1+. Ignoring this argument...", "#ffd166"),
                           ("loading model cpsam_v2", "#9be7a1")]); g.append(s); y += h
g.append(note(xi, y + 10, ["The advised 'nuclei' model no longer exists:", "the code fails, or silently runs a different", "model; only a log line says so."]))
y += 76
g.append(t(xi, y, ["The reply also gave current-version code and", "said to check the installed version: the advice", "is plausible, mixed and easy to copy wrongly."], 13, fill=BODY, lh=17))
g.append(check_box(xi, CY + CH - 16 - 58, w, ["Verify against the documentation of", "the version you have installed."]))
add(group("a advice", "".join(g)))

# ================================================================ b: ask for code
x = cols[1]; w = CW - 2 * IN; xi = x + IN
g = [col_frame(1, "Ask for code", "e.g. Python, Fiji macro")]
y = CY + 82
RES = {k: json.load(open(f"codetest/{k}/result.json")) for k in ("vague", "box1")}
CR = json.load(open("assets/code_roi.json"))
hw = (w - 12) / 2
for k_, (key, ttl, lines) in enumerate([("vague", "Vague prompt", ["“Write a Python script that", "measures nuclear area in", "nuclei.tif.”"]),
                                        ("box1", "Box 1 prompt", ["“…pixel size 0.65 µm; do not", "silently resize or normalise;", "expose parameters; include", "a test; list assumptions.”"])]):
    xx = xi + k_ * (hw + 12)
    g.append(t(xx, y + 4, ttl, 15, "bold", INK))
    g.append(rrect(xx, y + 14, hw, 92, 8, "#ffffff", "#b8c2d0", 1.2) + t(xx + 10, y + 34, lines, 12.5, fill=INK, lh=17))
y += 122
TS = hw
for k_, key in enumerate(["vague", "box1"]):
    xx = xi + k_ * (hw + 12)
    g.append(group(f"b {key} tile", real_image(xx, y, TS, TS, "assets/code_dapi.png", PX, CR["w"], 20, f"b {key}")
                   + vector_outlines_sub(xx, y, TS, TS, "assets/code_manual.json", "manual nuclei (vector)", REF, 1.4, DASH, (0, 0, CR["w"], CR["w"]))
                   + vector_outlines_sub(xx, y, TS, TS, f"assets/code_{key}.json", f"{key} code (vector)", MODEL, 1.4, None, (0, 0, CR["w"], CR["w"]))))
g.append(key_item(xi, y + TS + 20, MODEL, "LLM-written code") + key_item(xi + 168, y + TS + 20, REF, "manual nuclei", DASH))
y += TS + 40
rows_ = [("runs without error", "yes", "yes"), ("nuclei F1 (IoU ≥ 0.5)", f"{RES['vague']['f1']:.2f}", f"{RES['box1']['f1']:.2f}"),
         ("area vs manual (median)", f"×{RES['vague']['area_ratio_median']:.2f}", f"×{RES['box1']['area_ratio_median']:.2f}"),
         ("extra objects", f"{RES['vague']['n_objects']-RES['vague']['matched']}", f"{RES['box1']['n_objects']-RES['box1']['matched']}"),
         ("units saved", "pixels", "µm²"), ("built-in test", "none", "passes")]
g.append(t(xi + 230, y + 4, "vague", 13.5, "bold", INK, "middle") + t(xi + 330, y + 4, "Box 1", 13.5, "bold", INK, "middle"))
for i, (lbl, a_, b_) in enumerate(rows_):
    yy = y + 28 + i * 24
    g.append(t(xi, yy, lbl, 13.5, fill=BODY) + t(xi + 230, yy, a_, 13.5, "bold", NOC if i else INK, "middle")
             + t(xi + 330, yy, b_, 13.5, "bold", NOC if i in (1, 2, 3) else INK, "middle"))
y += 28 + len(rows_) * 24
g.append(note(xi, y + 6, ["Both run without error. The vague code finds", "1 nucleus in 3 and shrinks them by a third;", "the specified code is better but still adds", f"{RES['box1']['n_objects']-RES['box1']['matched']} extra objects. Neither is validated."]))
g.append(check_box(xi, CY + CH - 16 - 58, w, ["Specify the measurement and units; test", "on images with a known result."]))
add(group("b code", "".join(g)))

# ================================================================ c: agent runs and optimises
x = cols[2]; w = CW - 2 * IN; xi = x + IN
g = [col_frame(2, "Let an agent run it", "runs and optimises the workflow")]
y = CY + 82
s, h = prompt(xi, y, w, ["Optimise nuclei segmentation on the", "development half; log each change."]); g.append(s); y += h
HO = json.load(open("heldout/heldout_scores.json"))
FS_ = 118
g.append(group("c field split", real_image(xi, y, FS_, FS_, "assets/agent_field.png", PX, 1024, 0, "c DAPI field")
               + f'<rect x="{xi}" y="{y}" width="{FS_}" height="{FS_/2}" fill="none" stroke="{ACC}" stroke-width="2.5"/>'
               + f'<rect x="{xi}" y="{y+FS_/2}" width="{FS_}" height="{FS_/2}" fill="#0b111d" fill-opacity="0.55" stroke="#8a94a3" stroke-width="2.5" stroke-dasharray="6 4"/>'
               + halo(xi + 5, y + 15, "development", size=11.5) + halo(xi + 5, y + FS_ / 2 + 15, "held out", size=11.5)))
px0, py0, pw_, ph_ = xi + FS_ + 50, y + 4, w - FS_ - 86, FS_ - 22
lo_, hi_ = 0.75, 0.95
Yv = lambda v: py0 + ph_ - ph_ * (v - lo_) / (hi_ - lo_)
Xv = lambda i: px0 + pw_ * (i - 1) / 4
g.append(f'<line x1="{px0}" y1="{py0+ph_}" x2="{px0+pw_}" y2="{py0+ph_}" stroke="{INK}" stroke-width="1.2"/>'
         f'<line x1="{px0}" y1="{py0}" x2="{px0}" y2="{py0+ph_}" stroke="{INK}" stroke-width="1.2"/>')
for v in (0.75, 0.95):
    g.append(t(px0 - 5, Yv(v) + 4, f"{v:.2f}", 11, fill=BODY, anchor="end"))
g.append(t(px0 + pw_ / 2, py0 + ph_ + 15, "iteration 1–5", 11.5, fill=BODY, anchor="middle")
         + f'<text x="{px0-30}" y="{py0+ph_/2}" font-size="11.5" fill="{BODY}" text-anchor="middle" transform="rotate(-90 {px0-30} {py0+ph_/2})">F1</text>')
for key, colr, dash in [("dev", ACC, None), ("heldout", "#4a5568", "6 4")]:
    pts = " ".join(f"{Xv(r['version']):.1f},{Yv(r[key]):.1f}" for r in HO)
    g.append(f'<polyline points="{pts}" fill="none" stroke="{colr}" stroke-width="2.4"' + (f' stroke-dasharray="{dash}"' if dash else "") + "/>"
             + "".join(f'<circle cx="{Xv(r["version"]):.1f}" cy="{Yv(r[key]):.1f}" r="3.2" fill="{colr}"/>' for r in HO)
             + t(Xv(5) + 6, Yv(HO[-1][key]) + (0 if key == "dev" else 12), f"{HO[-1][key]:.2f}", 12, "bold", colr))
y += FS_ + 14
s, h = reply(xi, y, w, ["it 2: drop objects with mean intensity", "  > 550 or area > 1000 px  →  F1 0.78 → 0.89"],
             title="agent log, iteration 2 (excerpt)", size=12.5); g.append(s); y += h + 2
EX = json.load(open("assets/agent_excl.json"))
TW_ = w
TH2 = TW_ * EX["h"] / EX["w"]
k_ = TW_ / EX["w"]
gg = [real_image(xi, y, TW_, TH2, "assets/agent_excl.png", PX, EX["w"], 20, "c excluded nuclei"),
      vector_outlines_sub(xi, y, TW_, TH2, "assets/agent_excl_kept.json", "kept by the agent's workflow (vector)", MODEL, 1.3, None, (0, 0, EX["w"], EX["h"]))]
for ex_, ey_, inten, area in EX["excluded"]:
    gg.append(f'<circle cx="{xi+ex_*k_:.1f}" cy="{y+ey_*k_:.1f}" r="{16*k_/1.4:.1f}" fill="none" stroke="#ffd23f" stroke-width="2.6" stroke-dasharray="5 3"/>')
gg.append(rrect(xi + 4, y + 4, 330, 40, 4, "#0b111d", "none", 0, ' fill-opacity="0.8"')
          + f'<line x1="{xi+10}" y1="{y+16}" x2="{xi+28}" y2="{y+16}" stroke="{MODEL}" stroke-width="2.5"/>' + t(xi + 34, y + 20, "kept by the agent's workflow", 12, "bold", "#ffffff")
          + f'<circle cx="{xi+19}" cy="{y+33}" r="6" fill="none" stroke="#ffd23f" stroke-width="2.2" stroke-dasharray="4 2"/>' + t(xi + 34, y + 37, "removed by its filter, yet annotated", 12, "bold", "#ffffff"))
g.append(group("c excluded nuclei", "".join(gg)))
y += TH2 + 10
g.append(note(xi, y + 8, ["To raise the score, the agent added a filter that", "also removed bright or large endothelial nuclei:", "a biological exclusion hidden in one line of code."]))
y += 64
g.append(t(xi, y, ["Given an editable evaluation list in a second run,", "it did not drop tiles; we checked, not assumed."], 13, fill=BODY, lh=17))
g.append(check_box(xi, CY + CH - 16 - 58, w, ["Hold data out; review every code", "change and every excluded object."]))
add(group("c agent", "".join(g)))

# ================================================================ d: ask for the answer -- answer table per crop
x = cols[3]; w = CW - 2 * IN; xi = x + IN
g = [col_frame(3, "Ask for the answer", "multimodal model, direct answer")]
y = CY + 82
CC = json.load(open("data/count_crops.json"))
CRES = json.load(open("data/count_results.json"))
s, h = prompt(xi, y, w, ["How many cells / nuclei / cancer cells", "are in this image?  (3 times, 3 models)"]); g.append(s); y += h
OKT, MIDT, BADT = "#1a7a4c", "#c27c0e", NOC
LBW = 30
cw_ = (w - LBW) / 6
TH_ = cw_ - 6


def colour(v, lo, hi):
    if lo <= v <= hi:
        return OKT
    err = (lo - v) / lo if v < lo else (v - hi) / hi
    return MIDT if err <= 0.25 else BADT


titles = {"cells_pecam": "Endothelial cells (PECAM-1)", "nuclei_dapi": "Nuclei (DAPI)", "cancer_bf": "Cancer cells (brightfield)"}
for key in ("cells_pecam", "nuclei_dapi", "cancer_bf"):
    g.append(t(xi, y + 12, titles[key], 14, "bold", INK)); y += 20
    rows = [r for r in CRES["rows"] if r["type"] == key]
    for c in range(6):
        cx = xi + LBW + c * cw_
        crop = CC[key][c]
        g.append(real_image(cx + 3, y, TH_, TH_, crop["file"], PX * crop["size_px"] / 512, 512, 0, f"d {key} {c+1}"))
        r = rows[c]
        g.append(t(cx + cw_ / 2, y + TH_ + 14, f"{r['lo']}–{r['hi']}" if r["lo"] != r["hi"] else str(r["lo"]), 12, "bold", INK, "middle"))
        for mi, m in enumerate(("haiku", "sonnet", "opus")):
            yy = y + TH_ + 31 + mi * 15
            vals = r[m]
            xs = [cx + cw_ / 2 - 18, cx + cw_ / 2, cx + cw_ / 2 + 18]
            for v, xx_ in zip(vals, xs):
                g.append(t(xx_, yy, str(v), 11.5, "bold", colour(v, r["lo"], r["hi"]), "middle"))
    g.append(t(xi, y + TH_ + 14, "manual", 10.5, fill=BODY))
    for mi, m in enumerate(("Haiku", "Sonnet", "Opus")):
        g.append(t(xi, y + TH_ + 31 + mi * 15, m[:2] if False else m[0], 12, "bold", MCOL[m.lower()]))
    y += TH_ + 31 + 2 * 15 + 18
# colour key + summary
g.append(t(xi, y, "answer:", 12, fill=BODY) + t(xi + 50, y, "within manual range", 12, "bold", OKT)
         + t(xi + 178, y, "≤ 25% off", 12, "bold", MIDT) + t(xi + 252, y, "> 25% off", 12, "bold", BADT))
y += 18
g.append(t(xi, y, "H, S, O: Claude Haiku, Sonnet, Opus; 3 runs each", 12, fill=BODY))
S_ = CRES["summary"]
g.append(note(xi, y + 24, ["Answers change between runs and models, and", "consistent answers can be consistently wrong",
                            f"(within range: H {S_['haiku']['within_truth_range_pct']}%, S {S_['sonnet']['within_truth_range_pct']}%, O {S_['opus']['within_truth_range_pct']}%)."]))
g.append(check_box(xi, CY + CH - 16 - 58, w, ["Not for quantification without", "validation on images with known answers."]))
add(group("d direct answer", "".join(g)))

# ================================================================ e: keep the analysis, not the conversation
EY = CY + CH + 10
EH = 120
e = [rrect(28, EY, 1784, EH, 16, NN["bg"], NN["stroke"], 1.4),
     f'<circle cx="64" cy="{EY+36}" r="20" fill="{ACC}"/>' + t(64, EY + 44, "e", 22, "bold", "#fff", "middle"),
     t(94, EY + 43, "Keep the analysis, not the conversation", 20, "bold", INK)]
items = [("1–3", "save the code, configuration, parameters, software versions and environment; the analysis should rerun without the LLM"),
         ("4", "if the LLM stays in the analysis, also keep the prompts and model version; validate against reference data"),
         ("all", "record the LLM, version, date and role; check where images are sent (provider terms, institutional or local models)")]
for i, (tag, txt) in enumerate(items):
    yy = EY + 72 + i * 0
for i, (tag, txt) in enumerate(items):
    xx = 44 + i * 590
    e.append(rrect(xx, EY + 60, 572, 50, 8, "#ffffff", NN["stroke"], 1.2) + rrect(xx + 8, EY + 72, 42, 26, 6, ACC, "none")
             + t(xx + 29, EY + 90, tag, 13, "bold", "#fff", "middle"))
    words, lines_, cur = txt.split(), [], ""
    for w_ in words:
        if len(cur) + len(w_) > 70:
            lines_.append(cur); cur = w_
        else:
            cur = (cur + " " + w_).strip()
    lines_.append(cur)
    e.append(t(xx + 60, EY + 80, lines_, 13, fill=INK, lh=17))
add(group("e reporting", "".join(e)))

H = EY + EH + 20
svg = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
       f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" xmlns:xlink="http://www.w3.org/1999/xlink" '
       f'width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">\n'
       f'<defs>{"".join(defs)}</defs>\n<rect width="{W}" height="{H}" fill="#ffffff"/>\n'
       + "\n".join(out) + "\n</svg>\n")
open("fig3.svg", "w", encoding="utf-8").write(svg)
print("written", len(svg) // 1024, "KB; height", H)
