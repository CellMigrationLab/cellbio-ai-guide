# ======================================================================= FIGURE 3 (rows): four ways to use an LLM on one hard task
BF = "bf/"
ROI = (0, 0, 260, 260)                       # ROI contours are stored in ROI pixel coordinates
DEFC = "#9aa4b2"                             # grey baseline: Cellpose-SAM, default settings (as Fig. 2a)
CAVF, CAVS = "#fdf0ef", "#efc2be"


def J(p):
    try:
        return json.load(open(BF + p))
    except Exception:
        return None


def f1(p):
    d = J(p)
    return None if d is None else d["f1"]


SC = dict(default=0.775, adv=f1("advice/score_b.json"), adv_a=f1("advice/score_a.json"), gen=f1("codeG/score.json"),
          spec=f1("codeS/score.json"), agent=f1("agent/score.json"),
          haiku=f1("draw/haiku_score.json"), sonnet=f1("draw/sonnet_score.json"), opus=f1("draw/opus_score.json"))
COUNTS = {m: [r["cancer_bf"] for r in json.load(open("v3/full/answers.json"))[m]] for m in ["haiku", "sonnet", "opus"]}
NDRAW = {m: J(f"draw/{m}_score.json")["n_pred"] for m in ["haiku", "sonnet", "opus"]}
TRUE_N = 124


def roi_tile(x, y, w, key, label, sub_lbl=None):
    """Magnified ROI (260 x 260 px of the field), manual annotation dashed blue, LLM-derived result magenta, as in Fig. 2."""
    import os
    g = [real_image(x, y, w, w, BF + "roi/bf_roi.png", PX, 260, 50, label, "#111111")]
    g.append(vector_outlines_sub(x, y, w, w, BF + "roi/gt.json", "manual annotation (vector)", REF, 1.6, DASH, ROI))
    if os.path.exists(BF + f"roi/{key}.json"):
        g.append(vector_outlines_sub(x, y, w, w, BF + f"roi/{key}.json", f"{label} (vector)", MODEL, 1.7, None, ROI))
    else:
        g.append(rrect(x, y, w, w, 2, "#ffffff", "none", extra=' fill-opacity="0.6"') + t(x + w / 2, y + w / 2, "running…", 15, "bold", "#7a8699", "middle"))
    if sub_lbl:
        g.append(halo(x + 7, y + 18, sub_lbl))
    return group(label, "".join(g))


def f1bars(x, y, w, items, title="F1"):
    """Fig. 1/2 style: thin bars, track in light grey, value at right; grey bar = Cellpose-SAM default."""
    g = [t(x, y, title, 13.5, "bold", INK)]
    for i, (lbl, v, is_def) in enumerate(items):
        yy = y + 22 + i * 37
        g.append(t(x, yy, lbl, 13.5, fill=BODY))
        if v is None:
            g.append(t(x, yy + 17, "running…", 13, "bold", "#7a8699"))
            continue
        g.append(f'<rect x="{x}" y="{yy+6}" width="{w-44}" height="9" rx="3" fill="#e4e8ee"/>'
                 f'<rect x="{x}" y="{yy+6}" width="{(w-44)*v:.1f}" height="9" rx="3" fill="{DEFC if is_def else F1C}"/>'
                 + t(x + w - 38, yy + 15, f"{v:.2f}", 13.5, "bold", INK))
    return "".join(g)


# ---------------------------------------------------------------- grid
Y0 = 20
LW = 64                                       # delegation-arrow strip
RX = 28 + LW + 10                             # row frames start
RW = 1812 - RX
CX_ASK, W_ASK = RX + 20, 470
CX_RES = CX_ASK + W_ASK + 24
TS = 196                                      # ROI tile size
CX_F1 = CX_RES + 2 * TS + 14 + 26
W_F1 = 230
CX_CAV = CX_F1 + W_F1 + 26
W_CAV = 1812 - 16 - CX_CAV
RH = 262                                      # row height
GAP = 12

# ---------------------------------------------------------------- header strip: the task
HDH = 92
add(group("task", rrect(RX, Y0, RW, HDH, 14, "#ffffff", NN["stroke"], 1.3)
          + real_image(RX + 14, Y0 + 10, 72, 72, BF + "draw/bf_full.png", PX, 1024, 0, "task: full field")
          + rrect(RX + 14 + 440 / 1024 * 72, Y0 + 10 + 40 / 1022 * 72, 260 / 1024 * 72, 260 / 1022 * 72, 0, "none", REF2, 1.6)
          + t(RX + 104, Y0 + 36, "One task for every use: segment the cancer cells on the endothelial monolayer", 19, "bold", INK)
          + t(RX + 104, Y0 + 62, ["Brightfield, one field, 124 manually annotated cells. Tiles: magnified region (yellow box). Claude, 16 Oct 2026."],
              14, fill=BODY)
          + key_item(1812 - 520, Y0 + 58, MODEL, "segmentation result") + key_item(1812 - 350, Y0 + 58, REF, "manual annotation", DASH)
          + f'<rect x="{1812-170}" y="{Y0+52}" width="22" height="9" rx="3" fill="{DEFC}"/>' + t(1812 - 142, Y0 + 61, "Cellpose-SAM default", 13.5, fill=BODY)))

rows_y = [Y0 + HDH + GAP + k * (RH + GAP) for k in range(4)]
HEADS = [("a", "Ask for advice"), ("b", "Ask for code"), ("c", "Let an agent run it"), ("d", "Ask for the answer")]
for k, (L, ttl) in enumerate(HEADS):
    y = rows_y[k]
    add(group(f"row {L}", rrect(RX, y, RW, RH, 16, NN["bg"], NN["stroke"], 1.4)
              + f'<circle cx="{CX_ASK+16}" cy="{y+28}" r="16" fill="{ACC}"/>' + t(CX_ASK + 16, y + 34.5, L, 18, "bold", "#fff", "middle")
              + t(CX_ASK + 42, y + 35, ttl, 19, "bold", INK)
              + rrect(CX_CAV - 10, y + 10, W_CAV + 16, RH - 20, 12, CAVF, CAVS, 1.2)))


def cav_title(k, lines):
    y = rows_y[k]
    return caution(CX_CAV + 12, y + 32, NOC) + t(CX_CAV + 32, y + 37, lines, 15, "bold", NOC, lh=19)


def col_head(k):
    y = rows_y[k]
    return t(CX_F1, y + 35, "", 1)


# ================================================================ a: advice
y = rows_y[0]
s, h = prompt(CX_ASK, y + 52, W_ASK, ["Which tool, model and settings would you", "recommend? I don't need code."], 14); add(s)
s, h2 = reply(CX_ASK, y + 52 + h, W_ASK, ["“…Cellpose… Model: start with `cyto3`, or", "`cpsam` if you use Cellpose 4… Raise [cell", "probability] to reduce false positives on", "the endothelium… a short fine-tune.”"],
              13.5, False, "Sonnet, excerpt"); add(s)
add(roi_tile(CX_RES, y + 52, TS, "default", "Cellpose-SAM default", "Cellpose-SAM default"))
add(roi_tile(CX_RES + TS + 14, y + 52, TS, "advised_b", "advice, implemented", "advice, as implemented"))
add(f1bars(CX_F1, y + 58, W_F1, [("Cellpose-SAM default", SC["default"], True), ("advice, as implemented", SC["adv"], False)]))
add(cav_title(0, ["Advice can be outdated, and a wrong model", "name is silently replaced by the default"]))
add(t(CX_CAV + 12, y + 82, "Following the advice with the installed Cellpose 4.2.1.1:", 13.5, "bold", INK))
s, _ = terminal(CX_CAV + 12, y + 94, W_CAV - 12, [(">>> m = models.CellposeModel(pretrained_model='cyto3')", "#d5dbe5"),
                                                   ("                                    (no message)", "#8a94a3"),
                                                   (">>> m.pretrained_model", "#d5dbe5"),
                                                   ("'/root/.cellpose/models/cpsam_v2'", "#ff8a80")], 13); add(s)

# ================================================================ b: code
y = rows_y[1]
s, h = prompt(CX_ASK, y + 52, W_ASK, ["“Please segment the cancer cells in this image.”"], 14); add(s)
s, h2 = prompt(CX_ASK, y + 52 + h, W_ASK, ["“…using Cellpose 4, pixel size 0.65 µm, cells", "15–25 µm, endothelial cells must NOT be", "segmented, do not resize…”"], 14); add(s)
add(t(CX_ASK + 46, y + 52 + h + h2 + 14, "Sonnet wrote one script per prompt; we ran both.", 13.5, "bold", "#6b2c87"))
add(roi_tile(CX_RES, y + 52, TS, "generic", "code, generic prompt", "generic prompt"))
add(roi_tile(CX_RES + TS + 14, y + 52, TS, "specific", "code, specific prompt", "specific prompt"))
add(f1bars(CX_F1, y + 58, W_F1, [("Cellpose-SAM default", SC["default"], True), ("generic prompt", SC["gen"], False), ("specific prompt", SC["spec"], False)]))
add(cav_title(1, ["The code was never run by the LLM:", "it is only as good as your test"]))
s, _ = reply(CX_CAV + 12, y + 84, W_CAV - 12, ["“I can't run code, so it is untested, and", "the parameters are estimates read off", "the preview.”"], 13.5, False, "Sonnet, generic prompt, verbatim"); add(s)

# ================================================================ c: agent
y = rows_y[2]
s, h = prompt(CX_ASK, y + 52, W_ASK, ["“Please run the analysis pipeline, assess", "the result, improve the analysis, and give", "me the result.”"], 14); add(s)
s, h2 = reply(CX_ASK, y + 52 + h, W_ASK, ["“I segmented 138 cancer cells… The result", "is good but not perfect. About 3 objects", "are false positives and about 10 to 15", "cells are missed.”"], 13.5, False, "Sonnet agent, excerpt"); add(s)
add(roi_tile(CX_RES, y + 52, TS, "agent_first", "agent first pass", "agent, first pass"))
add(roi_tile(CX_RES + TS + 14, y + 52, TS, "agent", "agent result", "agent, final"))
add(f1bars(CX_F1, y + 58, W_F1, [("Cellpose-SAM default", SC["default"], True), ("agent, first pass", f1("agent/first_pass_score.json"), False),
                                 ("agent, final", SC["agent"], False)]))
add(cav_title(2, ["The agent grades its own work,", "without reference data"]))
AGS = J("agent/score.json")
# self-assessment vs measurement: paired dot plot
px0, px1 = CX_CAV + 150, CX_CAV + W_CAV - 40
PXs = lambda v: px0 + v / 20 * (px1 - px0)
g = [t(CX_CAV + 12, y + 86, "Its estimate against the manual annotation:", 13.5, "bold", INK)]
for i, (lbl, est, meas) in enumerate([("false positives", (3, 3), AGS["fp"]), ("missed cells", (10, 15), AGS["fn"])]):
    yy = y + 118 + i * 34
    g.append(t(px0 - 12, yy + 5, lbl, 13.5, "bold", BODY, "end")
             + f'<line x1="{px0}" y1="{yy}" x2="{px1}" y2="{yy}" stroke="#d9c4c1" stroke-width="1.2"/>'
             + f'<line x1="{PXs(est[0]):.1f}" y1="{yy}" x2="{PXs(est[1]):.1f}" y2="{yy}" stroke="{ACC}" stroke-width="10" stroke-linecap="round" stroke-opacity="0.45"/>'
             + f'<circle cx="{PXs(meas):.1f}" cy="{yy}" r="6.5" fill="{INK}"/>')
for v in range(0, 21, 5):
    g.append(f'<line x1="{PXs(v):.1f}" y1="{y+168}" x2="{PXs(v):.1f}" y2="{y+172}" stroke="#8a94a3"/>' + t(PXs(v), y + 186, str(v), 12, fill=BODY, anchor="middle"))
g.append(f'<line x1="{CX_CAV+12}" y1="{y+206}" x2="{CX_CAV+30}" y2="{y+206}" stroke="{ACC}" stroke-width="10" stroke-linecap="round" stroke-opacity="0.45"/>'
         + t(CX_CAV + 38, y + 211, "agent's estimate", 13, fill=BODY)
         + f'<circle cx="{CX_CAV+170}" cy="{y+206}" r="6" fill="{INK}"/>' + t(CX_CAV + 182, y + 211, "measured", 13, fill=BODY)
         + t(CX_CAV + 12, y + 234, "Not asked for: diameter and 5 filters, all tuned on this one image", 13, fill=INK))
add(group("agent self-assessment", "".join(g)))

# ================================================================ d: direct answer (Sonnet, 3 runs of the same prompts)
CNT = json.load(open(BF + "count/counts.json"))
y = rows_y[3]
s, h = prompt(CX_ASK, y + 52, W_ASK, ["“Outline every cancer cell in the image.”"], 14); add(s)
s, h2 = prompt(CX_ASK, y + 52 + h, W_ASK, ["“How many cancer cells and how many", "endothelial cells are in this image?”"], 14); add(s)
add(t(CX_ASK + 46, y + 52 + h + h2 + 14, "Each prompt sent three times, new conversation each time.", 13.5, "bold", "#6b2c87"))
TS3 = (2 * TS + 14 - 2 * 8) / 3
for r in range(3):
    add(roi_tile(CX_RES + r * (TS3 + 8), y + 52, TS3, f"sonnet_r{r+1}", f"drawn, run {r+1}", f"run {r+1}"))
add(f1bars(CX_F1, y + 58, W_F1, [("Cellpose-SAM default", SC["default"], True)]
           + [(f"drawn, run {r+1}", f1(f"draw/sonnet_r{r+1}_score.json"), False) for r in range(3)]))
add(cav_title(3, ["Plausible numbers, but no way to check them:", "the endothelial count is half the annotation"]))


def strip(x0, x1, yy, lo, hi, step, vals, truth, lbl, band=None):
    X = lambda v: x0 + (v - lo) / (hi - lo) * (x1 - x0)
    g = [t(x0 - 12, yy + 5, lbl, 13.5, "bold", BODY, "end"),
         f'<line x1="{x0}" y1="{yy}" x2="{x1}" y2="{yy}" stroke="#d9c4c1" stroke-width="1.2"/>']
    if band:
        g.append(f'<rect x="{X(band[0]):.1f}" y="{yy-13}" width="{X(band[1])-X(band[0]):.1f}" height="26" fill="{INK}" fill-opacity="0.12"/>'
                 + t((X(band[0]) + X(band[1])) / 2, yy - 18, f"manual: {band[0]}–{band[1]}", 12.5, "bold", INK, "middle"))
    else:
        g.append(f'<line x1="{X(truth):.1f}" y1="{yy-13}" x2="{X(truth):.1f}" y2="{yy+13}" stroke="{INK}" stroke-width="2" stroke-dasharray="4 3"/>'
                 + t(X(truth), yy - 18, f"manual: {truth}", 12.5, "bold", INK, "middle"))
    seen = {}
    for v in vals:
        n = seen.get(v, 0); seen[v] = n + 1
        k_ = vals.count(v)
        g.append(f'<circle cx="{X(v):.1f}" cy="{yy+(n-(k_-1)/2)*10:.1f}" r="5.5" fill="{MCOL["sonnet"]}" stroke="#ffffff" stroke-width="1"/>')
    for v in range(lo, hi + 1, step):
        g.append(f'<line x1="{X(v):.1f}" y1="{yy+16}" x2="{X(v):.1f}" y2="{yy+20}" stroke="#8a94a3"/>' + t(X(v), yy + 33, str(v), 12, fill=BODY, anchor="middle"))
    return "".join(g)


sx0, sx1 = CX_CAV + 128, CX_CAV + W_CAV - 24
add(group("count strips",
          strip(sx0, sx1, y + 118, 80, 160, 20, [r["cancer_cells"] for r in CNT["runs"]], 124, "cancer cells")
          + strip(sx0, sx1, y + 192, 0, 500, 100, [r["endothelial_cells"] for r in CNT["runs"]], None, "endothelial cells",
                  (CNT["truth"]["endothelial_complete"], CNT["truth"]["endothelial_incl_border"]))
          + t(CX_CAV + 12, y + RH - 22, "● Sonnet's answer, 3 runs (identical answers stacked)", 13, fill=BODY)))

# ================================================================ delegation arrow (left, top to bottom)
AT, AB = rows_y[0], rows_y[3] + RH
defs.append(f'<linearGradient id="deleg" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#d9cbea"/><stop offset="1" stop-color="{ACC}"/></linearGradient>')
AXc = 28 + LW / 2
add(group("delegation arrow", f'<path d="M{AXc-20},{AT} H{AXc+20} V{AB-26} H{AXc+30} L{AXc},{AB} L{AXc-30},{AB-26} H{AXc-20} Z" fill="url(#deleg)"/>'
          + f'<text x="{AXc+6}" y="{(AT+AB)/2}" font-size="15" font-weight="bold" fill="#ffffff" text-anchor="middle" '
            f'transform="rotate(-90 {AXc+6} {(AT+AB)/2})">more of the analysis delegated to, and hidden in, the LLM</text>'))

# ================================================================ final row: what to keep
KY = rows_y[3] + RH + GAP
KH = 118
add(group("keep frame", rrect(28, KY, 1784, KH, 16, "#ffffff", NN["stroke"], 1.4) + t(48, KY + 32, "What to keep", 19, "bold", INK)))
KEEP = [("check", "Check advice against the docs", "of the version you have installed"),
        ("ruler", "Give the context", "pixel size, object size, what to exclude"),
        ("target", "Validate every output", "against manual annotation (F1), as in Fig. 1"),
        ("file", "Keep code, prompts, model, date", "the final analysis reruns without the LLM")]
KW = (1784 - 40) / 4


def kicon(name, cx, cy, col):
    st_ = f'fill="none" stroke="{col}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"'
    if name == "check":
        return f'<rect x="{cx-14}" y="{cy-17}" width="28" height="34" rx="3" {st_}/><path d="M{cx-7},{cy+1} l5,5 l10,-11" {st_}/>'
    if name == "ruler":
        return (f'<rect x="{cx-18}" y="{cy-8}" width="36" height="16" rx="2" {st_}/>'
                + "".join(f'<line x1="{cx-12+i*8}" y1="{cy-8}" x2="{cx-12+i*8}" y2="{cy-1-(3 if i%2==0 else 0)}" {st_}/>' for i in range(4)))
    if name == "target":
        return f'<circle cx="{cx}" cy="{cy}" r="16" {st_}/><circle cx="{cx}" cy="{cy}" r="9" {st_} stroke-dasharray="3 2.5"/><circle cx="{cx}" cy="{cy}" r="2.6" fill="{col}"/>'
    return (f'<path d="M{cx-13},{cy-17} H{cx+5} L{cx+13},{cy-9} V{cy+17} H{cx-13} Z" {st_}/>'
            f'<line x1="{cx-7}" y1="{cy-3}" x2="{cx+7}" y2="{cy-3}" {st_}/><line x1="{cx-7}" y1="{cy+5}" x2="{cx+7}" y2="{cy+5}" {st_}/>')


for i, (ic, a, b) in enumerate(KEEP):
    x = 48 + i * KW
    add(group(f"keep {a}", kicon(ic, x + 22, KY + 78, ACC) + t(x + 54, KY + 74, a, 15.5, "bold", INK) + t(x + 54, KY + 95, b, 13.5, fill=BODY)))

H = KY + KH + 20
svg = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
       f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" xmlns:xlink="http://www.w3.org/1999/xlink" '
       f'width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">\n'
       f'<defs>{"".join(defs)}</defs>\n<rect width="{W}" height="{H}" fill="#ffffff"/>\n'
       + "\n".join(out) + "\n</svg>\n")
open("fig3_v4.svg", "w", encoding="utf-8").write(svg)
print("written", len(svg) // 1024, "KB; height", H)
