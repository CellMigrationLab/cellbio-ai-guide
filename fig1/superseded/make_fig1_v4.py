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

W, H = 1840, 2334
AUDIT = os.environ.get("AUDIT", "1") == "1"  # audited wording is the default; AUDIT=0 restores the original


def V(orig, audited):
    """Original figure wording vs. wording tuned against the article text."""
    return audited if AUDIT else orig

FONT = "Arial, Helvetica, 'Liberation Sans', sans-serif"
INK = "#14223a"
BODY = "#2b3442"

C = {
    "A": dict(accent="#1f6fc5", bg="#e8f1fb", stroke="#bcd3ee", inner="#f7fbff", innerstroke="#cfe0f3",
              val="#d6e5f7", tint="#dbe9fa", tintstroke="#9cc2ea"),
    "B": dict(accent="#2f9a43", bg="#eaf6e8", stroke="#bfe0b9", inner="#f8fcf7", innerstroke="#cde8c8",
              val="#d8edd3", tint="#d9efd5", tintstroke="#93cc8b"),
    "N": dict(accent="#4a5568", bg="#f1f4f8", stroke="#c8d3e0", inner="#ffffff", innerstroke="#d5dde8",
              val="#e3e8ef", tint="#eef2f7", tintstroke="#c8d3e0"),
    "C": dict(accent="#d6336c", bg="#fceaf0", stroke="#f1c1d2", inner="#fff8fa", innerstroke="#f3cfdc",
              val="#f8d8e3", tint="#fde9f0", tintstroke="#f0b3c8"),
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
YO = 20
CT = YO + HH
WS, GAP, PADX = 232, 10, 14
RO = HH + 38 + WS + 36 + 12
o = [row(YO, RO, "N", "A", "Deep-learning applications", "")]



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
               ("img", "data5/llm_qc.png", "Check output")]

cards_o = [
    ("A", "Extract information",
     [("detect", "data5/detect_input.png", "data5/detect_boxes.json", "Detection"),
      ("split", "data5/split_cells.png", "input", "output", (50 / (210 * um_bf) * WS, "50 µm"), "Segmentation"),
      ("classify", "data5/split_classif.png", ["Control", "Mecillinam", "Nalidixate", "Rifampicin"], "Classification"),
      ("track", "data5/tracks_smoothed.json", "Tracking")]),
    ("B", "Predict image content",
     [("split", "data5/split_denoise.png", "input", "output", (20 / (200 * 0.6337) * WS, "20 µm"), "Denoising"),
      ("split", "data5/split_sr_zoom.png", "input", "output", (2 / (140 * 0.0626) * WS, "2 µm"), "Super-resolution"),
      ("split", "data5/split_label.png", "input", "output", (50 / (210 * um_bf) * WS, "50 µm"), "Artificial labelling")]),
]
x = 44
for i, (key, ttl, widgets) in enumerate(cards_o):
    k = C[key]
    n_ = len(widgets)
    CW = n_ * WS + (n_ - 1) * GAP + 2 * PADX     # card width follows its widget count
    g = [rrect(x, CT, CW, 38 + WS + 36, 12, k["bg"], k["stroke"], 1.8),
         t(x + CW / 2, CT + 27, ttl, 18, "bold", k["accent"], "middle")]
    for j, w in enumerate(widgets):
        wx, wy = x + PADX + j * (WS + GAP), CT + 38
        g.append(draw_widget(w, wx, wy))
        g.append(t(wx + WS / 2, wy + WS + 24, w[-1], 15, "bold", INK, "middle"))
    o.append(group(f"overview card {ttl}", "".join(g)))
    x += CW + 10
add(group("Panel A overview", "".join(o)))


# ================================================================ Fig. 1 v4: rows B-D
CT_COLS = {"siCTRL": "#3d74c6", "siCCT8#5": "#c96a28", "siCCT8#8": "#2a9d8f"}   # validated categorical palette
CT_NAME = {"siCTRL": "Control", "siCCT8#5": "Condition 1", "siCCT8#8": "Condition 2"}
CP = json.load(open("data7/cct8_plots.json"))
NN = C["N"]


def card(x, y, w, h, title, key="N"):
    k = C[key]
    return rrect(x, y, w, h, 12, k["bg"], k["stroke"], 1.8) + t(x + w / 2, y + 27, title, 18, "bold", k["accent"], "middle")


def letter(x, y, L, key="N"):
    return f'<circle cx="{x}" cy="{y}" r="20" fill="{C[key]["accent"]}"/>' + t(x, y + 8, L, 22, "bold", "#fff", "middle")


# ---------------- row 2: B (LLM) and C (start a project)
Y2 = YO + RO + 10
H2 = 38 + WS + 36
b2 = []
CWB = 3 * WS + 2 * GAP + 2 * PADX
CWB += 16
b2.append(card(28, Y2, CWB, H2, "Build or run the analysis (LLM)", "C"))
_badges = []
for j_, w_ in enumerate(LLM_WIDGETS):
    wx_, wy_ = 28 + PADX + 8 + j_ * (WS + GAP), Y2 + 38
    b2.append(draw_widget(w_, wx_, wy_))
    b2.append(t(wx_ + WS / 2, wy_ + WS + 24, w_[-1], 15, "bold", INK, "middle"))
    if j_ < 2:
        bx_, by_ = wx_ + WS + GAP / 2, wy_ + WS / 2
        _badges.append(f'<circle cx="{bx_}" cy="{by_}" r="9" fill="{C["C"]["accent"]}" stroke="#ffffff" stroke-width="2"/>'
                       f'<path d="M{bx_-3},{by_-4} L{bx_+2.5},{by_} L{bx_-3},{by_+4}" fill="none" stroke="#ffffff" stroke-width="2.2" '
                       f'stroke-linecap="round" stroke-linejoin="round"/>')
b2 += _badges
xC = 28 + CWB + 10
WC = 1812 - xC
c2 = [card(xC, Y2, WC, H2, "Start a project")]
# question
qx, qy = xC + 18, Y2 + 52
c2.append(rrect(qx, qy, 230, 150, 12, "#ffffff", "#9fb3cc", 1.6))
c2.append(t(qx + 14, qy + 26, "Question", 14, "bold", INK))
c2.append(t(qx + 14, qy + 50, ["Do the conditions change", "cell shape?"], 14, fill=INK, lh=18))
c2.append(t(qx + 14, qy + 100, "Measurement", 14, "bold", INK))
c2.append(t(qx + 14, qy + 122, ["area, aspect ratio and", "other shape features"], 13, fill=BODY, lh=16))
# acquire: real images
ax0 = qx + 230 + 30
c2.append(arrow(qx + 236, qy + 75, ax0 - 6, qy + 75, "#4a5568", 2.5))
IMS = 200
for k_, (png, px, lbl) in enumerate([("data7/MAX_ctrl3-Pr.png", 0.131788, "Control"), ("data7/MAX_si8-6-Pr.png", 0.119808, "Condition 2")]):
    ix = ax0 + k_ * (IMS + 10)
    c2.append(real_image(ix, Y2 + 38, IMS, IMS, png, px, 1024, 20, f"CCT8 CDM {lbl} (real)"))
    c2.append(halo(ix + 6, Y2 + 54, lbl))
c2.append(t(ax0 + IMS + 5, Y2 + 38 + IMS + 24, "Acquire representative images", 15, "bold", INK, "middle"))
# approach
vx = ax0 + 2 * IMS + 10 + 36
c2.append(arrow(ax0 + 2 * IMS + 16, qy + 75, vx - 6, qy + 75, "#4a5568", 2.5))
vcx = vx + 120
ven = []
for dx, colr in [(-62, "#8a94a3"), (-20, C["A"]["accent"]), (22, C["B"]["accent"]), (64, C["C"]["accent"])]:
    ven.append(f'<circle cx="{vcx+dx}" cy="{qy+70}" r="38" fill="{colr}" opacity="0.72"/>')
for dx, word in [(-70, "Classical"), (-18, "Extract"), (24, "Predict"), (70, "LLM")]:
    if word:
        ven.append(t(vcx + dx, qy + 75, word, 11.5, "bold", "#ffffff", "middle"))
c2.append(group("approach circles", "".join(ven)))
c2.append(t(vcx, Y2 + 38 + IMS + 24, "Choose the approach", 15, "bold", INK, "middle"))
c2.append(t(vcx, qy + 135, ["Start with an established", "approach; compare candidates", "on reference examples"], 13, fill=BODY, anchor="middle", lh=16))

# ---------------- row 3: D (conclude)
Y3 = Y2 + H2 + 10
H3 = 340
d3 = [card(28, Y3, 1784, H3, "Validate, then conclude from a reliable measurement")]
# validation checklist
lx, ly = 64, Y3 + 70
d3.append(rrect(lx, ly, 270, 200, 12, "#ffffff", "#c8d3e0", 1.5))
d3.append(t(lx + 16, ly + 28, "Validate", 15, "bold", INK))
for k_, txt in enumerate(["Representative variation", "Measurement-relevant errors", "Independent test data",
                          "Every biological repeat"]):
    yy = ly + 62 + k_ * 34
    d3.append(rrect(lx + 16, yy - 13, 18, 18, 3, "#ffffff", "#2f9a43", 2)
              + f'<path d="M{lx+20},{yy-4} L{lx+24},{yy+1} L{lx+31},{yy-8}" fill="none" stroke="#2f9a43" stroke-width="2.4" stroke-linecap="round"/>'
              + t(lx + 44, yy + 1, txt, 14, fill=BODY))
d3.append(arrow(lx + 276, ly + 100, lx + 304, ly + 100, "#4a5568", 2.5))


def axis_ticks(x0, y0, x1, y1, ticks, vmin, vmax, vertical=True):
    g = []
    for v in ticks:
        if vertical:
            yy = y1 - (v - vmin) / (vmax - vmin) * (y1 - y0)
            g.append(f'<line x1="{x0-4}" y1="{yy:.1f}" x2="{x0}" y2="{yy:.1f}" stroke="{BODY}" stroke-width="1"/>' + t(x0 - 7, yy + 4, f"{v:g}", 11.5, fill=BODY, anchor="end"))
        else:
            xx = x0 + (v - vmin) / (vmax - vmin) * (x1 - x0)
            g.append(f'<line x1="{xx:.1f}" y1="{y1}" x2="{xx:.1f}" y2="{y1+4}" stroke="{BODY}" stroke-width="1"/>' + t(xx, y1 + 16, f"{v:g}", 11.5, fill=BODY, anchor="middle"))
    return "".join(g)


# superplot (aspect ratio): cells as points in condition colour, repeat means as larger shapes
px0, py0, pw, ph = lx + 380, Y3 + 72, 360, 210
YMAX = 10
sp = [t(px0 + pw / 2, Y3 + 60, "Every repeat (SuperPlot)", 14, "bold", INK, "middle")]
sp.append(f'<line x1="{px0}" y1="{py0}" x2="{px0}" y2="{py0+ph}" stroke="{BODY}" stroke-width="1.2"/>'
          f'<line x1="{px0}" y1="{py0+ph}" x2="{px0+pw}" y2="{py0+ph}" stroke="{BODY}" stroke-width="1.2"/>')
sp.append(axis_ticks(px0, py0, px0, py0 + ph, [0, 2, 4, 6, 8, 10], 0, YMAX))
sp.append(f'<text x="{px0-38}" y="{py0+ph/2}" font-size="13" fill="{INK}" text-anchor="middle" transform="rotate(-90 {px0-38} {py0+ph/2})">Aspect ratio</text>')
rng_ = np.random.default_rng(1) if "np" in globals() else None
import numpy as np
rng_ = np.random.default_rng(1)
cw_ = pw / 3
SH = {1: "circle", 2: "square", 3: "triangle"}


def marker(kind, x, y, r, fill):
    if kind == "circle":
        return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}" stroke="#14223a" stroke-width="1.4"/>'
    if kind == "square":
        return f'<rect x="{x-r:.1f}" y="{y-r:.1f}" width="{2*r}" height="{2*r}" fill="{fill}" stroke="#14223a" stroke-width="1.4"/>'
    return f'<path d="M{x:.1f},{y-r*1.15:.1f} L{x+r*1.05:.1f},{y+r*0.75:.1f} L{x-r*1.05:.1f},{y+r*0.75:.1f} Z" fill="{fill}" stroke="#14223a" stroke-width="1.4"/>'


for ci, c in enumerate(CP["conditions"]):
    cx = px0 + cw_ * (ci + 0.5)
    for cc, r, v in CP["superplot"]["cells"]:
        if cc != c:
            continue
        vy = py0 + ph - min(v, YMAX) / YMAX * ph
        jx = cx + (r - 2) * 28 + rng_.uniform(-9, 9)
        sp.append(f'<circle cx="{jx:.1f}" cy="{vy:.1f}" r="2.3" fill="{CT_COLS[c]}" opacity="0.45"/>')
    for cc, r, m in CP["superplot"]["means"]:
        if cc == c:
            sp.append(marker(SH[r], cx + (r - 2) * 28, py0 + ph - m / YMAX * ph, 6.5, CT_COLS[c]))
    sp.append(t(cx, py0 + ph + 18, CT_NAME[c], 12.5, fill=INK, anchor="middle"))
# repeat key
for k_, r in enumerate((1, 2, 3)):
    kx = px0 + 70 + k_ * 90
    sp.append(marker(SH[r], kx, py0 + ph + 42, 5, "#ffffff") + t(kx + 10, py0 + ph + 46, f"repeat {r}", 12, fill=BODY))
d3.append(group("SuperPlot aspect ratio", "".join(sp)))

# p-value heatmap: -log10(Bonferroni p) per feature and comparison
hx0, hy0 = px0 + pw + 200, Y3 + 72
FEATS = CP["features"]
FN = {"Perim.": "Perimeter", "Circ.": "Circularity", "AR": "Aspect ratio", "Round": "Roundness", "MinFeret": "Min Feret",
      "Major": "Major axis", "Minor": "Minor axis"}
cwh, chh = 80, 21
hm = [t(hx0 + cwh, Y3 + 60, "All features (p-values)", 14, "bold", INK, "middle")]
PMAX = 3.5


def seq(v):   # single-hue sequential ramp, light -> dark purple
    a = np.array([243, 238, 250]); b = np.array([84, 39, 143])
    u = min(max(v / PMAX, 0), 1)
    c_ = (a + (b - a) * u).astype(int)
    return "#%02x%02x%02x" % tuple(c_)


for ri, f in enumerate(FEATS):
    yy = hy0 + ri * chh
    hm.append(t(hx0 - 8, yy + 15, FN.get(f, f), 12, fill=BODY, anchor="end"))
    for ci, c in enumerate(["siCCT8#5", "siCCT8#8"]):
        p = CP["stats"][f"{f}|siCTRL|{c}"]["p_bonf"]
        v = -np.log10(p)
        hm.append(f'<rect x="{hx0+ci*cwh}" y="{yy}" width="{cwh-2}" height="{chh-2}" fill="{seq(v)}"/>')
        if p < 0.05:
            hm.append(t(hx0 + ci * cwh + cwh / 2 - 1, yy + 15, "•", 14, "bold", "#ffffff" if v > 1.8 else INK, "middle"))
for ci, c in enumerate(["siCCT8#5", "siCCT8#8"]):
    hm.append(t(hx0 + ci * cwh + cwh / 2, hy0 + len(FEATS) * chh + 16, CT_NAME[c], 12, fill=INK, anchor="middle"))
    hm.append(f'<rect x="{hx0+ci*cwh+cwh/2-26}" y="{hy0+len(FEATS)*chh+20}" width="52" height="3" fill="{CT_COLS[c]}"/>')
hm.append(t(hx0 + cwh, hy0 + len(FEATS) * chh + 38, "vs control", 12, fill=BODY, anchor="middle"))
# colour bar
cbx, cby = hx0 + 2 * cwh + 18, hy0
for k_ in range(40):
    v = PMAX * (1 - k_ / 39)
    hm.append(f'<rect x="{cbx}" y="{cby + k_ * 4.6:.1f}" width="12" height="4.8" fill="{seq(v)}"/>')
hm.append(t(cbx + 18, cby + 8, "3.5", 11.5, fill=BODY) + t(cbx + 18, cby + 184, "0", 11.5, fill=BODY))
hm.append(f'<text x="{cbx+46}" y="{cby+92}" font-size="12" fill="{INK}" text-anchor="middle" transform="rotate(-90 {cbx+46} {cby+92})">−log10 p</text>')
hm.append(t(cbx - 2, cby + 205, "• p < 0.05", 12, fill=BODY))
d3.append(group("p-value heatmap", "".join(hm)))

# PCA
qx0, qy0, qw, qh = cbx + 170, Y3 + 72, 400, 210
pts = CP["pca"]["pts"]
xs = np.array([p[1] for p in pts]); ys = np.array([p[2] for p in pts])
xl, xh = np.percentile(xs, [0, 99.5]); yl, yh = np.percentile(ys, [0.5, 99.5])
pc = [t(qx0 + qw / 2, Y3 + 60, "Phenotype space (PCA)", 14, "bold", INK, "middle"),
      f'<line x1="{qx0}" y1="{qy0}" x2="{qx0}" y2="{qy0+qh}" stroke="{BODY}" stroke-width="1.2"/>'
      f'<line x1="{qx0}" y1="{qy0+qh}" x2="{qx0+qw}" y2="{qy0+qh}" stroke="{BODY}" stroke-width="1.2"/>']
cid_ = clip(qx0, qy0, qw, qh, 0)
dots = []
for c in CP["conditions"]:
    for cc, a_, b_ in pts:
        if cc == c:
            X_ = qx0 + (a_ - xl) / (xh - xl) * qw
            Y_ = qy0 + qh - (b_ - yl) / (yh - yl) * qh
            dots.append(f'<circle cx="{X_:.1f}" cy="{Y_:.1f}" r="3.2" fill="{CT_COLS[c]}" opacity="0.75" stroke="#ffffff" stroke-width="0.6"/>')
pc.append(f'<g clip-path="url(#{cid_})">{"".join(dots)}</g>')
v1, v2 = CP["pca"]["var"]
pc.append(t(qx0 + qw / 2, qy0 + qh + 18, f"PC1 ({v1*100:.0f}%)", 12.5, fill=INK, anchor="middle"))
pc.append(f'<text x="{qx0-12}" y="{qy0+qh/2}" font-size="12.5" fill="{INK}" text-anchor="middle" transform="rotate(-90 {qx0-12} {qy0+qh/2})">PC2 ({v2*100:.0f}%)</text>')
for k_, c in enumerate(CP["conditions"]):
    kx = qx0 + 60 + k_ * 100
    pc.append(f'<circle cx="{kx+6}" cy="{qy0+qh+42}" r="5" fill="{CT_COLS[c]}"/>' + t(kx + 15, qy0 + qh + 46, CT_NAME[c], 12, fill=BODY))
d3.append(group("PCA", "".join(pc)))

add(group("Panel B LLM", "".join(b2) + letter(36, Y2 + 6, "B", "C")))
add(group("Panel C start a project", "".join(c2) + letter(xC + 6, Y2 + 6, "C")))
add(group("Panel D conclude", "".join(d3) + letter(36, Y3 + 6, "D")))
H = Y3 + H3 + 20
svg = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
       f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" xmlns:xlink="http://www.w3.org/1999/xlink" '
       f'width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">\n'
       f'<defs>{"".join(defs)}</defs>\n<rect width="{W}" height="{H}" fill="#ffffff"/>\n'
       + "\n".join(out) + "\n</svg>\n")
open("fig1_v4.svg", "w", encoding="utf-8").write(svg)
print("written", len(svg) // 1024, "KB; height", H)
