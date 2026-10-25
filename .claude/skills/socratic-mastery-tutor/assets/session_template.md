---
title: "{{TITLE}}"
subtitle: "{{SUBTITLE}}"
author: "{{AUTHOR}}"
date: "{{DATE}}"
---

<!--
CANONICAL SESSION SKELETON. Keep every H1 heading and its order: the learner navigates every session
the same way, and a fresh AI session rebuilds this format from this file alone.
Delete these comments and the "(guidance)" lines as you fill sections in. Target 10-20 pages.
Math: plain LaTeX in $...$ / $$...$$; use aligned (not raw align: dropped from .docx); any \newcommand goes inside this file.
Multi-line derivations: $$ \begin{aligned} ... \end{aligned} $$ ; label with  {#eq:name}  after the $$
and cite in prose as @eq:name. Boxes: ::: {.definition title="..."} ... :::  (definition, keyidea,
warning, exercise, create, term). Figures: ![caption](figures/figNN_name.png){width=85%}.
-->

# Session map

::: {.keyidea title="Outcome of this session"}
After this session you can: (state 3-5 concrete, testable abilities, e.g. "derive X from Y", "reproduce Fig. 3 from scratch").
:::

- **Prerequisites:** (nodes/sessions; link by session number)
- **Depth levels taught:** {{LEVELS}}  (L0 intuition · L1 school · L2 advanced school · L3 college · L4 master's · L5 PhD · L6 frontier; levels below the range get a 3-line recap)
- **Difficulty ladder used:** easy → medium → medium-hard → hard → hardest (say which tiers this session covers)
- **Deliverables:** this document (.md always; .tex/.pdf/.docx when the toolchain exists), N figures, code module(s) `codes/...` with README
- **Source anchors:** (book + section + page for every claim that comes from the literature)

# 1. Terms: the term tree

(guidance) Optionally open with ONE cited verse (KJV, from references/wisdom-lens.md) that fits this session's
theme, as a single italic line; skip it if the learner asked for a secular course. Hear before answering
(Prov 18:13): state what the learner already knows before teaching.
List EVERY term that appears in this session, including ones hidden inside definitions.
Mark each **new** or **known** (grep the glossary first). New terms discovered while explaining another
term become child nodes: say so, and register them with `kb_update.py discover`.

| Term | Symbol | One-line meaning | Where it appears | New / known |
|:-----|:------:|:-----------------|:-----------------|:-----------:|
|      |        |                  |                  |             |

# 2. Remember

(guidance) Definitions, symbols, units, dimensions, index notation. Give a memory hook for each cluster
(mnemonic, picture, or analogy). End with a 5-item recall quiz whose answers are in Section 10.

# 3. Understand: the derivation

(guidance) Full derivation, NO skipped algebra: every line follows from the previous by a stated rule.
After each equation say what each term means physically. Layer it by difficulty tier; a session may
cover only some tiers, but the tiers it covers appear in this order.

## 3.1 Tier 1 (easy): intuition and a picture

## 3.2 Tier 2 (medium): the definitions made precise

## 3.3 Tier 3 (medium-hard): the main derivation

## 3.4 Tier 4 (hard): generalisation, edge cases, what the textbook glosses over

## 3.5 Tier 5 (hardest): the open question or research-level connection

## 3.6 Level ladder: the same idea from intuition to the frontier

(guidance) One row per depth level (references/depth-levels.md). Teach the levels in this session's range in full
above; give every other level one line so the learner sees the whole staircase and where they stand. Each row must
be TRUE at its level (a simplification, never a falsehood) and say what the next level adds or corrects.

| Level | Audience | The idea at this level | Key equation / tool | What the next level corrects |
|:------|:---------|:-----------------------|:--------------------|:-----------------------------|
| L0 | intuition |  |  |  |
| L1 | school |  |  |  |
| L2 | advanced school |  |  |  |
| L3 | college |  |  |  |
| L4 | master's |  |  |  |
| L5 | PhD |  |  |  |
| L6 | frontier |  |  |  |

## 3.7 Regime ladder: push every parameter to its extremes

(guidance) For each governing parameter (speed, size, energy, gravity, number of particles, time, temperature ...),
name the dimensionless number that signals a regime change, what happens there, and which theory takes over
(e.g. v/c → 1: Newton → special relativity). Add a figure that shows the breakdown (old vs new prediction).

| Parameter | Regime | Signal (dimensionless number) | What changes | Theory that takes over |
|:----------|:-------|:------------------------------|:-------------|:-----------------------|
|           |        |                               |              |                        |

# 4. Apply

(guidance) Worked problems with numbers, then code. Nothing is taught without a figure. Every figure gets:
what to look at, what it proves, what would look different if the theory were wrong.

## 4.1 Worked problem(s)

## 4.2 Code and figures

```python
# minimal, runnable snippet; full version lives in codes/<topic>/<module>/
```

![Caption saying what to look at.](figures/fig01_name.png){width=85%}

# 5. Analyze

(guidance) Limits and asymptotics, order-of-magnitude estimates, which term dominates where, what breaks
and why, sensitivity to assumptions. Include a table or plot that makes the dominance visible.

# 6. Evaluate

(guidance) Judge the idea in several contexts: compare with alternative models/methods, other scales or
disciplines, cost vs accuracy, and (as the learner asked) the wider intellectual context, e.g. the
philosophy of the concept, dimensional-analysis view, historical dispute. State when NOT to use it.
End with a short **Discernment** paragraph: which claim here would "the simple" believe at once, and how the prudent
check it (Prov 14:15); hear the other side (Prov 18:17).

# 7. Create

::: {.create title="What you can build from this"}
3-5 concrete project ideas, at least one that COMBINES this session with earlier sessions
(name them), and one that could become a module of the eventual open-source package.
:::

# 8. Visualization lesson

(guidance) The learner must learn the charts themselves, not only the physics. For every chart type used:
name and synonyms, what data shape it suits, how to read it, how it can mislead, and the matplotlib
call. Use the same Bloom ladder (remember → create). Log each in VIZ_LOG via `kb_update.py viz-add`.

| Chart type | Best for | How it misleads | matplotlib call |
|:-----------|:---------|:----------------|:----------------|
|            |          |                 |                 |

# 9. Problem set

::: {.exercise title="Graded exercises"}
1. (easy) …
2. (medium) …
3. (medium-hard) …
4. (hard) …
5. (hardest) …
:::

# 10. Retrieval practice and recap

- Answers to the Section 2 recall quiz.
- Three "explain it to a friend" prompts.
- What to re-derive by hand tomorrow without looking (spaced retrieval).

# 11. Where next

- Next curriculum node(s) and why they follow.
- Terms discovered here but not yet taught (they are now in CURRICULUM.md).
- Open threads for the learner to bring back.
