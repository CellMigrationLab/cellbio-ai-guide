# Fixed answers to follow-up questions (answer only what is asked)
- Preview/field: the image is the full field, 1024 x 1022 px (the PNG is contrast-scaled to 8-bit for display).
- Pixel size: 0.65 µm per pixel, from the metadata. Objective: not to hand.
- Dimensionality: single 2D plane per field; no z-stack, no time series.
- Number of images: one field annotated now; more fields of the same kind will follow (same microscope and settings).
- Imaging: same microscope and settings for all fields; widefield DAPI / plain brightfield.
- Raw intensities (DAPI): uint16, 48–4095; percentiles 1/50/99/99.8 = 62/108/1210/1623; 6 pixels at 4095.
  (Brightfield: uint16, 151–4009; percentiles 1/50/99 = 2239/2620/2905.)
- Other channels: only this channel will be available for the analysis; cancer cells are not fluorescently labelled.
  The endothelial annotation was drawn using a PECAM-1 junction stain of this field (not available for other fields).
- Nuclei: only endothelial nuclei are wanted (cancer-cell nuclei sitting on top are not annotated); dividing endothelial nuclei count.
- Cancer cells: mostly rounded, bright with a dark rim; some small clusters; count touching cells individually; area = projected 2D footprint.
- Endothelial cells under cancer cells: the annotation follows the junctions and runs under the cancer cells (full cell, not only the visible part).
- Border: endothelial cells touching the image border are not annotated; border objects can be excluded from area statistics.
- Annotation counts: 441 endothelial nuclei; 124 cancer cells; 382 complete endothelial cells.
- Control (endothelium-only) image: not available.
- Software: Python is fine; Fiji is also available. Hardware: laptop, no GPU.
- Use of the result: counts and areas will be compared between conditions.
- Anything else: "I don't know" / "not available".
