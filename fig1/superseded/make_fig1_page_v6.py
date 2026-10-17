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
            + t(x + w - 8 - bar / 2, y + h - 13, f"{bar_um:g} µm", 11.5, "bold" if bar_col != "#ffffff" else "normal", bar_col, "middle") + "</g>")


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
            + t(106, y + 46, title, 24, "bold", INK) + t(106, y + 72, desc, 16, fill=BODY))


HH = 92                       # row header height


PX = 0.649614
cA, cB, cC = C["A"], C["B"], C["C"]
icol = cC["accent"]

add(group("Title", t(28, 48, "Fig. 1 | Where AI can enter a microscopy image-analysis workflow", 38, "bold", INK)
          + t(28, 80, "Each use has different outputs, and each needs its own validation against the intended biological measurement.",
              20, fill="#3a4250")))


HC = 360                      # content height of the segmentation row
IMW, IMH = 210, 280           # main image size


def image_pipeline(ct, col, left_lbl, right_lbl, right_png, right_w, ai_lines, right_bar, hc=None):
    """Acquired image -> AI model (U-Net) -> output image, shared by panels A and B (same geometry, aligned columns)."""
    k = C[col]
    hc = hc or HC
    p = [rrect(44, ct, 700, hc, 12, k["inner"], k["innerstroke"])]
    ct += (hc - HC) / 2                     # centre the pipeline vertically in taller rows
    p.append(box_title(171, ct + 26, "Acquired image", "(brightfield)"))
    p.append(real_image(66, ct + 62, IMW, IMH, "data3/A_bf.png", PX, 210, 50, f"{col} acquired brightfield (real)", "#111111"))
    p.append(arrow(280, ct + 202, 298, ct + 202, k["accent"]))
    p.append(rrect(304, ct + 82, 130, 240, 12, k["tint"], k["tintstroke"]))
    p.append(t(369, ct + 112, "AI model", 18, "bold", INK, "middle"))
    p.append(unet(369, ct + 162, k["accent"], "U-Net-style model icon"))
    p.append(t(369, ct + 224, ai_lines, 16, fill=INK, anchor="middle", lh=21))
    p.append(arrow(438, ct + 202, 456, ct + 202, k["accent"]))
    p.append(box_title(567, ct + 26, right_lbl[0], right_lbl[1]))
    p.append(real_image(462, ct + 62, IMW, IMH, right_png, PX, right_w, 50, f"{col} output (real)", right_bar))
    return p


MONO = 'font-family="Liberation Mono, Courier New, monospace"'


VH = 92                       # validation strip height


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
COL2, COL3 = (764, 572), (1352, 444)          # shared column grid for rows A and B (x, width)


def key_item(x, y, colr, label, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<line x1="{x}" y1="{y}" x2="{x+22}" y2="{y}" stroke="{colr}" stroke-width="3"{d}/>'
            + t(x + 28, y + 4.5, label, 12.5, fill=BODY))


def bar(x, y, w, v, colr, label, value_txt=None):
    return (t(x, y, label, 13, fill=BODY)
            + f'<rect x="{x}" y="{y+5}" width="{w}" height="12" rx="3" fill="#e4e8ee"/>'
            + f'<rect x="{x}" y="{y+5}" width="{w*v:.1f}" height="12" rx="3" fill="{colr}"/>'
            + t(x + w + 6, y + 15.5, value_txt or f"{v:.2f}", 12.5, "bold", INK))


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


# ---------------------------------------------------------------- panel A: overview of the three uses
YO, RO = 104, HH + 252 + 12
o = [row(YO, RO, "N", "A", "Three ways AI enters an image-analysis workflow",
         "AI can turn images into measurements, predict image content, or build and run the analysis.")]
CT = YO + HH
CW = 576


def mini_unet(cx, cy, col):
    return f'<g transform="translate({cx} {cy}) scale(0.55) translate({-cx} {-cy})">' + unet(cx, cy, col, "mini U-Net icon") + "</g>"


def mini_llm(cx, cy):
    pet = "".join(f'<rect x="{cx-6}" y="{cy-17}" width="12" height="26" rx="6" fill="none" stroke="{INK}" stroke-width="2.4" '
                  f'transform="rotate({k*60} {cx} {cy})"/>' for k in range(6))
    return f'<g inkscape:label="mini LLM icon (generic)">{pet}</g>'


def text_card(x, y, w, h, head, lines, col):
    return (rrect(x, y, w, h, 8, "#ffffff", col, 1.6) + t(x + 9, y + 18, head, 12, "bold", col)
            + t(x + 9, y + 38, lines, 11, fill=INK, lh=15, extra=" " + MONO))


cards_o = [
    ("A", "Extract information", "Detect, segment, classify or track objects to measure them.", "example: B",
     ("img", "data3/A_bf.png", 210, "acquired"), ("img", "data3/A_cancer_labels_overlay.png", 630, "labels"), "AI model"),
    ("B", "Predict image content", "Denoise, super-resolve or predict a label: inferred pixels.", "example: C",
     ("img", "data3/A_bf.png", 210, "acquired"), ("img", "data3/B_predicted_composite.png", 210, "predicted"), "AI model"),
    ("C", "Build, run or interpret", "LLMs advise, write code, run workflows or answer directly.", "example: D",
     ("txt", "prompt", ["Write only the", "segmentation step.", "Do not silently", "resize or normalise.", "Include a test."]),
     ("txt", "code you can test", ["lbl = segment(img)", "area = measure(lbl)", "test_known_case()"]), "LLM"),
]
for i, (key, ttl, desc, ptr, left, right, mid_lbl) in enumerate(cards_o):
    k = C[key]
    x = 44 + i * (CW + 12)
    cx = x + CW / 2
    g = [rrect(x, CT, CW, 252, 12, k["bg"], k["stroke"], 1.8),
         t(x + 18, CT + 28, ttl, 18, "bold", k["accent"]), t(x + CW - 16, CT + 28, ptr, 13.5, fill=BODY, anchor="end", style="italic"),
         t(x + 18, CT + 49, desc, 14, fill=BODY)]
    yy, iw, ih = CT + 62, 120, 160
    for side, spec in [(-1, left), (1, right)]:
        if spec[0] == "img":
            xx = cx - 60 - iw if side < 0 else cx + 60
            g.append(real_image(xx, yy, iw, ih, spec[1], PX, spec[2], 50, f"overview {ttl} {spec[3]}", "#111111" if "bf" in spec[1] or "overlay" in spec[1] else "#ffffff"))
            g.append(t(xx + iw / 2, yy + ih + 18, spec[3], 13, fill=BODY, anchor="middle"))
        else:
            ww = 150
            xx = cx - 50 - ww if side < 0 else cx + 50
            g.append(text_card(xx, yy + 10, ww, 140, spec[1], spec[2], k["accent"]))
    if mid_lbl == "LLM":
        g.append(mini_llm(cx, yy + 72) + arrow(cx - 46, yy + 80, cx - 26, yy + 80, k["accent"], 2.4) + arrow(cx + 26, yy + 80, cx + 46, yy + 80, k["accent"], 2.4))
        g.append(t(cx, yy + 116, "LLM", 13, fill=BODY, anchor="middle"))
    else:
        g.append(mini_unet(cx, yy + 74, k["accent"]) + arrow(cx - 56, yy + 80, cx - 38, yy + 80, k["accent"], 2.4)
                 + arrow(cx + 38, yy + 80, cx + 56, yy + 80, k["accent"], 2.4))
        g.append(t(cx, yy + 116, mid_lbl, 13, fill=BODY, anchor="middle"))
    o.append(group(f"overview card {ttl}", "".join(g)))
add(group("Panel A overview", "".join(o)))

# ---------------------------------------------------------------- panel A (row)
RH = HH + HC + 12 + VH + 12
YA = YO + RO + 12
a = [row(YA, RH, "A", "B", "Extract information: a segmentation example",
         "Deep-learning models detect, segment, classify or track objects to generate measurements. Here: cancer cells on an endothelial monolayer.")]
CT = YA + HH
a += image_pipeline(CT, "A", None, ("Analysis output", "(cancer-cell labels, StarDist)"), "data3/A_cancer_labels_overlay.png", 630,
                    ["Detect", "Segment", "Classify", "Track"], "#111111")
a.append(arrow(746, CT + 202, COL2[0] - 4, CT + 202, cA["accent"]))
# application: what will you measure, and which errors matter
x0, w0 = COL2
a.append(rrect(x0, CT, w0, HC, 12, cA["inner"], cA["innerstroke"]))
a.append(box_title(x0 + w0 / 2, CT + 28, "What will you measure?", "and which errors matter"))
cuts = [0]
ms = []
# counts
for (dx, dy) in [(-22, -14), (4, -22), (24, -2), (-14, 10), (10, 18), (-34, 14), (32, 22)]:
    ms.append(f'<circle cx="{117+dx}" cy="{660+dy}" r="13" fill="#9cc3ee" stroke="{cA["accent"]}" stroke-width="2"/>'
              f'<circle cx="{117+dx}" cy="{660+dy}" r="5.5" fill="{cA["accent"]}"/>')
ms.append(t(117, 726, "Counts", 15.5, fill=INK, anchor="middle"))
cuts.append(len(ms))
# morphology: three cell shapes with different features (spiky / elongated / protrusive)
mcol, mfill = cA["accent"], "#9cc3ee"
spikes = []
for k in range(13):
    ang = 2 * math.pi * k / 13 + 0.2
    ln = 22 + (5 if k % 2 else 0)
    spikes.append(f'<line x1="{214+13*math.cos(ang):.1f}" y1="{666+13*math.sin(ang):.1f}" x2="{214+ln*math.cos(ang):.1f}" '
                  f'y2="{666+ln*math.sin(ang):.1f}" stroke="{mcol}" stroke-width="2" stroke-linecap="round"/>')
ms.append('<g inkscape:label="cell spiky (filopodia)">' + "".join(spikes)
          + f'<circle cx="214" cy="666" r="14" fill="{mfill}" stroke="{mcol}" stroke-width="2.2"/>'
          + f'<circle cx="214" cy="666" r="6" fill="{mcol}"/></g>')
ms.append(f'<g inkscape:label="cell elongated" transform="translate(262 660) rotate(-58)">'
          f'<path d="M-36,0 C-18,-11 18,-11 36,0 C18,11 -18,11 -36,0 Z" fill="{mfill}" stroke="{mcol}" stroke-width="2.2" '
          f'stroke-linejoin="round"/><ellipse cx="0" cy="0" rx="9" ry="5" fill="{mcol}"/></g>')
# protrusive cell: round body with a thin, ruffled lamellipodium fanning out to the upper right
lam = ["M3,-11"]
angs = [math.radians(a) for a in range(-80, 51, 13)]
for i, ang in enumerate(angs):
    r_out = 31 if i % 2 == 0 else 27
    lam.append(f"Q{(r_out+5)*math.cos(ang - 0.11):.1f},{(r_out+5)*math.sin(ang - 0.11):.1f} "
               f"{r_out*math.cos(ang):.1f},{r_out*math.sin(ang):.1f}")
lam.append("L8,9 Z")
ms.append(f'<g inkscape:label="cell protrusive (lamellipodium)" transform="translate(296 676)">'
          f'<path d="{" ".join(lam)}" fill="#cfe2f6" stroke="{mcol}" stroke-width="1.8" stroke-linejoin="round"/>'
          f'<circle cx="0" cy="0" r="13" fill="{mfill}" stroke="{mcol}" stroke-width="2.2"/>'
          f'<circle cx="-1" cy="1" r="6" fill="{mcol}"/></g>')
ms.append(t(263, 726, "Morphology", 15.5, fill=INK, anchor="middle"))
cuts.append(len(ms))
# phenotypes
for (dx, dy, colr) in [(-26, -16, "#2ec4b6"), (0, -26, "#ff7a3d"), (24, -12, "#7b5cff"), (-14, 6, "#ff4fa3"),
                       (12, 10, "#2f9a43"), (-32, 20, "#ffd23f"), (30, 20, "#3ec1ff"), (0, 30, "#c86bff")]:
    ms.append(f'<circle cx="{409+dx}" cy="{662+dy}" r="9.5" fill="{colr}"/>')
ms.append(t(409, 726, "Phenotypes", 15.5, fill=INK, anchor="middle"))
cuts.append(len(ms))
# tracks
for i, colr in enumerate(["#2f9a43", "#d6336c", "#7b5cff", "#1f6fc5"]):
    rr = random.Random(40 + i)
    px, py = 498, 694 - i * 18
    pts = [(px, py)]
    for _ in range(5):
        px += rr.uniform(18, 24)
        py += rr.uniform(-16, 6)
        pts.append((px, py))
    ms.append(f'<polyline points="{" ".join(f"{p:.1f},{q:.1f}" for p, q in pts)}" fill="none" stroke="{colr}" stroke-width="2.4"/>')
    ms += [f'<circle cx="{p:.1f}" cy="{q:.1f}" r="3.2" fill="{colr}"/>' for p, q in pts]
ms.append(t(555, 726, ["Tracks", "and dynamics"], 15.5, fill=INK, anchor="middle", lh=19))
cuts.append(len(ms))
old_c = [(117, 662), (263, 664), (409, 664), (555, 662)]
meas = [("Counts", "missed or extra objects"), ("Morphology", "boundary accuracy"),
        ("Phenotypes", "misclassified objects"), ("Tracks", "linking errors over time")]
for i in range(4):
    cx = x0 + w0 * (0.25 if i % 2 == 0 else 0.75)
    cy = CT + (110 if i < 2 else 268)
    a.append(f'<g transform="translate({cx:.1f} {cy}) scale(0.9) translate({-old_c[i][0]} {-old_c[i][1]})">'
             + group(f"icon {meas[i][0]}", "".join(ms[cuts[i]:cuts[i + 1] - 1])) + "</g>")
    a.append(t(cx, cy + 60, meas[i][0], 16, "bold", INK, "middle") + t(cx, cy + 80, meas[i][1], 14, fill=BODY, anchor="middle"))
a.append(arrow(COL2[0] + COL2[1] + 2, CT + 202, COL3[0] - 4, CT + 202, cA["accent"]))
# example: two models against the manual reference (score card, same form as panel B)
A_SC = json.load(open("data4/A_scores.json"))
x1, w1 = COL3
a.append(rrect(x1, CT, w1, HC, 12, cA["inner"], cA["innerstroke"]))
a.append(box_title(x1 + w1 / 2, CT + 28, "When is good enough, good enough?"))
a.append(t(x1 + w1 / 2, CT + 46, "Counting cancer cells: F1 at IoU ≥ 0.5 vs a manual reference", 12.5, fill=BODY, anchor="middle"))
a.append(key_item(x1 + 70, CT + 64, MODEL, "model") + key_item(x1 + 180, CT + 64, REF, "manual reference", DASH))
TWa, THa = 120, 129.6
SUB = (60, 118, 150, 162)
BXa = x1 + 16 + TWa + 16
for k_, (tag, lbl, cjson, bars_) in enumerate([
        ("stardist", "StarDist", "data3/A_stardist_contours.json",
         [("StarDist, source-study test set", 0.933, "#8a94a3", None), ("StarDist, this field", A_SC["stardist"], cA["accent"], None)]),
        ("cellpose", "Cellpose-SAM", "data4/A_cellpose_contours.json",
         [("Cellpose-SAM (generalist), this field", A_SC["cellpose"], cA["accent"], None)])]):
    ry = CT + 76 + k_ * (THa + 12)
    tl = [real_image(x1 + 16, ry, TWa, THa, "data4/A_tile_bf.png", PX, 150, 20, f"A example tile {tag}", "#111111"),
          vector_outlines_sub(x1 + 16, ry, TWa, THa, "data3/A_manual_contours.json", "manual reference (vector)", REF, 1.4, DASH, SUB),
          vector_outlines_sub(x1 + 16, ry, TWa, THa, cjson, f"{lbl} (vector)", MODEL, 1.4, None, SUB),
          rrect(x1 + 19, ry + 3, 8.4 * len(lbl) + 8, 19, 4, "#ffffff", "none", 0, ' opacity="0.85"') + t(x1 + 23, ry + 17, lbl, 12.5, "bold", INK)]
    if tag == "stardist":
        kk = TWa / SUB[2]
        ax, ay = x1 + 16 + (183 - SUB[0]) * kk, ry + (230 - SUB[1]) * kk
        tl.append(group("arrow cell missed by both", arrow(ax - 30, ay - 28, ax - 11, ay - 10, cA["accent"])))
    a.append(group(f"example {lbl}", score_row(x1, ry, tl, bars_, BXa)))
a.append(validate_strip(CT + HC + 12, "A", [
    ["Compare with reference annotations on representative", "and difficult images; treat them as references,", "not ground truth."],
    ["Check the errors that matter for the measurement", "(e.g. merges for counts, boundaries for area)."],
    ["Confirm on images not used for tuning; check that", "plausible errors do not change the biological result."],
]))
add(group("Panel B segmentation", "".join(a)))

# ---------------------------------------------------------------- panel B (row)
HCB = 456
RHB = HH + HCB + 12 + VH + 12
YB = YA + RH + 12
b = [row(YB, RHB, "B", "C", "Predict image content: an artificial-labelling example",
         "AI models predict image content: they reduce noise, infer finer detail, or predict a label that was not acquired. Here: DAPI and PECAM from brightfield.")]
CT = YB + HH
b += image_pipeline(CT, "B", None, ("Predicted image", "(DAPI + PECAM, inferred)"), "data3/B_predicted_composite.png", 210,
                    ["Denoise", "Artificial label", "Super-resolve"], "#ffffff", hc=HCB)
b.append(step_pill(58, CT - 12, 1, "Generate", cB["accent"]))
b.append(arrow(746, CT + HCB / 2, COL2[0] - 4, CT + HCB / 2, cB["accent"]))
# application: how will the predicted image be used?
x0, w0 = COL2
b.append(rrect(x0, CT, w0, HCB, 12, cB["inner"], cB["innerstroke"]))
b.append(step_pill(x0 + 14, CT - 12, 2, "Measure", cB["accent"]))
b.append(box_title(x0 + w0 / 2, CT + 28, "What will you measure in the generated image?"))
uses = [
    ("ok", "As an intermediate step", ["visualise", "segment", "detect", "register"],
     "Validate the downstream output against acquired data", "e.g. cells segmented on predicted PECAM vs manual outlines"),
    ("caution", "As the measurement itself", ["intensity", "abundance", "localisation"],
     "Only after validation against acquired data", "e.g. predicted vs acquired intensities, pixel by pixel"),
]
for k_, (kind, ttl, icons, concl, eg) in enumerate(uses):
    yb = CT + 60 + k_ * 196
    if k_:
        b.append(f'<line x1="{x0+20}" y1="{yb-18}" x2="{x0+w0-20}" y2="{yb-18}" stroke="{cB["tintstroke"]}" stroke-width="1.5" stroke-dasharray="5 4"/>')
    if kind == "ok":
        b.append(check_badge(x0 + 32, yb + 4, cB["accent"], 11).replace('stroke-width="4.5"', 'stroke-width="2.8"')
                 .replace(f'M{x0+22},{yb+5} L{x0+29},{yb+12} L{x0+43},{yb-4}', f'M{x0+26.5},{yb+4.5} L{x0+30.5},{yb+8.5} L{x0+37.5},{yb-0.5}'))
    else:
        b.append(caution(x0 + 32, yb + 3))
    b.append(t(x0 + 52, yb + 10, ttl, 17, "bold", INK))
    n = len(icons)
    for i, nm in enumerate(icons):
        cx = x0 + w0 * (i + 0.5) / 4 + (w0 / 8 if n == 3 else 0)
        b.append(group(f"use icon {nm}", b_icon(nm, cx, yb + 66, cB["accent"])))
        b.append(t(cx, yb + 110, nm, 14.5, fill=INK, anchor="middle"))
    b.append(t(x0 + w0 / 2, yb + 146, "→ " + concl, 15.5, "bold", INK, "middle"))
    b.append(t(x0 + w0 / 2, yb + 167, eg, 13, fill=BODY, anchor="middle", style="italic"))
b.append(arrow(COL2[0] + COL2[1] + 2, CT + HCB / 2, COL3[0] - 4, CT + HCB / 2, cB["accent"]))
# example: score card (same form as panel A)
x1, w1 = COL3
b.append(rrect(x1, CT, w1, HCB, 12, cB["inner"], cB["innerstroke"]))
b.append(box_title(x1 + w1 / 2, CT + 28, "When is good enough, good enough?"))
b.append(t(x1 + w1 / 2, CT + 46, "Bars: F1 at IoU ≥ 0.5 (segmentation) or pixel r (intensity)", 12.5, fill=BODY, anchor="middle"))
b.append(key_item(x1 + 40, CT + 64, MODEL, "model") + key_item(x1 + 140, CT + 64, REF, "annotator 1", DASH)
         + key_item(x1 + 270, CT + 64, REF2, "annotator 2", DASH))
TWb, THb = 88, 118.8
BXb1 = x1 + 16 + TWb + 16
BXb2 = x1 + 16 + 2 * TWb + 6 + 16
rows_b = [
    ("cells", [("data3/B_PECAM_acquired.png", [("data3/B_cells_contours.json", "Cellpose on predicted PECAM (vector)", MODEL, None),
                                                ("data3/B_annotator1_contours.json", "annotator 1 (vector)", REF, DASH)])],
     [("Annotator 1 vs 2 (human agreement)", 0.897, "#8a94a3", None), ("Cellpose on predicted vs annotator 1", 0.781, cB["accent"], None),
      ("Cellpose on predicted vs annotator 2", 0.746, cB["accent"], None)], BXb1),
    ("nuclei", [("data3/B_DAPI_acquired_nuclei_tile.png", [("data3/B_nuclei_manual_contours.json", "manual HUVEC nuclei (vector)", REF, DASH),
                                                            ("data3/B_nuclei_stardist_contours.json", "StarDist on predicted DAPI (vector)", MODEL, None)])],
     [("StarDist, source-study test set", 0.976, "#8a94a3", None), ("StarDist on predicted DAPI, this field", 0.828, cB["accent"], None)], BXb1),
    ("intensity", [("data3/B_tile_predicted.png", []), ("data3/B_tile_acquired.png", [])],
     [("DAPI, predicted vs acquired", 0.891, cB["accent"], "r 0.89"), ("PECAM, predicted vs acquired", 0.243, cB["accent"], "r 0.24")], BXb2),
]
for k_, (name, tiles, bars_, bx) in enumerate(rows_b):
    ry = CT + 76 + k_ * (THb + 10)
    tl = []
    for j_, (png, layers) in enumerate(tiles):
        tx_ = x1 + 16 + j_ * (TWb + 6)
        tl.append(real_image(tx_, ry, TWb, THb, png, PX, 100, 20, f"B example {name} {j_}"))
        for path, lbl, colr, dash in layers:
            tl.append(vector_outlines_l(tx_, ry, TWb, THb, path, lbl, colr, 1.1, dash))
    cap = {"cells": ["cells"], "nuclei": ["nuclei"], "intensity": ["predicted", "acquired"]}[name]
    for j_, cp in enumerate(cap):
        tl.append(t(x1 + 21 + j_ * (TWb + 6), ry + 15, cp, 12, "bold", "#ffffff"))
    b.append(group(f"example {name}", score_row(x1, ry, tl, bars_, bx, 150, 34)))
b.append(validate_strip(CT + HCB + 12, "B", [
    ["Validate what you will measure: the downstream", "output, or the measurement from the predicted image."],
    ["Benchmark against experimental reference images", "and human agreement, not an absolute threshold."],
    ["Label predicted images as predicted; watch for", "plausible content the acquired data do not support."],
]))
add(group("Panel C artificial labelling", "".join(b)))

# ---------------------------------------------------------------- panel C (row)
YC = YB + RHB + 12
HCD = 300
c = [row(YC, HH + HCD + 12 + VH + 12, "C", "D", "Build, run or interpret the analysis: LLM assistance",
         "Large language models (LLMs) can help design, generate, execute and optimise image-analysis workflows, or — "
         "through multimodal models — inspect images and return an answer directly.")]
CT = YC + HH
ctop = []
# LLM box
ctop.append(rrect(1400, 252, 260, 74, 12, "#ffffff", cC["accent"], 2.5))
petals = "".join(f'<rect x="1446" y="270" width="14" height="30" rx="7" fill="none" stroke="{INK}" stroke-width="2.6" '
                 f'transform="rotate({k*60} 1453 289)"/>' for k in range(6))
ctop.append(f'<g inkscape:label="LLM icon (generic)">{petals}</g>')
ctop.append(t(1484, 298, "LLM / agent", 24, "bold", INK))
# branches
xs = [1308, 1449, 1590, 1732]
ctop.append(f'<path d="M1530,326 V350 M{xs[0]},350 H{xs[-1]}" fill="none" stroke="{cC["accent"]}" stroke-width="2.5"/>')
for xx in xs:
    ctop.append(arrow(xx, 350, xx, 372, cC["accent"], 2.5))
cards = [
    (["Advise"], ["on tools,", "parameters", "or strategies"]),
    (["Generate", "code"], ["(e.g. Python,", "Fiji macro)"]),
    (["Execute", "and optimise", "workflow"], []),
    (["Multimodal", "analysis"], ["(direct answer", "from image)"]),
]
for xx, (bold, reg) in zip(xs, cards):
    ctop.append(rrect(xx - 67, 378, 134, 182, 10, cC["tint"], cC["tintstroke"]))
    ctop.append(t(xx, 404, bold, 16, "bold", "#b02055", "middle", lh=18.5))
    if reg:
        ctop.append(t(xx, 404 + 18.5 * len(bold), reg, 14.5, fill=BODY, anchor="middle", lh=17.5))
icol = cC["accent"]
# icons: chat, code, gears, image
ctop.append(f'<g inkscape:label="icon advise"><path d="M1286,498 h44 a8,8 0 0 1 8,8 v24 a8,8 0 0 1 -8,8 h-28 l-12,10 v-10 h-4 '
         f'a8,8 0 0 1 -8,-8 v-24 a8,8 0 0 1 8,-8 z" fill="none" stroke="{icol}" stroke-width="2.8" stroke-linejoin="round"/>'
         f'<line x1="1294" y1="512" x2="1322" y2="512" stroke="{icol}" stroke-width="2.8" stroke-linecap="round"/>'
         f'<line x1="1294" y1="522" x2="1314" y2="522" stroke="{icol}" stroke-width="2.8" stroke-linecap="round"/></g>')
ctop.append(f'<g inkscape:label="icon code" fill="none" stroke="{icol}" stroke-width="3.2" stroke-linecap="round" '
         f'stroke-linejoin="round"><path d="M1432,506 L1420,518 L1432,530"/><path d="M1466,506 L1478,518 L1466,530"/>'
         f'<path d="M1455,500 L1443,536"/></g>')

ctop.append('<g inkscape:label="icon gears">' + gear(1580, 512, 17) + gear(1606, 532, 12, 7) + "</g>")
ctop.append(f'<g inkscape:label="icon image"><rect x="1714" y="498" width="38" height="32" rx="4" fill="none" stroke="{icol}" '
         f'stroke-width="2.8"/><path d="M1718,526 L1729,512 L1737,520 L1742,515 L1749,526 Z" fill="{icol}"/>'
         f'<circle cx="1742" cy="506" r="3.5" fill="{icol}"/></g>')

c.append(rrect(44, CT, 700, HCD, 12, cC["inner"], cC["innerstroke"]))
c.append(f'<g transform="translate({138 - 0.92 * 1242:.1f} {CT + 8 - 0.92 * 252:.1f}) scale(0.92)">' + group("LLM and uses", "".join(ctop)) + "</g>")
cflow = []
# workflow strip
cflow.append(rrect(1242, 572, 400, 196, 10, "#f4f2fa", "#ddd6ea"))
cflow.append(micro(1256, 600, 66, 66, 5, "raw", 6, 7, 10, label="C input"))
cflow.append(t(1289, 694, ["Input image", "and data"], 14.5, fill=BODY, anchor="middle", lh=17.5))
cflow.append(arrow(1328, 634, 1360, 634, "#4a5568", 2.5))
mon = (f'<rect x="1374" y="598" width="76" height="54" rx="5" fill="#ffffff" stroke="{INK}" stroke-width="2.6"/>'
       f'<rect x="1384" y="608" width="56" height="34" rx="2" fill="#eef2f8"/>'
       f'<circle cx="1396" cy="625" r="6" fill="none" stroke="{INK}" stroke-width="2"/>'
       f'<line x1="1408" y1="619" x2="1432" y2="619" stroke="{INK}" stroke-width="2"/>'
       f'<line x1="1408" y1="630" x2="1426" y2="630" stroke="{INK}" stroke-width="2"/>'
       f'<path d="M1404,652 L1400,666 L1424,666 L1420,652 Z" fill="{INK}"/>'
       f'<line x1="1390" y1="668" x2="1434" y2="668" stroke="{INK}" stroke-width="3" stroke-linecap="round"/>')
cflow.append(f'<g inkscape:label="icon workflow monitor">{mon}</g>')
cflow.append(t(1412, 694, "Analysis workflow", 14.5, "bold", INK, "middle"))
cflow.append(t(1412, 712, ["(e.g. segmentation, tracking,", "quantification)"], 13.5, fill=BODY, anchor="middle", lh=16.5))
cflow.append(arrow(1462, 634, 1496, 634, "#4a5568", 2.5))
tab = [f'<rect x="1510" y="604" width="58" height="58" rx="3" fill="#ffffff" stroke="{INK}" stroke-width="2.4"/>',
       f'<rect x="1510" y="604" width="58" height="12" fill="{INK}"/>']
for k in range(1, 4):
    tab.append(f'<line x1="1510" y1="{616+k*11.5:.1f}" x2="1568" y2="{616+k*11.5:.1f}" stroke="{INK}" stroke-width="1.4"/>')
for k in (1, 2):
    tab.append(f'<line x1="{1510+k*19.3:.1f}" y1="604" x2="{1510+k*19.3:.1f}" y2="662" stroke="{INK}" stroke-width="1.4"/>')
cflow.append('<g inkscape:label="icon table">' + "".join(tab) + "</g>")
cflow.append(t(1584, 694, ["Measurements", "and results"], 14.5, fill=BODY, anchor="end", lh=17.5,
           extra='') .replace('text-anchor="end"', 'text-anchor="middle"').replace('x="1584.0"', 'x="1540.0"'))
# multimodal column
cflow.append(f'<line x1="1662" y1="566" x2="1662" y2="776" stroke="{cC["accent"]}" stroke-width="2" stroke-dasharray="6 5"/>')
cflow.append(micro(1700, 592, 64, 62, 9, "labels", 8, 6, 9, label="C multimodal"))
cflow.append(arrow(1732, 658, 1732, 680, cC["accent"], 2.5))
cflow.append(f'<g inkscape:label="icon answer"><path d="M1718,684 h28 a6,6 0 0 1 6,6 v14 a6,6 0 0 1 -6,6 h-16 l-8,7 v-7 h-4 '
         f'a6,6 0 0 1 -6,-6 v-14 a6,6 0 0 1 6,-6 z" fill="#fff" stroke="{icol}" stroke-width="2.4"/>'
         f'<circle cx="1724" cy="697" r="2" fill="{icol}"/><circle cx="1732" cy="697" r="2" fill="{icol}"/>'
         f'<circle cx="1740" cy="697" r="2" fill="{icol}"/></g>')
cflow.append(t(1732, 736, "Direct answer", 15.5, "bold", "#b02055", "middle"))
cflow.append(t(1734, 753, V(["(e.g. count, classification,", "interpretation)"], ["(exploratory; validate", "before quantitative use)"]), 11.5, fill=BODY, anchor="middle", lh=15))
cflow.append(t(1732, 584, "Multimodal", 13, "bold", "#b02055", "middle"))
c.append(arrow(746, CT + 150, COL2[0] - 4, CT + 150, cC["accent"], 2.5))
c.append(rrect(COL2[0], CT, COL2[1], HCD, 12, cC["inner"], cC["innerstroke"]))
c.append(box_title(COL2[0] + COL2[1] / 2, CT + 30, "A workflow you can rerun, or a direct answer"))
c.append(f'<g transform="translate({COL2[0] + 8 - 1242} {CT + 165 - 671})">' + group("Workflow and direct answer", "".join(cflow)) + "</g>")
# Box 1 excerpt: the code-generation prompt (verbatim from the article)
bx = [rrect(COL3[0], CT, COL3[1], HCD, 12, "#ffffff", cC["tintstroke"], 1.8),
      t(COL3[0] + COL3[1] / 2, CT + 30, "Example prompt (Box 1): code you can test", 16.5, "bold", "#b02055", "middle"),
      t(COL3[0] + 16, CT + 54, ["I want to measure nuclear area from single-channel",
                        "2D fluorescence images. Write only the segmentation",
                        "step using an established, maintained library and",
                        "its documented API. The input is Y, X, and the pixel",
                        "size is provided in µm per pixel. Do not silently",
                        "resize, normalise, change channels or substitute",
                        "defaults. Expose consequential parameters, fail",
                        "clearly on invalid input, return the label image in",
                        "the original coordinate system, and include a simple",
                        "test. List the assumptions I should verify on real data."], 12, fill=INK, lh=15.5, extra=" " + MONO),
      t(COL3[0] + 16, CT + 222, "Then: adversarial check", 13.5, "bold", INK),
      t(COL3[0] + 16, CT + 241, ["“Assume that this analysis is scientifically", "wrong even though the code runs. Identify", "the assumptions most likely to fail…”"], 12, fill=BODY, lh=15.5, extra=" " + MONO)]
c.append(group("Box 1 prompt excerpt", "".join(bx)))
c.append(validate_strip(CT + HCD + 12, "C", [
    ["Test code on examples with known outputs; save the", "code, parameters, software, model and LLM versions."],
    ["Keep independent test data inaccessible", "during optimisation."],
    ["Direct multimodal answers are not recommended", "for quantitative analysis without task-specific", "validation; they may not be deterministic."],
]))
add(group("Panel D LLM", "".join(c)))

# ---------------------------------------------------------------- bottom strip
YS = YC + HH + HCD + 12 + VH + 12 + 12
s = []
# 1 question
s.append(t(50, 1026, ["Biological question", "and intended measurement"], 17, "bold", INK, lh=20))
person = (f'<circle cx="92" cy="1094" r="17" fill="#f2c9a5"/>'
          f'<path d="M74,1090 C72,1068 108,1064 112,1086 C104,1078 88,1076 74,1090 Z" fill="#3b2a20"/>'
          f'<path d="M58,1186 C58,1140 74,1118 96,1116 C120,1116 132,1140 134,1186 Z" fill="#cfe0f3" stroke="#7aa6d6" stroke-width="2"/>'
          f'<path d="M110,1132 L150,1150" stroke="#cfe0f3" stroke-width="12" stroke-linecap="round"/>')
scope = (f'<g fill="none" stroke="{INK}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">'
         f'<path d="M168,1186 H212"/><path d="M196,1186 C206,1176 210,1160 200,1144"/>'
         f'<path d="M182,1170 H206"/><path d="M178,1110 L194,1148"/><circle cx="196" cy="1150" r="5"/>'
         f'<path d="M188,1186 V1172"/></g>')
s.append(f'<g inkscape:label="scientist + microscope">{person}{scope}</g>')
s.append(rrect(222, 1052, 178, 126, 12, "#ffffff", "#9fb3cc", 1.8) +
         '<path d="M222,1120 L206,1132 L224,1134 Z" fill="#ffffff" stroke="#9fb3cc" stroke-width="1.8"/>'
         '<rect x="222" y="1122" width="4" height="10" fill="#ffffff"/>')
s.append(t(236, 1078, ["Count nuclei?", "Measure nuclear area?", "Identify dividing cells?", "Track cell migration?",
                       "…"], 14, fill=BODY, lh=18.5))
s.append(chevron(426, 1112))
# 2 acquire
s.append(t(520, 1026, ["Acquire", "images"], 17, "bold", INK, "middle", lh=20))
for k in range(5):
    s.append(micro(452 + k * 11, 1068 + k * 9, 92, 76, 30 + k, "raw", 6, 8, 11, label=f"stack {k}"))
    s.append(rrect(452 + k * 11, 1068 + k * 9, 92, 76, 2, "none", "#ffffff", 1.2))
s.append(chevron(630, 1112))
# 3 choose
s.append(t(796, 1026, V("Choose how AI is used", "Choose the approach"), 17, "bold", INK, "middle"))
s.append(t(796, 1046, "(classical, AI, or a combination)", 15, fill=BODY, anchor="middle"))
venn = [f'<circle cx="704" cy="1124" r="40" fill="#8a94a3" opacity="0.8" inkscape:label="classical"/>']
for cx, key in [(772, "A"), (830, "B"), (888, "C")]:
    venn.append(f'<circle cx="{cx}" cy="1124" r="40" fill="{C[key]["accent"]}" opacity="0.72"/>')
venn.append(t(704, 1183, "Classical", 14.5, "bold", "#5d6675", "middle"))
for cx, word in [(778, "Extract"), (830, "Predict"), (886, "LLM")]:
    venn.append(t(cx, 1129, word, 13, "bold", "#ffffff", "middle"))
s.append('<g inkscape:label="approach circles">' + "".join(venn) + "</g>")
s.append(chevron(980, 1112))
# 4 validate
s.append(t(1110, 1026, ["Validate with", "reference data"], 17, "bold", INK, "middle", lh=20))
for k in range(4):
    s.append(micro(1010 + k * 10, 1074 + k * 9, 86, 74, 50 + k, "pred", 6, 8, 11, label=f"ref stack {k}"))
    s.append(rrect(1010 + k * 10, 1074 + k * 9, 86, 74, 2, "none", "#ffffff", 1.2))
s.append(micro(1140, 1072, 82, 82, 60, "labels", 8, 8, 12, label="reference labels"))
s.append(rrect(1240, 1062, 238, 112, 10, "#ffffff", "#c8d3e0", 1.5))
for k, txt in enumerate(["Representative variation", V("Method-specific errors", "Measurement-relevant errors"), "Independent test data"]):
    yy = 1088 + k * 32
    s.append(rrect(1252, yy - 12, 16, 16, 3, "#ffffff", "#2f9a43", 2)
             + f'<path d="M1255,{yy-4} L1259,{yy} L1265,{yy-8}" fill="none" stroke="#2f9a43" stroke-width="2.4" '
               f'stroke-linecap="round"/>' + t(1276, yy + 1, txt, 14.5, fill=BODY))
s.append(chevron(1512, 1112))
# 5 conclusion
s.append(t(1660, 1026, "Biological conclusion", 17, "bold", INK, "middle"))
s.append(t(1660, 1046, "based on a reliable measurement", 15, fill=BODY, anchor="middle"))
bars = [f'<line x1="1560" y1="1068" x2="1560" y2="1180" stroke="{INK}" stroke-width="2"/>',
        f'<line x1="1560" y1="1180" x2="1772" y2="1180" stroke="{INK}" stroke-width="2"/>']
rng = random.Random(3)
for k, hgt in enumerate([24, 38, 54, 72, 92]):
    bx = 1578 + k * 38
    shade = ["#cfe0f3", "#a9c8ea", "#7ea9db", "#5389c8", "#2e66ad"][k]
    bars.append(f'<rect x="{bx}" y="{1180-hgt}" width="24" height="{hgt}" fill="{shade}"/>')
    bars.append(f'<line x1="{bx+12}" y1="{1180-hgt-12}" x2="{bx+12}" y2="{1180-hgt+8}" stroke="{INK}" stroke-width="1.6"/>'
                f'<line x1="{bx+6}" y1="{1180-hgt-12}" x2="{bx+18}" y2="{1180-hgt-12}" stroke="{INK}" stroke-width="1.6"/>')
    for _ in range(5):
        bars.append(f'<circle cx="{bx+12+rng.uniform(-8,8):.1f}" cy="{1180-hgt+rng.uniform(-8,8):.1f}" r="2.2" '
                    f'fill="#ffffff" stroke="{INK}" stroke-width="1"/>')
s.append('<g inkscape:label="bar chart">' + "".join(bars) + "</g>")
add(group("Panel E workflow", rrect(28, YS, 1784, 262, 16, C["N"]["bg"], C["N"]["stroke"], 2)
          + f'<circle cx="70" cy="{YS+34}" r="22" fill="{C["N"]["accent"]}"/>' + t(70, YS + 43, "E", 25, "bold", "#fff", "middle")
          + t(106, YS + 43, "From biological question to biological conclusion", 24, "bold", INK)
          + f'<g transform="translate(0 {YS + 60 - 998})">' + "".join(s) + "</g>"))
H = YS + 262 + 14

svg = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
       f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" xmlns:xlink="http://www.w3.org/1999/xlink" '
       f'width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">\n'
       f'<defs>{"".join(defs)}</defs>\n<rect width="{W}" height="{H}" fill="#ffffff"/>\n'
       + "\n".join(out) + "\n</svg>\n")
open("fig1_page.svg", "w", encoding="utf-8").write(svg)
print("written", len(svg) // 1024, "KB; height", H, "bottom strip ends", YS + 196)
