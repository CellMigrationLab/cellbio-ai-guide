# Answer sheet for follow-up questions (round 2; frozen with the protocol)

Answer **only what the model asks**, quoting the line below verbatim (combine lines if several questions are asked).
If a question is not covered: "I don't know." Never volunteer information, hints, opinions or corrections.
Verified against the data on 17 Oct 2026.

| Topic | Answer |
|---|---|
| Image size / preview | "The image is 1024 × 1022 pixels (width × height). The PNG preview is contrast-scaled to 8-bit for display; the original is uint16." |
| Pixel size | "0.65 µm per pixel, from the metadata." |
| Objective / microscope | "I don't have the objective details to hand; the pixel size is 0.65 µm." |
| Dimensions | "Single 2D plane; no z-stack, no time series." |
| Number of images | "I have this field now; more fields of the same kind will follow, from the same microscope and settings." |
| Other channels / labels | "Only this channel will be available for the analysis. The cancer cells are not fluorescently labelled." |
| Intensity values (DAPI) | "uint16, values 48–4095; 1st, 50th, 99th and 99.8th percentiles 62, 108, 1210 and 1623; 6 pixels at 4095." |
| Intensity values (brightfield) | "uint16, values 151–4009; 1st, 50th and 99th percentiles 2239, 2620 and 2905." |
| Which nuclei | "Only the endothelial nuclei. The nuclei of the cancer cells sitting on top are not of interest. Dividing endothelial nuclei count." |
| Cancer cells: appearance, clusters | "They are mostly rounded and bright with a dark rim; some form small clusters. Touching cells should be counted individually. Area means the projected 2D footprint." |
| Endothelial cells under cancer cells | "Count them as whole cells; their outline follows the cell junctions, including the part under the cancer cell." |
| Cells at the image border | "Cells cut by the image border can be left out of the area statistics." |
| Use of the results | "The counts and areas will be compared between conditions." |
| Software / hardware | As in the prompt; if not stated: "Python 3.13 and a current Fiji, on a laptop without GPU." |
| Can you send the image? | Upload `assets/<task>_image.png` (and say: "The original is the uint16 TIFF I attached" if one was attached). |
| Can you send an annotation / example of the result? | Upload `assets/<task>_annotation_left.png` and say: "This is my manual annotation of the left half of the image (x < 512); I keep the right half to check the result." |
| How many objects are annotated? | "I'd rather not say; please use the annotation to check the analysis." |
| Control image (no cancer cells) | "Not available." |
| Anything else | "I don't know." |
