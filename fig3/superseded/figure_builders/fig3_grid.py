# ======================================================================= FIGURE 3: example / LLM output / caveat / evidence
LW = 112                                   # row-label column
GX = 28 + LW + 8
CWg = (1812 - GX - 3 * 8) / 4
colx = [GX + i * (CWg + 8) for i in range(4)]
IP = 14
IW = CWg - 2 * IP
Y0 = 20
HD = 66
ROWS = [("Example", 104), ("LLM output", 178), ("Caveat", 96), ("Example of the caveat", 392)]
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


# ================================================================ 1 advice
x = colx[0] + IP
s, h = prompt(x, ry[0] + 8, IW, ["How should I segment nuclei in 2D DAPI", "images with Cellpose in Python? Which", "model and parameters should I use?"], 13.5); add(s)
s, h = reply(x, ry[1] + 6, IW, ['“…start with Cellpose\'s `nuclei` model…', ' Set `diameter` to your nuclei size', ' in pixels.”', 'model = models.Cellpose(gpu=True,', '    model_type="nuclei")', 'masks, flows, styles, diams =', '    model.eval(img, diameter=30, ...)'],
             title="Claude Sonnet, excerpt (Cellpose 3 example in 3/3 runs)", size=12.5); add(s)
cav(0, ["Answers can sound convincing yet use an", "outdated API, a non-existent parameter or an", "unsuitable method. Verify against the docs."])
y = ry[3] + 10
add(t(x, y + 6, "Run as given (Cellpose 4.2.1.1 installed):", 13.5, "bold", INK))
s, h = terminal(x, y + 16, IW, [(">>> models.Cellpose(model_type='nuclei')", "#d5dbe5"),
                                ("AttributeError: module 'cellpose.models'", "#ff8a80"), ("  has no attribute 'Cellpose'", "#ff8a80")]); add(s)
y += h + 22
add(t(x, y + 6, "Variant from the same reply:", 13.5, "bold", INK))
s, h2 = terminal(x, y + 16, IW, [(">>> models.CellposeModel(model_type='nuclei')", "#d5dbe5"),
                                 ("WARNING model_type argument is not used", "#ffd166"), ("  in v4.0.1+. Ignoring this argument...", "#ffd166"),
                                 ("loading model cpsam_v2", "#9be7a1")]); add(s)
add(note(x, y + h2 + 36, ["The 'nuclei' model no longer exists: the code", "fails, or runs another model with only a warning."]))

# ================================================================ 2 code
x = colx[1] + IP
RES = {k: json.load(open(f"codetest/{k}/result.json")) for k in ("vague", "box1")}
CR = json.load(open("assets/code_roi.json"))
hw = (IW - 10) / 2
for k_, (ttl, lines) in enumerate([("Vague prompt", ["“Measure nuclear area", "in nuclei.tif.”"]),
                                   ("Box 1 prompt", ["“…pixel size 0.65 µm;", "no silent resizing; expose", "parameters; add a test.”"])]):
    xx = x + k_ * (hw + 10)
    add(t(xx, ry[0] + 20, ttl, 14, "bold", INK) + rrect(xx, ry[0] + 28, hw, 66, 8, "#ffffff", "#b8c2d0", 1.2)
        + t(xx + 8, ry[0] + 46, lines, 12, fill=INK, lh=16))
for k_, (ttl, lines) in enumerate([("excerpt, vague prompt", ["mask = corrected >", "  filters.threshold_otsu(", "    corrected)", "labels = segmentation", "  .watershed(...)", 'header = ["nucleus_id",', '  "area_px"]']),
                                   ("excerpt, Box 1 prompt", ["def segment_nuclei(image,", "  pixel_size_um, ...):", "  if image.ndim != 2:", "    raise ValueError(", "      f\"Expected a 2D", "      (Y, X) image…\")", "def test_segmentation():"])]):
    xx = x + k_ * (hw + 10)
    add(rrect(xx, ry[1] + 6, hw, ROWS[1][1] - 12, 8, LL["tint"], LL["tintstroke"], 1.2)
        + t(xx + 8, ry[1] + 24, ttl, 12, "bold", "#6b2c87") + t(xx + 8, ry[1] + 42, lines, 11, fill=INK, lh=17, extra=MONO))
add(t(x, ry[1] + ROWS[1][1] + 1, "", 1))
cav(1, ["Code that runs is not necessarily the intended", "analysis. Specify the measurement and units;", "test on images with a known result."])
y = ry[3] + 10
for k_, key in enumerate(["vague", "box1"]):
    xx = x + k_ * (hw + 10)
    add(group(f"2 {key} tile", real_image(xx, y, hw, hw, "assets/code_dapi.png", PX, CR["w"], 20, f"2 {key}")
              + vector_outlines_sub(xx, y, hw, hw, "assets/code_manual.json", "manual nuclei (vector)", REF, 1.4, DASH, (0, 0, CR["w"], CR["w"]))
              + vector_outlines_sub(xx, y, hw, hw, f"assets/code_{key}.json", f"{key} code (vector)", MODEL, 1.4, None, (0, 0, CR["w"], CR["w"]))
              + halo(xx + 6, y + 16, ["vague", "Box 1"][k_])))
add(key_item(x, y + hw + 18, MODEL, "LLM-written code") + key_item(x + 170, y + hw + 18, REF, "manual nuclei", DASH))
yy0 = y + hw + 42
rows_ = [("runs without error", "yes", "yes"), ("nuclei F1", f"{RES['vague']['f1']:.2f}", f"{RES['box1']['f1']:.2f}"),
         ("area vs manual", f"×{RES['vague']['area_ratio_median']:.2f}", f"×{RES['box1']['area_ratio_median']:.2f}"),
         ("units", "pixels", "µm²")]
for i, (lbl, a_, b_) in enumerate(rows_):
    yy = yy0 + i * 19
    add(t(x, yy, lbl, 13, fill=BODY) + t(x + hw / 2 + 60, yy, a_, 13, "bold", NOC if i else INK, "middle")
        + t(x + hw + 10 + hw / 2, yy, b_, 13, "bold", NOC if i in (1, 2) else INK, "middle"))

# ================================================================ 3 agent
x = colx[2] + IP
HO = json.load(open("heldout/heldout_scores.json"))
s, h = prompt(x, ry[0] + 8, IW, ["Optimise nuclei segmentation on", "dapi_dev.tif (development half only);", "log each change and its F1."], 13.5); add(s)
s, h = reply(x, ry[1] + 6, IW, ["it 1 baseline              F1 0.78", "it 2 drop objects with mean", "     intensity > 550 or", "     area > 1000 px        F1 0.89", "it 3 min area 80 -> 120    F1 0.91", "it 4 block size 101 -> 51  F1 0.92"],
             title="Claude Sonnet agent, log (condensed)", size=12); add(s)
cav(2, ["An agent rewarded for a score may exclude", "difficult objects or loosen a filter. Hold data", "out; review every change and exclusion."])
y = ry[3] + 10
EX = json.load(open("assets/agent_excl.json"))
TH2 = IW * EX["h"] / EX["w"]
k_ = IW / EX["w"]
gg = [real_image(x, y, IW, TH2, "assets/agent_excl.png", PX, EX["w"], 20, "3 excluded nuclei"),
      vector_outlines_sub(x, y, IW, TH2, "assets/agent_excl_kept.json", "kept by the agent's workflow (vector)", MODEL, 1.3, None, (0, 0, EX["w"], EX["h"]))]
for ex_, ey_, inten, area in EX["excluded"]:
    gg.append(f'<circle cx="{x+ex_*k_:.1f}" cy="{y+ey_*k_:.1f}" r="{16*k_/1.4:.1f}" fill="none" stroke="#ffd23f" stroke-width="2.6" stroke-dasharray="5 3"/>')
gg.append(rrect(x + 4, y + 4, 300, 40, 4, "#0b111d", "none", 0, ' fill-opacity="0.8"')
          + f'<line x1="{x+10}" y1="{y+16}" x2="{x+28}" y2="{y+16}" stroke="{MODEL}" stroke-width="2.5"/>' + t(x + 34, y + 20, "kept by the agent's workflow", 12, "bold", "#ffffff")
          + f'<circle cx="{x+19}" cy="{y+33}" r="6" fill="none" stroke="#ffd23f" stroke-width="2.2" stroke-dasharray="4 2"/>' + t(x + 34, y + 37, "removed by its filter, yet annotated", 12, "bold", "#ffffff"))
add(group("3 excluded nuclei", "".join(gg)))
y += TH2 + 22
add(note(x, y, ["The iteration-2 filter raised F1 but also removed", "annotated endothelial nuclei (8 in the development", f"half). Held-out F1: {HO[-1]['heldout']:.2f} (development {HO[-1]['dev']:.2f})."]))

# ================================================================ 4 direct answer
x = colx[3] + IP
CC = json.load(open("data/count_crops.json"))
CRES = json.load(open("data/count_results.json"))
ex = [r for r in CRES["rows"] if r["type"] == "cells_pecam" and r["crop"] == 6][0]
add(real_image(x, ry[0] + 8, 88, 88, "counts/cells_pecam_6.png", PX * CC["cells_pecam"][5]["size_px"] / 512, 512, 0, "4 prompt image"))
s, h = prompt(x + 96, ry[0] + 16, IW - 96, ["How many cells are", "in this image?"], 13.5); add(s)
s, h = reply(x, ry[1] + 6, IW, [f"Claude Haiku:   {ex['haiku'][0]}, {ex['haiku'][1]}, {ex['haiku'][2]}",
                                 f"Claude Sonnet:  {ex['sonnet'][0]}, {ex['sonnet'][1]}, {ex['sonnet'][2]}",
                                 f"Claude Opus:    {ex['opus'][0]}, {ex['opus'][1]}, {ex['opus'][2]}"],
             title="Answers to the same question, asked 3 times", size=13); add(s)
add(t(x, ry[1] + h + 26, f"Manual count: {ex['lo']}–{ex['hi']} cells", 14, "bold", INK))
cav(3, ["The analysis is hidden, outputs are not", "deterministic and models change. Not for", "quantification without validation."])
y = ry[3] + 10
OKT, MIDT, BADT = "#1a7a4c", "#c27c0e", NOC
LBW = 22
cw_ = (IW - LBW) / 6
TH_ = cw_ - 6


def colour(v, lo, hi):
    if lo <= v <= hi:
        return OKT
    err = (lo - v) / lo if v < lo else (v - hi) / hi
    return MIDT if err <= 0.25 else BADT


for key, ttl in (("cells_pecam", "cells"), ("nuclei_dapi", "nuclei"), ("cancer_bf", "cancer cells")):
    rows = [r for r in CRES["rows"] if r["type"] == key]
    for c in range(6):
        cx = x + LBW + c * cw_
        crop = CC[key][c]
        add(real_image(cx + 3, y, TH_, TH_, crop["file"], PX * crop["size_px"] / 512, 512, 0, f"4 {key} {c+1}"))
        r = rows[c]
        add(t(cx + cw_ / 2, y + TH_ + 13, f"{r['lo']}–{r['hi']}" if r["lo"] != r["hi"] else str(r["lo"]), 11.5, "bold", INK, "middle"))
        for mi, m in enumerate(("haiku", "sonnet", "opus")):
            for v, dx in zip(r[m], (-17, 0, 17)):
                add(t(cx + cw_ / 2 + dx, y + TH_ + 27 + mi * 13, str(v), 10.5, "bold", colour(v, r["lo"], r["hi"]), "middle"))
    add(f'<text x="{x+8}" y="{y+TH_/2}" font-size="11.5" font-weight="bold" fill="{INK}" text-anchor="middle" transform="rotate(-90 {x+8} {y+TH_/2})">{ttl}</text>')
    for mi, m in enumerate(("H", "S", "O")):
        add(t(x + 8, y + TH_ + 27 + mi * 13, m, 10.5, "bold", MCOL[["haiku", "sonnet", "opus"][mi]], "middle"))
    y += TH_ + 27 + 2 * 13 + 10
add(t(x, y + 6, "manual", 11.5, "bold", INK) + t(x + 52, y + 6, "within", 11.5, "bold", OKT) + t(x + 98, y + 6, "≤ 25% off", 11.5, "bold", MIDT)
    + t(x + 164, y + 6, "> 25% off", 11.5, "bold", BADT) + t(x + 232, y + 6, "H/S/O: Haiku/Sonnet/Opus", 11.5, fill=BODY))

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
open("fig3_v2.svg", "w", encoding="utf-8").write(svg)
print("written", len(svg) // 1024, "KB; height", H)
