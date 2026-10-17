Act as a helpful coding assistant for a cell biologist. You cannot run code. You may use the Read tool ONLY to view the image the user attached: <fig3-work>/bf3/py_box1_nuclei_r2/dapi_preview.png (a preview of their file dapi.tif). You may use WebSearch and WebFetch. Do not open any other file.

The user writes:
"I want to measure the number and area of the nuclei from single-channel 2D fluorescence (DAPI) images. Write only the segmentation step using a maintained library and its documented API. If possible, check the documentation for the library you plan to use instead of relying on memory. The input is Y, X, pixel size is 0.65 µm per pixel, and nuclei are approximately 13–17 µm across. State consequential parameters, defaults and transformations, including any resizing or normalisation. Return labels in the original coordinate system and include a test that compares the output with a manually annotated example and saves an overlay for inspection. List the assumptions I should check on real data.
My setup: Python with numpy, scipy, scikit-image, tifffile, pandas and Cellpose 4.2.1.1 (CPU only). My image file is dapi.tif."

Reply as you normally would. Put the segmentation script in ONE complete ```python block that reads dapi.tif and saves the label image as labels.tif; put the test in a SECOND ```python block.
