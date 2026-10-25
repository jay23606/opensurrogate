"""Checkpoint for Session 1. Prints PASS or FAIL."""
import numpy as np


def run_checks(L):
    """L is the lesson module (or notebook namespace). Returns a list of (label, passed)."""
    checks = []
    checks.append(("the slow simulation agrees with exp(-k): k = 1 gives 0.36787 and k = 5 is within 1e-4",
                   abs(L.slow_simulation(1.0) - np.exp(-1.0)) < 1e-4 and abs(L.slow_simulation(5.0) - np.exp(-5.0)) < 1e-4))
    s6 = L.make_surrogate(6)
    hand = (np.exp(-2.0) + np.exp(-3.0)) / 2
    checks.append((f"worked example: with 6 runs (k = 0, 1, ..., 5) the surrogate at k = 2.5 is (0.1353 + 0.0498) / 2 = 0.0926, true 0.0821, error 0.0105 (got {float(s6(2.5)):.4f})",
                   abs(float(s6(2.5)) - hand) < 1e-4 and abs(hand - 0.0926) < 5e-5
                   and abs(float(L.exact_answer(2.5)) - 0.0821) < 5e-5 and abs(abs(float(s6(2.5)) - float(L.exact_answer(2.5))) - 0.0105) < 5e-4))
    k6, y6 = L.training_runs(6)
    checks.append(("the surrogate reproduces its own training runs exactly", np.allclose(s6(k6), y6)))
    checks.append(("worst-case error shrinks with more runs: 3 runs 0.265, 6 runs 0.078, 18 runs 0.0094",
                   abs(L.max_error(3) - 0.265) < 0.002 and abs(L.max_error(6) - 0.0779) < 0.001 and abs(L.max_error(18) - 0.00935) < 0.0003
                   and L.max_error(3) > L.max_error(6) > L.max_error(18)))
    checks.append(("design: 18 runs are the fewest that give an error below 0.01 (17 runs give 0.0105)",
                   L.runs_needed(0.01) == 18 and L.max_error(17) > 0.01 > L.max_error(18)))
    checks.append(("a tenfold tighter target costs about three times as many runs: error below 0.001 needs 56",
                   L.runs_needed(0.001) == 56))
    checks.append(("edge: with only 2 runs the surrogate is one straight line and the worst error is 0.48",
                   abs(L.max_error(2) - 0.480) < 0.002))
    checks.append(("limit: outside the trained range np.interp just repeats the end value, so k = 6 gives 0.0067 instead of 0.0025",
                   abs(float(L.make_surrogate(18)(6.0)) - np.exp(-5.0)) < 1e-4 and abs(float(L.exact_answer(6.0)) - 0.00248) < 1e-4))
    checks.append(("a grid of 18 values per input needs 18 x 18 = 324 runs for two inputs and 5832 for three", 18 ** 2 == 324 and 18 ** 3 == 5832))
    t_sim, t_sur = L.time_per_call(L.slow_simulation, 10), L.time_per_call(L.make_surrogate(18), 1000)
    checks.append((f"speed (illustrative): one surrogate answer is more than 100 times faster than one slow run (ratio {t_sim / t_sur:.0f})",
                   t_sim / t_sur > 100))
    s3 = L.make_surrogate(3)
    est, tru = float(s3(1.25)), float(L.exact_answer(1.25))
    checks.append((f"3 runs at k = 1.25: surrogate {est:.3f}, true {tru:.4f}, error {est - tru:.3f} (nearly 90 percent of the truth)",
                   abs(est - 0.541) < 0.001 and abs(tru - 0.2865) < 5e-5 and abs(est - tru - 0.255) < 0.002 and 0.85 < (est - tru) / tru < 0.9))
    e6 = abs(float(s6(2.5)) - float(L.exact_answer(2.5)))
    checks.append(("6 runs at k = 2.5: the error 0.0105 is about 13 percent of the true answer",
                   0.12 < e6 / float(L.exact_answer(2.5)) < 0.135))
    checks.append(("at k = 6 the surrogate (0.0067) is more than twice the truth (0.0025)",
                   float(L.make_surrogate(18)(6.0)) > 2 * float(L.exact_answer(6.0))))
    checks.append(("run costs at 2 minutes per run: 18 runs 36 min, 56 runs 112 min, 324 runs 648 min",
                   (2 * 18, 2 * 56, 2 * 324) == (36, 112, 648)))
    checks.append(("exercise: 24 runs give an error more than 3 times smaller than 12 runs", L.max_error(12) > 3 * L.max_error(24)))
    q = np.linspace(L.K_LO, L.K_HI, 501)
    err = np.abs(L.make_surrogate(6)(q) - L.exact_answer(q))
    checks.append(("the error of the 6-run surrogate peaks at small k (below 0.5), where exp(-k) bends most", q[int(np.argmax(err))] < 0.5))
    return checks


# --- runner ---
if __name__ == "__main__":
    import importlib.util
    import pathlib
    import sys

    path = pathlib.Path(__file__).resolve().parent / "lesson.py"
    spec = importlib.util.spec_from_file_location("lesson1", path)
    lesson = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lesson)
    ok = True
    for label, passed in run_checks(lesson):
        print(("PASS  " if passed else "FAIL  ") + label)
        ok &= bool(passed)
    print("PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)
