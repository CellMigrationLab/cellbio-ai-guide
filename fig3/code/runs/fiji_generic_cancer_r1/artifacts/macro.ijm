input = "<fig3-work>/bf3/fj_gen_cancer_r1/bf.tif"; output = "<fig3-work>/bf3/fj_gen_cancer_r1/labels.tif";

// ---- Tunable parameters (pixels) ----
varRadius   = 3;     // radius of the local-variance (texture) filter
smoothSigma = 2;     // smoothing of the texture map
minArea     = 150;   // smaller objects (debris) are discarded
maxArea     = 2500;  // larger objects (big clumps/artefacts) are discarded
minCirc     = 0.5;   // minimum circularity (0-1)

setBatchMode(true);
open(input);
origTitle = getTitle();
run("Options...", "iterations=1 count=1 black");

// Work on a copy so the original is untouched
run("Duplicate...", "title=work");
selectWindow("work");
run("8-bit");
run("32-bit");

// Texture map: rims of round cells have strong local contrast, flat background does not
run("Variance...", "radius=" + varRadius);
run("Gaussian Blur...", "sigma=" + smoothSigma);

// Threshold the texture map
setAutoThreshold("Otsu dark no-reset");
run("Convert to Mask");

// Turn rings into solid discs, remove specks, split touching cells
run("Fill Holes");
run("Open");
run("Watershed");

// Size and shape filter, then build the label image (0 = background, 1..N = cells)
run("Analyze Particles...", "size=" + minArea + "-" + maxArea + " pixel circularity=" + minCirc + "-1.00 show=[Count Masks] exclude clear");
labelTitle = getTitle();
selectWindow(labelTitle);

n = getValue("Max");
print("Segmented objects: " + n);

saveAs("Tiff", output);
setBatchMode(false);
