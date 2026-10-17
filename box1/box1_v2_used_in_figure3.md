# Box 1 (v2): code-generation prompt used for the Box 1 rows of Figure 3 (runs of 17 Oct 2026)

Exact text sent for the nuclei task (cancer/endothelial versions differ only in the object, size and file name; see each run's prompt.md). The last line ('My setup: ...') was added by us so the code could run in our environment; it is not part of Box 1.

```text
I want to measure the number and area of the nuclei from single-channel 2D fluorescence (DAPI) images. Write only the segmentation step using a maintained library and its documented API. If possible, check the documentation for the library you plan to use instead of relying on memory. The input is Y, X, pixel size is 0.65 µm per pixel, and nuclei are approximately 13–17 µm across. State consequential parameters, defaults and transformations, including any resizing or normalisation. Return labels in the original coordinate system and include a test that compares the output with a manually annotated example and saves an overlay for inspection. List the assumptions I should check on real data.
My setup: Python with numpy, scipy, scikit-image, tifffile, pandas and Cellpose 4.2.1.1 (CPU only). My image file is dapi.tif.
```
