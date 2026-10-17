Act as a helpful coding assistant for a cell biologist. Do not use any tools (no files, no code execution).

The user writes: "Please write a Python script to segment the cancer cells in my brightfield image bf.tif using Cellpose (I have Cellpose 4 installed, CPU only). The image is a single-channel 2D brightfield image (Y, X), 16-bit, pixel size 0.65 µm. The cancer cells are round, refractile cells, about 15–25 µm across, sitting on top of a flat, confluent endothelial monolayer; the endothelial cells must NOT be segmented. Do not resize the image. Save the label image as labels.tif and the cancer-cell areas in µm² as areas.csv, and print the number of cancer cells. Available packages: numpy, scipy, scikit-image, tifffile, pandas, cellpose."

Reply with one complete script in a single ```python block and nothing else.
