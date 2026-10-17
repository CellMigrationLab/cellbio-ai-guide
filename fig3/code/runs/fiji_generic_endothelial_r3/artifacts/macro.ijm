input = "<fig3-work>/bf3/fj_gen_endo_r3/bf.tif"; output = "<fig3-work>/bf3/fj_gen_endo_r3/labels.tif";

// ---- Parameters to tune (pixels / gray levels, for a ~1000 px image) ----
bgSigma      = 40;   // large-scale background (illumination) sigma
seedSigma    = 8;    // smoothing before seed detection; ~ 1/6 of cell diameter
prominence   = 1.5;  // seed sensitivity: lower = more (smaller) cells, higher = fewer
rejectThresh = 18;   // local contrast above this = round cell / debris, excluded
rejectGrow   = 3;    // dilation (px) of the excluded mask
minArea      = 400;  // smallest endothelial cell territory kept (px^2)
maxArea      = 12000;// largest territory kept (px^2)
seedsAreDark = false;// set true if cell centres/nuclei appear darker than surroundings

setBatchMode(true);
setOption("BlackBackground", true);
run("Clear Results");
if (roiManager("count") > 0) roiManager("reset");

open(input);
origID = getImageID();
w = getWidth(); h = getHeight();
run("8-bit");

// ---- 1. Mask round bright cells and debris (strong local contrast) ----
run("Duplicate...", "title=dev");
devID = getImageID();
run("32-bit");
run("Duplicate...", "title=bg");
bgID = getImageID();
run("Gaussian Blur...", "sigma=" + bgSigma);
selectImage(devID);
run("Gaussian Blur...", "sigma=1");
imageCalculator("Subtract 32-bit", devID, bgID);
selectImage(bgID); close();
selectImage(devID);
run("Abs");
setThreshold(rejectThresh, 100000);
run("Convert to Mask");
rename("reject");
rejectID = getImageID();
run("Close-");
run("Fill Holes");
for (i = 0; i < rejectGrow; i++) run("Dilate");

// keep = NOT reject
run("Duplicate...", "title=keep");
keepID = getImageID();
run("Invert");

// ---- 2. Seeds and watershed on a smoothed, flat-fielded image ----
selectImage(origID);
run("Duplicate...", "title=smooth");
smoothID = getImageID();
run("32-bit");
run("Duplicate...", "title=bg2");
bg2ID = getImageID();
run("Gaussian Blur...", "sigma=" + bgSigma);
imageCalculator("Subtract 32-bit", smoothID, bg2ID);
selectImage(bg2ID); close();
selectImage(smoothID);
run("Gaussian Blur...", "sigma=" + seedSigma);
run("Enhance Contrast...", "saturated=0.35 normalize");
run("8-bit");
opts = "prominence=" + prominence + " output=[Segmented Particles]";
if (!seedsAreDark) { } else { opts = opts + " light"; }
if (seedsAreDark) run("Invert");   // so maxima = cell centres in all cases
run("Find Maxima...", "prominence=" + prominence + " output=[Segmented Particles]");
segID = getImageID();
setOption("BlackBackground", true);

// ---- 3. Restrict territories to endothelial area ----
imageCalculator("Min create", segID, keepID);
cleanID = getImageID();
rename("clean");
setThreshold(255, 255);
run("Analyze Particles...", "size=" + minArea + "-" + maxArea + " pixel show=Nothing add");

// ---- 4. Build label image: 0 = background, 1..N = cells ----
n = roiManager("count");
newImage("labels", "16-bit black", w, h, 1);
labID = getImageID();
for (i = 0; i < n; i++) {
    roiManager("select", i);
    setColor(i + 1);
    fill();
}
run("Select None");
resetMinAndMax();
saveAs("Tiff", output);

print("Segmented " + n + " cells; saved " + output);
setBatchMode(false);
