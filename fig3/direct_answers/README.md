# Row d: ask for the answer directly

`runs/count_*`: "How many … are in this image?" (answer ends with a JSON count). `runs/draw_*`: "Please draw around every
… and count them." (polygons as JSON, rasterised by `code/rasterise_poly.py` into `artifacts/labels.tif`). The model saw
the full field as a PNG and could not run code. `source/` holds the scores and stated counts used by the figure.
