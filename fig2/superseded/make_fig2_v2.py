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

# ---------------------------------------------------------------- a: when a pre-trained model performs poorly (four checks)
FTW = 196                                 # fine-tune box width
GW = (1784 - 28 - FTW - 3 * 26) / 3      # width of one check group
BW = 200                                  # bar column width
TW = GW - BW - 14
TH = TW * SEGH / SEGW
R1 = round(66 + 64 + TH + 26 + 14)
bb = [frame(28, YO, 1784, R1, "a", "When a pre-trained model performs poorly, find the mismatch first", "A")]
bb.append(key_item(1812 - 250, YO + 42, MODEL, "model") + key_item(1812 - 150, YO + 42, REF, "reference", DASH))
ty0 = YO + 66 + 64
DEFC = "#9aa4b2"                          # default settings: grey baseline bar in every group


def minibars(x, y, w, items, hl):
    g = [t(x, y, "F1", 13.5, "bold", INK)]
    for i, (lbl, v, is_def) in enumerate(items):
        yy = y + 22 + i * 37
        g.append(t(x, yy, lbl, 13.5, "bold" if lbl == hl else "normal", INK if lbl == hl else BODY))
        if v is None:
            g.append(t(x, yy + 17, "running…", 13, "bold", "#7a8699"))
            continue
        g.append(f'<rect x="{x}" y="{yy+6}" width="{w-44}" height="9" rx="3" fill="#e4e8ee"/>'
                 f'<rect x="{x}" y="{yy+6}" width="{(w-44)*v:.1f}" height="9" rx="3" fill="{DEFC if is_def else F1C}"/>'
                 + t(x + w - 38, yy + 15, f"{v:.2f}", 13.5, "bold", INK))
    return "".join(g)


def step_tile(x, key, label):
    if PS.get(key) is None:
        return (rrect(x, ty0, TW, TH, 4, "#e9edf2", "#c8d3e0", 1.2, ' stroke-dasharray="6 4"')
                + t(x + TW / 2, ty0 + TH / 2, "running…", 15, "bold", "#7a8699", "middle"))
    return tile(x, ty0, TW, TH, "data4/B_rep_bf.png",
                [("data4/B_rep_ref.json", "reference (vector)", REF, DASH), (f"data/ts_cp_{key}.json", f"{label} (vector)", MODEL, None)],
                f"tile {label}")


def header(x, n, ttl, sub):
    return (f'<circle cx="{x+11}" cy="{YO+88}" r="11" fill="{cA["accent"]}"/>' + t(x + 11, YO + 93, str(n), 13, "bold", "#fff", "middle")
            + t(x + 28, YO + 93, ttl, 16.5, "bold", INK) + t(x, YO + 114, sub, 13.5, fill=BODY))


D = PS["default"]
groups = [(1, "Check the normalisation", "tile: forgot to normalise", "nonorm", "forgot to normalise",
           [("forgot to normalise", PS["nonorm"], False), ("percentile (default)", D, True), ("min–max", PS.get("file_minmax"), False),
            ("histogram equalisation", PS.get("file_histeq"), False), ("CLAHE", PS.get("file_clahe"), False)]),
          (2, "Check the object scale", "tile: input downsampled 4×", "down4", "downsampled 4×",
           [("downsampled 4×", PS["down4"], False), ("downsampled 2×", PS["down2"], False), ("native (default)", D, True),
            ("upsampled 2×", PS.get("up2"), False)]),
          (3, "Check the post-processing", "is it segmenting the intended object?", "postfilter", "low-contrast objects removed",
           [("default", D, True), ("stricter probability threshold", PS["cellprob2"], False), ("looser flow threshold", PS.get("flow0.8"), False),
            ("low-contrast objects removed", PS["postfilter"], False)])]
x = 42
for n, ttl, sub, key, hl, items in groups:
    if n > 1:
        bb.append(f'<line x1="{x-13}" y1="{YO+78}" x2="{x-13}" y2="{YO+R1-18}" stroke="{NN["tintstroke"]}" stroke-width="1.2"/>')
    bb.append(header(x, n, ttl, sub) + step_tile(x, key, hl) + minibars(x + TW + 14, ty0 + 4, BW, items, hl))
    x += GW + 26
# 4: fine-tune (schematic)
x5 = 1798 - FTW
bb.append(rrect(x5, YO + 70, FTW, R1 - 70 - 14, 12, cA["tint"], cA["tintstroke"], 1.3))
bb.append(f'<circle cx="{x5+22}" cy="{YO+92}" r="11" fill="{cA["accent"]}"/>' + t(x5 + 22, YO + 97, "4", 13, "bold", "#fff", "middle")
          + t(x5 + 40, YO + 97, "If nothing works,", 16, "bold", INK) + t(x5 + 40, YO + 116, "fine-tune", 16, "bold", INK))
cy5 = ty0 + TH / 2 + 8
bb.append(t(x5 + FTW / 2, ty0 + 8, ["only for a systematic", "failure"], 13.5, fill=BODY, anchor="middle", lh=17))
bb.append(group("fine-tune loop (schematic)",
                f'<circle cx="{x5+FTW/2}" cy="{cy5}" r="50" fill="none" stroke="{cA["accent"]}" stroke-width="2.4" stroke-dasharray="6 5"/>'
                + t(x5 + FTW / 2, cy5 - 60, "correct", 13.5, "bold", INK, "middle")
                + t(x5 + FTW / 2, cy5 + 72, "retrain", 13.5, "bold", INK, "middle")
                + unet2(x5 + FTW / 2, cy5, cA["accent"])))
bb.append(t(x5 + FTW / 2, cy5 + 100, ["correct diverse predictions", "where it fails"], 13, fill=BODY, anchor="middle", lh=16))
add(group("a troubleshooting", "".join(bb)))
# ---------------------------------------------------------------- b: is it good enough?
Y2 = YO + R1 + GAPR
R2 = 66 + 360 + 14
cc = [frame(28, Y2, 1784, R2, "b", "Is it good enough? Check the errors that matter for the measurement", "A")]
# measurement -> error that matters
x0, w0 = 44, 420
cc.append(rrect(x0, Y2 + 66, w0, 360, 12, "#ffffff", cA["innerstroke"]))
cc.append(box_title(x0 + w0 / 2, Y2 + 96, "What will you measure?"))
MEAS = [("Counts", "missed and false objects"), ("Morphology", "boundaries of matched cells"),
        ("Phenotypes", "misclassified objects"), ("Tracks", "merges and splits break links")]
POS = [(x0 + w0 * 0.25, Y2 + 176), (x0 + w0 * 0.75, Y2 + 176), (x0 + w0 * 0.25, Y2 + 330), (x0 + w0 * 0.75, Y2 + 330)]
a = []
CT = 0
exec(open("measure_icons_block.py").read())
cc += a
cc.append(arrow(x0 + w0 + 4, Y2 + 246, x0 + w0 + 22, Y2 + 246, cA["accent"]))
# two tiles with error markers
ES = json.load(open("data/error_summary.json"))
EM = json.load(open("data/err_markers.json"))
x1 = x0 + w0 + 26
w1 = 1796 - x1
cc.append(rrect(x1, Y2 + 66, w1, 360, 12, "#ffffff", cA["innerstroke"]))
ETW = 276
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

# ---------------------------------------------------------------- c: denoising   |   d: artificial labelling
Y3 = Y2 + R2 + GAPR
R3 = 66 + 380 + 14
WC = 640
xd = 28 + WC + 6
WD = 1812 - xd
gg = [frame(28, Y3, WC, R3, "c", "Denoising", "B")]
DI = json.load(open("data/dn_intensity.json"))
gg.append(t(44, Y3 + 92, ["Derive the mask from the restored image;", "measure intensity in the acquired image"], 15.5, "bold", INK, lh=19))
DS = 196
for k_, (png, lbl, cap) in enumerate([("data/dn_restored.png", "restored", "mask from here"), ("data/dn_acquired.png", "acquired", "measure here")]):
    tx = 44 + k_ * (DS + 32)
    gg.append(group(f"c denoise {lbl}", real_image(tx, Y3 + 128, DS, DS, png, 0.6337, 200, 20, f"denoise {lbl}")
                    + vector_outlines_sub(tx, Y3 + 128, DS, DS, "data/dn_mask.json", "nuclei from restored image (vector)", MODEL, 1.4, None, (0, 0, 200, 200))
                    + halo(tx + 6, Y3 + 144, lbl)))
    gg.append(t(tx + DS / 2, Y3 + 128 + DS + 22, cap, 14, "bold", INK, "middle"))
gg.append(arrow(44 + DS + 4, Y3 + 128 + DS / 2, 44 + DS + 28, Y3 + 128 + DS / 2, cB["accent"]))
sx0, sy0 = 44 + 2 * (DS + 32) + 28, Y3 + 128
sw_ = 28 + WC - 16 - sx0
sh2 = DS
a_ = np.array(DI["acquired"]) - DI["bg_acquired"]
d_ = np.array(DI["restored"]) - DI["bg_restored"]
mx = float(np.percentile(np.r_[a_, d_], 99.5)) * 1.1
pts = "".join(f'<circle cx="{sx0+sw_*u/mx:.1f}" cy="{sy0+sh2-sh2*v/mx:.1f}" r="2" fill="{cB["accent"]}" fill-opacity="0.55"/>'
              for u, v in zip(a_, d_) if 0 < u < mx and 0 < v < mx)
gg.append(group("c denoise intensity scatter",
                f'<line x1="{sx0}" y1="{sy0+sh2}" x2="{sx0+sw_}" y2="{sy0+sh2}" stroke="{INK}" stroke-width="1.4"/>'
                f'<line x1="{sx0}" y1="{sy0}" x2="{sx0}" y2="{sy0+sh2}" stroke="{INK}" stroke-width="1.4"/>'
                f'<line x1="{sx0}" y1="{sy0+sh2}" x2="{sx0+sw_}" y2="{sy0+sh2-sh2*sw_/sw_}" stroke="#8a94a3" stroke-width="1.4" stroke-dasharray="5 4"/>'
                + pts
                + t(sx0 + sw_ / 2, sy0 + sh2 + 22, "acquired", 13.5, fill=BODY, anchor="middle")
                + f'<text x="{sx0-10}" y="{sy0+sh2/2}" font-size="13.5" fill="{BODY}" text-anchor="middle" transform="rotate(-90 {sx0-10} {sy0+sh2/2})">restored</text>'
                + t(sx0 + sw_, sy0 + sh2 - 30, f"r = {DI['r']:.2f}", 13.5, "bold", INK, "end")
                + t(sx0 + sw_, sy0 + sh2 - 12, f"×{DI['ratio_median']:.2f}", 13.5, "bold", INK, "end")
                + t(sx0 + sw_ - 6, sy0 + 14, "y = x", 12, fill="#6b7686", anchor="end")))
gg.append(t(sx0 + sw_ / 2, Y3 + 128 + DS + 44, "per-nucleus intensity", 12.5, fill=BODY, anchor="middle"))
add(group("c denoising", "".join(gg)))

# d: artificial labelling
dd = [frame(xd, Y3, WD, R3, "d", "Artificial labelling", "B")]
dd.append(key_item(xd + WD - 470, Y3 + 42, MODEL, "on predicted image") + key_item(xd + WD - 290, Y3 + 42, REF, "manual outlines 1", DASH)
          + key_item(xd + WD - 140, Y3 + 42, REF2, "outlines 2", DASH))
# input / predicted pair
PSZ = 150
px_ = xd + 16
for k_, (png, lbl, sub) in enumerate([("data/al_bf.png", "brightfield", "input"), ("data/al_pred.png", "predicted", "pix2pix: DAPI + PECAM-1")]):
    yy = Y3 + 76 + k_ * (PSZ + 36)
    dd.append(real_image(px_, yy, PSZ, PSZ, png, PX, 210, 50, f"d {lbl}", "#ffffff" if k_ else "#111111") + halo(px_ + 6, yy + 16, lbl))
    dd.append(t(px_ + PSZ / 2, yy + PSZ + 18, sub, 13, fill=BODY, anchor="middle"))
dd.append(arrow(px_ + PSZ / 2, Y3 + 76 + PSZ + 22, px_ + PSZ / 2, Y3 + 76 + PSZ + 34, cB["accent"], 2.4))
TWd, THd = 168, 210
gx1 = px_ + PSZ + 20
grp = [("ok", "An intermediate step", "validate the downstream output", [
            ("Cells", "data3/B_PECAM_acquired.png",
             [("data3/B_annotator1_contours.json", "manual outlines 1 (vector)", REF, DASH), ("data3/B_annotator2_contours.json", "manual outlines 2 (vector)", REF2, DASH),
              ("data3/B_cells_contours.json", "Cellpose on predicted PECAM (vector)", MODEL, None)],
             "F1", [("outlines 1 vs 2", 0.897, "#8a94a3"), ("vs outlines 1", 0.781, F1C), ("vs outlines 2", 0.746, F1C)]),
            ("Nuclei", "data3/B_DAPI_acquired_nuclei_tile.png",
             [("data3/B_nuclei_manual_contours.json", "manual nuclei (vector)", REF, DASH), ("data3/B_nuclei_stardist_contours.json", "StarDist on predicted DAPI (vector)", MODEL, None)],
             "F1", [("vs manual nuclei", 0.828, F1C)])]),
       ("caution", "The measurement itself", "compare with acquired fluorescence", [
            ("Intensity", "data5/split_intensity.png", None, "Pearson r, per pixel", [("DAPI", 0.891, RC), ("PECAM-1", 0.243, RC)])])]
gx = gx1
for kind, ttl, sub, items in grp:
    gw_ = len(items) * (TWd + 16) + 16
    if kind == "caution":
        gw_ = xd + WD - 14 - gx
    dd.append(rrect(gx, Y3 + 66, gw_, 380, 12, "#ffffff", cB["innerstroke"]))
    if kind == "ok":
        dd.append(check_badge(gx + 24, Y3 + 88, cB["accent"], 11).replace('stroke-width="4.5"', 'stroke-width="2.8"')
                  .replace(f'M{gx+14},{Y3+89} L{gx+21},{Y3+96} L{gx+35},{Y3+80}', f'M{gx+18.5},{Y3+88.5} L{gx+22.5},{Y3+92.5} L{gx+29.5},{Y3+83.5}'))
    else:
        dd.append(caution(gx + 24, Y3 + 87))
    dd.append(t(gx + 42, Y3 + 93, ttl, 16, "bold", INK) + t(gx + 42, Y3 + 112, sub, 13.5, fill=BODY))
    for j_, (name, png, layers, metric, bars_) in enumerate(items):
        tx = gx + 16 + j_ * (TWd + 16)
        ty = Y3 + 126
        if layers is None:
            dd.append(split_widget_r(tx, ty, TWd, THd, png, "predicted", "acquired"))
        else:
            g = [real_image(tx, ty, TWd, THd, "data5/dark_tile.png", PX, 100, 20, f"d {name} (outlines only)")]
            for path, lbl, colr, dash in layers:
                g.append(vector_outlines_l(tx, ty, TWd, THd, path, lbl, colr, 1.6, dash))
            dd.append(group(f"d {name}", "".join(g)))
        dd.append(t(tx, ty + THd + 20, f"{name} · {metric}", 13.5, "bold", INK))
        bw_ = (TWd - 40) if layers is not None else (gw_ - 32 - 40)
        for i, (lbl, v, colr) in enumerate(bars_):
            yy = ty + THd + 38 + i * 27
            dd.append(t(tx, yy, lbl, 12.5, fill=BODY) + f'<rect x="{tx}" y="{yy+5}" width="{bw_}" height="8" rx="3" fill="#e4e8ee"/>'
                      f'<rect x="{tx}" y="{yy+5}" width="{bw_*v:.1f}" height="8" rx="3" fill="{colr}"/>' + t(tx + bw_ + 5, yy + 13, f"{v:.2f}", 13, "bold", INK))
    gx += gw_ + 12
add(group("d artificial labelling", "".join(dd)))

# ---------------------------------------------------------------- e: super-resolution
Y5 = Y3 + R3 + GAPR
R5 = 66 + 290 + 14
ee = [frame(28, Y5, 1784, R5, "e", "Super-resolution: check against the input and, where possible, higher-resolution data", "B")]
SP = json.load(open("data/sr_profile.json"))
SQ = json.load(open("data/squirrel.json"))
TWS = json.load(open("data/tubule_width.json"))["summary"]
SS = 186
rowy = SP["row"] / 140
ee.append(rrect(42, Y5 + 66, 3 * (SS + 10) + 22, 290, 12, "#ffffff", cB["innerstroke"]))
ee.append(t(58, Y5 + 90, "Consistency with the diffraction-limited input (SQUIRREL)", 14.5, "bold", INK))
tiles_ = [("data/sr_input.png", "low-res input", True), ("data/sr_predicted.png", "predicted", True), ("data/sr_squirrel.png", "error map", False)]
for k_, (png, lbl, line) in enumerate(tiles_):
    tx = 58 + k_ * (SS + 10)
    ee.append(group(f"e sr {lbl}", real_image(tx, Y5 + 104, SS, SS, png, 0.0313, 140, 1, f"sr {lbl}")
                    + (f'<line x1="{tx}" y1="{Y5+104+SS*rowy:.1f}" x2="{tx+SS}" y2="{Y5+104+SS*rowy:.1f}" stroke="#ffd23f" stroke-width="1.6" stroke-dasharray="4 3"/>' if line else "")))
    ee.append(t(tx + SS / 2, Y5 + 104 + SS + 20, lbl, 14, "bold", INK, "middle"))
mx_ = 58 + 2 * (SS + 10)
ee.append(t(mx_ + SS / 2, Y5 + 104 + SS + 40, f"RSP: predicted {SQ['predicted']['RSP']:.2f} · reference {SQ['high_res']['RSP']:.2f}", 12.5, fill=INK, anchor="middle"))
x2 = 42 + 3 * (SS + 10) + 22 + 12
w2 = 1798 - x2
ee.append(rrect(x2, Y5 + 66, w2, 290, 12, "#ffffff", cB["innerstroke"]))
ee.append(t(x2 + 16, Y5 + 90, "Comparison with higher-resolution data: test the feature you will measure", 14.5, "bold", INK))
tx = x2 + 16
ee.append(group("e sr reference", real_image(tx, Y5 + 104, SS, SS, "data/sr_hr.png", 0.0313, 140, 1, "sr reference")
                + f'<line x1="{tx}" y1="{Y5+104+SS*rowy:.1f}" x2="{tx+SS}" y2="{Y5+104+SS*rowy:.1f}" stroke="#ffd23f" stroke-width="1.6" stroke-dasharray="4 3"/>'))
ee.append(t(tx + SS / 2, Y5 + 104 + SS + 20, "higher-res reference", 14, "bold", INK, "middle"))
# profile
px0, py0 = tx + SS + 30, Y5 + 112
pw_, ph_ = 330, 150
ee.append(f'<line x1="{px0}" y1="{py0+ph_}" x2="{px0+pw_}" y2="{py0+ph_}" stroke="{INK}" stroke-width="1.4"/>')
for key, colr, sw, dash in [("low_res", "#9aa4b2", 1.8, "4 3"), ("high_res", INK, 2.0, None), ("predicted", MODEL, 2.0, None)]:
    v = SP[key]
    pl = " ".join(f"{px0+pw_*i/(len(v)-1):.1f},{py0+ph_-ph_*q:.1f}" for i, q in enumerate(v))
    ee.append(f'<polyline points="{pl}" fill="none" stroke="{colr}" stroke-width="{sw}"' + (f' stroke-dasharray="{dash}"' if dash else "") + "/>")
ee.append(t(px0 + pw_ / 2, py0 + ph_ + 20, "intensity along the dashed line", 13, fill=BODY, anchor="middle"))
ee.append(key_item(px0, py0 + ph_ + 46, INK, "reference") + key_item(px0 + 110, py0 + ph_ + 46, MODEL, "predicted")
          + key_item(px0 + 222, py0 + ph_ + 46, "#9aa4b2", "low-res", "4 3"))
# tubule width: median and interquartile range
wx0 = px0 + pw_ + 50
ww = x2 + w2 - 24 - wx0
ee.append(t(wx0, Y5 + 120, f"Tubule width (FWHM, nm), {TWS['n_locations']} locations", 13.5, "bold", INK))
lo_, hi_ = 100, 400
for i, (key, lbl, colr) in enumerate([("low_res", "low-res input", "#9aa4b2"), ("predicted", "predicted", MODEL), ("reference", "reference", INK)]):
    yy = Y5 + 156 + i * 40
    q = TWS[key]
    X_ = lambda v: wx0 + 110 + (ww - 160) * (v - lo_) / (hi_ - lo_)
    ee.append(t(wx0, yy + 5, lbl, 13.5, fill=BODY)
              + f'<line x1="{X_(q["q25"]):.1f}" y1="{yy}" x2="{X_(q["q75"]):.1f}" y2="{yy}" stroke="{colr}" stroke-width="7" stroke-linecap="round" opacity="0.45"/>'
              + f'<circle cx="{X_(q["median_nm"]):.1f}" cy="{yy}" r="6" fill="{colr}"/>'
              + t(X_(hi_) + 10, yy + 5, f"{q['median_nm']:.0f}", 13.5, "bold", INK))
ax_y = Y5 + 156 + 3 * 40 - 14
ee.append(f'<line x1="{wx0+110}" y1="{ax_y}" x2="{wx0+110+ww-160}" y2="{ax_y}" stroke="{INK}" stroke-width="1.2"/>')
for v in (100, 200, 300, 400):
    xx = wx0 + 110 + (ww - 160) * (v - lo_) / (hi_ - lo_)
    ee.append(f'<line x1="{xx:.1f}" y1="{ax_y}" x2="{xx:.1f}" y2="{ax_y+5}" stroke="{INK}" stroke-width="1.2"/>' + t(xx, ax_y + 19, str(v), 12, fill=BODY, anchor="middle"))
ee.append(t(wx0, ax_y + 46, [f"predicted vs reference: differs by > 30 nm", f"at {TWS['abs_diff_gt_30nm_pct']:.0f}% of locations"], 13, fill=INK, lh=17))
add(group("e super-resolution", "".join(ee)))

H = Y5 + R5 + 20
svg = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
       f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" xmlns:xlink="http://www.w3.org/1999/xlink" '
       f'width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">\n'
       f'<defs>{"".join(defs)}</defs>\n<rect width="{W}" height="{H}" fill="#ffffff"/>\n'
       + "\n".join(out) + "\n</svg>\n")
open("fig2_v2.svg", "w", encoding="utf-8").write(svg)
print("written", len(svg) // 1024, "KB; height", H)
