"""Checkpoint for Session 3. Prints PASS or FAIL."""
import numpy as np


def run_checks(L):
    """L is the lesson module (or notebook namespace). Returns a list of (label, passed)."""
    checks = []

    # --- the toy model by hand (Section E) ---
    eps, n = 0.02, 50
    a_true, a_sur, total = L.toy_rollout(eps, n)
    q = 0.95 * 1.02
    hand = eps * (1 - q ** n) / (1 - q)
    checks.append((f"worked example: toy drift after 50 steps with eps = 2 percent is 0.512 (got {total - 1:.3f}); A is 0.0769 true, 0.2071 surrogate",
                   abs(total - 1 - 0.5115) < 5e-4 and abs(hand - (total - 1)) < 1e-9 and abs(a_true - 0.0769) < 5e-4 and abs(a_sur - 0.2071) < 5e-4))
    checks.append(("toy: the conserved version has zero drift, and eps = 0 has none either",
                   L.toy_rollout(eps, n, conserved=True)[2] == 1.0 and abs(L.toy_rollout(0.0, n)[2] - 1) < 1e-12))
    checks.append(("toy: a negative eps destroys mass (drift -0.290 after 100 steps at -2 percent)",
                   abs(L.toy_rollout(-0.02, 100)[2] - 1 + 0.2896) < 5e-4))
    checks.append(("toy challenge: eps = 2 percent, 100 steps drifts 0.617, but eps = 0.04 percent stays below 0.01",
                   abs(L.toy_drift_formula(0.02, 100) - 0.6175) < 5e-4 and abs(L.toy_drift_formula(0.0004, 100)) < 0.01))

    # --- log scaling and the two state codings ---
    checks.append(("log scaling: s(1e-5) = 0.667, s(0) = -1 (finite), and y2 survives the round trip",
                   abs(L.s_of(1e-5) - 0.6667) < 1e-3 and L.s_of(0.0) == -1.0 and abs(L.y2_of(L.s_of(3e-5)) - 3e-5) < 1e-12 and L.y2_of(L.s_of(0.0)) == 0.0))
    y = np.array([[0.8, 1e-5, 0.19999]])
    zf, zc = L.to_z(y, "free"), L.to_z(y, "conserved")
    checks.append(("worked example: state (0.8, 1e-5, 0.19999) codes as (0.8, 0.19999, 0.667) free and (0.8, 0.667) conserved, and decodes back",
                   np.allclose(zf, [[0.8, 0.19999, 0.6667]], atol=1e-3) and np.allclose(zc, [[0.8, 0.6667]], atol=1e-3)
                   and np.allclose(L.from_z(zc, "conserved").sum(axis=-1), 1.0) and np.allclose(L.from_z(zf, "free"), y)))

    # --- hand-coded backpropagation against finite differences ---
    rng = np.random.default_rng(0)
    P = L.init_mlp([4, 5, 5, 3], 3)
    z0, k1, zt = rng.uniform(0.2, 0.8, (6, 3)), rng.uniform(0.03, 0.05, 6), rng.uniform(0.2, 0.8, (2, 6, 3))
    loss, grads = L.unrolled_loss_grad(P, z0, k1, zt)
    worst = 0.0
    for (i, j, idx) in [(0, 0, (1, 2)), (1, 0, (3, 1)), (2, 0, (2, 2)), (0, 1, (3,)), (2, 1, (1,))]:
        h = 1e-6
        P[i][j][idx] += h
        up = L.unrolled_loss_grad(P, z0, k1, zt)[0]
        P[i][j][idx] -= 2 * h
        dn = L.unrolled_loss_grad(P, z0, k1, zt)[0]
        P[i][j][idx] += h
        num, ana = (up - dn) / (2 * h), grads[i][j][idx]
        worst = max(worst, abs(num - ana) / (abs(num) + abs(ana) + 1e-12))
    checks.append((f"backpropagation through a 2-step unroll matches finite differences (worst relative difference {worst:.1e})", worst < 1e-5))

    # --- the true solver is the reference ---
    d = L.make_dataset(20, 5)
    checks.append(("true solver: fractions add to 1 along every run, and a start from (1, 0, 0) at k1 = 0.04 reaches y1 = 0.7158 at 40 s",
                   np.max(np.abs(d["Y"].sum(axis=-1) - 1)) < 1e-10
                   and abs(L.true_trajectories(np.array([[1.0, 0.0, 0.0]]), np.array([0.04]))[-1, 0, 0] - 0.7158) < 2e-4))

    # --- one step versus rollout, conservation ---
    test = L.test_set()
    free1, cons1 = L.trained("free"), L.trained("conserved")
    free2, cons2 = L.trained("free", 2), L.trained("conserved", 2)
    e = {k: L.evaluate(m, test) for k, m in (("free1", free1), ("cons1", cons1), ("free2", free2), ("cons2", cons2))}
    os1 = L.one_step_error(cons1, test)
    checks.append((f"one step looks excellent: error {os1:.5f} (below 0.002) from the true state",
                   os1 < 0.002 and L.one_step_error(free1, test) < 0.002))
    r80 = e["cons1"]["lin"][80]
    checks.append((f"but the one-step-trained rollout drifts: error {e['cons1']['lin'][1]:.4f} at step 1 grows to {r80:.3f} at step 80 (above 0.1)",
                   e["cons1"]["lin"][1] < 0.01 and r80 > 0.1 and e["cons1"]["lin"][80] > 10 * e["cons1"]["lin"][1]))
    checks.append((f"training on 2-step rollouts cuts the step-80 error to {e['cons2']['lin'][80]:.4f} (below 0.03, under a quarter of one-step training)",
                   e["cons2"]["lin"][80] < 0.03 and e["cons2"]["lin"][80] < 0.25 * r80))
    checks.append((f"decades of species B at step 80: {e['cons1']['dec'][80]:.2f} (one-step) against {e['cons2']['dec'][80]:.3f} (2-step training)",
                   e["cons1"]["dec"][80] > 0.3 and e["cons2"]["dec"][80] < 0.05))
    checks.append((f"mass: the free network drifts by {e['free1']['drift'][80]:.2f} after 80 steps (above 0.1); the conserved one by {e['cons1']['drift'][80]:.0e}",
                   e["free1"]["drift"][80] > 0.1 and e["cons1"]["drift"][80] < 1e-12 and e["cons2"]["drift"][80] < 1e-12))
    checks.append((f"multi-step training alone lowers the free drift to {e['free2']['drift'][80]:.3f} but does not remove it (between 0.002 and 0.1)",
                   0.002 < e["free2"]["drift"][80] < 0.1))

    # --- audit: where it fails ---
    lin, dec = L.error_by_step(cons2, test)
    checks.append((f"error concentrates at the fast transient: y2 error {dec[0]:.3f} decades in step 1 against {dec[1:].mean():.3f} on average later",
                   dec[0] > 10 * dec[1:].mean() and lin[0] > 3 * lin[1:].mean()))
    ex = L.extrapolation_errors()
    inside = ex["inside (training range)"]
    checks.append((f"outside the training range the error is {ex['y1_0 below the range']:.2f} / {ex['k1 above the range']:.2f} against {inside:.3f} inside",
                   inside < 0.03 and ex["y1_0 below the range"] > 3 * inside and ex["k1 above the range"] > 0.3 and ex["both outside"] > 0.3))
    s10, s200 = L.mean_rollout_error(L.sweep_model(10), test), L.mean_rollout_error(L.sweep_model(200), test)
    n0, n1 = L.mean_rollout_error(L.sweep_model(200, 0.0), test), L.mean_rollout_error(L.sweep_model(200, 1.0), test)
    checks.append((f"data size: 10 runs give {s10:.4f}, 200 runs {s200:.4f}; noise of one standard deviation raises {n0:.4f} to {n1:.4f}",
                   s10 > 1.2 * s200 and n1 > 2.5 * n0 and L.mean_rollout_error(L.sweep_model(200, 0.3), test) < 2 * n0))
    one = [L.dt_experiment(dt)[0] for dt in (0.5, 2.0, 8.0, 20.0)]
    checks.append((f"a larger step is harder to learn: one-step error {one[0]:.4f} at dt = 0.5 s grows to {one[3]:.3f} at 20 s",
                   all(np.diff(one) > 0) and one[3] > 20 * one[0]))

    # --- speed ---
    sp = L.speed_test(cons2, n_runs=200)
    checks.append((f"speed (illustrative): surrogate {sp['one_at_a_time'] / sp['surrogate']:.0f} times faster than the solver run one at a time, {sp['vectorised'] / sp['surrogate']:.1f} times faster than the vectorised solver",
                   sp["one_at_a_time"] / sp["surrogate"] > 50 and sp["vectorised"] / sp["surrogate"] > 1.5))
    # --- held-out validation against the true solver ---
    R = e["cons2"]["R"]
    checks.append(("validation: on 100 held-out runs the conserved 2-step surrogate keeps every y1 within 0.06 of the true solver for all 80 steps",
                   float(np.max(np.abs(R[..., 0] - test["Y"][..., 0]))) < 0.06))
    checks.append(("toy: with eps = 1 percent, 100 steps the free drift is 0.243; A surrogate 0.2071 is 2.5 to 3 times the true 0.0769",
                   abs(L.toy_drift_formula(0.01, 100) - 0.243) < 1e-3 and 2.5 < a_sur / a_true < 3.0))
    checks.append(("quoted numbers: step 1 error 0.004, step 80 error 0.22 (one-step) against 0.009 (2-step); free drift 0.28 and 0.02; conserved 0",
                   abs(e["cons1"]["lin"][1] - 0.004) < 0.001 and abs(r80 - 0.22) < 0.05 and abs(e["cons2"]["lin"][80] - 0.009) < 0.003
                   and abs(e["free1"]["drift"][80] - 0.28) < 0.05 and abs(e["free2"]["drift"][80] - 0.02) < 0.01
                   and e["cons2"]["lin"][10:].max() < 0.015 and abs(e["cons1"]["dec"][80] - 0.9) < 0.3))
    worst = float(np.max(np.abs(e["cons2"]["R"][..., 0] - test["Y"][..., 0])))
    checks.append((f"worst y1 error over the held-out runs is {worst:.3f} (between 0.04 and 0.06), several times the mean error", 0.04 < worst < 0.06 and worst > 4 * e["cons2"]["lin"][1:].mean()))
    checks.append(("quoted audit numbers: inside 0.012, k1 above range 0.96; 10 runs 0.018, 200 runs 0.013; dt = 20 s one-step error 0.031",
                   abs(inside - 0.012) < 0.004 and abs(ex["k1 above the range"] - 0.96) < 0.2 and abs(s10 - 0.0178) < 0.004
                   and abs(s200 - 0.0128) < 0.003 and abs(one[3] - 0.031) < 0.006))
    sp2 = L.speed_test(cons2, n_runs=200)
    checks.append(("the speed-up over the vectorised solver is only a few times (between 2 and 30), far below the one-at-a-time figure",
                   2 < sp2["vectorised"] / sp2["surrogate"] < 30))
    return checks


# --- runner ---
if __name__ == "__main__":
    import importlib.util
    import pathlib
    import sys

    path = pathlib.Path(__file__).resolve().parent / "lesson.py"
    spec = importlib.util.spec_from_file_location("lesson3", path)
    lesson = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lesson)
    ok = True
    for label, passed in run_checks(lesson):
        print(("PASS  " if passed else "FAIL  ") + label)
        ok &= bool(passed)
    print("PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)
