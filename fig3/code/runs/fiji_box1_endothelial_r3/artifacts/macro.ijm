input = "<fig3-work>/bf3/fj_box1_endo_r3/bf.tif"; output = "<fig3-work>/bf3/fj_box1_endo_r3/labels.tif";

// ---- Parameters (all physical units in um; converted to pixels below) ----
pxSize      = 0.65;   // um/pixel, forced onto the image
bgSigmaUm   = 50;     // flat-field Gaussian sigma (should exceed cell size)
varRadiusPx = 3;      // Variance filter radius for round-cell/debris mask
maskMethod  = "Triangle dark"; // auto-threshold on the variance image
maskDilatePx= 3;      // iterations for close/dilate of the exclusion mask
seedSigmaUm = 8;      // blur before seed detection (~ cell radius / 2)
promK       = 0.3;    // seed prominence = promK * std(smoothed image)
seedLight   = false;  // true if cell centres are DARKER than their surroundings
minAreaUm2  = 200;    // size filter on final objects
maxAreaUm2  = 3500;
excludeEdge = false;  // true = drop cells touching the image border

setBatchMode(true);
setOption("BlackBackground", true);

open(input);
srcID = getImageID();
getDimensions(w, h, ch, sl, fr);
if (ch*sl*fr > 1 || bitDepth() == 24)
    exit("Expected a single-channel 2D grayscale image (Y,X).");
run("Set Scale...", "distance=1 known="+pxSize+" unit=um");

// 1. Work copy, 32-bit (no rescaling), flat-field by Gaussian background subtraction
run("Duplicate...", "title=work");
run("32-bit");
workID = getImageID();
run("Duplicate...", "title=bg");
bgID = getImageID();
run("Gaussian Blur...", "sigma="+(bgSigmaUm/pxSize));
imageCalculator("Subtract create 32-bit", workID, bgID);
flatID = getImageID();
rename("flat");

// 2. Mask of round refractile cells / debris (high local variance)
selectImage(flatID);
run("Duplicate...", "title=var");
varID = getImageID();
run("Variance...", "radius="+varRadiusPx);
setAutoThreshold(maskMethod);
run("Convert to Mask");
maskID = getImageID();
run("Options...", "iterations="+maskDilatePx+" count=1 black");
run("Close-");
run("Fill Holes");
run("Dilate");
run("Create Selection");
hasMask = (selectionType() != -1);
if (hasMask) {
    selectImage(flatID);
    run("Restore Selection");
    setColor(0);
    fill();
    run("Select None");
}

// 3. Seeds + watershed tessellation on the smoothed image
selectImage(flatID);
run("Gaussian Blur...", "sigma="+(seedSigmaUm/pxSize));
getStatistics(a, mean, mn, mx, sd);
prom = promK * sd;
light = "";
if (seedLight) light = "light ";
run("Find Maxima...", "prominence="+prom+" "+light+"output=[Segmented Particles]");
segID = getImageID();
rename("seg");
getStatistics(a, mean);
if (mean < 127) run("Invert");   // make particles 255, lines/background 0

// 4. Remove excluded (round cell/debris) region, then size-filter and label
if (hasMask) imageCalculator("Subtract", segID, maskID);
selectImage(segID);
setThreshold(255, 255);
minPx = minAreaUm2 / (pxSize*pxSize);
maxPx = maxAreaUm2 / (pxSize*pxSize);
opts = "size="+minPx+"-"+maxPx+" pixel show=[Count Masks]";
if (excludeEdge) opts = opts + " exclude";
run("Analyze Particles...", opts);
selectImage("Count Masks of seg");
labID = getImageID();
getStatistics(a, mean, mn, nLabels);
if (nLabels < 1) exit("No objects found; adjust the parameters.");
if (nLabels > 65535) exit("More than 65535 objects; 16-bit labels overflow.");
if (getWidth() != w || getHeight() != h) exit("Size mismatch (unexpected).");
run("Select None");
resetThreshold();
saveAs("Tiff", output);
print("Saved " + nLabels + " labelled objects to " + output);
setBatchMode(false);
