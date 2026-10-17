# Figure 3 round 1: asking for the answer directly

This folder records the **round-1 draft** experiment in which an LLM viewed a full-field PNG and answered without running code. The revised study is in [protocol v2](../PROTOCOL_V2.md).

Two requests were tested:

- `runs/count_*`: ask how many objects are in the image; the reply includes a JSON count.
- `runs/draw_*`: ask the model to outline every object and count them. The JSON polygons were converted to a label image by [rasterise_poly.py](code/rasterise_poly.py).

The [source folder](source/) contains the stated counts and scores used for the draft figure. The rasterised outlines are derived from the LLM's coordinates; they are not manually corrected annotations.
