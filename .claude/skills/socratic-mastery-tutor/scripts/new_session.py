#!/usr/bin/env python3
"""Scaffold sessions/NNN-slug/ with source.md from the canonical template.

    new_session.py <kb_root> --slug reynolds-decomposition --title "Reynolds decomposition" --node P1.03
                   [--levels L2..L4] [--phase "Phase 1"] [--author "Tutor"]

NNN is the next free number (max existing + 1), so numbering never collides across fresh sessions.
--levels is the depth-level range this session teaches (L0 intuition ... L6 frontier; see references/depth-levels.md);
when omitted it is taken from the node's `level:` field in CURRICULUM.md, else from STATE.md's Learner level.
"""
import argparse
import datetime as dt
import os
import re
import shutil
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.normpath(os.path.join(HERE, "..", "assets"))
sys.path.insert(0, HERE)
from kb_update import NODE_RE, check_level, fields, learner_level, slugify  # noqa: E402  (one rule set, no drift)


def _read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def default_levels(kb, node):
    for line in _read(os.path.join(kb, "CURRICULUM.md")).splitlines():
        m = NODE_RE.match(line)
        if m and m["id"] == node and fields(m["rest"]).get("level"):
            return fields(m["rest"])["level"]
    return learner_level(kb) or ""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("kb")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--node", required=True)
    ap.add_argument("--levels", default=None, help="depth levels taught, e.g. L1..L3")
    ap.add_argument("--phase", default="")
    ap.add_argument("--author", default="Socratic Mastery Tutor")
    a = ap.parse_args()

    if not os.path.exists(os.path.join(a.kb, "STATE.md")):
        sys.exit(f"{a.kb} has no STATE.md: create the knowledge base first with `kb_update.py init {a.kb} --course NAME`")
    levels = a.levels if a.levels is not None else default_levels(a.kb, a.node)
    check_level(levels)   # same validation as kb_update (format and lower-first range)
    slug = slugify(a.slug)
    if not slug:
        sys.exit("--slug must contain at least one letter or digit")

    root = os.path.join(a.kb, "sessions")
    os.makedirs(root, exist_ok=True)
    nums = [int(m.group(1)) for d in os.listdir(root) if (m := re.match(r"(\d{3,})-", d))]   # 001 ... 999, 1000 ...
    n = (max(nums) + 1) if nums else 1
    sd = os.path.join(root, f"{n:03d}-{slug}")
    if os.path.exists(sd):   # never overwrite an authored session
        sys.exit(f"{sd} already exists; refusing to overwrite")
    for sub in ("figures", "out"):
        os.makedirs(os.path.join(sd, sub))
    with open(os.path.join(ASSETS, "session_template.md"), encoding="utf-8") as f:
        t = f.read()
    subtitle = " · ".join(x for x in (f"Session {n:03d}", a.phase.strip(), f"curriculum node {a.node}",
                                      f"levels {levels}" if levels else "") if x)
    def yq(s):   # escape for a YAML double-quoted string
        return s.replace("\\", "\\\\").replace('"', '\\"')

    for k, v in {"{{TITLE}}": yq(a.title), "{{SUBTITLE}}": yq(subtitle), "{{AUTHOR}}": yq(a.author),
                 "{{DATE}}": dt.date.today().isoformat(), "{{LEVELS}}": levels or "(set the levels this session teaches)"}.items():
        t = t.replace(k, v)
    with open(os.path.join(sd, "source.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(t)
    shutil.copy2(os.path.join(ASSETS, "figure_common_template.py"), os.path.join(sd, "figures", "_common.py"))
    fs = os.path.join(a.kb, "figures_shared")
    os.makedirs(fs, exist_ok=True)
    if not os.path.exists(os.path.join(fs, "viz_style.py")):
        shutil.copy2(os.path.join(ASSETS, "viz_style.py"), os.path.join(fs, "viz_style.py"))
    with open(os.path.join(sd, "notes.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# Session {n:03d} notes: learner questions and answers\n\n(Append each question the learner asks, with the "
                "answer and the depth level it was answered at, so later sessions can see what confused them.)\n")
    print(sd)


if __name__ == "__main__":
    main()
