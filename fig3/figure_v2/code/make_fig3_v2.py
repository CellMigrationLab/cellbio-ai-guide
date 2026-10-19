"""Figure 3 (protocol v2) in the layout of Figures 1 and 2: editable SVG built from the stored main runs.

Reads fig3/v2/runs/*/score.json (see build_scores_v2 below), writes source_data/fig_scores_v2.json first, then draws.
Row b is the Python script only (the Fiji test was dropped). Rows b and c: the model works on a mosaic of the left halves
of fields 104 and 209; bars and circles show the mean of the F1 on the held-out right halves of the two fields (the
images in the header are the whole development field 104). Row d: whole fields. Re-run after every scenario: `make fig3v2` (cwd fig3/figure_v2/source_data).
Row a (illustration) and the red call-outs are round-1 wording until the v2 item tables and the full results are reviewed.
"""
import csv
import os
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


# ======================================================================= FIGURE 3 v9: three tasks; scores + counts per row; minimal text
import os as _os
A3 = "../../figure/source_data/round1/fig_assets/"
RUNS = "../../v2/runs/"
TASK_IDS = ("nuclei", "cancer", "endo")
REF_209 = {}


def build_scores_v2():
    """Collect per-task lists from the stored v2 runs. Rows b and c: the mean of the F1 on the held-out right halves of
    fields 104 and 209 (a failed field counts 0; both failed = -1, drawn as x). Row d: count / manual count, both fields."""
    with open("../../v2/scenarios.csv", newline="") as f:
        sc = {r["scenario_id"]: r for r in csv.DictReader(f)}
    tasks = {k: {"py": {"before": [], "after": [], "before_n": [], "after_n": [], "before_shape": [], "after_shape": []},
                 "agent": {"before": [], "after": [], "before_n": [], "after_n": [], "before_shape": [], "after_shape": []},
                 "draw": {"f1": [], "drawn": [], "asked": [], "area_ratio": [], "ar_ratio": [],
                          "count_by_field": {"104": [], "209": []}, "manual_by_field": {}}, "default": None}
             for k in TASK_IDS}
    n_runs = 0
    n_ref = {k: 0 for k in TASK_IDS}
    for sid, r in sc.items():
        sp = _os.path.join(RUNS, sid, "score.json")
        if not _os.path.exists(sp):
            continue
        n_runs += 1
        d, task = json.load(open(sp)), r["task"]
        T = tasks[task]
        if r["row"] in ("code", "optimise"):
            fields = [d["f104"], d["f209"]]
            ok = [f["status"] == "ok" for f in fields]
            blk = T["py"] if r["row"] == "code" else T["agent"]
            side = "before" if r["condition"] in ("simple", "by_eye") else "after"
            blk[side].append(d["mean"]["f1"] if any(ok) else -1)
            blk[side + "_n"].append(sum(f["n_pred"] for f in fields) if all(ok) else None)
            if all(ok):
                n_ref[task] = sum(f["n_ref"] for f in fields)
                # shape accuracy on matched held-out objects: mean over the two fields of the median |errors|
                a_err = [f["median_abs_area_error_pct"] for f in fields]
                r_err = [f["median_abs_aspect_ratio_error"] for f in fields]
                blk[side + "_shape"].append([sum(a_err) / 2, sum(r_err) / 2] if None not in a_err + r_err else None)
        elif r["row"] == "direct":
            ok = d["turn3"]["status"] == "ok"
            ref = d["reference"]["count"]
            T["draw"]["f1"].append(d["turn3"]["f1"] if ok else None)
            T["draw"]["drawn"].append(d["turn3"]["n_drawn"] / ref if ok else None)
            T["draw"]["asked"].append(d["turn1"]["count"] / ref if d["turn1"]["count"] is not None else None)
            T["draw"]["manual_by_field"][str(d["field"])] = ref
            if d["turn1"]["count"] is not None:
                T["draw"]["count_by_field"][str(d["field"])].append(d["turn1"]["count"])
            t2, rs = d["turn2"], d["reference"]
            if t2["turn2_median_area_um2"] is not None and rs["median_area_um2"]:
                T["draw"]["area_ratio"].append(t2["turn2_median_area_um2"] / rs["median_area_um2"])
                T["draw"]["ar_ratio"].append(t2["turn2_median_aspect_ratio"] / rs["median_aspect_ratio"])
    return {"tasks": tasks, "n_runs": n_runs, "n_ref_heldout": n_ref}


BOX1_ONLY = os.environ.get("BOX1_ONLY") == "1"   # row b: Box 1 only (simple vs Box 1 goes to the supplement)
FSJ = build_scores_v2()
json.dump(FSJ, open("fig_scores_v2.json", "w"), indent=1)
FS = FSJ["tasks"]
from fig3.scoring.tasks import heldout_reference   # manual annotation, held-out right halves (data/raw)
import numpy as _np
MAN = {k: sum(int(len(_np.unique(heldout_reference(k, f))) - 1) for f in (104, 209)) for k in TASK_IDS}
MAN104 = {"nuclei": 441, "cancer": 124, "endo": 382}
DEFC = "#9aa4b2"
CAVF, CAVS = "#fdf0ef", "#efc2be"
CHG = "#6b2c87"
OKT = "#1a7a4c"
BEFC = "#b7c0e3"
TASK_TEXT = {"nuclei": ["Task: segment and count the endothelial nuclei", "(not the cancer cells' nuclei); area and aspect ratio of each"],
             "cancer": ["Task: segment and count the cancer cells;", "area and aspect ratio of each"],
             "endo": ["Task: segment and count the endothelial cells (whole", "cells, outlined at the junctions); area and aspect ratio of each"]}
TASKS = [("nuclei", "Nuclei", "DAPI"), ("cancer", "Cancer cells", "brightfield"), ("endo", "Endothelial cells", "brightfield")]


def med(v):
    v = [max(x, 0) for x in v if x is not None]
    return float(np.median(v)) if len(v) else None


def medn(v):
    v = [x for x in v if x is not None]
    return int(np.median(v)) if len(v) else None


def img(x, y, w, h, png, label):
    cid = clip(x, y, w, h, 3)
    data = base64.b64encode(open(png, "rb").read()).decode()
    return (f'<g inkscape:label="{label}"><g clip-path="url(#{cid})"><image x="{x}" y="{y}" width="{w}" height="{h}" '
            f'preserveAspectRatio="none" xlink:href="data:image/png;base64,{data}"/></g></g>')


def change_pill(cx, cy, lines, w=96):
    h = 16 + 15 * len(lines)
    return (f'<path d="M{cx-w/2},{cy-h/2} h{w-12} l12,{h/2} l-12,{h/2} h-{w-12} z" fill="{CHG}"/>'
            + t(cx - 4, cy - h / 2 + 20, lines, 12, "bold", "#ffffff", "middle", lh=15))


# ---------------------------------------------------------------- grid
Y0 = 20
LW_ = 64
RX = 28 + LW_ + 10
RW = 1812 - RX
CX_ASK, W_ASK = RX + 18, 344
CX_SC = CX_ASK + W_ASK + 28
GW, GG = 288, 18
CX_CAV = CX_SC + 3 * GW + 2 * GG + 24
W_CAV = 1812 - 14 - CX_CAV
GAP = 10


def shape_text(runs):
    """'area err 18 % · AR err 0.16' = median over runs of the mean (two fields) median |error| of matched objects."""
    v = [r for r in runs if r]
    if not v:
        return ""
    return f"area err {np.median([r[0] for r in v]):.0f}% · AR err {np.median([r[1] for r in v]):.2f}"


def group(x, y, task, b, a, bn, an, lb, la, manual=None, shapes=([], [])):
    """Two bars (median F1 of runs; open circles = runs; x = crashed) + median object count vs manual."""
    bw = GW - 150
    g = []
    d = FS[task]["default"]
    manual = manual or MAN[task]
    conds = [(lb, b, bn, BEFC), (la, a, an, F1C)]
    if lb is None:                      # one condition only (Box 1)
        conds, shapes = conds[1:], shapes[1:]
    for i, (lbl, vals, ns, col) in enumerate(conds):
        yy = y + i * 30
        g.append(t(x, yy + 9, lbl, 12.5, "bold" if i else "normal", INK if i else BODY))
        bx = x + 58
        g.append(f'<rect x="{bx}" y="{yy}" width="{bw}" height="11" rx="3" fill="#eef1f5"/>')
        m = med(vals)
        if m is None:
            g.append(t(bx + bw + 6, yy + 10, "…", 13, "bold", "#7a8699"))
            continue
        g.append(f'<rect x="{bx}" y="{yy}" width="{bw*m:.1f}" height="11" rx="3" fill="{col}"/>'
                 + t(bx + bw + 6, yy + 10, f"{m:.2f}", 13, "bold", INK))
        if len(vals) > 1:
            for v in vals:
                if v is None:
                    continue
                if v < 0:
                    g.append(f'<path d="M{bx-4:.1f},{yy+1.5} l8,8 M{bx+4:.1f},{yy+1.5} l-8,8" stroke="{NOC}" stroke-width="2"/>')
                else:
                    g.append(f'<circle cx="{bx+bw*v:.1f}" cy="{yy+5.5}" r="3.2" fill="#ffffff" stroke="{INK}" stroke-width="1.2"/>')
        n = medn(ns)
        if n is not None:
            g.append(t(bx + bw + 40, yy + 10, f"n={n}", 12, fill="#5b6676"))
    for i, (runs, lbl) in enumerate(zip(shapes, [c[0] for c in conds])):
        txt = shape_text(runs)
        if txt:
            g.append(t(x, y + 66 + i * 15, f"{lbl}: {txt}", 11.5, fill="#5b6676"))
    if d is not None:
        ax = x + 58 + bw * d
        g.append(f'<line x1="{ax:.1f}" y1="{y-6}" x2="{ax:.1f}" y2="{y+46}" stroke="{DEFC}" stroke-width="2" stroke-dasharray="3 2"/>')
    return "".join(g)


def panel(key, y, sub, lb, la, half=False):
    g = []
    for i, (task, name, _) in enumerate(TASKS):
        x = CX_SC + i * (GW + GG)
        r = FS[task][sub]
        manual = FSJ.get("manual_half", {}).get(task) if half else None
        g.append(t(x, y, f"{name}", 13.5, "bold", INK) + t(x + GW - 6, y, f"manual n={manual or MAN[task]}", 11.5, fill="#5b6676", anchor="end")
                 + group(x, y + 14, task, r["before"], r["after"], r.get("before_n", [None]), r.get("after_n", [None]), lb, la, manual,
                                                                     (r.get("before_shape", []), r.get("after_shape", []))))
    return "".join(g)


# ---------------------------------------------------------------- task row: original image + desired result (full field)
TT = 232
HDH = TT + 98
add(group_svg := None) if False else None
row = [rrect(RX, Y0, RW, HDH, 14, "#ffffff", NN["stroke"], 1.3)]
for i, (task, name, mod) in enumerate(TASKS):
    x = RX + 20 + i * (2 * TT + 8 + 48)
    src = A3 + ("dapi_full.png" if task == "nuclei" else "bf_full.png")
    row.append(t(x, Y0 + 30, f"{name}", 17, "bold", INK) + t(x + 2 * TT + 8, Y0 + 30, f"{mod} · FOV 1 · manual n = {MAN104[task]}", 13, fill=BODY, anchor="end"))
    row.append(img(x, Y0 + 44, TT, TT, src, f"{task} image") + img(x + TT + 8, Y0 + 44, TT, TT, A3 + f"labels_{task}.png", f"{task} manual labels"))
    row.append(t(x, Y0 + 44 + TT + 22, TASK_TEXT[task], 13, "bold", INK, lh=17))
    row.append(halo(x + 6, Y0 + 62, "image", size=12.5) + halo(x + TT + 14, Y0 + 62, "desired result (manual)", size=12.5))
add("".join(row))

ORDER = [("a", "Ask for advice", 156), ("b", "Ask for code: Python script", 134),
         ("c", "Let an agent run it", 134), ("d", "Ask for the answer", 164)]
ry, RH = {}, {}
yy = Y0 + HDH + GAP
for key, ttl, h in ORDER:
    ry[key], RH[key] = yy, h
    yy += h + GAP
for key, ttl, h in ORDER:
    y = ry[key]
    add(rrect(RX, y, RW, h, 16, NN["bg"], NN["stroke"], 1.4)
        + f'<circle cx="{CX_ASK+15}" cy="{y+24}" r="15" fill="{ACC}"/>' + t(CX_ASK + 15, y + 30, key[0], 17, "bold", "#fff", "middle")
        + t(CX_ASK + 40, y + 30, ttl, 17, "bold", INK)
        + rrect(CX_CAV - 8, y + 9, W_CAV + 14, h - 18, 12, CAVF, CAVS, 1.2))


def cav(key, lines, dy=0):
    y = ry[key] + dy
    return caution(CX_CAV + 14, y + 38, NOC) + t(CX_CAV + 36, y + 44, lines, 16.5, "bold", NOC, lh=21)


def ask(key, items, y0=42):
    y = ry[key] + y0
    for tg, lines in items:
        if tg:
            add(t(CX_ASK + 46, y + 2, tg, 11.5, "bold", CHG)); y += 5
        s, h = prompt(CX_ASK, y, W_ASK, lines, 12); add(s); y += h - 6


# ================================================================ a
key = "a"
ask(key, [("before", ["“Which tool, model and settings would you", "recommend? I don't need code.”"]),
          ("after", ["“…check the current documentation first.”"])])
y = ry[key] + 40
WB = 300
s, hA = reply(CX_SC, y, WB, ["“…Cellpose-SAM (Cellpose 4) or cyto3.”", "“…try the cyto3 denoise models.”"], 12.5, False, "From memory"); add(s)
add(t(CX_SC + 4, y + hA + 4, "models removed in Cellpose 4", 12.5, "bold", NOC))
add(change_pill(CX_SC + WB + 48, y + 34, ["read the", "docs"]))
XD = CX_SC + WB + 104
s, hB = reply(XD, y, CX_CAV - 30 - XD, ["“The docs list … cpsam_v2, cpdino …", "The old cyto3 and nuclei models are", "not mentioned in the current docs.”"], 12.5, False, "After reading the docs"); add(s)
add(t(XD + 4, y + hB + 4, "current models", 12.5, "bold", OKT))
add(cav(key, ["Outdated advice runs without error"], -8))
s, _ = terminal(CX_CAV + 14, ry[key] + 62, W_CAV - 16, [(">>> CellposeModel(pretrained_model='cyto3')", "#d5dbe5"),
                                                       ("(no message)  → loads cpsam_v2", "#ff8a80")], 12.5); add(s)

# ================================================================ b1 / b2 / c / d
key = "b"
ask(key, [("", ["“Please write a Python script to segment the …”", "+ ask for explicit, testable code"])] if BOX1_ONLY else
    [("before", ["“Please write a Python script to segment the …”"]), ("after", ["Box 1 prompt"])])
add(panel(key, ry[key] + 34, "py", None if BOX1_ONLY else "generic", "script" if BOX1_ONLY else "Box 1"))
add(cav(key, ["Writing code doesn't guarantee it runs:", "ask for code that is easier to debug"]) if BOX1_ONLY else
    cav(key, ["Box 1 makes the settings visible;", "only the test shows if they work"]))
add(t(CX_CAV + 36, ry[key] + 88, ["The code differs between runs, but each script", "gives the same result every time it is run."], 11.5, "normal", "#5b6270", lh=15))

key = "c"
ask(key, [("before", ["“…run the pipeline, assess, improve…”"]), ("after", ["“…score every version against my annotation…”"])])
add(panel(key, ry[key] + 34, "agent", "by eye", "scored"))
add(cav(key, ["By eye it had no score to check;", "give agents an external objective"]))
key = "d"
ask(key, [("before", ["“How many … are in this image?”"]), ("after", ["“Draw around every … and count them.”"])])
y = ry[key] + 34
for i, (task, name, _) in enumerate(TASKS):
    x = CX_SC + i * (GW + GG)
    dd = FS[task]["draw"]
    bw = GW - 20
    gg = [t(x, y, name, 13.5, "bold", INK)]
    for j, fld in enumerate(("104", "209")):
        man = dd["manual_by_field"].get(fld)
        vals = dd["count_by_field"][fld]
        if man is None:
            continue
        yy = y + 34 + j * 40
        top = int(np.ceil(max([1.6 * man] + vals) / 100.0) * 100)   # axis from 0 to a round number >= 1.6 x manual
        X = lambda v, top=top: x + 40 + v / top * (bw - 40)
        gg.append(t(x, yy + 4, {"104": "FOV 1", "209": "FOV 2"}[fld], 11.5, fill=BODY))
        gg.append(f'<line x1="{X(0):.1f}" y1="{yy}" x2="{X(top):.1f}" y2="{yy}" stroke="#c9d1dc" stroke-width="1.2"/>')
        for tick in (0, top):
            gg.append(f'<line x1="{X(tick):.1f}" y1="{yy-3}" x2="{X(tick):.1f}" y2="{yy+3}" stroke="#9aa4b2" stroke-width="1"/>')
            gg.append(t(X(tick), yy + 17, str(tick), 10.5, fill="#7a8699", anchor="middle"))
        gg.append(f'<line x1="{X(man):.1f}" y1="{yy-10}" x2="{X(man):.1f}" y2="{yy+10}" stroke="{INK}" stroke-width="2" stroke-dasharray="3 2"/>')
        gg.append(t(X(man), yy - 13, str(man), 10.5, "bold", INK, anchor="middle"))
        placed = []                                           # dots that would overlap are spread vertically
        for v in sorted(vals):
            k = sum(abs(X(v) - px) < 9 for px in placed)
            placed.append(X(v))
            dy = [0, -6, 6, -12, 12][min(k, 4)]
            gg.append(f'<circle cx="{X(v):.1f}" cy="{yy + dy}" r="4.5" fill="{MCOL["sonnet"]}" stroke="#fff" stroke-width="1"/>')
    add("".join(gg))
add(f'<circle cx="{CX_SC+6}" cy="{ry[key]+RH[key]-18}" r="4.5" fill="{MCOL["sonnet"]}"/>' + t(CX_SC + 16, ry[key] + RH[key] - 14, "one run", 12, fill=BODY)
    + f'<line x1="{CX_SC+80}" y1="{ry[key]+RH[key]-23}" x2="{CX_SC+80}" y2="{ry[key]+RH[key]-11}" stroke="{INK}" stroke-width="2" stroke-dasharray="3 2"/>' + t(CX_SC + 90, ry[key] + RH[key] - 14, "manual count", 12, fill=BODY))
add(cav(key, ["Estimated, not counted: not reproducible,", "asking again gives different numbers"]))

# ---------------------------------------------------------------- key line under task row: F1 legend
add(t(CX_SC, ry["b"] - 2, "", 1))

# ================================================================ delegation arrow
AT, AB = ry["a"], ry["d"] + RH["d"]
defs.append(f'<linearGradient id="deleg" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#d9cbea"/><stop offset="1" stop-color="{ACC}"/></linearGradient>')
AXc = 28 + LW_ / 2
add(f'<path d="M{AXc-20},{AT} H{AXc+20} V{AB-26} H{AXc+30} L{AXc},{AB} L{AXc-30},{AB-26} H{AXc-20} Z" fill="url(#deleg)"/>'
    + f'<text x="{AXc+6}" y="{(AT+AB)/2}" font-size="15" font-weight="bold" fill="#ffffff" text-anchor="middle" '
      f'transform="rotate(-90 {AXc+6} {(AT+AB)/2})">more of the analysis happens inside the LLM interaction</text>')

# ================================================================ what to keep
KY = ry["d"] + RH["d"] + GAP
KH = 92
add(rrect(28, KY, 1784, KH, 16, "#ffffff", NN["stroke"], 1.4)
    + t(48, KY + 28, "Regardless of the level of delegation, test on representative images with reference outputs", 16.5, "bold", INK))
KEEP = [("lock", "Check how the service handles data"), ("check", "Verify advice against the docs"),
        ("ruler", "Ask for code that is easy to debug" if BOX1_ONLY else "Ask it to expose parameters (Box 1)"), ("target", "Give agents an external objective"),
        ("file", "Request masks, not only a number")]
KW = (1784 - 40) / 5


def kicon(name, cx, cy, col):
    st_ = f'fill="none" stroke="{col}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"'
    if name == "lock":
        return f'<rect x="{cx-13}" y="{cy-4}" width="26" height="21" rx="3" {st_}/><path d="M{cx-8},{cy-4} v-6 a8,8 0 0 1 16,0 v6" {st_}/>'
    if name == "check":
        return f'<rect x="{cx-14}" y="{cy-17}" width="28" height="34" rx="3" {st_}/><path d="M{cx-7},{cy+1} l5,5 l10,-11" {st_}/>'
    if name == "ruler":
        return (f'<rect x="{cx-18}" y="{cy-8}" width="36" height="16" rx="2" {st_}/>'
                + "".join(f'<line x1="{cx-12+i*8}" y1="{cy-8}" x2="{cx-12+i*8}" y2="{cy-1-(3 if i%2==0 else 0)}" {st_}/>' for i in range(4)))
    if name == "target":
        return f'<circle cx="{cx}" cy="{cy}" r="16" {st_}/><circle cx="{cx}" cy="{cy}" r="9" {st_} stroke-dasharray="3 2.5"/><circle cx="{cx}" cy="{cy}" r="2.6" fill="{col}"/>'
    return (f'<path d="M{cx-13},{cy-17} H{cx+5} L{cx+13},{cy-9} V{cy+17} H{cx-13} Z" {st_}/>'
            f'<line x1="{cx-7}" y1="{cy-3}" x2="{cx+7}" y2="{cy-3}" {st_}/><line x1="{cx-7}" y1="{cy+5}" x2="{cx+7}" y2="{cy+5}" {st_}/>')


for i, (ic, a_) in enumerate(KEEP):
    x = 48 + i * KW
    add(kicon(ic, x + 20, KY + 62, ACC) + t(x + 48, KY + 67, a_, 14.5, "bold", INK))

add(t(1812 - 14, KY + KH + 18, f"DRAFT: {FSJ['n_runs']} of 72 main runs scored. Rows b, c: bar = median of the runs' mean F1 on the held-out halves of FOV 1 and FOV 2 (open circles: runs; x: failed). Images above: FOV 1.",
      12, fill="#7a8699", anchor="end"))
H = KY + KH + 34
svg = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
       f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" xmlns:xlink="http://www.w3.org/1999/xlink" '
       f'width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">\n'
       f'<defs>{"".join(defs)}</defs>\n<rect width="{W}" height="{H}" fill="#ffffff"/>\n'
       + "\n".join(out) + "\n</svg>\n")
open("../output/fig3_v2_box1only.svg" if BOX1_ONLY else "../output/fig3_v2.svg", "w", encoding="utf-8").write(svg)
print("written", len(svg) // 1024, "KB; height", H)
