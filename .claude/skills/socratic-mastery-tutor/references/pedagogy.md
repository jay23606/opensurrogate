# Pedagogy: the ladder, the tiers, the depth levels, and the "Distance" standard

The learner's own brief defines the bar. Read this when planning a session or when unsure how deep to go.

## Contents
1. The seven stages, with what "done" looks like
2. The five difficulty tiers
3. The recursion rule (term tree)
4. Worked standard: "Distance" (the learner's own example)
5. Cross-topic synthesis ("combine multiple ideas")
6. Depth and pacing
7. Depth levels (L0-L6) and regime ladders

## 1. The seven stages: what "done" looks like

| Stage | You have done it when the learner can... | Typical artefact in the session |
|---|---|---|
| **Terms** | see every word used, with none left unexplained | Section 1 term table; new terms registered |
| **Remember** | recall definition, symbol, units, dimensions without looking | recall quiz + memory hook (mnemonic/picture/analogy) |
| **Understand** | reproduce the derivation and say what each term means physically | full derivation, every line justified |
| **Apply** | use it on a fresh numeric problem and in code | worked problems + runnable script + figure |
| **Analyze** | say which term dominates where, and what breaks at the limits | asymptotic/limit table, order-of-magnitude estimate, sensitivity plot |
| **Evaluate** | judge it against alternatives and in other contexts, and say when NOT to use it | comparison table, cost/accuracy, cross-discipline, philosophical/dimensional view |
| **Create** | propose something new by combining this with earlier material | 3-5 project ideas, ≥1 combining sessions, ≥1 open-source-package seed |

For first-time learners, Understand questions must follow supplied information (a starter, figure or observation),
or answers only reveal prior ideas; see `question-banks.md`.

Each stage is anchored in Proverbs or the teaching of Christ: see `wisdom-lens.md`.

Bloom's revised taxonomy is the backbone (remember → understand → apply → analyze → evaluate → create);
"Terms" is prepended because the learner's method starts by listing all terms.

## 2. The five difficulty tiers

Within a topic, in this order (a session may cover a subset, but never out of order):

1. **Easy**: a picture, an analogy, a number you can compute by hand. Why it exists at all.
2. **Medium**: precise definitions, notation, the simplest correct equation.
3. **Medium-hard**: the main derivation, done completely.
4. **Hard**: generalisation (3-D, compressible, tensor form), edge cases, what the textbook glosses over.
5. **Hardest**: the open question, the research-level connection, the place the theory is known to fail.

`tiers_done: easy,medium` on the curriculum node records progress across sessions.

**Notation.** Tier names: `easy`, `medium`, `medium-hard`, `hard`, `hardest`. In a node's `tier:` field a range is
written `a..b` (`easy..medium`, `medium-hard..hard`); a bare name is one tier, and `medium-hard` is ONE tier, not a range.
The field states what the node teaches; if it starts above `easy`, replace the lower tiers by a short recap that
links the session where they were covered (Sections 1-2 of the session are always present).

## 3. The recursion rule (term tree)

Learning is a tree search. For a term T:
1. Grep the glossary. Known → one-line reminder with a pointer to the session.
2. Unknown → define it now (2-4 lines), add to the glossary, and ask: does T's definition use terms the
   learner has not met? Recurse on those, to a depth that keeps the session moving.
3. If T deserves a full lesson, register it: `kb_update.py discover <kb> "T" --parent <NODE>`. It
   becomes a node that the tutor can schedule later.
Stop recursing when the terms are prerequisites the curriculum already covers earlier, or are plain language.

## 4. Worked standard: "Distance" (verbatim intent of the learner's example)

The learner said that if "distance" were explained like this, they would be satisfied. Use it as the
yardstick for breadth *and* depth of any topic:

- **Disambiguate neighbours**: distance vs displacement (scalar path length vs vector change of position).
- **Scale ladder** with the formula/method that applies at each scale: light-years (stellar parallax,
  standard candles), planetary (radar ranging, Kepler), human (rulers, GPS/time-of-flight), micro
  (interferometry), atomic (X-ray diffraction, Bragg's law, bond lengths), down to ~0.001 nm (electron
  scattering, spectroscopy). Say how two stars' distance is found and how two atoms' distance is found.
- **Combine with change** to build the next concepts: distance + time → velocity → acceleration (jerk...).
- **Cross-disciplinary meaning**: metric spaces in mathematics, distance measures in statistics/ML
  (Euclidean, Mahalanobis, KL as a non-metric), philosophical "distance" (space, separation, aesthetic
  distance), everyday idioms.
- **New terms discovered on the way get their own explanation** (parallax, metric, geodesic, ...): the
  recursive tree.
- **Order**: easy → medium → medium-hard → hard → hardest; each part reads like a document with code.
- **Code**: compute and plot each scale; every concept has a figure.
- **Level view** (depth-levels.md): L0 "how far away" → L1 metres, kilometres, a map scale → L2 displacement vectors,
  Pythagoras in 3-D → L3 arc length $\int |\mathbf r'(t)|\,dt$, metric spaces → L4 the metric tensor
  $ds^2 = g_{ij}dx^i dx^j$, geodesics → L5 the spacetime interval, proper distance in an expanding universe
  (comoving vs luminosity distance) → L6 is distance meaningful below the Planck length?

Translate this to any subject by asking, for topic X: *What are its neighbours and look-alikes? What is
its scale ladder? What does it combine with to give the next concept? Where else is X used, including
non-technical senses? Which unfamiliar terms does explaining X drag in? What does X look like at each depth
level L0-L6, and in which regime does it stop being true?*

## 5. Cross-topic synthesis

The learner wants to "combine multiple ideas to create something good". In the Create section:
- name the earlier sessions used (e.g. "S003 spectra + S007 wall functions");
- say what the combination yields that neither has alone;
- give a first concrete step (a function, an experiment, a plot) small enough to start tomorrow;
- flag the ones that belong in the eventual open-source package.

## 6. Depth and pacing

- Target 10-20 pages per session, i.e. roughly one focused topic through 2-3 tiers. Longer is fine when
  the derivation needs it; shorter means a stage was skipped.
- "Fast pace" means no padding and no repeated explanations, **not** skipped algebra.
- The learner will interrupt with questions on what they do not understand. Answer at the depth of that
  question, record it in `notes.md`, then return to the plan. Repeated confusion → update the Learner
  profile in STATE.md.

## 7. Depth levels (L0-L6) and regime ladders

Full method and two worked examples ("Motion" at every level and through its regimes) in `depth-levels.md`. In short:
- **Levels**: L0 intuition · L1 school · L2 advanced school · L3 college · L4 master's · L5 PhD · L6 frontier. A session
  teaches a level *range* (the node's `level:` field, defaulting to the learner level in STATE). All seven stages and the
  tier order apply inside that range.
- **Section 3.6** (level ladder) shows the whole staircase, one line per level, each true at its level and naming what
  the next level corrects. **Section 3.7** (regime ladder) pushes each governing parameter to its extremes, names the
  dimensionless signal and the theory that takes over, with a breakdown figure.
- Lower levels simplify but never lie; above L4 every claim is cited; L6 claims are labelled settled / mainstream /
  speculative.
- The learner climbs a level when they solve the hard/hardest exercises at the current level unaided
  (`kb_update.py set-level`); a learner's explicit request ("explain at PhD level") wins for that explanation.
