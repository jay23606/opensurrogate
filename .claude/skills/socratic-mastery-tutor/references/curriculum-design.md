# Designing a curriculum for any subject (no domain pack needed)

A domain pack is optional. When the learner says "teach me X" and no pack exists, the tutor builds the
curriculum itself, records it with `kb_update.py add-node`, and grows it with `discover` as new terms appear.
Read this once per new course.

## Contents
1. Interview (2 minutes)
2. Build the term tree
3. Order, group, and size the nodes
4. Assign tier and level ranges
5. Write it with the scripts
6. Sources and the literature map
7. Optional: turn it into a reusable domain pack

## 1. Interview (2 minutes, then start)
Ask at most three questions, then proceed with sensible defaults:
- **Goal**: why X? (exam, research, job, curiosity) → decides the top level to reach (L3 for most professional use,
  L5-L6 for research).
- **Starting point**: one diagnostic question per depth-levels.md §8 → the learner level.
- **Format and pace**: full documents (.pdf/.docx) or Markdown only; sessions per week.
Save the brief verbatim to `<kb>/ROLE.txt` (never edited later) and set the level: `kb_update.py set-level <kb> L2`.

Wisdom check (references/wisdom-lens.md): count the cost before building (Luke 14:28), so state the top level and
the number of sessions; start at the learner's measure (Mark 4:33); make Phase 1 a **parable phase**: concrete,
everyday, picture-first nodes before any formalism (Matt 13:34); every phase ends with a node where the learner
teaches it back or creates something (Luke 6:40).

## 2. Build the term tree
1. Write the subject's **core question** in one line ("How do things move and why?").
2. List the **10-20 load-bearing concepts** an expert would name (for mechanics: position, velocity, acceleration,
   force, mass, momentum, energy, work, rotation, oscillation, gravitation, frames, action, phase space, relativity).
3. For each concept, list the **terms its definition uses**; each unknown one is a prerequisite (the recursion rule).
4. Add the **cross-cutting skills** the subject needs (for physics: vectors, derivatives, integrals, ODEs, numerical
   integration, dimensional analysis). They become early nodes or "refresher" nodes.
5. Add one **regime / frontier** node per major theory boundary (Newton → relativity, classical → quantum).

## 3. Order, group, and size the nodes
- **Order** = a topological sort of the prerequisite graph; ties broken by "most useful soonest".
- **Groups** = `## Phase N: title` headings of 5-12 nodes each (the learner's mental chapters).
- **Size** = one node ≈ one session of 10-20 pages at the session's level range. Split a node that would need three
  sessions; merge two tiny adjacent nodes (or teach them together with `session-done --also`).
- Seed **20-40 nodes**, not 200. The tree grows by `discover` as teaching reveals what the learner actually lacks.

## 4. Assign tier and level ranges
- `tier:` the difficulty span the node covers (`easy..medium` for foundations, `medium-hard..hardest` for advanced).
- `level:` the depth span (depth-levels.md). A foundational concept taught to an L3 learner might be `L1..L3`
  (recap L1, teach L2-L3); a concept you plan to revisit at higher depth later gets a second node
  ("Motion II: Lagrangian view", `level: L4..L5`) rather than an endless single node.
- **Spiral**: big ideas appear several times at rising levels. Mark the later node's prerequisite with `prereq:`.

## 5. Write it with the scripts (never hand-edit the line format)
```
kb_update.py init <kb> --course "Classical to modern mechanics" --learner-level L2
kb_update.py add-node <kb> --group "Phase 1: Describing motion" --title "Position and displacement" --tier easy..medium --level L1..L2
kb_update.py add-node <kb> --group "Phase 1: Describing motion" --title "Velocity and speed" --tier easy..medium-hard --level L1..L3 --prereq N001
kb_update.py add-node <kb> --group "Phase 4: Beyond Newton" --title "Motion near the speed of light" --tier medium..hardest --level L2..L5 --src "Taylor & Wheeler, Spacetime Physics, ch. 1"
kb_update.py lint <kb>
```
Ids are auto-assigned (`N001`, `N002`, ...) unless you pass `--id P1.03`. A pack-seeded curriculum keeps the pack's ids.

## 6. Sources and the literature map
For each group, name 1-3 standard sources **per level band** (a school text for L1-L2, an undergraduate text for L3,
a graduate text for L4, reviews/papers for L5-L6) in `--src` or in `<kb>/literature/README.md`. Only cite what you
can name precisely (author, title, chapter/section); if unsure, say "standard undergraduate texts" rather than invent
a reference. Put PDFs the learner supplies in `<kb>/literature/`.

## 7. Optional: turn it into a reusable domain pack
When a course proves useful, freeze it as a pack: a skill folder whose SKILL.md says "use socratic-mastery-tutor" and
names the KB root, plus `references/curriculum-spine.md` (the node lines), `literature-map.md`, `notation.md`,
`<domain>-visualization.md`, `canonical-results.md` (benchmark numbers with sources), and the learner's brief.
