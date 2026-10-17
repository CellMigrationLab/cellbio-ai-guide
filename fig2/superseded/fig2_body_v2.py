YO = 20
GAPR = 10
SEGX, SEGY, SEGW, SEGH = 240, 40, 240, 260          # troubleshooting window (full-field px), as Fig. 1c step 3
cA, cB = C["A"], C["B"]
PS = json.load(open("data/perturb_scores.json"))


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
FTW = 196                                 # fine-tune box width
GW = (1784 - 28 - FTW - 3 * 26) / 3      # width of one check group
BW = 200                                  # bar column width
TW = GW - BW - 14
TH = TW * SEGH / SEGW
R1 = round(66 + 64 + TH + 26 + 14)
bb = [frame(28, YO, 1784, R1, "a", "When a pre-trained model performs poorly, find the mismatch first", "A")]
bb.append(key_item(1812 - 250, YO + 42, MODEL, "model") + key_item(1812 - 150, YO + 42, REF, "reference", DASH))
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
    return tile(x, ty0, TW, TH, "data4/B_rep_bf.png",
                [("data4/B_rep_ref.json", "reference (vector)", REF, DASH), (f"data/ts_cp_{key}.json", f"{label} (vector)", MODEL, None)],
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
          (3, "Check the post-processing", "is it segmenting the intended object?", "postfilter", "low-contrast objects removed",
           [("default", D, True), ("stricter probability threshold", PS["cellprob2"], False), ("looser flow threshold", PS.get("flow0.8"), False),
            ("low-contrast objects removed", PS["postfilter"], False)])]
x = 42
for n, ttl, sub, key, hl, items in groups:
    if n > 1:
        bb.append(f'<line x1="{x-13}" y1="{YO+78}" x2="{x-13}" y2="{YO+R1-18}" stroke="{NN["tintstroke"]}" stroke-width="1.2"/>')
    bb.append(header(x, n, ttl, sub) + step_tile(x, key, hl) + minibars(x + TW + 14, ty0 + 4, BW, items, hl))
    x += GW + 26
# 4: fine-tune (schematic)
x5 = 1798 - FTW
bb.append(rrect(x5, YO + 70, FTW, R1 - 70 - 14, 12, cA["tint"], cA["tintstroke"], 1.3))
bb.append(f'<circle cx="{x5+22}" cy="{YO+92}" r="11" fill="{cA["accent"]}"/>' + t(x5 + 22, YO + 97, "4", 13, "bold", "#fff", "middle")
          + t(x5 + 40, YO + 97, "If nothing works,", 16, "bold", INK) + t(x5 + 40, YO + 116, "fine-tune", 16, "bold", INK))
cy5 = ty0 + TH / 2 + 8
bb.append(t(x5 + FTW / 2, ty0 + 8, ["only for a systematic", "failure"], 13.5, fill=BODY, anchor="middle", lh=17))
bb.append(group("fine-tune loop (schematic)",
                f'<circle cx="{x5+FTW/2}" cy="{cy5}" r="50" fill="none" stroke="{cA["accent"]}" stroke-width="2.4" stroke-dasharray="6 5"/>'
                + t(x5 + FTW / 2, cy5 - 60, "correct", 13.5, "bold", INK, "middle")
                + t(x5 + FTW / 2, cy5 + 72, "retrain", 13.5, "bold", INK, "middle")
                + unet2(x5 + FTW / 2, cy5, cA["accent"])))
bb.append(t(x5 + FTW / 2, cy5 + 100, ["correct diverse predictions", "where it fails"], 13, fill=BODY, anchor="middle", lh=16))
add(group("a troubleshooting", "".join(bb)))
# ---------------------------------------------------------------- b: is it good enough?
Y2 = YO + R1 + GAPR
R2 = 66 + 360 + 14
cc = [frame(28, Y2, 1784, R2, "b", "Is it good enough? Check the errors that matter for the measurement", "A")]
# measurement -> error that matters
x0, w0 = 44, 420
cc.append(rrect(x0, Y2 + 66, w0, 360, 12, "#ffffff", cA["innerstroke"]))
cc.append(box_title(x0 + w0 / 2, Y2 + 96, "What will you measure?"))
MEAS = [("Counts", "missed and false objects"), ("Morphology", "boundaries of matched cells"),
        ("Phenotypes", "misclassified objects"), ("Tracks", "merges and splits break links")]
POS = [(x0 + w0 * 0.25, Y2 + 176), (x0 + w0 * 0.75, Y2 + 176), (x0 + w0 * 0.25, Y2 + 330), (x0 + w0 * 0.75, Y2 + 330)]
a = []
CT = 0
exec(open("measure_icons_block.py").read())
cc += a
cc.append(arrow(x0 + w0 + 4, Y2 + 246, x0 + w0 + 22, Y2 + 246, cA["accent"]))
# two tiles with error markers
ES = json.load(open("data/error_summary.json"))
EM = json.load(open("data/err_markers.json"))
x1 = x0 + w0 + 26
w1 = 1796 - x1
cc.append(rrect(x1, Y2 + 66, w1, 360, 12, "#ffffff", cA["innerstroke"]))
ETW = 276
ETH = ETW * 260 / 240
SUBE = (0, 0, 240, 260)
cand = [("Custom-trained", "stardist", "data/err_stardist.json", ES["stardist"]),
        ("Pre-trained generalist + post-processing", "cellpose_filtered", "data/err_cellpose_filtered.json", ES["cellpose_postfilter"])]
for k_, (lbl, key, cj, s_) in enumerate(cand):
    tx = x1 + 18 + k_ * (ETW + 22)
    cc.append(t(tx, Y2 + 94, lbl, 15, "bold", INK))
    cc.append(tile(tx, Y2 + 114, ETW, ETH, "data/err_bf.png",
                   [("data/err_ref.json", "reference (vector)", REF, DASH), (cj, f"{lbl} (vector)", MODEL, None)],
                   f"errors {lbl}", EM[key]))
# error table
tx0 = x1 + 18 + 2 * (ETW + 22) + 14
cols = [tx0 + 250, tx0 + 360]
ty = Y2 + 100
cc.append(t(cols[0], ty, ["Custom-", "trained"], 13.5, "bold", INK, "middle", lh=16)
          + t(cols[1], ty, ["Generalist +", "post-proc."], 13.5, "bold", INK, "middle", lh=16))
BIO = json.load(open("data/bio_result.json"))
rows_ = [("missed cells", "missed", "ring"), ("false objects", "false", "cross"), ("merged cells", "merges", None),
         ("split cells", "splits", None), ("boundary IoU, matched", "mean_iou_matched", None), ("F1 (IoU ≥ 0.5)", "f1", None)]
RS = 29
for r_, (lbl, key, mk) in enumerate(rows_):
    yy = ty + 46 + r_ * RS
    if r_ in (4,):
        cc.append(f'<line x1="{tx0}" y1="{yy-24}" x2="{cols[1]+50}" y2="{yy-24}" stroke="{NN["tintstroke"]}" stroke-width="1.2"/>')
    if mk == "ring":
        cc.append(f'<circle cx="{tx0+8}" cy="{yy-5}" r="7" fill="none" stroke="{ERRC}" stroke-width="2.4"/>')
    elif mk == "cross":
        cc.append(f'<path d="M{tx0+2},{yy-11} L{tx0+14},{yy+1} M{tx0+14},{yy-11} L{tx0+2},{yy+1}" stroke="{ERRC}" stroke-width="2.6" stroke-linecap="round"/>')
    cc.append(t(tx0 + 24, yy, lbl, 14.5, fill=INK))
    for ci, nm in enumerate(["stardist", "cellpose_postfilter"]):
        v = ES[nm][key]
        cc.append(t(cols[ci], yy, f"{v:.2f}" if isinstance(v, float) else str(v), 15, "bold", INK, "middle"))
yb_ = ty + 46 + 6 * RS + 8
cc.append(f'<line x1="{tx0}" y1="{yb_-20}" x2="{cols[1]+50}" y2="{yb_-20}" stroke="{NN["tintstroke"]}" stroke-width="1.2"/>')
cc.append(t(tx0, yb_, "Biological result (reference)", 13.5, "bold", "#1f4e8c"))
for r_, (lbl, key, unit, fmt) in enumerate([("cell count", "count", "", "{:.0f}"), ("mean area, µm²", "mean_area_um2", "", "{:.0f}")]):
    yy = yb_ + 26 + r_ * RS
    refv = BIO["reference"][key]
    cc.append(t(tx0 + 24, yy, f"{lbl} ({fmt.format(refv)})", 14.5, fill=INK))
    for ci, nm in enumerate(["custom_trained", "generalist_postfilter"]):
        v = BIO[nm][key]
        pct = 100 * (v / refv - 1)
        cc.append(t(cols[ci], yy, f"{fmt.format(v)} ({pct:+.0f}%)", 14.5, "bold", INK, "middle"))
add(group("c good enough", "".join(cc)))

# ---------------------------------------------------------------- c: denoising   |   d: artificial labelling
Y3 = Y2 + R2 + GAPR
R3 = 66 + 380 + 14
WC = 640
xd = 28 + WC + 6
WD = 1812 - xd
gg = [frame(28, Y3, WC, R3, "c", "Denoising", "B")]
DI = json.load(open("data/dn_intensity.json"))
gg.append(t(44, Y3 + 92, ["Derive the mask from the restored image;", "measure intensity in the acquired image"], 15.5, "bold", INK, lh=19))
DS = 196
for k_, (png, lbl, cap) in enumerate([("data/dn_restored.png", "restored", "mask from here"), ("data/dn_acquired.png", "acquired", "measure here")]):
    tx = 44 + k_ * (DS + 32)
    gg.append(group(f"c denoise {lbl}", real_image(tx, Y3 + 128, DS, DS, png, 0.6337, 200, 20, f"denoise {lbl}")
                    + vector_outlines_sub(tx, Y3 + 128, DS, DS, "data/dn_mask.json", "nuclei from restored image (vector)", MODEL, 1.4, None, (0, 0, 200, 200))
                    + halo(tx + 6, Y3 + 144, lbl)))
    gg.append(t(tx + DS / 2, Y3 + 128 + DS + 22, cap, 14, "bold", INK, "middle"))
gg.append(arrow(44 + DS + 4, Y3 + 128 + DS / 2, 44 + DS + 28, Y3 + 128 + DS / 2, cB["accent"]))
sx0, sy0 = 44 + 2 * (DS + 32) + 28, Y3 + 128
sw_ = 28 + WC - 16 - sx0
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
                + t(sx0 + sw_ / 2, sy0 + sh2 + 22, "acquired", 13.5, fill=BODY, anchor="middle")
                + f'<text x="{sx0-10}" y="{sy0+sh2/2}" font-size="13.5" fill="{BODY}" text-anchor="middle" transform="rotate(-90 {sx0-10} {sy0+sh2/2})">restored</text>'
                + t(sx0 + sw_, sy0 + sh2 - 30, f"r = {DI['r']:.2f}", 13.5, "bold", INK, "end")
                + t(sx0 + sw_, sy0 + sh2 - 12, f"×{DI['ratio_median']:.2f}", 13.5, "bold", INK, "end")
                + t(sx0 + sw_ - 6, sy0 + 14, "y = x", 12, fill="#6b7686", anchor="end")))
gg.append(t(sx0 + sw_ / 2, Y3 + 128 + DS + 44, "per-nucleus intensity", 12.5, fill=BODY, anchor="middle"))
add(group("c denoising", "".join(gg)))

# d: artificial labelling
dd = [frame(xd, Y3, WD, R3, "d", "Artificial labelling", "B")]
dd.append(key_item(xd + WD - 470, Y3 + 42, MODEL, "on predicted image") + key_item(xd + WD - 290, Y3 + 42, REF, "manual outlines 1", DASH)
          + key_item(xd + WD - 140, Y3 + 42, REF2, "outlines 2", DASH))
# input / predicted pair
PSZ = 150
px_ = xd + 16
for k_, (png, lbl, sub) in enumerate([("data/al_bf.png", "brightfield", "input"), ("data/al_pred.png", "predicted", "pix2pix: DAPI + PECAM-1")]):
    yy = Y3 + 76 + k_ * (PSZ + 36)
    dd.append(real_image(px_, yy, PSZ, PSZ, png, PX, 210, 50, f"d {lbl}", "#ffffff" if k_ else "#111111") + halo(px_ + 6, yy + 16, lbl))
    dd.append(t(px_ + PSZ / 2, yy + PSZ + 18, sub, 13, fill=BODY, anchor="middle"))
dd.append(arrow(px_ + PSZ / 2, Y3 + 76 + PSZ + 22, px_ + PSZ / 2, Y3 + 76 + PSZ + 34, cB["accent"], 2.4))
TWd, THd = 168, 210
gx1 = px_ + PSZ + 20
grp = [("ok", "An intermediate step", "validate the downstream output", [
            ("Cells", "data3/B_PECAM_acquired.png",
             [("data3/B_annotator1_contours.json", "manual outlines 1 (vector)", REF, DASH), ("data3/B_annotator2_contours.json", "manual outlines 2 (vector)", REF2, DASH),
              ("data3/B_cells_contours.json", "Cellpose on predicted PECAM (vector)", MODEL, None)],
             "F1", [("outlines 1 vs 2", 0.897, "#8a94a3"), ("vs outlines 1", 0.781, F1C), ("vs outlines 2", 0.746, F1C)]),
            ("Nuclei", "data3/B_DAPI_acquired_nuclei_tile.png",
             [("data3/B_nuclei_manual_contours.json", "manual nuclei (vector)", REF, DASH), ("data3/B_nuclei_stardist_contours.json", "StarDist on predicted DAPI (vector)", MODEL, None)],
             "F1", [("vs manual nuclei", 0.828, F1C)])]),
       ("caution", "The measurement itself", "compare with acquired fluorescence", [
            ("Intensity", "data5/split_intensity.png", None, "Pearson r, per pixel", [("DAPI", 0.891, RC), ("PECAM-1", 0.243, RC)])])]
gx = gx1
for kind, ttl, sub, items in grp:
    gw_ = len(items) * (TWd + 16) + 16
    if kind == "caution":
        gw_ = xd + WD - 14 - gx
    dd.append(rrect(gx, Y3 + 66, gw_, 380, 12, "#ffffff", cB["innerstroke"]))
    if kind == "ok":
        dd.append(check_badge(gx + 24, Y3 + 88, cB["accent"], 11).replace('stroke-width="4.5"', 'stroke-width="2.8"')
                  .replace(f'M{gx+14},{Y3+89} L{gx+21},{Y3+96} L{gx+35},{Y3+80}', f'M{gx+18.5},{Y3+88.5} L{gx+22.5},{Y3+92.5} L{gx+29.5},{Y3+83.5}'))
    else:
        dd.append(caution(gx + 24, Y3 + 87))
    dd.append(t(gx + 42, Y3 + 93, ttl, 16, "bold", INK) + t(gx + 42, Y3 + 112, sub, 13.5, fill=BODY))
    for j_, (name, png, layers, metric, bars_) in enumerate(items):
        tx = gx + 16 + j_ * (TWd + 16)
        ty = Y3 + 126
        if layers is None:
            dd.append(split_widget_r(tx, ty, TWd, THd, png, "predicted", "acquired"))
        else:
            g = [real_image(tx, ty, TWd, THd, "data5/dark_tile.png", PX, 100, 20, f"d {name} (outlines only)")]
            for path, lbl, colr, dash in layers:
                g.append(vector_outlines_l(tx, ty, TWd, THd, path, lbl, colr, 1.6, dash))
            dd.append(group(f"d {name}", "".join(g)))
        dd.append(t(tx, ty + THd + 20, f"{name} · {metric}", 13.5, "bold", INK))
        bw_ = (TWd - 40) if layers is not None else (gw_ - 32 - 40)
        for i, (lbl, v, colr) in enumerate(bars_):
            yy = ty + THd + 38 + i * 27
            dd.append(t(tx, yy, lbl, 12.5, fill=BODY) + f'<rect x="{tx}" y="{yy+5}" width="{bw_}" height="8" rx="3" fill="#e4e8ee"/>'
                      f'<rect x="{tx}" y="{yy+5}" width="{bw_*v:.1f}" height="8" rx="3" fill="{colr}"/>' + t(tx + bw_ + 5, yy + 13, f"{v:.2f}", 13, "bold", INK))
    gx += gw_ + 12
add(group("d artificial labelling", "".join(dd)))

# ---------------------------------------------------------------- e: super-resolution
Y5 = Y3 + R3 + GAPR
R5 = 66 + 290 + 14
ee = [frame(28, Y5, 1784, R5, "e", "Super-resolution: check against the input and, where possible, higher-resolution data", "B")]
SP = json.load(open("data/sr_profile.json"))
SQ = json.load(open("data/squirrel.json"))
TWS = json.load(open("data/tubule_width.json"))["summary"]
SS = 186
rowy = SP["row"] / 140
ee.append(rrect(42, Y5 + 66, 3 * (SS + 10) + 22, 290, 12, "#ffffff", cB["innerstroke"]))
ee.append(t(58, Y5 + 90, "Consistency with the diffraction-limited input (SQUIRREL)", 14.5, "bold", INK))
tiles_ = [("data/sr_input.png", "low-res input", True), ("data/sr_predicted.png", "predicted", True), ("data/sr_squirrel.png", "error map", False)]
for k_, (png, lbl, line) in enumerate(tiles_):
    tx = 58 + k_ * (SS + 10)
    ee.append(group(f"e sr {lbl}", real_image(tx, Y5 + 104, SS, SS, png, 0.0313, 140, 1, f"sr {lbl}")
                    + (f'<line x1="{tx}" y1="{Y5+104+SS*rowy:.1f}" x2="{tx+SS}" y2="{Y5+104+SS*rowy:.1f}" stroke="#ffd23f" stroke-width="1.6" stroke-dasharray="4 3"/>' if line else "")))
    ee.append(t(tx + SS / 2, Y5 + 104 + SS + 20, lbl, 14, "bold", INK, "middle"))
mx_ = 58 + 2 * (SS + 10)
ee.append(t(mx_ + SS / 2, Y5 + 104 + SS + 40, f"RSP: predicted {SQ['predicted']['RSP']:.2f} · reference {SQ['high_res']['RSP']:.2f}", 12.5, fill=INK, anchor="middle"))
x2 = 42 + 3 * (SS + 10) + 22 + 12
w2 = 1798 - x2
ee.append(rrect(x2, Y5 + 66, w2, 290, 12, "#ffffff", cB["innerstroke"]))
ee.append(t(x2 + 16, Y5 + 90, "Comparison with higher-resolution data: test the feature you will measure", 14.5, "bold", INK))
tx = x2 + 16
ee.append(group("e sr reference", real_image(tx, Y5 + 104, SS, SS, "data/sr_hr.png", 0.0313, 140, 1, "sr reference")
                + f'<line x1="{tx}" y1="{Y5+104+SS*rowy:.1f}" x2="{tx+SS}" y2="{Y5+104+SS*rowy:.1f}" stroke="#ffd23f" stroke-width="1.6" stroke-dasharray="4 3"/>'))
ee.append(t(tx + SS / 2, Y5 + 104 + SS + 20, "higher-res reference", 14, "bold", INK, "middle"))
# profile
px0, py0 = tx + SS + 30, Y5 + 112
pw_, ph_ = 330, 150
ee.append(f'<line x1="{px0}" y1="{py0+ph_}" x2="{px0+pw_}" y2="{py0+ph_}" stroke="{INK}" stroke-width="1.4"/>')
for key, colr, sw, dash in [("low_res", "#9aa4b2", 1.8, "4 3"), ("high_res", INK, 2.0, None), ("predicted", MODEL, 2.0, None)]:
    v = SP[key]
    pl = " ".join(f"{px0+pw_*i/(len(v)-1):.1f},{py0+ph_-ph_*q:.1f}" for i, q in enumerate(v))
    ee.append(f'<polyline points="{pl}" fill="none" stroke="{colr}" stroke-width="{sw}"' + (f' stroke-dasharray="{dash}"' if dash else "") + "/>")
ee.append(t(px0 + pw_ / 2, py0 + ph_ + 20, "intensity along the dashed line", 13, fill=BODY, anchor="middle"))
ee.append(key_item(px0, py0 + ph_ + 46, INK, "reference") + key_item(px0 + 110, py0 + ph_ + 46, MODEL, "predicted")
          + key_item(px0 + 222, py0 + ph_ + 46, "#9aa4b2", "low-res", "4 3"))
# tubule width: median and interquartile range
wx0 = px0 + pw_ + 50
ww = x2 + w2 - 24 - wx0
ee.append(t(wx0, Y5 + 120, f"Tubule width (FWHM, nm), {TWS['n_locations']} locations", 13.5, "bold", INK))
lo_, hi_ = 100, 400
for i, (key, lbl, colr) in enumerate([("low_res", "low-res input", "#9aa4b2"), ("predicted", "predicted", MODEL), ("reference", "reference", INK)]):
    yy = Y5 + 156 + i * 40
    q = TWS[key]
    X_ = lambda v: wx0 + 110 + (ww - 160) * (v - lo_) / (hi_ - lo_)
    ee.append(t(wx0, yy + 5, lbl, 13.5, fill=BODY)
              + f'<line x1="{X_(q["q25"]):.1f}" y1="{yy}" x2="{X_(q["q75"]):.1f}" y2="{yy}" stroke="{colr}" stroke-width="7" stroke-linecap="round" opacity="0.45"/>'
              + f'<circle cx="{X_(q["median_nm"]):.1f}" cy="{yy}" r="6" fill="{colr}"/>'
              + t(X_(hi_) + 10, yy + 5, f"{q['median_nm']:.0f}", 13.5, "bold", INK))
ax_y = Y5 + 156 + 3 * 40 - 14
ee.append(f'<line x1="{wx0+110}" y1="{ax_y}" x2="{wx0+110+ww-160}" y2="{ax_y}" stroke="{INK}" stroke-width="1.2"/>')
for v in (100, 200, 300, 400):
    xx = wx0 + 110 + (ww - 160) * (v - lo_) / (hi_ - lo_)
    ee.append(f'<line x1="{xx:.1f}" y1="{ax_y}" x2="{xx:.1f}" y2="{ax_y+5}" stroke="{INK}" stroke-width="1.2"/>' + t(xx, ax_y + 19, str(v), 12, fill=BODY, anchor="middle"))
ee.append(t(wx0, ax_y + 46, [f"predicted vs reference: differs by > 30 nm", f"at {TWS['abs_diff_gt_30nm_pct']:.0f}% of locations"], 13, fill=INK, lh=17))
add(group("e super-resolution", "".join(ee)))

H = Y5 + R5 + 20
svg = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
       f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" xmlns:xlink="http://www.w3.org/1999/xlink" '
       f'width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">\n'
       f'<defs>{"".join(defs)}</defs>\n<rect width="{W}" height="{H}" fill="#ffffff"/>\n'
       + "\n".join(out) + "\n</svg>\n")
open("fig2.svg", "w", encoding="utf-8").write(svg)
print("written", len(svg) // 1024, "KB; height", H)
