"""Checkpoint for Session 2. Prints PASS or FAIL."""
import numpy as np


def run_checks(L):
    """L is the lesson module (or notebook namespace). Returns a list of (label, passed)."""
    checks = []

    # --- worked example: one implicit step against one explicit step, by hand ---
    kk, hh = 1.0e4, 1.0e-2
    f = lambda y: -kk * y
    jac = lambda y: -kk * np.ones(y.shape + (1,))      # 1x1 Jacobian
    imp = L.backward_euler_step(f, jac, np.array([1.0]), hh)
    checks.append((f"worked example: for dy/dt = -10000 y and h = 0.01 backward Euler gives 1 / (1 + k h) = 1/101 = 0.0099 (got {imp[0]:.5f}); explicit Euler gives 1 - k h = -99",
                   abs(imp[0] - 1 / 101) < 1e-12 and abs((1 - kk * hh) + 99) < 1e-9))

    # --- validation on the chain with an exact solution ---
    e50, e100, e200 = (L.chain_error(n) for n in (50, 100, 200))
    r50, r100 = L.chain_error(50, richardson=True), L.chain_error(100, richardson=True)
    checks.append((f"chain A -> B -> C (k1 = 1, k2 = 1e4): backward Euler error {e50:.1e}, {e100:.1e}, {e200:.1e} halves when the steps double (first order)",
                   abs(e50 / e100 - 2) < 0.15 and abs(e100 / e200 - 2) < 0.15 and e50 < 2.5e-3))
    checks.append((f"Richardson extrapolation makes it second order: error {r50:.1e} and {r100:.1e} (ratio 4)",
                   abs(r50 / r100 - 4) < 0.5 and r100 < 2e-5))
    ex = L.chain_exact(np.array([0.0, 1.0, 5.0]))
    checks.append(("the exact chain solution adds to 1, starts at (1, 0, 0) and at t = 5 has A = exp(-5) = 0.00674",
                   np.allclose(ex.sum(axis=-1), 1) and np.allclose(ex[0], [1, 0, 0]) and abs(ex[2, 0] - np.exp(-5)) < 1e-15))
    checks.append(("explicit Euler on the fast step (k = 1e4, T = 0.01): h = 2e-5 decays, h = 2e-4 (limit 2/k) neither grows nor decays, h = 5e-4 explodes to 1e12",
                   L.explicit_euler_chain(2e-5) < 1e-4 and abs(L.explicit_euler_chain(2e-4) - 1.0) < 1e-9 and L.explicit_euler_chain(5e-4) > 1e11))

    # --- the Robertson problem ---
    y = L.solve(np.array([1.0, 0.0, 0.0]), 0.04, L.T_OUT)
    checks.append((f"Robertson at 40 s: y = ({y[-1, 0]:.4f}, {y[-1, 1]:.2e}, {y[-1, 2]:.4f}), the standard test values 0.7158, 9.19e-6, 0.2842",
                   abs(y[-1, 0] - 0.7158) < 2e-4 and abs(y[-1, 1] - 9.19e-6) < 2e-8 and abs(y[-1, 2] - 0.2842) < 2e-4))
    checks.append(("the three fractions add to 1 to 1e-12 at every output time", np.max(np.abs(y.sum(axis=-1) - 1)) < 1e-12))
    checks.append(("a faster slow reaction (k1 = 0.05) leaves less A at 40 s than k1 = 0.03",
                   L.solve(np.array([1.0, 0.0, 0.0]), 0.05, L.T_OUT)[-1, 0] < L.solve(np.array([1.0, 0.0, 0.0]), 0.03, L.T_OUT)[-1, 0]))
    lam = max(L.fastest_rate(s) for s in y)
    steps = len(L.make_grid(L.T_OUT)[0]) - 1
    checks.append((f"cost: the fastest rate is {lam:.0f} per second, so explicit Euler needs h < {2 / lam:.1e} s, more than 60000 steps to 40 s; the implicit grid has {steps} steps",
                   1e3 < lam < 1.1e4 and L.T_END / (2 / lam) > 60000 and steps < 300))
    import time
    t0 = time.perf_counter()
    L.solve(np.array([1.0, 0.0, 0.0]), 0.04, L.T_OUT)
    checks.append(("one accurate solve takes between 1 ms and 5 s (timing is illustrative)", 1e-3 < time.perf_counter() - t0 < 5.0))

    # --- sampling and the surrogate ---
    u = L.latin_hypercube(40, 2, 3)
    checks.append(("Latin hypercube: every one of the 40 slices of each input is used exactly once",
                   all(np.array_equal(np.sort(np.floor(u[:, j] * 40)), np.arange(40)) for j in range(2))))
    checks.append(("polynomial of total degree 6 in 3 inputs has 84 terms", L.poly_features(np.zeros((1, 3)), 6).shape[1] == 84))
    test_runs, test_states = L.run_data(200, seed=999)
    err = {}
    for n in (10, 20, 30, 160):
        runs, states = L.run_data(n, 7)
        err[n] = L.held_out_errors(L.fit_surrogate(runs, states, 6, True), test_runs, test_states)
    checks.append((f"held-out RMS error of y1: {err[10][0]:.4f} (10 runs), {err[20][0]:.4f} (20), {err[30][0]:.5f} (30), {err[160][0]:.5f} (160): it falls, then levels off at the polynomial's own limit (0.0002)",
                   err[10][0] > 0.01 and 0.0015 < err[20][0] < 0.004 and err[30][0] < 0.0005 and err[160][0] < 0.00030 and abs(err[30][0] - err[160][0]) < 6e-5))
    runs, states = L.run_data(160, 7)
    raw = L.held_out_errors(L.fit_surrogate(runs, states, 6, False), test_runs, test_states)
    checks.append((f"log scaling helps species B: median relative error {err[160][1]:.4f} when fitting log10(y2) against {raw[1]:.4f} when fitting y2 (more than twice as good), same y1 error",
                   raw[1] > 2 * err[160][1] and abs(raw[0] - err[160][0]) < 1e-9))
    checks.append(("design: 30 runs are the fewest (of 10, 20, 30, ...) for an RMS error of y1 below 0.0005, and 20 runs for below 0.003",
                   L.runs_for_target(0.0005) == 30 and L.runs_for_target(0.003) == 20))
    p = L.predict(L.fit_surrogate(runs, states), test_runs, L.T_OUT)
    checks.append(("predicted fractions add to 1 by construction, and y2 from the log fit is never negative",
                   np.allclose(p.sum(axis=1), 1) and bool(np.all(p[:, 1] > 0))))
    checks.append(("F_B: for dy/dt = -2000 y and h = 0.002, k h = 4, explicit factor -3, implicit factor 0.2, explicit limit h = 0.001",
                   abs(2000 * 0.002 - 4) < 1e-12 and abs((1 - 4) + 3) < 1e-12 and abs(1 / (1 + 4) - 0.2) < 1e-12 and abs(2 / 2000 - 0.001) < 1e-15))
    checks.append(("the rate constants differ by a factor 3e7 / 0.04 = 7.5e8", abs(L.K3 / 0.04 - 7.5e8) < 1))
    checks.append(("species B: about 3e-5 at 0.1 s, 9.19e-6 at 40 s, so it changes by a factor of 3 or more over the run",
                   1e-5 < y[0, 1] < 5e-5 and abs(y[-1, 1] - 9.19e-6) < 2e-8 and y[0, 1] > 3 * y[-1, 1]))
    checks.append((f"fastest rate is a few thousand per second (got {lam:.0f})", 3000 < lam < 4000))
    r10 = L.held_out_errors(L.fit_surrogate(*L.run_data(10, 7), 6, True), test_runs, test_states)
    r10raw = L.held_out_errors(L.fit_surrogate(*L.run_data(10, 7), 6, False), test_runs, test_states)
    r30 = L.held_out_errors(L.fit_surrogate(*L.run_data(30, 7), 6, True), test_runs, test_states)
    r30raw = L.held_out_errors(L.fit_surrogate(*L.run_data(30, 7), 6, False), test_runs, test_states)
    checks.append((f"with 10 runs the direct fit of y2 is better ({r10raw[1]:.3f} against {r10[1]:.3f}); from 30 runs the log fit wins ({r30[1]:.4f} against {r30raw[1]:.4f}); at 160 runs 0.0007 against 0.0019",
                   abs(r10raw[1] - 0.021) < 0.003 and abs(r10[1] - 0.076) < 0.005 and r30[1] < r30raw[1]
                   and abs(err[160][1] - 0.0007) < 0.0002 and abs(raw[1] - 0.0019) < 0.0003 and 2 < raw[1] / err[160][1] < 3.5))
    checks.append(("the plateau of the y1 error is near 0.0002 (between 0.00015 and 0.0003)", 0.00015 < err[160][0] < 0.0003))
    return checks


# --- runner ---
if __name__ == "__main__":
    import importlib.util
    import pathlib
    import sys

    path = pathlib.Path(__file__).resolve().parent / "lesson.py"
    spec = importlib.util.spec_from_file_location("lesson2", path)
    lesson = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lesson)
    ok = True
    for label, passed in run_checks(lesson):
        print(("PASS  " if passed else "FAIL  ") + label)
        ok &= bool(passed)
    print("PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)
