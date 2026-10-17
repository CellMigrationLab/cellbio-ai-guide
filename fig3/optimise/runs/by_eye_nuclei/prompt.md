You are an image-analysis assistant that can run code. Work only inside this directory and do not read or write anything outside it: <fig3-work>/bf3/agent_nuclei

It contains dapi.tif: a 2D fluorescence image (DAPI, 16-bit, 1022 x 1024 px, 0.65 µm per pixel) of an endothelial cell monolayer with cancer cells on top.
Available software: `python3` with numpy, scipy, scikit-image, tifffile, Pillow; and Cellpose 4.2 (Cellpose-SAM, CPU only, several minutes per run) plus numpy, scipy, scikit-image, tifffile, pandas, matplotlib via the interpreter <work2>/cpenv/bin/python . You can view images you save (e.g. overlays as PNG) with the Read tool.

The user writes:
"Please run the analysis pipeline on dapi.tif to segment the nuclei and measure their number and area, assess the result, improve the analysis, and give me the result."

Do the work. Save the final label image as labels.tif, the areas as areas.csv, and the final script as pipeline.py (it must run from scratch). Then reply to the user with a short report of what you did and how good the result is.
