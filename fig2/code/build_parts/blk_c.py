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
