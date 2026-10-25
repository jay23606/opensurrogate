#!/usr/bin/env python3
"""Regression test for the knowledge-base state machine (kb_update.py, new_session.py, new_code_module.py).

Run after ANY change to those scripts:   python kb_selftest.py      (exit 0 = ALL PASS)
Works on a throw-away KB in a temp directory; never touches a real KB.

Each check below exists because a real bug or a real failure mode showed up during development:
repeated --thread silently keeping only the last, `next` ignoring the declared next node, unbounded growth of
STATE.md, forgotten glossary write-backs, session numbering after the first session.
"""
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
results = []


def sh(script, *args):
    r = subprocess.run([sys.executable, os.path.join(HERE, script), *map(str, args)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    return r.returncode, r.stdout + r.stderr


def ok(name, cond, detail=""):
    results.append(bool(cond))
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else f"\n      {detail[:400]}"))


def rd(kb, name):
    with open(os.path.join(kb, name), encoding="utf-8") as f:
        return f.read()


def main():
    with tempfile.TemporaryDirectory() as td:
        kb = os.path.join(td, "kb")
        K = lambda *a: sh("kb_update.py", *a)

        # ---- init
        rc, out = K("init", kb, "--course", "T", "--pack", "p")
        ok("init creates the state files", rc == 0 and all(os.path.exists(os.path.join(kb, f)) for f in
           ("STATE.md", "CURRICULUM.md", "GLOSSARY.md", "SESSION_INDEX.md", "CODE_INDEX.md", "VIZ_LOG.md")), out)
        ok("init puts viz_style.py in figures_shared (portable figures)", os.path.exists(os.path.join(kb, "figures_shared", "viz_style.py")))
        with open(os.path.join(kb, "CURRICULUM.md"), "a", encoding="utf-8") as f:
            f.write("## P1\n- [ ] P1.01 | Alpha | src: a | tier: easy..medium\n- [ ] P1.02 | Beta | src: b | tier: medium-hard\n- [ ] P1.03 | Gamma | src: c | tier: hard..hardest\n")

        # ---- curriculum navigation
        rc, out = K("next", kb)
        ok("next = first open node when nothing declared", "P1.01" in out, out)
        K("set-status", kb, "P1.01", "doing", "--tiers", "easy")
        rc, out = K("next", kb)
        ok("next prefers the in-progress node", "P1.01" in out and "in progress" in out, out)
        K("set-status", kb, "P1.01", "done", "--tiers", "easy,medium")
        ok("set-status records tiers_done", "tiers_done: easy,medium" in rd(kb, "CURRICULUM.md"))

        # ---- session-done: multiple --thread, --also, declared next, skipped-node note
        rc, out = K("session-done", kb, "--num", 1, "--slug", "s1", "--title", "S1", "--node", "P1.01", "--also", "P1.02",
                    "--terms", "a,b", "--pages", 12, "--next", "P1.03", "--thread", "one", "--thread", "two")
        st = rd(kb, "STATE.md")
        ok("repeated --thread keeps ALL threads (was silently dropping)", "(S001) one" in st and "(S001) two" in st, st)
        ok("STATE 'Last session covered' lists --also nodes", "Last session covered: S001 (P1.01; also P1.02)" in st, st)
        rc, out = K("next", kb)
        ok("next honours the node declared in STATE.md", "P1.03" in out.splitlines()[0] and "declared next" in out, out)
        ok("next warns that earlier node(s) were skipped", "still open" in out and "P1.02" in out, out)

        # ---- discover / glossary duplicates
        K("discover", kb, "Delta term", "--parent", "P1.01")
        rc, out = K("discover", kb, "Delta term", "--parent", "P1.01")
        ok("discover rejects a duplicate term", "already in curriculum" in out and rd(kb, "CURRICULUM.md").count("Delta term") == 1, out)
        K("glossary-add", kb, "Widget", "--session", 1, "--def", "a thing", "--symbol", "W")
        rc, out = K("glossary-add", kb, "widget", "--session", 1, "--def", "again")
        ok("glossary-add rejects a duplicate (case-insensitive)", "already in glossary" in out and rd(kb, "GLOSSARY.md").lower().count("### widget") == 1, out)
        rc, out = K("glossary-find", kb, "thing")
        ok("glossary-find greps entries", "### Widget" in out, out)

        # ---- threads
        K("thread-add", kb, "three", "--session", 1)
        ok("thread-add appends a thread", "(S001) three" in rd(kb, "STATE.md"))
        rc, out = K("close-thread", kb, "two")
        ok("close-thread removes only the match", "(S001) two" not in rd(kb, "STATE.md") and "(S001) one" in rd(kb, "STATE.md"), out)

        # ---- session numbering and the term-registration check
        rc, sd1 = sh("new_session.py", kb, "--slug", "First!", "--title", "First", "--node", "P1.01")
        rc, sd2 = sh("new_session.py", kb, "--slug", "second", "--title", "Second", "--node", "P1.02")
        ok("new_session numbers 001 then 002 (max+1 branch)", sd1.strip().endswith("001-first") and sd2.strip().endswith("002-second"), sd1 + sd2)
        os.makedirs(os.path.join(kb, "sessions", "009-gap"))
        rc, sd3 = sh("new_session.py", kb, "--slug", "after", "--title", "After", "--node", "P1.03")
        ok("new_session continues after a numbering gap (010)", sd3.strip().endswith("010-after"), sd3)
        ok("new_session scaffolds portable figures/_common.py", os.path.exists(os.path.join(sd1.strip(), "figures", "_common.py")))
        src = os.path.join(sd1.strip(), "source.md")
        with open(src, encoding="utf-8") as f:
            t = f.read()
        t = t.replace("|      |        |                  |                  |             |",
                      "| Widget | $W$ | a thing | 3.1 | new |\n| Gadget (thing) | – | another | 3.2 | new |\n| Unknown fwd | – | later | 3.3 | fwd |")
        with open(src, "w", encoding="utf-8") as f:
            f.write(t)
        rc, out = K("check-session", kb, 1)
        ok("check-session flags unregistered new/fwd terms", rc == 1 and "Gadget" in out and "Unknown fwd" in out and "Widget" not in out.replace("Widget) ", ""), out)
        K("glossary-add", kb, "Gadget", "--session", 1, "--def", "x")
        K("discover", kb, "Unknown fwd", "--parent", "P1.01")
        rc, out = K("check-session", kb, 1)
        ok("check-session passes once terms are registered", rc == 0, out)

        # ---- code module
        rc, out = sh("new_code_module.py", kb, "--topic", "fundamentals", "--name", "mod_a", "--summary", "does a", "--session", 1)
        d = os.path.join(kb, "codes", "fundamentals", "mod_a")
        ok("new_code_module writes module, example, test, README and indexes it",
           all(os.path.exists(os.path.join(d, x)) for x in ("mod_a.py", "example_basic.py", "README.md", os.path.join("tests", "test_mod_a.py")))
           and "mod_a" in rd(kb, "CODE_INDEX.md"), out)
        rc, out = sh("new_code_module.py", kb, "--topic", "fundamentals", "--name", "mod_a", "--summary", "x", "--session", 1)
        ok("new_code_module refuses to overwrite", rc != 0, out)

        # ---- depth levels (L0 intuition .. L6 frontier)
        rc, out = K("set-level", kb, "L3")
        ok("set-level writes the learner level into STATE Position", rc == 0 and "- Learner level: L3 (college)" in rd(kb, "STATE.md"), out)
        K("set-level", kb, "L5")
        st = rd(kb, "STATE.md")
        ok("set-level replaces, never duplicates", st.count("- Learner level:") == 1 and "L5 (PhD)" in st, st)
        rc, out = K("set-level", kb, "L9")
        ok("set-level rejects an unknown level", rc != 0, out)
        rc, out = K("add-node", kb, "--title", "Motion", "--group", "Mechanics", "--tier", "easy..hard", "--level", "L0..L6", "--src", "any")
        cur = rd(kb, "CURRICULUM.md")
        ok("add-node creates the group and an auto id N001", rc == 0 and "## Mechanics\n- [ ] N001 | Motion | src: any | tier: easy..hard | level: L0..L6" in cur, out + cur)
        ok("add-node puts new groups before 'Discovered terms'", cur.index("## Mechanics") < cur.index("## Discovered terms"), cur)
        rc, out = K("add-node", kb, "--title", "Velocity", "--group", "Mechanics", "--level", "L1..L3")
        cur = rd(kb, "CURRICULUM.md")
        ok("add-node appends inside an existing group (N002 after N001)", cur.index("N001 | Motion") < cur.index("N002 | Velocity") < cur.index("## Discovered terms"), cur)
        rc, out = K("add-node", kb, "--title", "motion")
        ok("add-node rejects a duplicate title", "already in curriculum" in out and rd(kb, "CURRICULUM.md").count("| Motion |") == 1, out)
        rc, out = K("add-node", kb, "--title", "Motion (Lagrangian view)", "--group", "Mechanics", "--level", "L4..L5")
        ok("add-node accepts a spiral node that differs only by a parenthetical", "N003 | Motion (Lagrangian view)" in rd(kb, "CURRICULUM.md"), out)
        rc, out = K("add-node", kb, "--title", "Bad", "--level", "L4..L2")
        ok("add-node rejects a reversed level range", rc != 0, out)
        rc, out = K("add-node", kb, "--title", "Bad2", "--tier", "medium..impossible")
        ok("add-node rejects an unknown tier", rc != 0, out)
        rc, out = K("set-status", kb, "N001", "doing", "--levels", "L0,L1,L2")
        ok("set-status records levels_done", rc == 0 and "levels_done: L0,L1,L2" in rd(kb, "CURRICULUM.md"), out)
        rc, out = K("set-status", kb, "N001", "doing", "--levels", "L1,L2,L3")
        ok("set-status replaces levels_done (no duplicate field)", rd(kb, "CURRICULUM.md").count("levels_done") == 1, rd(kb, "CURRICULUM.md"))
        rc, out = K("set-status", kb, "N001", "doing", "--levels", "L7")
        ok("set-status rejects a bad level", rc != 0, out)
        rc, out = K("next", kb)
        ok("next shows the node's level range and the learner level", "N001" in out and "levels to teach: L0..L6" in out and "learner level: L5" in out, out)
        K("set-status", kb, "N001", "todo")
        rc, out = K("glossary-add", kb, "Velocity", "--session", 1, "--def", "rate of change of position", "--level", "L1")
        ok("glossary-add records a level", "- level: L1" in rd(kb, "GLOSSARY.md"), out)

        # ---- bug regressions
        with open(os.path.join(kb, "CURRICULUM.md"), "a", encoding="utf-8") as f:
            f.write("- [ ] P1.04 | Epsilon\n")
        rc, out = K("discover", kb, "Epsilon", "--parent", "P1.01")
        ok("discover sees a duplicate whose title is the last field", "already in curriculum" in out, out)
        rc, out = K("session-done", kb, "--num", 1, "--slug", "s1", "--title", "S1", "--node", "P1.01", "--pages", 12,
                    "--profile-note", "keep me in the profile", "--levels", "L1..L3")
        idx, st = rd(kb, "SESSION_INDEX.md"), rd(kb, "STATE.md")
        ok("session-done is idempotent (re-run replaces S001, no double count)",
           idx.count("- S001 |") == 1 and "Sessions completed: 1" in st and "Approx pages written: 12" in st, idx + st)
        ok("session-done records the levels taught", "levels: L1..L3" in idx and "levels L1..L3" in st, idx + st)
        K("session-done", kb, "--num", 1, "--slug", "s1", "--title", "S1", "--node", "P1.01", "--pages", 12,
          "--profile-note", "keep me in the profile", "--level", "L1..L3")
        st = rd(kb, "STATE.md")
        ok("session-done re-run does not duplicate the profile note; --level means depth levels",
           st.count("keep me in the profile") == 1 and "levels L1..L3" in st, st)
        rc, out = K("session-done", kb, "--num", 1, "--slug", "s1", "--title", "S1", "--node", "P1.01", "--level", "free text note")
        ok("old-style --level 'free text' fails loudly instead of being misfiled", rc != 0 and "bad level" in out, out)
        rc, out = K("add-node", kb, "--title", "Pipe", "--src", "Warsi 6.13 | p.484")
        ok("add-node rejects '|' in any field", rc != 0 and "Pipe" not in rd(kb, "CURRICULUM.md"), out)
        rc, out = K("close-thread", kb, "keep me")
        ok("close-thread never deletes Learner-profile notes", rc != 0 and "keep me in the profile" in rd(kb, "STATE.md"), out)
        K("close-thread", kb, "one"); K("close-thread", kb, "three")
        st = rd(kb, "STATE.md")
        ok("closing the last thread leaves '(none)'", "## Open threads\n(none)\n" in st, st)
        rc, out = K("glossary-find", kb, "(unbalanced")
        ok("glossary-find survives an invalid regex", rc == 0, out)
        rc, out = K("status", os.path.join(td, "nope"))
        ok("a missing KB gives a clear message, not a traceback", rc != 0 and "Traceback" not in out and "init" in out, out)

        # ---- new_session: levels in subtitle, no empty phase separator
        rc, sd4 = sh("new_session.py", kb, "--slug", "motion", "--title", 'Motion "from zero"', "--node", "N001")
        t = rd(sd4.strip(), "source.md")
        ok("new_session takes levels from the node and keeps YAML valid",
           "levels L0..L6" in t and "·  ·" not in t and 'title: "Motion \\"from zero\\""' in t, t[:400])
        ok("session template has the level and regime ladders", "## 3.6 Level ladder" in t and "## 3.7 Regime ladder" in t, t[:200])

        # ---- new_code_module: UTF-8 on Windows, name validation
        rc, out = sh("new_code_module.py", kb, "--topic", "Mechanics Basics", "--name", "kinematics",
                     "--summary", "x(t) for v ≪ c, γ ≈ 1 — Galilean limit", "--session", 1)
        d = os.path.join(kb, "codes", "mechanics_basics", "kinematics")
        ok("new_code_module writes non-ASCII summaries as UTF-8 (cp1252 crash fixed) and slugs the topic",
           rc == 0 and "γ ≈ 1" in rd(d, "kinematics.py") and "codes/mechanics_basics/kinematics" in rd(kb, "CODE_INDEX.md"), out)
        rc, out = sh("new_code_module.py", kb, "--topic", "x", "--name", "1bad-name", "--summary", "s", "--session", 1)
        ok("new_code_module rejects an invalid module name", rc != 0 and not os.path.exists(os.path.join(kb, "codes", "x")), out)

        # ---- build_session Markdown fallback (works with no pandoc / TeX)
        sdir = sd4.strip()
        with open(os.path.join(sdir, "source.md"), "w", encoding="utf-8") as f:
            f.write('---\ntitle: "B"\n---\n\n# A\n\nSee @eq:m.\n\n$$\nv = \\frac{dx}{dt}\n$$ {#eq:m}\n\n'
                    '::: {.keyidea title="Outer"}\ntext\n:::\n\n![cap](figures/f.png){width=50%}\n\n```python\nprint("@eq:none")\n```\n')
        rc, out = sh("build_session.py", sdir, "--md-only", "--stem", "b")
        ok("build_session refuses a missing figure before building", rc != 0 and "figure not found" in out, out)
        with open(os.path.join(sdir, "figures", "f.png"), "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n")
        rc, out = sh("build_session.py", sdir, "--md-only", "--stem", "b")
        md = rd(os.path.join(sdir, "out"), "b.md") if rc == 0 else ""
        ok("build_session --md-only writes numbered equations, resolved refs, boxes, copied figures",
           rc == 0 and "See (1)." in md and "\\tag{1}" in md and "> **Outer**" in md and "{#eq" not in md
           and os.path.exists(os.path.join(sdir, "out", "figures", "f.png")), out + md)
        with open(os.path.join(sdir, "source.md"), "a", encoding="utf-8") as f:
            f.write("\nAnd @eq:missing.\n\n::: warning\nopen box\n")
        rc, out = sh("build_session.py", sdir, "--md-only", "--stem", "b")
        ok("build_session flags unknown @eq refs and unclosed boxes (code blocks ignored)",
           rc != 0 and "eq:missing" in out and "never closed" in out and "eq:none" not in out, out)
        with open(os.path.join(sdir, "source.md"), "w", encoding="utf-8") as f:
            f.write("# A\n\n```markdown\n$$ y $$ {#eq:demo}\n::: {.warning}\nx\n:::\n```\n\n$$\nE = mc^2\n$$ {#eq:real}\n\nSee @eq:real and `@eq:real`.\n")
        rc, out = sh("build_session.py", sdir, "--md-only", "--stem", "c")
        md = rd(os.path.join(sdir, "out"), "c.md") if rc == 0 else ""
        ok("markdown fallback leaves code fences verbatim and numbers only real equations",
           rc == 0 and "$$ y $$ {#eq:demo}" in md and "\n::: {.warning}" in md and "\\tag{1}" in md
           and "See (1) and `@eq:real`." in md, out + md)
        with open(os.path.join(sdir, "source.md"), "w", encoding="utf-8") as f:
            f.write("# A\n\n![x](../../figures_shared/f.png)\n")
        rc, out = sh("build_session.py", sdir, "--md-only", "--stem", "d")
        ok("build_session rejects figure paths that leave the session dir", rc != 0 and "leaves the session dir" in out, out)

        # ---- second-review regressions (fresh KB so numbering is predictable)
        kb2 = os.path.join(td, "kb2")
        K("init", kb2, "--course", "T2")
        os.makedirs(os.path.join(kb2, "sessions", "999-x"))
        rc1, o1 = sh("new_session.py", kb2, "--slug", "y", "--title", "Y", "--node", "N001")
        rc2, o2 = sh("new_session.py", kb2, "--slug", "y", "--title", "Y", "--node", "N001")
        ok("new_session numbers past 999 (1000, then 1001) and never reuses a number",
           o1.strip().endswith("1000-y") and o2.strip().endswith("1001-y"), o1 + o2)
        rc, out = sh("new_session.py", kb2, "--slug", "z", "--title", "Z", "--node", "N001", "--levels", "L4..L2")
        ok("new_session rejects a reversed level range (same rule as kb_update)", rc != 0 and "lower level first" in out, out)
        rc, out = K("session-done", kb2, "--num", 1000, "--slug", "Y", "--title", "Y", "--node", "N001", "--pages", 3)
        idx, st = rd(kb2, "SESSION_INDEX.md"), rd(kb2, "STATE.md")
        ok("session-done counts 4-digit session numbers and points at the real directory",
           "Sessions completed: 1" in st and "dir: sessions/1000-y/" in idx, idx + st)
        rc, out = K("session-done", kb2, "--num", 7, "--slug", "Reynolds Decomposition", "--title", "R", "--node", "N001")
        ok("session-done slugifies --slug like new_session (no 'dir:' to a missing path)",
           "dir: sessions/007-reynolds-decomposition/" in rd(kb2, "SESSION_INDEX.md"), rd(kb2, "SESSION_INDEX.md"))
        rc, out = K("session-done", kb2, "--num", 8, "--slug", "s", "--title", "Momentum | energy", "--node", "N001")
        ok("session-done rejects '|' in --title", rc != 0 and "Momentum" not in rd(kb2, "SESSION_INDEX.md"), out)
        with open(os.path.join(kb2, "CURRICULUM.md"), "a", encoding="utf-8") as f:
            f.write("\n## Later group\n- [ ] Z1.01 | Zed\n")
        K("discover", kb2, "Torque", "--parent", "Z1.01")
        cur = rd(kb2, "CURRICULUM.md")
        ok("discover files new terms under 'Discovered terms' even when a group follows it",
           cur.index("## Discovered terms") < cur.index("| Torque |") < cur.index("## Later group"), cur)

        sdir2 = o1.strip()
        src = ("# A\n\n<!-- $$ old $$ {#eq:old} -->\n\n$$\nC = 5\\,\\text{\\$}\n$$ {#eq:c}\n\n"
               "See @eq:c and [@eq:c; @eq:d].\n\n$$ d $$ {#eq:d}\n\n"
               "::: {#w1 .warning}\nboxed\n:::\n\n::: {#plain}\nplain div\n:::\n")
        with open(os.path.join(sdir2, "source.md"), "w", encoding="utf-8") as f:
            f.write(src)
        rc, out = sh("build_session.py", sdir2, "--md-only", "--stem", "e")
        md = rd(os.path.join(sdir2, "out"), "e.md") if rc == 0 else ""
        ok("md fallback: comments take no number, \\$ inside math works, grouped refs, {#id .cls} boxes, plain divs transparent",
           rc == 0 and "See (1) and (1); (2)." in md and "\\tag{1}" in md and "\\tag{2}" in md and "old" not in md
           and "> **Watch out**" in md and "> boxed" in md and "plain div" in md and "> plain div" not in md
           and ":::" not in md, out + md)
        with open(os.path.join(sdir2, "source.md"), "w", encoding="utf-8") as f:
            f.write("# A\n\n$$ x $$ {#eq:a}.\n\nSee @eq:a.\n")
        rc, out = sh("build_session.py", sdir2, "--md-only", "--stem", "f")
        ok("validation rejects a label the Lua filter would not number (trailing punctuation)",
           rc != 0 and "not recognised" in out, out)
        with open(os.path.join(sdir2, "source.md"), "w", encoding="utf-8") as f:
            f.write("# A\n\n$v \to c$ and $\beta$\n")   # a lost backslash: \b is U+0008 (crashes pdflatex, breaks docx XML)
        rc, out = sh("build_session.py", sdir2, "--md-only", "--stem", "g")
        ok("validation rejects control characters before any format is built", rc != 0 and "U+0008" in out, out)

        # ---- growth caps over many sessions
        for i in range(2, 30):
            K("session-done", kb, "--num", i, "--slug", f"s{i}", "--title", f"T{i}", "--node", "P1.03", "--pages", 12,
              "--thread", f"q{i}", "--profile-note", f"note {i}")
        st = rd(kb, "STATE.md")
        threads = [l for l in st.split("## Learner profile")[0].split("## Open threads")[1].splitlines() if l.startswith("- (S")]
        prof = [l for l in st.split("## Learner profile")[1].splitlines() if re.match(r"- \(S\d{3}\)", l)]
        ok("open threads capped at 8 after 29 sessions", len(threads) <= 8, str(len(threads)))
        ok("auto profile notes capped at 10", len(prof) <= 10, str(len(prof)))
        ok("STATE.md stays under the 120-line cap", len(st.splitlines()) <= 120, str(len(st.splitlines())))
        ok("overflow is archived, not lost", os.path.exists(os.path.join(kb, "STATE_ARCHIVE.md")) and "q2" in rd(kb, "STATE_ARCHIVE.md"))
        rc, out = K("lint", kb)
        ok("lint exits 0 on a healthy KB", rc == 0, out)

    print("ALL PASS" if all(results) else "KB SELFTEST FAILED")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
