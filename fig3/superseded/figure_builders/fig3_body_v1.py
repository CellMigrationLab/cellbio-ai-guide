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
          + t(44, YO + 21, "more of the analysis delegated to the LLM  →  more decisions hidden, less reproducible", 15, "bold", "#ffffff")))
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
             title="LLM reply (excerpt; 3/3 runs: 'nuclei' model)"); g.append(s); y += h + 6
g.append(t(xi, y + 4, "Run as given with the installed Cellpose 4.2.1.1:", 13.5, "bold", INK)); y += 14
s, h = terminal(xi, y, w, [(">>> models.Cellpose(model_type='nuclei')", "#d5dbe5"),
                           ("AttributeError: module 'cellpose.models'", "#ff8a80"), ("  has no attribute 'Cellpose'", "#ff8a80"),
                           ("", "#d5dbe5"),
                           (">>> models.CellposeModel(model_type='nuclei')", "#d5dbe5"),
                           ("WARNING model_type argument is not used", "#ffd166"), ("  in v4.0.1+. Ignoring this argument...", "#ffd166"),
                           ("loading model cpsam_v2", "#9be7a1")]); g.append(s); y += h
g.append(note(xi, y + 8, ["The advised model no longer exists: the code fails,", "or runs a different model with a warning."])); y += 54
s, h = prompt(xi, y, w, ["Does this show that my treatment", "increases cell size? (no true difference)"]); g.append(s); y += h
s, h = reply(xi, y, w, ["“No. The means differ by about 3%", "and the medians are the same…”"], mono=False, size=13.5,
             title="LLM reply (6/6 runs, leading or neutral question)"); g.append(s); y += h
g.append(t(xi, y + 6, ["This model did not simply agree here; a leading", "question still invites confirmation."], 13, fill=BODY, lh=17))
g.append(check_box(xi, CY + CH - 16 - 76, w, ["Verify recommendations against the", "documentation of your installed version;", "ask what the data show, not for confirmation."]))
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
         ("units saved", "pixels", "µm²"), ("built-in test", "none", "passes"), ("assumptions listed", "none", "10")]
g.append(t(xi + 230, y + 4, "vague", 13.5, "bold", INK, "middle") + t(xi + 330, y + 4, "Box 1", 13.5, "bold", INK, "middle"))
for i, (lbl, a_, b_) in enumerate(rows_):
    yy = y + 28 + i * 24
    g.append(t(xi, yy, lbl, 13.5, fill=BODY) + t(xi + 230, yy, a_, 13.5, "bold", NOC if i in (1, 2, 3, 4, 5) else INK, "middle")
             + t(xi + 330, yy, b_, 13.5, "bold", "#1a6b57" if i in (1, 3, 4, 5) else INK, "middle"))
y += 28 + 6 * 24
g.append(note(xi, y + 6, ["Both codes run; the vague one measures less", "of each nucleus and reports pixels."]))
g.append(check_box(xi, CY + CH - 16 - 76, w, ["Specify the measurement, axes and units;", "test the code on images with known", "outputs and inspect intermediate outputs."]))
add(group("b code", "".join(g)))

# ================================================================ c: agent runs and optimises
x = cols[2]; w = CW - 2 * IN; xi = x + IN
g = [col_frame(2, "Let an agent run it", "runs and optimises the workflow")]
y = CY + 82
s, h = prompt(xi, y, w, ["Optimise nuclei segmentation on", "dapi_dev.tif; log each change.", "(scored against manual nuclei)"]); g.append(s); y += h
FS_ = 190
fx = xi + (w - FS_) / 2
g.append(group("c field split", real_image(fx, y, FS_, FS_, "assets/agent_field.png", PX, 1024, 100, "c DAPI field")
               + f'<rect x="{fx}" y="{y}" width="{FS_}" height="{FS_/2}" fill="none" stroke="{ACC}" stroke-width="2.5"/>'
               + f'<rect x="{fx}" y="{y+FS_/2}" width="{FS_}" height="{FS_/2}" fill="#0b111d" fill-opacity="0.55" stroke="#8a94a3" stroke-width="2.5" stroke-dasharray="6 4"/>'
               + halo(fx + 6, y + 16, "development: agent sees") + halo(fx + 6, y + FS_ / 2 + 16, "held out: never seen")))
y += FS_ + 18
HO = json.load(open("heldout/heldout_scores.json"))
LOG = [json.loads(l) for l in open("agent_sandbox/log.jsonl")]
px0, py0, pw_, ph_ = xi + 40, y + 14, w - 60, 170
lo_, hi_ = 0.75, 0.95
Yv = lambda v: py0 + ph_ - ph_ * (v - lo_) / (hi_ - lo_)
Xv = lambda i: px0 + pw_ * (i - 1) / 4
g.append(f'<line x1="{px0}" y1="{py0+ph_}" x2="{px0+pw_}" y2="{py0+ph_}" stroke="{INK}" stroke-width="1.3"/>'
         f'<line x1="{px0}" y1="{py0}" x2="{px0}" y2="{py0+ph_}" stroke="{INK}" stroke-width="1.3"/>')
for v in (0.75, 0.85, 0.95):
    g.append(t(px0 - 6, Yv(v) + 4, f"{v:.2f}", 11.5, fill=BODY, anchor="end"))
for i in range(1, 6):
    g.append(t(Xv(i), py0 + ph_ + 16, str(i), 11.5, fill=BODY, anchor="middle"))
g.append(t(px0 + pw_ / 2, py0 + ph_ + 33, "iteration (frozen after 5)", 12.5, fill=BODY, anchor="middle")
         + f'<text x="{px0-32}" y="{py0+ph_/2}" font-size="12.5" fill="{BODY}" text-anchor="middle" transform="rotate(-90 {px0-32} {py0+ph_/2})">F1</text>')
for key, colr, dash, lbl in [("dev", ACC, None, "development"), ("heldout", "#4a5568", "6 4", "held out")]:
    pts = " ".join(f"{Xv(r['version']):.1f},{Yv(r[key]):.1f}" for r in HO)
    g.append(f'<polyline points="{pts}" fill="none" stroke="{colr}" stroke-width="2.6"' + (f' stroke-dasharray="{dash}"' if dash else "") + "/>"
             + "".join(f'<circle cx="{Xv(r["version"]):.1f}" cy="{Yv(r[key]):.1f}" r="4" fill="{colr}"/>' for r in HO))
    last = HO[-1][key]
    g.append(t(Xv(5) + 8, Yv(last) + (-4 if key == "dev" else 14), f"{last:.2f}", 13, "bold", colr))
g.append(key_item(px0, py0 - 8, ACC, "development") + key_item(px0 + 130, py0 - 8, "#4a5568", "held out", "6 4"))
y = py0 + ph_ + 44
s, h = reply(xi, y, w, ["it 2: drop objects with mean intensity", "  > 550 or area > 1000 px", "it 3-5: tune minimum area, block size"],
             title="agent log (excerpt)", size=12.5); g.append(s); y += h
g.append(note(xi, y + 4, ["Development F1 keeps rising after iteration 2;", "the held-out score does not."]))
g.append(check_box(xi, CY + CH - 16 - 76, w, ["Decide what it may change; hold data out,", "freeze, then test; work on a copy and", "review every code change and exclusion."]))
add(group("c agent", "".join(g)))

# ================================================================ d: ask for the answer
x = cols[3]; w = CW - 2 * IN; xi = x + IN
g = [col_frame(3, "Ask for the answer", "multimodal model, direct answer")]
y = CY + 82
CC = json.load(open("data/count_crops.json"))
CRES = json.load(open("data/count_results.json"))
ex = CC["cells_pecam"][5]
exr = [r for r in CRES["rows"] if r["type"] == "cells_pecam" and r["crop"] == 6][0]
s, h = prompt(xi, y, w, ["How many cells are in this image?", "(PECAM-1; asked 3 times per model)"]); g.append(s); y += h
ES = 150
g.append(real_image(xi, y, ES, ES, "counts/cells_pecam_6.png", PX * ex["size_px"] / 512, 512, 50, "d example crop"))
ax = xi + ES + 14
g.append(t(ax, y + 16, f"manual: {exr['lo']}–{exr['hi']}", 14, "bold", INK))
for i, m in enumerate(["haiku", "sonnet", "opus"]):
    g.append(f'<circle cx="{ax+6}" cy="{y+44+i*30}" r="6" fill="{MCOL[m]}"/>' + t(ax + 18, y + 49 + i * 30, f"{m.capitalize()}: " + " · ".join(map(str, exr[m])), 14, fill=INK))
y += ES + 22
# answers vs manual count, all crops, log axes
px0, py0, sz = xi + 46, y + 10, w - 70
import math
lo_, hi_ = 1, 100
L_ = lambda v: (math.log10(max(v, 1)) - math.log10(lo_)) / (math.log10(hi_) - math.log10(lo_))
Xc = lambda v: px0 + sz * L_(v)
Yc = lambda v: py0 + sz - sz * L_(v)
g.append(f'<rect x="{px0}" y="{py0}" width="{sz}" height="{sz}" fill="#ffffff" stroke="{INK}" stroke-width="1.2"/>'
         f'<line x1="{px0}" y1="{py0+sz}" x2="{px0+sz}" y2="{py0}" stroke="#8a94a3" stroke-width="1.3" stroke-dasharray="5 4"/>')
for v in (1, 3, 10, 30, 100):
    g.append(t(Xc(v), py0 + sz + 15, str(v), 11.5, fill=BODY, anchor="middle") + t(px0 - 5, Yc(v) + 4, str(v), 11.5, fill=BODY, anchor="end"))
SH = {"cells_pecam": "circle", "nuclei_dapi": "square", "cancer_bf": "triangle"}
rng = np.random.default_rng(3)
for r in CRES["rows"]:
    mid = (r["lo"] + r["hi"]) / 2
    g.append(f'<line x1="{Xc(mid):.1f}" y1="{Yc(r["lo"]):.1f}" x2="{Xc(mid):.1f}" y2="{Yc(r["hi"]):.1f}" stroke="#c8d3e0" stroke-width="5"/>')
for r in CRES["rows"]:
    mid = (r["lo"] + r["hi"]) / 2
    for mi, m in enumerate(["haiku", "sonnet", "opus"]):
        for v in r[m]:
            cx_, cy_ = Xc(mid) * 1 + (mi - 1) * 3.5 + rng.uniform(-1.2, 1.2), Yc(v)
            if SH[r["type"]] == "circle":
                g.append(f'<circle cx="{cx_:.1f}" cy="{cy_:.1f}" r="3.6" fill="{MCOL[m]}" fill-opacity="0.85"/>')
            elif SH[r["type"]] == "square":
                g.append(f'<rect x="{cx_-3.3:.1f}" y="{cy_-3.3:.1f}" width="6.6" height="6.6" fill="{MCOL[m]}" fill-opacity="0.85"/>')
            else:
                g.append(f'<path d="M{cx_:.1f},{cy_-4.2:.1f} l4,7.2 h-8 z" fill="{MCOL[m]}" fill-opacity="0.85"/>')
g.append(t(px0 + sz / 2, py0 + sz + 32, "manual count (bar: range)", 12.5, fill=BODY, anchor="middle")
         + f'<text x="{px0-32}" y="{py0+sz/2}" font-size="12.5" fill="{BODY}" text-anchor="middle" transform="rotate(-90 {px0-32} {py0+sz/2})">model answer</text>')
y = py0 + sz + 50
g.append(f'<circle cx="{xi+6}" cy="{y-4}" r="4" fill="{INK}"/>' + t(xi + 14, y, "PECAM-1 cells", 12.5, fill=BODY)
         + f'<rect x="{xi+112}" y="{y-8}" width="7" height="7" fill="{INK}"/>' + t(xi + 124, y, "DAPI nuclei", 12.5, fill=BODY)
         + f'<path d="M{xi+218},{y-9} l4,7.2 h-8 z" fill="{INK}"/>' + t(xi + 228, y, "cancer cells (BF)", 12.5, fill=BODY))
S_ = CRES["summary"]
g.append(t(xi, y + 24, "within the manual range: " + ", ".join(f"{m.capitalize()} {S_[m]['within_truth_range_pct']}%" for m in ["haiku", "sonnet", "opus"]), 13, "bold", NOC))
g.append(check_box(xi, CY + CH - 16 - 76, w, ["Not for quantification without validation;", "ask ≥ 3 times, on images with a known", "answer. Consistent is not the same as correct."]))
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
