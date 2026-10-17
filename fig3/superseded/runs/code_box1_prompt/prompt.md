Act as a helpful coding assistant for a cell biologist. Do not use any tools: no file reading, no code execution. Reply with code only.

The user writes:
"I want to measure nuclear area from single-channel 2D fluorescence images. Write only the segmentation step using an established, maintained library and its documented API. The input is Y, X, and the pixel size is provided in µm per pixel. Do not silently resize, normalise, change channels or substitute defaults. Expose consequential parameters, fail clearly on invalid input, return the label image in the original coordinate system, and include a simple test. List the assumptions I should verify on real data.
My image is nuclei.tif (DAPI, 16-bit, pixel size 0.65 µm, nuclei about 10-20 µm across, some touching). Save a label image to labels.tif and the nuclear areas in µm² to areas.csv. Available packages: numpy, scipy, scikit-image, tifffile."

Reply with ONE complete Python script in a single ```python code block (put the list of assumptions as comments at the top of the script) and nothing else.
