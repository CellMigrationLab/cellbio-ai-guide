# ======================================================================= FIGURE 3 v9: three tasks; scores + counts per row; minimal text
import os as _os
A3 = "bf3/fig_assets/"
FSJ = json.load(open("bf3/fig_scores.json"))
FS = FSJ["tasks"]
MAN = FSJ["manual"]
DEFC = "#9aa4b2"
CAVF, CAVS = "#fdf0ef", "#efc2be"
CHG = "#6b2c87"
OKT = "#1a7a4c"
BEFC = "#b7c0e3"
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


def group(x, y, task, b, a, bn, an, lb, la, manual=None):
    """Two bars (median F1 of runs; open circles = runs; x = crashed) + median object count vs manual."""
    bw = GW - 150
    g = []
    d = FS[task]["default"]
    manual = manual or MAN[task]
    for i, (lbl, vals, ns, col) in enumerate([(lb, b, bn, BEFC), (la, a, an, F1C)]):
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
                 + group(x, y + 14, task, r["before"], r["after"], r.get("before_n", [None]), r.get("after_n", [None]), lb, la, manual))
    return "".join(g)


# ---------------------------------------------------------------- task row: original image + desired result (full field)
TT = 232
HDH = TT + 70
add(group_svg := None) if False else None
row = [rrect(RX, Y0, RW, HDH, 14, "#ffffff", NN["stroke"], 1.3)]
for i, (task, name, mod) in enumerate(TASKS):
    x = RX + 20 + i * (2 * TT + 8 + 48)
    src = A3 + ("dapi_full.png" if task == "nuclei" else "bf_full.png")
    row.append(t(x, Y0 + 30, f"{name}", 17, "bold", INK) + t(x + 2 * TT + 8, Y0 + 30, f"{mod} · manual n = {MAN[task]}", 13, fill=BODY, anchor="end"))
    row.append(img(x, Y0 + 44, TT, TT, src, f"{task} image") + img(x + TT + 8, Y0 + 44, TT, TT, A3 + f"labels_{task}.png", f"{task} manual labels"))
    row.append(halo(x + 6, Y0 + 62, "image", size=12.5) + halo(x + TT + 14, Y0 + 62, "desired result (manual)", size=12.5))
add("".join(row))

ORDER = [("a", "Ask for advice", 156), ("b1", "Ask for code: Fiji macro", 134), ("b2", "Ask for code: Python script", 134),
         ("c", "Let an agent run it", 134), ("d", "Ask for the answer", 150)]
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
key = "b1"
ask(key, [("before", ["“Please write a Fiji macro to segment the …”"]), ("after", ["Box 1 prompt"])])
add(panel(key, ry[key] + 34, "fj", "generic", "Box 1"))
add(cav(key, ["Code that runs is not code that works:", "test it against annotation"]))

key = "b2"
ask(key, [("before", ["“Please write a Python script to segment the …”"]), ("after", ["Box 1 prompt"])])
add(panel(key, ry[key] + 34, "py", "generic", "Box 1"))
add(cav(key, ["Box 1 makes the settings visible;", "only the test shows if they work"]))

key = "c"
ask(key, [("before", ["“…run the pipeline, assess, improve…”"]), ("after", ["“…score every version against my annotation…”"])])
add(panel(key, ry[key] + 34, "agent", "by eye", "scored", half=True))
add(cav(key, ["By eye it had no score to check;", "scored, its reported F1 held", "on the held-out half"]))
_rep = [(FS[tk]["agent"]["dev_reported"], FS[tk]["agent"]["after"][0]) for tk, _, _ in TASKS]
add(t(CX_CAV + 36, ry[key] + 116, ["reported → held-out F1: " + "  ·  ".join(
    "…" if a is None or b is None else f"{a + 1e-9:.2f} → {b:.2f}" for a, b in _rep)], 11.5, "normal", "#5b6270"))

key = "d"
ask(key, [("before", ["“How many … are in this image?”"]), ("after", ["“Draw around every … and count them.”"])])
y = ry[key] + 34
for i, (task, name, _) in enumerate(TASKS):
    x = CX_SC + i * (GW + GG)
    dd = FS[task]["draw"]
    man = MAN[task]
    bw = GW - 20
    X = lambda v: x + min(v / man, 1.6) / 1.6 * bw
    gg = [t(x, y, name, 13.5, "bold", INK) + t(x + GW - 6, y, f"manual n={man}", 11.5, fill="#5b6676", anchor="end"),
          f'<line x1="{x}" y1="{y+30}" x2="{x+bw}" y2="{y+30}" stroke="#c9d1dc" stroke-width="1.2"/>',
          f'<line x1="{X(man):.1f}" y1="{y+18}" x2="{X(man):.1f}" y2="{y+42}" stroke="{INK}" stroke-width="2" stroke-dasharray="3 2"/>']
    for v in dd["asked"] or []:
        gg.append(f'<circle cx="{X(v):.1f}" cy="{y+30}" r="5" fill="{MCOL["sonnet"]}" stroke="#fff" stroke-width="1"/>')
    for v in dd["drawn"]:
        if v is not None:
            gg.append(f'<rect x="{X(v)-4.5:.1f}" y="{y+25.5}" width="9" height="9" fill="none" stroke="{ACC}" stroke-width="2"/>')
    for fr, lab in [(0, "0"), (1, "manual"), (1.5, "1.5×")]:
        gg.append(t(x + fr / 1.6 * bw, y + 56, lab, 11, fill="#7a8699", anchor="middle"))
    f1d = [v for v in dd["f1"] if v is not None]
    gg.append(t(x, y + 80, f"F1 of drawn outlines: {min(f1d):.2f}–{max(f1d):.2f}" if f1d else "", 12.5, "bold", INK))
    add("".join(gg))
add(f'<circle cx="{CX_SC+6}" cy="{ry[key]+RH[key]-18}" r="5" fill="{MCOL["sonnet"]}"/>' + t(CX_SC + 16, ry[key] + RH[key] - 14, "count, number only", 12, fill=BODY)
    + f'<rect x="{CX_SC+150}" y="{ry[key]+RH[key]-22.5}" width="9" height="9" fill="none" stroke="{ACC}" stroke-width="2"/>' + t(CX_SC + 165, ry[key] + RH[key] - 14, "count of cells it drew", 12, fill=BODY))
add(cav(key, ["The numbers were estimated,", "not counted"]))

# ---------------------------------------------------------------- key line under task row: F1 legend
add(t(CX_SC, ry["b1"] - 2, "", 1))

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
        ("ruler", "Ask it to expose parameters (Box 1)"), ("target", "Give agents an external objective"),
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

H = KY + KH + 20
svg = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
       f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" xmlns:xlink="http://www.w3.org/1999/xlink" '
       f'width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">\n'
       f'<defs>{"".join(defs)}</defs>\n<rect width="{W}" height="{H}" fill="#ffffff"/>\n'
       + "\n".join(out) + "\n</svg>\n")
open("fig3_v9.svg", "w", encoding="utf-8").write(svg)
print("written", len(svg) // 1024, "KB; height", H)
