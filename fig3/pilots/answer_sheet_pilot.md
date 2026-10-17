# Fixed answers given when a model asks (same facts for every run; only the questions asked are answered)
- Field size / preview: the preview is the full field (1024 x 1022 px), contrast-scaled to 8-bit for display.
- Pixel size: 0.65 µm per pixel, from the metadata (correct). Objective details not to hand.
- Dimensionality: single 2D plane per field, no z-stack, no time series.
- Number of images: one field annotated now; more fields of the same kind will follow (same microscope and settings).
- Imaging: same microscope and settings for all fields; plain brightfield (or widefield DAPI).
- Extra channels (brightfield tasks): none available for the analysis; cancer cells are not fluorescently labelled. (Endothelial annotation was drawn using a PECAM-1 junction stain of the same field.)
- Nuclei: only endothelial nuclei are wanted; nuclei of the cancer cells sitting on top are not annotated. Dividing endothelial nuclei count.
- Cancer cells: mostly rounded, bright with a dark rim; some small clusters; count touching cells individually; area = projected 2D footprint.
- Endothelial cells partly covered by a cancer cell: label the visible part, do not exclude.
- Border: cells touching the image border are not annotated (endothelial) / may be excluded from area statistics.
- Annotation content: label image of the target objects only, 0 elsewhere (nuclei: 441; cancer: 124; endothelial: 382 complete cells).
- Control (endothelium-only) image: not available.
- Software preference: Python is fine; Fiji also available. Density: confluent; nuclei mostly separate, some touching.
- Image/annotation requested: preview PNGs supplied (assets/), viewable with Read.

## Correction (recorded)
- My first answer "label the visible part of endothelial cells under cancer cells" was wrong: the annotation follows PECAM-1 junctions and runs under the cancer cells. The Box 1 advice run for endothelial cells spotted the inconsistency in turn 2; corrected in turn 3. The code pilot (pb3_endo) received the uncorrected answer.
- Raw DAPI stats given on request: 48–4095, percentiles 1/50/99/99.8 = 62/108/1210/1623, 6 px at 4095.
