// Count and measure cancer cells on a confluent endothelial monolayer (brightfield)
// Input : image.tif (working directory)   Output: labels.tif (16-bit label image), Results table
// Idea  : cancer cells are round, with a strong dark rim / bright halo; the endothelial
//         monolayer is low-contrast. So segment on LOCAL CONTRAST (local SD), not intensity.

// ---- parameters (pixels; tune to your magnification) ----
bgSigma    = 30;    // background flattening (>> cell diameter)
sdRadius   = 3;     // local variance radius (~ rim thickness)
smoothSig  = 1;     // smoothing of the contrast map
thrScale   = 1.0;   // multiply Otsu threshold (lower = more sensitive)
closeIter  = 3;     // close gaps in rims
openIter   = 5;     // remove thin debris / monolayer texture
minArea    = 250;   // px^2, rejects debris
maxArea    = 2500;  // px^2
minCirc    = 0.30;  // loose, only to drop jagged debris

dir = getDirectory("current");
open(dir + "image.tif");
orig = getTitle();
W = getWidth(); H = getHeight();
run("Properties...", "unit=pixel pixel_width=1 pixel_height=1 voxel_depth=1"); // areas in px^2; remove to use calibration

// 1. flatten background, local contrast map
run("Duplicate...", "title=work");
run("32-bit");
run("Duplicate...", "title=bg");
run("Gaussian Blur...", "sigma="+bgSigma);
imageCalculator("Subtract 32-bit", "work", "bg");
close("bg");
run("Variance...", "radius="+sdRadius);   // local variance
run("Square Root");                        // -> local SD
run("Gaussian Blur...", "sigma="+smoothSig);

// 2. threshold (Otsu) scaled by thrScale
setAutoThreshold("Otsu dark no-reset");
getThreshold(lo, hi);
setThreshold(lo*thrScale, 1e30);
run("Convert to Mask");
rename("mask");

// 3. clean up: close rims, fill the cell interior, remove thin stuff
run("Options...", "iterations="+closeIter+" count=1 black do=Close");
run("Fill Holes");
run("Options...", "iterations="+openIter+" count=1 black do=Open");
run("Options...", "iterations=1 count=1 black");   // reset
run("Watershed");                                   // split touching cells

// 4. objects -> ROI Manager, filtered by size/shape
roiManager("reset");
run("Set Measurements...", "area shape redirect=None decimal=2");
run("Analyze Particles...", "size="+minArea+"-"+maxArea+" circularity="+minCirc+"-1.00 show=Nothing exclude clear add");
// ("exclude" drops cells cut by the image border so areas are not biased; remove the word to keep them)
n = roiManager("count");

// 5. label image + per-cell area table
newImage("labels", "16-bit black", W, H, 1);
run("Clear Results");
selectImage(orig);
for (i = 0; i < n; i++) {
    roiManager("select", i);
    run("Measure");                         // area (px^2) in Results
    selectImage("labels");
    roiManager("select", i);
    setColor(i+1);
    run("Fill", "slice");
    selectImage(orig);
}
roiManager("deselect");
selectImage("labels");
run("glasbey on dark");                      // optional: distinct LUT (ignored if absent)
saveAs("Tiff", dir + "labels.tif");

// 6. summary
sum = 0;
for (i = 0; i < n; i++) sum += getResult("Area", i);
print("Cancer cells counted: " + n);
if (n > 0) print("Mean area (px^2): " + d2s(sum/n, 1));
saveAs("Results", dir + "cell_areas.csv");
selectImage(orig);
roiManager("Show All without labels");
close("work"); close("mask");
