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
