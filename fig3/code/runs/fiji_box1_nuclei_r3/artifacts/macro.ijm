input = "<fig3-work>/bf3/fj_box1_nuclei_r3/dapi.tif"; output = "<fig3-work>/bf3/fj_box1_nuclei_r3/labels.tif";

// ---- parameters (pixels unless stated) ----
pixelSizeUm  = 0.65;   // um per pixel (documented by you)
sigmaPx      = 2;      // Gaussian blur, about 1.3 um
rollingPx    = 50;     // Subtract Background radius, > nucleus radius (~13 px)
thrMethod    = "Li";   // global threshold on the background-subtracted image
minAreaPx    = 100;    // ~0.3x of 20 px diameter circle area (314 px^2)
maxAreaPx    = 1200;   // ~2.2x of 26 px diameter circle area (537 px^2)

setBatchMode(true);
open(input);
origTitle = getTitle();
getDimensions(w, h, ch, sl, fr);
if (ch > 1 || sl > 1 || fr > 1) exit("Expected a single 2D (Y,X) image, got " + ch + "c " + sl + "z " + fr + "t");
getVoxelSize(vx, vy, vz, unit);   // keep original calibration for the output

// Work on a copy; original is untouched. No resizing, no normalisation.
run("Duplicate...", "title=work");
run("Set Scale...", "distance=0 known=0 unit=pixel");   // remove scale -> all sizes in pixels
run("32-bit");
run("Gaussian Blur...", "sigma=" + sigmaPx);
run("Subtract Background...", "rolling=" + rollingPx);

setOption("BlackBackground", true);
setAutoThreshold(thrMethod + " dark");
run("Convert to Mask");
run("Fill Holes");
run("Watershed");

// Label image: one integer per particle (16-bit), same size as input
run("Analyze Particles...", "size=" + minAreaPx + "-" + maxAreaPx + " show=[Count Masks] clear");
labelTitle = getTitle();   // "Count Masks of work"
if (labelTitle == "work") exit("No particles found; check the threshold.");
run("Grays");
setVoxelSize(vx, vy, vz, unit);   // restore calibration on the labels
saveAs("Tiff", output);

getStatistics(a, m, mn, mx);
print("Segmented " + mx + " nuclei -> " + output);
setBatchMode(false);
