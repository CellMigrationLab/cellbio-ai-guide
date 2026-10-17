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

W, H = 1840, 2074
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
            + f'<circle cx="72" cy="{y+44}" r="23" fill="{c["accent"]}"/>' + t(72, y + 53, letter, 26, "bold", "#fff", "middle")
            + t(110, y + 53, title, 25, "bold", INK) + t(110, y + 82, desc, 16.5, fill=BODY))


PX = 0.649614
cA, cB, cC = C["A"], C["B"], C["C"]
icol = cC["accent"]

add(group("Title", t(28, 48, "Fig. 1 | Where AI can enter a microscopy image-analysis workflow", 38, "bold", INK)
          + t(28, 82, "AI can turn images into measurements, predict image content, or build and run the analysis. "
                      "Validate each use against the intended measurement.", 20.5, fill="#3a4250")))


def image_pipeline(ct, col, left_lbl, right_lbl, right_png, right_w, ai_lines, right_bar):
    """Acquired image -> AI model (U-Net) -> output image, shared by panels A and B (same geometry, aligned columns)."""
    k = C[col]
    p = [rrect(44, ct, 700, 356, 12, k["inner"], k["innerstroke"])]
    p.append(t(169, ct + 30, "Acquired image", 17, "bold", INK, "middle") + t(169, ct + 50, "(brightfield)", 16, anchor="middle"))
    p.append(real_image(64, ct + 62, 210, 280, "data3/A_bf.png", PX, 210, 50, f"{col} acquired brightfield (real)", "#111111"))
    p.append(arrow(278, ct + 202, 300, ct + 202, k["accent"]))
    p.append(rrect(304, ct + 84, 140, 240, 12, k["tint"], k["tintstroke"]))
    p.append(t(374, ct + 114, "AI model", 18, "bold", INK, "middle"))
    p.append(unet(374, ct + 164, k["accent"], "U-Net-style model icon"))
    p.append(t(374, ct + 224, ai_lines, 16, fill=INK, anchor="middle", lh=21))
    p.append(arrow(448, ct + 202, 474, ct + 202, k["accent"]))
    p.append(t(585, ct + 30, right_lbl[0], 17, "bold", INK, "middle") + t(585, ct + 50, right_lbl[1], 15.5, anchor="middle"))
    p.append(real_image(480, ct + 62, 210, 280, right_png, PX, right_w, 50, f"{col} output (real)", right_bar))
    return p



MONO = 'font-family="Liberation Mono, Courier New, monospace"'


def validate_strip(y, key, items, cols_x, size=15, lh=19):
    c = C[key]
    g = [rrect(44, y, 1752, 84, 12, c["val"]), check_badge(80, y + 42, c["accent"], 20), t(110, y + 49, "Validate", 20, "bold", INK)]
    for x, lines in zip(cols_x, items):
        g.append(f'<circle cx="{x-10}" cy="{y+31}" r="2.6" fill="{BODY}"/>' + t(x, y + 36, lines, size, fill=BODY, lh=lh))
    return group(f"Validate {key}", "".join(g))


def box_title(cx, y, title, sub=None):
    return t(cx, y, title, 16.5, "bold", INK, "middle") + (t(cx, y + 20, sub, 14.5, fill=BODY, anchor="middle") if sub else "")


# ---------------------------------------------------------------- panel A (row)
YA = 110
a = [row(YA, 578, "A", "A", "Extract information from acquired images",
         "Deep-learning models detect, segment, classify or track objects to generate measurements.")]
CT = YA + 106
a += image_pipeline(CT, "A", None, ("Analysis output", "(cancer-cell labels, StarDist)"), "data3/A_cancer_labels_overlay.png", 630,
                    ["Detect", "Segment", "Classify", "Track"], "#111111")
a.append(arrow(746, CT + 202, 760, CT + 202, cA["accent"]))
# check against manual annotation (compare_cancer_gt.py)
a.append(rrect(764, CT, 356, 356, 12, cA["inner"], cA["innerstroke"]))
a.append(box_title(942, CT + 30, "Compare with a reference annotation"))
a.append(real_image(774, CT + 62, 210, 280, "data4/A_check_overlay.png", PX, 630, 50, "A check StarDist vs manual (real)", "#111111"))
k = [t(996, CT + 80, "Whole field", 13.5, "bold", INK),
     t(996, CT + 106, "F1 = 0.86", 19, "bold", cA["accent"]),
     t(996, CT + 124, ["agreement with", "the reference"], 12, fill=BODY, lh=15)]
for i, (colr, lbl) in enumerate([("#26c7ff", "manual"), ("#ff3dd2", "StarDist")]):
    yy = CT + 172 + i * 20
    k.append(f'<line x1="996" y1="{yy}" x2="1014" y2="{yy}" stroke="{colr}" stroke-width="3"/>' + t(1020, yy + 4.5, lbl, 13, fill=BODY))
# arrow to the cell missed by both the reference and StarDist (crop-local ~(183, 230) px; legend explains)
ax, ay = 774 + 183, CT + 62 + 230
a.append(group("arrow cell missed by both", arrow(ax - 36, ay - 32, ax - 13, ay - 11, cA["accent"])))
a.append(group("check stats + key", "".join(k)))
# second task: nuclei (fluorescence) with Cellpose
a.append(rrect(1136, CT, 324, 356, 12, cA["inner"], cA["innerstroke"]))
a.append(box_title(1298, CT + 30, "Another task: nuclei", "(fluorescence, Cellpose)"))
a.append(real_image(1146, CT + 70, 150, 200, "data/panelA_acquired_crop.png", 0.158436, 600, 20, "A nuclei acquired (HPMEC)"))
a.append(real_image(1302, CT + 70, 150, 200, "data/panelA_cellpose_labels_rgb.png", 0.158436, 600, 20, "A nuclei labels (Cellpose)"))
a.append(t(1151, CT + 84, "acquired", 11.5, "bold", "#ffffff") + t(1307, CT + 84, "labels", 11.5, "bold", "#ffffff"))
a.append(t(1298, CT + 300, ["Same principle, different image", "type and model"], 13, fill=BODY, anchor="middle", lh=17))
# measurements 2 x 2
a.append(rrect(1476, CT, 320, 356, 12, cA["inner"], cA["innerstroke"]))
a.append(box_title(1636, CT + 30, "Measurements"))
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
old_c = [(117, 666), (263, 666), (409, 666), (555, 662)]
new_c = [(1560, CT + 118), (1716, CT + 118), (1560, CT + 262), (1716, CT + 262)]
names = ["Counts", "Morphology", "Phenotypes", "Tracks and dynamics"]
for i in range(4):
    dx, dy = new_c[i][0] - old_c[i][0], new_c[i][1] - old_c[i][1]
    a.append(f'<g transform="translate({dx} {dy})">' + group(f"icon {names[i]}", "".join(ms[cuts[i]:cuts[i + 1]])) + "</g>")
a.append(validate_strip(CT + 372, "A", [
    ["Compare with reference annotations on representative and", "difficult images; treat them as references, not ground truth."],
    ["Check the errors that matter for the measurement", "(e.g. merges for counts, boundaries for area)."],
    ["Confirm on images not used for tuning; check that", "plausible errors do not change the biological result."],
], [262, 766, 1270]))
add(group("Panel A", "".join(a)))

# ---------------------------------------------------------------- panel B (row)
YB = YA + 578 + 14
b = [row(YB, 578, "B", "B", "Predict or restore image content",
         "AI models predict image content: they reduce noise, infer finer detail, or predict a label that was not acquired.")]
CT = YB + 106
b += image_pipeline(CT, "B", None, ("Predicted image", "(DAPI + PECAM, inferred)"), "data3/B_predicted_composite.png", 210,
                    ["Denoise", "Artificial label", "Super-resolve"], "#ffffff")
b.append(step_pill(58, CT - 12, 1, "Generate", cB["accent"]))
b.append(arrow(746, CT + 202, 760, CT + 202, cB["accent"]))
S2 = 764
b.append(rrect(S2, CT, 572, 356, 12, cB["inner"], cB["innerstroke"]))
b.append(step_pill(S2 + 14, CT - 12, 2, "Measure", cB["accent"]))
b.append(t(1050, CT + 34, "What will you measure in the generated image?", 17, "bold", INK, "middle"))
b.append(f'<line x1="1052" y1="{CT+50}" x2="1052" y2="{CT+340}" stroke="{cB["tintstroke"]}" stroke-width="1.5" stroke-dasharray="5 4"/>')
TW_, TH_ = 100, 135
st = []
y0 = CT + 64
st.append(check_badge(800, y0, cB["accent"], 9).replace('stroke-width="4.5"', 'stroke-width="2.6"')
          .replace(f'M790,{y0+1} L797,{y0+8} L811,{y0-8}', f'M795.5,{y0+0.5} L798.8,{y0+3.8} L804.6,{y0-3.5}'))
st.append(t(815, y0 + 5, "As an intermediate step", 15, "bold", INK))
st.append(t(908, y0 + 24, "visualise · segment · detect · register", 13, fill=BODY, anchor="middle"))
ty = y0 + 36
for xx, tag in [(786, "predicted"), (930, "acquired")]:
    st.append(real_image(xx, ty, TW_, TH_, f"data3/B_PECAM_{tag}.png", PX, 100, 20, f"step2 PECAM {tag}"))
    if tag == "acquired":
        st.append(vector_outlines_l(xx, ty, TW_, TH_, "data3/B_annotator1_contours.json",
                                    "manual outlines (annotator 1, on acquired PECAM), vector", "#ffffff", 1.1, "3 2"))
    st.append(vector_outlines_l(xx, ty, TW_, TH_, "data3/B_cells_contours.json",
                                "cell outlines (Cellpose on predicted PECAM), vector", "#ff3dd2", 1.1))
    st.append(t(xx + 5, ty + 13, tag, 11.5, "bold", "#ffffff"))
st.append(arrow(890, ty + 68, 926, ty + 68, cB["accent"], 2.2))
st.append(t(908, ty + 60, "check", 11, fill=BODY, anchor="middle"))
# outline key
st.append(f'<line x1="830" y1="{ty+TH_+15}" x2="850" y2="{ty+TH_+15}" stroke="#ff3dd2" stroke-width="2.4"/>'
          + t(856, ty + TH_ + 19, "Cellpose on predicted PECAM", 11.5, fill=BODY)
          + f'<line x1="830" y1="{ty+TH_+31}" x2="850" y2="{ty+TH_+31}" stroke="#7d8796" stroke-width="2.4" stroke-dasharray="3 2"/>'
          + t(856, ty + TH_ + 35, "manual outlines (annotator 1)", 11.5, fill=BODY))
st.append(t(908, ty + TH_ + 60, "Validate the downstream output", 14, "bold", INK, "middle"))
st.append(caution(1086, y0 - 1))
st.append(t(1103, y0 + 5, "As the measurement itself", 15, "bold", INK))
st.append(t(1196, y0 + 24, "intensity · abundance · localisation", 13, fill=BODY, anchor="middle"))
for xx, tag in [(1074, "predicted"), (1218, "acquired")]:
    st.append(real_image(xx, ty, TW_, TH_, f"data3/B_tile_{tag}.png", PX, 100, 20, f"step2 composite {tag}"))
    st.append(t(xx + 5, ty + 13, tag, 11.5, "bold", "#ffffff"))
st.append(t(1196, ty + 73, "vs", 14, "bold", BODY, "middle"))
st.append(t(1196, ty + TH_ + 20, "DAPI magenta · PECAM green", 11.5, fill=BODY, anchor="middle"))
st.append(t(1196, ty + TH_ + 60, "Only after validation vs acquired", 14, "bold", INK, "middle"))
b.append(group("Step 2 measure", "".join(st)))


# agreement chart (compare_annotations.py)
b.append(arrow(1338, CT + 178, 1350, CT + 178, cB["accent"]))
b.append(rrect(1352, CT, 444, 356, 12, cB["inner"], cB["innerstroke"]))
ch = [box_title(1574, CT + 26, "How close is close enough?"),
      t(1574, CT + 44, "Segmentation on predicted images vs manual references on acquired images", 11.5, fill=BODY, anchor="middle")]
TWc, THc = 112, 151.2
for cx, ttl, png, layers in [
        (1463, "Cells (acquired PECAM)", "data3/B_PECAM_acquired.png",
         [("data3/B_annotator1_contours.json", "annotator 1 (vector)", "#ffffff", "3 2"),
          ("data3/B_annotator2_contours.json", "annotator 2 (vector)", "#ffd23f", "3 2")]),
        (1685, "Nuclei (acquired DAPI)", "data3/B_DAPI_acquired_nuclei_tile.png",
         [("data3/B_nuclei_manual_contours.json", "manual HUVEC nuclei (vector)", "#ffffff", "3 2"),
          ("data3/B_nuclei_stardist_contours.json", "StarDist on predicted DAPI (vector)", "#ff3dd2", None)])]:
    ch.append(t(cx, CT + 66, ttl, 13, "bold", INK, "middle"))
    ch.append(real_image(cx - TWc / 2, CT + 74, TWc, THc, png, PX, 100, 20, f"agreement tile {ttl}"))
    for path, lbl, colr, dash in layers:
        ch.append(vector_outlines_l(cx - TWc / 2, CT + 74, TWc, THc, path, lbl, colr, 1.1, dash))
BX0 = 1450
for i, (lbl, v, colr) in enumerate([("A1 vs A2", 0.897, "#8a94a3"), ("Cellpose vs A1", 0.781, cB["accent"]),
                                     ("Cellpose vs A2", 0.746, cB["accent"])]):
    yy = CT + 244 + i * 19
    ch.append(t(BX0 - 6, yy + 10, lbl, 11.5, fill=BODY, anchor="end"))
    ch.append(f'<rect x="{BX0}" y="{yy}" width="85" height="12" rx="3" fill="#e4e8ee"/>'
              f'<rect x="{BX0}" y="{yy}" width="{85*v:.1f}" height="12" rx="3" fill="{colr}"/>')
    ch.append(t(BX0 + 85 + 5, yy + 10.5, f"{v:.2f}", 12, "bold", INK))
BX1 = 1672
ch.append(t(BX1 - 6, CT + 254, "StarDist vs ref", 11.5, fill=BODY, anchor="end"))
ch.append(f'<rect x="{BX1}" y="{CT+244}" width="85" height="12" rx="3" fill="#e4e8ee"/>'
          f'<rect x="{BX1}" y="{CT+244}" width="{85*0.828:.1f}" height="12" rx="3" fill="{cB["accent"]}"/>')
ch.append(t(BX1 + 90, CT + 254.5, "0.83", 12, "bold", INK))
ch.append(t(1685, CT + 278, ["39 of 81 extra nuclei lie on", "cancer cells (HUVEC-only reference)"], 11.5, fill=BODY, anchor="middle", lh=14.5))
ky = CT + 320
ch.append(f'<line x1="1370" y1="{ky}" x2="1388" y2="{ky}" stroke="#ff3dd2" stroke-width="2.4"/>' + t(1393, ky + 4, "model, from predicted image", 11.5, fill=BODY)
          + f'<line x1="1570" y1="{ky}" x2="1588" y2="{ky}" stroke="#7d8796" stroke-width="2.4" stroke-dasharray="3 2"/>' + t(1593, ky + 4, "manual (A1)", 11.5, fill=BODY)
          + f'<line x1="1676" y1="{ky}" x2="1694" y2="{ky}" stroke="#d9a400" stroke-width="2.4" stroke-dasharray="3 2"/>' + t(1699, ky + 4, "manual (A2)", 11.5, fill=BODY))
ch.append(t(1574, CT + 343, "Bars: F1 at IoU ≥ 0.5, whole field (369–450 objects); A1, A2 = annotators", 11, fill=BODY, anchor="middle"))
b.append(group("Agreement chart (F1)", "".join(ch)))
b.append(validate_strip(CT + 372, "B", [
    ["Validate what you will measure: the downstream", "output, or the measurement from the predicted image."],
    ["Use experimental reference images (matched high-SNR,", "acquired fluorescence, higher resolution)."],
    ["Compare with human agreement: annotators also", "differ, so their agreement sets a realistic target."],
    ["Label predicted images as predicted; watch for", "plausible content the acquired data do not support."],
], [262, 640, 1018, 1396], 14, 18.5))
add(group("Panel B", "".join(b)))

# ---------------------------------------------------------------- panel C (row)
YC = YB + 578 + 14
c = [row(YC, 552, "C", "C", "Build, run or interpret the analysis",
         "Large language models (LLMs) can help design, generate, execute and optimise image-analysis workflows, or — "
         "through multimodal models — inspect images and return an answer directly.")]
CT = YC + 106
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

c.append(f'<g transform="translate(-1198 {CT + 8 - 252})">' + group("LLM and uses", "".join(ctop)) + "</g>")
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
c.append(arrow(604, CT + 172, 646, CT + 172, cC["accent"], 2.5))
c.append(f'<g transform="translate(-590 {CT + 172 - 671})">' + group("Workflow and direct answer", "".join(cflow)) + "</g>")
# Box 1 excerpt: the code-generation prompt (verbatim from the article)
bx = [rrect(1226, CT, 570, 330, 12, "#ffffff", cC["tintstroke"], 1.8),
      t(1246, CT + 30, "Example prompt: ask for code you can test (Box 1)", 15.5, "bold", "#b02055"),
      t(1246, CT + 58, ["I want to measure nuclear area from single-channel",
                        "2D fluorescence images. Write only the segmentation",
                        "step using an established, maintained library and",
                        "its documented API. The input is Y, X, and the pixel",
                        "size is provided in µm per pixel. Do not silently",
                        "resize, normalise, change channels or substitute",
                        "defaults. Expose consequential parameters, fail",
                        "clearly on invalid input, return the label image in",
                        "the original coordinate system, and include a simple",
                        "test. List the assumptions I should verify on real data."], 12.5, fill=INK, lh=17, extra=" " + MONO),
      t(1246, CT + 246, "Then: adversarial check", 13.5, "bold", INK),
      t(1246, CT + 266, ["“Assume that this analysis is scientifically wrong even though",
                         "the code runs. Identify the assumptions most likely to fail…”"], 12.5, fill=BODY, lh=17, extra=" " + MONO)]
c.append(group("Box 1 prompt excerpt", "".join(bx)))
c.append(validate_strip(CT + 346, "C", [
    ["Test code on examples with known outputs; save the", "code, parameters, software, model and LLM versions."],
    ["Keep independent test data inaccessible", "during optimisation."],
    ["Direct multimodal answers are not recommended for quantitative", "analysis without task-specific validation; may not be deterministic."],
], [262, 766, 1150]))
add(group("Panel C", "".join(c)))

# ---------------------------------------------------------------- bottom strip
YS = YC + 552 + 14
s = [rrect(28, 998, 1784, 196, 14, "#eef3f9", "#c8d3e0", 2)]
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
s.append(t(796, 1046, V("(A, B or C, or a combination)", "(classical, A, B, C or a combination)"), 15, fill=BODY, anchor="middle"))
venn = [f'<circle cx="704" cy="1124" r="40" fill="#8a94a3" opacity="0.8" inkscape:label="classical"/>']
for cx, key in [(772, "A"), (830, "B"), (888, "C")]:
    venn.append(f'<circle cx="{cx}" cy="1124" r="40" fill="{C[key]["accent"]}" opacity="0.72"/>')
venn.append(t(704, 1183, "Classical", 14.5, "bold", "#5d6675", "middle"))
for cx, letter in [(778, "A"), (830, "B"), (884, "C")]:
    venn.append(t(cx, 1134, letter, 26, "bold", "#ffffff", "middle"))
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
add(f'<g transform="translate(0 {YS - 998})">' + group("Bottom workflow", "".join(s)) + "</g>")

svg = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
       f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" xmlns:xlink="http://www.w3.org/1999/xlink" '
       f'width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">\n'
       f'<defs>{"".join(defs)}</defs>\n<rect width="{W}" height="{H}" fill="#ffffff"/>\n'
       + "\n".join(out) + "\n</svg>\n")
open("fig1_page.svg", "w", encoding="utf-8").write(svg)
print("written", len(svg) // 1024, "KB; height", H, "bottom strip ends", YS + 196)
