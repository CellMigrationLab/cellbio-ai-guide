You are an image-analysis assistant that can run code. Work only inside this directory and do not read or write anything outside it: <fig3-work>/bf3/ref_cancer

It contains (read-only):
- bf_dev.tif: a 2D brightfield image (16-bit, 1022 x 512 px, 0.65 µm per pixel) of cancer cells sitting on top of an endothelial cell monolayer. This is the development part of the user's data.
- annot_dev.tif: the user's manual annotation of the cancer cells in bf_dev.tif (label image, same size; 0 = background, one integer per cell).
Available software: `python3` with numpy, scipy, scikit-image, tifffile, Pillow; and Cellpose 4.2 (Cellpose-SAM, CPU only, several minutes per run) plus numpy, scipy, scikit-image, tifffile, pandas, matplotlib via the interpreter <work2>/cpenv/bin/python . You can view images you save (e.g. overlays as PNG) with the Read tool.

The user writes:
"Please build and optimise an analysis pipeline to segment the cancer cells and measure their number and area. Score every version against my annotation (object F1 at IoU >= 0.5, one-to-one matching) and keep a log of each change and its score. Other images are held out for a final check that you will not see, so the pipeline must run unchanged on a new image of the same kind. When you are done, give me the final pipeline and report its score."

Do the work. Save the final script as pipeline.py; it must run from scratch as `python pipeline.py <input.tif> <output_labels.tif>` (no cached results). Save your log as log.txt. Then reply with a short report: what you did, each version's score, and the final score.
