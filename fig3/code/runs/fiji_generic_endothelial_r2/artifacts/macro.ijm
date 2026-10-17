input = "<fig3-work>/bf3/fj_gen_endo_r2/bf.tif"; output = "<fig3-work>/bf3/fj_gen_endo_r2/labels.tif";

// ---- Parameters to tune (pixels) ----
flatSigma    = 50;   // background flattening (larger than a cell)
seedSigma    = 8;    // smoothing for finding one seed per endothelial cell (~1/4 cell diameter)
prominence   = 1.5;  // seed sensitivity; lower = more (smaller) cells, higher = fewer (merged) cells
cellsLight   = false;// true if the cell centres (nuclei) look brighter than their surroundings
texRadius    = 3;    // radius of local-variance filter used to detect round cells / debris
texK         = 1.0;  // exclusion threshold = mean + texK * SD of local variance (lower = exclude more)
excludeGrow  = 4;    // dilation (iterations) of the excluded round cells / debris
minArea      = 400;  // smallest object kept (px^2)

setBatchMode(true);
run("Options...", "iterations=1 count=1 black");
open(input);
src = getTitle();
run("Duplicate...", "title=work");
run("32-bit");

// 1. Flatten uneven illumination
run("Duplicate...", "title=bg");
run("Gaussian Blur...", "sigma=" + flatSigma);
imageCalculator("Subtract 32-bit", "work", "bg");
selectWindow("bg"); close();

// 2. Mask out round bright cells and debris (strong local texture / edges)
selectWindow("work");
run("Duplicate...", "title=tex");
run("Variance...", "radius=" + texRadius);
getStatistics(area, mean, min, max, sd);
setThreshold(mean + texK * sd, 1e30);
run("Convert to Mask");
run("Close-");
run("Fill Holes");
for (i = 0; i < excludeGrow; i++) run("Dilate");
run("Fill Holes");
rename("excluded");

// 3. One seed per endothelial cell, then watershed into cell territories
selectWindow("work");
run("Gaussian Blur...", "sigma=" + seedSigma);
opt = "prominence=" + prominence + " output=[Segmented Particles]";
if (cellsLight) opt = opt + " light";
run("Find Maxima...", opt);
rename("territories");
setThreshold(255, 255);
run("Convert to Mask");

// 4. Keep only territories outside the excluded round cells / debris
selectWindow("excluded");
run("Invert");
imageCalculator("AND create", "territories", "excluded");
rename("cells");

// 5. Label image: one integer per object, 0 = background
selectWindow("cells");
setThreshold(255, 255);
run("Analyze Particles...", "size=" + minArea + "-Infinity show=[Count Masks] clear");
rename("labels");
saveAs("Tiff", output);

setBatchMode(false);
