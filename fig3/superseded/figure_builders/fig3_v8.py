# ======================================================================= FIGURE 3 v8: three tasks; rows show scores (before -> after)
import os as _os
R2 = "bf/roi2/"
FS = json.load(open("bf3/fig_scores.json"))["tasks"]
ROI = (0, 0, 260, 260)
DEFC = "#9aa4b2"
CAVF, CAVS = "#fdf0ef", "#efc2be"
CHG = "#6b2c87"
OKT = "#1a7a4c"
BEFC = "#b7c0e3"                               # 'before' bar (light F1 colour); 'after' = F1C
TASKS = [("nuclei", "Nuclei", "DAPI · easy"), ("cancer", "Cancer cells", "brightfield · medium"),
         ("endo", "Endothelial cells", "brightfield · hard")]


def med(v):
    v = [max(x, 0) for x in v if x is not None]
    return float(np.median(v)) if len(v) else None


def change_pill(cx, cy, lines, w=100):
    h = 16 + 15 * len(lines)
    return (f'<path d="M{cx-w/2},{cy-h/2} h{w-12} l12,{h/2} l-12,{h/2} h-{w-12} z" fill="{CHG}"/>'
            + t(cx - 4, cy - h / 2 + 20, lines, 12, "bold", "#ffffff", "middle", lh=15))


def tag(x, y, txt, col="#5b6676"):
    w = 6.9 * len(txt) + 16
    return rrect(x, y - 13, w, 19, 9, "#ffffff", col, 1.1) + t(x + w / 2, y + 1, txt, 11.5, "bold", col, "middle")


# ---------------------------------------------------------------- grid
Y0 = 20
LW_ = 64
RX = 28 + LW_ + 10
RW = 1812 - RX
CX_ASK, W_ASK = RX + 18, 352
CX_SC = CX_ASK + W_ASK + 30                    # score panel: three task groups
GW, GG = 196, 20                               # group width, gap
CX_CAV = CX_SC + 3 * GW + 2 * GG + 30
W_CAV = 1812 - 14 - CX_CAV
GAP = 10


def group_bars(x, y, task, before, after, lb="before", la="after", ref=True):
    """One task group: two bars (median of runs) with the individual runs as dots; × = run that crashed."""
    bw = GW - 46
    g = []
    d = FS[task]["default"]
    for i, (lbl, vals, col) in enumerate([(lb, before, BEFC), (la, after, F1C)]):
        yy = y + 18 + i * 34
        g.append(t(x, yy - 4, lbl, 11.5, "bold" if i else "normal", INK if i else BODY)
                 + f'<rect x="{x}" y="{yy}" width="{bw}" height="10" rx="3" fill="#eef1f5"/>')
        m = med(vals)
        if m is None:
            g.append(t(x + bw + 6, yy + 9, "…", 12.5, "bold", "#7a8699"))
            continue
        g.append(f'<rect x="{x}" y="{yy}" width="{bw*m:.1f}" height="10" rx="3" fill="{col}"/>'
                 + t(x + bw + 6, yy + 9, f"{m:.2f}", 12.5, "bold", INK))
        if len(vals) > 1:
            for v in vals:
                if v is None:
                    continue
                if v < 0:      # crashed run: no labels written
                    g.append(f'<path d="M{x-4:.1f},{yy+1} l8,8 M{x+4:.1f},{yy+1} l-8,8" stroke="{NOC}" stroke-width="2"/>')
                    continue
                g.append(f'<circle cx="{x+bw*v:.1f}" cy="{yy+5}" r="3.2" fill="#ffffff" stroke="{INK}" stroke-width="1.2"/>')
    if ref and d is not None:
        ax = x + bw * d
        g.append(f'<line x1="{ax:.1f}" y1="{y+12}" x2="{ax:.1f}" y2="{y+64}" stroke="{DEFC}" stroke-width="2" stroke-dasharray="3 2"/>')
    return "".join(g)


def score_panel(key, y, before_key, after_key, lb, la, sub=None):
    g = []
    for i, (task, name, _) in enumerate(TASKS):
        x = CX_SC + i * (GW + GG)
        r = FS[task][sub] if sub else None
        b = r["before"] if r else before_key(task)
        a = r["after"] if r else after_key(task)
        g.append(t(x, y, name, 12.5, "bold", INK) + group_bars(x, y + 8, task, b, a, lb, la))
    return "".join(g)


# ---------------------------------------------------------------- header + task row
HDH = 214
add(group("task row", rrect(RX, Y0, RW, HDH, 14, "#ffffff", NN["stroke"], 1.3)
          + t(RX + 18, Y0 + 32, "Three segmentation tasks on one field, from easy to hard", 18.5, "bold", INK)
          + t(RX + 18, Y0 + 54, ["Claude Sonnet, Oct 2026. Every row applies one change from the text;", "bars show object F1 (IoU ≥ 0.5) against manual annotation;",
                                 "median of three runs (open circles: single runs); dashed grey: Cellpose-SAM default.", "Illustration on one field, not a benchmark."], 13, fill=BODY, lh=17)))
TT = 176
for i, (task, name, sub) in enumerate(TASKS):
    x = RX + 560 + i * (TT + 130)
    png = R2 + ("dapi_roi.png" if task == "nuclei" else "bf_roi.png")
    gtk = {"nuclei": "gt_nuclei", "cancer": "gt", "endo": "gt_endo"}[task]
    n = {"nuclei": "441 endothelial nuclei", "cancer": "124 cells", "endo": "382 cells; annotators agree 0.90"}[task]
    d = FS[task]["default"]
    add(group(f"task {task}", real_image(x, Y0 + 16, TT, TT, png, PX, 260, 50, f"task {task}", "#111111")
              + vector_outlines_sub(x, Y0 + 16, TT, TT, R2 + f"{gtk}.json", "manual annotation (vector)", REF, 1.3, DASH, ROI)
              + t(x + TT + 10, Y0 + 34, name, 14, "bold", INK) + t(x + TT + 10, Y0 + 52, [sub], 12, fill=BODY)
              + t(x + TT + 10, Y0 + 84, ["manual:", n if len(n) < 18 else n.split(";")[0]], 12, fill=BODY, lh=15)
              + (t(x + TT + 10, Y0 + 128, ["", ""], 12) if True else "")
              + t(x + TT + 10, Y0 + 132, ["Cellpose", f"default: {d:.2f}" if d is not None else "default: …"], 12, "bold", "#5b6676", lh=15)))
add(key_item(RX + 18, Y0 + HDH - 22, REF, "manual annotation", DASH) + f'<path d="M{RX+190},{Y0+HDH-27} l8,8 M{RX+198},{Y0+HDH-27} l-8,8" stroke="{NOC}" stroke-width="2"/>' + t(RX + 206, Y0 + HDH - 17, "script crashed (counted as F1 0)", 14, fill=BODY))

ORDER = [("a", "Ask for advice", 172), ("b1", "Ask for code: Fiji macro", 168), ("b2", "Ask for code: Python script", 168),
         ("c", "Let an agent run it", 168), ("d", "Ask for the answer", 172)]
ry = {}
yy = Y0 + HDH + GAP
for key, ttl, h in ORDER:
    ry[key] = yy
    yy += h + GAP
RH = {k: h for k, _, h in ORDER}
for key, ttl, h in ORDER:
    y = ry[key]
    add(group(f"row {key}", rrect(RX, y, RW, h, 16, NN["bg"], NN["stroke"], 1.4)
              + f'<circle cx="{CX_ASK+15}" cy="{y+24}" r="15" fill="{ACC}"/>' + t(CX_ASK + 15, y + 30, key[0], 17, "bold", "#fff", "middle")
              + t(CX_ASK + 40, y + 30, ttl, 17, "bold", INK)
              + rrect(CX_CAV - 8, y + 9, W_CAV + 14, h - 18, 12, CAVF, CAVS, 1.2)))


def cav(key, title):
    y = ry[key]
    return caution(CX_CAV + 12, y + 30, NOC) + t(CX_CAV + 32, y + 35, title, 14, "bold", NOC, lh=17)


def ask(key, items, y0=44):
    y = ry[key] + y0
    for tg, lines in items:
        if tg:
            add(t(CX_ASK + 46, y + 2, tg, 11.5, "bold", CHG)); y += 5
        s, h = prompt(CX_ASK, y, W_ASK, lines, 12); add(s); y += h - 4


# ================================================================ a: advice (text only, unchanged message)
key = "a"
ask(key, [("before", ["“Which tool, model and settings would you", "recommend? I don't need code.”"]),
          ("after", ["“…Do not rely on your memory: check the", "current documentation first.”"])])
y = ry[key] + 40
WB = 268
s, hA = reply(CX_SC, y, WB, ["“…either Cellpose-SAM (Cellpose 4)", "or cyto3.” “…try the cyto3 denoise", "or deblur models.”"], 12, False, "From memory"); add(s)
add(t(CX_SC + 4, y + hA + 4, "Offers models removed in Cellpose 4", 12, "bold", NOC))
add(change_pill(CX_SC + WB + 46, y + 44, ["read the", "docs"], 84))
XD = CX_SC + WB + 98
s, hB = reply(XD, y, CX_CAV - 30 - XD, ["“The docs list these built-in models: cpsam_v2,", "cpdino … The old cyto3 and nuclei models", "are not mentioned in the current docs.”"], 12, False, "After reading the docs"); add(s)
add(t(XD + 4, y + hB + 4, "Names the current models and the pages it read", 12, "bold", OKT))
add(cav(key, ["Outdated advice can run without error;", "only the documentation reveals it"]))
s, _ = terminal(CX_CAV + 12, ry[key] + 56, W_CAV - 12, [(">>> CellposeModel(pretrained_model='cyto3')", "#d5dbe5"),
                                                       ("    (no message)  → loads cpsam_v2", "#ff8a80")], 12); add(s)
add(t(CX_CAV + 12, ry[key] + RH[key] - 22, "The default model runs; the result looks normal.", 12.5, fill=INK))

# ================================================================ b1: Fiji macro
key = "b1"
ask(key, [("before", ["“Please write a Fiji macro to segment the", "[nuclei | cancer cells | endothelial cells].”"]),
          ("after: Box 1", ["“…pixel size, object size, check the docs,", "state parameters, test against my annotation…”"])])
add(tag(CX_SC, ry[key] + RH[key] - 14, "runs in Fiji, no setup needed"))
add(score_panel(key, ry[key] + 30, None, None, "generic", "Box 1", sub="fj"))
add(cav(key, ["All macros ran or failed silently;", "only the test shows which"]))
add(t(CX_CAV + 12, ry[key] + 80, ["Endothelial cells: F1 0 in every generic run.", "One macro called a command that does not", "exist (“Set Scaling…”)."], 12.5, fill=INK, lh=17))

# ================================================================ b2: Python script
key = "b2"
ask(key, [("before", ["“Please write a Python script to segment the", "[nuclei | cancer cells | endothelial cells].”"]),
          ("after: Box 1", ["“…pixel size, object size, check the docs,", "state parameters, test against my annotation…”"])])
add(tag(CX_SC, ry[key] + RH[key] - 14, "needs a Python environment with Cellpose (e.g. a notebook)"))
add(score_panel(key, ry[key] + 30, None, None, "generic", "Box 1", sub="py"))
add(cav(key, ["Box 1 exposes the choices; only the", "test shows whether they work"]))
add(t(CX_CAV + 12, ry[key] + 80, ["Same prompt, different runs: object size set", "to 58 px in one script, left at the default", "in another."], 12.5, fill=INK, lh=17))

# ================================================================ c: agent
key = "c"
ask(key, [("before", ["“Please run the analysis pipeline, assess the", "result, improve the analysis…”"]),
          ("after", ["“…Score every version against my annotation…", "other images are held out for a final check.”"])])
add(score_panel(key, ry[key] + 30, None, None, "by eye", "scored", sub="agent"))
add(t(CX_SC, ry[key] + RH[key] - 14, "F1 on the held-out half of the field for both", 11.5, fill="#5b6676"))
add(cav(key, ["Without an external objective, the", "agent judged its result by eye"]))
add(t(CX_CAV + 12, ry[key] + 80, ["Cancer: “about 5 false positives” → 17.", "Endothelial: “match the faint borders well”", "→ F1 0.54, cells 36% too small."], 12.5, fill=INK, lh=17))

# ================================================================ d: answer — counts relative to manual, and drawn outlines
key = "d"
ask(key, [("before · 3 runs", ["“How many [nuclei | cancer cells |", "endothelial cells] are in this image?”"]),
          ("after · 3 runs", ["“Please draw around every … and count them.”"])])
y = ry[key] + 30
for i, (task, name, _) in enumerate(TASKS):
    x = CX_SC + i * (GW + GG)
    dd = FS[task]["draw"]
    man = dd["manual"][0]
    bw = GW - 30
    X = lambda v: x + min(v / man, 1.6) / 1.6 * bw
    g = [t(x, y, name, 12.5, "bold", INK),
         t(x, y + 18, "count / manual", 11, fill=BODY),
         f'<line x1="{x}" y1="{y+34}" x2="{x+bw}" y2="{y+34}" stroke="#c9d1dc" stroke-width="1.2"/>',
         f'<line x1="{X(man):.1f}" y1="{y+24}" x2="{X(man):.1f}" y2="{y+44}" stroke="{INK}" stroke-width="2" stroke-dasharray="3 2"/>']
    if dd["manual"][1] != man:
        g.append(f'<rect x="{X(man):.1f}" y="{y+26}" width="{X(dd["manual"][1])-X(man):.1f}" height="16" fill="{INK}" fill-opacity="0.12"/>')
    for v in dd["asked"] or []:
        g.append(f'<circle cx="{X(v):.1f}" cy="{y+34}" r="4.5" fill="{MCOL["sonnet"]}" stroke="#fff" stroke-width="1"/>')
    for v in dd["drawn"]:
        if v is not None:
            g.append(f'<rect x="{X(v)-4:.1f}" y="{y+30}" width="8" height="8" fill="none" stroke="{ACC}" stroke-width="1.8"/>')
    for fr, lab in [(0, "0"), (1, "1×"), (1.5, "1.5×")]:
        g.append(t(x + fr / 1.6 * bw, y + 56, lab, 10.5, fill="#7a8699", anchor="middle"))
    f1d = [v for v in dd["f1"] if v is not None]
    g.append(t(x, y + 80, f"drawn outlines: F1 {min(f1d):.2f}–{max(f1d):.2f}" if f1d else "drawn: …", 11.5, "bold", INK))
    add(group(f"d {task}", "".join(g)))
add(f'<circle cx="{CX_SC+6}" cy="{ry[key]+RH[key]-20}" r="4.5" fill="{MCOL["sonnet"]}"/>' + t(CX_SC + 15, ry[key] + RH[key] - 16, "number only", 11.5, fill=BODY)
    + f'<rect x="{CX_SC+108}" y="{ry[key]+RH[key]-24}" width="8" height="8" fill="none" stroke="{ACC}" stroke-width="1.8"/>' + t(CX_SC + 121, ry[key] + RH[key] - 16, "cells it drew", 11.5, fill=BODY))
add(cav(key, ["The outlines showed the numbers were", "estimated, not counted"]))
add(t(CX_CAV + 12, ry[key] + 80, ["Even for nuclei it drew 40–100 hexagons and", "called them “partial”; asked for a number:", "430–480."], 12.5, fill=INK, lh=17))

# ================================================================ delegation arrow
AT, AB = ry["a"], ry["d"] + RH["d"]
defs.append(f'<linearGradient id="deleg" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#d9cbea"/><stop offset="1" stop-color="{ACC}"/></linearGradient>')
AXc = 28 + LW_ / 2
add(group("delegation arrow", f'<path d="M{AXc-20},{AT} H{AXc+20} V{AB-26} H{AXc+30} L{AXc},{AB} L{AXc-30},{AB-26} H{AXc-20} Z" fill="url(#deleg)"/>'
          + f'<text x="{AXc+6}" y="{(AT+AB)/2}" font-size="15" font-weight="bold" fill="#ffffff" text-anchor="middle" '
            f'transform="rotate(-90 {AXc+6} {(AT+AB)/2})">more of the analysis happens inside the LLM interaction</text>'))

# ================================================================ what to keep
KY = ry["d"] + RH["d"] + GAP
KH = 100
add(group("keep frame", rrect(28, KY, 1784, KH, 16, "#ffffff", NN["stroke"], 1.4)
          + t(48, KY + 28, "Regardless of the level of delegation, test quantitative use on representative images with reference outputs", 16.5, "bold", INK)))
KEEP = [("lock", "Check how the service handles data", "approved services or local models"),
        ("check", "Verify advice against the docs", "for the version you use"),
        ("ruler", "Ask it to expose parameters", "defaults and transformations (Box 1)"),
        ("target", "Give agents an external objective", "and keep held-out data separate"),
        ("file", "Request inspectable outputs", "masks or locations, not only a number")]
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


for i, (ic, a_, b_) in enumerate(KEEP):
    x = 48 + i * KW
    add(group(f"keep {a_}", kicon(ic, x + 20, KY + 66, ACC) + t(x + 48, KY + 62, a_, 14, "bold", INK) + t(x + 48, KY + 82, b_, 12.5, fill=BODY)))

H = KY + KH + 20
svg = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
       f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" xmlns:xlink="http://www.w3.org/1999/xlink" '
       f'width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">\n'
       f'<defs>{"".join(defs)}</defs>\n<rect width="{W}" height="{H}" fill="#ffffff"/>\n'
       + "\n".join(out) + "\n</svg>\n")
open("fig3_v8.svg", "w", encoding="utf-8").write(svg)
print("written", len(svg) // 1024, "KB; height", H)
