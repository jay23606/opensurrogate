#!/usr/bin/env python3
"""Knowledge-base state machine. The ONLY sanctioned way to change STATE / CURRICULUM / indices,
so their formats stay machine-readable across 100+ sessions and any fresh AI session can resume.
Standard library only: works on any machine with Python 3.8+.

    kb_update.py init <kb> --course "Name" [--engine socratic-mastery-tutor] [--pack NAME] [--learner-level L3]
    kb_update.py status <kb>                       # print STATE.md (the resume read)
    kb_update.py next <kb>                         # next curriculum node to teach
    kb_update.py add-node <kb> --title T [--group G] [--id ID] [--tier easy..medium] [--level L1..L3] [--src "..."] [--prereq "N001,N002"]
    kb_update.py set-status <kb> <NODE_ID> <todo|doing|done> [--tiers easy,medium] [--levels L1,L2]
    kb_update.py set-level <kb> <L0..L6>           # the learner's current default depth level
    kb_update.py discover <kb> "<term>" --parent <NODE_ID> [--note "why it matters"] [--level L2..L4]
    kb_update.py glossary-add <kb> "<term>" --session N [--symbol S] --def "..." [--see "a; b"] [--level L3]
    kb_update.py glossary-find <kb> "<regex>"      # grep the glossary (never read it whole)
    kb_update.py session-done <kb> --num N --slug S --title T --node ID --terms "a,b" --pages P
                                   [--next ID] [--also "P3.01,P3.02"] [--levels L1..L3]
                                   [--thread "q1" [--thread "q2" ...]] [--profile-note "note"]
    kb_update.py thread-add <kb> "<open question>" --session N
    kb_update.py close-thread <kb> "<substring of the thread>"   # when the learner resolves it
    kb_update.py code-add <kb> --path codes/x/y --name N --summary "..." --session N
    kb_update.py viz-add  <kb> --chart "parity plot" --session N --used-for "..."
    kb_update.py check-session <kb> <NNN>          # every term marked new/fwd in the session is registered
    kb_update.py lint <kb>                         # size caps + format checks

Curriculum line format (one node per line, greppable):
    - [ ] P1.03 | Reynolds decomposition | src: Warsi 6.13 p.484 | tier: easy..medium | level: L2..L4
    marker  [ ]=todo  [~]=doing  [x]=done
    tier field: one tier name (easy, medium, medium-hard, hard, hardest) or a range "a..b" (e.g. easy..medium,
    medium-hard..hard). "medium-hard" is ONE tier. tiers_done uses commas: easy,medium,medium-hard.
    level field: one depth level L0..L6 or a range "L1..L4"; levels_done uses commas: L1,L2.
    Levels: L0 intuition, L1 school, L2 advanced school, L3 college, L4 master's, L5 PhD, L6 frontier
    (see references/depth-levels.md).
"""
import argparse
import datetime as dt
import os
import re
import shutil
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")   # Windows consoles default to cp1252
    except Exception:
        pass

STATE_CAP = 120          # lines; STATE.md must stay quick to read
RECENT_KEEP = 3
THREAD_CAP = 8           # open threads kept in STATE; older ones move to STATE_ARCHIVE.md
PROFILE_AUTO_CAP = 10    # auto-appended "(S00n) ..." learner-profile lines kept in STATE
MARK = {"todo": "[ ]", "doing": "[~]", "done": "[x]"}
TIERS = ["easy", "medium", "medium-hard", "hard", "hardest"]
LEVELS = {
    "L0": "intuition", "L1": "school", "L2": "advanced school", "L3": "college",
    "L4": "master's", "L5": "PhD", "L6": "frontier",
}
ID_PAT = r"[A-Z]+\d+(?:\.\d+)*[a-z]?"
NODE_RE = re.compile(r"^- \[(?P<m>[ ~x])\] (?P<id>" + ID_PAT + r") \| (?P<title>[^|]+?)(?: \| (?P<rest>.*))?$")
TIER_ONE = "(?:" + "|".join(sorted(map(re.escape, TIERS), key=len, reverse=True)) + ")"
TIER_FIELD_RE = re.compile(rf"^{TIER_ONE}(?:\.\.{TIER_ONE})?$")
LEVEL_FIELD_RE = re.compile(r"^L[0-6](?:\.\.L[0-6])?$")
THREADS_RE = re.compile(r"(## Open threads\n)(.*?)(\n## )", re.S)


def today():
    return dt.date.today().isoformat()


def p(kb, *a):
    return os.path.join(kb, *a)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def write(path, text):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def append(path, text):
    with open(path, "a", encoding="utf-8", newline="\n") as f:
        f.write(text)


def need(kb, name):
    path = p(kb, name)
    if not os.path.exists(path):
        sys.exit(f"{path} not found: is '{kb}' a knowledge base? Create one with `kb_update.py init {kb} --course NAME`.")
    return path


def fields(rest):
    """' | '-separated 'key: value' segments -> dict (keys lower-case)."""
    out = {}
    for seg in (rest or "").split(" | "):
        k, sep, v = seg.partition(": ")
        if sep:
            out[k.strip().lower()] = v.strip()
    return out


def set_field(rest, key, value):
    """Replace (or append) one 'key: value' segment of a node line's tail."""
    segs = [s for s in (rest or "").split(" | ") if s.strip() and not s.strip().lower().startswith(key + ":")]
    segs.append(f"{key}: {value}")
    return " | ".join(segs)


def check_tier(v):
    if v and not TIER_FIELD_RE.match(v):
        sys.exit(f"bad tier '{v}': use one of {', '.join(TIERS)} or a range a..b (e.g. easy..medium)")
    return v


def check_level(v):
    if v and not LEVEL_FIELD_RE.match(v):
        sys.exit(f"bad level '{v}': use L0..L6 or a range like L1..L3 (see references/depth-levels.md)")
    if v and ".." in v:
        lo, hi = v.split("..")
        if int(lo[1]) > int(hi[1]):
            sys.exit(f"bad level range '{v}': lower level first")
    return v


def check_list(v, allowed, what):
    items = [x.strip() for x in v.split(",") if x.strip()]
    bad = [x for x in items if x not in allowed]
    if bad:
        sys.exit(f"bad {what} {bad}: allowed {', '.join(allowed)}")
    return ",".join(items)


# ---------------------------------------------------------------- STATE.md
STATE_TMPL = """# STATE  (read me FIRST every session; keep under {cap} lines)
<!-- Managed by kb_update.py. Hand-edit only the Learner profile block. -->
Course: {course}
Engine skill: {engine}   |   Domain pack: {pack}
Knowledge base root: {kb}
Last updated: {date}

## Position
- Sessions completed: 0
- Approx pages written: 0
- Last session covered: (none yet)
- Next node: (run `kb_update.py next`)
- Learner level: {level}

## Recent sessions (newest first, max {keep})
(none yet)

## Open threads
(none yet)

## Learner profile (hand-edited; what the learner has shown they know / prefer)
- Visual learner: no concept is "learned" until code + a figure shows it.
- Wants derivations shown in full, no skipped algebra.
- Wants every idea seen at several depth levels (school -> college -> master's -> PhD -> frontier) and in its extreme regimes.
- Deliverables per session: .tex + .pdf + .docx (or .md when the toolchain is missing) + figures + code + README.
"""


def level_label(lv):
    return f"{lv} ({LEVELS[lv]})"


def cmd_init(a):
    kb = a.kb
    os.makedirs(kb, exist_ok=True)
    for d in ("sessions", "codes", "figures_shared", "literature"):
        os.makedirs(p(kb, d), exist_ok=True)
    lv = level_label(a.learner_level) if a.learner_level else "(not set; ask the learner, then `kb_update.py set-level`)"
    files = {
        "STATE.md": STATE_TMPL.format(cap=STATE_CAP, course=a.course, engine=a.engine, pack=a.pack, kb=os.path.abspath(kb),
                                      date=today(), keep=RECENT_KEEP, level=lv),
        "GLOSSARY.md": "# GLOSSARY  (grow-only; GREP it, never read it whole: kb_update.py glossary-find <kb> <regex>)\n\n",
        "SESSION_INDEX.md": "# SESSION INDEX  (one line per session)\n\n",
        "CODE_INDEX.md": "# CODE INDEX  (one line per module; each module dir has its own README.md)\n\n",
        "VIZ_LOG.md": "# VISUALIZATION LOG  (chart types taught, so they are re-used and compared across sessions)\n\n",
        "CURRICULUM.md": "# CURRICULUM  (recursive term tree; see kb_update.py docstring for line format)\n\n"
                         "## Discovered terms (unsorted)\n\n",
    }
    for name, text in files.items():
        if os.path.exists(p(kb, name)):
            print("kept existing", name)
        else:
            write(p(kb, name), text)
            print("created", name + (" (stub: seed it with add-node, see references/curriculum-design.md)" if name == "CURRICULUM.md" else ""))
    fs = p(kb, "figures_shared", "viz_style.py")
    if not os.path.exists(fs):
        shutil.copy2(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "viz_style.py"), fs)
        print("created figures_shared/viz_style.py")


def cmd_status(a):
    print(read(need(a.kb, "STATE.md")))


def cmd_set_level(a):
    path = need(a.kb, "STATE.md")
    st = read(path)
    line = f"- Learner level: {level_label(a.level)}"
    if re.search(r"(?m)^- Learner level: .*$", st):
        st = re.sub(r"(?m)^- Learner level: .*$", lambda _m: line, st)
    else:  # KB created before levels existed: insert at the end of the Position block
        st = re.sub(r"(## Position\n(?:- .*\n)*)", lambda m: m.group(1) + line + "\n", st, count=1)
    write(path, st)
    print(line[2:])


# ---------------------------------------------------------------- CURRICULUM
def load_nodes(kb):
    lines = read(need(kb, "CURRICULUM.md")).splitlines()
    return lines, [(i, m) for i, m in ((i, NODE_RE.match(l)) for i, l in enumerate(lines)) if m]


def _norm(t):
    t = re.sub(r"\([^)]*\)", " ", t.lower())
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def _title_key(t):
    # unlike _norm, keeps parentheticals: "Motion (Lagrangian view)" is a different node from "Motion"
    return re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()


def find_title(nodes, title):
    t = _title_key(title)
    for _, m in nodes:
        if _title_key(m["title"]) == t:
            return m["id"]
    return None


def learner_level(kb):
    try:
        m = re.search(r"(?m)^- Learner level: (L[0-6])", read(p(kb, "STATE.md")))
        return m.group(1) if m else None
    except OSError:
        return None


def _hint(kb, m):
    f = fields(m["rest"])
    bits = []
    if f.get("level"):
        bits.append(f"levels to teach: {f['level']}" + (f" (done: {f['levels_done']})" if f.get("levels_done") else ""))
    lv = learner_level(kb)
    if lv:
        bits.append(f"learner level: {lv}")
    return ("    [" + "; ".join(bits) + "]") if bits else ""


def cmd_next(a):
    """Order: (1) in-progress [~] node; (2) the node STATE.md declares as 'Next node' if still open;
    (3) first [ ] node in curriculum order. STATE's declaration wins over file order so a session that
    deliberately jumped ahead continues coherently."""
    lines, nodes = load_nodes(a.kb)
    for i, m in nodes:
        if m["m"] == "~":
            print(lines[i] + "    <- in progress" + _hint(a.kb, m))
            return
    st = read(need(a.kb, "STATE.md"))
    d = re.search(r"- Next node: (" + ID_PAT + r")", st)
    if d:
        for idx, (i, m) in enumerate(nodes):
            if m["id"] == d.group(1) and m["m"] == " ":
                print(lines[i] + "    <- declared next in STATE.md" + _hint(a.kb, m))
                skipped = [n["id"] for _, n in nodes[:idx] if n["m"] == " "]
                if skipped:
                    print(f"note: {len(skipped)} earlier node(s) in curriculum order are still open (skipped so far), e.g. "
                          f"{', '.join(skipped[:4])}. Tell the learner, and offer them as the alternative.")
                return
    for i, m in nodes:
        if m["m"] == " ":
            print(lines[i] + "    <- first open node in curriculum order" + _hint(a.kb, m))
            return
    if not nodes:
        print("CURRICULUM.md has no nodes yet. Seed it: `kb_update.py add-node` (see references/curriculum-design.md).")
    else:
        print("All curriculum nodes are done. Add new territory via `discover` / `add-node`, or teach the next depth level.")


def cmd_add_node(a):
    check_tier(a.tier)
    check_level(a.level)
    path = need(a.kb, "CURRICULUM.md")
    lines, nodes = load_nodes(a.kb)
    dup = find_title(nodes, a.title)
    if dup:
        print(f"'{a.title}' already in curriculum as {dup}; not adding")
        return
    ids = {m["id"] for _, m in nodes}
    if a.id:
        if not re.fullmatch(ID_PAT, a.id):
            sys.exit(f"bad id '{a.id}': capital letters then dotted numbers, e.g. P1.03, M2.10a")
        if a.id in ids:
            sys.exit(f"id {a.id} already used")
        nid = a.id
    else:
        nums = [int(i[1:]) for i in ids if re.fullmatch(r"N\d+", i)]
        nid = f"N{(max(nums) + 1) if nums else 1:03d}"
    for name in ("title", "group", "src", "prereq"):
        if "|" in getattr(a, name):
            sys.exit(f"--{name} must not contain '|' (it is the field separator of the curriculum line format)")
    tail = [f"{k}: {v}" for k, v in (("src", a.src), ("tier", a.tier), ("level", a.level), ("prereq", a.prereq)) if v]
    line = f"- [ ] {nid} | {a.title.strip()}" + "".join(" | " + t for t in tail)
    head = f"## {a.group or 'Core'}"
    if head in lines:
        k = lines.index(head) + 1
        while k < len(lines) and not lines[k].startswith("## "):
            k += 1
        while k > 0 and not lines[k - 1].strip():   # insert after the group's last non-blank line
            k -= 1
        lines.insert(k, line)
    else:   # new group goes before the "Discovered terms" bucket so teaching order stays readable
        disc = next((i for i, l in enumerate(lines) if l.startswith("## Discovered terms")), len(lines))
        block = [head, line, ""]
        if disc > 0 and lines[disc - 1].strip():
            block.insert(0, "")
        lines[disc:disc] = block
    write(path, "\n".join(lines).rstrip("\n") + "\n")
    print(line)


def cmd_set_status(a):
    lines, nodes = load_nodes(a.kb)
    for i, m in nodes:
        if m["id"] == a.node:
            rest = m["rest"] or ""
            if a.tiers is not None:
                rest = set_field(rest, "tiers_done", check_list(a.tiers, TIERS, "tiers"))
            if a.levels is not None:
                rest = set_field(rest, "levels_done", check_list(a.levels, list(LEVELS), "levels"))
            lines[i] = f"- {MARK[a.status]} {m['id']} | {m['title'].strip()}" + (f" | {rest}" if rest else "")
            write(p(a.kb, "CURRICULUM.md"), "\n".join(lines) + "\n")
            print(lines[i])
            return
    sys.exit(f"node {a.node} not found in CURRICULUM.md")


def cmd_discover(a):
    check_level(a.level)
    path = need(a.kb, "CURRICULUM.md")
    text = read(path)
    _, nodes = load_nodes(a.kb)
    dup = find_title(nodes, a.term)
    if dup:
        print(f"'{a.term}' already in curriculum as {dup}; not adding")
        return
    for name in ("term", "note", "parent"):
        if "|" in getattr(a, name):
            sys.exit(f"{name} must not contain '|' (it is the field separator of the curriculum line format)")
    ids = [int(x) for x in re.findall(r"^- \[.\] D(\d+) \|", text, re.M)]
    nid = f"D{(max(ids) + 1) if ids else 1:03d}"
    line = (f"- [ ] {nid} | {a.term} | discovered under {a.parent}" + (f" | level: {a.level}" if a.level else "")
            + (f" | note: {a.note}" if a.note else "") + f" | found: {today()}\n")
    lines = text.rstrip("\n").splitlines()
    head = next((i for i, l in enumerate(lines) if l.startswith("## Discovered terms")), None)
    if head is None:
        lines += ["", "## Discovered terms (unsorted)", ""]
        head = len(lines) - 2
    # insert at the end of the Discovered-terms section, even when other groups follow it
    k = head + 1
    while k < len(lines) and not lines[k].startswith("## "):
        k += 1
    while k > head + 1 and not lines[k - 1].strip():
        k -= 1
    lines.insert(k, line.rstrip("\n"))
    write(path, "\n".join(lines).rstrip("\n") + "\n")
    print(line.strip())


# ---------------------------------------------------------------- GLOSSARY
def cmd_glossary_add(a):
    check_level(a.level)
    path = need(a.kb, "GLOSSARY.md")
    if re.search(r"^### " + re.escape(a.term) + r"\s*$", read(path), re.M | re.I):
        print(f"'{a.term}' already in glossary; not adding (edit by hand to refine)")
        return
    entry = (f"### {a.term}\n- symbol: {a.symbol or '-'}\n- definition: {a.definition}\n"
             + (f"- level: {a.level}\n" if a.level else "")
             + f"- introduced: session {a.session:03d}\n" + (f"- see also: {a.see}\n" if a.see else "") + "\n")
    append(path, entry)
    print("added", a.term)


def cmd_glossary_find(a):
    text = read(need(a.kb, "GLOSSARY.md"))
    try:
        rx = re.compile(a.pattern, re.I)
    except re.error:   # an unbalanced "(" etc. is searched literally instead of crashing
        rx = re.compile(re.escape(a.pattern), re.I)
    blocks = re.split(r"(?m)^(?=### )", text)
    hits = [b.rstrip() for b in blocks if b.startswith("### ") and rx.search(b)]
    print("\n\n".join(hits) if hits else f"no glossary entry matches /{a.pattern}/")


# ---------------------------------------------------------------- sessions
def slugify(s):
    """Same rule as new_session.py, so SESSION_INDEX 'dir:' always names the directory that exists."""
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def session_dir_name(kb, num, slug):
    """The real sessions/NNN-slug directory for this number if it exists, else the name new_session.py would create."""
    root = p(kb, "sessions")
    if os.path.isdir(root):
        hits = sorted(d for d in os.listdir(root) if re.match(rf"0*{num}-", d) and int(d.split("-", 1)[0]) == num)
        if hits:
            return hits[0]
    return f"{num:03d}-{slugify(slug)}"


def _threads_block(st):
    m = THREADS_RE.search(st)
    if not m:  # repair a STATE.md whose Open threads block was removed by hand
        st = st.replace("## Learner profile", "## Open threads\n(none)\n\n## Learner profile", 1)
        m = THREADS_RE.search(st)
        if not m:
            sys.exit("STATE.md has neither '## Open threads' nor '## Learner profile'; repair it from the spec")
    return st, m


def cmd_session_done(a):
    kb = a.kb
    check_level(a.levels)
    idx_path = need(kb, "SESSION_INDEX.md")
    st = read(need(kb, "STATE.md"))
    for name in ("title", "node", "terms", "slug", "also"):
        if "|" in getattr(a, name):
            sys.exit(f"--{name} must not contain '|' (it is the field separator of the SESSION_INDEX line format)")
    tag = f"S{a.num:03d}"
    sdir = session_dir_name(kb, a.num, a.slug)
    entry = (f"- {tag} | {today()} | {a.title} | node {a.node} | ~{a.pages} pp"
             + (f" | levels: {a.levels}" if a.levels else "")
             + f" | terms: {a.terms} | dir: sessions/{sdir}/")
    idx = read(idx_path).splitlines()
    pos = [i for i, l in enumerate(idx) if l.startswith(f"- {tag} |")]
    if pos:   # idempotent: re-running for the same session replaces its line instead of double-counting
        idx[pos[0]] = entry
        idx = [l for j, l in enumerate(idx) if j not in pos[1:]]
        print(f"note: {tag} was already recorded; its index line was replaced")
    else:
        idx.append(entry)
    write(idx_path, "\n".join(idx).rstrip("\n") + "\n")
    idx_text = read(idx_path)
    done = len(re.findall(r"^- S\d{3,} \|", idx_text, re.M))   # S001 ... S999, S1000 ...
    pages = sum(int(x) for x in re.findall(r"~(\d+) pp", idx_text))
    st = re.sub(r"- Sessions completed: \d+", f"- Sessions completed: {done}", st)
    st = re.sub(r"- Approx pages written: \d+", f"- Approx pages written: {pages}", st)
    also = [x.strip() for x in a.also.split(",") if x.strip()]
    covered = (f"{tag} ({a.node}" + (f"; also {', '.join(also)}" if also else "")
               + (f"; levels {a.levels}" if a.levels else "") + ")")
    st = re.sub(r"- (?:Current node|Last session covered): .*", lambda _m: f"- Last session covered: {covered}", st)
    if a.next:
        st = re.sub(r"- Next node: .*", lambda _m: f"- Next node: {a.next}", st)
    st = re.sub(r"Last updated: .*", lambda _m: f"Last updated: {today()}", st)
    # recent sessions block: newest first, capped, one line per session number
    m = re.search(r"(## Recent sessions[^\n]*\n)(.*?)(\n## )", st, re.S)
    if m:
        items = [l for l in m.group(2).splitlines() if l.startswith("- S") and not l.startswith(f"- {tag} ")]
        items.insert(0, f"- {tag} {a.title} (node {a.node}; terms: {a.terms})")
        st = st[:m.start(2)] + "\n".join(items[:RECENT_KEEP]) + "\n" + st[m.end(2):]
    if a.thread:
        st, m = _threads_block(st)
        cur = [l for l in m.group(2).splitlines() if l.startswith("- ")]
        new = [f"- ({tag}) {t}" for t in a.thread if f"- ({tag}) {t}" not in cur]
        st = st[:m.start(2)] + "\n".join(cur + new) + "\n" + st[m.end(2):]
    if a.profile and f"- ({tag}) {a.profile}" not in st.splitlines():   # idempotent re-runs: no duplicate note
        st = st.rstrip("\n") + f"\n- ({tag}) {a.profile}\n"
    st = prune_state(kb, st)
    write(p(kb, "STATE.md"), st)
    n = len(st.splitlines())
    print(f"STATE updated: {done} sessions, ~{pages} pages, {n}/{STATE_CAP} lines")
    if n > STATE_CAP:
        print("WARNING: STATE.md over cap; prune Open threads / Learner profile by hand.")


def prune_state(kb, st):
    """Keep STATE.md small forever: overflow threads / auto profile notes go to STATE_ARCHIVE.md."""
    moved = []
    m = THREADS_RE.search(st)
    if m:
        th = [l for l in m.group(2).splitlines() if l.startswith("- ")]
        if len(th) > THREAD_CAP:
            moved += ["thread " + l[2:] for l in th[:-THREAD_CAP]]
            th = th[-THREAD_CAP:]
        st = st[:m.start(2)] + ("\n".join(th) or "(none)") + "\n" + st[m.end(2):]
    head, sep, prof = st.partition("## Learner profile")
    lines = prof.splitlines()
    auto = [l for l in lines if re.match(r"- \(S\d{3,}\)", l)]
    if len(auto) > PROFILE_AUTO_CAP:
        drop = set(auto[:-PROFILE_AUTO_CAP])
        moved += ["profile " + l[2:] for l in auto[:-PROFILE_AUTO_CAP]]
        lines = [l for l in lines if l not in drop]
        st = head + sep + "\n".join(lines).rstrip("\n") + "\n"
    if moved:
        append(p(kb, "STATE_ARCHIVE.md"), "".join(f"- {today()} archived {x}\n" for x in moved))
    return st


def cmd_thread_add(a):
    path = need(a.kb, "STATE.md")
    st, m = _threads_block(read(path))
    cur = [l for l in m.group(2).splitlines() if l.startswith("- ")]
    line = f"- (S{a.session:03d}) {a.text}"
    if line in cur:
        print("thread already open")
        return
    st = st[:m.start(2)] + "\n".join(cur + [line]) + "\n" + st[m.end(2):]
    write(path, prune_state(a.kb, st))
    print("thread added")


def cmd_close_thread(a):
    path = need(a.kb, "STATE.md")
    st, m = _threads_block(read(path))
    cur = [l for l in m.group(2).splitlines() if l.startswith("- ")]
    keep = [l for l in cur if a.match.lower() not in l.lower()]   # only the Open threads block, never the profile
    if len(keep) == len(cur):
        sys.exit(f'no open thread matches "{a.match}"')
    st = st[:m.start(2)] + ("\n".join(keep) or "(none)") + "\n" + st[m.end(2):]
    write(path, st)
    print(f"closed {len(cur) - len(keep)} thread(s)")


def cmd_code_add(a):
    path = need(a.kb, "CODE_INDEX.md")
    rel = a.path.replace("\\", "/")
    if re.search(rf"(?m)^- {re.escape(a.name)} \| {re.escape(rel)} \|", read(path)):
        print("already indexed", a.name)
        return
    append(path, f"- {a.name} | {rel} | S{a.session:03d} | {a.summary} | README: {rel}/README.md\n")
    print("indexed", a.name)


def cmd_viz_add(a):
    append(need(a.kb, "VIZ_LOG.md"), f"- {a.chart} | S{a.session:03d} | used for: {a.used_for}\n")
    print("logged", a.chart)


def cmd_check_session(a):
    """Every term the session's Section 1 table marks `new` must be in GLOSSARY.md; `fwd` terms must be in
    GLOSSARY.md or CURRICULUM.md. Catches forgotten write-backs (lint cannot: it does not read sessions)."""
    root = p(a.kb, "sessions")
    if not os.path.isdir(root):
        sys.exit(f"{root} not found")
    cand = sorted(d for d in os.listdir(root)
                  if d == a.session or (a.session.isdigit() and d.startswith(f"{int(a.session):03d}-")))
    if not cand:
        sys.exit(f"no session directory matches {a.session}")
    src = read(p(root, cand[0], "source.md"))
    m = re.search(r"# 1\. Terms.*?\n(.*?)\n# 2\.", src, re.S)
    if not m:
        sys.exit("no '# 1. Terms' section found")
    gloss = {_norm(t) for t in re.findall(r"(?m)^### (.+)$", read(need(a.kb, "GLOSSARY.md")))}
    curr = {_norm(mm["title"]) for _, mm in load_nodes(a.kb)[1]}
    missing, n = [], 0
    for row in m.group(1).splitlines():
        if not row.strip().startswith("|"):
            continue
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        if len(cells) < 5 or cells[0].lower() == "term" or set(cells[0]) <= set(":- "):
            continue
        status = re.sub(r"[^a-z]", "", cells[-1].lower())[:3]   # last column = New / known / fwd
        term = _norm(cells[0])
        if not term:
            continue
        n += 1
        if status == "new" and term not in gloss:
            missing.append(f"{cells[0]}  (marked new, not in GLOSSARY)")
        elif status == "fwd" and term not in gloss and term not in curr:
            missing.append(f"{cells[0]}  (marked fwd, in neither GLOSSARY nor CURRICULUM)")
    print(f"{cand[0]}: {n} term rows checked; {len(missing)} problem(s)")
    for x in missing:
        print("  MISSING:", x)
    sys.exit(1 if missing else 0)


def cmd_lint(a):
    bad = 0
    st = read(need(a.kb, "STATE.md"))
    n = len(st.splitlines())
    print(f"STATE.md {n}/{STATE_CAP} lines", "OK" if n <= STATE_CAP else "OVER CAP"); bad += n > STATE_CAP
    for sec in ("## Position", "## Recent sessions", "## Open threads", "## Learner profile"):
        if sec not in st:
            print(f"STATE.md missing section '{sec}'"); bad += 1
    lines, nodes = load_nodes(a.kb)
    ids = [m["id"] for _, m in nodes]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    print(f"CURRICULUM {len(ids)} nodes; duplicate ids: {dup or 'none'}"); bad += bool(dup)
    stray = [l for l in lines if l.startswith("- [") and not NODE_RE.match(l)]
    print(f"malformed node lines: {len(stray)}"); [print("  ", s) for s in stray[:5]]; bad += bool(stray)
    badf = []
    for _, m in nodes:
        f = fields(m["rest"])
        if f.get("tier") and not TIER_FIELD_RE.match(f["tier"]):
            badf.append(f"{m['id']} tier: {f['tier']}")
        if f.get("level") and not LEVEL_FIELD_RE.match(f["level"]):
            badf.append(f"{m['id']} level: {f['level']}")
        for key, allowed in (("tiers_done", TIERS), ("levels_done", list(LEVELS))):
            if f.get(key) and any(x.strip() not in allowed for x in f[key].split(",")):
                badf.append(f"{m['id']} {key}: {f[key]}")
    print(f"bad tier/level fields: {len(badf)}"); [print("  ", s) for s in badf[:5]]; bad += bool(badf)
    g = read(need(a.kb, "GLOSSARY.md"))
    terms = [t.strip().lower() for t in re.findall(r"(?m)^### (.+)$", g)]
    dupg = sorted({t for t in terms if terms.count(t) > 1})
    print(f"GLOSSARY {len(terms)} terms; duplicates: {dupg or 'none'}"); bad += bool(dupg)
    print("LINT OK" if not bad else f"LINT: {bad} problem group(s)")
    sys.exit(1 if bad else 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add(name, fn, *args):
        s = sub.add_parser(name); s.add_argument("kb")
        for spec, kw in args:
            s.add_argument(*spec if isinstance(spec, tuple) else (spec,), **kw)
        s.set_defaults(fn=fn)
        return s

    lv = dict(choices=list(LEVELS))
    add("init", cmd_init, (("--course",), dict(required=True)), (("--engine",), dict(default="socratic-mastery-tutor")),
        (("--pack",), dict(default="(none: standalone course)")), (("--learner-level",), dict(default=None, **lv)))
    add("status", cmd_status)
    add("next", cmd_next)
    add("add-node", cmd_add_node, (("--title",), dict(required=True)), (("--group",), dict(default="")), (("--id",), dict(default="")),
        (("--tier",), dict(default="")), (("--level",), dict(default="")), (("--src",), dict(default="")), (("--prereq",), dict(default="")))
    add("set-status", cmd_set_status, ("node", {}), ("status", dict(choices=list(MARK))), (("--tiers",), dict(default=None)),
        (("--levels",), dict(default=None)))
    add("set-level", cmd_set_level, ("level", lv))
    add("discover", cmd_discover, ("term", {}), (("--parent",), dict(required=True)), (("--note",), dict(default="")),
        (("--level",), dict(default="")))
    add("glossary-add", cmd_glossary_add, ("term", {}), (("--session",), dict(type=int, required=True)), (("--symbol",), dict(default="")),
        (("--def", "--definition"), dict(dest="definition", required=True)), (("--see",), dict(default="")), (("--level",), dict(default="")))
    add("glossary-find", cmd_glossary_find, ("pattern", {}))
    add("session-done", cmd_session_done, (("--num",), dict(type=int, required=True)), (("--slug",), dict(required=True)),
        (("--title",), dict(required=True)), (("--node",), dict(required=True)), (("--terms",), dict(default="")),
        (("--pages",), dict(type=int, default=0)), (("--next",), dict(default="")), (("--also",), dict(default="")),
        (("--levels",), dict(default="")), (("--thread",), dict(action="append", default=[])),
        (("--profile-note",), dict(dest="profile", default="", help="auto Learner-profile note")))
    # On session-done "--level" abbreviates "--levels" (depth levels), as everywhere else; an old-style
    # "--level 'free text'" profile note now fails loudly in check_level instead of being silently misfiled.
    add("thread-add", cmd_thread_add, ("text", {}), (("--session",), dict(type=int, required=True)))
    add("close-thread", cmd_close_thread, ("match", {}))
    add("code-add", cmd_code_add, (("--path",), dict(required=True)), (("--name",), dict(required=True)), (("--summary",), dict(required=True)),
        (("--session",), dict(type=int, required=True)))
    add("viz-add", cmd_viz_add, (("--chart",), dict(required=True)), (("--session",), dict(type=int, required=True)),
        (("--used-for",), dict(dest="used_for", required=True)))
    add("check-session", cmd_check_session, ("session", {}))
    add("lint", cmd_lint)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
