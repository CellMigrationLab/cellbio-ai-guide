Act as a helpful assistant for a cell biologist. You cannot run code. You may use the Read tool ONLY to view the image the user attached: <fig3-work>/bf3/fj_gen_endo_r2/bf_preview.png (a preview of their file bf.tif). Do not open anything else.

The user writes: "Please write a Fiji macro to segment the endothelial cells in my brightfield image." (attached: bf.tif)

Reply as you normally would. Put the macro in ONE complete ```ijm block. Begin it with these two lines, which the user will edit: input = "bf.tif"; output = "labels.tif"; The macro must open input and save a label image of the segmented objects (0 = background, one integer per object) to output.
