#!/usr/bin/env python3
"""Build one session: source.md  ->  out/<stem>.tex, out/<stem>.pdf, out/<stem>.docx  (+ out/<stem>.md always)

Canonical source is Markdown + LaTeX math (NOT raw .tex): pandoc's Markdown reader is far more
reliable than its LaTeX reader, so all outputs are generated mechanically from one file and cannot
silently drop content.

Graceful degradation: the source is validated first (missing figures, unknown @eq: references,
unbalanced ::: boxes, characters pdflatex cannot typeset). Then every format the machine can produce is
built; anything skipped is named together with the install command. out/<stem>.md (equations numbered,
boxes as quotes, figures copied) is always written, so a session is readable even with no toolchain.

Usage:
    python build_session.py <session_dir> [--no-pdf] [--no-docx] [--md-only] [--stem NAME]

<session_dir> must contain source.md; figures are referenced relative to it (figures/x.png).
YAML front matter in source.md supplies title / subtitle / author / date.
Exit code 0 = every requested-and-possible format built; 1 = validation or build failure.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.normpath(os.path.join(HERE, "..", "assets"))
sys.path.insert(0, HERE)
from check_env import TEX_HINT, capabilities, find_pandoc, missing_tex_packages, tex_env, tex_tool, tlmgr_cmd  # noqa: E402

BOX_CLASSES = ("definition", "keyidea", "warning", "exercise", "create", "term")
BOX_TITLES = {"definition": "Definition", "keyidea": "Key idea", "warning": "Watch out", "exercise": "Exercise",
              "create": "Create", "term": "Term"}
# Exactly what assets/pedagogy_boxes.lua accepts: an ASCII label right after the closing $$, followed by whitespace.
EQ_ID = r"eq:[A-Za-z0-9_-]+"
EQ_LABEL = re.compile(r"\$\$[ \t]*\{#(" + EQ_ID + r")\}(?=\s|$)")
EQ_ANY_LABEL = re.compile(r"\{#eq:[^}]*\}")
EQ_REF = re.compile(r"(?<![\w@])@(" + EQ_ID + r")")
EQ_GROUP = re.compile(r"\[\s*(@" + EQ_ID + r"(?:\s*;\s*@" + EQ_ID + r")*)\s*\]")   # [@eq:a; @eq:b]
DISPLAY_LABELLED = re.compile(r"\$\$((?:\\.|[^$\\])*?)\$\$[ \t]*\{#(" + EQ_ID + r")\}(?=\s|$)", re.S)
BOX_OPEN = re.compile(r"^:{3,}\s*(?:\{([^}]*)\}|([A-Za-z][\w-]*)(.*))\s*$")
FIG_REF = re.compile(r"!\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")


def run(cmd, cwd, env=None, fatal=True):
    r = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0 and fatal:
        sys.exit(f"FAILED: {' '.join(map(str, cmd[:3]))} ...\n{r.stdout[-2500:]}\n{r.stderr[-2500:]}")
    return r


def strip_code(text):
    """Source with fenced code blocks and inline code blanked (keeps line numbers), so validation ignores code."""
    out, fence = [], None
    for line in text.splitlines():
        m = re.match(r"^\s*(```+|~~~+)", line)
        if fence:
            out.append("")
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence):
                fence = None
            continue
        if m:
            fence = m.group(1)
            out.append("")
            continue
        out.append(re.sub(r"`[^`]*`", "", line))
    return "\n".join(out)


def strip_comments(text):
    return re.sub(r"<!--.*?-->", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)


def unmapped_unicode(src_text, preamble_text):
    """Non-ASCII characters in the source that the preamble cannot typeset (would crash pdflatex).
    Typographic chars pandoc already converts (quotes, dashes, nbsp) are exempt."""
    mapped = set(re.findall(r"\\newunicodechar\{(.)\}", preamble_text))
    exempt = set("\u2018\u2019\u201c\u201d\u2013\u2014\u00a0\u2026\u00e9\u00e8\u00fc\u00f6\u00e4\u00e1\u00ed\u00f3\u00fa\u00f1\u00e7\u00df")
    bad = {}
    for ln, line in enumerate(src_text.splitlines(), 1):
        for ch in line:
            if ord(ch) > 127 and ch not in mapped and ch not in exempt:
                bad.setdefault(ch, ln)
    return bad


def validate(sd, text):
    """Problems that would silently damage every output format. Returns a list of messages."""
    body = strip_code(strip_comments(text))
    probs = []
    # Control characters (often a "\b" or "\f" that an editor or script turned into a byte) crash pdflatex and are
    # invalid in the .docx XML, so they are rejected for every format. Tab, newline and carriage return are fine.
    for ln, line in enumerate(text.splitlines(), 1):
        bad = sorted({f"U+{ord(c):04X}" for c in line if (ord(c) < 32 and c not in "\t\r") or 0x7F <= ord(c) <= 0x9F})
        if bad:
            probs.append(f"line {ln}: control character(s) {', '.join(bad)} (a '\\b', '\\t' or '\\f' that lost its backslash?)")
    labels = EQ_LABEL.findall(body)
    good = {m.start(1) - 2 for m in EQ_LABEL.finditer(body)}   # offset of each accepted "{#"
    for m in EQ_ANY_LABEL.finditer(body):
        if m.start() not in good:
            ln = body.count("\n", 0, m.start()) + 1
            probs.append(f"line {ln}: equation label {m.group(0)} is not recognised: it must directly follow the closing $$, "
                         "use only ASCII letters, digits, '_' or '-', and be followed by a space or line end")
    dup = sorted({x for x in labels if labels.count(x) > 1})
    if dup:
        probs.append("duplicate equation labels: " + ", ".join(dup))
    unknown = sorted(set(EQ_REF.findall(body)) - set(labels))
    if unknown:
        probs.append("@eq: references with no matching {#eq:...} label: " + ", ".join(unknown))
    for ref in FIG_REF.findall(body):
        if re.match(r"^[a-z]+://", ref):
            continue
        if not inside(ref):
            probs.append(f"figure path leaves the session dir: {ref}  (copy the file into figures/ so out/ stays self-contained)")
        elif not os.path.isfile(os.path.join(sd, ref)):
            probs.append(f"figure not found: {ref}  (run its figure script, or fix the path; paths are relative to the session dir)")
    depth = 0
    for ln, line in enumerate(body.splitlines(), 1):
        s = line.strip()
        if BOX_OPEN.match(s):
            depth += 1
        elif re.match(r"^:{3,}\s*$", s):
            depth -= 1
            if depth < 0:
                probs.append(f"line {ln}: ':::' closes a box that was never opened")
                depth = 0
    if depth > 0:
        probs.append(f"{depth} ':::' box(es) never closed")
    return probs


def to_markdown(text):
    """Portable Markdown rendering of source.md (the fallback deliverable): numbered equations, resolved
    @eq: references, boxes as titled block quotes. Mirrors assets/pedagogy_boxes.lua."""
    # Split into prose / fenced-code chunks: code is copied verbatim (as the Lua filter leaves code alone),
    # so authoring examples inside ``` fences are never numbered, resolved or turned into boxes.
    chunks, cur, fence = [], [], None
    for line in text.splitlines():
        m = re.match(r"^\s*(```+|~~~+)", line)
        if fence is None and m:
            chunks.append((False, "\n".join(cur))); cur, fence = [line], m.group(1)
        elif fence is not None:
            cur.append(line)
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence):
                chunks.append((True, "\n".join(cur))); cur, fence = [], None
        else:
            cur.append(line)
    chunks.append((fence is not None, "\n".join(cur)))

    numbers = {}

    def tag(m):   # display math followed by {#eq:x} -> math with \tag{n}, numbered in document order
        numbers[m.group(2)] = n = len(numbers) + 1
        return f"$${m.group(1).rstrip()} \\tag{{{n}}}\n$$"

    # HTML comments never reach the .tex/.docx (pandoc drops them), so they must not take equation numbers here
    chunks = [(c, t if c else re.sub(r"<!--.*?-->", "", t, flags=re.S)) for c, t in chunks]
    chunks = [(c, t if c else DISPLAY_LABELLED.sub(tag, t)) for c, t in chunks]

    def num(eq):
        return f"({numbers[eq]})" if eq in numbers else f"(??{eq})"

    def refs(t):   # resolve @eq: outside inline code spans; [@eq:a; @eq:b] -> (1); (2), as the Lua filter does
        parts = re.split(r"(`[^`]*`)", t)
        return "".join(p if p.startswith("`") else
                       EQ_REF.sub(lambda m: num(m.group(1)),
                                  EQ_GROUP.sub(lambda g: "; ".join(num(x) for x in re.findall(EQ_ID, g.group(1))), p))
                       for p in parts)

    chunks = [(c, t if c else refs(t)) for c, t in chunks]
    out, stack = [], []
    for is_code, chunk in chunks:
        if is_code:
            out.extend(("> " * sum(stack) + l) if sum(stack) else l for l in chunk.splitlines())
            continue
        for line in chunk.splitlines():
            _box_line(line, out, stack)
    return "\n".join(out) + "\n"


def _box_line(line, out, stack):
    """Render one prose line, turning ::: fenced divs into (nested) titled block quotes. Divs that are not one of the
    pedagogy boxes (e.g. ::: {#id}) stay transparent, as the Lua filter leaves them: the stack holds True for a box
    (one quote level) and False for a transparent div."""
    s = line.strip()
    depth = sum(stack)
    mo = BOX_OPEN.match(s)
    if mo:
        attrs = mo.group(1) if mo.group(1) is not None else "." + mo.group(2) + " " + (mo.group(3) or "")
        cls = next((c for c in re.findall(r"(?:^|\s)\.([\w-]+)", attrs) if c in BOX_CLASSES), None)
        if cls is None:
            stack.append(False)
            return
        t = re.search(r'title="([^"]*)"', attrs)
        stack.append(True)
        out.append("> " * depth + f"> **{t.group(1) if t else BOX_TITLES[cls]}**")
        out.append("> " * (depth + 1))
        return
    if re.match(r"^:{3,}\s*$", s) and stack:
        if stack.pop():
            out.append("> " * sum(stack))
        return
    out.append(("> " * depth + line) if depth else line)


def inside(ref):
    """True for a relative path that stays inside its base directory (no '..' escape, not absolute)."""
    n = os.path.normpath(ref)
    return not os.path.isabs(ref) and not re.match(r"^[A-Za-z]:", ref) and n != ".." and not n.startswith(".." + os.sep)


def copy_figures(sd, out, refs):
    copied = 0
    for ref in refs:
        srcf = os.path.join(sd, ref)
        if os.path.isfile(srcf) and inside(ref):
            dst = os.path.join(out, ref)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(srcf, dst)
            copied += 1
    return copied


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("session_dir")
    ap.add_argument("--no-pdf", action="store_true")
    ap.add_argument("--no-docx", action="store_true")
    ap.add_argument("--md-only", action="store_true", help="validate and write out/<stem>.md only")
    ap.add_argument("--stem", default=None, help="output file stem (default: session directory name)")
    a = ap.parse_args()

    sd = os.path.abspath(a.session_dir)
    src = os.path.join(sd, "source.md")
    if not os.path.exists(src):
        sys.exit(f"no source.md in {sd}")
    with open(src, encoding="utf-8") as f:
        text = f.read()

    probs = validate(sd, text)
    if probs:
        sys.exit("source.md has problems; nothing built:\n  " + "\n  ".join(probs))

    stem = a.stem or os.path.basename(os.path.normpath(sd))
    out = os.path.join(sd, "out")
    os.makedirs(out, exist_ok=True)

    # 1. Markdown deliverable: always (needs nothing but Python)
    md_path = os.path.join(out, stem + ".md")
    with open(md_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(to_markdown(text))
    n_fig = copy_figures(sd, out, [r for r in FIG_REF.findall(strip_code(strip_comments(text))) if not re.match(r"^[a-z]+://", r)])
    print("built", md_path, f"(+{n_fig} figure file(s) in out/figures)")
    if a.md_only:
        return

    caps = capabilities()
    skipped = []
    if not caps["pandoc"]:
        skipped.append(".tex/.pdf/.docx: pandoc missing -> pip install pypandoc_binary  (then re-run this build)")
        print("SKIPPED", *skipped, sep="\n  ")
        print("The session is readable as", md_path)
        return

    want_pdf = not a.no_pdf
    if want_pdf and not caps["pdf"]:
        skipped.append(".pdf: TeX/latexmk missing -> " + TEX_HINT)
        want_pdf = False
    if want_pdf:
        missing = missing_tex_packages()
        if missing:
            skipped.append(".pdf: LaTeX packages missing -> " + tlmgr_cmd(missing))
            want_pdf = False
    failed = []
    if want_pdf:
        with open(os.path.join(ASSETS, "preamble.tex"), encoding="utf-8") as f2:
            bad = unmapped_unicode(strip_comments(text), f2.read())   # comments never reach pdflatex
        if bad:   # only pdflatex chokes on these; .tex and .docx are still built
            failed.append(".pdf: unsupported Unicode would crash pdflatex; write these as LaTeX math or add them to the "
                          "newunicodechar map in assets/preamble.tex:\n    " +
                          "\n    ".join(f"{c!r} U+{ord(c):04X} first at line {n}" for c, n in bad.items()))
            want_pdf = False

    pandoc = find_pandoc()
    lua = os.path.join(ASSETS, "pedagogy_boxes.lua")
    common = [pandoc, "source.md", "-f", "markdown+tex_math_dollars+raw_tex", "--lua-filter", lua, "--resource-path", sd]

    tex_path = os.path.join(out, stem + ".tex")
    run(common + ["-s", "-t", "latex", "--listings", "--toc", "-H", os.path.join(ASSETS, "preamble.tex"),
                  "-V", "documentclass=article", "-V", "fontsize=11pt", "-V", "geometry:margin=2.3cm",
                  "-V", "colorlinks=true", "-V", "linkcolor=blue!50!black", "-V", "urlcolor=blue!50!black",
                  "-o", tex_path], cwd=sd)
    print("built", tex_path)

    # out/ is a self-contained LaTeX project: every graphic the .tex references is copied under out/
    with open(tex_path, encoding="utf-8") as tf:
        refs = set(re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", tf.read()))
    print(f"copied {copy_figures(sd, out, refs)} referenced figure file(s) into out/ (out/ is a self-contained LaTeX project)")

    if want_pdf:
        # TEXINPUTS: session dir searched recursively ('//', forward slashes for kpathsea), then the default path.
        # os.pathsep is ';' on Windows (a ':' separator would split 'C:/...'); the trailing separator keeps TeX's defaults.
        env = {**tex_env(), "TEXINPUTS": sd.replace("\\", "/").rstrip("/") + "//" + os.pathsep}
        r = run([tex_tool("latexmk") or "latexmk", "-pdf", "-g", "-interaction=nonstopmode", "-halt-on-error", "-outdir=out",
                 os.path.join("out", stem + ".tex")], cwd=sd, env=env, fatal=False)
        pdf = os.path.join(out, stem + ".pdf")
        if r.returncode != 0:   # a LaTeX error must not cost the learner the .docx: record it and carry on
            log = (r.stdout or "")[-2500:]
            err = [l for l in log.splitlines() if l.startswith("!") or l.startswith("l.")]
            failed.append(".pdf: latexmk failed (see out/" + stem + ".log)\n    " + "\n    ".join(err[:6] or log.splitlines()[-12:]))
        else:
            print("built", pdf)
            if caps["pymupdf"]:
                import pymupdf
                with pymupdf.open(pdf) as doc:
                    n = doc.page_count
                print(f"PDF pages: {n}" + ("" if n >= 10 else "   (< 10: a ladder stage or depth level is probably thin; target 10-20)"))

    if not a.no_docx:
        ref = os.path.join(ASSETS, "reference.docx")
        cmd = common + ["-s", "-t", "docx", "--toc", "-o", os.path.join(out, stem + ".docx")]
        if os.path.exists(ref):
            cmd += ["--reference-doc", ref]
        r = run(cmd, cwd=sd, fatal=False)   # a .docx failure must not hide the PDF diagnostics collected above
        if r.returncode != 0:
            msg = ((r.stderr or "") + (r.stdout or "")).strip().splitlines()[-12:]
            failed.append(".docx: pandoc failed\n    " + "\n    ".join(msg))
        else:
            print("built", os.path.join(out, stem + ".docx"))

    if skipped:
        print("SKIPPED", *skipped, sep="\n  ")
    if failed:
        print("FAILED", *failed, sep="\n  ")
        sys.exit(1)


if __name__ == "__main__":
    main()
