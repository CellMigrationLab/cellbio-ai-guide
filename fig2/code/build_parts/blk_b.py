# ---------------------------------------------------------------- b: is it good enough? compare with human agreement
Y2 = YO + R1 + GAPR
R2 = 66 + 330 + 14
AG = json.load(open("data/annot_agree.json"))
cc = [frame(28, Y2, 1784, R2, "b", "Is it good enough? Compare the model with how much people agree", "A")]
cc.append(key_item(1812 - 520, Y2 + 42, MODEL, "model") + key_item(1812 - 410, Y2 + 42, REF, "annotator 1", DASH)
          + key_item(1812 - 270, Y2 + 42, REF2, "annotator 2", DASH))
PT = 274
PTH = PT * 280 / 260
cc.append(t(44, Y2 + 88, "Cell outlines, acquired PECAM-1", 15, "bold", INK))
lay = [("data/pecam_annotator1.json", "annotator 1 (vector)", REF, DASH), ("data/pecam_annotator2.json", "annotator 2 (vector)", REF2, DASH)]
if os.path.exists("data/pecam_model.json"):
    lay.append(("data/pecam_model.json", "Cellpose-SAM on acquired PECAM-1 (vector)", MODEL, None))
cc.append(tile(44, Y2 + 100, PT, PTH, "data/pecam_tile.png", lay, "b PECAM outlines", um=PX, imgw=260, bar=50, sub=(0, 0, 260, 280)))
# agreement
ax0 = 44 + PT + 50
cc.append(t(ax0, Y2 + 88, "Agreement, object F1 (IoU ≥ 0.5)", 15, "bold", INK))
rows_ = [("annotator 1 vs annotator 2", AG["pairs"].get("annotator 1 vs annotator 2"), "#8a94a3"),
         ("model vs annotator 1", AG["pairs"].get("annotator 1 vs model"), F1C),
         ("model vs annotator 2", AG["pairs"].get("annotator 2 vs model"), F1C)]
for i, (lbl, v, colr) in enumerate(rows_):
    yy = Y2 + 128 + i * 52
    cc.append(t(ax0, yy, lbl, 14.5, fill=INK))
    if v is None:
        cc.append(t(ax0, yy + 22, "running…", 14, "bold", "#7a8699"))
        continue
    cc.append(f'<rect x="{ax0}" y="{yy+8}" width="320" height="12" rx="3" fill="#e4e8ee"/>'
              f'<rect x="{ax0}" y="{yy+8}" width="{320*v:.1f}" height="12" rx="3" fill="{colr}"/>' + t(ax0 + 330, yy + 20, f"{v:.2f}", 15, "bold", INK))
cc.append(t(ax0, Y2 + 128 + 3 * 52 + 6, ["People disagree too: judge the model against their agreement,", "not against a perfect score."], 14, "bold", "#1f4e8c", lh=18))
# biological result
bx0 = ax0 + 470
cc.append(t(bx0, Y2 + 88, "Biological result (whole field)", 15, "bold", INK))
heads = ["", "cells", "mean area, µm²"]
cols = [bx0, bx0 + 170, bx0 + 290]
for c_, h_ in zip(cols, heads):
    cc.append(t(c_, Y2 + 120, h_, 14, "bold", INK, "start" if c_ == bx0 else "middle"))
for i, k in enumerate(["annotator 1", "annotator 2", "model"]):
    yy = Y2 + 152 + i * 34
    cc.append(t(cols[0], yy, k, 14.5, fill=INK))
    if k not in AG["bio"]:
        cc.append(t(cols[1], yy, "…", 14.5, "bold", "#7a8699", "middle") + t(cols[2], yy, "…", 14.5, "bold", "#7a8699", "middle"))
        continue
    cc.append(t(cols[1], yy, str(AG["bio"][k]["count"]), 14.5, "bold", INK, "middle")
              + t(cols[2], yy, f"{AG['bio'][k]['mean_area_um2']:.0f}", 14.5, "bold", INK, "middle"))
cc.append(t(bx0, Y2 + 152 + 3 * 34 + 10, ["Check whether the model changes the result", "more than the annotators do."], 14, "bold", "#1f4e8c", lh=18))
# which errors matter depends on the measurement
x0, w0 = 1812 - 16 - 470, 470
cc.append(f'<line x1="{x0-16}" y1="{Y2+76}" x2="{x0-16}" y2="{Y2+R2-18}" stroke="{NN["tintstroke"]}" stroke-width="1.2"/>')
cc.append(t(x0, Y2 + 88, "The errors that matter depend on the measurement", 15, "bold", INK))
MEAS = [("Counts", "missed and false objects"), ("Morphology", "boundaries of matched cells"),
        ("Phenotypes", "misclassified objects"), ("Tracks", "merges and splits break links")]
POS = [(x0 + w0 * 0.25, Y2 + 162), (x0 + w0 * 0.75, Y2 + 162), (x0 + w0 * 0.25, Y2 + 312), (x0 + w0 * 0.75, Y2 + 312)]
a = []
exec(open("measure_icons_block.py").read())
cc += a
add(group("b human agreement", "".join(cc)))
