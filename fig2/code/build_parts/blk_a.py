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
