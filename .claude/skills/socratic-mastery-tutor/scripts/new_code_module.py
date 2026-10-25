#!/usr/bin/env python3
"""Scaffold codes/<topic>/<name>/ with module, example, test and a README from the template,
then register it in CODE_INDEX.md. Every code artifact gets a README so a future AI (and the eventual
open-source package) can learn what the code does without opening it.

    new_code_module.py <kb_root> --topic fundamentals --name reynolds_decomposition
                       --summary "Split a signal into mean + fluctuation; check Reynolds axioms" --session 1
"""
import argparse
import keyword
import os
import re
import subprocess
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.normpath(os.path.join(HERE, "..", "assets"))

MODULE = '''"""{summary}

See README.md in this folder for purpose, API, and runnable examples.
"""
import numpy as np


def main():
    raise NotImplementedError("replace with the real implementation")


if __name__ == "__main__":
    main()
'''

EXAMPLE = '''"""Minimal runnable example for {name}. Run: python example_basic.py  (writes example_basic.png)."""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import {name}  # noqa: F401


def main():
    fig, ax = plt.subplots()
    ax.set(title="{name} example")
    fig.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)), "example_basic.png"), dpi=150)


if __name__ == "__main__":
    main()
'''

TEST = '''"""Smoke test: pytest, or python test_{name}.py."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import {name}  # noqa: F401


def test_imports():
    assert {name} is not None


if __name__ == "__main__":
    test_imports()
    print("ok")
'''


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("kb")
    ap.add_argument("--topic", required=True)
    ap.add_argument("--name", required=True, help="python-identifier module name")
    ap.add_argument("--summary", required=True)
    ap.add_argument("--session", type=int, required=True)
    a = ap.parse_args()

    if not a.name.isidentifier() or keyword.iskeyword(a.name):
        sys.exit(f"--name '{a.name}' is not a valid Python module name (letters, digits, underscore; not a keyword)")
    topic = re.sub(r"[^a-z0-9_]+", "_", a.topic.lower()).strip("_")
    if not topic:
        sys.exit("--topic must contain at least one letter or digit")
    if not os.path.exists(os.path.join(a.kb, "CODE_INDEX.md")):
        sys.exit(f"{a.kb} has no CODE_INDEX.md: create the knowledge base first with `kb_update.py init`")
    summary = " ".join(a.summary.split())          # one line: it goes into a greppable index line
    doc = summary.replace("\\", "\\\\").replace('"""', "'''")   # safe inside the module docstring

    rel = f"codes/{topic}/{a.name}"
    d = os.path.join(a.kb, "codes", topic, a.name)
    if os.path.exists(d):
        sys.exit(f"{rel} already exists; refusing to overwrite")
    os.makedirs(os.path.join(d, "tests"))

    def put(path, text):
        with open(path, "w", encoding="utf-8", newline="\n") as f:   # explicit UTF-8: cp1252 crashes on Windows
            f.write(text)

    put(os.path.join(d, f"{a.name}.py"), MODULE.format(summary=doc))
    put(os.path.join(d, "example_basic.py"), EXAMPLE.format(name=a.name))
    put(os.path.join(d, "tests", f"test_{a.name}.py"), TEST.format(name=a.name))
    with open(os.path.join(ASSETS, "CODE_README_template.md"), encoding="utf-8") as f:
        t = f.read()
    for k, v in {"{{NAME}}": a.name, "{{SUMMARY}}": summary, "{{SESSION}}": f"{a.session:03d}", "{{TOPIC}}": topic}.items():
        t = t.replace(k, v)
    put(os.path.join(d, "README.md"), t)
    subprocess.run([sys.executable, os.path.join(HERE, "kb_update.py"), "code-add", a.kb, "--path", rel,
                    "--name", a.name, "--summary", summary, "--session", str(a.session)], check=True)
    print(d)


if __name__ == "__main__":
    main()
