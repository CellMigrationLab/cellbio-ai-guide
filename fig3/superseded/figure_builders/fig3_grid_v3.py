# ======================================================================= FIGURE 3: example / LLM output / caveat / evidence
LW = 112                                   # row-label column
GX = 28 + LW + 8
CWg = (1812 - GX - 3 * 8) / 4
colx = [GX + i * (CWg + 8) for i in range(4)]
IP = 14
IW = CWg - 2 * IP
Y0 = 20
HD = 66
ROWS = [("Example", 108), ("LLM output", 196), ("Caveat", 96), ("Example of the caveat", 372)]
ry = [Y0 + HD]
for _, hh in ROWS:
    ry.append(ry[-1] + hh + 8)
GRID_B = ry[-1] - 8
CAVF, CAVS = "#fdf0ef", "#efc2be"
# row labels
for k, (lbl, hh) in enumerate(ROWS):
    add(group(f"row label {lbl}", rrect(28, ry[k], LW, hh, 10, "#eef2f7" if k != 2 else CAVF, NN["stroke"] if k != 2 else CAVS, 1.2)
              + t(28 + LW / 2, ry[k] + hh / 2 - (9 if " " in lbl and len(lbl) > 12 else 0) + 5,
                  ["Example of", "the caveat"] if lbl.startswith("Example of") else (["LLM", "output"] if lbl == "LLM output" else lbl),
                  15, "bold", INK if k != 2 else NOC, "middle", lh=18)))
# column frames + headers
HEAD = [("Ask for advice", "software, parameters, approaches"), ("Ask for code", "e.g. Python, Fiji macro"),
        ("Let an agent run it", "runs and optimises the workflow"), ("Ask for the answer", "multimodal model, direct answer")]
for i, (ttl, sub) in enumerate(HEAD):
    x = colx[i]
    add(group(f"column {i+1}", rrect(x, Y0, CWg, GRID_B - Y0, 16, NN["bg"], NN["stroke"], 1.4)
              + f'<circle cx="{x+34}" cy="{Y0+34}" r="19" fill="{ACC}"/>' + t(x + 34, Y0 + 41, str(i + 1), 20, "bold", "#fff", "middle")
              + t(x + 62, Y0 + 31, ttl, 19, "bold", INK) + t(x + 62, Y0 + 51, sub, 13.5, fill=BODY)
              + rrect(x + 6, ry[2], CWg - 12, ROWS[2][1], 10, CAVF, CAVS, 1.2)))


def cav(i, lines):
    x = colx[i] + IP
    add(group(f"caveat {i+1}", caution(x + 10, ry[2] + 22, NOC) + t(x + 30, ry[2] + 27, lines, 13.5, fill=INK, lh=18)))



V3 = "v3/"
OKT, MIDT, BADT = "#1a7a4c", "#c27c0e", NOC


def colour(v, lo, hi):
    if lo <= v <= hi:
        return OKT
    err = (lo - v) / lo if v < lo else (v - hi) / hi
    return MIDT if err <= 0.25 else BADT


# ================================================================ 1 advice
x = colx[0] + IP
s, h = prompt(x, ry[0] + 6, IW, ["2D DAPI images, touching nuclei, 0.65 µm/px.", "Which tool, model and settings would you", "recommend to measure nuclear area? No code."], 13.5); add(s)
s, h = reply(x, ry[1] + 6, IW, ["“Recommended: Cellpose, `nuclei` model", " (or cpsam in Cellpose 4) … Diameter:", " start at about 20 px … Flow threshold:", " keep the default of 0.4 … Mitotic or", " apoptotic nuclei are small and bright,", " so exclude them if you want interphase", " area.”"], mono=False, size=13,
             title="Claude Sonnet, excerpt (similar in 3/3 runs)"); add(s)
cav(0, ["Answers can sound convincing yet use an", "outdated API, a non-existent parameter or an", "unsuitable method. Verify against the docs."])
y = ry[3] + 10
add(t(x, y + 6, "Advised settings, run with the installed Cellpose 4.2.1.1:", 13.5, "bold", INK))
s, h = terminal(x, y + 16, IW, [(">>> m = models.CellposeModel(", "#d5dbe5"), ("...     model_type='nuclei')", "#d5dbe5"),
                                ("                    (no message)", "#8a94a3"),
                                (">>> m.pretrained_model", "#d5dbe5"), ("'.../models/cpsam_v2'", "#ff8a80")]); add(s)
y += h + 26
chk = [("'nuclei' model", "silently ignored; Cellpose-SAM runs", BADT, "✗"),
       ("diameter 20, flow 0.4, prob 0", "runs; nuclei F1 0.93", OKT, "✓"),
       ("exclude mitotic nuclei", "a biological choice, not a setting", MIDT, "!")]
for k_, (a_, b_, col, mk) in enumerate(chk):
    yy = y + k_ * 40
    add(t(x + 8, yy + 14, mk, 17, "bold", col, "middle") + t(x + 24, yy + 8, a_, 13, "bold", INK) + t(x + 24, yy + 26, b_, 13, fill=BODY))
add(note(x, y + 3 * 40 + 14, ["Following the advice, the methods would name a", "model that was never used."]))

# ================================================================ 2 code
x = colx[1] + IP
RG = json.load(open(V3 + "code_generic_score.json")); RS = json.load(open(V3 + "code_specific_score.json"))
CR = json.load(open("assets/code_roi.json"))
hw = (IW - 10) / 2
for k_, (ttl, lines) in enumerate([("Generic prompt", ["“Please analyse this image", "and segment the nuclei.”", "(nuclei.tif attached)"]),
                                   ("Specific prompt", ["“…use Cellpose 4; pixel size", "0.65 µm; nuclei 10–20 µm; do", "not resize or normalise; save", "areas in µm².”"])]):
    xx = x + k_ * (hw + 10)
    add(t(xx, ry[0] + 18, ttl, 14, "bold", INK) + rrect(xx, ry[0] + 26, hw, 76, 8, "#ffffff", "#b8c2d0", 1.2)
        + t(xx + 8, ry[0] + 43, lines, 12, fill=INK, lh=16))
for k_, (ttl, lines) in enumerate([("excerpt, generic prompt", ["PIXEL_SIZE_UM = None  # set", "  e.g. 0.65 to get areas", "  in um^2", "LOCAL_BLOCK = 51", "MIN_DIST    = 4", "“I estimated them from a", " downsampled preview.”"]),
                                   ("excerpt, specific prompt", ["model = models.", "  CellposeModel(gpu=False)", "masks, flows, styles =", "  model.eval(img)", "area_um2 = p.area *", "  PIXEL_SIZE_UM ** 2"])]):
    xx = x + k_ * (hw + 10)
    add(rrect(xx, ry[1] + 6, hw, ROWS[1][1] - 12, 8, LL["tint"], LL["tintstroke"], 1.2)
        + t(xx + 8, ry[1] + 24, ttl, 12, "bold", "#6b2c87") + t(xx + 8, ry[1] + 44, lines, 11, fill=INK, lh=17, extra=MONO))
cav(1, ["Code that runs is not necessarily the intended", "analysis. Specify the measurement and units;", "test on images with a known result."])
y = ry[3] + 10
for k_, key in enumerate(["generic", "specific"]):
    xx = x + k_ * (hw + 10)
    add(group(f"2 {key} tile", real_image(xx, y, hw, hw, V3 + "assets/code_dapi.png", PX, CR["w"], 20, f"2 {key}")
              + vector_outlines_sub(xx, y, hw, hw, V3 + "assets/code_manual.json", "manual nuclei (vector)", REF, 1.4, DASH, (0, 0, CR["w"], CR["w"]))
              + vector_outlines_sub(xx, y, hw, hw, V3 + f"assets/code_{key}.json", f"{key} code (vector)", MODEL, 1.4, None, (0, 0, CR["w"], CR["w"]))
              + halo(xx + 6, y + 16, key)))
add(key_item(x, y + hw + 18, MODEL, "LLM-written code") + key_item(x + 170, y + hw + 18, REF, "manual nuclei", DASH))
yy0 = y + hw + 42
rows_ = [("runs without error", "yes", "yes", INK, INK), ("nuclei F1", f"{RG['f1']:.2f}", f"{RS['f1']:.2f}", BADT, OKT),
         ("area vs manual", f"×{RG['area_ratio_median']:.2f}", f"×{RS['area_ratio_median']:.2f}", BADT, OKT),
         ("units", "pixels", "µm²", BADT, OKT)]
for i, (lbl, a_, b_, ca, cb) in enumerate(rows_):
    yy = yy0 + i * 19
    add(t(x, yy, lbl, 13, fill=BODY) + t(x + hw / 2 + 60, yy, a_, 13, "bold", ca, "middle") + t(x + hw + 10 + hw / 2, yy, b_, 13, "bold", cb, "middle"))

# ================================================================ 3 agent
x = colx[2] + IP
AR = json.load(open(V3 + "agent_rerun.json")) if os.path.exists(V3 + "agent_rerun.json") else None
RA = json.load(open(V3 + "code_agent_score.json"))
s, h = prompt(x, ry[0] + 6, IW, ["Please run the analysis pipeline on", "nuclei.tif, assess the result, improve", "the analysis, and give me the result."], 13.5); add(s)
s, h = reply(x, ry[1] + 6, IW, ["“I segmented 598 nuclei, and the outlines", " look good on a visual check of the", " overlay. I did not measure accuracy", " against hand-drawn ground truth.", " … I applied the final 95 px size filter", " to the saved labels rather than", " re-running Cellpose.”"], mono=False, size=13,
             title="Claude Sonnet agent, report (excerpt)"); add(s)
cav(2, ["Decisions between image and result can be", "hidden in the agent's code. Review every", "change; keep a workflow that reruns."])
y = ry[3] + 10
TS2 = 168
add(group("3 agent tile", real_image(x, y, TS2, TS2, V3 + "assets/code_dapi.png", PX, CR["w"], 20, "3 agent")
          + vector_outlines_sub(x, y, TS2, TS2, V3 + "assets/code_manual.json", "manual nuclei (vector)", REF, 1.3, DASH, (0, 0, CR["w"], CR["w"]))
          + vector_outlines_sub(x, y, TS2, TS2, V3 + "assets/code_agent.json", "agent result (vector)", MODEL, 1.3, None, (0, 0, CR["w"], CR["w"]))))
dx = x + TS2 + 14
add(t(dx, y + 12, "Decided without being asked:", 13, "bold", INK))
for k_, ln in enumerate(["background subtraction", "re-normalisation", "diameter 20 px", "probability threshold −1", "remove objects < 40 µm²"]):
    add(f'<circle cx="{dx+5}" cy="{y+31+k_*19}" r="2.6" fill="{INK}"/>' + t(dx + 13, y + 35 + k_ * 19, ln, 12.5, fill=BODY))
y2 = y + TS2 + 22
add(t(x, y2, "Our checks", 13.5, "bold", INK))
checks = [("accuracy vs manual nuclei (not measured by the agent)", f"F1 {RA['f1']:.2f}", OKT)]
if AR:
    checks.append(("final pipeline.py rerun from scratch", AR["verdict"], OKT if AR["identical"] else BADT))
else:
    checks.append(("final pipeline.py rerun from scratch", "running…", "#7a8699"))
for k_, (a_, b_, col) in enumerate(checks):
    add(t(x, y2 + 22 + k_ * 20, a_, 12.5, fill=BODY) + t(x + IW, y2 + 22 + k_ * 20, b_, 12.5, "bold", col, "end"))
add(note(x, y2 + 70, ["The result is good, but the agent judged it by", "eye and never reran its own final pipeline."]))

# ================================================================ 4 direct answer
x = colx[3] + IP
TR = json.load(open(V3 + "full/truth.json")); ANS = json.load(open(V3 + "full/answers.json"))
TRR = {"cells_pecam": (TR["cells_pecam"]["cells_complete"], TR["cells_pecam"]["cells_incl_border"]),
       "nuclei_dapi": (TR["nuclei_dapi"]["endothelial_nuclei"], TR["nuclei_dapi"]["endothelial_nuclei"] + TR["nuclei_dapi"]["cancer_cells"]),
       "cancer_bf": (TR["cancer_bf"]["cancer_cells"], TR["cancer_bf"]["cancer_cells"])}
th = 70
for k_, (fn, lbl) in enumerate([("pecam_full.png", "PECAM-1"), ("dapi_full.png", "DAPI"), ("bf_full.png", "brightfield")]):
    xx = x + k_ * (th + 8)
    add(real_image(xx, ry[0] + 6, th, th, V3 + "full/" + fn, PX, 1024, 0, f"4 {lbl}") + halo(xx + 3, ry[0] + 19, lbl, size=10.5))
add(t(x + 3 * (th + 8) + 4, ry[0] + 22, ["Whole field:", "how many cells /", "nuclei / cancer", "cells?"], 13, fill=INK, lh=16))
add(t(x, ry[0] + th + 28, "(asked 3 times of each of 3 models)", 12, fill=BODY))
# output: answer table
y = ry[1] + 10
add(rrect(x, y - 4, IW, ROWS[1][1] - 12, 8, LL["tint"], LL["tintstroke"], 1.2))
cx0 = [x + 84, x + 162, x + 240]
add(t(x + 8, y + 14, "Claude", 12, "bold", "#6b2c87"))
for mi, m in enumerate(("Haiku", "Sonnet", "Opus")):
    add(t(cx0[mi] + 35, y + 14, m, 12.5, "bold", MCOL[m.lower()], "middle"))
add(t(x + IW - 8, y + 14, "manual", 12.5, "bold", INK, "end"))
for r_, (key, lbl) in enumerate([("cells_pecam", "cells"), ("nuclei_dapi", "nuclei"), ("cancer_bf", "cancer")]):
    yy = y + 46 + r_ * 44
    lo, hi = TRR[key]
    add(t(x + 8, yy, lbl, 13, "bold", INK))
    for mi, m in enumerate(("haiku", "sonnet", "opus")):
        for ri in range(3):
            v = ANS[m][ri][key]
            add(t(cx0[mi] + 10 + ri * 25, yy, str(v), 12, "bold", colour(v, lo, hi), "middle"))
    add(t(x + IW - 8, yy, f"{lo}–{hi}" if lo != hi else str(lo), 12.5, "bold", INK, "end"))
add(t(x + 8, y + ROWS[1][1] - 24, "within range", 11.5, "bold", OKT) + t(x + 92, y + ROWS[1][1] - 24, "≤ 25% off", 11.5, "bold", MIDT)
    + t(x + 160, y + ROWS[1][1] - 24, "> 25% off", 11.5, "bold", BADT))
cav(3, ["The analysis is hidden, outputs are not", "deterministic and models change; models can", "also invent plausible image content."])
y = ry[3] + 10
DS = json.load(open(V3 + "draw/draw_scores.json")); DA = json.load(open(V3 + "draw/answers.json"))
add(t(x, y + 6, "“Draw the nuclei in this brightfield image.”", 13.5, "bold", INK))
y += 16
tw = (IW - 16) / 3
tiles = [(V3 + "draw/bf_roi.png", "brightfield"), (V3 + "draw/llm_dapi_opus.png", "LLM-drawn (Opus)"), (V3 + "draw/dapi_roi.png", "acquired DAPI")]
for k_, (png, lbl) in enumerate(tiles):
    xx = x + k_ * (tw + 8)
    g = [real_image(xx, y, tw, tw, png, PX * 200 / 512, 512, 0, f"4 draw {lbl}")]
    if k_ == 2:
        kk = tw / 512
        for e in DA["opus"]:
            g.append(f'<ellipse cx="{xx+e["x"]*kk:.1f}" cy="{y+e["y"]*kk:.1f}" rx="{e["rx"]*kk:.1f}" ry="{e["ry"]*kk:.1f}" '
                     f'transform="rotate({e["angle_deg"]} {xx+e["x"]*kk:.1f} {y+e["y"]*kk:.1f})" fill="none" stroke="{MODEL}" stroke-width="1.3"/>')
    g.append(halo(xx + 4, y + 14, lbl, size=10.5))
    add(group(f"4 draw {k_}", "".join(g)))
y += tw + 18
add(t(x, y, f"Real nuclei in the field: {DS['n_true']}", 13, "bold", INK))
for mi, m in enumerate(("haiku", "sonnet", "opus")):
    d = DS[m]
    add(t(x, y + 22 + mi * 19, f"{m.capitalize()}: drew {d['n_drawn']}, {d['tp']} at a real nucleus, {d['fn']} missed", 12.5, fill=BODY))
add(note(x, y + 22 + 3 * 19 + 10, ["Plausible-looking, regularly spaced nuclei", "were drawn where none are."]))

# ================================================================ arrow: giving more to the model
AY = GRID_B + 12
defs.append(f'<linearGradient id="deleg" x1="0" x2="1"><stop offset="0" stop-color="#d9cbea"/><stop offset="1" stop-color="{ACC}"/></linearGradient>')
add(group("delegation arrow", f'<path d="M{GX},{AY} H1790 L1812,{AY+17} L1790,{AY+34} H{GX} Z" fill="url(#deleg)"/>'
          + t(GX + 14, AY + 23, "More of the analysis visible and controllable", 15, "bold", "#4a2a63")
          + t(1780, AY + 23, "More of the analysis delegated to, and hidden in, the LLM", 15, "bold", "#ffffff", "end")))

# ================================================================ final row: what to keep
KY = AY + 46
KH = 128
add(group("keep row label", rrect(28, KY, LW, KH, 10, "#eef2f7", NN["stroke"], 1.2) + t(28 + LW / 2, KY + KH / 2 - 4, ["What to", "keep"], 15, "bold", INK, "middle", lh=18)))
boxes = [(GX, 3 * CWg + 2 * 8, "Uses 1–3: keep the analysis, not the conversation",
          ["Save the code, configuration, consequential parameters, software versions and, where practical, the",
           "computational environment. The final analysis should rerun from these files without the LLM.",
           "Record which LLM and version was used, when, and for which step."]),
         (colx[3], CWg, "Use 4: the LLM is part of the analysis",
          ["Also keep the prompts and model version; the", "same input may not give the same answer again.", "Validate against reference data."])]
for bx, bw, ttl, lines in boxes:
    add(group(f"keep {ttl}", rrect(bx, KY, bw, KH, 12, "#ffffff", NN["stroke"], 1.3) + t(bx + 16, KY + 26, ttl, 15.5, "bold", INK)
              + t(bx + 16, KY + 52, lines, 13.5, fill=BODY, lh=19)))
add(t(GX, KY + KH + 22, "In all cases: check where images are sent (provider terms, institutional or local models). The authors remain responsible for every step.", 13, "bold", "#4a2a63"))

H = KY + KH + 40
svg = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
       f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" xmlns:xlink="http://www.w3.org/1999/xlink" '
       f'width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">\n'
       f'<defs>{"".join(defs)}</defs>\n<rect width="{W}" height="{H}" fill="#ffffff"/>\n'
       + "\n".join(out) + "\n</svg>\n")
open("fig3_v3.svg", "w", encoding="utf-8").write(svg)
print("written", len(svg) // 1024, "KB; height", H)
