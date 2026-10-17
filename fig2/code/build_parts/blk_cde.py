# ---------------------------------------------------------------- c: denoising   |   d: artificial labelling
Y3 = Y2 + R2 + GAPR
R3 = 66 + 380 + 14
WC = 640
xd = 28 + WC + 6
WD = 1812 - xd
gg = [frame(28, Y3, WC, R3, "c", "Denoising", "B")]
DI = json.load(open("panels/dn_intensity.json"))
gg.append(t(44, Y3 + 92, ["Derive the mask from the restored image;", "measure intensity in the acquired image"], 15.5, "bold", INK, lh=19))
DS = 196
for k_, (png, lbl, cap) in enumerate([("panels/dn_restored.png", "restored", "mask from here"), ("panels/dn_acquired.png", "acquired", "measure here")]):
    tx = 44 + k_ * (DS + 32)
    gg.append(group(f"c denoise {lbl}", real_image(tx, Y3 + 128, DS, DS, png, 0.6337, 200, 20, f"denoise {lbl}")
                    + vector_outlines_sub(tx, Y3 + 128, DS, DS, "panels/dn_mask.json", "nuclei from restored image (vector)", MODEL, 1.4, None, (0, 0, 200, 200))
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
for k_, (png, lbl, sub) in enumerate([("panels/al_bf.png", "brightfield", "input"), ("panels/al_pred.png", "predicted", "pix2pix: DAPI + PECAM-1")]):
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
            ("Intensity", "from_fig1_panel_a/split_intensity.png", None, "Pearson r, per pixel", [("DAPI", 0.891, RC), ("PECAM-1", 0.243, RC)])])]
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
            g = [real_image(tx, ty, TWd, THd, "from_fig1_panel_a/dark_tile.png", PX, 100, 20, f"d {name} (outlines only)")]
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
SP = json.load(open("panels/sr_profile.json"))
SQ = json.load(open("panels/squirrel.json"))
TWS = json.load(open("panels/tubule_width.json"))["summary"]
SS = 186
rowy = SP["row"] / 140
ee.append(rrect(42, Y5 + 66, 3 * (SS + 10) + 22, 290, 12, "#ffffff", cB["innerstroke"]))
ee.append(t(58, Y5 + 90, "Consistency with the diffraction-limited input (SQUIRREL)", 14.5, "bold", INK))
tiles_ = [("panels/sr_input.png", "low-res input", True), ("panels/sr_predicted.png", "predicted", True), ("panels/sr_squirrel.png", "error map", False)]
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
ee.append(group("e sr reference", real_image(tx, Y5 + 104, SS, SS, "panels/sr_hr.png", 0.0313, 140, 1, "sr reference")
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
