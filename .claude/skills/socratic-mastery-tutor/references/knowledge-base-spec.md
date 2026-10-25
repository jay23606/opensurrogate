# Knowledge-base specification

Exact layout and line formats. The scripts in `scripts/` read and write these formats; a future
session with no memory can rely on them. Change a format only by changing the script and this file together.

```
<kb>/
├── STATE.md            always read first; ≤120 lines (enforced)
├── STATE_ARCHIVE.md    overflow of old threads / profile notes (write-only log)
├── CURRICULUM.md       term tree, one node per line
├── GLOSSARY.md         grow-only, GREP ONLY
├── SESSION_INDEX.md    one line per session
├── CODE_INDEX.md       one line per code module
├── VIZ_LOG.md          one line per chart type taught
├── ROLE.txt            the learner's original brief (never edit)
├── literature/         the learner's reference material + README.md literature map (older KBs may use another
│                       folder name, e.g. "litearture"; never rename an existing one)
├── figures_shared/     viz_style.py copied from the engine, so figures never depend on the skill's install path
├── sessions/NNN-slug/  source.md, notes.md, figures/, out/
└── codes/<topic>/<module>/  <module>.py, example_*.py, tests/, README.md   (topic = short slug; reuse existing ones, `ls codes/`)
```

## STATE.md
Sections (fixed): header block, `## Position` (`Sessions completed`, `Approx pages written`, `Last session covered`, `Next node`, `Learner level`), `## Recent sessions` (newest first, max 3),
`## Open threads` (max 8; each line `- (S007) text`), `## Learner profile` (hand-edited; auto notes are
`- (S007) text`, max 10 kept). Written by `kb_update.py session-done`, `thread-add`, `close-thread`. `kb_update.py next` prefers the `- Next node:` line of Position (when that node is still open) over curriculum file order. Overflow moves to
STATE_ARCHIVE.md. `- Learner level: L3 (college)` is written by `kb_update.py set-level` (inserted into Position on older KBs).
`close-thread` only touches the Open threads block; an empty block reads `(none)`.

## CURRICULUM.md node line
```
- [ ] P1.03 | Reynolds decomposition | src: Warsi 6.13 p.484 | tier: easy..medium | level: L3..L4 | tiers_done: easy | levels_done: L3
```
- marker: `[ ]` todo, `[~]` doing, `[x]` done
- id: capital letters + dotted numbers (`P1.03`, `P2.10a`); `add-node` without `--id` assigns `N001`, `N002`, ...;
  discovered terms are `D001`, `D002`, ...
- fields after the title are free `key: value` segments separated by ` | `
- `tier:` is one tier name (`easy`, `medium`, `medium-hard`, `hard`, `hardest`) or a range `a..b`; `tiers_done:` is a comma list.
  `medium-hard` is ONE tier.
- `level:` is one depth level `L0`..`L6` or a range `L1..L3` (lower first); `levels_done:` is a comma list
  (`L1,L2`). See depth-levels.md. Optional `prereq:` lists node ids. `lint` validates all four fields.
- Groups are markdown `##` headings; nodes appear in teaching order. `add-node --group G` appends to group G (creating
  it before `## Discovered terms`). `kb_update.py next` returns the first `[~]` node, else the declared Next node,
  else the first `[ ]`, and prints the node's level range and the learner level.

## GLOSSARY.md entry
```
### Reynolds stress
- symbol: -rho <u_i' u_j'>
- definition: momentum flux due to velocity fluctuations
- level: L4            (optional: the depth level the definition is written at)
- introduced: session 001
- see also: closure problem; eddy viscosity
```
Headings are unique (case-insensitive). Look up with `kb_update.py glossary-find <kb> "<regex>"`.

## SESSION_INDEX.md line
`- S001 | 2026-09-21 | Title | node P1.01 | ~14 pp | levels: L2..L3 | terms: a,b,c | dir: sessions/001-slug/`
(`levels:` only when `session-done --levels` is given). Re-running `session-done` for the same number replaces the line.

## CODE_INDEX.md line
`- name | codes/topic/name | S001 | summary | README: codes/topic/name/README.md`

## VIZ_LOG.md line
`- parity plot | S004 | used for: model vs DNS comparison`

## Session directory
`source.md` (canonical), `notes.md` (learner Q&A), `figures/figNN_name.png` + `figNN_name.py`,
`out/<dir-name>.{md,tex,pdf,docx}` (`.md` always; the others when the toolchain exists, see `check_env.py`). `NNN` = highest existing + 1, zero-padded to three digits.

## Per-code-module README
From `assets/CODE_README_template.md`: purpose, capabilities, theory, quick start, examples, units,
validation, limits, dependencies, path toward the open-source package.
