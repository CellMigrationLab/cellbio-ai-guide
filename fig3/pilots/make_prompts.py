"""Fill the user's Box 1 draft (v3, verbatim) for the three tasks; write box3/<task>.txt and ../../figure3/box1_v3_filled.md."""
BOX = """I want to {q} from {imgs}. Help me write the analysis.
My images are 2D, with axes Y, X, channels {ch}, data type uint16 (12-bit values), pixel/voxel size 0.65 µm, and objects of interest approximately {size} in size. The output I need is {out}. I can provide a manually annotated example (a label image of one field).
Please:

* Clarify the task. Ask for missing information only when it could materially affect the analysis. If useful, ask me for representative images or examples of the expected result.
* Use appropriate methods. Prefer established, maintained software and documented APIs. Check current documentation rather than relying only on memory. If consequential behaviour remains unclear, inspect the source code when available rather than guessing.
* Check deep learning model suitability. If using a pre-trained model, consider whether my images match its training data, including image type, channels, dimensionality, object scale, preprocessing and post-processing.
* Write code according to best practices. Keep functions small and focused, use clear names and annotations, and separate consequential processing steps. Validate inputs, provide informative errors and do not use silent fallbacks.
* Make processing explicit. State important parameters, defaults and transformations, including resizing, resampling, normalisation, channel selection and post-processing. Preserve the original coordinate system and physical units unless a transformation is explicitly required and documented.
* Make the analysis testable. Test it on representative reference data where possible, save useful intermediate outputs and overlays, and use validation measures appropriate to the intended biological measurement rather than relying on a single generic score.
* Audit and challenge the result. Before finishing, assume that the analysis could be scientifically wrong even if the code runs and the output looks plausible. Identify the failure modes most likely to change the biological conclusion and suggest concrete tests or reference data that would expose them."""
T = {
 'nuclei': dict(q='count the endothelial nuclei and measure their area',
   imgs='widefield fluorescence images of a DAPI-stained endothelial monolayer', ch='1 (DAPI)', size='13–17 µm',
   out='a label image with one integer per nucleus (0 = background) and a table of nuclear areas in µm²'),
 'cancer': dict(q='count the cancer cells attached to an endothelial monolayer and measure their area',
   imgs='brightfield images of cancer cells sitting on top of a confluent endothelial monolayer', ch='1 (brightfield)', size='15–25 µm',
   out='a label image with one integer per cancer cell (0 = background; the endothelial cells underneath should not be labelled) and a table of cancer-cell areas in µm²'),
 'endo': dict(q='count the endothelial cells and measure their area',
   imgs='brightfield images of a confluent endothelial monolayer (some cancer cells sit on top)', ch='1 (brightfield)', size='25–50 µm',
   out='a label image with one integer per endothelial cell (0 = background) and a table of endothelial-cell areas in µm²'),
}
md = ['# Box 1 (draft v3) filled in for the three Figure 3 tasks\n']
for k, v in T.items():
    s = BOX.format(**v); open(f'box3/{k}.txt', 'w').write(s)
    md += [f'## {k}\n', '```text', s, '```\n']
open('../../figure3/box1_v3_filled.md', 'w').write('\n'.join(md))
