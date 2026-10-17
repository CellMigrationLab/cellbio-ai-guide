
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
b2.append(card(44, Y2, CWB, H2, "Build or run the analysis (LLM)", "C"))
_badges = []
for j_, w_ in enumerate(LLM_WIDGETS):
    wx_, wy_ = 44 + PADX + j_ * (WS + GAP), Y2 + 38
    b2.append(draw_widget(w_, wx_, wy_))
    b2.append(t(wx_ + WS / 2, wy_ + WS + 24, w_[-1], 15, "bold", INK, "middle"))
    if j_ < 2:
        bx_, by_ = wx_ + WS + GAP / 2, wy_ + WS / 2
        _badges.append(f'<circle cx="{bx_}" cy="{by_}" r="9" fill="{C["C"]["accent"]}" stroke="#ffffff" stroke-width="2"/>'
                       f'<path d="M{bx_-3},{by_-4} L{bx_+2.5},{by_} L{bx_-3},{by_+4}" fill="none" stroke="#ffffff" stroke-width="2.2" '
                       f'stroke-linecap="round" stroke-linejoin="round"/>')
b2 += _badges
xC = 44 + CWB + 10
WC = 1796 - xC
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
    c2.append(t(ix + IMS / 2, Y2 + 38 + IMS + 24, ["Acquire representative", "images"][0] if k_ == 0 else "", 15, "bold", INK, "middle"))
c2[-2] = c2[-2]  # (labels below)
c2.append(t(ax0 + IMS + 5, Y2 + 38 + IMS + 24, "Acquire representative images", 15, "bold", INK, "middle"))
# approach
vx = ax0 + 2 * IMS + 10 + 36
c2.append(arrow(ax0 + 2 * IMS + 16, qy + 75, vx - 6, qy + 75, "#4a5568", 2.5))
vcx = vx + 120
ven = []
for dx, colr in [(-62, "#8a94a3"), (-20, C["A"]["accent"]), (22, C["B"]["accent"]), (64, C["C"]["accent"])]:
    ven.append(f'<circle cx="{vcx+dx}" cy="{qy+70}" r="38" fill="{colr}" opacity="0.72"/>')
for dx, word in [(-66, "Classical"), (-14, "DL"), (24, ""), (68, "LLM")]:
    if word:
        ven.append(t(vcx + dx, qy + 75, word, 12.5, "bold", "#ffffff", "middle"))
c2.append(group("approach circles", "".join(ven)))
c2.append(t(vcx, Y2 + 38 + IMS + 24, "Choose the approach", 15, "bold", INK, "middle"))
c2.append(t(vcx, qy + 135, ["Start with an established", "approach; compare candidates", "on reference examples"], 13, fill=BODY, anchor="middle", lh=16))

# ---------------- row 3: D (conclude)
Y3 = Y2 + H2 + 10
H3 = 340
d3 = [card(44, Y3, 1752, H3, "Validate, then conclude from a reliable measurement")]
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
px0, py0, pw, ph = lx + 360, Y3 + 72, 300, 210
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
        jx = cx + (r - 2) * 22 + rng_.uniform(-8, 8)
        sp.append(f'<circle cx="{jx:.1f}" cy="{vy:.1f}" r="2.3" fill="{CT_COLS[c]}" opacity="0.45"/>')
    for cc, r, m in CP["superplot"]["means"]:
        if cc == c:
            sp.append(marker(SH[r], cx + (r - 2) * 22, py0 + ph - m / YMAX * ph, 6, CT_COLS[c]))
    sp.append(t(cx, py0 + ph + 18, CT_NAME[c], 12.5, fill=INK, anchor="middle"))
# repeat key
for k_, r in enumerate((1, 2, 3)):
    kx = px0 + 40 + k_ * 86
    sp.append(marker(SH[r], kx, py0 + ph + 42, 5, "#ffffff") + t(kx + 10, py0 + ph + 46, f"repeat {r}", 12, fill=BODY))
d3.append(group("SuperPlot aspect ratio", "".join(sp)))

# p-value heatmap: -log10(Bonferroni p) per feature and comparison
hx0, hy0 = px0 + pw + 140, Y3 + 72
FEATS = CP["features"]
FN = {"Perim.": "Perimeter", "Circ.": "Circularity", "AR": "Aspect ratio", "Round": "Roundness", "MinFeret": "Min Feret",
      "Major": "Major axis", "Minor": "Minor axis"}
cwh, chh = 64, 21
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
hm.append(t(hx0 + cwh, hy0 + len(FEATS) * chh + 32, "vs control", 12, fill=BODY, anchor="middle"))
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
qx0, qy0, qw, qh = cbx + 120, Y3 + 72, 250, 210
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
    kx = qx0 + k_ * 88
    pc.append(f'<circle cx="{kx+6}" cy="{qy0+qh+42}" r="5" fill="{CT_COLS[c]}"/>' + t(kx + 15, qy0 + qh + 46, CT_NAME[c], 12, fill=BODY))
d3.append(group("PCA", "".join(pc)))

add(group("Panel B LLM", letter(44 + 6, Y2 + 6, "B", "C") + "".join(b2)))
add(group("Panel C start a project", "".join(c2) + letter(xC + 6, Y2 + 6, "C")))
add(group("Panel D conclude", "".join(d3) + letter(50, Y3 + 6, "D")))
H = Y3 + H3 + 20
