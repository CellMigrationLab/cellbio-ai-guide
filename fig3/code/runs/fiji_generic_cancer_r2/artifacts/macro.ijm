input = "<fig3-work>/bf3/fj_gen_cancer_r2/bf.tif"; output = "<fig3-work>/bf3/fj_gen_cancer_r2/labels.tif";

// ---- Parameters to tune ----
bgRadius   = 50;    // rolling-ball radius (px), larger than a cell
varRadius  = 3;     // texture filter radius (px); ~ rim thickness
smoothSigma = 2;    // smoothing of the texture map (px)
threshMethod = "Triangle";  // try "Otsu" or "Li" if too few/many cells
closeIter  = 2;     // closes gaps in the cell rim before hole filling
minArea    = 150;   // px^2; removes debris (cells are ~300-700 px^2)
maxArea    = 3000;  // px^2; removes huge blobs / glare artefacts

setBatchMode(true);
run("Clear Results");
setOption("BlackBackground", true);

open(input);
origTitle = getTitle();
run("Select None");
if (nSlices > 1) run("Z Project...", "projection=[Max Intensity]");  // safety for stacks
run("8-bit");
w = getWidth(); h = getHeight();
rename("work");

// 1. Flatten uneven illumination
run("32-bit");
run("Subtract Background...", "rolling=" + bgRadius + " light sliding");

// 2. Texture map: rims and halos of round cells have high local variance,
//    the faint flat background layer does not
run("Variance...", "radius=" + varRadius);
run("Gaussian Blur...", "sigma=" + smoothSigma);
run("Enhance Contrast", "saturated=0.35");
run("8-bit");

// 3. Threshold to a binary mask
setAutoThreshold(threshMethod + " dark");
run("Convert to Mask");

// 4. Close rings, fill the cell interiors, remove specks
for (i = 0; i < closeIter; i++) run("Dilate");
run("Fill Holes");
for (i = 0; i < closeIter; i++) run("Erode");
run("Open");
run("Fill Holes");

// 5. Split touching cells
run("Watershed");

// 6. Size filter and label image (0 = background, 1..N = objects)
run("Analyze Particles...", "size=" + minArea + "-" + maxArea + " pixel show=[Count Masks] exclude clear");
// "exclude" drops cells cut by the image border; remove that word to keep them.
labelTitle = getTitle();
run("Select None");
resetMinAndMax();

// 7. Save
saveAs("Tiff", output);
n = getValue("Max");
print("Segmented objects: " + n);

setBatchMode(false);
