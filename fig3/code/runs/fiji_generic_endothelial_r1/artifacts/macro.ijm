input = "<fig3-work>/bf3/fj_gen_endo_r1/bf.tif"; output = "<fig3-work>/bf3/fj_gen_endo_r1/labels.tif";

// ---- Parameters to tune ----
bgSigma    = 50;   // px, background flattening (larger than a cell)
varRadius  = 3;    // px, local-variance window for round cells/debris
varK       = 2.0;  // lower = more masked as round cells/debris
maskGrow   = 4;    // px, dilation of the round cell/debris mask
seedSigma  = 8;    // px, smoothing for seeds (about 1/5 of a cell diameter)
seedProm   = 0.5;  // seed prominence, in units of image std (lower = more cells)
minArea    = 400;  // px^2, smallest object kept

setBatchMode(true);
setOption("BlackBackground", true);
open(input);
orig = getTitle();
run("Duplicate...", "title=flat");
run("32-bit");
run("Duplicate...", "title=bg");
run("Gaussian Blur...", "sigma=" + bgSigma);
imageCalculator("Subtract", "flat", "bg");
close("bg");
selectImage("flat");
getStatistics(area, fmean, fmin, fmax, fstd);

// 1. Mask of round cells and debris (high local variance)
run("Duplicate...", "title=mask");
run("Variance...", "radius=" + varRadius);
getStatistics(area, vmean, vmin, vmax, vstd);
setThreshold(vmean + varK * vstd, vmax);
run("Convert to Mask");
for (i = 0; i < maskGrow; i++) run("Dilate");
run("Fill Holes");

// 2. Seeds from the smoothed monolayer, with the masked areas flattened out
selectImage("flat");
run("Duplicate...", "title=smooth");
selectImage("mask");
run("Create Selection");
selectImage("smooth");
run("Restore Selection");
setColor(fmean);
run("Fill", "slice");
run("Select None");
run("Gaussian Blur...", "sigma=" + seedSigma);

// Watershed regions around each seed. For dark nuclei, add the word "light" after "prominence=...".
run("Find Maxima...", "prominence=" + (seedProm * fstd) + " output=[Segmented Particles]");
rename("regions");

// 3. Keep only monolayer (remove round cells/debris), then label
imageCalculator("Subtract create", "regions", "mask");
rename("endo");
run("Analyze Particles...", "size=" + minArea + "-Infinity show=[Count Masks] display clear");
rename("labels");
saveAs("Tiff", output);
close("*");
setBatchMode(false);
