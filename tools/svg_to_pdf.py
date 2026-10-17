"""Render a figure SVG to PDF (and optionally PNG) with headless Chromium, as the published PDFs were made.

Usage: python tools/svg_to_pdf.py fig1/figure/fig1.svg [--png out.png]
The page size equals the SVG size (1 px = 0.75 pt), so the PDF has no margins and no scaling."""
import argparse
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

CHROMIUM_CANDIDATES = ["/opt/pw-browsers/chromium", "chromium", "chromium-browser", "google-chrome"]


def find_chromium() -> str:
    for c in CHROMIUM_CANDIDATES:
        path = c if Path(c).is_file() else shutil.which(c)
        if path:
            return path
    raise FileNotFoundError(f"Chromium not found; tried {CHROMIUM_CANDIDATES}")


def svg_size(svg: Path) -> tuple[int, int]:
    head = svg.read_text(encoding="utf-8")[:2000]
    m = re.search(r'<svg[^>]*\bwidth="(\d+)"[^>]*\bheight="(\d+)"', head)
    if not m:
        raise ValueError(f"{svg}: no integer width/height on the <svg> element")
    return int(m.group(1)), int(m.group(2))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("svg", type=Path)
    ap.add_argument("--png", type=Path, help="also write a PNG screenshot here")
    args = ap.parse_args()
    svg = args.svg.resolve()
    w, h = svg_size(svg)
    chrome = find_chromium()
    with tempfile.TemporaryDirectory() as tmp:
        wrap = Path(tmp) / "wrap.html"
        wrap.write_text(f"<!doctype html><html><head><style>@page{{size:{w}px {h}px;margin:0}}"
                        f"html,body{{margin:0;padding:0}}img{{display:block;width:{w}px;height:{h}px}}</style></head>"
                        f'<body><img src="{svg.as_uri()}"></body></html>', encoding="utf-8")
        common = [chrome, "--headless", "--no-sandbox", "--disable-gpu", "--allow-file-access-from-files"]
        pdf = svg.with_suffix(".pdf")
        subprocess.run(common + ["--no-pdf-header-footer", f"--print-to-pdf={pdf}", wrap.as_uri()], check=True,
                       capture_output=True)
        print("wrote", pdf)
        if args.png:
            subprocess.run(common + ["--hide-scrollbars", f"--window-size={w},{h}", f"--screenshot={args.png.resolve()}", wrap.as_uri()],
                           check=True, capture_output=True)
            print("wrote", args.png)


if __name__ == "__main__":
    main()
