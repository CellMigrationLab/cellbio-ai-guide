
# ================================================================ Fig. 1 v5: rows B (LLM) and C (start a project)
NN = C["N"]


def card(x, y, w, h, title, key="N"):
    k = C[key]
    return rrect(x, y, w, h, 12, k["bg"], k["stroke"], 1.8) + t(x + w / 2, y + 27, title, 18, "bold", k["accent"], "middle")


def row_frame(y, h, L, title, key="N"):
    k = C[key]
    return (rrect(28, y, 1784, h, 16, NN["bg"], NN["stroke"], 2)
            + f'<circle cx="70" cy="{y+38}" r="22" fill="{NN["accent"]}"/>' + t(70, y + 47, L, 25, "bold", "#fff", "middle")
            + t(106, y + 46, title, 24, "bold", INK))


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


# ---------------- row B: LLM uses + example
Y2 = YO + RO + 10
HB = 66 + 38 + 200 + 34 + 16
bB = [row_frame(Y2, HB, "B", "Large language models in the analysis")]
CT2 = Y2 + 66
k = C["C"]
# four uses
UW, UG = 192, 10
ux0 = 44
uses = [("advise", "Ask for advice", ["tools, parameters,", "strategies"]),
        ("code", "Ask for code", ["code you run", "and test"]),
        ("run", "Let an agent run", ["executes and", "optimises the workflow"]),
        ("answer", "Ask for the answer", ["multimodal model", "inspects the image"])]
WU = 4 * UW + 3 * UG
bB.append(rrect(ux0, CT2, WU + 28, 38 + 200 + 34, 12, k["bg"], k["stroke"], 1.8)
          + t(ux0 + (WU + 28) / 2, CT2 + 27, "Four ways to use an LLM", 18, "bold", k["accent"], "middle"))
for i, (nm, ttl, sub) in enumerate(uses):
    x = ux0 + 14 + i * (UW + UG)
    bB.append(rrect(x, CT2 + 40, UW, 150, 10, "#ffffff", k["tintstroke"], 1.5))
    bB.append(t(x + 22, CT2 + 62, str(i + 1), 15, "bold", k["accent"], "middle"))
    bB.append(group(f"icon {nm}", ico(nm, x + UW / 2, CT2 + 92, k["accent"])))
    bB.append(t(x + UW / 2, CT2 + 140, ttl, 15, "bold", INK, "middle"))
    bB.append(t(x + UW / 2, CT2 + 158, sub, 12.5, fill=BODY, anchor="middle", lh=15))
# gradient: more of the analysis is delegated, more decisions can be hidden (text: "When AI builds or runs the analysis")
gid = "llmgrad"
defs.append(f'<linearGradient id="{gid}" x1="0" x2="1" y1="0" y2="0"><stop offset="0" stop-color="#8fb3e0"/>'
            f'<stop offset="1" stop-color="{k["accent"]}"/></linearGradient>')
gy = CT2 + 204
bB.append(f'<path d="M{ux0+14},{gy} H{ux0+14+WU-14} L{ux0+14+WU},{gy+13} L{ux0+14+WU-14},{gy+26} H{ux0+14} Z" fill="url(#{gid})"/>'
          + t(ux0 + 24, gy + 18, "more of the analysis delegated, more decisions hidden", 13.5, "bold", "#ffffff"))
bB.append(t(ux0 + 14 + WU / 2, gy + 50, "Validate each use differently: from checking documentation (1) to reference data (4)",
            12.5, fill=BODY, anchor="middle"))
# example: asking for code (real, from preparing this figure)
ex0 = ux0 + WU + 28 + 16
EW = 1796 - ex0
bB.append(arrow(ux0 + WU + 28 + 2, CT2 + 120, ex0 - 3, CT2 + 120, k["accent"], 2.5))
bB.append(rrect(ex0, CT2, EW, 38 + 200 + 34, 12, k["bg"], k["stroke"], 1.8)
          + t(ex0 + EW / 2, CT2 + 27, "Example (2): what did the LLM decide?", 18, "bold", k["accent"], "middle"))
_keep = WS
WS = 200
wx0 = ex0 + (EW - 3 * WS - 2 * 14) / 2
for j_, w_ in enumerate(LLM_WIDGETS):
    wx_, wy_ = wx0 + j_ * (WS + 14), CT2 + 40
    bB.append(draw_widget(w_, wx_, wy_))
    bB.append(t(wx_ + WS / 2, wy_ + WS + 24, w_[-1], 15, "bold", INK, "middle"))
for j_ in range(2):
    bx_, by_ = wx0 + j_ * (WS + 14) + WS + 7, CT2 + 40 + WS / 2
    bB.append(f'<circle cx="{bx_}" cy="{by_}" r="9" fill="{k["accent"]}" stroke="#ffffff" stroke-width="2"/>'
              f'<path d="M{bx_-3},{by_-4} L{bx_+2.5},{by_} L{bx_-3},{by_+4}" fill="none" stroke="#ffffff" stroke-width="2.2" '
              f'stroke-linecap="round" stroke-linejoin="round"/>')
WS = _keep
add(group("Panel B LLM", "".join(bB)))

# ---------------- row C: start an image-analysis project (whole pipeline, one row, real images)
Y3 = Y2 + HB + 10
HCR = 66 + 250 + 16
cC_ = [row_frame(Y3, HCR, "C", "Start an image-analysis project")]
CT3 = Y3 + 66
IS = 150                                   # thumbnail size
steps = 7
SW_ = (1752 - (steps - 1) * 22) / steps    # step width
TITLES = ["Question and\nmeasurement", "Representative\nimages", "Reference\nannotations", "Development and\nheld-out test sets",
          "Choose and compare\napproaches", "Validate on the\nheld-out test set", "Measure and\nconclude"]
SUBS = ["what will you measure?", "include the variation", "references, not\nground truth",
        "never tune on the test set", "classical, DL, LLM", "errors that matter", "across biological repeats"]
for i in range(steps):
    sx = 44 + i * (SW_ + 22)
    cx = sx + SW_ / 2
    ty = CT3 + 16
    cC_.append(t(cx, ty, TITLES[i].split("\n"), 14.5, "bold", INK, "middle", lh=17))
    iy = CT3 + 54
    ix = cx - IS / 2
    if i == 0:   # question
        cC_.append(rrect(ix - 6, iy, IS + 12, IS, 12, "#ffffff", "#9fb3cc", 1.6)
                   + t(ix + 6, iy + 30, ["How many cancer", "cells attach to the", "endothelium?"], 13.5, fill=INK, lh=17)
                   + t(ix + 6, iy + 104, ["Measurement:", "cell count per field"], 13, fill=BODY, lh=16))
    elif i == 1:  # three different fields
        for k_ in range(3):
            cC_.append(real_image(ix + k_ * 14 - 14, iy + k_ * 12, IS - 14, IS - 14, f"data8/rep{k_}.png", PX * 260 / 300, 300, 50,
                                  f"representative field {k_}", "#111111").replace('stroke="#111111" stroke-width="2.5"', 'stroke="none" stroke-width="0"'))
            cC_.append(rrect(ix + k_ * 14 - 14, iy + k_ * 12, IS - 14, IS - 14, 2, "none", "#ffffff", 1.2))
    elif i == 2:  # reference annotations
        cC_.append(real_image(ix, iy, IS, IS * 260 / 240, "data4/B_rep_bf.png", PX, 240, 50, "reference annotation", "#111111"))
        cC_.append(vector_outlines_sub(ix, iy, IS, IS * 260 / 240, "data4/B_rep_ref.json", "manual reference (vector)", REF, 1.5, DASH, (0, 0, 240, 260)))
    elif i == 3:  # dev / test split
        cid_ = clip(ix, iy, IS, IS, 2)
        data_ = base64.b64encode(open("data8/field.png", "rb").read()).decode()
        g_ = [f'<g clip-path="url(#{cid_})"><image x="{ix}" y="{iy}" width="{IS}" height="{IS}" xlink:href="data:image/png;base64,{data_}"/>']
        TEST = {(0, 3), (1, 1), (2, 2), (3, 0)}
        for r_ in range(4):
            for c_ in range(4):
                col_ = "#d08a1f" if (r_, c_) in TEST else "#3d74c6"
                g_.append(f'<rect x="{ix+c_*IS/4+1:.1f}" y="{iy+r_*IS/4+1:.1f}" width="{IS/4-2:.1f}" height="{IS/4-2:.1f}" fill="{col_}" '
                          f'fill-opacity="{0.42 if (r_, c_) in TEST else 0.18}" stroke="{col_}" stroke-width="1.6"/>')
        g_.append("</g>")
        cC_.append("".join(g_))
        cC_.append(f'<rect x="{ix}" y="{iy+IS+8}" width="12" height="12" fill="#3d74c6" fill-opacity="0.5"/>' + t(ix + 17, iy + IS + 18, "development", 12, fill=BODY)
                   + f'<rect x="{ix+92}" y="{iy+IS+8}" width="12" height="12" fill="#d08a1f" fill-opacity="0.7"/>' + t(ix + 109, iy + IS + 18, "test", 12, fill=BODY))
    elif i == 4:  # approaches
        vcx, vcy = cx, iy + 58
        ven = []
        for dx, colr in [(-45, "#8a94a3"), (-15, C["A"]["accent"]), (15, C["B"]["accent"]), (45, C["C"]["accent"])]:
            ven.append(f'<circle cx="{vcx+dx}" cy="{vcy}" r="30" fill="{colr}" opacity="0.72"/>')
        cC_.append(group("approach circles", "".join(ven)))
        cC_.append(t(cx, iy + 112, ["compare 2-3 candidates", "on the development set"], 13, fill=INK, anchor="middle", lh=16))
    elif i == 5:  # validate on test
        cC_.append(real_image(ix, iy, IS, IS * 260 / 240, "data4/B_rep_bf.png", PX, 240, 50, "validation tile", "#111111"))
        cC_.append(vector_outlines_sub(ix, iy, IS, IS * 260 / 240, "data4/B_rep_ref.json", "reference (vector)", REF, 1.4, DASH, (0, 0, 240, 260)))
        cC_.append(vector_outlines_sub(ix, iy, IS, IS * 260 / 240, "data4/B_rep_stardist.json", "model (vector)", MODEL, 1.4, None, (0, 0, 240, 260)))
    elif i == 6:  # conclude (schematic)
        bars = [f'<line x1="{ix+14}" y1="{iy+10}" x2="{ix+14}" y2="{iy+130}" stroke="{INK}" stroke-width="1.6"/>',
                f'<line x1="{ix+14}" y1="{iy+130}" x2="{ix+IS-6}" y2="{iy+130}" stroke="{INK}" stroke-width="1.6"/>']
        rng_ = random.Random(5)
        for g_i, (mx, my, colr) in enumerate([(ix + 50, iy + 86, "#3d74c6"), (ix + 110, iy + 46, "#c96a28")]):
            for _ in range(22):
                bars.append(f'<circle cx="{mx+rng_.uniform(-16,16):.1f}" cy="{my+rng_.gauss(0,14):.1f}" r="2.2" fill="{colr}" opacity="0.4"/>')
            for r_, dy in enumerate((-5, 3, 8)):
                bars.append(f'<circle cx="{mx-12+r_*12}" cy="{my+dy}" r="5" fill="{colr}" stroke="{INK}" stroke-width="1.2"/>')
        cC_.append(group("conclusion schematic (repeat means)", "".join(bars)))
    cC_.append(t(cx, CT3 + 236, SUBS[i].split("\n"), 12.5, fill=BODY, anchor="middle", lh=15))
    if i < steps - 1:
        cC_.append(arrow(sx + SW_ + 2, iy + IS / 2, sx + SW_ + 20, iy + IS / 2, "#4a5568", 2.4))
add(group("Panel C start a project", "".join(cC_)))
H = Y3 + HCR + 14
