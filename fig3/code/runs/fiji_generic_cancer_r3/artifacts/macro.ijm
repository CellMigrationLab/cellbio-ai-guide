input = "<fig3-work>/bf3/fj_gen_cancer_r3/bf.tif"; output = "<fig3-work>/bf3/fj_gen_cancer_r3/labels.tif";

// ---- Parameters to tune (all in pixels) ----
varRadius   = 2;     // local variance radius (edge/texture detection)
smoothSigma = 2;     // smoothing of the texture map
minArea     = 200;   // removes debris / small specks
maxArea     = 5000;  // removes very large clumps / artefacts
minCirc     = 0.5;   // removes irregular debris (0-1)

setBatchMode(true);
setOption("BlackBackground", true);
run("Clear Results");

open(input);
origTitle = getTitle();
run("Set Scaling...", "distance=0 known=0 unit=pixel");  // measure sizes in pixels
if (nSlices > 1) run("Z Project...", "projection=[Max Intensity]");
run("32-bit");
run("Select None");
work = getImageID();

// Texture map: round cells have a strong dark rim and bright halo,
// whereas the flat monolayer has low local variance.
run("Variance...", "radius=" + varRadius);
run("Gaussian Blur...", "sigma=" + smoothSigma);

// Threshold the texture map (try "Otsu dark" or "Li dark" if Triangle is off)
setAutoThreshold("Triangle dark");
run("Convert to Mask");

// Clean up: join rims, fill the cell interiors, remove specks, split touching cells
run("Close-");
run("Fill Holes");
run("Open");
run("Watershed");

// Label image: one integer per object, 0 = background
run("Analyze Particles...", "size=" + minArea + "-" + maxArea +
    " circularity=" + minCirc + "-1.00 show=[Count Masks] exclude clear");
labels = getImageID();
selectImage(labels);
run("Select None");
getStatistics(area, mean, min, max);
print("Segmented objects: " + max);

saveAs("Tiff", output);

setBatchMode(false);
