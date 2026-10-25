import importlib.util
from pathlib import Path


LESSON_PATH = Path(__file__).resolve().parents[1] / "sessions" / "session-01" / "lesson.py"
SPEC = importlib.util.spec_from_file_location("lesson1", LESSON_PATH)
LESSON = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LESSON)


def test_two_input_table_reports_runs_and_error(capsys):
    table = LESSON.two_input_table(18)
    output = capsys.readouterr().out

    assert table.shape == (18, 18)
    assert "324 runs" in output
    assert "error" in output
