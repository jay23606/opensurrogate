# Authoring a session that builds cleanly

`source.md` → pandoc → `.tex` and `.docx`, and `.tex` → `.pdf`. These conventions were verified on a
fixture (multi-line derivation, figures, table, code, boxes) and everything survived in all three outputs.

## Contents
1. Front matter and structure
2. Math
3. Boxes
4. Figures
5. Tables
6. Code listings
7. Things that silently break
8. Page-count and quality checks

## 1. Front matter and structure
`new_session.py` writes the YAML front matter (title, subtitle with node and depth levels, author, date) and the eleven
mandatory H1 sections from `assets/session_template.md`, including Section 3.6 (level ladder) and 3.7 (regime ladder). Keep the headings and order. The wisdom lens (references/wisdom-lens.md) shows up in two places only: an optional cited KJV verse line at the top of Section 1 (book chapter:verse), and a **Discernment** paragraph closing Section 6. Sub-sections use `##`/`###`.
Headings are **not** auto-numbered: the numbers typed in the template (`# 3. Understand`, `## 3.2 Tier 2 ...`) are the only ones, and identical in the .tex, .pdf and .docx. Cross-refer to them as "Section 5". (Auto-numbering was tried and removed: it collided with the typed numbers and does not exist in the .docx.)

## 2. Math
- Inline `$...$`; display `$$...$$`. Multi-line derivations: `$$ \begin{aligned} a &= b \\ &= c \end{aligned} $$`.
- **Do not** use raw `\begin{align}`: it renders in the PDF but is **dropped from the .docx** (tested). Use
  `aligned` inside `$$`. Prefer plain LaTeX (`\overline{u_i' u_j'}`, `\frac{\partial}{\partial x_j}`).
- Macros: `\newcommand` written **inside source.md** works in both outputs (pandoc expands it, tested).
  A macro defined in `assets/preamble.tex` would exist only in the PDF, so never put math macros there.
- Number a display equation by appending a label after the closing `$$`:
  `$$ ... $$ {#eq:rans}` and cite it as `@eq:rans` → renders `(1)` in both formats. Numbers count in
  document order per session. A cite of an unknown label shows `(??eq:name)`, a visible signal.
- Chain each aligned line to the previous one by a stated rule; say the rule in prose or `&&\text{(by ...)}`.
- Verify non-trivial algebra with sympy before writing it down.

## 2b. Figure scripts and the self-contained `out/`
`new_session.py` scaffolds `figures/_common.py`. Start every figure script with `from _common import *` (gives `np`, `plt`,
`PAL`, `FIG`, `save`, `out`, `use_code`); call `use_code("<topic>/<module>")` to import a module from `codes/`. The style
comes from `<KB>/figures_shared/viz_style.py` (copied there by `init`/`new_session`), so nothing depends on where a skill
is installed. `build_session.py` copies every figure the `.tex` references into `out/figures/`, so **`out/` alone is a
complete LaTeX project** (drop it into Overleaf); the selftest compiles an isolated copy to prove it.

## 3. Boxes (pedagogical roles)
```
::: {.definition title="Reynolds decomposition"}
text and $math$
:::
```
Classes: `definition`, `keyidea`, `warning`, `exercise`, `create`, `term`. Title optional (defaults to the
class name). Boxes must not nest. Rendered as coloured tcolorbox in PDF and shaded `Box-*` styles in .docx.

## 4. Figures
`![Caption: what to look at and what it proves.](figures/fig03_spectrum.png){width=85%}`
- The figure script lives next to the PNG (`figures/fig03_spectrum.py`) and uses `assets/viz_style.py`.
- Caption = what to look at + what it proves. Labelled axes with units. Colour-blind-safe palette.
- Save at dpi 200; width 70-90% for single plots.

## 5. Tables
Pipe tables. Add a caption line beneath: `Table: caption text`. Keep ≤ 6 columns (wider tables overflow the PDF).
Right-align numeric columns with `---:`.

## 6. Code listings
Fenced blocks with a language (```` ```python ````). Keep snippets ≤ 25 lines; the full version lives in
`codes/` with its README, and the session points to it by path.

## 7. Things that silently break
| Mistake | Effect | Fix |
|---|---|---|
| `\newcommand` in `preamble.tex` | macro missing in .docx | define it inside source.md or use plain math |
| `\begin{align}` raw | dropped in .docx | `aligned` inside `$$` |
| Nested `:::` boxes | works in both (tested), but reads busy | avoid unless needed |
| Figure path not relative to session dir | LaTeX "file not found" | `figures/x.png` |
| Blank line missing before/after `$$` or a list | text merges | add blank lines |
| `%` or `&` outside math in prose | fine in Markdown; pandoc escapes | nothing to do |
| Very wide table | overflows margin | fewer columns / split |
| Unicode symbols (∂, ε, κ, ≈, ...) | 92 common ones are mapped in `preamble.tex` and are fine in prose and math. An UNMAPPED non-ASCII character would crash pdflatex, so `build_session.py` scans first and names the character and line | write it as LaTeX math or add it to the `newunicodechar` map |

## 8. Page-count and quality checks
- `build_session.py` validates first (missing figure files, `@eq:` references without a label, duplicate labels,
  unbalanced `:::`), then builds every format the machine supports. `out/<stem>.md` is always written (numbered
  equations via `	ag{n}`, boxes as titled quotes); without pandoc that is the deliverable, and the build says what
  was skipped and how to install it.
- `build_session.py` prints the PDF page count; target 10-20. Below 10, a ladder stage is probably thin.
- Render pages 1 and a mid page to PNG and look at them (`pymupdf`: `page.get_pixmap(dpi=80).save(...)`).
- `.docx` is usually not renderable headlessly; verify structurally: equations
  (`<m:oMath>` count), images (`word/media/`), tables, styles. Tell the learner to open it in Word once.
- Every number and figure in the text must come from code you ran. Re-run figure scripts before the final build.
