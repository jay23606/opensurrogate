# Mode 3: single-level question bank (worksheet for first-time learners)

Use when the user asks for "questions at Bloom level N", a "worksheet", a "question bank", "why questions", or
material "for beginners / students seeing this for the first time". Output: one PDF (plus the .md source), no KB.
Worked example: *Reflection of light, Level 2 Understand, 42 why-questions* (see §9).

## Contents
1. Principle: supply the information before asking
2. Bank, not test
3. Words first (the Terms stage for beginners)
4. Starters, figures and groups
5. Writing the questions (Level 2 verbs and stems)
6. Scaffolds for answering
7. Misconception group
8. Teacher key
9. Quality checklist and worked example
10. Build

## 1. Principle: supply the information before asking

An *Understand* question asks the learner to explain information they have **just met**. If nothing has been
supplied, answers reveal prior ideas, not understanding. So every question must be answerable from a **starter**
(a short supplied explanation), a **figure**, or a **described observation** printed in the worksheet. If a
question needs a fact that appears nowhere above it, add the fact to a starter or drop the question.

## 2. Bank, not test

State in the teacher note that the sheet is a bank of alternative prompts: the teacher picks a few at a time. The
lettered groups organise the topic; they are **not** separate Bloom levels. All questions sit at the one level
the sheet declares.

## 3. Words first (the Terms stage for beginners)

The skill's first stage is Terms: never leave a word standing unexplained. For a beginner sheet this becomes a
**Words we use** table placed before the starters. For each word:

| Column | What it holds |
|---|---|
| Word | the term as the questions use it |
| Plain meaning | one sentence a newcomer can use; true at this level, never false |
| Everyday vs subject sense | when the everyday meaning differs (e.g. "reflection" = my image, or "to think back") |
| Origin | only when it helps memory (Latin *re-* "back" + *flectere* "to bend") ; check an etymology source |
| Not the same as | the look-alike a beginner confuses it with (image vs object, source vs reflector) |

Every word in the table must be used later; every subject word used later must be in the table (recursion rule).

## 4. Starters, figures and groups

- A **starter** is 3-6 sentences, one idea cluster, plain language, defines the new term in bold on first use.
- Do not state something false to simplify (e.g. "a mirror sends back all light"): say what the rest does
  (absorbed, passed through).
- A **figure** carries: a caption saying what is simplified or not to scale; colour meaning **also given in words**;
  arrows for direction only; a drawing obeys the physics it shows (e.g. equal angles about the normal).
- Groups of about 6 questions, each preceded by its starter. Order from the new word -> a path -> a comparison ->
  an observation -> familiar cases -> misconceptions.

## 5. Writing the questions

Level 2 (Understand) verbs: interpret, exemplify, classify, summarise, infer, compare, explain. Stems for
"Why" banks: *Why can... / Why does... / Why do... / Why is... / Why would... / Why can we not... / Why is this an
example of...* Use natural grammar ("Why can we not see..." not "Why cannot we see...").

One idea per question. Vary the stem inside a group. Include a few "would" questions (what would happen if...)
that are still answerable from the starter.

## 6. Scaffolds for answering

Invite "Because...", point-and-explain on the figure, explaining aloud before writing, and the evidence frame
"When the torch..., the light..., so...". Accept everyday language ("light comes back"). Do not require exact
wording: a copied sentence is weaker evidence than an explanation linked to the case.

## 7. Misconception group

Final group: each question names a common mistaken idea and asks why it does not fit the starters. Typical for
physics: eyes send out light; only mirrors reflect; every reflecting surface gives a clear image; the mirror
makes its own light. Collect the real misconceptions of the topic from a source, do not invent them.

## 8. Teacher key

After the questions, a key: a 1-2 sentence model answer per question, and for the misconception group the common
wrong answer plus one follow-up probe. Model answers use only what the starters supplied.

## 9. Quality checklist and worked example

- No circular question ("Why does the picture show X?" answered by "because it is drawn").
- Each question answerable from supplied material (§1); one idea per question; natural grammar.
- Facts checked against a cited source that was read, not quoted from memory; etymology checked.
- Counts in the title match the content (N questions, M diagrams).
- Words table complete both ways (§3).

Worked example (reflection of light): 6 starters + Words table, 42 questions in groups A-G, 5 figures, teacher key;
sources OpenStax *Physics* §16.1 and University of Vermont on Bloom's taxonomy.

## 10. Build

Write `source.md` from `assets/worksheet_template.md`, figures as PNG next to it, then
`python $ENGINE/scripts/build_worksheet.py source.md -o out.pdf`. It uses pandoc -> HTML (`assets/worksheet.css`)
-> headless Edge/Chrome print-to-PDF; no TeX needed. Render pages to PNG and look at them before handing over.
