"""Session 2 (Level 2): a stiff chemical toy, an implicit solver, training data and a fitted surrogate.

Run:  python start.py 2
"""
# %% [markdown]
# # Session 2: the stiff toy and a first surrogate
# **A. Real-world problem.** Chemical kinetics is *stiff*: some reactions finish in microseconds
# while the slow ones take seconds. A simulation must take tiny steps to stay stable, so it is
# expensive, and a surrogate is attractive. Today: (1) a stiff toy and a solver we can trust,
# (2) training data from many runs, (3) a surrogate fitted by least squares, (4) a design question:
# how many runs do we need for a target accuracy?
#
# **Still a toy.** We use the classic three-species Robertson problem (1966), not a real fuel.
# Mass fractions here are three numbers that always add to 1.

# %%
import pathlib
import time

import numpy as np

# where figures are saved (works as a script and in Jupyter/Colab)
OUT = (pathlib.Path(__file__).resolve().parent if "__file__" in globals() else pathlib.Path(".")) / "out"

K2, K3 = 1.0e4, 3.0e7          # fast rate constants (1/(s) in mass-fraction units); slow rate k1 is an input
K1_DEFAULT = 0.04              # slow rate constant, 1/s
T_END = 40.0                   # end time, s


# %% [markdown]
# ## Step 1: the model
# Species A, B, C with fractions `y1, y2, y3`:
#
#     A -> B        rate k1 y1          (slow, k1 = 0.04)
#     B + B -> C + B   rate k3 y2^2     (very fast, k3 = 3e7)
#     B + C -> A + B   rate k2 y2 y3   (fast, k2 = 1e4)
#
#     dy1/dt = -k1 y1 + k2 y2 y3
#     dy2/dt =  k1 y1 - k2 y2 y3 - k3 y2^2
#     dy3/dt =  k3 y2^2
#
# The three right-hand sides add to zero, so `y1 + y2 + y3` never changes. Rate constants differ by
# a factor `k3 / k1 = 7.5e8`. The Jacobian (matrix of derivatives of the right-hand side) has an
# eigenvalue of size from about 1e3 to 1e4 per second (the fastest rate, growing as C forms) while the slow physics runs at
# 0.04 per second. An explicit method must keep `h` below 2 / (fastest rate) to stay stable.

# %%
def rhs(y, k1=K1_DEFAULT):
    y1, y2, y3 = y[..., 0], y[..., 1], y[..., 2]
    a, b, c = k1 * y1, K2 * y2 * y3, K3 * y2 * y2
    return np.stack([-a + b, a - b - c, c], axis=-1)


def jacobian(y, k1=K1_DEFAULT):
    y1, y2, y3 = y[..., 0], y[..., 1], y[..., 2]
    J = np.zeros(y.shape[:-1] + (3, 3))
    J[..., 0, 0] = -k1
    J[..., 0, 1] = K2 * y3
    J[..., 0, 2] = K2 * y2
    J[..., 1, 0] = k1
    J[..., 1, 1] = -K2 * y3 - 2 * K3 * y2
    J[..., 1, 2] = -K2 * y2
    J[..., 2, 1] = 2 * K3 * y2
    return J


# %%
def fastest_rate(y, k1=K1_DEFAULT):
    """Largest |eigenvalue| of the Jacobian at state y (1/s): sets the explicit stability limit."""
    return float(np.max(np.abs(np.linalg.eigvals(jacobian(np.asarray(y, dtype=float), k1)))))


# %% [markdown]
# ## Step 2: an implicit solver (backward Euler with Newton)
# Explicit Euler computes `y_new = y + h f(y)` and is unstable once `h` exceeds about 2 / (fastest
# rate). *Backward Euler* defines `y_new` by the equation `y_new = y + h f(y_new)`. We solve it with
# Newton's method: repeat `y_new <- y_new - (I - h J)^(-1) (y_new - y - h f(y_new))`. It stays
# stable for any `h`, so the step can follow the slow physics. It is only first-order accurate
# (error proportional to `h`), so we combine a run with step `h` and one with `h/2` (Richardson
# extrapolation: `2 y(h/2) - y(h)`), which removes the first-order error.

# %%
def backward_euler_step(f, jac, y, h, args=(), tol=1e-13, max_iter=30):
    """One implicit step for a batch of states y (shape (..., n)). Returns the new states."""
    yn = y.copy()
    eye = np.eye(y.shape[-1])
    for _ in range(max_iter):
        r = yn - y - h * f(yn, *args)
        A = eye - h * jac(yn, *args)
        d = np.linalg.solve(A, -r[..., None])[..., 0]
        yn = yn + d
        if np.max(np.abs(d)) < tol:
            break
    return yn


def make_grid(t_out, sub=1, n_first=60, t_first=1e-7):
    """Time grid that contains every output time: a geometric start (the fast transient) and
    `16*sub` equal steps between neighbouring output times. Returns (grid, index of each output time)."""
    t_out = np.asarray(t_out, dtype=float)
    g = [0.0] + list(np.geomspace(t_first, t_out[0], n_first * sub))
    idx = [len(g) - 1]
    for a, b in zip(t_out[:-1], t_out[1:]):
        g += list(np.linspace(a, b, 16 * sub + 1)[1:])
        idx.append(len(g) - 1)
    return np.array(g), idx


def integrate(f, jac, y0, t_out, args=(), sub=1):
    """Backward Euler from y0 (shape (..., n)) over a grid that contains t_out; returns states at t_out."""
    g, idx = make_grid(t_out, sub)
    y = np.array(y0, dtype=float)
    out = {}
    for j in range(1, len(g)):
        y = backward_euler_step(f, jac, y, g[j] - g[j - 1], args)
        out[j] = y
    return np.stack([out[i] for i in idx], axis=0)


def solve(y0, k1, t_out):
    """Accurate (second order) solution of the Robertson problem at the times t_out."""
    coarse = integrate(rhs, jacobian, y0, t_out, (k1,), sub=1)
    fine = integrate(rhs, jacobian, y0, t_out, (k1,), sub=2)
    return 2 * fine - coarse


# %% [markdown]
# ## Step 3: validate on a case with a known answer
# A *linear* chain `A -> B -> C` with `k1 = 1` and `k2 = 1e4` (rates 1e4 apart) is stiff and has an
# exact solution: `A = exp(-k1 t)`, `B = k1 (exp(-k1 t) - exp(-k2 t)) / (k2 - k1)`, `C = 1 - A - B`.

# %%
def chain_rhs(y, k1, k2):
    return np.stack([-k1 * y[..., 0], k1 * y[..., 0] - k2 * y[..., 1], k2 * y[..., 1]], axis=-1)


def chain_jac(y, k1, k2):
    J = np.zeros(y.shape[:-1] + (3, 3))
    J[..., 0, 0] = -k1
    J[..., 1, 0] = k1
    J[..., 1, 1] = -k2
    J[..., 2, 1] = k2
    return J


def chain_exact(t, k1=1.0, k2=1.0e4):
    t = np.asarray(t, dtype=float)
    A = np.exp(-k1 * t)
    B = k1 * (np.exp(-k1 * t) - np.exp(-k2 * t)) / (k2 - k1)
    return np.stack([A, B, 1 - A - B], axis=-1)


def chain_error(n_steps, T=5.0, richardson=False):
    """Worst error of backward Euler on the chain with n_steps equal steps to time T."""
    y0 = np.array([1.0, 0.0, 0.0])

    def run(n):
        y = y0.copy()
        h = T / n
        for _ in range(n):
            y = backward_euler_step(chain_rhs, chain_jac, y, h, (1.0, 1.0e4))
        return y

    y = run(n_steps)
    if richardson:
        y = 2 * run(2 * n_steps) - y
    return float(np.max(np.abs(y - chain_exact(T))))


def explicit_euler_chain(h, T=0.01, k2=1.0e4):
    """Explicit Euler on the fast step B -> C alone (dB/dt = -k2 B, B(0) = 1): returns |B(T)|."""
    n = int(round(T / h))
    b = 1.0
    for _ in range(n):
        b = b * (1.0 - k2 * h)
    return abs(b)


# %% [markdown]
# ## Step 4: the cost of a solve and the training data
# One run starts from `y = (y1_0, 0, 1 - y1_0)` with a slow rate `k1`. The *inputs* of the surrogate
# are `y1_0` (between 0.7 and 1), `k1` (between 0.03 and 0.05 per second) and a time `t`
# (between 0.1 and 40 s, log-spaced); the *outputs* are the state at `t`. We draw the runs with a
# seeded *Latin hypercube*: each input range is cut into n equal slices and each slice is used once.

# %%
Y1_RANGE = (0.7, 1.0)
K1_RANGE = (0.03, 0.05)
T_OUT = np.geomspace(0.1, T_END, 12)


def latin_hypercube(n, d, seed):
    rng = np.random.default_rng(seed)
    u = np.empty((n, d))
    for j in range(d):
        u[:, j] = (rng.permutation(n) + rng.random(n)) / n
    return u


def run_data(n, seed):
    """n runs: returns inputs (y1_0, k1) of shape (n, 2) and states of shape (len(T_OUT), n, 3)."""
    u = latin_hypercube(n, 2, seed)
    y1 = Y1_RANGE[0] + u[:, 0] * (Y1_RANGE[1] - Y1_RANGE[0])
    k1 = K1_RANGE[0] + u[:, 1] * (K1_RANGE[1] - K1_RANGE[0])
    y0 = np.stack([y1, np.zeros(n), 1 - y1], axis=1)
    return np.stack([y1, k1], axis=1), solve(y0, k1, T_OUT)


# %% [markdown]
# ## Step 5: the surrogate, a polynomial fitted by least squares
# Every (run, time) pair is one training example: features `(y1_0, k1, ln t)` scaled to [-1, 1],
# all products up to total degree `d`, and the target is the state at that time. Least squares
# (`np.linalg.lstsq`) finds the coefficients. Species B is tiny (about 1e-5) and changes by
# decades, so we also try fitting `log10(y2)` instead of `y2`.

# %%
def scaled_inputs(runs, t):
    """Scale (y1_0, k1, ln t) to [-1, 1]. runs has shape (n, 2); t has shape (m,). Returns (n*m, 3)."""
    n, m = len(runs), len(t)
    a = 2 * (runs[:, 0] - Y1_RANGE[0]) / (Y1_RANGE[1] - Y1_RANGE[0]) - 1
    b = 2 * (runs[:, 1] - K1_RANGE[0]) / (K1_RANGE[1] - K1_RANGE[0]) - 1
    lt = np.log(t)
    c = 2 * (lt - np.log(T_OUT[0])) / (np.log(T_OUT[-1]) - np.log(T_OUT[0])) - 1
    return np.stack([np.repeat(a, m), np.repeat(b, m), np.tile(c, n)], axis=1)


def poly_features(X, degree):
    cols = [np.ones(len(X))]
    for i in range(degree + 1):
        for j in range(degree + 1 - i):
            for k in range(degree + 1 - i - j):
                if i + j + k > 0:
                    cols.append(X[:, 0] ** i * X[:, 1] ** j * X[:, 2] ** k)
    return np.stack(cols, axis=1)


def targets(states, log_species=True):
    """states (m, n, 3) -> (n*m, 2): y1 and (log10 of y2 or y2 itself)."""
    s = np.transpose(states, (1, 0, 2)).reshape(-1, 3)
    return np.stack([s[:, 0], np.log10(s[:, 1]) if log_species else s[:, 1]], axis=1)


def fit_surrogate(runs, states, degree=6, log_species=True):
    X = poly_features(scaled_inputs(runs, T_OUT), degree)
    coef, *_ = np.linalg.lstsq(X, targets(states, log_species), rcond=None)
    return dict(coef=coef, degree=degree, log_species=log_species)


def predict(model, runs, t):
    """Predicted states (n*m, 3); species C follows from the fractions adding to 1."""
    out = poly_features(scaled_inputs(runs, t), model["degree"]) @ model["coef"]
    y1 = out[:, 0]
    y2 = 10 ** out[:, 1] if model["log_species"] else out[:, 1]
    return np.stack([y1, y2, 1 - y1 - y2], axis=1)


def held_out_errors(model, runs, states):
    """RMS error of y1 and the median relative error of y2 on runs never used for fitting."""
    pred = predict(model, runs, T_OUT)
    true = np.transpose(states, (1, 0, 2)).reshape(-1, 3)
    rms1 = float(np.sqrt(np.mean((pred[:, 0] - true[:, 0]) ** 2)))
    rel2 = float(np.median(np.abs(pred[:, 1] - true[:, 1]) / true[:, 1]))
    return rms1, rel2


def runs_for_target(target_rms, degree=6, sizes=(10, 20, 30, 40, 60, 80, 160), seed=7):
    """Smallest training-set size (from `sizes`) whose held-out y1 RMS error is below the target."""
    test_runs, test_states = run_data(200, seed=999)
    for n in sizes:
        runs, states = run_data(n, seed)
        if held_out_errors(fit_surrogate(runs, states, degree), test_runs, test_states)[0] < target_rms:
            return n
    return None


# %%
if __name__ == "__main__":
    import matplotlib.pyplot as plt

    OUT.mkdir(exist_ok=True)
    # validation on the chain with a known solution
    for n in (50, 100, 200):
        print(f"chain, {n:4d} steps: backward Euler error {chain_error(n):.2e}, with Richardson {chain_error(n, richardson=True):.2e}")
    y = solve(np.array([1.0, 0.0, 0.0]), 0.04, T_OUT)[-1]
    print("Robertson at t = 40:", y, " sum", y.sum())

    # cost of one solve
    t0 = time.perf_counter()
    for _ in range(20):
        solve(np.array([1.0, 0.0, 0.0]), 0.04, T_OUT)
    cost = (time.perf_counter() - t0) / 20
    g, _ = make_grid(T_OUT)
    lam = max(fastest_rate(s) for s in solve(np.array([1.0, 0.0, 0.0]), 0.04, T_OUT))
    print(f"one accurate solve: {cost * 1e3:.1f} ms, {len(g) - 1} implicit steps; fastest rate {lam:.0f} /s; "
          f"explicit Euler needs h < {2 / lam:.1e} s, i.e. more than {T_END / (2 / lam):.0f} steps")

    # figure 1: the stiff trajectory
    tt = np.geomspace(1e-6, T_END, 60)
    traj = solve(np.array([1.0, 0.0, 0.0]), 0.04, tt)
    fig, ax = plt.subplots(figsize=(6.5, 4))
    for i, (lab, col) in enumerate((("y1 (A)", "tab:blue"), ("y2 (B)", "tab:red"), ("y3 (C)", "tab:green"))):
        ax.loglog(tt, np.maximum(traj[:, i], 1e-12), color=col, label=lab)
    ax.set_xlabel("time t (s)")
    ax.set_ylabel("mass fraction (no unit)")
    ax.set_title("Robertson problem: B changes by decades")
    ax.grid(alpha=0.3, which="both")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT / "robertson_trajectory.png", dpi=120)

    # figure 2: held-out error vs training runs, and the log-scaling effect
    test_runs, test_states = run_data(200, seed=999)
    ns = (10, 20, 30, 40, 60, 80, 160)
    fig2, axes = plt.subplots(1, 2, figsize=(9.5, 4))
    for logs, lab in ((True, "fit log10(y2)"), (False, "fit y2 directly")):
        r1, r2 = [], []
        for n in ns:
            runs, states = run_data(n, seed=7)
            a, b = held_out_errors(fit_surrogate(runs, states, 6, logs), test_runs, test_states)
            r1.append(a)
            r2.append(b)
        axes[0].loglog(ns, r1, "o-", label=lab)
        axes[1].loglog(ns, r2, "o-", label=lab)
        print(lab, "held-out y1 RMS", np.round(r1, 5), "median relative y2 error", np.round(r2, 4))
    axes[0].set_ylabel("held-out RMS error of y1")
    axes[1].set_ylabel("held-out median relative error of y2")
    for ax in axes:
        ax.set_xlabel("number of training runs")
        ax.grid(alpha=0.3, which="both")
        ax.legend(fontsize=8)
    axes[0].set_title("Species A")
    axes[1].set_title("Species B (tiny, spans decades)")
    fig2.tight_layout()
    fig2.savefig(OUT / "error_vs_runs.png", dpi=120)
    print("runs needed for y1 RMS below 0.0005:", runs_for_target(0.0005))

# %% [markdown]
# ## Where this stops
# A polynomial in three inputs works here because the map `(inputs, t) -> state at t` is smooth. It
# cannot step a state forward again and again, and the number of polynomial terms explodes with
# more inputs. Session 3 builds a neural network that predicts the next state after a small time
# step and rolls it forward, which is how surrogates are used inside bigger simulations.
