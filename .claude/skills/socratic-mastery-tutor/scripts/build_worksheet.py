#!/usr/bin/env python3
"""Build a worksheet PDF from a Markdown source: pandoc -> HTML (worksheet.css) -> headless Edge/Chrome -> PDF.

    python build_worksheet.py source.md [-o out.pdf]

No TeX needed. The .html is always kept next to the source; if no Chromium-based browser is found, the .html is the
deliverable and the script says so (exit code 2). Images referenced in source.md are resolved relative to it.
"""
import argparse
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from check_env import find_pandoc  # noqa: E402

CSS = os.path.join(HERE, "..", "assets", "worksheet.css")
BROWSERS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]


def find_browser():
    for name in ("msedge", "chrome", "google-chrome", "chromium", "chromium-browser"):
        p = shutil.which(name)
        if p:
            return p
    for p in BROWSERS:
        if os.path.exists(p):
            return p
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", help="worksheet source.md")
    ap.add_argument("-o", "--output", help="output .pdf (default: next to source)")
    a = ap.parse_args()

    src = os.path.abspath(a.source)
    out = os.path.abspath(a.output) if a.output else os.path.splitext(src)[0] + ".pdf"
    html = os.path.splitext(src)[0] + ".html"  # next to the source, so the output folder holds only the PDF

    pandoc = find_pandoc()
    if not pandoc:
        sys.exit("pandoc missing -> pip install pypandoc_binary")
    r = subprocess.run([pandoc, src, "-f", "markdown+raw_html+pipe_tables", "-t", "html5", "-s",
                        "--embed-resources", "--css", os.path.abspath(CSS), "--metadata", "lang=en",
                        "--resource-path", os.path.dirname(src), "-o", html],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit("pandoc failed:\n" + r.stderr)
    print("wrote", html)

    br = find_browser()
    if not br:
        print("no Edge/Chrome found: the .html is the deliverable (open it and print to PDF).")
        sys.exit(2)
    pdf_cmd = [br, "--headless", "--disable-gpu", "--no-pdf-header-footer",
               "--print-to-pdf=" + out, "file:///" + html.replace("\\", "/")]
    r = subprocess.run(pdf_cmd, capture_output=True, text=True, timeout=120)
    if not os.path.exists(out):
        sys.exit("browser did not produce a PDF:\n" + r.stderr)
    print("wrote", out)


if __name__ == "__main__":
    main()
