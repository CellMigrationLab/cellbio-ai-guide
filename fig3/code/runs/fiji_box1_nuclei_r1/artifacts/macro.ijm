input = "<fig3-work>/bf3/fj_box1_nuclei_r1/dapi.tif";
output = "<fig3-work>/bf3/fj_box1_nuclei_r1/labels.tif";

// ---------------- parameters (edit if needed) ----------------
pixelSize    = 0.65;   // um per pixel (assumed; checked against file calibration below)
sigmaPx      = 1.0;    // Gaussian blur sigma in PIXELS (~0.65 um)
rollingPx    = 30;     // rolling-ball radius in PIXELS (~19.5 um; > largest nucleus radius)
thrMethod    = "Li";   // global auto-threshold on the 16-bit histogram
minDiamUm    = 6;      // smallest object kept (equivalent diameter, um)
maxDiamUm    = 25;     // largest object kept (equivalent diameter, um)
excludeEdges = false;  // true = drop nuclei touching the image border
// -------------------------------------------------------------

setBatchMode(true);
open(input);
origID = getImageID();
if (nSlices > 1) exit("Expected a single 2D plane (Y,X); this image has " + nSlices + " planes/channels.");
if (bitDepth() == 24 || bitDepth() == 32) exit("Expected 8- or 16-bit grayscale (found " + bitDepth() + "-bit).");

getPixelSize(unit, pw, ph);
if (unit != "pixels" && unit != "pixel" && abs(pw - pixelSize) / pixelSize > 0.05)
    print("WARNING: file calibration is " + pw + " " + unit + "/px, macro assumes " + pixelSize + " um/px.");

// size limits converted to pixel area (circle of the given diameter)
minArea = PI / 4 * pow(minDiamUm / pixelSize, 2);
maxArea = PI / 4 * pow(maxDiamUm / pixelSize, 2);

// work on a copy; the original is never modified
run("Duplicate...", "title=work");
run("Gaussian Blur...", "sigma=" + sigmaPx);                    // pixels (no 'scaled' flag)
run("Subtract Background...", "rolling=" + rollingPx);          // pixels; modifies intensities
setAutoThreshold(thrMethod + " dark 16-bit");
run("Options...", "iterations=1 count=1 black do=Nothing");     // global setting: black background
run("Convert to Mask");                                         // foreground = 255
run("Fill Holes");
run("Open");                                                    // removes 1-px bridges/specks
run("Watershed");                                               // splits touching convex nuclei

opts = "size=" + minArea + "-" + maxArea + " pixel circularity=0.00-1.00 show=[Count Masks]";
if (excludeEdges) opts = opts + " exclude";
run("Analyze Particles...", opts);                              // new 16-bit label image becomes active

getStatistics(area, mean, min, max);
print("Nuclei segmented: " + max);
saveAs("Tiff", output);

// tidy up
while (nImages > 0) { selectImage(nImages); close(); }
setBatchMode(false);
