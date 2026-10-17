# Answer sheet, protocol v2 (answers to the subject's follow-up questions)

Answer **only what is asked**, quoting the line below verbatim (combine lines if several questions are asked); at most 3
replies, then "Thanks, that is all I need." Only explicit questions are answered (a sentence ending in "?", or a list
headed as questions); a conditional offer ("If you tell me X, I can ...") gets no reply. If a question is not covered: "I don't know." Never volunteer information,
hints, opinions or corrections. Record in `meta.json` which lines were used (`answers_given`), in particular the hints.

| Topic | Answer |
|---|---|
| Image size (rows B, C, D) | "The image is 1024 × 1022 pixels (width × height), uint16." |
| Image size (row A) | "My images are 1024 × 1022 pixels (width × height), uint16." |
| Pixel size | "0.65 µm per pixel, from the metadata." |
| Objective / microscope | "I don't have the objective details to hand; the pixel size is 0.65 µm." |
| Dimensions | "Single 2D plane; no z-stack, no time series." |
| Number of images | "I have more fields of the same kind, from the same microscope and settings." |
| Other channels / labels | "Only this channel will be available for the analysis. The cancer cells are not fluorescently labelled." |
| **Hint, cancer cells** | "They are rounded and sit on top of the endothelial monolayer; touching cells should be counted individually." |
| **Hint, endothelial nuclei** | "Only the endothelial nuclei. The nuclei of the cancer cells are brighter and rounder in DAPI." |
| **Hint, endothelial cells** | "Count them as whole cells; their outline follows the cell junctions, including the part under the cancer cells." |
| Cells at the image border | "Cells cut by the image border can be left out of the area and shape statistics." |
| Aspect ratio definition | "Major axis divided by minor axis of the fitted ellipse." |
| Use of the results | "The counts, areas and aspect ratios will be compared between conditions." |
| Software / hardware | As in the prompt; if not stated: "Python 3.13 on a laptop without GPU." |
| Intensity values | Field 104: "uint16; DAPI 48–4095 (1st/50th/99th percentile 62/108/1210); brightfield 151–4009 (2239/2620/2905)." Field 209 (row D only): "uint16; DAPI 51–4095 (80/182/1915); brightfield 1574–4095 (2591/3113/3550)." |
| **Image / annotation request** | Row B **before any code has been given**: put the field-104 files in the subject folder (`image.tif`, `image.png`; annotation as `annotation.png` and `annotation.tif`) and say: "I added the image and my manual annotation of this image to your folder. I will check the final analysis on other images." Row B after code: "I don't know." Row C labels arm: "The annotation is annotation.tif in your folder." Row C by-eye arm: "I'd rather you judge the result from the image." Row A: "I don't have an example image to share in this conversation." Row D: "I'd rather you work from the image." |
| How many objects are annotated? | Row B (before code) and row C labels arm: field 104 counts (124 cancer cells, 441 nuclei, 382 endothelial cells). Rows A, D and row C by-eye arm: "I'd rather not say." |
| Control image (no cancer cells) | "Not available." |
| Anything else | "I don't know." |

The field-209 annotation is never given to a subject in any row.
