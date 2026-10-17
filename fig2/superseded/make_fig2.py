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
            f'<line x1="{x+w-8-bar:.2f}" y1="{y+h-8}" x2="{x+w-8}" y2="{y+h-8}" stroke="{bar_col}" stroke-width="2.5" '
            f'inkscape:label="scale bar {bar_um} um"/>'
            + t(x + w - 8 - bar / 2, y + h - 13, f"{bar_um:g} µm", 13, "bold", bar_col, "middle") + "</g>")


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
YO = 20
GAPR = 10
SEGX, SEGY, SEGW, SEGH = 240, 40, 240, 260          # troubleshooting window (full-field px), as Fig. 1c step 3
cA, cB = C["A"], C["B"]
PS = json.load(open("data/perturb_scores.json"))


def f1bar(x, y, w, v, lbl=None, colr=None):
    colr = colr or F1C
    return (f'<rect x="{x}" y="{y}" width="{w}" height="10" rx="3" fill="#e4e8ee"/>'
            f'<rect x="{x}" y="{y}" width="{w*v:.1f}" height="10" rx="3" fill="{colr}"/>'
            + t(x + w + 7, y + 10, f"{v:.2f}", 14, "bold", INK) + (t(x, y - 6, lbl, 13.5, fill=BODY) if lbl else ""))


def tile(x, y, w, h, png, layers, label, markers=None, um=PX, imgw=240, bar=50, sub=(0, 0, 240, 260)):
    g = [real_image(x, y, w, h, png, um, imgw, bar, label, "#111111")]
    for path, lbl, colr, dash in layers:
        g.append(vector_outlines_sub(x, y, w, h, path, lbl, colr, 1.6, dash, sub))
    k = w / sub[2]
    for kind, pts in (markers or {}).items():
        for px, py in pts:
            cx, cy = x + (px - sub[0]) * k, y + (py - sub[1]) * k
            if kind == "missed":
                g.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="17" fill="none" stroke="{ERRC}" stroke-width="2.6"/>')
            else:
                g.append(f'<path d="M{cx-9:.1f},{cy-9:.1f} L{cx+9:.1f},{cy+9:.1f} M{cx+9:.1f},{cy-9:.1f} L{cx-9:.1f},{cy+9:.1f}" '
                         f'stroke="{ERRC}" stroke-width="3" stroke-linecap="round"/>')
    return group(label, "".join(g))


ERRC = "#ff8c1a"

# ---------------------------------------------------------------- a: when a pre-trained model fails (full width)
TH_ = 0
xb, wb = 28, 1784
LASTW = 170
NT = 7 - 1
TW = (wb - 28 - LASTW - NT * 12) / NT
TH = TW * SEGH / SEGW
R1 = round(66 + 76 + TH + 62 + 14)
bb = [frame(xb, YO, wb, R1, "a", "When a pre-trained model performs poorly, find the mismatch first", "A")]
bb.append(key_item(xb + wb - 250, YO + 42, MODEL, "model") + key_item(xb + wb - 150, YO + 42, REF, "reference", DASH))
steps = [("Default settings", ["pre-trained generalist,", "no retraining"], "cp_default", PS["default"]),
         ("Object scale", ["input downsampled 4×"], "cp_down4", PS["down4"]),
         ("Object scale", ["input upsampled 2×"], "cp_up2", PS.get("up2")),
         ("Pre-processing", ["normalisation switched off:", "no cells found"], "cp_nonorm", PS["nonorm"]),
         ("Post-processing", ["stricter probability", "threshold"], "cp_cellprob2", PS["cellprob2"]),
         ("Post-processing", ["low-contrast objects", "(endothelium) removed"], "cp_postfilter", PS["postfilter"])]
ty0 = YO + 66 + 76
for i, (ttl, sub, key, v) in enumerate(steps):
    x = xb + 14 + i * (TW + 12)
    bb.append(f'<circle cx="{x+11}" cy="{YO+86}" r="11" fill="{cA["accent"]}"/>' + t(x + 11, YO + 91, str(i + 1), 13, "bold", "#fff", "middle")
              + t(x + 28, YO + 91, ttl, 16, "bold", INK) + t(x, YO + 112, sub, 13.5, fill=BODY, lh=16))
    if v is None:                     # run still in progress: placeholder
        bb.append(rrect(x, ty0, TW, TH, 4, "#e9edf2", "#c8d3e0", 1.2, ' stroke-dasharray="6 4"')
                  + t(x + TW / 2, ty0 + TH / 2, "running…", 15, "bold", "#7a8699", "middle"))
        bb.append(t(x, ty0 + TH + 28, "F1", 13.5, fill=BODY) + t(x, ty0 + TH + 46, "pending", 14, "bold", "#7a8699"))
        continue
    bb.append(tile(x, ty0, TW, TH, "data4/B_rep_bf.png",
                   [("data4/B_rep_ref.json", "reference (vector)", REF, DASH), (f"data/ts_{key}.json", f"{ttl} (vector)", MODEL, None)],
                   f"step {i+1} {ttl}"))
    bb.append(f1bar(x, ty0 + TH + 30, TW - 52, v, "F1"))
# step 7: fine-tune only if needed (schematic)
x5 = xb + 14 + NT * (TW + 12)
bb.append(rrect(x5, YO + 70, LASTW, R1 - 70 - 14, 12, cA["tint"], cA["tintstroke"], 1.3))
bb.append(f'<circle cx="{x5+22}" cy="{YO+92}" r="11" fill="{cA["accent"]}"/>' + t(x5 + 22, YO + 97, str(NT + 1), 13, "bold", "#fff", "middle")
          + t(x5 + 40, YO + 97, "Fine-tune", 16, "bold", INK))
bb.append(t(x5 + LASTW / 2, YO + 128, ["only if a", "systematic failure", "remains"], 14, fill=BODY, anchor="middle", lh=18))
cy5 = ty0 + TH / 2 + 16
bb.append(group("fine-tune loop (schematic)",
                f'<circle cx="{x5+LASTW/2}" cy="{cy5}" r="52" fill="none" stroke="{cA["accent"]}" stroke-width="2.4" stroke-dasharray="6 5"/>'
                + t(x5 + LASTW / 2, cy5 - 64, "correct", 13.5, "bold", INK, "middle")
                + t(x5 + LASTW / 2, cy5 + 76, "retrain", 13.5, "bold", INK, "middle")
                + unet2(x5 + LASTW / 2, cy5, cA["accent"])))
bb.append(t(x5 + LASTW / 2, cy5 + 110, ["add diverse", "examples where", "it fails"], 13, fill=BODY, anchor="middle", lh=16))
add(group("a troubleshooting", "".join(bb)))

# ---------------------------------------------------------------- c: is it good enough?
Y2 = YO + R1 + GAPR
R2 = 66 + 340 + 14
cc = [frame(28, Y2, 1784, R2, "b", "Is it good enough? Check the errors that matter for the measurement", "A")]
# measurement -> error that matters
x0, w0 = 44, 560
cc.append(rrect(x0, Y2 + 66, w0, 340, 12, "#ffffff", cA["innerstroke"]))
cc.append(box_title(x0 + w0 / 2, Y2 + 96, "What will you measure?"))
MEAS = [("Counts", "missed and false objects"), ("Morphology", "boundaries of matched cells"),
        ("Phenotypes", "misclassified objects"), ("Tracks", "merges and splits break links")]
POS = [(x0 + w0 * 0.25, Y2 + 170), (x0 + w0 * 0.75, Y2 + 170), (x0 + w0 * 0.25, Y2 + 320), (x0 + w0 * 0.75, Y2 + 320)]
a = []
CT = 0
exec(open("measure_icons_block.py").read())
cc += a
cc.append(arrow(x0 + w0 + 4, Y2 + 236, x0 + w0 + 22, Y2 + 236, cA["accent"]))
# two tiles with error markers
ES = json.load(open("data/error_summary.json"))
EM = json.load(open("data/err_markers.json"))
x1 = x0 + w0 + 26
w1 = 1796 - x1
cc.append(rrect(x1, Y2 + 66, w1, 340, 12, "#ffffff", cA["innerstroke"]))
ETW = 252
ETH = ETW * 260 / 240
SUBE = (0, 0, 240, 260)
cand = [("Custom-trained", "stardist", "data/err_stardist.json", ES["stardist"]),
        ("Pre-trained generalist + post-processing", "cellpose_filtered", "data/err_cellpose_filtered.json", ES["cellpose_postfilter"])]
for k_, (lbl, key, cj, s_) in enumerate(cand):
    tx = x1 + 18 + k_ * (ETW + 22)
    cc.append(t(tx, Y2 + 94, lbl, 15, "bold", INK))
    cc.append(tile(tx, Y2 + 114, ETW, ETH, "data/err_bf.png",
                   [("data/err_ref.json", "reference (vector)", REF, DASH), (cj, f"{lbl} (vector)", MODEL, None)],
                   f"errors {lbl}", EM[key]))
# error table
tx0 = x1 + 18 + 2 * (ETW + 22) + 14
cols = [tx0 + 250, tx0 + 360]
ty = Y2 + 100
cc.append(t(cols[0], ty, ["Custom-", "trained"], 13.5, "bold", INK, "middle", lh=16)
          + t(cols[1], ty, ["Generalist +", "post-proc."], 13.5, "bold", INK, "middle", lh=16))
BIO = json.load(open("data/bio_result.json"))
rows_ = [("missed cells", "missed", "ring"), ("false objects", "false", "cross"), ("merged cells", "merges", None),
         ("split cells", "splits", None), ("boundary IoU, matched", "mean_iou_matched", None), ("F1 (IoU ≥ 0.5)", "f1", None)]
RS = 29
for r_, (lbl, key, mk) in enumerate(rows_):
    yy = ty + 46 + r_ * RS
    if r_ in (4,):
        cc.append(f'<line x1="{tx0}" y1="{yy-24}" x2="{cols[1]+50}" y2="{yy-24}" stroke="{NN["tintstroke"]}" stroke-width="1.2"/>')
    if mk == "ring":
        cc.append(f'<circle cx="{tx0+8}" cy="{yy-5}" r="7" fill="none" stroke="{ERRC}" stroke-width="2.4"/>')
    elif mk == "cross":
        cc.append(f'<path d="M{tx0+2},{yy-11} L{tx0+14},{yy+1} M{tx0+14},{yy-11} L{tx0+2},{yy+1}" stroke="{ERRC}" stroke-width="2.6" stroke-linecap="round"/>')
    cc.append(t(tx0 + 24, yy, lbl, 14.5, fill=INK))
    for ci, nm in enumerate(["stardist", "cellpose_postfilter"]):
        v = ES[nm][key]
        cc.append(t(cols[ci], yy, f"{v:.2f}" if isinstance(v, float) else str(v), 15, "bold", INK, "middle"))
yb_ = ty + 46 + 6 * RS + 8
cc.append(f'<line x1="{tx0}" y1="{yb_-20}" x2="{cols[1]+50}" y2="{yb_-20}" stroke="{NN["tintstroke"]}" stroke-width="1.2"/>')
cc.append(t(tx0, yb_, "Biological result (reference)", 13.5, "bold", "#1f4e8c"))
for r_, (lbl, key, unit, fmt) in enumerate([("cell count", "count", "", "{:.0f}"), ("mean area, µm²", "mean_area_um2", "", "{:.0f}")]):
    yy = yb_ + 26 + r_ * RS
    refv = BIO["reference"][key]
    cc.append(t(tx0 + 24, yy, f"{lbl} ({fmt.format(refv)})", 14.5, fill=INK))
    for ci, nm in enumerate(["custom_trained", "generalist_postfilter"]):
        v = BIO[nm][key]
        pct = 100 * (v / refv - 1)
        cc.append(t(cols[ci], yy, f"{fmt.format(v)} ({pct:+.0f}%)", 14.5, "bold", INK, "middle"))
add(group("c good enough", "".join(cc)))

# ---------------------------------------------------------------- d: artificial-labelling pipeline
Y3 = Y2 + R2 + GAPR
R3 = 66 + 400 + 14
add(group("d artificial labelling", frame(28, Y3, 740, R3, "c", "Artificial labelling", "B")
          + "".join(image_pipeline(Y3 + 66, "B", None, ("Output", "predicted DAPI + PECAM-1"), "data3/B_predicted_composite.png", 210,
                                   ["pix2pix"], "#ffffff", hc=400))))

# ---------------------------------------------------------------- e: what will you measure?
xe = 28 + 740 + 6
we = 1812 - xe
ee = [frame(xe, Y3, we, R3, "d", "What will you measure from the predicted image?", "B")]
halves = [("ok", "An intermediate step", ["visualise", "segment", "detect", "register"],
           ["Validate the downstream output", "against experimentally labelled samples"]),
          ("caution", "The measurement itself", ["intensity", "abundance", "localisation"],
           ["Compare with acquired fluorescence", "in independent paired samples,", "across the relevant conditions"])]
hw = (we - 28 - 14) / 2
for k_, (kind, ttl, icons, concl) in enumerate(halves):
    hx = xe + 14 + k_ * (hw + 14)
    ee.append(rrect(hx, Y3 + 66, hw, 300, 12, "#ffffff", cB["innerstroke"]))
    yb = Y3 + 110
    if kind == "ok":
        ee.append(check_badge(hx + 30, yb - 5, cB["accent"], 13).replace('stroke-width="4.5"', 'stroke-width="3"')
                  .replace(f'M{hx+20},{yb-4} L{hx+27},{yb+3} L{hx+41},{yb-13}', f'M{hx+24},{yb-5} L{hx+28.5},{yb} L{hx+36},{yb-10}'))
    else:
        ee.append(caution(hx + 30, yb - 7))
    ee.append(t(hx + 52, yb + 1, ttl, 18, "bold", INK))
    n = len(icons)
    for i, nm in enumerate(icons):
        cx = hx + 20 + (hw - 40) * (i + 0.5) / n
        ee.append(group(f"use icon {nm}", f'<g transform="translate({cx} {yb+80}) scale(1.3) translate({-cx} {-(yb+80)})">'
                        + b_icon(nm, cx, yb + 80, cB["accent"]) + "</g>"))
        ee.append(t(cx, yb + 132, nm, 15, fill=INK, anchor="middle"))
    ee.append(f'<line x1="{hx+24}" y1="{yb+158}" x2="{hx+hw-24}" y2="{yb+158}" stroke="{cB["tintstroke"]}" stroke-width="1.4" stroke-dasharray="5 4"/>')
    ee.append(t(hx + hw / 2, yb + 190, concl, 16, "bold", INK, "middle", lh=21))
# reporting rule, under both halves
ry_ = Y3 + 66 + 300 + 12
ee.append(rrect(xe + 14, ry_, we - 28, R3 - (ry_ - Y3) - 14, 12, cB["tint"], cB["tintstroke"], 1.3))
ee.append(f'<rect x="{xe+34}" y="{ry_+24}" width="58" height="40" rx="3" fill="#123"/>' + halo(xe + 63, ry_ + 49, "predicted", "middle", 12))
ee.append(t(xe + 112, ry_ + 38, "In figures and legends, label predicted images as predicted.", 16, "bold", INK)
          + t(xe + 112, ry_ + 60, "Do not describe predicted fluorescence as though the marker had been measured.", 15, fill=BODY))
add(group("e what will you measure", "".join(ee)))

# ---------------------------------------------------------------- f: compare with acquired data
Y4 = Y3 + R3 + GAPR
R4 = 66 + 330 + 14
ff = [frame(28, Y4, 1784, R4, "e", "Is it good enough? Compare with experimental reference data", "B")]
ff.append(key_item(1812 - 470, Y4 + 42, MODEL, "on predicted image") + key_item(1812 - 290, Y4 + 42, REF, "annotator 1", DASH)
          + key_item(1812 - 160, Y4 + 42, REF2, "annotator 2", DASH))
TWf, THf = 220, 297
gw = (1784 - 28 - 2 * 14) / 3
ex = [("Cells", "Cellpose on predicted PECAM-1 vs outlines on acquired PECAM-1", "data3/B_PECAM_acquired.png",
       [("data3/B_annotator1_contours.json", "annotator 1 (vector)", REF, DASH), ("data3/B_annotator2_contours.json", "annotator 2 (vector)", REF2, DASH),
        ("data3/B_cells_contours.json", "Cellpose on predicted PECAM (vector)", MODEL, None)],
       [("between annotators", 0.897, "#8a94a3"), ("vs annotator 1", 0.781, F1C), ("vs annotator 2", 0.746, F1C)], "F1"),
      ("Nuclei", "StarDist on predicted DAPI vs manual nuclei", "data3/B_DAPI_acquired_nuclei_tile.png",
       [("data3/B_nuclei_manual_contours.json", "manual nuclei (vector)", REF, DASH), ("data3/B_nuclei_stardist_contours.json", "StarDist on predicted DAPI (vector)", MODEL, None)],
       [("vs manual nuclei", 0.828, F1C)], "F1"),
      ("Intensity", "predicted vs acquired, per pixel", "data5/split_intensity.png", [],
       [("DAPI", 0.891, RC), ("PECAM-1", 0.243, RC)], "Pearson r")]
for k_, (name, sub_, png, layers, bars_, metric) in enumerate(ex):
    gx = 28 + 14 + k_ * (gw + 14)
    ff.append(rrect(gx, Y4 + 66, gw, 330, 12, "#ffffff", cB["innerstroke"]))
    tx, ty = gx + 16, Y4 + 82
    if name == "Intensity":
        ff.append(split_widget_r(tx, ty, TWf, THf, png, "predicted", "acquired"))
    else:
        g = [real_image(tx, ty, TWf, THf, "data5/dark_tile.png", PX, 100, 20, f"f {name} (outlines only)")]
        for path, lbl, colr, dash in layers:
            g.append(vector_outlines_l(tx, ty, TWf, THf, path, lbl, colr, 1.6, dash))
        ff.append(group(f"f {name}", "".join(g)))
    bx = tx + TWf + 22
    ff.append(t(bx, ty + 22, name, 18, "bold", INK))
    ff.append(t(bx, ty + 44, sub_.split(" vs ")[0] if " vs " in sub_ else sub_, 13.5, fill=BODY))
    if " vs " in sub_:
        ff.append(t(bx, ty + 61, "vs " + sub_.split(" vs ")[1], 13.5, fill=BODY))
    ff.append(t(bx, ty + 100, metric, 14, "bold", INK))
    for i, (lbl, v, colr) in enumerate(bars_):
        ff.append(f1bar(bx, ty + 132 + i * 44, gw - TWf - 16 - 22 - 60, v, lbl, colr))
add(group("f good enough", "".join(ff)))

# ---------------------------------------------------------------- g: denoising and super-resolution
Y5 = Y4 + R4 + GAPR
R5 = 66 + 300 + 14
gg = [frame(28, Y5, 1784, R5, "f", "Denoising and super-resolution: check what the model changed", "B")]
DI = json.load(open("data/dn_intensity.json"))
SP = json.load(open("data/sr_profile.json"))
# g1 denoising
g1x, g1w = 42, 690
gg.append(rrect(g1x, Y5 + 66, g1w, 300, 12, "#ffffff", cB["innerstroke"]))
gg.append(t(g1x + 16, Y5 + 92, "Denoising: mask from the restored image, intensity from the acquired one", 15.5, "bold", INK))
DS = 186
for k_, (png, lbl) in enumerate([("data/dn_restored.png", "restored"), ("data/dn_acquired.png", "acquired")]):
    tx = g1x + 16 + k_ * (DS + 34)
    gg.append(group(f"g denoise {lbl}", real_image(tx, Y5 + 108, DS, DS, png, 0.6337, 200, 20, f"denoise {lbl}")
                    + vector_outlines_sub(tx, Y5 + 108, DS, DS, "data/dn_mask.json", "nuclei from restored image (vector)", MODEL, 1.4, None, (0, 0, 200, 200))
                    + halo(tx + 6, Y5 + 124, lbl)))
    gg.append(t(tx + DS / 2, Y5 + 108 + DS + 22, ["mask from here" if k_ == 0 else "measure here"], 14, "bold", INK, "middle"))
gg.append(arrow(g1x + 16 + DS + 5, Y5 + 108 + DS / 2, g1x + 16 + DS + 29, Y5 + 108 + DS / 2, cB["accent"]))
# scatter: per-nucleus mean intensity, background subtracted
sx0, sy0, sw_, sh2 = g1x + 16 + 2 * (DS + 34) + 34, Y5 + 108, g1w - (16 + 2 * (DS + 34) + 34) - 16, DS
a_ = np.array(DI["acquired"]) - DI["bg_acquired"]
d_ = np.array(DI["restored"]) - DI["bg_restored"]
mx = float(np.percentile(np.r_[a_, d_], 99.5)) * 1.1          # axis to the 99.5th percentile; the few brighter nuclei are clipped
pts = "".join(f'<circle cx="{sx0+sw_*u/mx:.1f}" cy="{sy0+sh2-sh2*v/mx:.1f}" r="2.2" fill="{cB["accent"]}" fill-opacity="0.55"/>'
              for u, v in zip(a_, d_) if 0 < u < mx and 0 < v < mx)
gg.append(group("g denoise intensity scatter",
                f'<line x1="{sx0}" y1="{sy0+sh2}" x2="{sx0+sw_}" y2="{sy0+sh2}" stroke="{INK}" stroke-width="1.4"/>'
                f'<line x1="{sx0}" y1="{sy0}" x2="{sx0}" y2="{sy0+sh2}" stroke="{INK}" stroke-width="1.4"/>'
                f'<line x1="{sx0}" y1="{sy0+sh2}" x2="{sx0+sw_}" y2="{sy0+sh2-sh2*sw_/sw_}" stroke="#8a94a3" stroke-width="1.4" stroke-dasharray="5 4"/>'
                + pts
                + t(sx0 + sw_ / 2, sy0 + sh2 + 22, "acquired intensity", 13.5, fill=BODY, anchor="middle")
                + f'<text x="{sx0-12}" y="{sy0+sh2/2}" font-size="13.5" fill="{BODY}" text-anchor="middle" transform="rotate(-90 {sx0-12} {sy0+sh2/2})">restored intensity</text>'
                + t(sx0 + sw_, sy0 + sh2 - 66, f"r = {DI['r']:.2f}", 14, "bold", INK, "end")
                + t(sx0 + sw_, sy0 + sh2 - 46, f"×{DI['ratio_median']:.2f} vs acquired", 14, "bold", INK, "end")
                + t(sx0 + sw_, sy0 + sh2 - 28, "median ratio, background-", 12, fill=BODY, anchor="end")
                + t(sx0 + sw_, sy0 + sh2 - 14, "subtracted", 12, fill=BODY, anchor="end")
                + t(sx0 + sw_ - 14, sy0 + 14, "y = x", 12.5, fill="#6b7686", anchor="end")))
# g2 super-resolution
SQ = json.load(open("data/squirrel.json"))
g2x = g1x + g1w + 14
g2w = 1798 - g2x
gg.append(rrect(g2x, Y5 + 66, g2w, 300, 12, "#ffffff", cB["innerstroke"]))
gg.append(t(g2x + 16, Y5 + 92, "Super-resolution: check against the diffraction-limited input and, where possible, higher-resolution data", 15.5, "bold", INK))
SS = 162
rowy = SP["row"] / 140
tiles_ = [("data/sr_input.png", "low-res input", True), ("data/sr_predicted.png", "predicted", True),
          ("data/sr_squirrel.png", "SQUIRREL error map", False), ("data/sr_hr.png", "acquired high-res", True)]
for k_, (png, lbl, line) in enumerate(tiles_):
    tx = g2x + 16 + k_ * (SS + 10) + (12 if k_ == 3 else 0)
    gg.append(group(f"g sr {lbl}", real_image(tx, Y5 + 108, SS, SS, png, 0.0626, 140, 2, f"sr {lbl}")
                    + (f'<line x1="{tx}" y1="{Y5+108+SS*rowy:.1f}" x2="{tx+SS}" y2="{Y5+108+SS*rowy:.1f}" stroke="#ffd23f" stroke-width="1.6" stroke-dasharray="4 3"/>' if line else "")))
    gg.append(t(tx + SS / 2, Y5 + 108 + SS + 20, lbl, 14, "bold", INK, "middle"))
mx_ = g2x + 16 + 2 * (SS + 10)
gg.append(t(mx_ + SS / 2, Y5 + 108 + SS + 42, f"RSP vs input: predicted {SQ['predicted']['RSP']:.2f}", 13, fill=INK, anchor="middle")
          + t(mx_ + SS / 2, Y5 + 108 + SS + 60, f"acquired high-res {SQ['high_res']['RSP']:.2f}", 13, fill=INK, anchor="middle"))
gg.append(f'<line x1="{mx_+SS+11}" y1="{Y5+104}" x2="{mx_+SS+11}" y2="{Y5+108+SS+64}" stroke="{cB["tintstroke"]}" stroke-width="1.4" stroke-dasharray="5 4"/>')
px0, py0 = g2x + 16 + 4 * (SS + 10) + 12 + 22, Y5 + 116
pw_, ph_ = g2x + g2w - 20 - px0, 152
gg.append(f'<line x1="{px0}" y1="{py0+ph_}" x2="{px0+pw_}" y2="{py0+ph_}" stroke="{INK}" stroke-width="1.4"/>')
for key, colr, sw, dash in [("low_res", "#9aa4b2", 1.8, "4 3"), ("high_res", INK, 2.0, None), ("predicted", MODEL, 2.0, None)]:
    v = SP[key]
    pl = " ".join(f"{px0+pw_*i/(len(v)-1):.1f},{py0+ph_-ph_*q:.1f}" for i, q in enumerate(v))
    gg.append(f'<polyline points="{pl}" fill="none" stroke="{colr}" stroke-width="{sw}"' + (f' stroke-dasharray="{dash}"' if dash else "") + "/>")
gg.append(t(px0 + pw_ / 2, py0 + ph_ + 20, "intensity along the dashed line", 13, fill=BODY, anchor="middle"))
gg.append(key_item(px0, py0 + ph_ + 48, INK, "high-res") + key_item(px0 + 96, py0 + ph_ + 48, MODEL, "predicted")
          + key_item(px0 + 206, py0 + ph_ + 48, "#9aa4b2", "low-res", "4 3"))
add(group("g denoising and super-resolution", "".join(gg)))

H = Y5 + R5 + 20
svg = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
       f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" xmlns:xlink="http://www.w3.org/1999/xlink" '
       f'width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">\n'
       f'<defs>{"".join(defs)}</defs>\n<rect width="{W}" height="{H}" fill="#ffffff"/>\n'
       + "\n".join(out) + "\n</svg>\n")
open("fig2.svg", "w", encoding="utf-8").write(svg)
print("written", len(svg) // 1024, "KB; height", H)
