# ======================================================================= FIGURE 3 BODY: four ways to use an LLM, real runs
LL = C["C"]                                   # LLM purple, as in Fig. 1b
ACC = LL["accent"]
MONO = ' font-family="DejaVu Sans Mono, Menlo, Consolas, monospace"'
OKF, OKS = "#eef8f1", "#b9e0c5"
NOF, NOS, NOC = "#fdf0ef", "#efc2be", "#c8423b"
MCOL = {"haiku": "#56b4e9", "sonnet": "#e69f00", "opus": "#cc79a7"}   # Okabe-Ito, one colour per model
YO = 20


def petal(cx, cy, s=0.55, col=ACC):
    return "".join(f'<rect x="{cx-6.5*s:.1f}" y="{cy-17*s:.1f}" width="{13*s:.1f}" height="{28*s:.1f}" rx="{6.5*s:.1f}" fill="none" '
                   f'stroke="{col}" stroke-width="2" transform="rotate({q*60} {cx} {cy})"/>' for q in range(6))


def person(cx, cy, col=INK):
    return (f'<circle cx="{cx}" cy="{cy-7}" r="6.5" fill="none" stroke="{col}" stroke-width="2"/>'
            f'<path d="M{cx-11},{cy+12} a11,11 0 0 1 22,0" fill="none" stroke="{col}" stroke-width="2"/>')


def bubble(x, y, w, h, fill, stroke, side):
    tx = x + w - 30 if side == "r" else x + 30
    d = (f'M{x+10},{y} h{w-20} a10,10 0 0 1 10,10 v{h-20} a10,10 0 0 1 -10,10 '
         + (f'H{tx+10} l2,11 l-13,-11 ' if side == "r" else f'H{tx+10} l-13,11 l2,-11 ')
         + f'H{x+10} a10,10 0 0 1 -10,-10 v-{h-20} a10,10 0 0 1 10,-10 z')
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="1.4"/>'


def prompt(x, y, w, lines, size=14):
    h = 18 + 18 * len(lines)
    return (bubble(x + 30, y, w - 30, h, "#ffffff", "#b8c2d0", "l") + f'<g>{person(x + 12, y + h / 2)}</g>'
            + t(x + 46, y + 22, lines, size, fill=INK, lh=18)), h + 12


def reply(x, y, w, lines, size=13, mono=True, title=None):
    h = 16 + 17 * len(lines) + (18 if title else 0)
    g = [bubble(x, y, w - 30, h, LL["tint"], LL["tintstroke"], "r"), f'<g>{petal(x + w - 12, y + h / 2)}</g>']
    yy = y + 20
    if title:
        g.append(t(x + 12, yy, title, 12.5, "bold", "#6b2c87")); yy += 18
    g.append(t(x + 12, yy, lines, size, fill=INK, lh=17, extra=MONO if mono else ""))
    return "".join(g), h + 12


def terminal(x, y, w, lines, size=12.5):
    h = 30 + 17 * len(lines)
    g = [rrect(x, y, w, h, 8, "#1b2230", "none"),
         "".join(f'<circle cx="{x+14+i*13}" cy="{y+12}" r="4" fill="{c}"/>' for i, c in enumerate(["#ff5f57", "#febc2e", "#28c840"]))]
    yy = y + 32
    for ln, col in lines:
        g.append(t(x + 10, yy, ln, size, fill=col, extra=MONO)); yy += 17
    return "".join(g), h + 12


def check_box(x, y, w, lines):
    h = 22 + 18 * len(lines)
    return (rrect(x, y, w, h, 10, OKF, OKS, 1.4)
            + check_badge(x + 20, y + h / 2, "#1f8a70", 10).replace('stroke-width="4.5"', 'stroke-width="2.6"')
            .replace(f"M{x+10},{y+h/2+1} L{x+17},{y+h/2+8} L{x+31},{y+h/2-8}", f"M{x+15},{y+h/2} L{x+19},{y+h/2+4} L{x+26},{y+h/2-4}")
            + t(x + 38, y + 20, lines, 13.5, fill=INK, lh=18))


def note(x, y, lines, col=NOC):
    return t(x, y, lines, 13.5, "bold", col, lh=18)


# ---------------------------------------------------------------- delegation gradient across the four columns
gid = "llmgrad"
defs.append(f'<linearGradient id="{gid}" x1="0" x2="1"><stop offset="0" stop-color="#c7b3e0"/><stop offset="1" stop-color="{ACC}"/></linearGradient>')
add(group("delegation gradient", f'<path d="M28,{YO} H1796 L1812,{YO+15} L1796,{YO+30} H28 Z" fill="url(#{gid})"/>'
          + t(44, YO + 21, "more of the analysis delegated to the LLM  →  more decisions hidden", 15, "bold", "#ffffff")))
CY = YO + 42
CW = (1784 - 3 * 10) / 4
CH = 850
cols = [28 + i * (CW + 10) for i in range(4)]


def col_frame(i, title, sub):
    x = cols[i]
    return (rrect(x, CY, CW, CH, 16, NN["bg"], NN["stroke"], 1.4)
            + f'<circle cx="{x+36}" cy="{CY+36}" r="20" fill="{ACC}"/>' + t(x + 36, CY + 44, "abcd"[i], 22, "bold", "#fff", "middle")
            + t(x + 66, CY + 34, title, 20, "bold", INK) + t(x + 66, CY + 55, sub, 13.5, fill=BODY))


IN = 16                                       # inner padding
# ================================================================ a: ask for advice
x = cols[0]; w = CW - 2 * IN; xi = x + IN
g = [col_frame(0, "Ask for advice", "software, parameters, approaches")]
y = CY + 82
s, h = prompt(xi, y, w, ["How should I segment nuclei in 2D", "DAPI images with Cellpose in Python?"]); g.append(s); y += h
s, h = reply(xi, y, w, ['model = models.Cellpose(', '    model_type="nuclei")', 'masks, flows, styles, diams = \\', '    model.eval(img, channels=[0, 0])'],
             title="LLM reply, first code example (3/3 runs)"); g.append(s); y += h + 6
g.append(t(xi, y + 4, "Run as given with the installed Cellpose (4.2.1.1):", 13.5, "bold", INK)); y += 14
s, h = terminal(xi, y, w, [(">>> models.Cellpose(model_type='nuclei')", "#d5dbe5"),
                           ("AttributeError: module 'cellpose.models'", "#ff8a80"), ("  has no attribute 'Cellpose'", "#ff8a80")]); g.append(s); y += h
g.append(t(xi, y + 6, "Variant suggested in the same reply:", 13.5, "bold", INK)); y += 16
s, h = terminal(xi, y, w, [(">>> models.CellposeModel(model_type='nuclei')", "#d5dbe5"),
                           ("WARNING model_type argument is not used", "#ffd166"), ("  in v4.0.1+. Ignoring this argument...", "#ffd166"),
                           ("loading model cpsam_v2", "#9be7a1")]); g.append(s); y += h
g.append(note(xi, y + 10, ["The advised 'nuclei' model no longer exists:", "the code fails, or silently runs a different", "model; only a log line says so."]))
y += 76
g.append(t(xi, y, ["The reply also gave current-version code and", "said to check the installed version: the advice", "is plausible, mixed and easy to copy wrongly."], 13, fill=BODY, lh=17))
g.append(check_box(xi, CY + CH - 16 - 58, w, ["Verify against the documentation of", "the version you have installed."]))
add(group("a advice", "".join(g)))

# ================================================================ b: ask for code
x = cols[1]; w = CW - 2 * IN; xi = x + IN
g = [col_frame(1, "Ask for code", "e.g. Python, Fiji macro")]
y = CY + 82
RES = {k: json.load(open(f"codetest/{k}/result.json")) for k in ("vague", "box1")}
CR = json.load(open("assets/code_roi.json"))
hw = (w - 12) / 2
for k_, (key, ttl, lines) in enumerate([("vague", "Vague prompt", ["“Write a Python script that", "measures nuclear area in", "nuclei.tif.”"]),
                                        ("box1", "Box 1 prompt", ["“…pixel size 0.65 µm; do not", "silently resize or normalise;", "expose parameters; include", "a test; list assumptions.”"])]):
    xx = xi + k_ * (hw + 12)
    g.append(t(xx, y + 4, ttl, 15, "bold", INK))
    g.append(rrect(xx, y + 14, hw, 92, 8, "#ffffff", "#b8c2d0", 1.2) + t(xx + 10, y + 34, lines, 12.5, fill=INK, lh=17))
y += 122
TS = hw
for k_, key in enumerate(["vague", "box1"]):
    xx = xi + k_ * (hw + 12)
    g.append(group(f"b {key} tile", real_image(xx, y, TS, TS, "assets/code_dapi.png", PX, CR["w"], 20, f"b {key}")
                   + vector_outlines_sub(xx, y, TS, TS, "assets/code_manual.json", "manual nuclei (vector)", REF, 1.4, DASH, (0, 0, CR["w"], CR["w"]))
                   + vector_outlines_sub(xx, y, TS, TS, f"assets/code_{key}.json", f"{key} code (vector)", MODEL, 1.4, None, (0, 0, CR["w"], CR["w"]))))
g.append(key_item(xi, y + TS + 20, MODEL, "LLM-written code") + key_item(xi + 168, y + TS + 20, REF, "manual nuclei", DASH))
y += TS + 40
rows_ = [("runs without error", "yes", "yes"), ("nuclei F1 (IoU ≥ 0.5)", f"{RES['vague']['f1']:.2f}", f"{RES['box1']['f1']:.2f}"),
         ("area vs manual (median)", f"×{RES['vague']['area_ratio_median']:.2f}", f"×{RES['box1']['area_ratio_median']:.2f}"),
         ("extra objects", f"{RES['vague']['n_objects']-RES['vague']['matched']}", f"{RES['box1']['n_objects']-RES['box1']['matched']}"),
         ("units saved", "pixels", "µm²"), ("built-in test", "none", "passes")]
g.append(t(xi + 230, y + 4, "vague", 13.5, "bold", INK, "middle") + t(xi + 330, y + 4, "Box 1", 13.5, "bold", INK, "middle"))
for i, (lbl, a_, b_) in enumerate(rows_):
    yy = y + 28 + i * 24
    g.append(t(xi, yy, lbl, 13.5, fill=BODY) + t(xi + 230, yy, a_, 13.5, "bold", NOC if i else INK, "middle")
             + t(xi + 330, yy, b_, 13.5, "bold", NOC if i in (1, 2, 3) else INK, "middle"))
y += 28 + len(rows_) * 24
g.append(note(xi, y + 6, ["Both run without error. The vague code finds", "1 nucleus in 3 and shrinks them by a third;", "the specified code is better but still adds", f"{RES['box1']['n_objects']-RES['box1']['matched']} extra objects. Neither is validated."]))
g.append(check_box(xi, CY + CH - 16 - 58, w, ["Specify the measurement and units; test", "on images with a known result."]))
add(group("b code", "".join(g)))

# ================================================================ c: agent runs and optimises
x = cols[2]; w = CW - 2 * IN; xi = x + IN
g = [col_frame(2, "Let an agent run it", "runs and optimises the workflow")]
y = CY + 82
s, h = prompt(xi, y, w, ["Optimise nuclei segmentation on the", "development half; log each change."]); g.append(s); y += h
HO = json.load(open("heldout/heldout_scores.json"))
FS_ = 118
g.append(group("c field split", real_image(xi, y, FS_, FS_, "assets/agent_field.png", PX, 1024, 0, "c DAPI field")
               + f'<rect x="{xi}" y="{y}" width="{FS_}" height="{FS_/2}" fill="none" stroke="{ACC}" stroke-width="2.5"/>'
               + f'<rect x="{xi}" y="{y+FS_/2}" width="{FS_}" height="{FS_/2}" fill="#0b111d" fill-opacity="0.55" stroke="#8a94a3" stroke-width="2.5" stroke-dasharray="6 4"/>'
               + halo(xi + 5, y + 15, "development", size=11.5) + halo(xi + 5, y + FS_ / 2 + 15, "held out", size=11.5)))
px0, py0, pw_, ph_ = xi + FS_ + 50, y + 4, w - FS_ - 86, FS_ - 22
lo_, hi_ = 0.75, 0.95
Yv = lambda v: py0 + ph_ - ph_ * (v - lo_) / (hi_ - lo_)
Xv = lambda i: px0 + pw_ * (i - 1) / 4
g.append(f'<line x1="{px0}" y1="{py0+ph_}" x2="{px0+pw_}" y2="{py0+ph_}" stroke="{INK}" stroke-width="1.2"/>'
         f'<line x1="{px0}" y1="{py0}" x2="{px0}" y2="{py0+ph_}" stroke="{INK}" stroke-width="1.2"/>')
for v in (0.75, 0.95):
    g.append(t(px0 - 5, Yv(v) + 4, f"{v:.2f}", 11, fill=BODY, anchor="end"))
g.append(t(px0 + pw_ / 2, py0 + ph_ + 15, "iteration 1–5", 11.5, fill=BODY, anchor="middle")
         + f'<text x="{px0-30}" y="{py0+ph_/2}" font-size="11.5" fill="{BODY}" text-anchor="middle" transform="rotate(-90 {px0-30} {py0+ph_/2})">F1</text>')
for key, colr, dash in [("dev", ACC, None), ("heldout", "#4a5568", "6 4")]:
    pts = " ".join(f"{Xv(r['version']):.1f},{Yv(r[key]):.1f}" for r in HO)
    g.append(f'<polyline points="{pts}" fill="none" stroke="{colr}" stroke-width="2.4"' + (f' stroke-dasharray="{dash}"' if dash else "") + "/>"
             + "".join(f'<circle cx="{Xv(r["version"]):.1f}" cy="{Yv(r[key]):.1f}" r="3.2" fill="{colr}"/>' for r in HO)
             + t(Xv(5) + 6, Yv(HO[-1][key]) + (0 if key == "dev" else 12), f"{HO[-1][key]:.2f}", 12, "bold", colr))
y += FS_ + 14
s, h = reply(xi, y, w, ["it 2: drop objects with mean intensity", "  > 550 or area > 1000 px  →  F1 0.78 → 0.89"],
             title="agent log, iteration 2 (excerpt)", size=12.5); g.append(s); y += h + 2
EX = json.load(open("assets/agent_excl.json"))
TW_ = w
TH2 = TW_ * EX["h"] / EX["w"]
k_ = TW_ / EX["w"]
gg = [real_image(xi, y, TW_, TH2, "assets/agent_excl.png", PX, EX["w"], 20, "c excluded nuclei"),
      vector_outlines_sub(xi, y, TW_, TH2, "assets/agent_excl_kept.json", "kept by the agent's workflow (vector)", MODEL, 1.3, None, (0, 0, EX["w"], EX["h"]))]
for ex_, ey_, inten, area in EX["excluded"]:
    gg.append(f'<circle cx="{xi+ex_*k_:.1f}" cy="{y+ey_*k_:.1f}" r="{16*k_/1.4:.1f}" fill="none" stroke="#ffd23f" stroke-width="2.6" stroke-dasharray="5 3"/>')
gg.append(rrect(xi + 4, y + 4, 330, 40, 4, "#0b111d", "none", 0, ' fill-opacity="0.8"')
          + f'<line x1="{xi+10}" y1="{y+16}" x2="{xi+28}" y2="{y+16}" stroke="{MODEL}" stroke-width="2.5"/>' + t(xi + 34, y + 20, "kept by the agent's workflow", 12, "bold", "#ffffff")
          + f'<circle cx="{xi+19}" cy="{y+33}" r="6" fill="none" stroke="#ffd23f" stroke-width="2.2" stroke-dasharray="4 2"/>' + t(xi + 34, y + 37, "removed by its filter, yet annotated", 12, "bold", "#ffffff"))
g.append(group("c excluded nuclei", "".join(gg)))
y += TH2 + 10
g.append(note(xi, y + 8, ["To raise the score, the agent added a filter that", "also removed bright or large endothelial nuclei:", "a biological exclusion hidden in one line of code."]))
y += 64
g.append(t(xi, y, ["Given an editable evaluation list in a second run,", "it did not drop tiles; we checked, not assumed."], 13, fill=BODY, lh=17))
g.append(check_box(xi, CY + CH - 16 - 58, w, ["Hold data out; review every code", "change and every excluded object."]))
add(group("c agent", "".join(g)))

# ================================================================ d: ask for the answer -- answer table per crop
x = cols[3]; w = CW - 2 * IN; xi = x + IN
g = [col_frame(3, "Ask for the answer", "multimodal model, direct answer")]
y = CY + 82
CC = json.load(open("data/count_crops.json"))
CRES = json.load(open("data/count_results.json"))
s, h = prompt(xi, y, w, ["How many cells / nuclei / cancer cells", "are in this image?  (3 times, 3 models)"]); g.append(s); y += h
OKT, MIDT, BADT = "#1a7a4c", "#c27c0e", NOC
LBW = 30
cw_ = (w - LBW) / 6
TH_ = cw_ - 6


def colour(v, lo, hi):
    if lo <= v <= hi:
        return OKT
    err = (lo - v) / lo if v < lo else (v - hi) / hi
    return MIDT if err <= 0.25 else BADT


titles = {"cells_pecam": "Endothelial cells (PECAM-1)", "nuclei_dapi": "Nuclei (DAPI)", "cancer_bf": "Cancer cells (brightfield)"}
for key in ("cells_pecam", "nuclei_dapi", "cancer_bf"):
    g.append(t(xi, y + 12, titles[key], 14, "bold", INK)); y += 20
    rows = [r for r in CRES["rows"] if r["type"] == key]
    for c in range(6):
        cx = xi + LBW + c * cw_
        crop = CC[key][c]
        g.append(real_image(cx + 3, y, TH_, TH_, crop["file"], PX * crop["size_px"] / 512, 512, 0, f"d {key} {c+1}"))
        r = rows[c]
        g.append(t(cx + cw_ / 2, y + TH_ + 14, f"{r['lo']}–{r['hi']}" if r["lo"] != r["hi"] else str(r["lo"]), 12, "bold", INK, "middle"))
        for mi, m in enumerate(("haiku", "sonnet", "opus")):
            yy = y + TH_ + 31 + mi * 15
            vals = r[m]
            xs = [cx + cw_ / 2 - 18, cx + cw_ / 2, cx + cw_ / 2 + 18]
            for v, xx_ in zip(vals, xs):
                g.append(t(xx_, yy, str(v), 11.5, "bold", colour(v, r["lo"], r["hi"]), "middle"))
    g.append(t(xi, y + TH_ + 14, "manual", 10.5, fill=BODY))
    for mi, m in enumerate(("Haiku", "Sonnet", "Opus")):
        g.append(t(xi, y + TH_ + 31 + mi * 15, m[:2] if False else m[0], 12, "bold", MCOL[m.lower()]))
    y += TH_ + 31 + 2 * 15 + 18
# colour key + summary
g.append(t(xi, y, "answer:", 12, fill=BODY) + t(xi + 50, y, "within manual range", 12, "bold", OKT)
         + t(xi + 178, y, "≤ 25% off", 12, "bold", MIDT) + t(xi + 252, y, "> 25% off", 12, "bold", BADT))
y += 18
g.append(t(xi, y, "H, S, O: Claude Haiku, Sonnet, Opus; 3 runs each", 12, fill=BODY))
S_ = CRES["summary"]
g.append(note(xi, y + 24, ["Answers change between runs and models, and", "consistent answers can be consistently wrong",
                            f"(within range: H {S_['haiku']['within_truth_range_pct']}%, S {S_['sonnet']['within_truth_range_pct']}%, O {S_['opus']['within_truth_range_pct']}%)."]))
g.append(check_box(xi, CY + CH - 16 - 58, w, ["Not for quantification without", "validation on images with known answers."]))
add(group("d direct answer", "".join(g)))

# ================================================================ e: keep the analysis, not the conversation
EY = CY + CH + 10
EH = 120
e = [rrect(28, EY, 1784, EH, 16, NN["bg"], NN["stroke"], 1.4),
     f'<circle cx="64" cy="{EY+36}" r="20" fill="{ACC}"/>' + t(64, EY + 44, "e", 22, "bold", "#fff", "middle"),
     t(94, EY + 43, "Keep the analysis, not the conversation", 20, "bold", INK)]
items = [("1–3", "save the code, configuration, parameters, software versions and environment; the analysis should rerun without the LLM"),
         ("4", "if the LLM stays in the analysis, also keep the prompts and model version; validate against reference data"),
         ("all", "record the LLM, version, date and role; check where images are sent (provider terms, institutional or local models)")]
for i, (tag, txt) in enumerate(items):
    yy = EY + 72 + i * 0
for i, (tag, txt) in enumerate(items):
    xx = 44 + i * 590
    e.append(rrect(xx, EY + 60, 572, 50, 8, "#ffffff", NN["stroke"], 1.2) + rrect(xx + 8, EY + 72, 42, 26, 6, ACC, "none")
             + t(xx + 29, EY + 90, tag, 13, "bold", "#fff", "middle"))
    words, lines_, cur = txt.split(), [], ""
    for w_ in words:
        if len(cur) + len(w_) > 70:
            lines_.append(cur); cur = w_
        else:
            cur = (cur + " " + w_).strip()
    lines_.append(cur)
    e.append(t(xx + 60, EY + 80, lines_, 13, fill=INK, lh=17))
add(group("e reporting", "".join(e)))

H = EY + EH + 20
svg = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
       f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" xmlns:xlink="http://www.w3.org/1999/xlink" '
       f'width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">\n'
       f'<defs>{"".join(defs)}</defs>\n<rect width="{W}" height="{H}" fill="#ffffff"/>\n'
       + "\n".join(out) + "\n</svg>\n")
open("fig3.svg", "w", encoding="utf-8").write(svg)
print("written", len(svg) // 1024, "KB; height", H)
