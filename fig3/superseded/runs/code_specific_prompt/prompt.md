Act as a helpful coding assistant for a cell biologist. Do not use any tools (no files, no code execution).

The user writes: "Please write a Python script to segment the nuclei in nuclei.tif using Cellpose (I have Cellpose 4 installed, CPU only). The image is a single-channel 2D DAPI image (Y, X), 16-bit, pixel size 0.65 µm; nuclei are about 10–20 µm across and some touch. Do not resize or normalise the image yourself. Save the label image as labels.tif and the nuclear areas in µm² as areas.csv, and print the number of nuclei."

Reply with one complete script in a single ```python block and nothing else.
