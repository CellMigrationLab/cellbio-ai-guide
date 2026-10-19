"""Export fig3_v2.svg as a PNG (2x) with headless Chromium (the same engine as tools/svg_to_pdf.py).

The browser window is made taller than the figure (headless Chromium loses about 90 px to its own frame) and the image is
cropped to the exact figure size, so nothing at the bottom is cut off.
Usage (from fig3/figure_v2/source_data): python ../code/export_png.py
"""
import glob
import re
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

SCALE = 2
SVG = Path("../output/fig3_v2.svg").resolve()
OUT = Path("../output/fig3_v2.png").resolve()


def main() -> None:
    head = SVG.read_text(encoding="utf-8")[:2000]
    w, h = (int(v) for v in re.search(r'width="(\d+)" height="(\d+)"', head).groups())
    chrome = sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome"))[-1]
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "page.html"
        page.write_text(f"<html><body style='margin:0;background:#fff'><img src='{SVG.as_uri()}' "
                        f"style='display:block;width:{w}px;height:{h}px'></body></html>")
        shot = Path(tmp) / "shot.png"
        subprocess.run([chrome, "--headless", "--no-sandbox", "--hide-scrollbars", f"--force-device-scale-factor={SCALE}",
                        f"--screenshot={shot}", f"--window-size={w},{h + 200}", page.as_uri()],
                       check=True, capture_output=True)
        Image.open(shot).crop((0, 0, w * SCALE, h * SCALE)).save(OUT)
    print("written", OUT.name, w * SCALE, "x", h * SCALE)


if __name__ == "__main__":
    main()
