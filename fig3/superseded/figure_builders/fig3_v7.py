# ======================================================================= FIGURE 3 v7: five rows, before -> after; endothelial (main) + cancer (small)
import os as _os
BF = "bf/"
R2 = "bf/roi2/"
S = json.load(open("bf2/all_scores.json"))
if _os.path.exists("bf3/new_scores.json"):
    S.update(json.load(open("bf3/new_scores.json")))
ROI = (0, 0, 260, 260)
DEFC = "#9aa4b2"
CAVF, CAVS = "#fdf0ef", "#efc2be"
CHG = "#6b2c87"
OKT = "#1a7a4c"


def f(k):
    return S[k]["f1"] if k and k in S and S[k].get("f1") is not None else None


def tile(x, y, w, key, gt, label, cap=None, msg="running…"):
    g = [real_image(x, y, w, w, R2 + "bf_roi.png", PX, 260, 50, label, "#111111"),
         vector_outlines_sub(x, y, w, w, R2 + f"{gt}.json", "manual annotation (vector)", REF, 1.3, DASH, ROI)]
    if key and _os.path.exists(R2 + f"{key}.json"):
        g.append(vector_outlines_sub(x, y, w, w, R2 + f"{key}.json", f"{label} (vector)", MODEL, 1.7, None, ROI))
    else:
        g.append(rrect(x, y, w, w, 2, "#ffffff", "none", extra=' fill-opacity="0.55"')
                 + t(x + w / 2, y + w / 2 + 5, msg, 14, "bold", "#56606e", "middle"))
    if cap:
        g.append(halo(x + 6, y + 17, cap, size=12.5))
    return group(label, "".join(g))


def bars(x, y, w, endo, cancer):
    """Main: endothelial F1 (default, before, after). Small: cancer-cell F1 (before, after) as thin bars."""
    g = [t(x, y, "F1 · endothelial cells", 13, "bold", INK)]
    bw = w - 40
    yy = y
    for lbl, k, kind in endo:
        yy += 30
        v = f(k)
        g.append(t(x, yy - 8, lbl, 12.5, "bold" if kind == "after" else "normal", INK if kind == "after" else BODY)
                 + f'<rect x="{x}" y="{yy-2}" width="{bw}" height="9" rx="3" fill="#e4e8ee"/>')
        g.append(t(x + bw + 6, yy + 7, "…" if v is None else f"{v:.2f}", 13, "bold", INK if v is not None else "#7a8699"))
        if v is not None:
            g.append(f'<rect x="{x}" y="{yy-2}" width="{bw*v:.1f}" height="9" rx="3" fill="{DEFC if kind == "default" else F1C}"/>')
    ax = x + bw * 0.897
    g.append(f'<line x1="{ax:.1f}" y1="{y+14}" x2="{ax:.1f}" y2="{yy+9}" stroke="{INK}" stroke-width="1.2" stroke-dasharray="2 2"/>')
    if cancer:
        yy += 24
        g.append(t(x, yy, "F1 · cancer cells", 12, "bold", "#5b6676"))
        for lbl, k in cancer:
            yy += 17
            v = f(k)
            g.append(t(x, yy, lbl, 11.5, fill="#5b6676") + f'<rect x="{x+92}" y="{yy-7}" width="{bw-92}" height="5" rx="2" fill="#e4e8ee"/>')
            if v is not None:
                g.append(f'<rect x="{x+92}" y="{yy-7}" width="{(bw-92)*v:.1f}" height="5" rx="2" fill="#8b96c9"/>'
                         + t(x + bw + 6, yy, f"{v:.2f}", 11.5, "bold", "#5b6676"))
            else:
                g.append(t(x + bw + 6, yy, "…", 11.5, "bold", "#7a8699"))
    return "".join(g)


def change_pill(cx, cy, lines, w=104):
    h = 16 + 15 * len(lines)
    return (f'<path d="M{cx-w/2},{cy-h/2} h{w-12} l12,{h/2} l-12,{h/2} h-{w-12} z" fill="{CHG}"/>'
            + t(cx - 4, cy - h / 2 + 20, lines, 12, "bold", "#ffffff", "middle", lh=15))


def tag(x, y, txt, col="#5b6676"):
    w = 7.2 * len(txt) + 16
    return rrect(x, y - 13, w, 19, 9, "#ffffff", col, 1.1) + t(x + w / 2, y + 1, txt, 11.5, "bold", col, "middle")


# ---------------------------------------------------------------- grid
Y0 = 20
LW_ = 64
RX = 28 + LW_ + 10
RW = 1812 - RX
CX_ASK, W_ASK = RX + 18, 352
TS = 178
CX_T1 = CX_ASK + W_ASK + 18
CX_P = CX_T1 + TS + 8
CX_T2 = CX_P + 116
CX_F1 = CX_T2 + TS + 22
W_F1 = 226
CX_CAV = CX_F1 + W_F1 + 22
W_CAV = 1812 - 14 - CX_CAV
GAP = 10
RHS = {"a": 214, "b1": TS + 62, "b2": TS + 62, "c": TS + 62, "d": TS + 62}

HDH = 84
add(group("task", rrect(RX, Y0, RW, HDH, 14, "#ffffff", NN["stroke"], 1.3)
          + real_image(RX + 12, Y0 + 9, 66, 66, BF + "draw/bf_full.png", PX, 1024, 0, "task: full field")
          + rrect(RX + 12 + 760 / 1024 * 66, Y0 + 9 + 240 / 1022 * 66, 260 / 1024 * 66, 260 / 1022 * 66, 0, "none", REF2, 1.6)
          + t(RX + 94, Y0 + 34, "One brightfield field, two tasks: endothelial cells (hard; tiles) and cancer cells (easy; small bars)", 18.5, "bold", INK)
          + t(RX + 94, Y0 + 60, "Claude Sonnet, Oct 2026 · each row: one change suggested in the text · F1 against manual annotation (382 endothelial, 124 cancer cells) · illustration, one field", 13.5, fill=BODY)
          + key_item(1812 - 470, Y0 + 30, MODEL, "LLM-derived result") + key_item(1812 - 310, Y0 + 30, REF, "manual annotation", DASH)
          + f'<rect x="{1812-470}" y="{Y0+50}" width="20" height="7" rx="2.5" fill="{DEFC}"/>' + t(1812 - 444, Y0 + 58, "Cellpose default", 13, fill=BODY)
          + f'<line x1="{1812-310+11}" y1="{Y0+48}" x2="{1812-310+11}" y2="{Y0+64}" stroke="{INK}" stroke-width="1.2" stroke-dasharray="2 2"/>'
          + t(1812 - 310 + 28, Y0 + 60, "two annotators agree (0.90)", 13, fill=BODY)))

ORDER = [("a", "Ask for advice"), ("b1", "Ask for code: Fiji macro"), ("b2", "Ask for code: Python script"),
         ("c", "Let an agent run it"), ("d", "Ask for the answer")]
ry = {}
yy = Y0 + HDH + GAP
for key, _ in ORDER:
    ry[key] = yy
    yy += RHS[key] + GAP
for key, ttl in ORDER:
    y = ry[key]
    L = key[0] if key[0] != "b" else key
    add(group(f"row {key}", rrect(RX, y, RW, RHS[key], 16, NN["bg"], NN["stroke"], 1.4)
              + f'<circle cx="{CX_ASK+15}" cy="{y+24}" r="15" fill="{ACC}"/>' + t(CX_ASK + 15, y + 30, L if len(L) == 1 else "b", 17, "bold", "#fff", "middle")
              + t(CX_ASK + 40, y + 30, ttl, 18, "bold", INK)
              + rrect(CX_CAV - 8, y + 9, W_CAV + 14, RHS[key] - 18, 12, CAVF, CAVS, 1.2)))


def cav(key, title):
    y = ry[key]
    return caution(CX_CAV + 12, y + 30, NOC) + t(CX_CAV + 32, y + 35, title, 14.5, "bold", NOC, lh=18)


def ask(key, items, y0=46):
    y = ry[key] + y0
    for tg, lines in items:
        if tg:
            add(t(CX_ASK + 46, y + 2, tg, 12, "bold", CHG)); y += 6
        s, h = prompt(CX_ASK, y, W_ASK, lines, 12.5); add(s); y += h - 2


def pair(key, t1, t2, pill, msg2="running…"):
    y = ry[key] + 44
    add(tile(CX_T1, y, TS, *t1))
    add(change_pill(CX_P + 50, y + TS / 2, pill))
    add(tile(CX_T2, y, TS, *t2, msg=msg2))


# ================================================================ a: advice (text only)
key = "a"
ask(key, [("before", ["“Which tool, model and settings would you", "recommend? I don't need code.”"]),
          ("after", ["“…Do not rely on your memory: check the", "current documentation first.”"])])
y = ry[key] + 44
WB = 300
s, hA = reply(CX_T1, y, WB, ["“Start with the newest generalist", "model available to you, either", "Cellpose-SAM (Cellpose 4) or cyto3.”", "“…try the cyto3 denoise or", "deblur models.”"],
              12.5, False, "From memory (excerpt)"); add(s)
add(t(CX_T1 + 4, y + hA + 6, "Offers models removed in Cellpose 4", 12.5, "bold", NOC))
add(change_pill(CX_T1 + WB + 62, y + 62, ["read the", "docs"]))
XD = CX_T1 + WB + 122
s, hB = reply(XD, y, CX_CAV - 30 - XD, ["“The docs list these built-in models: cpsam_v2 …,", "cpdino …, cpdino-vitb …, and the original cpsam.”", "“The old cyto3 and nuclei models are not mentioned", "in the current docs, and the old models.Cellpose", "class was removed in Cellpose 4.”"],
              12.5, False, "After reading the docs (excerpt)"); add(s)
add(t(XD + 4, y + hB + 6, "Names the current models and the pages it read", 12.5, "bold", OKT))
add(cav(key, ["Outdated advice can run without error;", "only the documentation reveals it"]))
s, _ = terminal(CX_CAV + 12, ry[key] + 60, W_CAV - 12, [(">>> CellposeModel(pretrained_model='cyto3')", "#d5dbe5"),
                                                       ("            (no message)", "#8a94a3"),
                                                       (">>> m.pretrained_model  →  '…/cpsam_v2'", "#ff8a80")], 12.5); add(s)
add(t(CX_CAV + 12, ry[key] + RHS[key] - 28, "The default model is loaded; the analysis runs normally.", 13, fill=INK))

# ================================================================ b1: Fiji macro
key = "b1"
ask(key, [("before", ["“Please write a Fiji macro to segment the", "endothelial cells in my image.”"]),
          ("after: Box 1", ["“…built-in commands or maintained plugins,", "0.65 µm/px, cells 25–50 µm, expose parameters,", "compare with my annotation, save an overlay…”"])])
add(tag(CX_ASK + 46, ry[key] + RHS[key] - 16, "runs in Fiji · no setup"))
pair(key, ("fj_gen_endo", "gt_endo", "Fiji macro, generic", "generic"), ("fj_box1_endo", "gt_endo", "Fiji macro, Box 1", "Box 1"), ["Box 1", "prompt"],
     msg2="not run yet")
add(bars(CX_F1, ry[key] + 44, W_F1, [("Cellpose default", "default_endo", "default"), ("generic prompt", "fj_gen_endo", "before"), ("Box 1 prompt", "fj_box1_endo", "after")],
         [("generic", "fj_gen_cancer"), ("Box 1", "fj_box1_cancer")]))
add(cav(key, ["(result-dependent) e.g. “The macro ran;", "only the overlay test showed it failed”"]))
add(t(CX_CAV + 12, ry[key] + 92, ["Placeholder: excerpt of the parameter list,", "or the plugin the macro needs but plain Fiji", "does not have."], 13, fill="#7a8699", lh=18))

# ================================================================ b2: Python script
key = "b2"
ask(key, [("before", ["“Please write a Python script to segment the", "endothelial cells in my image.”"]),
          ("after: Box 1", ["“…check the documentation… 0.65 µm/px, cells", "25–50 µm… state consequential parameters,", "defaults and transformations…”"])])
add(tag(CX_ASK + 46, ry[key] + RHS[key] - 16, "needs Python + Cellpose (e.g. a notebook)"))
pair(key, ("cG_endo", "gt_endo", "Python, generic", "generic"), ("b1_endo_med", "gt_endo", "Python, Box 1", "Box 1"), ["Box 1", "prompt"])
add(bars(CX_F1, ry[key] + 44, W_F1, [("Cellpose default", "default_endo", "default"), ("generic prompt", "gen_endo_med", "before"), ("Box 1 prompt", "box1_endo_med", "after")],
         [("generic", "gen_cancer_med"), ("Box 1", "box1_cancer_med")]))
add(cav(key, ["Exposing the parameters makes the choice", "visible; only the test shows if it works"]))
s, _ = reply(CX_CAV + 12, ry[key] + 66, W_CAV - 12, ["diameter | 58 px | No  | 37.5 µm / 0.65 µm/px", "diameter | None  | Yes | “no rescaling…”"], 12, True,
             "Box 1 replies, same prompt, two runs (excerpt)"); add(s)

# ================================================================ c: agent
key = "c"
ask(key, [("before", ["“Please run the analysis pipeline, assess the", "result, improve the analysis…”"]),
          ("after", ["“…Score every version against my annotation…", "other images are held out for a final check.”"])])
pair(key, ("ag_endo", "gt_endo", "agent judging by eye", "judged by eye"), ("ref_endo", "gt_endo", "agent with reference data", "scored · held-out"),
     ["give it an", "objective"])
add(bars(CX_F1, ry[key] + 44, W_F1, [("Cellpose default", "default_endo", "default"), ("judged by eye", "agent_endo", "before"), ("scored, held-out half", "ref_endo_heldout", "after")],
         [("by eye", "agent_cancer"), ("held-out", "ref_cancer_heldout")]))
add(cav(key, ["Without an external objective, it judged", "its result by eye"]))
y = ry[key]
REFD = S.get("ref_endo_dev_reported")
rowsC = [("by eye", "“match … well”", f"F1 {f('agent_endo'):.2f}"),
         ("scored", f"F1 {REFD:.2f} (dev)" if REFD else "…", f"F1 {f('ref_endo_heldout'):.2f} (held-out)" if f('ref_endo_heldout') else "…")]
add(t(CX_CAV + 150, y + 74, "it reported", 12.5, "bold", CHG, "middle") + t(CX_CAV + 300, y + 74, "we measured", 12.5, "bold", INK, "middle"))
for i, (lbl, said, meas) in enumerate(rowsC):
    yy = y + 100 + i * 26
    add(t(CX_CAV + 12, yy, lbl, 13, "bold", BODY) + t(CX_CAV + 150, yy, said, 13.5, "bold", CHG, "middle")
        + t(CX_CAV + 300, yy, meas, 13.5, "bold", NOC, "middle"))
add(t(CX_CAV + 12, y + RHS[key] - 26, "Fix the workflow, then test it on data it never saw.", 13, fill=INK))

# ================================================================ d: answer — number only -> outlines
key = "d"
ask(key, [("before · 3 runs", ["“How many endothelial cells are in this image?”"]),
          ("after · 3 runs", ["“Please draw around every endothelial cell", "in this image and count them.”"])])
y = ry[key] + 44
# before: numbers only (strip in the tile slot)
add(rrect(CX_T1, y, TS, TS, 4, "#ffffff", NN["stroke"], 1.2) + t(CX_T1 + 10, y + 22, "answers (number only)", 12.5, "bold", INK))
sx0, sx1 = CX_T1 + 16, CX_T1 + TS - 16
X = lambda v: sx0 + v / 500 * (sx1 - sx0)
g = [f'<line x1="{sx0}" y1="{y+100}" x2="{sx1}" y2="{y+100}" stroke="#c9d1dc" stroke-width="1.2"/>',
     f'<rect x="{X(382):.1f}" y="{y+86}" width="{X(462)-X(382):.1f}" height="28" fill="{INK}" fill-opacity="0.12"/>',
     f'<line x1="{X(382):.1f}" y1="{y+84}" x2="{X(382):.1f}" y2="{y+116}" stroke="{INK}" stroke-width="2" stroke-dasharray="4 3"/>',
     t(X(382), y + 78, "manual", 11.5, "bold", INK, "middle")]
for i, v in enumerate(S["counts_asked"]["endo"]):
    g.append(f'<circle cx="{X(v):.1f}" cy="{y+100}" r="5.5" fill="{MCOL["sonnet"]}" stroke="#fff" stroke-width="1"/>')
for v in (0, 250, 500):
    g.append(t(X(v), y + 132, str(v), 11, fill="#7a8699", anchor="middle"))
g.append(t(CX_T1 + 10, y + 160, ["100, 170, 200 cells", "(manual: 382)"], 12.5, "bold", NOC, lh=15))
add(group("number only", "".join(g)))
add(change_pill(CX_P + 50, y + TS / 2, ["ask for the", "outlines"]))
add(tile(CX_T2, y, TS, "d_endo_r3", "gt_endo", "drawn, run 3", "drawn · run 3"))
add(bars(CX_F1, ry[key] + 44, W_F1, [("Cellpose default", "default_endo", "default"), ("drawn, run 1", "draw_endo_r1", "after"),
                                     ("drawn, run 2", "draw_endo_r2", "after"), ("drawn, run 3", "draw_endo_r3", "after")], None))
add(cav(key, ["The outlines showed the numbers were", "estimated, not counted"]))
add(t(CX_CAV + 12, ry[key] + 86, ["“These 20 hexagons are a rough placeholder", "grid, not traced outlines.”  (run 3)"], 13.5, fill=CHG, style="italic", lh=18))
add(t(CX_CAV + 12, ry[key] + 140, ["Drawn: 12, 30, 20 cells. Asked for a number:", "100, 170, 200. Manual: 382."], 13, fill=INK, lh=18))
add(t(CX_CAV + 12, ry[key] + RHS[key] - 26, "Cancer cells: drawn well in 2 of 3 runs (F1 0.56–0.90).", 12.5, fill="#5b6676"))

# ================================================================ delegation arrow
AT, AB = ry["a"], ry["d"] + RHS["d"]
defs.append(f'<linearGradient id="deleg" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#d9cbea"/><stop offset="1" stop-color="{ACC}"/></linearGradient>')
AXc = 28 + LW_ / 2
add(group("delegation arrow", f'<path d="M{AXc-20},{AT} H{AXc+20} V{AB-26} H{AXc+30} L{AXc},{AB} L{AXc-30},{AB-26} H{AXc-20} Z" fill="url(#deleg)"/>'
          + f'<text x="{AXc+6}" y="{(AT+AB)/2}" font-size="15" font-weight="bold" fill="#ffffff" text-anchor="middle" '
            f'transform="rotate(-90 {AXc+6} {(AT+AB)/2})">more of the analysis happens inside the LLM interaction</text>'))

# ================================================================ what to keep
KY = ry["d"] + RHS["d"] + GAP
KH = 108
add(group("keep frame", rrect(28, KY, 1784, KH, 16, "#ffffff", NN["stroke"], 1.4)
          + t(48, KY + 30, "Regardless of the level of delegation, test quantitative use on representative images with reference outputs", 17, "bold", INK)))
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
    add(group(f"keep {a_}", kicon(ic, x + 20, KY + 72, ACC) + t(x + 48, KY + 68, a_, 14, "bold", INK) + t(x + 48, KY + 88, b_, 13, fill=BODY)))

H = KY + KH + 20
svg = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
       f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" xmlns:xlink="http://www.w3.org/1999/xlink" '
       f'width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">\n'
       f'<defs>{"".join(defs)}</defs>\n<rect width="{W}" height="{H}" fill="#ffffff"/>\n'
       + "\n".join(out) + "\n</svg>\n")
open("fig3_v7.svg", "w", encoding="utf-8").write(svg)
print("written", len(svg) // 1024, "KB; height", H)
