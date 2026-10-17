YO = 20
GAPR = 10
SEGX, SEGY, SEGW, SEGH = 240, 40, 240, 260          # troubleshooting window (full-field px), as Fig. 1c step 3
cA, cB = C["A"], C["B"]
PS = json.load(open("panels/perturb_scores.json"))


def f1bar(x, y, w, v, lbl=None, colr=None):
    colr = colr or F1C
    return (f'<rect x="{x}" y="{y}" width="{w}" height="10" rx="3" fill="#e4e8ee"/>'
            f'<rect x="{x}" y="{y}" width="{w*v:.1f}" height="10" rx="3" fill="{colr}"/>'
            + t(x + w + 7, y + 10, f"{v:.2f}", 14, "bold", INK) + (t(x, y - 6, lbl, 13.5, fill=BODY) if lbl else ""))


def tile(x, y, w, h, png, layers, label, markers=None, um=PX, imgw=240, bar=50, sub=(0, 0, 240, 260)):
    g = [real_image(x, y, w, h, png, um, imgw, bar, label, "#111111")]
    for path, lbl, colr, dash in layers:
        g.append(vector_outlines_sub(x, y, w, h, path, lbl, colr, 1.6, dash, sub))
    k = w / sub[2]
    for kind, pts in (markers or {}).items():
        for px, py in pts:
            cx, cy = x + (px - sub[0]) * k, y + (py - sub[1]) * k
            if kind == "missed":
                g.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="17" fill="none" stroke="{ERRC}" stroke-width="2.6"/>')
            else:
                g.append(f'<path d="M{cx-9:.1f},{cy-9:.1f} L{cx+9:.1f},{cy+9:.1f} M{cx+9:.1f},{cy-9:.1f} L{cx-9:.1f},{cy+9:.1f}" '
                         f'stroke="{ERRC}" stroke-width="3" stroke-linecap="round"/>')
    return group(label, "".join(g))


ERRC = "#ff8c1a"

# ---------------------------------------------------------------- a: when a pre-trained model performs poorly (four checks)
FTW = 172                                 # step-4 box width
GW = (1784 - 28 - FTW - 3 * 26) / 3      # width of one check group
BW = 210                                  # bar column width
TW = GW - BW - 14
TH = TW * SEGH / SEGW
R1 = round(66 + 64 + TH + 26 + 14)
bb = [frame(28, YO, 1784, R1, "a", "When a pre-trained model performs poorly, find the mismatch first", "A")]
bb.append(key_item(1812 - 330, YO + 42, MODEL, "model") + key_item(1812 - 230, YO + 42, REF, "manual annotation", DASH))
ty0 = YO + 66 + 64
DEFC = "#9aa4b2"                          # default settings: grey baseline bar in every group


def minibars(x, y, w, items, hl):
    g = [t(x, y, "F1", 13.5, "bold", INK)]
    for i, (lbl, v, is_def) in enumerate(items):
        yy = y + 22 + i * 37
        g.append(t(x, yy, lbl, 13.5, "bold" if lbl == hl else "normal", INK if lbl == hl else BODY))
        if v is None:
            g.append(t(x, yy + 17, "running…", 13, "bold", "#7a8699"))
            continue
        g.append(f'<rect x="{x}" y="{yy+6}" width="{w-44}" height="9" rx="3" fill="#e4e8ee"/>'
                 f'<rect x="{x}" y="{yy+6}" width="{(w-44)*v:.1f}" height="9" rx="3" fill="{DEFC if is_def else F1C}"/>'
                 + t(x + w - 38, yy + 15, f"{v:.2f}", 13.5, "bold", INK))
    return "".join(g)


def step_tile(x, key, label):
    if PS.get(key) is None:
        return (rrect(x, ty0, TW, TH, 4, "#e9edf2", "#c8d3e0", 1.2, ' stroke-dasharray="6 4"')
                + t(x + TW / 2, ty0 + TH / 2, "running…", 15, "bold", "#7a8699", "middle"))
    return tile(x, ty0, TW, TH, "from_fig1_panel_c/B_rep_bf.png",
                [("from_fig1_panel_c/B_rep_ref.json", "reference (vector)", REF, DASH), (f"panels/ts_cp_{key}.json", f"{label} (vector)", MODEL, None)],
                f"tile {label}")


def header(x, n, ttl, sub):
    return (f'<circle cx="{x+11}" cy="{YO+88}" r="11" fill="{cA["accent"]}"/>' + t(x + 11, YO + 93, str(n), 13, "bold", "#fff", "middle")
            + t(x + 28, YO + 93, ttl, 16.5, "bold", INK) + t(x, YO + 114, sub, 13.5, fill=BODY))


D = PS["default"]
groups = [(1, "Check the normalisation", "tile: forgot to normalise", "nonorm", "forgot to normalise",
           [("forgot to normalise", PS["nonorm"], False), ("percentile (default)", D, True), ("min–max", PS.get("file_minmax"), False),
            ("histogram equalisation", PS.get("file_histeq"), False), ("CLAHE", PS.get("file_clahe"), False)]),
          (2, "Check the object scale", "tile: input downsampled 4×", "down4", "downsampled 4×",
           [("downsampled 4×", PS["down4"], False), ("downsampled 2×", PS["down2"], False), ("native (default)", D, True),
            ("upsampled 2×", PS.get("up2"), False)]),
          (3, "Check the post-processing", "tile: low-contrast objects removed", "postfilter", "low-contrast objects removed",
           [("none (default)", D, True), ("stricter probability threshold", PS["cellprob2"], False), ("looser flow threshold", PS.get("flow0.8"), False),
            ("low-contrast objects removed", PS["postfilter"], False)])]
x = 42
for n, ttl, sub, key, hl, items in groups:
    if n > 1:
        bb.append(f'<line x1="{x-15}" y1="{YO+78}" x2="{x-15}" y2="{YO+R1-18}" stroke="{NN["tintstroke"]}" stroke-width="1.2"/>')
    bb.append(header(x, n, ttl, sub) + step_tile(x, key, hl) + minibars(x + TW + 14, ty0 + 4, BW, items, hl))
    x += GW + 26
# 4: only if nothing works (small box, centred vertically)
FBH = 96
x5, y5 = 1798 - FTW, YO + 70 + (R1 - 70 - 14 - FBH) / 2
bb.append(rrect(x5, y5, FTW, FBH, 12, cA["tint"], cA["tintstroke"], 1.3))
bb.append(f'<circle cx="{x5+FTW/2}" cy="{y5+22}" r="11" fill="{cA["accent"]}"/>' + t(x5 + FTW / 2, y5 + 27, "4", 13, "bold", "#fff", "middle")
          + t(x5 + FTW / 2, y5 + 56, "If nothing works,", 15, "bold", INK, "middle") + t(x5 + FTW / 2, y5 + 76, "fine-tune or train", 15, "bold", INK, "middle"))
add(group("a troubleshooting", "".join(bb)))
# ---------------------------------------------------------------- c: what will you measure from a predicted image?
Y3 = YO + R1 + GAPR
R3 = 66 + 310 + 14
WCC = 938
cc3 = [frame(28, Y3, WCC, R3, "b", "Predicted images: what will you measure?", "B")]
halves = [("ok", "Used as an intermediate step", ["visualise", "segment", "detect", "register"],
           "Validate the downstream output", "e.g. segment on the predicted image, compare with annotations of acquired images"),
          ("caution", "Used as the measurement itself", ["intensity", "abundance", "localisation"],
           "Validate the measurement against acquired data", "e.g. predicted vs acquired fluorescence, in independent paired samples")]
hw = (WCC - 28 - 14) / 2
for k_, (kind, ttl, icons, concl, eg) in enumerate(halves):
    hx = 42 + k_ * (hw + 14)
    cc3.append(rrect(hx, Y3 + 66, hw, 280, 12, "#eef8f1" if kind == "ok" else "#fdf0ef", "#b9e0c5" if kind == "ok" else "#efc2be", 1.4))
    yb = Y3 + 100
    if kind == "ok":
        cc3.append(check_badge(hx + 28, yb - 5, cB["accent"], 13).replace('stroke-width="4.5"', 'stroke-width="3"')
                   .replace(f'M{hx+18},{yb-4} L{hx+25},{yb+3} L{hx+39},{yb-13}', f'M{hx+22},{yb-5} L{hx+26.5},{yb} L{hx+34},{yb-10}'))
    else:
        cc3.append(caution(hx + 28, yb - 7, "#c8423b"))
    cc3.append(t(hx + 50, yb + 1, ttl, 17, "bold", INK))
    n = len(icons)
    for i, nm in enumerate(icons):
        cx = hx + 20 + (hw - 40) * (i + 0.5) / n
        cc3.append(group(f"use icon {nm}", f'<g transform="translate({cx} {yb+72}) scale(1.25) translate({-cx} {-(yb+72)})">'
                         + b_icon(nm, cx, yb + 72, cB["accent"]) + "</g>"))
        cc3.append(t(cx, yb + 122, nm, 14.5, fill=INK, anchor="middle"))
    cc3.append(f'<line x1="{hx+20}" y1="{yb+148}" x2="{hx+hw-20}" y2="{yb+148}" stroke="{"#b9e0c5" if kind == "ok" else "#efc2be"}" stroke-width="1.4" stroke-dasharray="5 4"/>')
    cc3.append(t(hx + hw / 2, yb + 180, "→ " + concl, 16, "bold", INK, "middle"))
    words, lines_, cur = eg.split(), [], ""
    for w_ in words:
        if len(cur) + len(w_) > 46:
            lines_.append(cur); cur = w_
        else:
            cur = (cur + " " + w_).strip()
    lines_.append(cur)
    cc3.append(t(hx + hw / 2, yb + 208, lines_, 14, fill=BODY, anchor="middle", lh=18))
cc3.append(t(42 + 4, Y3 + R3 - 20, "Label predicted images as predicted; do not describe predicted fluorescence as measured.", 13.5, "bold", "#1a6b57"))
add(group("c what will you measure", "".join(cc3)))
# ---------------------------------------------------------------- d: denoising
XD = 28 + WCC + 6
WDN = 1812 - XD
gg = [frame(XD, Y3, WDN, R3, "c", "Denoising: measure intensity in the acquired image", "B")]
DI = json.load(open("panels/dn_intensity.json"))
DS = 250
for k_, (png, lbl, cap) in enumerate([("panels/dn_restored.png", "restored", "mask from here"), ("panels/dn_acquired.png", "acquired", "measure here")]):
    tx = XD + 16 + k_ * (DS + 34)
    gg.append(group(f"c denoise {lbl}", real_image(tx, Y3 + 78, DS, DS, png, 0.6337, 200, 20, f"denoise {lbl}")
                    + vector_outlines_sub(tx, Y3 + 78, DS, DS, "panels/dn_mask.json", "nuclei from restored image (vector)", MODEL, 1.4, None, (0, 0, 200, 200))
                    + halo(tx + 6, Y3 + 94, lbl)))
    gg.append(t(tx + DS / 2, Y3 + 78 + DS + 22, cap, 14, "bold", INK, "middle"))
gg.append(arrow(XD + 16 + DS + 5, Y3 + 78 + DS / 2, XD + 16 + DS + 29, Y3 + 78 + DS / 2, cB["accent"]))
sx0, sy0 = XD + 16 + 2 * (DS + 34) + 40, Y3 + 78
sw_ = XD + WDN - 24 - sx0
sh2 = DS
a_ = np.array(DI["acquired"]) - DI["bg_acquired"]
d_ = np.array(DI["restored"]) - DI["bg_restored"]
mx = float(np.percentile(np.r_[a_, d_], 99.5)) * 1.1
pts = "".join(f'<circle cx="{sx0+sw_*u/mx:.1f}" cy="{sy0+sh2-sh2*v/mx:.1f}" r="2" fill="{cB["accent"]}" fill-opacity="0.55"/>'
              for u, v in zip(a_, d_) if 0 < u < mx and 0 < v < mx)
gg.append(group("c denoise intensity scatter",
                f'<line x1="{sx0}" y1="{sy0+sh2}" x2="{sx0+sw_}" y2="{sy0+sh2}" stroke="{INK}" stroke-width="1.4"/>'
                f'<line x1="{sx0}" y1="{sy0}" x2="{sx0}" y2="{sy0+sh2}" stroke="{INK}" stroke-width="1.4"/>'
                f'<line x1="{sx0}" y1="{sy0+sh2}" x2="{sx0+sw_}" y2="{sy0+sh2-sh2*sw_/sw_}" stroke="#8a94a3" stroke-width="1.4" stroke-dasharray="5 4"/>'
                + pts
                + t(sx0 + sw_ / 2, sy0 + sh2 + 22, "acquired (per nucleus)", 13.5, fill=BODY, anchor="middle")
                + f'<text x="{sx0-10}" y="{sy0+sh2/2}" font-size="13.5" fill="{BODY}" text-anchor="middle" transform="rotate(-90 {sx0-10} {sy0+sh2/2})">restored</text>'
                + t(sx0 + sw_, sy0 + sh2 - 30, f"r = {DI['r']:.2f}", 13.5, "bold", INK, "end")
                + t(sx0 + sw_, sy0 + sh2 - 12, f"×{DI['ratio_median']:.2f}", 13.5, "bold", INK, "end")
                + t(sx0 + sw_ - 6, sy0 + 14, "y = x", 12, fill="#6b7686", anchor="end")))
add(group("d denoising", "".join(gg)))

# ---------------------------------------------------------------- d: artificial labelling (one ROI; two rows)
Y4 = Y3 + R3 + GAPR
RH_ = 330                                                    # height of each row box
R4 = 66 + 2 * RH_ + 12 + 14
AI = json.load(open("panels/al_intensity.json"))
ROI = json.load(open("panels/roi.json"))
dd = [frame(28, Y4, 1784, R4, "d", "Artificial labelling: validate what you will measure", "B")]
dd.append(key_item(1812 - 560, Y4 + 42, MODEL, "model") + key_item(1812 - 460, Y4 + 42, REF, "manual, annotator 1", DASH)
          + key_item(1812 - 250, Y4 + 42, REF2, "manual, annotator 2", DASH))
# input: full brightfield field with the ROI, pix2pix below it, then the predicted / acquired composites of the ROI
TS_ = 278                                                    # same tile size as panel a
FS = TS_
ty1, ty2 = Y4 + 66 + 38, Y4 + 66 + RH_ + 12 + 38             # tile tops of row 1 and row 2
g = [real_image(44, ty1, FS, FS, "panels/al_bf_full.png", PX, 1024, 100, "d brightfield full field", "#111111"), halo(50, ty1 + 16, "brightfield")]
g.append(f'<rect x="{44+ROI["x"]*FS/1024:.1f}" y="{ty1+ROI["y"]*FS/1022:.1f}" width="{ROI["w"]*FS/1024:.1f}" height="{ROI["h"]*FS/1022:.1f}" '
         f'fill="none" stroke="#ffd23f" stroke-width="2"/>')
dd.append(group("d brightfield", "".join(g)))
bxw, bxh = 130, 112
bx_, by_ = 44 + FS / 2 - bxw / 2, ty2 + (TS_ - bxh) / 2
dd.append(arrow(44 + FS / 2, ty1 + FS + 4, 44 + FS / 2, by_ - 4, cB["accent"]))
dd.append(group("d pix2pix", rrect(bx_, by_, bxw, bxh, 12, cB["tint"], cB["tintstroke"], 1.3)
                + t(bx_ + bxw / 2, by_ + 24, "DL model", 15, "bold", INK, "middle") + gan(bx_ + bxw / 2, by_ + 62, cB["accent"])
                + t(bx_ + bxw / 2, by_ + bxh - 10, "pix2pix", 14, fill=INK, anchor="middle")))
x2 = 44 + FS + 56
dd.append(arrow(bx_ + bxw + 4, ty2 + TS_ / 2, x2 - 6, ty2 + TS_ / 2, cB["accent"]))        # pix2pix -> predicted
for png, lbl, yy in [("panels/roi_acq.png", "acquired", ty1), ("panels/roi_pred.png", "predicted", ty2)]:
    dd.append(group(f"d roi {lbl} composite", real_image(x2, yy, TS_, TS_, png, PX, ROI["w"], 20, f"d roi {lbl}", "#ffffff") + halo(x2 + 6, yy + 16, lbl)))
dd.append(t(x2 + TS_ / 2, ty1 - 10, "DAPI + PECAM-1", 13.5, "bold", INK, "middle"))
rx0 = x2 + TS_ + 100
# from the predicted image to the two analyses
xa_ = x2 + TS_ + 4
xm_ = xa_ + 20
acc = cB["accent"].strip("#")
dd.append(arrow(xa_, ty2 + TS_ / 2, rx0 - 6, ty2 + TS_ / 2, cB["accent"]))
dd.append(f'<path d="M{xa_},{ty2+TS_/2} H{xm_} V{ty1+TS_/2+50} H{rx0-6}" fill="none" stroke="{cB["accent"]}" stroke-width="3" marker-end="url(#ah-{acc})"/>')
# manual annotations come from the acquired image
dd.append(f'<line x1="{xa_}" y1="{ty1+TS_/2-50}" x2="{rx0-8}" y2="{ty1+TS_/2-50}" stroke="{REF}" stroke-width="3" stroke-dasharray="6 4"/>'
          f'<path d="M{rx0-12},{ty1+TS_/2-56} L{rx0-2},{ty1+TS_/2-50} L{rx0-12},{ty1+TS_/2-44} Z" fill="{REF}"/>'
          + t((xa_ + rx0) / 2, ty1 + TS_ / 2 - 78, ["manual", "annotation"], 12, "bold", "#1279a8", "middle", lh=14))
dd.append(t((xa_ + rx0) / 2, ty1 + TS_ / 2 + 22, ["model", "segmentation"], 12, "bold", "#1a6b57", "middle", lh=14))
SUBR = (0, 0, ROI["w"], ROI["h"])
PW = (1798 - rx0 - 32) / 2                                  # width of one (tile + result) pair


def row_box(ry, kind, ttl):
    g = [rrect(rx0, ry, 1798 - rx0, RH_, 12, "#eef8f1" if kind == "ok" else "#fdf0ef", "#b9e0c5" if kind == "ok" else "#efc2be", 1.4)]
    if kind == "ok":
        g.append(check_badge(rx0 + 24, ry + 22, cB["accent"], 11).replace('stroke-width="4.5"', 'stroke-width="2.8"')
                 .replace(f'M{rx0+14},{ry+23} L{rx0+21},{ry+30} L{rx0+35},{ry+14}', f'M{rx0+18.5},{ry+22.5} L{rx0+22.5},{ry+26.5} L{rx0+29.5},{ry+17.5}'))
    else:
        g.append(caution(rx0 + 24, ry + 21, "#c8423b"))
    g.append(t(rx0 + 42, ry + 27, ttl, 15.5, "bold", INK))
    return "".join(g)


def bars(x, y, title, items, w=150):
    g = [t(x, y, title, 15, "bold", INK)]
    for i, (lbl, v, colr) in enumerate(items):
        yy = y + 30 + i * 44
        g.append(t(x, yy, lbl, 13.5, fill=BODY) + f'<rect x="{x}" y="{yy+6}" width="{w}" height="11" rx="3" fill="#e4e8ee"/>'
                 f'<rect x="{x}" y="{yy+6}" width="{w*v:.1f}" height="11" rx="3" fill="{colr}"/>' + t(x + w + 8, yy + 17, f"{v:.2f}", 14.5, "bold", INK))
    return "".join(g)


def scatter(sx0, sy0, key, unit_lbl, colr, size=190):
    sh2 = size
    xa, xp = np.array(AI[key]["acquired"]), np.array(AI[key]["predicted"])
    ma, mp = np.percentile(xa, 99.5) * 1.08, np.percentile(xp, 99.5) * 1.08
    pts = "".join(f'<circle cx="{sx0+size*max(u,0)/ma:.1f}" cy="{sy0+sh2-sh2*max(v,0)/mp:.1f}" r="2" fill="{colr}" fill-opacity="0.5"/>'
                  for u, v in zip(xa, xp) if u < ma and v < mp)
    return group(f"d intensity {key}",
                 f'<line x1="{sx0}" y1="{sy0+sh2}" x2="{sx0+size}" y2="{sy0+sh2}" stroke="{INK}" stroke-width="1.4"/>'
                 f'<line x1="{sx0}" y1="{sy0}" x2="{sx0}" y2="{sy0+sh2}" stroke="{INK}" stroke-width="1.4"/>' + pts
                 + t(sx0, sy0 - 10, f"{key}, {unit_lbl}", 14.5, "bold", INK)
                 + t(sx0 + size / 2, sy0 + sh2 + 20, "acquired", 13.5, fill=BODY, anchor="middle")
                 + f'<text x="{sx0-10}" y="{sy0+sh2/2}" font-size="13.5" fill="{BODY}" text-anchor="middle" transform="rotate(-90 {sx0-10} {sy0+sh2/2})">predicted</text>'
                 + t(sx0 + 8, sy0 + 12, f"r = {AI[key]['r']:.2f}", 15, "bold", INK)
                 + t(sx0 + 8, sy0 + 30, f"n = {AI[key]['n']}", 12.5, fill=BODY))


# row 1: intermediate step (outlines only)
ry = Y4 + 66
dd.append(row_box(ry, "ok", "Intermediate step: to aid segmentation"))
seg = [("Nuclei", [("panels/roi_manual_nuclei.json", "manual nuclei (vector)", REF, DASH), ("panels/roi_model_nuclei.json", "StarDist on predicted DAPI (vector)", MODEL, None)],
        "Nuclei · F1", [("model vs manual nuclei", 0.828, F1C)]),
       ("Cells", [("panels/roi_annot1_cells.json", "annotator 1 cells (vector)", REF, DASH), ("panels/roi_annot2_cells.json", "annotator 2 cells (vector)", REF2, DASH),
                  ("panels/roi_model_cells.json", "Cellpose on predicted PECAM-1 (vector)", MODEL, None)],
        "Cells · F1", [("annotator 1 vs 2", 0.897, "#8a94a3"), ("model vs annotator 1", 0.781, F1C), ("model vs annotator 2", 0.746, F1C)])]
for k_, (name, lay, btitle, items) in enumerate(seg):
    tx = rx0 + 16 + k_ * (PW + 0)
    g = [real_image(tx, ry + 38, TS_, TS_, "from_fig1_panel_a/dark_tile.png", PX, ROI["w"], 20, f"d {name} (outlines only)")]
    for path, l_, colr, dash in lay:
        g.append(vector_outlines_sub(tx, ry + 38, TS_, TS_, path, l_, colr, 1.5, dash, SUBR))
    g.append(halo(tx + 6, ry + 54, name.lower()))
    yb_ = ry + 38 + TS_
    g.append(rrect(tx + 4, yb_ - 46, 150, 40, 4, "#0b111d", "none", 0, ' fill-opacity="0.85"')
             + t(tx + 10, yb_ - 31, "model, on predicted", 12.5, "bold", MODEL)
             + t(tx + 10, yb_ - 14, "manual, on acquired", 12.5, "bold", REF))
    dd.append(group(f"d {name} outlines", "".join(g)))
    dd.append(bars(tx + TS_ + 22, ry + 70, btitle, items))
# row 2: the measurement itself (grayscale, predicted | acquired)
ry = Y4 + 66 + RH_ + 12
dd.append(row_box(ry, "caution", "Measurement itself: intensity"))
for k_, (key, png, unit_lbl, colr) in enumerate([("DAPI", "panels/roi_dapi_split.png", "per nucleus", "#b0359c"),
                                                 ("PECAM-1", "panels/roi_pecam_split.png", "per cell", "#2a8a3e")]):
    tx = rx0 + 16 + k_ * PW
    dd.append(group(f"d {key} grayscale", split_widget_r(tx, ry + 38, TS_, TS_, png, "predicted", "acquired")
))
    dd.append(scatter(tx + TS_ + 40, ry + 80, key, unit_lbl, colr, 150))
add(group("d artificial labelling", "".join(dd)))
# ---------------------------------------------------------------- e: super-resolution
Y5 = Y4 + R4 + GAPR
R5 = 66 + 300 + 14
ee = [frame(28, Y5, 1784, R5, "e", "Super-resolution: check against the input and, where possible, higher-resolution data", "B")]
SP = json.load(open("panels/sr_profile.json"))
SQ = json.load(open("panels/squirrel.json"))
TWS = json.load(open("panels/tubule_width.json"))["summary"]
SS = 168
rowy = SP["row"] / 140
# --- left box: consistency with the diffraction-limited input (SQUIRREL)
w1 = 16 + 3 * (SS + 10) + 196
ee.append(rrect(42, Y5 + 66, w1, 300, 12, "#ffffff", cB["innerstroke"]))
ee.append(t(58, Y5 + 90, "Consistency with the diffraction-limited input (SQUIRREL)", 14.5, "bold", INK))
tiles_ = [("panels/sr_input.png", "low-res input", True), ("panels/sr_predicted.png", "predicted", True), ("panels/sr_squirrel.png", "error map", False)]
for k_, (png, lbl, line) in enumerate(tiles_):
    tx = 58 + k_ * (SS + 10)
    ee.append(group(f"e sr {lbl}", real_image(tx, Y5 + 104, SS, SS, png, 0.0313, 140, 1, f"sr {lbl}")
                    + (f'<line x1="{tx}" y1="{Y5+104+SS*rowy:.1f}" x2="{tx+SS}" y2="{Y5+104+SS*rowy:.1f}" stroke="#ffd23f" stroke-width="1.6" stroke-dasharray="4 3"/>' if line else "")))
    ee.append(t(tx + SS / 2, Y5 + 104 + SS + 20, lbl, 14, "bold", INK, "middle"))
# colour bar under the error map
mx_ = 58 + 2 * (SS + 10)
cb_y = Y5 + 104 + SS + 32
ee.append(real_image(mx_ + 14, cb_y, SS - 28, 9, "panels/inferno_bar.png", 1, 256, 0, "error map colour bar").replace("<line", "<!--").replace("/>\n", "-->")
          if False else f'<image x="{mx_+14}" y="{cb_y}" width="{SS-28}" height="9" preserveAspectRatio="none" '
          f'xlink:href="data:image/png;base64,{base64.b64encode(open("panels/inferno_bar.png","rb").read()).decode()}"/>')
ee.append(t(mx_ + 14, cb_y + 23, "0", 12, fill=BODY, anchor="middle") + t(mx_ + SS - 14, cb_y + 23, "high", 12, fill=BODY, anchor="middle")
          + t(mx_ + SS / 2, cb_y + 23, "error (a.u.)", 12, fill=BODY, anchor="middle"))
# RSP bars: agreement with the input (axis 0.90-1.00)
bx0 = 58 + 3 * (SS + 10) + 14
bw = 120
ee.append(t(bx0, Y5 + 124, "RSP with the input", 14, "bold", INK))
for i, (lbl, v, colr) in enumerate([("predicted", SQ["predicted"]["RSP"], MODEL), ("higher-res", SQ["high_res"]["RSP"], INK)]):
    yy = Y5 + 152 + i * 44
    ee.append(t(bx0, yy, lbl, 13.5, fill=BODY) + f'<rect x="{bx0}" y="{yy+6}" width="{bw}" height="11" rx="3" fill="#e4e8ee"/>'
              f'<rect x="{bx0}" y="{yy+6}" width="{bw*(v-0.9)/0.1:.1f}" height="11" rx="3" fill="{colr}"/>' + t(bx0 + bw + 6, yy + 17, f"{v:.2f}", 14, "bold", INK))
ay_ = Y5 + 152 + 2 * 44 + 4
ee.append(f'<line x1="{bx0}" y1="{ay_}" x2="{bx0+bw}" y2="{ay_}" stroke="{INK}" stroke-width="1.1"/>'
          + "".join(f'<line x1="{bx0+bw*k/2:.1f}" y1="{ay_}" x2="{bx0+bw*k/2:.1f}" y2="{ay_+4}" stroke="{INK}" stroke-width="1.1"/>'
                    + t(bx0 + bw * k / 2, ay_ + 17, f"{0.9+0.05*k:.2f}", 11.5, fill=BODY, anchor="middle") for k in range(3)))
# --- right box: comparison with higher-resolution data
x2 = 42 + w1 + 12
w2 = 1798 - x2
ee.append(rrect(x2, Y5 + 66, w2, 300, 12, "#ffffff", cB["innerstroke"]))
ee.append(t(x2 + 16, Y5 + 90, "Comparison with higher-resolution data: test the feature you will measure", 14.5, "bold", INK))
tx = x2 + 16
ee.append(group("e sr reference", real_image(tx, Y5 + 104, SS, SS, "panels/sr_hr.png", 0.0313, 140, 1, "sr reference")
                + f'<line x1="{tx}" y1="{Y5+104+SS*rowy:.1f}" x2="{tx+SS}" y2="{Y5+104+SS*rowy:.1f}" stroke="#ffd23f" stroke-width="1.6" stroke-dasharray="4 3"/>'))
ee.append(t(tx + SS / 2, Y5 + 104 + SS + 20, "higher-res", 14, "bold", INK, "middle"))
px0, py0 = tx + SS + 26, Y5 + 112
pw_, ph_ = 300, 150
ee.append(f'<line x1="{px0}" y1="{py0+ph_}" x2="{px0+pw_}" y2="{py0+ph_}" stroke="{INK}" stroke-width="1.4"/>')
for key, colr, sw, dash in [("low_res", "#9aa4b2", 1.8, "4 3"), ("high_res", INK, 2.0, None), ("predicted", MODEL, 2.0, None)]:
    v = SP[key]
    pl = " ".join(f"{px0+pw_*i/(len(v)-1):.1f},{py0+ph_-ph_*q:.1f}" for i, q in enumerate(v))
    ee.append(f'<polyline points="{pl}" fill="none" stroke="{colr}" stroke-width="{sw}"' + (f' stroke-dasharray="{dash}"' if dash else "") + "/>")
ee.append(t(px0 + pw_ / 2, py0 + ph_ + 20, "intensity along the dashed line (4.4 µm)", 13, fill=BODY, anchor="middle"))
ee.append(key_item(px0, py0 + ph_ + 46, INK, "higher-res") + key_item(px0 + 104, py0 + ph_ + 46, MODEL, "predicted")
          + key_item(px0 + 210, py0 + ph_ + 46, "#9aa4b2", "low-res", "4 3"))
# tubule width: median and interquartile range, same locations in all three images
wx0 = px0 + pw_ + 44
ww = x2 + w2 - 24 - wx0
ee.append(t(wx0, Y5 + 120, f"Tubule width (FWHM, nm), {TWS['n_locations']:,} locations", 13.5, "bold", INK))
lo_, hi_ = 100, 400
X_ = lambda v: wx0 + 100 + (ww - 150) * (v - lo_) / (hi_ - lo_)
for i, (key, lbl, colr) in enumerate([("low_res", "low-res input", "#9aa4b2"), ("predicted", "predicted", MODEL), ("reference", "higher-res", INK)]):
    yy = Y5 + 156 + i * 38
    q = TWS[key]
    ee.append(t(wx0, yy + 5, lbl, 13.5, fill=BODY)
              + f'<line x1="{X_(q["q25"]):.1f}" y1="{yy}" x2="{X_(q["q75"]):.1f}" y2="{yy}" stroke="{colr}" stroke-width="7" stroke-linecap="round" opacity="0.45"/>'
              + f'<circle cx="{X_(q["median_nm"]):.1f}" cy="{yy}" r="6" fill="{colr}"/>'
              + t(X_(hi_) + 10, yy + 5, f"{q['median_nm']:.0f}", 13.5, "bold", INK))
ax_y = Y5 + 156 + 3 * 38 - 14
ee.append(f'<line x1="{X_(lo_):.1f}" y1="{ax_y}" x2="{X_(hi_):.1f}" y2="{ax_y}" stroke="{INK}" stroke-width="1.2"/>')
for v in (100, 200, 300, 400):
    ee.append(f'<line x1="{X_(v):.1f}" y1="{ax_y}" x2="{X_(v):.1f}" y2="{ax_y+5}" stroke="{INK}" stroke-width="1.2"/>' + t(X_(v), ax_y + 19, str(v), 12, fill=BODY, anchor="middle"))
D_ = TWS["pred_minus_ref"]
ee.append(t(wx0, ax_y + 48, f"predicted − higher-res, same location: {D_['median_nm']:+.0f} nm (IQR {D_['q25']:+.0f} to {D_['q75']:+.0f})".replace("-", "−"), 13, "bold", INK))
add(group("e super-resolution", "".join(ee)))

H = Y5 + R5 + 20
svg = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
       f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" xmlns:xlink="http://www.w3.org/1999/xlink" '
       f'width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">\n'
       f'<defs>{"".join(defs)}</defs>\n<rect width="{W}" height="{H}" fill="#ffffff"/>\n'
       + "\n".join(out) + "\n</svg>\n")
open("fig2.svg", "w", encoding="utf-8").write(svg)
print("written", len(svg) // 1024, "KB; height", H)
