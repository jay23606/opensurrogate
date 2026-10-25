"""Run every lesson and checkpoint headless."""
import os
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
ENV = dict(os.environ, MPLBACKEND="Agg", PYTHONIOENCODING="utf-8")


@pytest.mark.parametrize("n", ["01", "02", "03"])
@pytest.mark.parametrize("script", ["lesson.py", "checkpoint.py"])
def test_session(n, script):
    path = ROOT / "sessions" / f"session-{n}" / script
    res = subprocess.run([sys.executable, str(path)], capture_output=True, text=True,
                         env=ENV, cwd=ROOT, timeout=180)
    assert res.returncode == 0, res.stdout + res.stderr
    if script == "checkpoint.py":
        assert "PASS" in res.stdout
