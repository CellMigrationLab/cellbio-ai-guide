# ======================================================================= FIGURE 3 v5: two targets, four uses (drafts A/B/C)
VAR = os.environ.get("VAR", "A")
BF = "bf/"
S = json.load(open("bf2/all_scores.json"))
ROI = (0, 0, 260, 260)
DEFC = "#9aa4b2"
CAVF, CAVS = "#fdf0ef", "#efc2be"
CC, EC = "#1f8a70", "#2563a8"          # small target tags: cancer (teal), endothelial (blue) — text only
TGT = {"cancer": "cancer cells", "endo": "endothelial cells"}


def f(k):
    return S[k]["f1"] if k in S else None


def tile(x, y, w, key, gt, label, cap=None, cap2=None):
    g = [real_image(x, y, w, w, BF + "roi2/bf_roi.png", PX, 260, 50 if w > 170 else 0, label, "#111111")]
    g.append(vector_outlines_sub(x, y, w, w, BF + f"roi2/{gt}.json", "manual annotation (vector)", REF, 1.3, DASH, ROI))
    g.append(vector_outlines_sub(x, y, w, w, BF + f"roi2/{key}.json", f"{label} (vector)", MODEL, 1.6, None, ROI))
    if cap:
        g.append(halo(x + 6, y + 17, cap, size=12.5))
    if cap2:
        g.append(t(x, y + w + 15, cap2, 12, fill="#6b2c87", style="italic"))
    return group(label, "".join(g))


def bars(x, y, w, groups):
    """Fig. 1/2 style F1 bars, grouped by target; grey = Cellpose-SAM default; tick = agreement between annotators."""
    g = [t(x, y, "F1", 13.5, "bold", INK)]
    yy = y + 8
    LW = 108
    bw = w - LW - 40
    for tg, items in groups:
        yy += 18
        g.append(t(x, yy, TGT[tg], 12.5, "bold", CC if tg == "cancer" else EC))
        for lbl, k in [("default", f"default_{tg}")] + items:
            yy += 17
            v = f(k)
            g.append(t(x + 6, yy, lbl, 12, fill=BODY))
            g.append(f'<rect x="{x+LW}" y="{yy-8}" width="{bw}" height="7" rx="2.5" fill="#e4e8ee"/>')
            if v is not None:
                g.append(f'<rect x="{x+LW}" y="{yy-8}" width="{bw*v:.1f}" height="7" rx="2.5" fill="{DEFC if lbl == "default" else F1C}"/>'
                         + t(x + LW + bw + 5, yy, f"{v:.2f}", 12, "bold", INK))
        if tg == "endo":
            ax = x + LW + bw * S["annot_endo"]["f1"]
            g.append(f'<line x1="{ax:.1f}" y1="{yy-17*(len(items)+1)-6}" x2="{ax:.1f}" y2="{yy+2}" stroke="{INK}" stroke-width="1.2" stroke-dasharray="2 2"/>')
    return "".join(g), yy - y


def dots(x, y, w, groups):
    """Variant C: one 0–1 axis per target; grey diamond = default; dots = variants (labelled)."""
    g = [t(x, y, "F1", 13.5, "bold", INK)]
    ax0, ax1 = x + 96, x + w - 10
    X = lambda v: ax0 + v * (ax1 - ax0)
    yy = y + 4
    for tg, items in groups:
        yy += 50
        g.append(t(x, yy + 4, TGT[tg].replace(" cells", ""), 12.5, "bold", CC if tg == "cancer" else EC))
        g.append(f'<line x1="{ax0}" y1="{yy}" x2="{ax1}" y2="{yy}" stroke="#c9d1dc" stroke-width="1.2"/>')
        d = f(f"default_{tg}")
        g.append(f'<path d="M{X(d):.1f},{yy-6} l6,6 l-6,6 l-6,-6 z" fill="{DEFC}"/>')
        if tg == "endo":
            g.append(f'<line x1="{X(0.897):.1f}" y1="{yy-9}" x2="{X(0.897):.1f}" y2="{yy+9}" stroke="{INK}" stroke-width="1.2" stroke-dasharray="2 2"/>')
        for i, (lbl, k) in enumerate(items):
            v = f(k)
            up = i % 2 == 0
            g.append(f'<circle cx="{X(v):.1f}" cy="{yy}" r="5.5" fill="{F1C}" stroke="#fff" stroke-width="1"/>'
                     + t(X(v), yy - 11 if up else yy + 20, f"{lbl} {v:.2f}", 11.5, fill=INK, anchor="middle"))
    for v in (0, 0.5, 1):
        g.append(t(X(v), yy + 36, f"{v:g}", 11, fill="#7a8699", anchor="middle"))
    return "".join(g), yy + 36 - y


# ---------------------------------------------------------------- grid
Y0 = 20
LW_ = 64
RX = 28 + LW_ + 10
RW = 1812 - RX
CX_ASK, W_ASK = RX + 18, 372
TS = {"A": 196, "B": 138, "C": 226}[VAR]
NT = {"A": 2, "B": 4, "C": 2}[VAR]
TG = 10
CX_RES = CX_ASK + W_ASK + 20
W_RES = NT * TS + (NT - 1) * TG
CX_F1 = CX_RES + W_RES + 22
W_F1 = {"A": 262, "B": 250, "C": 250}[VAR]
CX_CAV = CX_F1 + W_F1 + 22
W_CAV = 1812 - 14 - CX_CAV
RH = TS + 104 if VAR != "B" else 250
GAP = 12

HDH = 84
add(group("task", rrect(RX, Y0, RW, HDH, 14, "#ffffff", NN["stroke"], 1.3)
          + real_image(RX + 12, Y0 + 9, 66, 66, BF + "draw/bf_full.png", PX, 1024, 0, "task: full field")
          + rrect(RX + 12 + 760 / 1024 * 66, Y0 + 9 + 240 / 1022 * 66, 260 / 1024 * 66, 260 / 1022 * 66, 0, "none", REF2, 1.6)
          + t(RX + 94, Y0 + 34, "Two tasks on one brightfield field: segment the cancer cells (easy) and the endothelial cells (hard)", 18.5, "bold", INK)
          + t(RX + 94, Y0 + 60, "Claude Sonnet, 16–17 Oct 2026 · tiles: magnified region (yellow box) · F1 vs manual annotation (124 cancer, 382 endothelial cells)", 13.5, fill=BODY)
          + key_item(1812 - 560, Y0 + 30, MODEL, "LLM-derived result") + key_item(1812 - 400, Y0 + 30, REF, "manual annotation", DASH)
          + f'<rect x="{1812-230}" y="{Y0+24}" width="20" height="7" rx="2.5" fill="{DEFC}"/>' + t(1812 - 204, Y0 + 32, "Cellpose-SAM default", 13, fill=BODY)
          + f'<line x1="{1812-560+11}" y1="{Y0+50}" x2="{1812-560+11}" y2="{Y0+66}" stroke="{INK}" stroke-width="1.2" stroke-dasharray="2 2"/>'
          + t(1812 - 560 + 28, Y0 + 63, "agreement between two annotators (endothelial, 0.90)", 13, fill=BODY)))

rows_y = [Y0 + HDH + GAP + k * (RH + GAP) for k in range(4)]
HEADS = [("a", "Ask for advice"), ("b", "Ask for code"), ("c", "Let an agent run it"), ("d", "Ask for the answer")]
for k, (L, ttl) in enumerate(HEADS):
    y = rows_y[k]
    add(group(f"row {L}", rrect(RX, y, RW, RH, 16, NN["bg"], NN["stroke"], 1.4)
              + f'<circle cx="{CX_ASK+15}" cy="{y+26}" r="15" fill="{ACC}"/>' + t(CX_ASK + 15, y + 32, L, 17, "bold", "#fff", "middle")
              + t(CX_ASK + 40, y + 32, ttl, 18.5, "bold", INK)
              + rrect(CX_CAV - 8, y + 10, W_CAV + 14, RH - 20, 12, CAVF, CAVS, 1.2)))


def cav_title(k, lines):
    y = rows_y[k]
    return caution(CX_CAV + 12, y + 32, NOC) + t(CX_CAV + 32, y + 37, lines, 14.5, "bold", NOC, lh=18)


def ask(k, items):
    """items: (tag, lines). Small tag above each prompt bubble."""
    y = rows_y[k] + 50
    for tag, lines in items:
        if tag:
            add(t(CX_ASK + 46, y + 2, tag, 12, "bold", "#6b2c87")); y += 6
        s, h = prompt(CX_ASK, y, W_ASK, lines, 13); add(s); y += h


def tiles(k, spec):
    y = rows_y[k] + 46
    for i, (key, gt, lbl, cap, cap2) in enumerate(spec):
        add(tile(CX_RES + i * (TS + TG), y, TS, key, gt, lbl, cap, cap2 if VAR != "B" else None))


def score(k, groups):
    y = rows_y[k] + 46
    s, _ = (dots if VAR == "C" else bars)(CX_F1, y, W_F1, groups)
    add(s)


# ================================================================ a: advice — memory vs checking the docs
k = 0
ask(k, [("from memory", ["“Which tool, model and settings would you", "recommend? I don't need code.”"]),
        ("checking the docs", ["“…Do not rely on your memory: check the", "current documentation first.”"])])
A_T = [("aG_endo", "gt_endo", "advice from memory, endothelial", "memory", "“set the diameter to about 60 to 80 px”"),
       ("aS_endo", "gt_endo", "advice after docs, endothelial", "docs", "“Try leaving it unset first.”")]
if VAR == "B":
    A_T = [("aG_cancer", "gt", "memory, cancer", "memory · cancer", None), ("aS_cancer", "gt", "docs, cancer", "docs · cancer", None)] + \
          [(a, b, c, d.replace("memory", "memory · endo").replace("docs", "docs · endo"), e) for a, b, c, d, e in A_T]
tiles(k, A_T)
score(k, [("cancer", [("memory", "adviceG_cancer"), ("docs", "adviceS_cancer")]),
          ("endo", [("memory", "adviceG_endo"), ("docs", "adviceS_endo")])])
add(cav_title(k, ["Checking the docs fixed the model name,", "not the method"]))
y = rows_y[k]
s, _ = terminal(CX_CAV + 12, y + 66, W_CAV - 12, [(">>> CellposeModel(pretrained_model='cyto3')", "#d5dbe5"),
                                                  ("# from memory: no message, loads cpsam_v2", "#ff8a80")], 12.5); add(s)
add(t(CX_CAV + 12, y + 150, ["Following the docs, no diameter was set:", f"{S['adviceS_endo']['n_pred']} endothelial cells found (manual: 382)"], 13.5, fill=INK, lh=18))

# ================================================================ b: code — generic vs specific prompt
k = 1
ask(k, [("generic", ["“Please write a Python script to segment the", "[cancer | endothelial] cells in my image.”"]),
        ("specific", ["“…Cellpose 4, 0.65 µm/px, cells 25–50 µm,", "cancer cells must NOT be segmented,", "do not resize…”"])])
B_T = [("cG_endo", "gt_endo", "code, generic, endothelial", "generic", "diameter = 80 px (its choice)"),
       ("cS_endo", "gt_endo", "code, specific, endothelial", "specific", "“no `diameter` is passed”")]
if VAR == "B":
    B_T = [("cG_cancer", "gt", "generic, cancer", "generic · cancer", None), ("cS_cancer", "gt", "specific, cancer", "specific · cancer", None)] + \
          [(a, b, c, d + " · endo", e) for a, b, c, d, e in B_T]
tiles(k, B_T)
score(k, [("cancer", [("generic", "codeG_cancer"), ("specific", "codeS_cancer")]),
          ("endo", [("generic", "codeG_endo"), ("specific", "codeS_endo")])])
add(cav_title(k, ["All four scripts ran. Our “do not resize”", "removed the setting that works"]))
y = rows_y[k]
bx, bw = CX_CAV + 12, W_CAV - 70
for i, (lbl, key) in enumerate([("specific prompt, as written", "codeS_endo"), ("same script + diameter = 80 px", "codeS_endo_diam80")]):
    yy = y + 84 + i * 40
    v = f(key)
    add(t(bx, yy, lbl, 13, fill=BODY) + f'<rect x="{bx}" y="{yy+6}" width="{bw}" height="9" rx="3" fill="#e4e8ee"/>'
        + f'<rect x="{bx}" y="{yy+6}" width="{bw*v:.1f}" height="9" rx="3" fill="{F1C}"/>' + t(bx + bw + 6, yy + 15, f"{v:.2f}", 13, "bold", INK))
add(t(bx, y + 176, "F1, endothelial cells. Ask it to list every parameter it sets.", 13, fill=INK))

# ================================================================ c: agent
k = 2
ask(k, [(None, ["“Please run the analysis pipeline, assess the", "result, improve the analysis, and give me", "the result.”"])])
add(t(CX_ASK + 46, rows_y[k] + 146, ["Agent with code execution, one run per", "target, working on a copy of the image."], 12.5, fill="#6b2c87", lh=16))
C_T = [("ag_cancer", "gt", "agent, cancer", "cancer", "“About 5 false positives remain”"),
       ("ag_endo", "gt_endo", "agent, endothelial", "endothelial", "“outlines match the faint cell borders well”")]
tiles(k, C_T)
score(k, [("cancer", [("agent", "agent_cancer")]), ("endo", [("agent", "agent_endo")])])
add(cav_title(k, ["It graded its own result by eye,", "without reference data"]))
y = rows_y[k]
rowsC = [("cancer · false positives", "≈ 5", str(S["agent_cancer"]["fp"])), ("cancer · missed", "≈ 4", str(S["agent_cancer"]["fn"])),
         ("endothelial · median area", "“well”", "−36%"), ("endothelial · F1", "—", f"{f('agent_endo'):.2f}")]
add(t(CX_CAV + 190, y + 74, "it said", 12.5, "bold", "#6b2c87", "middle") + t(CX_CAV + 270, y + 74, "measured", 12.5, "bold", INK, "middle"))
for i, (lbl, said, meas) in enumerate(rowsC):
    yy = y + 98 + i * 24
    add(t(CX_CAV + 12, yy, lbl, 13, fill=BODY) + t(CX_CAV + 190, yy, said, 14, "bold", "#6b2c87", "middle")
        + t(CX_CAV + 270, yy, meas, 14, "bold", NOC, "middle"))
add(t(CX_CAV + 12, y + RH - 26, "Every threshold was tuned on the image it was judged on.", 13, fill=INK))

# ================================================================ d: direct answer
k = 3
ask(k, [("3 runs each", ["“Please draw around every [cancer |", "endothelial] cell in this image and count them.”"]),
        ("3 runs each", ["“How many [cancer | endothelial] cells", "are in this image?”"])])
D_T = [("d_cancer_r2", "gt", "drawn, cancer, run 2", "cancer · run 2", None),
       ("d_endo_r3", "gt_endo", "drawn, endothelial, run 3", "endothelial · run 3", "“a rough placeholder grid, not traced outlines”")]
if VAR == "B":
    D_T = [("d_cancer_r1", "gt", "drawn, cancer, run 1", "cancer · run 1", None), ("d_cancer_r2", "gt", "drawn, cancer, run 2", "run 2", None),
           ("d_cancer_r3", "gt", "drawn, cancer, run 3", "run 3", None), D_T[1][:3] + ("endo · run 3", None)]
tiles(k, D_T)
score(k, [("cancer", [(f"drawn, run {r}", f"draw_cancer_r{r}") for r in (1, 2, 3)]),
          ("endo", [(f"drawn, run {r}", f"draw_endo_r{r}") for r in (1, 2, 3)])])
add(cav_title(k, ["Answers change between runs and", "contradict each other"]))
y = rows_y[k]


def strip(x0, x1, yy, lo, hi, step, drawn, stated, asked, truth, lbl, band=None):
    X = lambda v: x0 + (v - lo) / (hi - lo) * (x1 - x0)
    g = [t(x0 - 10, yy + 4, lbl, 12.5, "bold", CC if "cancer" in lbl else EC, "end"),
         f'<line x1="{x0}" y1="{yy}" x2="{x1}" y2="{yy}" stroke="#d9c4c1" stroke-width="1.2"/>']
    if band:
        g.append(f'<rect x="{X(band[0]):.1f}" y="{yy-12}" width="{X(band[1])-X(band[0]):.1f}" height="24" fill="{INK}" fill-opacity="0.12"/>')
    g.append(f'<line x1="{X(truth):.1f}" y1="{yy-12}" x2="{X(truth):.1f}" y2="{yy+12}" stroke="{INK}" stroke-width="2" stroke-dasharray="4 3"/>'
             + t(X(truth), yy - 16, f"manual {truth}", 11.5, "bold", INK, "middle"))
    for v in drawn:
        g.append(f'<rect x="{X(v)-4.5:.1f}" y="{yy-12.5}" width="9" height="9" fill="none" stroke="{ACC}" stroke-width="1.8"/>')
    for v in stated:
        g.append(f'<path d="M{X(v):.1f},{yy+3} l5,5 l-5,5 l-5,-5 z" fill="{ACC}"/>')
    for v in asked:
        g.append(f'<circle cx="{X(v):.1f}" cy="{yy}" r="4.8" fill="{MCOL["sonnet"]}" stroke="#fff" stroke-width="1"/>')
    for v in range(lo, hi + 1, step):
        g.append(t(X(v), yy + 27, str(v), 11, fill="#7a8699", anchor="middle"))
    return "".join(g)


sx0, sx1 = CX_CAV + 112, CX_CAV + W_CAV - 18
dc = [S[f"draw_cancer_r{r}"]["n_drawn"] for r in (1, 2, 3)]
sc_ = [S[f"draw_cancer_r{r}"]["count_stated"] for r in (1, 2, 3)]
de = [S[f"draw_endo_r{r}"]["n_drawn"] for r in (1, 2, 3)]
add(group("count strips", strip(sx0, sx1, y + 86, 0, 160, 40, dc, sc_, S["counts_asked"]["cancer"], 124, "cancer")
          + strip(sx0, sx1, y + 146, 0, 500, 100, de, de, S["counts_asked"]["endo"], 382, "endothelial", (382, 462))
          + f'<rect x="{CX_CAV+12}" y="{y+RH-40}" width="9" height="9" fill="none" stroke="{ACC}" stroke-width="1.8"/>'
          + t(CX_CAV + 26, y + RH - 31, "cells drawn", 12.5, fill=BODY)
          + f'<path d="M{CX_CAV+118},{y+RH-41} l5,5 l-5,5 l-5,-5 z" fill="{ACC}"/>' + t(CX_CAV + 128, y + RH - 31, "count it stated", 12.5, fill=BODY)
          + f'<circle cx="{CX_CAV+244}" cy="{y+RH-36}" r="4.8" fill="{MCOL["sonnet"]}"/>' + t(CX_CAV + 254, y + RH - 31, "asked only for the number", 12.5, fill=BODY)))

# ================================================================ delegation arrow
AT, AB = rows_y[0], rows_y[3] + RH
defs.append(f'<linearGradient id="deleg" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#d9cbea"/><stop offset="1" stop-color="{ACC}"/></linearGradient>')
AXc = 28 + LW_ / 2
add(group("delegation arrow", f'<path d="M{AXc-20},{AT} H{AXc+20} V{AB-26} H{AXc+30} L{AXc},{AB} L{AXc-30},{AB-26} H{AXc-20} Z" fill="url(#deleg)"/>'
          + f'<text x="{AXc+6}" y="{(AT+AB)/2}" font-size="15" font-weight="bold" fill="#ffffff" text-anchor="middle" '
            f'transform="rotate(-90 {AXc+6} {(AT+AB)/2})">more of the analysis delegated to, and hidden in, the LLM</text>'))

# ================================================================ what to keep
KY = rows_y[3] + RH + GAP
KH = 112
add(group("keep frame", rrect(28, KY, 1784, KH, 16, "#ffffff", NN["stroke"], 1.4) + t(48, KY + 30, "What to keep", 18.5, "bold", INK)))
KEEP = [("lock", "Check where images go", "provider terms, local models"),
        ("check", "Check advice against the docs", "and test it on your images"),
        ("ruler", "Give context, ask for parameters", "and have every setting listed"),
        ("target", "Validate every output", "against manual annotation (F1)"),
        ("file", "Keep code, prompts, model, date", "so the analysis reruns without the LLM")]
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
    add(group(f"keep {a_}", kicon(ic, x + 20, KY + 74, ACC) + t(x + 48, KY + 70, a_, 14.5, "bold", INK) + t(x + 48, KY + 90, b_, 13, fill=BODY)))

H = KY + KH + 20
svg = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
       f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" xmlns:xlink="http://www.w3.org/1999/xlink" '
       f'width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">\n'
       f'<defs>{"".join(defs)}</defs>\n<rect width="{W}" height="{H}" fill="#ffffff"/>\n'
       + "\n".join(out) + "\n</svg>\n")
open(f"fig3_v5{VAR}.svg", "w", encoding="utf-8").write(svg)
print(VAR, "written", len(svg) // 1024, "KB; height", H)
