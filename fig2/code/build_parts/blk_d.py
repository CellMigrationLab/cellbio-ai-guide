# ---------------------------------------------------------------- d: denoising
XD = 28 + WCC + 6
WDN = 1812 - XD
gg = [frame(XD, Y3, WDN, R3, "c", "Denoising: measure intensity in the acquired image", "B")]
DI = json.load(open("data/dn_intensity.json"))
DS = 250
for k_, (png, lbl, cap) in enumerate([("data/dn_restored.png", "restored", "mask from here"), ("data/dn_acquired.png", "acquired", "measure here")]):
    tx = XD + 16 + k_ * (DS + 34)
    gg.append(group(f"c denoise {lbl}", real_image(tx, Y3 + 78, DS, DS, png, 0.6337, 200, 20, f"denoise {lbl}")
                    + vector_outlines_sub(tx, Y3 + 78, DS, DS, "data/dn_mask.json", "nuclei from restored image (vector)", MODEL, 1.4, None, (0, 0, 200, 200))
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

