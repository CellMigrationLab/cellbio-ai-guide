import csv, json, math
rows = list(csv.reader(open("model/Quality Control/predicted_bounding_boxes_for_custom_ROI_QC.csv")))
names = rows[0][1:]
data = {r[0]: r[1:] for r in rows[1:]}
out = {}
for c, n in enumerate(names):
    boxes = []
    k = 0
    while True:
        suf = "" if k == 0 else f".{k}"
        if "xmin" + suf not in data:
            break
        v = [data[f + suf][c] for f in ("xmin", "ymin", "xmax", "ymax", "confidence", "class")]
        if all(x not in ("", "nan") for x in v):
            boxes.append([float(v[0]), float(v[1]), float(v[2]), float(v[3]), float(v[4]), int(float(v[5]))])
        k += 1
    out[n] = boxes
json.dump(out, open("yolo_pred.json", "w"))
for n, b in out.items():
    cls = [x[5] for x in b]
    print(n, len(b), "rod", cls.count(0), "div", cls.count(1), "micro", cls.count(2))
