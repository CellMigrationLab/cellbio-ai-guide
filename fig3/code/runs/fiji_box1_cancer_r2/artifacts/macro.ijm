input = "<fig3-work>/bf3/fj_box1_cancer_r2/bf.tif"; output = "<fig3-work>/bf3/fj_box1_cancer_r2/labels.tif";
// Use full paths if the files are not in Fiji's working directory.

// ---- parameters ----
pixelSize = 0.65;   // um per pixel (set explicitly on the image)
varRadius = 3;      // px, Process>Filters>Variance radius
blurSigma = 2;      // px, Gaussian smoothing of log-variance map
erodeIter = 2;      // px, shrink mask to offset filter-induced growth
minArea   = 100;    // um^2
maxArea   = 800;    // um^2
minCirc   = 0.5;    // circularity lower bound

setBatchMode(true);
setOption("BlackBackground", true);   // global Fiji setting; objects = 255 in binary masks
run("Options...", "iterations=1 count=1 black");

open(input);
if (nSlices > 1) exit("Expected a single 2D image; got " + nSlices + " planes.");
origTitle = getTitle();
getDimensions(w, h, ch, sl, fr);
if (ch > 1) exit("Expected a single channel.");
run("Properties...", "channels=1 slices=1 frames=1 pixel_width=" + pixelSize +
    " pixel_height=" + pixelSize + " voxel_depth=1 unit=um");

// Work on a 32-bit copy; the original is never modified and nothing is resized.
run("Duplicate...", "title=work");
run("32-bit");
run("Variance...", "radius=" + varRadius);   // local texture: high at cell rims, low on flat monolayer/background
run("Add...", "value=1");
run("Log");                                  // natural log, tames the heavy tail
run("Gaussian Blur...", "sigma=" + blurSigma);
setAutoThreshold("Otsu dark");
run("Convert to Mask");                      // 8-bit binary, objects = 255

run("Fill Holes");                           // fills the bright centres inside the rims
for (i = 0; i < erodeIter; i++) run("Erode");
run("Open");                                 // remove thin bridges and specks
run("Watershed");                            // split touching cells (EDM-based)

// Size in calibrated um^2; "Count Masks" gives a 16-bit label image (one value per particle).
run("Analyze Particles...", "size=" + minArea + "-" + maxArea +
    " circularity=" + minCirc + "-1.00 show=[Count Masks]");
labID = getImageID();
run("Properties...", "channels=1 slices=1 frames=1 pixel_width=" + pixelSize +
    " pixel_height=" + pixelSize + " voxel_depth=1 unit=um");
if (getWidth() != w || getHeight() != h) exit("Label image size differs from input.");

getStatistics(a, mean, mn, nObjects);
print("Objects: " + nObjects);
saveAs("Tiff", output);

// Quick summary of areas (um^2)
run("Duplicate...", "title=m");
setThreshold(1, 65535);
run("Set Measurements...", "area redirect=None decimal=2");
run("Analyze Particles...", "size=0-Infinity display clear");
if (nResults > 0) {
    s = 0; for (r = 0; r < nResults; r++) s += getResult("Area", r);
    print("Mean area (um^2): " + s / nResults);
}
setBatchMode(false);
