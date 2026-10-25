"""One command to set up and run this repo. No activation of environments needed.

    python start.py 1          run Session 1 (also: 2, 3) and its checkpoint
    python start.py all        run all three sessions
    python start.py check 1    run only the checkpoint of Session 1
    python start.py run my.py  run your own file inside the private environment
    python start.py test       run every lesson and checkpoint (what CI does)
    python start.py setup      only create the private environment

On Mac and Linux type python3 instead of python.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".venv"


def fail(msg):
    print("\nSomething needs your attention:\n  " + msg.replace("\n", "\n  "))
    sys.exit(1)


def vpy():
    return VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def setup():
    if sys.version_info < (3, 10):
        fail(f"You are running Python {sys.version_info.major}.{sys.version_info.minor}; this repo needs 3.10 or newer.\n"
             "Install it from https://www.python.org/downloads/ and try again.")
    ok_marker, req = VENV / ".installed", ROOT / "requirements.txt"
    if not vpy().exists() or subprocess.call([str(vpy()), "-m", "pip", "--version"],
                                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL):
        if VENV.exists():
            shutil.rmtree(VENV, ignore_errors=True)   # never keep a half-built environment
        print("Creating a private Python environment in .venv (one time)...")
        code = subprocess.call([sys.executable, "-m", "venv", str(VENV)])
        if code or not vpy().exists():
            shutil.rmtree(VENV, ignore_errors=True)
            fail("Could not create the environment.\nOn Ubuntu/Debian run: sudo apt install python3-venv\nThen run this command again.")
    if not ok_marker.exists() or ok_marker.stat().st_mtime < req.stat().st_mtime:
        print("Installing requirements (one time, needs internet)...")
        code = subprocess.call([str(vpy()), "-m", "pip", "install", "-q", "-r", str(req), "pytest"])
        if code:
            fail("Installing the requirements failed. Check your internet connection and run this command again.")
        ok_marker.write_text("ok", encoding="utf-8")


def open_file(path):
    if not sys.stdout.isatty():
        return
    try:
        if os.name == "nt":
            os.startfile(path)  # noqa: S606
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
    except OSError:
        pass


def env():
    return dict(os.environ, PYTHONIOENCODING="utf-8")


def check(n):
    d = ROOT / "sessions" / f"session-0{n}"
    return subprocess.call([str(vpy()), str(d / "checkpoint.py")], cwd=ROOT, env=env())


def session(n):
    d = ROOT / "sessions" / f"session-0{n}"
    print(f"\n=== Session {n} ===")
    code = subprocess.call([str(vpy()), str(d / "lesson.py")], cwd=ROOT, env=env())
    pngs = sorted((d / "out").glob("*.png")) if (d / "out").exists() else []
    for p in pngs:
        print("Figure saved:", p.relative_to(ROOT))
    if pngs:
        open_file(pngs[0])
    if code == 0:
        code = check(n)
    print(f"Live app: open {d.relative_to(ROOT) / 'app.html'} in your browser")
    return code


def main(argv):
    what = argv[0] if argv else "1"
    if what not in {"1", "2", "3", "all", "test", "setup", "check", "run"}:
        print(__doc__)
        return 2
    if what == "check" and (len(argv) < 2 or argv[1] not in {"1", "2", "3"}):
        print("Usage: python start.py check 1   (or 2, 3)")
        return 2
    if what == "run" and (len(argv) < 2 or not Path(argv[1]).exists()):
        print("Usage: python start.py run my_file.py   (the file must exist)")
        return 2
    setup()
    if what == "setup":
        print("Ready. Try: python start.py 1")
        return 0
    if what == "check":
        return check(int(argv[1]))
    if what == "run":
        return subprocess.call([str(vpy()), argv[1]], cwd=ROOT, env=env())
    if what == "test":
        return subprocess.call([str(vpy()), "-m", "pytest", "-q"], cwd=ROOT, env=dict(env(), MPLBACKEND="Agg"))
    todo = [1, 2, 3] if what == "all" else [int(what)]
    return max(session(n) for n in todo)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
