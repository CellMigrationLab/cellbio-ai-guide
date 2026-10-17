# ======================================================================= FIGURE 3 v6: before -> after, one change per row (illustration)
import os as _os
BF = "bf/"
R2 = "bf/roi2/"
S = json.load(open("bf2/all_scores.json"))
N = json.load(open("bf3/new_scores.json")) if _os.path.exists("bf3/new_scores.json") else {}
S.update(N)
ROI = (0, 0, 260, 260)
DEFC = "#9aa4b2"
CAVF, CAVS = "#fdf0ef", "#efc2be"
CHG = "#6b2c87"


def f(k):
    return S[k]["f1"] if k in S and S[k].get("f1") is not None else None


def tile(x, y, w, key, gt, label, cap=None):
    g = [real_image(x, y, w, w, R2 + "bf_roi.png", PX, 260, 50, label, "#111111"),
         vector_outlines_sub(x, y, w, w, R2 + f"{gt}.json", "manual annotation (vector)", REF, 1.3, DASH, ROI)]
    if key and _os.path.exists(R2 + f"{key}.json"):
        g.append(vector_outlines_sub(x, y, w, w, R2 + f"{key}.json", f"{label} (vector)", MODEL, 1.7, None, ROI))
    else:
        g.append(rrect(x, y, w, w, 2, "#ffffff", "none", extra=' fill-opacity="0.55"')
                 + t(x + w / 2, y + w / 2 + 5, "running…", 15, "bold", "#56606e", "middle"))
    if cap:
        g.append(halo(x + 6, y + 17, cap, size=12.5))
    return group(label, "".join(g))


def bars3(x, y, w, items):
    g = [t(x, y, "F1, endothelial cells", 13, "bold", INK)]
    for i, (lbl, k, kind) in enumerate(items):
        yy = y + 24 + i * 34
        v = f(k)
        g.append(t(x, yy, lbl, 12.5, "bold" if kind == "after" else "normal", INK if kind == "after" else BODY))
        g.append(f'<rect x="{x}" y="{yy+6}" width="{w-40}" height="9" rx="3" fill="#e4e8ee"/>')
        if v is None:
            g.append(t(x + w - 34, yy + 15, "…", 13, "bold", "#7a8699"))
        else:
            g.append(f'<rect x="{x}" y="{yy+6}" width="{(w-40)*v:.1f}" height="9" rx="3" fill="{DEFC if kind == "default" else F1C}"/>'
                     + t(x + w - 34, yy + 15, f"{v:.2f}", 13, "bold", INK))
    ax = x + (w - 40) * 0.897
    g.append(f'<line x1="{ax:.1f}" y1="{y+24}" x2="{ax:.1f}" y2="{y+24+len(items)*34-12}" stroke="{INK}" stroke-width="1.2" stroke-dasharray="2 2"/>')
    return "".join(g)


def change_pill(cx, cy, lines):
    w = 112
    h = 16 + 15 * len(lines)
    return (f'<path d="M{cx-w/2},{cy-h/2} h{w-12} l12,{h/2} l-12,{h/2} h-{w-12} z" fill="{CHG}"/>'
            + t(cx - 4, cy - h / 2 + 20, lines, 12, "bold", "#ffffff", "middle", lh=15))


# ---------------------------------------------------------------- grid
Y0 = 20
LW_ = 64
RX = 28 + LW_ + 10
RW = 1812 - RX
CX_ASK, W_ASK = RX + 18, 360
TS = 206
CX_T1 = CX_ASK + W_ASK + 18
CX_P = CX_T1 + TS + 8                     # change pill
CX_T2 = CX_P + 128
CX_F1 = CX_T2 + TS + 22
W_F1 = 214
CX_CAV = CX_F1 + W_F1 + 22
W_CAV = 1812 - 14 - CX_CAV
RH = TS + 70
GAP = 12

HDH = 84
add(group("task", rrect(RX, Y0, RW, HDH, 14, "#ffffff", NN["stroke"], 1.3)
          + real_image(RX + 12, Y0 + 9, 66, 66, BF + "draw/bf_full.png", PX, 1024, 0, "task: full field")
          + rrect(RX + 12 + 760 / 1024 * 66, Y0 + 9 + 240 / 1022 * 66, 260 / 1024 * 66, 260 / 1022 * 66, 0, "none", REF2, 1.6)
          + t(RX + 94, Y0 + 34, "Segment the endothelial cells under the cancer cells (brightfield): what changes when you follow the advice", 18.5, "bold", INK)
          + t(RX + 94, Y0 + 60, "Claude Sonnet, Oct 2026 · tiles: magnified region (yellow box) · F1 against 382 manually annotated cells · illustration, one field", 13.5, fill=BODY)
          + key_item(1812 - 520, Y0 + 30, MODEL, "LLM-derived result") + key_item(1812 - 360, Y0 + 30, REF, "manual annotation", DASH)
          + f'<rect x="{1812-196}" y="{Y0+24}" width="20" height="7" rx="2.5" fill="{DEFC}"/>' + t(1812 - 170, Y0 + 32, "Cellpose default", 13, fill=BODY)
          + f'<line x1="{1812-520+11}" y1="{Y0+50}" x2="{1812-520+11}" y2="{Y0+66}" stroke="{INK}" stroke-width="1.2" stroke-dasharray="2 2"/>'
          + t(1812 - 520 + 28, Y0 + 63, "agreement between two annotators (0.90)", 13, fill=BODY)))

rows_y = [Y0 + HDH + GAP + k * (RH + GAP) for k in range(4)]
HEADS = [("a", "Ask for advice"), ("b", "Ask for code"), ("c", "Let an agent run it"), ("d", "Ask for the answer")]
for k, (L, ttl) in enumerate(HEADS):
    y = rows_y[k]
    add(group(f"row {L}", rrect(RX, y, RW, RH, 16, NN["bg"], NN["stroke"], 1.4)
              + f'<circle cx="{CX_ASK+15}" cy="{y+26}" r="15" fill="{ACC}"/>' + t(CX_ASK + 15, y + 32, L, 17, "bold", "#fff", "middle")
              + t(CX_ASK + 40, y + 32, ttl, 18.5, "bold", INK)
              + rrect(CX_CAV - 8, y + 10, W_CAV + 14, RH - 20, 12, CAVF, CAVS, 1.2)))


def cav(k, title, body=None, dy=0):
    y = rows_y[k]
    s = caution(CX_CAV + 12, y + 32, NOC) + t(CX_CAV + 32, y + 37, title, 14.5, "bold", NOC, lh=18)
    if body:
        s += t(CX_CAV + 12, y + 90 + dy, body, 13.5, fill=INK, lh=18)
    return s


def ask(k, items):
    y = rows_y[k] + 50
    for tag, lines in items:
        if tag:
            add(t(CX_ASK + 46, y + 2, tag, 12, "bold", CHG)); y += 6
        s, h = prompt(CX_ASK, y, W_ASK, lines, 13); add(s); y += h


def pair(k, t1, t2, pill):
    y = rows_y[k] + 50
    add(tile(CX_T1, y, TS, *t1))
    add(change_pill(CX_P + 56, y + TS / 2, pill))
    add(tile(CX_T2, y, TS, *t2))


# ================================================================ a: advice — reply from memory vs after reading the docs (no analysis run)
k = 0
ask(k, [("before", ["“Which tool, model and settings would you", "recommend? I don't need code.”"]),
        ("after", ["“…Do not rely on your memory: check the", "current documentation first.”"])])
y = rows_y[k] + 50
WB = 300
s, hA = reply(CX_T1, y, WB, ["“Start with the newest generalist", "model available to you, either", "Cellpose-SAM (Cellpose 4) or cyto3.”", " ", "“…try the cyto3 denoise or", "deblur models.”"],
              13, False, "From memory (excerpt)"); add(s)
add(t(CX_T1 + 4, y + hA + 8, ["Does not know the current models;", "offers models removed in Cellpose 4"], 12.5, "bold", NOC, lh=16))
add(change_pill(CX_T1 + WB + 68, y + 70, ["read the", "docs"]))
XD = CX_T1 + WB + 134
s, hB = reply(XD, y, CX_CAV - 30 - XD, ["“The docs list these built-in models:", "cpsam_v2 …, cpdino …, cpdino-vitb …,", "and the original cpsam.”", " ", "“The old cyto3 and nuclei models are", "not mentioned in the current docs, and", "the old models.Cellpose class was", "removed in Cellpose 4.”"],
              13, False, "After reading the docs (excerpt)"); add(s)
add(t(XD + 4, y + hB + 8, "Names the current models and lists the pages it read", 12.5, "bold", OKT if 'OKT' in globals() else "#1a7a4c"))
add(cav(k, ["Outdated advice can run without error:", "only the documentation reveals it"]))
s, _ = terminal(CX_CAV + 12, rows_y[k] + 72, W_CAV - 12, [(">>> m = models.CellposeModel(", "#d5dbe5"),
                                                         ("...     pretrained_model='cyto3')", "#d5dbe5"),
                                                         ("                      (no message)", "#8a94a3"),
                                                         (">>> m.pretrained_model", "#d5dbe5"),
                                                         ("'.../models/cpsam_v2'", "#ff8a80")], 12.5); add(s)
add(t(CX_CAV + 12, rows_y[k] + RH - 42, ["Cellpose 4.2.1.1 loads its default model instead,", "so the analysis runs and the result looks normal."], 13, fill=INK, lh=17))

# ================================================================ b: code
k = 1
ask(k, [("before", ["“Please write a Python script to segment the", "endothelial cells in my image.”"]),
        ("after: Box 1", ["“…check the documentation of Cellpose 4.2.1.1…", "cells 25–50 µm… for every parameter, state the", "value, whether it is the default, and why…”"])])
pair(k, ("cG_endo_med", "gt_endo", "code, generic prompt", "generic prompt"), ("b1_endo_med", "gt_endo", "code, Box 1 prompt", "Box 1 prompt"),
     ["Box 1", "prompt"])
add(bars3(CX_F1, rows_y[k] + 56, W_F1, [("Cellpose default", "default_endo", "default"), ("generic prompt", "gen_endo_med", "before"),
                                        ("Box 1 prompt", "box1_endo_med", "after")]))
B1Q = S.get("box1_quote", ["(parameter list from the Box 1 reply)"])
add(cav(k, ["All scripts ran; only the test against", "annotation shows which one works"]))
s, _ = reply(CX_CAV + 12, rows_y[k] + 72, W_CAV - 12, B1Q, 12.5, True, "Box 1 reply, parameter list (excerpt)"); add(s)

# ================================================================ c: agent
k = 2
ask(k, [("before", ["“Please run the analysis pipeline, assess the", "result, improve the analysis…”"]),
        ("after", ["“…Score every version against my annotation…", "other images are held out for a final check.”"])])
pair(k, ("ag_endo", "gt_endo", "agent judging by eye", "judged by eye"), ("ref_endo", "gt_endo", "agent with reference data", "scored, held-out"),
     ["give it", "annotations"])
add(bars3(CX_F1, rows_y[k] + 56, W_F1, [("Cellpose default", "default_endo", "default"), ("judged by eye", "agent_endo", "before"),
                                        ("scored (held-out half)", "ref_endo_heldout", "after")]))
add(cav(k, ["What the agent reported vs", "what we measured"]))
y = rows_y[k]
REFD = S.get("ref_endo_dev_reported")
rowsC = [("by eye", "“match … well”", f"F1 {f('agent_endo'):.2f}"),
         ("scored", f"F1 {REFD:.2f} (dev)" if REFD else "…", f"F1 {f('ref_endo_heldout'):.2f} (held-out)" if f('ref_endo_heldout') else "…")]
add(t(CX_CAV + 150, y + 76, "it reported", 12.5, "bold", CHG, "middle") + t(CX_CAV + 300, y + 76, "measured", 12.5, "bold", INK, "middle"))
for i, (lbl, said, meas) in enumerate(rowsC):
    yy = y + 104 + i * 28
    add(t(CX_CAV + 12, yy, lbl, 13, "bold", BODY) + t(CX_CAV + 150, yy, said, 13.5, "bold", CHG, "middle")
        + t(CX_CAV + 300, yy, meas, 13.5, "bold", NOC, "middle"))
add(t(CX_CAV + 12, y + RH - 28, "Freeze the workflow, then test it on data it never saw.", 13, fill=INK))

# ================================================================ d: direct answer
k = 3
ask(k, [("3 runs", ["“Please draw around every endothelial cell in", "this image and count them.”"]),
        ("3 runs", ["“How many endothelial cells are in this image?”"])])
pair(k, ("d_endo_r2", "gt_endo", "drawn, run 2", "drawn, run 2"), ("d_endo_r3", "gt_endo", "drawn, run 3", "drawn, run 3"),
     ["ask", "again"])
add(t(CX_T2, rows_y[k] + 50 + TS + 14, "“a rough placeholder grid, not traced outlines”", 12, fill=CHG, style="italic"))
add(bars3(CX_F1, rows_y[k] + 56, W_F1, [("Cellpose default", "default_endo", "default"), ("drawn, run 2", "draw_endo_r2", "before"),
                                        ("drawn, run 3", "draw_endo_r3", "after")]))
add(cav(k, ["Ask for the outlines behind the number,", "and ask more than once"]))
y = rows_y[k]
sx0, sx1 = CX_CAV + 30, CX_CAV + W_CAV - 18
X = lambda v: sx0 + v / 500 * (sx1 - sx0)
g = [f'<line x1="{sx0}" y1="{y+118}" x2="{sx1}" y2="{y+118}" stroke="#d9c4c1" stroke-width="1.2"/>',
     f'<rect x="{X(382):.1f}" y="{y+104}" width="{X(462)-X(382):.1f}" height="28" fill="{INK}" fill-opacity="0.12"/>',
     f'<line x1="{X(382):.1f}" y1="{y+102}" x2="{X(382):.1f}" y2="{y+134}" stroke="{INK}" stroke-width="2" stroke-dasharray="4 3"/>',
     t(X(382), y + 96, "manual 382", 12, "bold", INK, "middle")]
for r in (1, 2, 3):
    g.append(f'<rect x="{X(S[f"draw_endo_r{r}"]["n_drawn"])-5:.1f}" y="{y+113}" width="10" height="10" fill="none" stroke="{ACC}" stroke-width="2"/>')
for v in S["counts_asked"]["endo"]:
    g.append(f'<circle cx="{X(v):.1f}" cy="{y+118}" r="5.5" fill="{MCOL["sonnet"]}" stroke="#fff" stroke-width="1"/>')
for v in range(0, 501, 100):
    g.append(t(X(v), y + 150, str(v), 11.5, fill="#7a8699", anchor="middle"))
g.append(f'<rect x="{CX_CAV+12}" y="{y+170}" width="10" height="10" fill="none" stroke="{ACC}" stroke-width="2"/>' + t(CX_CAV + 28, y + 180, "cells drawn (= count stated)", 12.5, fill=BODY)
         + f'<circle cx="{CX_CAV+218}" cy="{y+175}" r="5.5" fill="{MCOL["sonnet"]}"/>' + t(CX_CAV + 230, y + 180, "asked only for the number", 12.5, fill=BODY))
g.append(t(CX_CAV + 12, y + RH - 28, "Different numbers each run; none was counted.", 13, fill=INK))
add(group("count strip", "".join(g)))

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
add(group("keep frame", rrect(28, KY, 1784, KH, 16, "#ffffff", NN["stroke"], 1.4)
          + t(48, KY + 30, "Whatever the level of delegation, only a test on images with a known answer shows whether the result is right", 17, "bold", INK)))
KEEP = [("lock", "Check where images go", "provider terms, local models"),
        ("check", "Check the docs of your version", "then test the advised settings"),
        ("ruler", "List every parameter and default", "ask for them to be justified (Box 1)"),
        ("target", "Test on annotated images", "keep held-out data out of reach"),
        ("file", "Keep code, prompts, model, date", "rerun from the raw images")]
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
open("fig3_v6.svg", "w", encoding="utf-8").write(svg)
print("written", len(svg) // 1024, "KB; height", H)
