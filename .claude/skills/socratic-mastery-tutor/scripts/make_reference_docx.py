#!/usr/bin/env python3
"""Generate assets/reference.docx: pandoc's default styles plus shaded Box-* paragraph styles.

Run once (or after changing box colours). build_session.py uses the result via --reference-doc
so the .docx boxes match the .tex boxes. Idempotent.
"""
import os
import subprocess
import sys
import tempfile

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

sys.path.insert(0, os.path.dirname(__file__))
from check_env import find_pandoc

COLORS = {  # class -> (border/text hex, fill hex)   mirrors preamble.tex
    "definition": ("1F4E79", "E8EEF4"),
    "keyidea": ("2E7D32", "E9F2E9"),
    "warning": ("A61C1C", "F6E8E8"),
    "exercise": ("B45F06", "F7EEE4"),
    "create": ("5B2C83", "EFE9F4"),
    "term": ("555555", "EEEEEE"),
}
OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "reference.docx")


# CT_PPr children that must come AFTER w:pBdr and w:shd (ECMA-376 schema order). Word rejects or ignores
# out-of-order pPr ("unreadable content"), so the box border/shading is inserted before the first of these.
AFTER_SHD = ("tabs", "suppressAutoHyphens", "kinsoku", "wordWrap", "overflowPunct", "topLinePunct", "autoSpaceDE",
             "autoSpaceDN", "bidi", "adjustRightInd", "snapToGrid", "spacing", "ind", "contextualSpacing", "mirrorIndents",
             "suppressOverlap", "jc", "textDirection", "textAlignment", "textboxTightWrap", "outlineLvl", "divId",
             "cnfStyle", "rPr", "sectPr", "pPrChange")


def shade(pPr, fill, border):
    for old in pPr.findall(qn("w:pBdr")) + pPr.findall(qn("w:shd")):   # idempotent re-runs
        pPr.remove(old)
    bdr = OxmlElement("w:pBdr")
    for side in ("top", "left", "bottom", "right"):
        e = OxmlElement(f"w:{side}")
        e.set(qn("w:val"), "single"); e.set(qn("w:sz"), "8"); e.set(qn("w:space"), "4"); e.set(qn("w:color"), border)
        bdr.append(e)
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), fill)
    after = {qn("w:" + t) for t in AFTER_SHD}
    anchor = next((c for c in pPr if c.tag in after), None)
    if anchor is None:
        pPr.append(bdr); pPr.append(shd)
    else:
        anchor.addprevious(bdr); anchor.addprevious(shd)


def main():
    pandoc = find_pandoc()
    if not pandoc:
        sys.exit("pandoc not found; run check_env.py")
    with tempfile.TemporaryDirectory() as td:
        base = os.path.join(td, "base.docx")
        with open(base, "wb") as f:
            f.write(subprocess.run([pandoc, "--print-default-data-file", "reference.docx"], check=True, capture_output=True).stdout)
        doc = Document(base)
        for cls, (border, fill) in COLORS.items():
            name = f"Box-{cls}"
            st = doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH) if name not in [s.name for s in doc.styles] else doc.styles[name]
            st.base_style = doc.styles["Normal"]
            st.font.size = Pt(10.5)
            st.font.color.rgb = RGBColor.from_string("000000")
            shade(st.element.get_or_add_pPr(), fill, border)
        doc.save(os.path.normpath(OUT))
    print("wrote", os.path.normpath(OUT))


if __name__ == "__main__":
    main()
