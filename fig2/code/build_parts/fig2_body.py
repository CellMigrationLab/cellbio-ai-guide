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

# ---------------------------------------------------------------- a: when a pre-trained model fails (full width)
TH_ = 0
xb, wb = 28, 1784
LASTW = 170
NT = 7 - 1
TW = (wb - 28 - LASTW - NT * 12) / NT
TH = TW * SEGH / SEGW
R1 = round(66 + 76 + TH + 62 + 14)
bb = [frame(xb, YO, wb, R1, "a", "When a pre-trained model performs poorly, find the mismatch first", "A")]
bb.append(key_item(xb + wb - 250, YO + 42, MODEL, "model") + key_item(xb + wb - 150, YO + 42, REF, "reference", DASH))
steps = [("Default settings", ["pre-trained generalist,", "no retraining"], "cp_default", PS["default"]),
         ("Object scale", ["input downsampled 4×"], "cp_down4", PS["down4"]),
         ("Object scale", ["input upsampled 2×"], "cp_up2", PS.get("up2")),
         ("Pre-processing", ["normalisation switched off:", "no cells found"], "cp_nonorm", PS["nonorm"]),
         ("Post-processing", ["stricter probability", "threshold"], "cp_cellprob2", PS["cellprob2"]),
         ("Post-processing", ["low-contrast objects", "(endothelium) removed"], "cp_postfilter", PS["postfilter"])]
ty0 = YO + 66 + 76
for i, (ttl, sub, key, v) in enumerate(steps):
    x = xb + 14 + i * (TW + 12)
    bb.append(f'<circle cx="{x+11}" cy="{YO+86}" r="11" fill="{cA["accent"]}"/>' + t(x + 11, YO + 91, str(i + 1), 13, "bold", "#fff", "middle")
              + t(x + 28, YO + 91, ttl, 16, "bold", INK) + t(x, YO + 112, sub, 13.5, fill=BODY, lh=16))
    if v is None:                     # run still in progress: placeholder
        bb.append(rrect(x, ty0, TW, TH, 4, "#e9edf2", "#c8d3e0", 1.2, ' stroke-dasharray="6 4"')
                  + t(x + TW / 2, ty0 + TH / 2, "running…", 15, "bold", "#7a8699", "middle"))
        bb.append(t(x, ty0 + TH + 28, "F1", 13.5, fill=BODY) + t(x, ty0 + TH + 46, "pending", 14, "bold", "#7a8699"))
        continue
    bb.append(tile(x, ty0, TW, TH, "data4/B_rep_bf.png",
                   [("data4/B_rep_ref.json", "reference (vector)", REF, DASH), (f"data/ts_{key}.json", f"{ttl} (vector)", MODEL, None)],
                   f"step {i+1} {ttl}"))
    bb.append(f1bar(x, ty0 + TH + 30, TW - 52, v, "F1"))
# step 7: fine-tune only if needed (schematic)
x5 = xb + 14 + NT * (TW + 12)
bb.append(rrect(x5, YO + 70, LASTW, R1 - 70 - 14, 12, cA["tint"], cA["tintstroke"], 1.3))
bb.append(f'<circle cx="{x5+22}" cy="{YO+92}" r="11" fill="{cA["accent"]}"/>' + t(x5 + 22, YO + 97, str(NT + 1), 13, "bold", "#fff", "middle")
          + t(x5 + 40, YO + 97, "Fine-tune", 16, "bold", INK))
bb.append(t(x5 + LASTW / 2, YO + 128, ["only if a", "systematic failure", "remains"], 14, fill=BODY, anchor="middle", lh=18))
cy5 = ty0 + TH / 2 + 16
bb.append(group("fine-tune loop (schematic)",
                f'<circle cx="{x5+LASTW/2}" cy="{cy5}" r="52" fill="none" stroke="{cA["accent"]}" stroke-width="2.4" stroke-dasharray="6 5"/>'
                + t(x5 + LASTW / 2, cy5 - 64, "correct", 13.5, "bold", INK, "middle")
                + t(x5 + LASTW / 2, cy5 + 76, "retrain", 13.5, "bold", INK, "middle")
                + unet2(x5 + LASTW / 2, cy5, cA["accent"])))
bb.append(t(x5 + LASTW / 2, cy5 + 110, ["add diverse", "examples where", "it fails"], 13, fill=BODY, anchor="middle", lh=16))
add(group("a troubleshooting", "".join(bb)))

# ---------------------------------------------------------------- c: is it good enough?
Y2 = YO + R1 + GAPR
R2 = 66 + 340 + 14
cc = [frame(28, Y2, 1784, R2, "b", "Is it good enough? Check the errors that matter for the measurement", "A")]
# measurement -> error that matters
x0, w0 = 44, 560
cc.append(rrect(x0, Y2 + 66, w0, 340, 12, "#ffffff", cA["innerstroke"]))
cc.append(box_title(x0 + w0 / 2, Y2 + 96, "What will you measure?"))
MEAS = [("Counts", "missed and false objects"), ("Morphology", "boundaries of matched cells"),
        ("Phenotypes", "misclassified objects"), ("Tracks", "merges and splits break links")]
POS = [(x0 + w0 * 0.25, Y2 + 170), (x0 + w0 * 0.75, Y2 + 170), (x0 + w0 * 0.25, Y2 + 320), (x0 + w0 * 0.75, Y2 + 320)]
a = []
CT = 0
exec(open("measure_icons_block.py").read())
cc += a
cc.append(arrow(x0 + w0 + 4, Y2 + 236, x0 + w0 + 22, Y2 + 236, cA["accent"]))
# two tiles with error markers
ES = json.load(open("data/error_summary.json"))
EM = json.load(open("data/err_markers.json"))
x1 = x0 + w0 + 26
w1 = 1796 - x1
cc.append(rrect(x1, Y2 + 66, w1, 340, 12, "#ffffff", cA["innerstroke"]))
ETW = 252
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

# ---------------------------------------------------------------- d: artificial-labelling pipeline
Y3 = Y2 + R2 + GAPR
R3 = 66 + 400 + 14
add(group("d artificial labelling", frame(28, Y3, 740, R3, "c", "Artificial labelling", "B")
          + "".join(image_pipeline(Y3 + 66, "B", None, ("Output", "predicted DAPI + PECAM-1"), "data3/B_predicted_composite.png", 210,
                                   ["pix2pix"], "#ffffff", hc=400))))

# ---------------------------------------------------------------- e: what will you measure?
xe = 28 + 740 + 6
we = 1812 - xe
ee = [frame(xe, Y3, we, R3, "d", "What will you measure from the predicted image?", "B")]
halves = [("ok", "An intermediate step", ["visualise", "segment", "detect", "register"],
           ["Validate the downstream output", "against experimentally labelled samples"]),
          ("caution", "The measurement itself", ["intensity", "abundance", "localisation"],
           ["Compare with acquired fluorescence", "in independent paired samples,", "across the relevant conditions"])]
hw = (we - 28 - 14) / 2
for k_, (kind, ttl, icons, concl) in enumerate(halves):
    hx = xe + 14 + k_ * (hw + 14)
    ee.append(rrect(hx, Y3 + 66, hw, 300, 12, "#ffffff", cB["innerstroke"]))
    yb = Y3 + 110
    if kind == "ok":
        ee.append(check_badge(hx + 30, yb - 5, cB["accent"], 13).replace('stroke-width="4.5"', 'stroke-width="3"')
                  .replace(f'M{hx+20},{yb-4} L{hx+27},{yb+3} L{hx+41},{yb-13}', f'M{hx+24},{yb-5} L{hx+28.5},{yb} L{hx+36},{yb-10}'))
    else:
        ee.append(caution(hx + 30, yb - 7))
    ee.append(t(hx + 52, yb + 1, ttl, 18, "bold", INK))
    n = len(icons)
    for i, nm in enumerate(icons):
        cx = hx + 20 + (hw - 40) * (i + 0.5) / n
        ee.append(group(f"use icon {nm}", f'<g transform="translate({cx} {yb+80}) scale(1.3) translate({-cx} {-(yb+80)})">'
                        + b_icon(nm, cx, yb + 80, cB["accent"]) + "</g>"))
        ee.append(t(cx, yb + 132, nm, 15, fill=INK, anchor="middle"))
    ee.append(f'<line x1="{hx+24}" y1="{yb+158}" x2="{hx+hw-24}" y2="{yb+158}" stroke="{cB["tintstroke"]}" stroke-width="1.4" stroke-dasharray="5 4"/>')
    ee.append(t(hx + hw / 2, yb + 190, concl, 16, "bold", INK, "middle", lh=21))
# reporting rule, under both halves
ry_ = Y3 + 66 + 300 + 12
ee.append(rrect(xe + 14, ry_, we - 28, R3 - (ry_ - Y3) - 14, 12, cB["tint"], cB["tintstroke"], 1.3))
ee.append(f'<rect x="{xe+34}" y="{ry_+24}" width="58" height="40" rx="3" fill="#123"/>' + halo(xe + 63, ry_ + 49, "predicted", "middle", 12))
ee.append(t(xe + 112, ry_ + 38, "In figures and legends, label predicted images as predicted.", 16, "bold", INK)
          + t(xe + 112, ry_ + 60, "Do not describe predicted fluorescence as though the marker had been measured.", 15, fill=BODY))
add(group("e what will you measure", "".join(ee)))

# ---------------------------------------------------------------- f: compare with acquired data
Y4 = Y3 + R3 + GAPR
R4 = 66 + 330 + 14
ff = [frame(28, Y4, 1784, R4, "e", "Is it good enough? Compare with experimental reference data", "B")]
ff.append(key_item(1812 - 470, Y4 + 42, MODEL, "on predicted image") + key_item(1812 - 290, Y4 + 42, REF, "annotator 1", DASH)
          + key_item(1812 - 160, Y4 + 42, REF2, "annotator 2", DASH))
TWf, THf = 220, 297
gw = (1784 - 28 - 2 * 14) / 3
ex = [("Cells", "Cellpose on predicted PECAM-1 vs outlines on acquired PECAM-1", "data3/B_PECAM_acquired.png",
       [("data3/B_annotator1_contours.json", "annotator 1 (vector)", REF, DASH), ("data3/B_annotator2_contours.json", "annotator 2 (vector)", REF2, DASH),
        ("data3/B_cells_contours.json", "Cellpose on predicted PECAM (vector)", MODEL, None)],
       [("between annotators", 0.897, "#8a94a3"), ("vs annotator 1", 0.781, F1C), ("vs annotator 2", 0.746, F1C)], "F1"),
      ("Nuclei", "StarDist on predicted DAPI vs manual nuclei", "data3/B_DAPI_acquired_nuclei_tile.png",
       [("data3/B_nuclei_manual_contours.json", "manual nuclei (vector)", REF, DASH), ("data3/B_nuclei_stardist_contours.json", "StarDist on predicted DAPI (vector)", MODEL, None)],
       [("vs manual nuclei", 0.828, F1C)], "F1"),
      ("Intensity", "predicted vs acquired, per pixel", "data5/split_intensity.png", [],
       [("DAPI", 0.891, RC), ("PECAM-1", 0.243, RC)], "Pearson r")]
for k_, (name, sub_, png, layers, bars_, metric) in enumerate(ex):
    gx = 28 + 14 + k_ * (gw + 14)
    ff.append(rrect(gx, Y4 + 66, gw, 330, 12, "#ffffff", cB["innerstroke"]))
    tx, ty = gx + 16, Y4 + 82
    if name == "Intensity":
        ff.append(split_widget_r(tx, ty, TWf, THf, png, "predicted", "acquired"))
    else:
        g = [real_image(tx, ty, TWf, THf, "data5/dark_tile.png", PX, 100, 20, f"f {name} (outlines only)")]
        for path, lbl, colr, dash in layers:
            g.append(vector_outlines_l(tx, ty, TWf, THf, path, lbl, colr, 1.6, dash))
        ff.append(group(f"f {name}", "".join(g)))
    bx = tx + TWf + 22
    ff.append(t(bx, ty + 22, name, 18, "bold", INK))
    ff.append(t(bx, ty + 44, sub_.split(" vs ")[0] if " vs " in sub_ else sub_, 13.5, fill=BODY))
    if " vs " in sub_:
        ff.append(t(bx, ty + 61, "vs " + sub_.split(" vs ")[1], 13.5, fill=BODY))
    ff.append(t(bx, ty + 100, metric, 14, "bold", INK))
    for i, (lbl, v, colr) in enumerate(bars_):
        ff.append(f1bar(bx, ty + 132 + i * 44, gw - TWf - 16 - 22 - 60, v, lbl, colr))
add(group("f good enough", "".join(ff)))

# ---------------------------------------------------------------- g: denoising and super-resolution
Y5 = Y4 + R4 + GAPR
R5 = 66 + 300 + 14
gg = [frame(28, Y5, 1784, R5, "f", "Denoising and super-resolution: check what the model changed", "B")]
DI = json.load(open("data/dn_intensity.json"))
SP = json.load(open("data/sr_profile.json"))
# g1 denoising
g1x, g1w = 42, 690
gg.append(rrect(g1x, Y5 + 66, g1w, 300, 12, "#ffffff", cB["innerstroke"]))
gg.append(t(g1x + 16, Y5 + 92, "Denoising: mask from the restored image, intensity from the acquired one", 15.5, "bold", INK))
DS = 186
for k_, (png, lbl) in enumerate([("data/dn_restored.png", "restored"), ("data/dn_acquired.png", "acquired")]):
    tx = g1x + 16 + k_ * (DS + 34)
    gg.append(group(f"g denoise {lbl}", real_image(tx, Y5 + 108, DS, DS, png, 0.6337, 200, 20, f"denoise {lbl}")
                    + vector_outlines_sub(tx, Y5 + 108, DS, DS, "data/dn_mask.json", "nuclei from restored image (vector)", MODEL, 1.4, None, (0, 0, 200, 200))
                    + halo(tx + 6, Y5 + 124, lbl)))
    gg.append(t(tx + DS / 2, Y5 + 108 + DS + 22, ["mask from here" if k_ == 0 else "measure here"], 14, "bold", INK, "middle"))
gg.append(arrow(g1x + 16 + DS + 5, Y5 + 108 + DS / 2, g1x + 16 + DS + 29, Y5 + 108 + DS / 2, cB["accent"]))
# scatter: per-nucleus mean intensity, background subtracted
sx0, sy0, sw_, sh2 = g1x + 16 + 2 * (DS + 34) + 34, Y5 + 108, g1w - (16 + 2 * (DS + 34) + 34) - 16, DS
a_ = np.array(DI["acquired"]) - DI["bg_acquired"]
d_ = np.array(DI["restored"]) - DI["bg_restored"]
mx = float(np.percentile(np.r_[a_, d_], 99.5)) * 1.1          # axis to the 99.5th percentile; the few brighter nuclei are clipped
pts = "".join(f'<circle cx="{sx0+sw_*u/mx:.1f}" cy="{sy0+sh2-sh2*v/mx:.1f}" r="2.2" fill="{cB["accent"]}" fill-opacity="0.55"/>'
              for u, v in zip(a_, d_) if 0 < u < mx and 0 < v < mx)
gg.append(group("g denoise intensity scatter",
                f'<line x1="{sx0}" y1="{sy0+sh2}" x2="{sx0+sw_}" y2="{sy0+sh2}" stroke="{INK}" stroke-width="1.4"/>'
                f'<line x1="{sx0}" y1="{sy0}" x2="{sx0}" y2="{sy0+sh2}" stroke="{INK}" stroke-width="1.4"/>'
                f'<line x1="{sx0}" y1="{sy0+sh2}" x2="{sx0+sw_}" y2="{sy0+sh2-sh2*sw_/sw_}" stroke="#8a94a3" stroke-width="1.4" stroke-dasharray="5 4"/>'
                + pts
                + t(sx0 + sw_ / 2, sy0 + sh2 + 22, "acquired intensity", 13.5, fill=BODY, anchor="middle")
                + f'<text x="{sx0-12}" y="{sy0+sh2/2}" font-size="13.5" fill="{BODY}" text-anchor="middle" transform="rotate(-90 {sx0-12} {sy0+sh2/2})">restored intensity</text>'
                + t(sx0 + sw_, sy0 + sh2 - 66, f"r = {DI['r']:.2f}", 14, "bold", INK, "end")
                + t(sx0 + sw_, sy0 + sh2 - 46, f"×{DI['ratio_median']:.2f} vs acquired", 14, "bold", INK, "end")
                + t(sx0 + sw_, sy0 + sh2 - 28, "median ratio, background-", 12, fill=BODY, anchor="end")
                + t(sx0 + sw_, sy0 + sh2 - 14, "subtracted", 12, fill=BODY, anchor="end")
                + t(sx0 + sw_ - 14, sy0 + 14, "y = x", 12.5, fill="#6b7686", anchor="end")))
# g2 super-resolution
SQ = json.load(open("data/squirrel.json"))
g2x = g1x + g1w + 14
g2w = 1798 - g2x
gg.append(rrect(g2x, Y5 + 66, g2w, 300, 12, "#ffffff", cB["innerstroke"]))
gg.append(t(g2x + 16, Y5 + 92, "Super-resolution: check against the diffraction-limited input and, where possible, higher-resolution data", 15.5, "bold", INK))
SS = 162
rowy = SP["row"] / 140
tiles_ = [("data/sr_input.png", "low-res input", True), ("data/sr_predicted.png", "predicted", True),
          ("data/sr_squirrel.png", "SQUIRREL error map", False), ("data/sr_hr.png", "acquired high-res", True)]
for k_, (png, lbl, line) in enumerate(tiles_):
    tx = g2x + 16 + k_ * (SS + 10) + (12 if k_ == 3 else 0)
    gg.append(group(f"g sr {lbl}", real_image(tx, Y5 + 108, SS, SS, png, 0.0626, 140, 2, f"sr {lbl}")
                    + (f'<line x1="{tx}" y1="{Y5+108+SS*rowy:.1f}" x2="{tx+SS}" y2="{Y5+108+SS*rowy:.1f}" stroke="#ffd23f" stroke-width="1.6" stroke-dasharray="4 3"/>' if line else "")))
    gg.append(t(tx + SS / 2, Y5 + 108 + SS + 20, lbl, 14, "bold", INK, "middle"))
mx_ = g2x + 16 + 2 * (SS + 10)
gg.append(t(mx_ + SS / 2, Y5 + 108 + SS + 42, f"RSP vs input: predicted {SQ['predicted']['RSP']:.2f}", 13, fill=INK, anchor="middle")
          + t(mx_ + SS / 2, Y5 + 108 + SS + 60, f"acquired high-res {SQ['high_res']['RSP']:.2f}", 13, fill=INK, anchor="middle"))
gg.append(f'<line x1="{mx_+SS+11}" y1="{Y5+104}" x2="{mx_+SS+11}" y2="{Y5+108+SS+64}" stroke="{cB["tintstroke"]}" stroke-width="1.4" stroke-dasharray="5 4"/>')
px0, py0 = g2x + 16 + 4 * (SS + 10) + 12 + 22, Y5 + 116
pw_, ph_ = g2x + g2w - 20 - px0, 152
gg.append(f'<line x1="{px0}" y1="{py0+ph_}" x2="{px0+pw_}" y2="{py0+ph_}" stroke="{INK}" stroke-width="1.4"/>')
for key, colr, sw, dash in [("low_res", "#9aa4b2", 1.8, "4 3"), ("high_res", INK, 2.0, None), ("predicted", MODEL, 2.0, None)]:
    v = SP[key]
    pl = " ".join(f"{px0+pw_*i/(len(v)-1):.1f},{py0+ph_-ph_*q:.1f}" for i, q in enumerate(v))
    gg.append(f'<polyline points="{pl}" fill="none" stroke="{colr}" stroke-width="{sw}"' + (f' stroke-dasharray="{dash}"' if dash else "") + "/>")
gg.append(t(px0 + pw_ / 2, py0 + ph_ + 20, "intensity along the dashed line", 13, fill=BODY, anchor="middle"))
gg.append(key_item(px0, py0 + ph_ + 48, INK, "high-res") + key_item(px0 + 96, py0 + ph_ + 48, MODEL, "predicted")
          + key_item(px0 + 206, py0 + ph_ + 48, "#9aa4b2", "low-res", "4 3"))
add(group("g denoising and super-resolution", "".join(gg)))

H = Y5 + R5 + 20
svg = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
       f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" xmlns:xlink="http://www.w3.org/1999/xlink" '
       f'width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">\n'
       f'<defs>{"".join(defs)}</defs>\n<rect width="{W}" height="{H}" fill="#ffffff"/>\n'
       + "\n".join(out) + "\n</svg>\n")
open("fig2.svg", "w", encoding="utf-8").write(svg)
print("written", len(svg) // 1024, "KB; height", H)
