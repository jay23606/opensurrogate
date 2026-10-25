#!/usr/bin/env python3
"""Verify the document/figure toolchain and print the exact fix for anything missing.

Readiness is reported in layers, because the course degrades gracefully instead of stopping:
    KB scripts   always (standard-library Python only)      -> state, curriculum, glossary all work
    figures      numpy + matplotlib (+ scipy, sympy)          -> figure scripts and code modules run
    documents    pandoc (system or pypandoc_binary)            -> .tex and .docx are generated
    PDF          a TeX distribution with latexmk + packages    -> .pdf is generated
    checks       pymupdf, python-docx                           -> page counts, structural .docx checks
Without pandoc, build_session.py still validates source.md and writes out/<stem>.md.

Import `find_pandoc`, `find_tex_bin`, `tex_env`, `check`, `capabilities` from other scripts.

Usage: python check_env.py [--quiet] [--strict]
Exit code: with --strict, 0 only when the full toolchain is present; without it, 0 whenever the KB layer works
(missing layers are printed as [warn] with the exact install command).
"""
import importlib
import os
import shutil
import subprocess
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

REQUIRED_TEX_PACKAGES = [
    "amsmath", "amssymb", "mathtools", "booktabs", "siunitx", "enumitem", "tcolorbox",
    "listings", "listingsutf8", "tikzfill.image", "pdfcol", "caption", "float", "hyperref", "geometry", "xcolor",
    "graphicx", "newunicodechar",
]
# .sty file name -> TeX Live package that ships it (tlmgr wants package names), where they differ
TLMGR_PKG = {"tikzfill.image": "tikzfill", "amsmath": "amsmath", "amssymb": "amsfonts", "graphicx": "graphics",
             "xcolor": "xcolor", "float": "float"}
FIGURE_PY = ["numpy", "matplotlib", "scipy", "sympy"]
EXTRA_PY = ["pandas", "yaml", "docx", "pymupdf"]
PIP_NAME = {"yaml": "pyyaml", "docx": "python-docx"}
WIN = os.name == "nt"
TEX_HINT = ("install TinyTeX: https://yihui.org/tinytex/  (Windows PowerShell: "
            "Invoke-WebRequest https://yihui.org/tinytex/install-bin-windows.bat -OutFile tt.bat; .\\tt.bat) "
            "then `tlmgr install latexmk`" if WIN else
            "install TinyTeX: curl -sL https://yihui.org/tinytex/install-bin-unix.sh | sh  then `tlmgr install latexmk`")


def find_pandoc():
    """Return a pandoc executable path or None. Falls back to the pypandoc_binary bundle."""
    p = shutil.which("pandoc")
    if p:
        return p
    try:
        import pypandoc
        p = pypandoc.get_pandoc_path()
        # on Windows pypandoc reports ".../files/pandoc" while the file on disk is pandoc.exe
        for cand in (p, p + ".exe") if p else ():
            if os.path.isfile(cand):
                return cand
    except Exception:
        pass
    return None


def find_tex_bin():
    """Resolve the real directory holding pdflatex (follows symlinks), or None. shutil.which honours PATHEXT,
    so this also finds pdflatex.exe on Windows."""
    p = shutil.which("pdflatex")
    if not p:
        return None
    real = os.path.realpath(p)
    return os.path.dirname(real) if os.path.exists(real) else None


def tex_env():
    """Environment with the real TeX bin dir first on PATH, so builds do not depend on symlinks."""
    env = os.environ.copy()
    b = find_tex_bin()
    if b:
        env["PATH"] = b + os.pathsep + env.get("PATH", "")
    return env


def tex_tool(name):
    """Path of a TeX tool (latexmk, kpsewhich) in the TeX bin dir or on PATH, Windows extensions included."""
    b = find_tex_bin()
    return shutil.which(name, path=b) if b and shutil.which(name, path=b) else shutil.which(name)


def missing_tex_packages():
    """Required .sty files kpsewhich cannot find: one subprocess, no heavy Python imports."""
    names = [p + ".sty" for p in REQUIRED_TEX_PACKAGES]
    r = subprocess.run([tex_tool("kpsewhich") or "kpsewhich", *names], capture_output=True, text=True, env=tex_env())
    found = {os.path.basename(l.strip()) for l in r.stdout.splitlines() if l.strip()}
    return [n[:-4] for n in names if n not in found]



def tlmgr_cmd(missing):
    """The tlmgr command that installs these .sty files (deduplicated TeX Live package names)."""
    return "tlmgr install " + " ".join(dict.fromkeys(TLMGR_PKG.get(m, m) for m in missing))


def _has(mod):
    try:
        importlib.import_module(mod)
        return True
    except Exception:
        return False


def capabilities():
    """Dict of booleans: what the machine can do right now (cheap; no TeX package scan)."""
    return {
        "figures": all(_has(m) for m in ("numpy", "matplotlib")),
        "pandoc": find_pandoc() is not None,
        "pdf": find_tex_bin() is not None and tex_tool("latexmk") is not None,
        "pymupdf": _has("pymupdf"),
    }


def check(quiet=False, strict=True):
    """Return a list of problems (empty = ready). strict=False only fails when the KB layer cannot work."""
    problems = []
    log = (lambda *a: None) if quiet else print

    log(f"[ok]   KB scripts python {sys.version.split()[0]} (standard library only)")
    if sys.version_info < (3, 8):
        problems.append("Python >= 3.8 required for the KB scripts")

    pandoc = find_pandoc()
    if pandoc:
        try:
            v = subprocess.run([pandoc, "--version"], capture_output=True, text=True).stdout.splitlines()[0]
        except Exception:
            v = "pandoc"
        log(f"[ok]   pandoc     {v}  ({pandoc})")
    else:
        problems.append("pandoc missing (no .tex/.docx; builds fall back to .md) -> pip install pypandoc_binary"
                        "   (or: winget install JohnMacFarlane.Pandoc / conda install -c conda-forge pandoc)")

    texbin = find_tex_bin()
    if texbin and tex_tool("latexmk"):
        log(f"[ok]   TeX bin    {texbin}")
        missing = missing_tex_packages()
        if missing:
            problems.append("LaTeX packages missing -> " + tlmgr_cmd(missing))
        else:
            log(f"[ok]   LaTeX pkgs {len(REQUIRED_TEX_PACKAGES)} required packages present")
    elif texbin:
        problems.append("pdflatex found but latexmk missing -> tlmgr install latexmk  (latexmk needs Perl; TinyTeX ships it)")
    else:
        problems.append("pdflatex/latexmk not found (no .pdf) -> " + TEX_HINT)

    miss_py = [m for m in FIGURE_PY + EXTRA_PY if not _has(m)]
    if miss_py:
        problems.append("python modules missing (" + ", ".join(miss_py) + ") -> "
                        + f'"{sys.executable}" -m pip install ' + " ".join(PIP_NAME.get(m, m) for m in miss_py))
    else:
        log(f"[ok]   python     {len(FIGURE_PY + EXTRA_PY)} figure/check modules present")

    for p in problems:
        log("[FAIL]" if strict else "[warn]", p)
    if problems and not quiet:
        caps = capabilities()
        print("\nWhat works right now:")
        print("  KB state machine (kb_update.py, new_session.py, quick-explain mode): yes")
        print(f"  figures and code modules: {'yes' if caps['figures'] else 'no (install numpy + matplotlib)'}")
        print(f"  .tex/.docx: {'yes' if caps['pandoc'] else 'no -> build_session.py writes out/<stem>.md instead'}")
        print(f"  .pdf: {'yes' if caps['pdf'] else 'no'}")
    if not strict:
        return [p for p in problems if "Python >= 3.8" in p]
    return problems


if __name__ == "__main__":
    sys.exit(1 if check(quiet="--quiet" in sys.argv, strict="--strict" in sys.argv) else 0)
