"""Generate Fig. 1 ("Where AI can enter a microscopy image-analysis workflow") as an editable SVG.

Everything is plain SVG: text stays as <text>, panels are named groups (Inkscape layers/labels),
microscopy thumbnails are procedurally drawn vector placeholders (seeded, so reproducible).
"""
import math
import base64
import json
import os
import random
from xml.sax.saxutils import escape

W, H = 1648, 2334
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


for col in ["#1f6fc5", "#2f9a43", "#d6336c", "#4a5568", "#1f4e8c"]:  # noqa
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
F1C, RC = "#4c5fa8", "#d08a1f"                  # one colour per metric, shared by rows B and C
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


def score_row(x1, ry, tiles, bars_, bx, bw=150, gap=36, metric=None):
    """One example row of a score card: image tile(s) with outlines, then bars (grey = benchmark, colour = this field)."""
    g = []
    for tl in tiles:
        g.append(tl)
    for i, (lbl, v, colr, txt) in enumerate(bars_):
        g.append(bar(bx, ry + 16 + i * gap, bw, v, colr, lbl, txt))
    if metric:                            # metric named once per bar graph, as a 0-1 axis under the bars
        ya = ry + 16 + len(bars_) * gap - 12
        g.append(f'<line x1="{bx}" y1="{ya}" x2="{bx+bw}" y2="{ya}" stroke="{BODY}" stroke-width="1"/>'
                 + "".join(f'<line x1="{bx+bw*v:.1f}" y1="{ya}" x2="{bx+bw*v:.1f}" y2="{ya+4}" stroke="{BODY}" stroke-width="1"/>'
                           + t(bx + bw * v, ya + 15, f"{v:g}", 11.5, fill=BODY, anchor="middle") for v in (0, 1))
                 + t(bx + bw / 2, ya + 15, metric, 12.5, "bold", INK, "middle"))
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


# ---------------------------------------------------------------- panel A: deep-learning applications

# ================================================================ Fig. 1 v11: A (DL examples, left) | B (LLM uses, right) ; C full row
YO = 20
CT = YO + HH
WS, GAP = 264, 10
M, FP = 10, 12                          # outer margin; padding inside a panel frame
WA = 3 * WS + 2 * GAP + 2 * FP          # panel A: three examples across
PADX = 0
NN = C["N"]



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


def pending(x, y, what):
    return (rrect(x, y, WS, WS, 9, "#ffffff", "#9aa5b4", 1.5, ' stroke-dasharray="6 4"')
            + t(x + WS / 2, y + WS / 2 - 4, what, 13, "bold", "#7d8796", "middle")
            + t(x + WS / 2, y + WS / 2 + 14, "(data to come)", 12, fill="#7d8796", anchor="middle"))


def code_widget(x, y, lines):
    g = [rrect(x, y, WS, WS, 9, "#1f2532", "none"),
         "".join(f'<circle cx="{x+12+i*11}" cy="{y+11}" r="3.2" fill="{c}"/>' for i, c in enumerate(["#ff5f57", "#febc2e", "#28c840"]))]
    pal = {"kw": "#ff7ab8", "fn": "#7cc4ff", "tx": "#e6e9ef", "cm": "#8a94a3", "hd": "#ffc94d"}
    for k_, segs in enumerate(lines):
        xx = x + 13
        spans = "".join(f'<tspan fill="{pal[c]}">{escape(tx)}</tspan>' for c, tx in segs)
        g.append(f'<text x="{xx}" y="{y + 30 + k_ * 15.5}" font-size="10" xml:space="preserve" {MONO}>{spans}</text>')
    return "".join(g)


def prompt_widget(x, y, text_lines):
    return (rrect(x, y, WS, WS, 9, "#ffffff", C["C"]["tintstroke"], 1.5)
            + rrect(x + 10, y + 28, WS - 20, 98, 12, C["C"]["tint"], "none")
            + f'<path d="M{x+24},{y+126} l0,12 l12,-12 z" fill="{C["C"]["tint"]}"/>'
            + t(x + 20, y + 52, text_lines, 14, fill=INK, lh=18))


um_bf = PX                     # brightfield px size
DET_COLS = ["#3b8cff", "#2fd65a", "#ff4646"]       # YOLOv2 classes: rod, dividing, microcolony


def draw_widget(w, wx, wy):
    """Draw one row-A-style widget (uses the global widget size WS)."""
    g = []
    if w[0] == "classify":                # input field | per-class gallery of cells (rows = predicted class)
        g.append(split_widget(wx, wy, w[1], "input", "output", None))
        sb = 5 / (400 * 0.084) * WS           # 5 um on the input half (84 nm px; 400 px across the widget)
        g.append(f'<line x1="{wx+8}" y1="{wy+WS-9}" x2="{wx+8+sb:.1f}" y2="{wy+WS-9}" stroke="#ffffff" stroke-width="2.5"/>'
                 + halo(wx + 8 + sb / 2, wy + WS - 14, "5 µm", "middle", 12))
        for r_, nm in enumerate(w[2]):
            g.append(halo(wx + WS / 2 + 4, wy + (r_ + 1) * WS / 4 - 5, nm, "start", 10.5))
        g.append(f'<line x1="{wx+WS/2}" y1="{wy+WS/4*1}" x2="{wx+WS}" y2="{wy+WS/4*1}" stroke="#ffffff" stroke-width="0.8" opacity="0.6"/>'
                 f'<line x1="{wx+WS/2}" y1="{wy+WS/2}" x2="{wx+WS}" y2="{wy+WS/2}" stroke="#ffffff" stroke-width="0.8" opacity="0.6"/>'
                 f'<line x1="{wx+WS/2}" y1="{wy+WS*3/4}" x2="{wx+WS}" y2="{wy+WS*3/4}" stroke="#ffffff" stroke-width="0.8" opacity="0.6"/>')
        return "".join(g)
    if w[0] == "detect":                  # input | output split; predicted boxes drawn as vectors on the output half
        d = json.load(open(w[2]))
        k_ = WS / d["size"]
        cid_ = clip(wx + WS / 2, wy, WS / 2, WS, 0)
        rects = "".join(f'<rect x="{wx+x0*k_:.1f}" y="{wy+y0*k_:.1f}" width="{(x1-x0)*k_:.1f}" height="{(y1-y0)*k_:.1f}" '
                        f'stroke="{DET_COLS[c]}"/>' for x0, y0, x1, y1, cf, c in d["boxes"])
        g.append(split_widget(wx, wy, w[1], "input", "output", None))
        sb = 10 / (256 * 0.160) * WS          # 10 um; 160 nm px (16 um EMCCD pixel / 100x; DeepBacs methods)
        g.append(f'<line x1="{wx+8}" y1="{wy+WS-9}" x2="{wx+8+sb:.1f}" y2="{wy+WS-9}" stroke="#ffffff" stroke-width="2.5"/>'
                 + halo(wx + 8 + sb / 2, wy + WS - 14, "10 µm", "middle", 12))
        g.append(f'<g clip-path="url(#{cid_})" fill="none" stroke-width="1.8" inkscape:label="YOLOv2 predicted boxes (vector)">{rects}</g>')
        g.append(f'<line x1="{wx+WS/2}" y1="{wy}" x2="{wx+WS/2}" y2="{wy+WS}" stroke="#ffffff" stroke-width="2"/>')
        return "".join(g)
    kind = w[0]
    if kind == "split":
        g.append(split_widget(wx, wy, w[1], w[2], w[3], w[4]))
    elif kind == "pending":
        g.append(pending(wx, wy, w[1]))
    elif kind == "prompt":
        g.append(prompt_widget(wx, wy, w[1]))
    elif kind == "code":
        g.append(code_widget(wx, wy, w[1]))
    elif kind == "track":                 # TrackMate tracks redrawn as smoothed vector polylines
        cid_ = clip(wx, wy, WS, WS, 9)
        trs = json.load(open(w[1]))
        lines_ = "".join(f'<polyline points="' + " ".join(f"{wx+px*WS:.1f},{wy+py*WS:.1f}" for px, py in tr["pts"])
                         + f'" stroke="{tr["rgb"]}"/>' for tr in trs)
        g.append(f'<g clip-path="url(#{cid_})"><rect x="{wx}" y="{wy}" width="{WS}" height="{WS}" fill="#ffffff"/>'
                 f'<g fill="none" stroke-width="0.9" stroke-linejoin="round" stroke-linecap="round" opacity="0.9" '
                 f'inkscape:label="tracks (TrackMate, smoothed, vector)">{lines_}</g></g>'
                 + rrect(wx, wy, WS, WS, 9, "none", "#9aa5b4", 1.2))
    elif kind == "img":
        g.append(split_widget(wx, wy, w[1], "", "", (20 / (480 * 0.158436) * WS, "20 µm")).replace(
            f'<line x1="{wx+WS/2}" y1="{wy}"', f'<line visibility="hidden" x1="{wx+WS/2}" y1="{wy}"').replace(
            f'<circle cx="{wx+WS/2}" cy="{wy+WS/2}" r="10"', f'<circle visibility="hidden" cx="{wx+WS/2}" cy="{wy+WS/2}" r="10"').replace(
            f'<path d="M{wx+WS/2-2}', f'<path visibility="hidden" d="M{wx+WS/2-2}'))
    return "".join(g)


LLM_WIDGETS = [("prompt", ["“we should use the", "image and segment", "it to show the", "equivalent labels”"], "Prompt"),
               ("code", [[("tx", "model = models."), ("fn", "Cellpose")],
                         [("fn", "  Model"), ("tx", "(gpu="), ("kw", "False"), ("tx", ")")],
                         [("hd", "# default Cellpose-SAM")],
                         [("hd", "# weights")],
                         [("tx", "masks, flows, styles = \\")],
                         [("tx", "  model."), ("fn", "eval"), ("tx", "(region)")],
                         [("hd", "# raw uint16 in; Cellpose")],
                         [("hd", "# normalises internally")],
                         [("hd", "# (default percentiles)")]], "Code"),
               ("img", "panel_a/llm_qc.png", "Check output")]

NN = C["N"]


def card(x, y, w, h, title, key="N"):
    k = C[key]
    return rrect(x, y, w, h, 12, k["bg"], k["stroke"], 1.8) + t(x + w / 2, y + 27, title, 18, "bold", k["accent"], "middle")


def row_frame(y, h, L, title, key="N"):
    k = C[key]
    return (rrect(M, y, W - 2 * M, h, 16, NN["bg"], NN["stroke"], 1.4)
            + f'<circle cx="{M+42}" cy="{y+38}" r="22" fill="{NN["accent"]}"/>' + t(M + 42, y + 47, L.lower(), 25, "bold", "#fff", "middle")
            + t(M + 78, y + 46, title, 24, "bold", INK))


def ico(name, cx, cy, col):
    st_ = f'fill="none" stroke="{col}" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"'
    if name == "advise":
        return (f'<path d="M{cx-24},{cy-16} h48 a6,6 0 0 1 6,6 v22 a6,6 0 0 1 -6,6 h-30 l-12,10 v-10 h-6 a6,6 0 0 1 -6,-6 v-22 a6,6 0 0 1 6,-6 z" {st_}/>'
                f'<line x1="{cx-14}" y1="{cy-4}" x2="{cx+14}" y2="{cy-4}" {st_}/><line x1="{cx-14}" y1="{cy+6}" x2="{cx+6}" y2="{cy+6}" {st_}/>')
    if name == "code":
        return (f'<path d="M{cx-12},{cy-14} L{cx-26},{cy} L{cx-12},{cy+14}" {st_}/><path d="M{cx+12},{cy-14} L{cx+26},{cy} L{cx+12},{cy+14}" {st_}/>'
                f'<path d="M{cx+5},{cy-18} L{cx-5},{cy+18}" {st_}/>')
    if name == "run":
        return (f'<path d="M{cx+18},{cy-6} A20,20 0 1 0 {cx+14},{cy+12}" {st_}/>'
                f'<path d="M{cx+20},{cy-18} L{cx+19},{cy-5} L{cx+7},{cy-7}" {st_}/>'
                f'<path d="M{cx-6},{cy-8} L{cx+8},{cy} L{cx-6},{cy+8} Z" fill="{col}"/>')
    if name == "answer":
        return (f'<rect x="{cx-26}" y="{cy-16}" width="30" height="26" rx="3" {st_}/>'
                f'<path d="M{cx-22},{cy+6} L{cx-15},{cy-3} L{cx-9},{cy+2} L{cx-5},{cy-2} L{cx},{cy+6} Z" fill="{col}"/>'
                f'<path d="M{cx+8},{cy-8} h18 a4,4 0 0 1 4,4 v10 a4,4 0 0 1 -4,4 h-8 l-6,6 v-6 h-4 a4,4 0 0 1 -4,-4 v-10 a4,4 0 0 1 4,-4 z" {st_}/>')
    return ""




def frame(x, y, w, h, L, title):
    return (rrect(x, y, w, h, 16, NN["bg"], NN["stroke"], 1.4)
            + f'<circle cx="{x+42}" cy="{y+38}" r="22" fill="{NN["accent"]}"/>' + t(x + 42, y + 47, L.lower(), 25, "bold", "#fff", "middle")
            + t(x + 78, y + 46, title, 24, "bold", INK))


# ---------------- A: six examples, two stacked groups of three
cards_o = [
    ("A", "Turn images into measurements",
     [("detect", "panel_a/detect_input.png", "panel_a/detect_boxes.json", "Detection"),
      ("split", "panel_a/split_cells.png", "input", "output", (50 / (210 * um_bf) * WS, "50 µm"), "Segmentation"),
      ("classify", "panel_a/split_classif.png", ["Control", "Mecillinam", "Nalidixate", "Rifampicin"], "Classification")]),
    ("B", "Predict image content",
     [("split", "panel_a/split_denoise.png", "input", "output", (20 / (200 * 0.6337) * WS, "20 µm"), "Denoising"),
      ("split", "panel_a/split_label.png", "input", "output", (50 / (210 * um_bf) * WS, "50 µm"), "Artificial labelling"),
      ("split", "panel_a/split_sr_zoom.png", "input", "output", (1 / (140 * 0.0313) * WS, "1 µm"), "Super-resolution")]),
]
GH = 34 + WS + 30                      # group height
HTOP = 66 + 2 * GH + 14
a = [frame(M, YO, WA, HTOP, "A", "Deep-learning examples")]
for gi, (key, ttl, widgets) in enumerate(cards_o):
    k = C[key]
    gx, gy = M + FP, YO + 66 + gi * GH
    a.append(t(gx + (WA - 2 * FP) / 2, gy + 18, ttl, 17, "bold", k["accent"], "middle")
             + f'<line x1="{gx+PADX}" y1="{gy+27}" x2="{gx+WA-2*FP-PADX}" y2="{gy+27}" stroke="{k["accent"]}" stroke-width="2"/>')
    for j, w in enumerate(widgets):
        wx, wy = gx + PADX + j * (WS + GAP), gy + 34
        a.append(draw_widget(w, wx, wy))
        a.append(t(wx + WS / 2, wy + WS + 21, w[-1], 14.5, "bold", INK, "middle"))
add(group("Panel A deep-learning examples", "".join(a)))

# ---------------- B: four ways to use an LLM, with context (2 x 2)
xB = M + WA + 4
WB = W - M - xB
k = C["C"]
b = [frame(xB, YO, WB, HTOP, "B", "Four ways to use an LLM")]
# compact tree: LLM / agent -> four uses; below, what each produces
kc = k["accent"]
bx0 = xB + 14
bw0 = WB - 28
# 2 x 2 grid: one card per use, each with an example prompt and the kind of reply it returns
MONO = ' font-family="DejaVu Sans Mono, Menlo, Consolas, monospace"' 
uses = [("advise", "Ask for advice", "software, parameters, approaches",
         ["Which tools can segment touching nuclei", "in 2D fluorescence images, and which", "parameters matter most?"],
         ("text", ["StarDist or Cellpose; check the", "probability threshold and object size."])),
        ("code", "Ask for code", "e.g. Python, Fiji macro",
         ["Write a Python script that segments", "nuclei and measures their area in µm².", "Do not silently resize or normalise."],
         ("mono", ["labels = segment(img)", "area_um2 = area_px * px_um**2"])),
        ("run", "Let an agent run it", "runs and optimises the workflow",
         ["Optimise the nuclei segmentation on", "the training folder and report the F1.", "Do not open the held-out folder."],
         ("mono", ["run 1: F1 = 0.62", "run 4: F1 = 0.81, saved"])),
        ("answer", "Ask for the answer", "multimodal model, direct answer",
         ["How many nuclei are", "in this image?"],
         ("runs", ["7 nuclei", "8 nuclei", "7 nuclei"]))]
G2 = 12
gx_, gy_ = xB + 10, YO + 70
cw2 = (WB - 20 - G2) / 2
ch2 = (YO + HTOP - 12 - gy_ - G2) / 2
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
    bx_ = x0 + 12
    if nm == "answer":
        IA = min(ch2 - 76 - 16, 0.4 * cw2)
        g.append(real_image(bx_, y0 + 74 + (ch2 - 90 - IA) / 2, IA, IA, "panel_b/panelA_acquired_crop.png", 0.158436, 600, 20, "attached image"))
        bx_ += IA + 16
    bw_ = x0 + cw2 - 12 - bx_
    ph = 26 + 21 * len(prm)
    py0 = y0 + 74
    g.append(bubble(bx_, py0, bw_, ph, "#ffffff", kc, "br"))
    g.append(t(bx_ + 16, py0 + 26, ["“" + prm[0]] + prm[1:-1] + [prm[-1] + "”"] if len(prm) > 1 else ["“" + prm[0] + "”"], 15.5, fill=INK, lh=21))
    ry0 = py0 + ph + 24
    rh = ch2 - (ry0 - y0) - 16
    rx0 = bx_ + 34
    g.append(f'<g inkscape:label="LLM icon">{petal(bx_ + 14, ry0 + 20, 0.62, kc)}</g>')
    g.append(bubble(rx0, ry0, x0 + cw2 - 12 - rx0, rh, "#ffffff", k["tintstroke"], "bl"))
    yy = ry0 + rh / 2 - 10.5 * (len(rep) - 1) + 5
    if rk == "runs":                      # same question asked three times
        g.append(t(rx0 + 16, ry0 + 24, "asked 3 times:", 12.5, "bold", "#6b2c87"))
        g.append(t(rx0 + 16, ry0 + 48, ["run 1: “" + rep[0] + "”", "run 2: “" + rep[1] + "”", "run 3: “" + rep[2] + "”"], 15, fill=INK, lh=21))
    elif rk == "mono":
        g.append(t(rx0 + 16, yy, rep, 14, fill=INK, lh=21, extra=MONO))
    else:
        g.append(t(rx0 + 16, yy, ["“" + rep[0]] + rep[1:-1] + [rep[-1] + "”"] if len(rep) > 1 else ["“" + rep[0] + "”"], 15.5, fill=INK, lh=21))
    b.append(group(f"LLM use {q+1}", "".join(g)))
add(group("Panel B LLM uses", "".join(b)))


Y2 = YO + HTOP - 10       # row C positioned from here (row C code adds its own +10 gap via Y3)
HB = 0
def slice_sub(w, h, pw=240, ph=260):
    """Crop window (in source px) that preserveAspectRatio='xMidYMid slice' shows for a pw x ph image in a w x h box."""
    if pw / ph < w / h:          # image taller than box: full width, centred vertically
        vh = pw * h / w
        return (0, (ph - vh) / 2, pw, vh)
    vw = ph * w / h
    return ((pw - vw) / 2, 0, vw, ph)


# ---------------- row C: start an image-analysis project (follows "Starting an image analysis project")
Y3 = YO + HTOP + 6
CT3_PAD = 16
HCR = 66 + 304 + 10
cC_ = [row_frame(Y3, HCR, "C", "Start an image-analysis project")]
CT3 = Y3 + 66 + CT3_PAD
IS = 236
steps = 5
REL = [1, 1, 2, 1, 1]
SG = 22                                          # gap between steps
SW_ = (W - 2 * (M + 14) - (steps - 1) * SG) / sum(REL)
TITLES = ["Define the measurement", "Build a reference test set", "Compare candidate approaches and optimise",
          "Final check on fresh images", "Track the cells"]
SUBS = ["from the biological question", "representative variation; annotations\nare references, not ground truth",
        "not good enough? find the failure first (channels, object scale, context,\npre- and post-processing), then adjust or fine-tune; F1 scores missed and extra cells",
        "not used to choose or tune; e.g.\nan independent repeat or day", "biological effect larger than\nthe analysis error"]
XS = [M + 14 + sum(REL[:q]) * SW_ + q * SG for q in range(steps)]
for i in range(steps):
    sx = XS[i]
    sw_i = SW_ * REL[i]
    cx = sx + sw_i / 2
    tw_ = len(TITLES[i]) * 7.9                     # approximate title width (Arial bold 14.5)
    nx_ = cx - (tw_ + 30) / 2 + 12
    cC_.append(f'<circle cx="{nx_:.1f}" cy="{CT3+2}" r="12" fill="{NN["accent"]}"/>' + t(nx_, CT3 + 7, str(i + 1), 13, "bold", "#ffffff", "middle"))
    cC_.append(t(nx_ + 20, CT3 + 7, TITLES[i], 14.5, "bold", INK))
    iy = CT3 + 30
    ix = cx - IS / 2
    if i == 0:   # scientist with microscope + question
        sc = 0.78
        pers = (f'<circle cx="92" cy="1094" r="17" fill="#f2c9a5"/>'
                f'<path d="M74,1090 C72,1068 108,1064 112,1086 C104,1078 88,1076 74,1090 Z" fill="#3b2a20"/>'
                f'<path d="M58,1186 C58,1140 74,1118 96,1116 C120,1116 132,1140 134,1186 Z" fill="#cfe0f3" stroke="#7aa6d6" stroke-width="2"/>'
                f'<path d="M110,1132 L150,1150" stroke="#cfe0f3" stroke-width="12" stroke-linecap="round"/>'
                f'<g fill="none" stroke="{INK}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">'
                f'<path d="M168,1186 H212"/><path d="M196,1186 C206,1176 210,1160 200,1144"/>'
                f'<path d="M182,1170 H206"/><path d="M178,1110 L194,1148"/><circle cx="196" cy="1150" r="5"/>'
                f'<path d="M188,1186 V1172"/></g>')
        cC_.append(f'<g transform="translate({ix-14:.1f} {iy+IS:.1f}) scale(0.95) translate(-58 -1186)" inkscape:label="scientist + microscope">{pers}</g>')
        bx, by, bw, bh = ix + 64, iy - 4, 180, 128
        cC_.append(rrect(bx, by, bw, bh, 12, "#ffffff", "#9fb3cc", 1.8)
                   + f'<path d="M{bx+8},{by+bh-14} L{bx-14},{by+bh+10} L{bx+26},{by+bh} Z" fill="#ffffff" stroke="#9fb3cc" stroke-width="1.8" stroke-linejoin="round"/>'
                   + f'<rect x="{bx+4}" y="{by+bh-18}" width="26" height="16" fill="#ffffff"/>'
                   + t(bx + 14, by + 24, ["Can we segment the", "cancer cells in these", "brightfield images so", "that we can track them?"], 14, fill=INK, lh=17.5)
                   + t(bx + 14, by + 110, "Measure: cell tracks", 13, "bold", INK))
    elif i == 1:  # reference test set: several representative fields, annotated
        for k_, rp in enumerate((2, 1, 0)):         # rep0 (annotated) drawn on top
            xx, yy = ix - 6 + k_ * 16, iy + k_ * 14
            cC_.append(real_image(xx, yy, IS - 30, IS - 30, f"panel_c_steps2_4/rep{rp}.png", PX * 260 / 300, 300, 50, f"reference field {k_}", "#111111")
                       .replace('stroke="#111111" stroke-width="2.5"', 'stroke="none" stroke-width="0"').replace('fill="#111111" text-anchor', 'fill="none" text-anchor'))
            cC_.append(rrect(xx, yy, IS - 30, IS - 30, 2, "none", "#ffffff", 1.4))
        top = (ix + 20, iy + 24, IS - 30, IS - 30)
        cC_.append(vector_outlines_sub(ix + 26, iy + 28, IS - 30, IS - 30, "panel_c_step3/B_rep_ref.json", "manual reference (vector)", REF, 1.4, DASH, (0, 0, 260, 260)))
    elif i == 2:  # three candidates on the same reference test set (real outputs), optimisation loop
        SC_ = json.load(open("panel_c_step3/A_scores.json"))
        hw = 166
        gap3 = 6
        x0_ = cx - (3 * hw + 2 * gap3) / 2
        for k_, (cj, lab, v) in enumerate([("panel_c_steps2_4/rep_classical.json", "Threshold", SC_["classical"]),
                                           ("panel_c_step3/B_rep_cellpose.json", "Pre-trained generalist", SC_["cellpose"]),
                                           ("panel_c_step3/B_rep_stardist.json", "Custom-trained", SC_["stardist"])]):
            xx = x0_ + k_ * (hw + gap3)
            hh = hw * 0.92
            cC_.append(real_image(xx, iy, hw, hh, "panel_c_step3/B_rep_bf.png", PX, 240, 50, f"candidate {lab}", "#111111")
                       .replace('stroke="#111111" stroke-width="2.5"', 'stroke="none" stroke-width="0"').replace('fill="#111111" text-anchor', 'fill="none" text-anchor'))
            sb_ = slice_sub(hw, hh)
            cC_.append(vector_outlines_sub(xx, iy, hw, hh, "panel_c_step3/B_rep_ref.json", "reference (vector)", REF, 1.2, DASH, sb_))
            cC_.append(vector_outlines_sub(xx, iy, hw, hh, cj, f"{lab} (vector)", MODEL, 1.2, None, sb_))
            cC_.append(t(xx + hw / 2, iy + hh + 18, lab, 13.5, "bold", INK, "middle"))
            cC_.append(f'<rect x="{xx+10}" y="{iy+hh+26}" width="{hw-56}" height="10" rx="3" fill="#e4e8ee"/>'
                       f'<rect x="{xx+10}" y="{iy+hh+26}" width="{(hw-56)*v:.1f}" height="10" rx="3" fill="{F1C}"/>'
                       + t(xx + hw - 40, iy + hh + 35, f"{v:.2f}", 12.5, "bold", INK))
        cC_.append(key_item(x0_ + 4, iy + hh + 66, MODEL, "candidate") + key_item(x0_ + 128, iy + hh + 66, REF, "manual annotation", DASH)
                   + t(x0_ + 3 * hw + 2 * gap3, iy + hh + 71, "bars: F1 score", 12.5, fill=BODY, anchor="end"))

    elif i == 99:  # (merged into step 3)
        lp = (f'<path d="M{cx+38},{iy+92} A40,40 0 1 1 {cx+30},{iy+56}" fill="none" stroke="{INK}" stroke-width="2.6" '
              f'marker-end="url(#ah-4a5568)"/>'
              f'<circle cx="{cx-6}" cy="{iy+80}" r="13" fill="none" stroke="{INK}" stroke-width="2.6"/>'
              f'<line x1="{cx+3}" y1="{iy+89}" x2="{cx+14}" y2="{iy+100}" stroke="{INK}" stroke-width="3" stroke-linecap="round"/>')
        cC_.append(group("find the failure (loop)", lp))
        cC_.append(t(cx, iy + 158, ["channels · object scale · context", "pre- and post-processing"], 12.5, fill=INK, anchor="middle", lh=16))
    elif i == 3:  # final check on fresh images
        cC_.append(real_image(ix, iy, IS, IS * 260 / 240 * 0.92, "panel_c_step4/test_bf.png", PX, 240, 50, "fresh image", "#111111"))
        sb_ = slice_sub(IS, IS * 260 / 240 * 0.92)
        cC_.append(vector_outlines_sub(ix, iy, IS, IS * 260 / 240 * 0.92, "panel_c_step4/test_ref.json", "reference (vector)", REF, 1.4, DASH, sb_))
        cC_.append(vector_outlines_sub(ix, iy, IS, IS * 260 / 240 * 0.92, "panel_c_step4/test_stardist.json", "model (vector)", MODEL, 1.4, None, sb_))
        cC_.append(halo(ix + 6, iy + 16, "unseen image"))
    elif i == 4:  # final result: cells tracked over time (TrackMate capture: brightfield, spots and tracks)
        cC_.append(real_image(ix, iy, IS, IS, "panel_c_step5/trackmate_crop.png", 1.31483, 280, 100, "tracked cells (TrackMate)", "#ffffff"))
    if i < steps - 1:
        cC_.append(arrow(sx + sw_i + 2, iy + IS / 2, sx + sw_i + SG - 2, iy + IS / 2, "#4a5568", 2.4))
add(group("Panel C start a project", "".join(cC_)))
H = Y3 + HCR + 14
svg = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
       f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" xmlns:xlink="http://www.w3.org/1999/xlink" '
       f'width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">\n'
       f'<defs>{"".join(defs)}</defs>\n<rect width="{W}" height="{H}" fill="#ffffff"/>\n'
       + "\n".join(out) + "\n</svg>\n")
open("../figure/fig1.svg", "w", encoding="utf-8").write(svg)
print("written", len(svg) // 1024, "KB; height", H)
