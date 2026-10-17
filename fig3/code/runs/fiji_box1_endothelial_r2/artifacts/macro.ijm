input = "<fig3-work>/bf3/fj_box1_endo_r2/bf.tif"; output = "<fig3-work>/bf3/fj_box1_endo_r2/labels.tif";

// ---------------- parameters (edit) ----------------
pixelSize     = 0.65;   // um per pixel (overrides file calibration)
minDiamUm     = 15;     // min equivalent diameter kept
maxDiamUm     = 80;     // max equivalent diameter kept
bgSigmaUm     = 60;     // illumination flattening Gaussian
seedSigmaUm   = 6;      // smoothing before seed detection
seedsAreDark  = true;   // ASSUMPTION: cell centres (nuclei) darker than surroundings
prominenceSD  = 0.3;    // seed prominence as fraction of SD of smoothed image
maskVarUm     = 3;      // Variance filter radius for round-cell/debris mask
maskK         = 3;      // mask threshold = mean + maskK * SD of variance image
maskGrowPx    = 2;      // dilation of exclusion mask
excludeEdge   = true;   // drop objects touching the image border
// ---------------------------------------------------

setBatchMode(true);
run("Options...", "iterations=1 count=1 black");
open(input);
origID = getImageID();
getDimensions(w, h, c, z, t);
if (c*z*t > 1) exit("Input must be a single 2D plane (Y,X).");
getPixelSize(unit, pw, ph);
if ((unit=="um" || unit=="micron" || unit=="microns" || unit=="µm") && abs(pw-pixelSize) > 0.01)
    print("WARNING: file calibration " + pw + " " + unit + "/px differs from pixelSize=" + pixelSize);
run("Properties...", "pixel_width=1 pixel_height=1 voxel_depth=1 unit=pixel");
if (bitDepth()==24) run("8-bit");

bgSigma   = bgSigmaUm/pixelSize;
seedSigma = seedSigmaUm/pixelSize;
varRadius = maxOf(1, round(maskVarUm/pixelSize));
minA = PI/4*pow(minDiamUm/pixelSize, 2);
maxA = PI/4*pow(maxDiamUm/pixelSize, 2);

// 1. exclusion mask from local variance (round refractile cells, debris)
selectImage(origID); run("Duplicate...", "title=rawmask"); run("32-bit");
run("Variance...", "radius=" + varRadius);
getStatistics(a, mean, mn, mx, sd);
setThreshold(mean + maskK*sd, 1e30);
run("Convert to Mask");
run("Fill Holes");
run("Options...", "iterations=" + maskGrowPx + " count=1 black do=Dilate");
run("Fill Holes");
run("Options...", "iterations=1 count=1 black");
rename("excl");

// 2. flatten illumination (float, no rescaling)
selectImage(origID); run("Duplicate...", "title=flat"); run("32-bit");
run("Duplicate...", "title=bgimg");
run("Gaussian Blur...", "sigma=" + bgSigma);
imageCalculator("Subtract 32-bit", "flat", "bgimg");
close("bgimg");

// 3. seeds + watershed tiling
selectImage("flat");
run("Gaussian Blur...", "sigma=" + seedSigma);
getStatistics(a, mean, mn, mx, sd);
prom = prominenceSD*sd;
light = "";
if (seedsAreDark) light = " light";
run("Find Maxima...", "prominence=" + prom + light + " output=[Segmented Particles]");
rename("tiles");

// 4. remove excluded regions, label, size/edge filter
imageCalculator("Subtract", "tiles", "excl");
selectImage("tiles");
setThreshold(255, 255);
opts = "size=" + minA + "-" + maxA + " pixel show=[Count Masks]";
if (excludeEdge) opts = opts + " exclude";
run("Analyze Particles...", opts);
rename("labels");
run("Select None");
getStatistics(a, mean, mn, nObj);
print("Objects: " + nObj);
saveAs("Tiff", output);
setBatchMode(false);
