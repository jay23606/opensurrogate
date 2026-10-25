"""Shared setup for this session's figure scripts (scaffolded by new_session.py; generic, portable).

Usage at the top of every figNN_*.py:

    from _common import *                       # np, plt, PAL, FIG, save, out, use_code
    use_code("fundamentals/reynolds_averaging") # optional: put a codes/<topic>/<module> on sys.path
    import reynolds_averaging as ra

The KB root is found by walking up to the folder containing STATE.md, and the plotting style is imported from
<KB>/figures_shared/viz_style.py, so nothing depends on where any skill is installed (the KB is what ships).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def _find_kb(start):
    d = start
    while d != os.path.dirname(d):
        if os.path.exists(os.path.join(d, "STATE.md")):
            return d
        d = os.path.dirname(d)
    raise RuntimeError("no STATE.md found above " + start + ": not inside a knowledge base")


KB = _find_kb(HERE)
sys.path.insert(0, os.path.join(KB, "figures_shared"))

import numpy as np                              # noqa: E402,F401
import matplotlib.pyplot as plt                 # noqa: E402,F401
from viz_style import setup, PAL, FIG, save     # noqa: E402,F401

setup()


def use_code(rel):
    """Make codes/<rel> importable, e.g. use_code('fundamentals/reynolds_averaging')."""
    sys.path.insert(0, os.path.join(KB, "codes", rel))


def out(name):
    """Path of an output file next to the figure scripts."""
    return os.path.join(HERE, name)
