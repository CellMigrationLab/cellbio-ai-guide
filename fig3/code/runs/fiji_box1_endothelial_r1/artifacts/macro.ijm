input = "<fig3-work>/bf3/fj_box1_endo_r1/bf.tif"; output = "<fig3-work>/bf3/fj_box1_endo_r1/labels.tif";

// ---------------- parameters (all consequential ones) ----------------
pixelSize   = 0.65;    // um per pixel (from you)
flatSigmaPx = 100;     // background flattening: Gaussian sigma in px (~65 um, > largest cell of ~77 px)
seedSigmaPx = 10;      // smoothing before seed finding (~6.5 um, ~0.2 x cell diameter)
promSD      = 0.30;    // Find Maxima prominence = promSD x SD of the smoothed image (relative, no fixed grey level)
seedsAreDark = true;   // endothelial nuclei/cell centres assumed DARKER than the surroundings; false = brighter
varRadiusPx = 2;       // Variance filter radius for detecting floating round cells/debris
varSmoothPx = 3;       // smoothing of the variance map
dilatePx    = 3;       // dilation of the "non-endothelial" mask (iterations, 1 px each)
maxMaskFrac = 0.30;    // drop a territory if more than this fraction of it lies in that mask
minDiam = 15; maxDiam = 75;   // um; accepted equivalent diameter (25-50 um expected, wide margin)
excludeEdge = true;    // drop territories touching the image border (truncated areas)

// ---------------- open and check ----------------
open(input);
origID = getImageID();
if (nSlices > 1) exit("Expected a single 2D image, got " + nSlices + " slices.");
if (bitDepth() == 24) run("8-bit");          // RGB -> grey (weighted/unweighted per your Edit>Options>Conversions)
getDimensions(W, H, c, z, t);
run("Properties...", "channels=1 slices=1 frames=1 unit=um pixel_width=" + pixelSize + " pixel_height=" + pixelSize + " voxel_depth=1");
run("Options...", "iterations=" + dilatePx + " count=1 black");   // binary ops: black background, dilate iterations

// ---------------- work copy: 32-bit, NO resizing ----------------
run("Duplicate...", "title=work");
run("32-bit");
workID = getImageID();
run("Duplicate...", "title=bg");
run("Gaussian Blur...", "sigma=" + flatSigmaPx);        // sigma in pixels (no 'scaled')
bgID = getImageID();
imageCalculator("Subtract create 32-bit", workID, bgID); // flat = work - blurred background (mean ~0, not rescaled)
flatID = getImageID();
rename("flat");

// ---------------- mask of floating round cells / debris ----------------
selectImage(flatID);
run("Duplicate...", "title=var");
run("Variance...", "radius=" + varRadiusPx);
run("Gaussian Blur...", "sigma=" + varSmoothPx);
setAutoThreshold("Triangle dark");                       // auto threshold on the variance map
run("Convert to Mask");
run("Dilate");                                           // 'dilatePx' iterations
maskID = getImageID();

// ---------------- seeds and watershed territories ----------------
selectImage(flatID);
run("Duplicate...", "title=seed");
run("Gaussian Blur...", "sigma=" + seedSigmaPx);
seedID = getImageID();
getStatistics(a, mean, mn, mx, sd);
prom = promSD * sd;
lightFlag = ""; if (seedsAreDark) lightFlag = " light";  // 'light' = look for minima
run("Find Maxima...", "prominence=" + prom + lightFlag + " output=[Segmented Particles]");
tessID = getImageID();                                   // 8-bit: particles 255, watershed lines 0
run("Properties...", "channels=1 slices=1 frames=1 unit=um pixel_width=" + pixelSize + " pixel_height=" + pixelSize + " voxel_depth=1");
setThreshold(1, 255);

minA = PI * pow(minDiam / 2, 2);   // um^2
maxA = PI * pow(maxDiam / 2, 2);
opts = "size=" + minA + "-" + maxA + " circularity=0.00-1.00 show=Nothing add";
if (excludeEdge) opts = opts + " exclude";
roiManager("reset");
run("Analyze Particles...", opts);

// ---------------- reject territories lying on round cells/debris ----------------
selectImage(maskID);
for (i = roiManager("count") - 1; i >= 0; i--) {
    roiManager("select", i);
    if (getValue("Mean") / 255 > maxMaskFrac) roiManager("delete");
}
n = roiManager("count");

// ---------------- label image, original X/Y grid ----------------
newImage("labels", "16-bit black", W, H, 1);
run("Properties...", "channels=1 slices=1 frames=1 unit=um pixel_width=" + pixelSize + " pixel_height=" + pixelSize + " voxel_depth=1");
labID = getImageID();
sumA = 0;
for (i = 0; i < n; i++) {
    roiManager("select", i);
    setColor(i + 1);
    fill();
    sumA += getValue("Area");
}
run("Select None");
saveAs("Tiff", output);
if (n > 0) print("Objects: " + n + "   mean area: " + (sumA / n) + " um^2");
else print("No objects found - check parameters.");
roiManager("reset");
