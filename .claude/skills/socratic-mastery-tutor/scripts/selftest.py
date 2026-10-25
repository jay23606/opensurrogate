#!/usr/bin/env python3
"""Smoke test of the whole document pipeline. Run after ANY change to the preamble, the Lua filter,
the reference docx or build_session.py:   python selftest.py      (exit 0 = pass, 1 = fail, 2 = skipped: pandoc or matplotlib missing;
PDF checks run only when TeX + pymupdf are present)

Builds a fixture session containing every construct a real session uses (aligned derivation, several
labelled equations in ONE paragraph, equation cross-references, figures, pipe tables with captions, code,
all box types incl. nested, Unicode symbols) and asserts on the .tex/.pdf/.docx outputs.
"""
import os
import re
import subprocess
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURE = r'''---
title: "Selftest"
subtitle: "fixture"
author: "selftest"
date: "2026-01-01"
---

# Equations

Averaging @eq:a gives the same for the fluctuation:
$$
\frac{\partial u_j'}{\partial x_j}=0 .
$$ {#eq:a}
Both fields are solenoidal (this line follows a label directly).
$$
\begin{aligned}
a &= b \\
  &= c
\end{aligned}
$$ {#eq:b}
Unicode in prose: ∂u/∂x, ε, ν, κ ≈ 0.41, § 6.13, ✔. And @eq:b refers back to @eq:a.
Grouped: [@eq:a; @eq:b].

- a tight list item with a labelled equation $$ F = ma $$ {#eq:n2}
- and @eq:n2 cited from the list

::: {.exercise title="1. Find the velocity"}
exercise text
:::

Unlabelled display math is untouched:
$$
E=mc^2
$$

# Figure, table, code, boxes

![fig01. A figure.](figures/fig01.png){width=60%}

| A | B |
|:--|--:|
| 1 | 2 |

Table: A caption.

```python
print("hello")
```

::: {.definition title="Mass & momentum: $p = \gamma m v$, 50% rule_x"}
boxed
:::

```python
print("@eq:a")
```

::: {.keyidea title="Outer"}
outer text

::: {.warning title="Inner"}
inner text $x^2$
:::
:::
'''


def main():
    sys.path.insert(0, HERE)
    from check_env import capabilities
    caps = capabilities()
    if not (caps["pandoc"] and caps["figures"]):
        need = [k for k in ("pandoc", "figures") if not caps[k]]
        print("SKIPPED: the document pipeline needs " + ", ".join(need) + " (run check_env.py for install commands).")
        print("The Markdown fallback is covered by kb_selftest.py.")
        sys.exit(2)
    do_pdf = caps["pdf"] and caps["pymupdf"]
    with tempfile.TemporaryDirectory() as td:
        os.makedirs(os.path.join(td, "figures"))
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(3, 2)); ax.plot([0, 1], [0, 1]); fig.savefig(os.path.join(td, "figures", "fig01.png"))
        with open(os.path.join(td, "source.md"), "w", encoding="utf-8") as f:
            f.write(FIXTURE)
        r = subprocess.run([sys.executable, os.path.join(HERE, "build_session.py"), td, "--stem", "st"] + ([] if do_pdf else ["--no-pdf"]),
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        checks = []

        def ok(name, cond):
            checks.append(cond)
            print(("PASS  " if cond else "FAIL  ") + name)

        ok("build_session exits 0" + ("" if r.returncode == 0 else "\n" + r.stdout[-800:] + r.stderr[-800:]), r.returncode == 0)
        out = os.path.join(td, "out")
        ok("figure copied into out/figures/ (tex is portable)", os.path.exists(os.path.join(td, "out", "figures", "fig01.png")))
        for ext in ("md", "tex", "docx") + (("pdf",) if do_pdf else ()):
            ok(f"out/st.{ext} exists", os.path.exists(os.path.join(out, "st." + ext)))
        if not all(checks):
            print("SELFTEST FAILED")
            sys.exit(1)
        tex = open(os.path.join(out, "st.tex"), encoding="utf-8").read()
        ok("tex: labelled equations numbered, refs resolved, no stray labels",
           r"\qquad (1)" in tex and r"\qquad (2)" in tex and r"{\#eq" not in tex and "??" not in tex)
        ok("tex: box title special characters escaped, math kept",
           r"Mass \& momentum" in tex and r"50\% rule\_x" in tex and r"\gamma" in tex)
        ok("tex: code block untouched (its @eq:a is not resolved)", "@eq:a" in tex)
        ok("tex: grouped [@eq:a; @eq:b] renders every number", "(1); (2)" in tex)
        ok("tex: labelled equation inside a tight list item is numbered and cited", r"\qquad (3)" in tex and "@eq:n2 cited" not in tex
           and "(3) cited" in tex)
        ok("tex: a list-like box title ('1. Find ...') stays a title", r"\begin{tbox-exercise}{1. Find the velocity}" in tex, )
        if do_pdf:
            import pymupdf
            with pymupdf.open(os.path.join(out, "st.pdf")) as pdf:   # closed before the temp dir is removed (Windows locks)
                txt = "\n".join(p.get_text() for p in pdf)
                n_img = sum(len(p.get_images()) for p in pdf)
            ok("pdf: no unresolved (??) references", "(??" not in txt)
            ok("pdf: no stray {#eq label text", "{#eq" not in txt)
            ok("pdf: both labelled equations numbered (1)(2), cross-refs resolved", "(1)" in txt and "(2)" in txt)
            ok("pdf: unicode symbols rendered", "∂" in txt or "𝜕" in txt)   # U+2202, or math-italic partial
            ok("pdf: figure embedded", n_img >= 1)
            ok("pdf: nested box text present", "inner text" in txt and "outer text" in txt)
            import shutil
            iso = os.path.join(td, "isolated"); shutil.copytree(out, iso)
            from check_env import tex_env, tex_tool
            p2 = subprocess.run([tex_tool("latexmk") or "latexmk", "-pdf", "-g", "-interaction=nonstopmode", "-halt-on-error", "st.tex"],
                                cwd=iso, env=tex_env(), capture_output=True, text=True, errors="replace")
            ok("out/ alone compiles (cwd=out, no help from the session dir): tex is portable", p2.returncode == 0)
        with zipfile.ZipFile(os.path.join(out, "st.docx")) as z:   # closed before the temp dir is removed (Windows locks)
            x = z.read("word/document.xml").decode()
            sty = z.read("word/styles.xml").decode()
            names = z.namelist()
        t = re.sub(r"<[^>]+>", "", x)
        ok("docx: no unresolved (??) / stray {#eq", "(??" not in t and "{#eq" not in t)
        ok("docx: equations are native OMML (>=4) incl. aligned block",   # pandoc < 3 writes eqArr, >= 3 a matrix
           x.count("<m:oMath>") >= 4 and ("<m:eqArr" in x or "<m:m>" in x))
        ok("docx: image, table, code, box styles present", any(n.startswith("word/media/") for n in names)
           and "<w:tbl>" in x and "SourceCode" in x and "Box-keyidea" in x)
        ok("docx: reference styles carry Box-* shading", "Box-keyidea" in sty and "<w:shd" in sty)
    if not do_pdf:
        print("NOTE  PDF checks skipped (TeX/latexmk or pymupdf missing); .md/.tex/.docx verified")
    print("ALL PASS" if all(checks) else "SELFTEST FAILED")
    sys.exit(0 if all(checks) else 1)


if __name__ == "__main__":
    main()
