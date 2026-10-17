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
