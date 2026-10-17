Act as a helpful coding assistant for a cell biologist. Do not use any tools (no files, no code execution).

The user writes: "Please write a Python script to segment the endothelial cells in my brightfield image bf.tif using Cellpose (I have Cellpose 4 installed, CPU only). The image is a single-channel 2D brightfield image (Y, X), 16-bit, pixel size 0.65 µm. The endothelial cells are flat, polygonal cells, about 25–50 µm across, forming a confluent monolayer with faint borders; round, refractile cancer cells (15–25 µm) sit on top and must NOT be segmented. Do not resize the image. Save the label image as labels.tif and the endothelial-cell areas in µm² as areas.csv, and print the number of endothelial cells. Available packages: numpy, scipy, scikit-image, tifffile, pandas, cellpose."

Reply with one complete script in a single ```python block and nothing else.
