"""Session 3 (Level 3): a neural one-step surrogate for the stiff toy, its rollout, and an honest audit.

Run:  python start.py 3
"""
# %% [markdown]
# # Session 3: a neural surrogate you can audit
# **A. Real-world problem.** Inside a big combustion simulation the chemistry is solved again and
# again in every grid cell, every time step. A neural network that jumps the chemical state forward
# by one small time step `dt` is a candidate stand-in. But a stand-in that is right for one step can
# be wrong after eighty, can create or destroy mass, and can fail without warning outside its training
# range. Today we build one in plain NumPy (network, backpropagation and Adam by hand), roll it out,
# and audit it against the true implicit solver.
#
# **Still a toy.** The chemistry is the three-species Robertson problem from Session 2, not a real
# mechanism; the network is tiny so that it trains in seconds. The lessons about rollout error,
# conservation and extrapolation are the real ones.

# %%
import functools
import pathlib
import time

import numpy as np

# where figures are saved (works as a script and in Jupyter/Colab)
OUT = (pathlib.Path(__file__).resolve().parent if "__file__" in globals() else pathlib.Path(".")) / "out"

K2, K3 = 1.0e4, 3.0e7          # fast rate constants of the Robertson problem
DT = 0.5                       # time step of the surrogate (s)
N_STEPS = 80                   # rollout length: 80 steps of 0.5 s = 40 s
Y1_TRAIN = (0.7, 1.0)          # training range of the initial fraction of species A
K1_TRAIN = (0.03, 0.05)        # training range of the slow rate constant (1/s)


# %% [markdown]
# ## Step 1: the true solver (from Session 2, in compact form)
# Backward Euler with Newton's method for a batch of runs at once; two runs with step `h` and `h/2`
# are combined (Richardson) to give second-order accuracy. The state is three mass fractions that add to 1.

# %%
def rhs(y, k1):
    y1, y2, y3 = y[..., 0], y[..., 1], y[..., 2]
    a, b, c = k1 * y1, K2 * y2 * y3, K3 * y2 * y2
    return np.stack([-a + b, a - b - c, c], axis=-1)


def jacobian(y, k1):
    y2, y3 = y[..., 1], y[..., 2]
    J = np.zeros(y.shape[:-1] + (3, 3))
    J[..., 0, 0], J[..., 0, 1], J[..., 0, 2] = -k1, K2 * y3, K2 * y2
    J[..., 1, 0], J[..., 1, 1], J[..., 1, 2] = k1, -K2 * y3 - 2 * K3 * y2, -K2 * y2
    J[..., 2, 1] = 2 * K3 * y2
    return J


def be_step(y, k1, h):
    yn, eye = y.copy(), np.eye(3)
    for _ in range(30):
        r = yn - y - h * rhs(yn, k1)
        d = np.linalg.solve(eye - h * jacobian(yn, k1), -r[..., None])[..., 0]
        yn = yn + d
        if np.max(np.abs(d)) < 1e-13:
            break
    return yn


def _march(y0, k1, dt, n_steps, sub):
    """Backward Euler through n_steps output intervals; the first interval is refined geometrically."""
    m = max(4, int(np.ceil(dt / 0.125))) * sub
    first = np.concatenate([[0.0], np.geomspace(1e-7, dt, 60 * sub)])
    later = np.linspace(0.0, dt, m + 1)
    y, out = np.array(y0, dtype=float), [np.array(y0, dtype=float)]
    for j in range(n_steps):
        g = first if j == 0 else later
        for a, b in zip(g[:-1], g[1:]):
            y = be_step(y, k1, b - a)
        out.append(y)
    return np.stack(out)


def true_trajectories(y0, k1, dt=DT, n_steps=N_STEPS):
    """Reference solution at times 0, dt, 2 dt, ...: array (n_steps + 1, batch, 3)."""
    return 2 * _march(y0, k1, dt, n_steps, 2) - _march(y0, k1, dt, n_steps, 1)


def initial_states(n, seed, y1_range=Y1_TRAIN, k_range=K1_TRAIN):
    rng = np.random.default_rng(seed)
    y1 = rng.uniform(*y1_range, n)
    k1 = rng.uniform(*k_range, n)
    return np.stack([y1, np.zeros(n), 1 - y1], axis=1), k1


def make_dataset(n, seed, y1_range=Y1_TRAIN, k_range=K1_TRAIN, dt=DT, n_steps=N_STEPS):
    y0, k1 = initial_states(n, seed, y1_range, k_range)
    return dict(Y=true_trajectories(y0, k1, dt, n_steps), k=k1, dt=dt)


# %% [markdown]
# ## Step 2: how the network sees the state (log scaling) and what it must conserve
# Species B changes by decades (zero at the start, about 1e-5 later), so the network works with
# `s = (log10(y2 + 1e-10) + 7) / 3`, a number between about -1 and 1, instead of `y2`. Two designs:
#
# * `free`: the network predicts changes of `y1`, `y3` and `s`. Nothing forces `y1 + y2 + y3 = 1`.
# * `conserved`: the network predicts changes of `y1` and `s` only; the third fraction is computed
#   as `y3 = 1 - y1 - y2` (a conservation-aware output layer), so mass is conserved by construction.

# %%
FLOOR = 1e-10


def s_of(y2):
    return (np.log10(np.maximum(y2, 0.0) + FLOOR) + 7.0) / 3.0


def y2_of(s):
    return np.maximum(10.0 ** (3.0 * s - 7.0) - FLOOR, 0.0)


def to_z(y, kind):
    """Fractions (..., 3) -> network state z: (y1, y3, s) for 'free', (y1, s) for 'conserved'."""
    if kind == "free":
        return np.stack([y[..., 0], y[..., 2], s_of(y[..., 1])], axis=-1)
    return np.stack([y[..., 0], s_of(y[..., 1])], axis=-1)


def from_z(z, kind):
    y2 = y2_of(z[..., -1])
    if kind == "free":
        return np.stack([z[..., 0], y2, z[..., 1]], axis=-1)
    return np.stack([z[..., 0], y2, 1.0 - z[..., 0] - y2], axis=-1)


# %% [markdown]
# ## Step 3: a small network with hand-coded backpropagation and Adam
# Input `x = (z, kn)` where `kn = (k1 - 0.04) / 0.01`. Two tanh hidden layers, linear output `o`.
# The surrogate step is residual: `z_next = z + SC * o`, so the network only learns the *change*
# over one step (`SC = 0.1` sets the typical size of `o` near 1). Backpropagation applies the chain
# rule layer by layer; for a tanh layer the derivative is `1 - h^2`. Adam keeps running averages of
# the gradient `m` and of its square `v` and takes a step of size `lr * m / (sqrt(v) + eps)`.

# %%
SC = 0.1


def init_mlp(sizes, seed):
    rng = np.random.default_rng(seed)
    return [[rng.normal(0.0, np.sqrt(1.0 / a), (a, b)), np.zeros(b)] for a, b in zip(sizes[:-1], sizes[1:])]


def mlp_forward(P, x):
    acts = [x]
    for i, (W, b) in enumerate(P):
        z = acts[-1] @ W + b
        acts.append(np.tanh(z) if i < len(P) - 1 else z)
    return acts


def mlp_backward(P, acts, dout):
    """Gradients of a loss whose derivative with respect to the output is dout. Returns (grads, dx)."""
    grads, d = [None] * len(P), dout
    for i in range(len(P) - 1, -1, -1):
        W = P[i][0]
        grads[i] = (acts[i].T @ d, d.sum(axis=0))
        d = d @ W.T
        if i > 0:
            d = d * (1.0 - acts[i] ** 2)
    return grads, d


def features(z, k1):
    return np.concatenate([z, ((k1 - 0.04) / 0.01)[:, None]], axis=1)


def unrolled_loss_grad(P, z0, k1, zt):
    """Loss and gradient when the network is applied len(zt) times in a row from z0 (zt: (K, n, d)).
    Loss = sum over steps of the mean squared error of z in units of SC. K = 1 is ordinary one-step training."""
    K, n, d = zt.shape
    z, stack, loss = z0, [], 0.0
    for j in range(K):
        acts = mlp_forward(P, features(z, k1))
        z = z + SC * acts[-1]
        stack.append((acts, z - zt[j]))
        loss += float(np.mean(((z - zt[j]) / SC) ** 2))
    grads = [[np.zeros_like(W), np.zeros_like(b)] for W, b in P]
    carry = np.zeros_like(z0)
    for j in range(K - 1, -1, -1):
        acts, err = stack[j]
        dz = carry + 2.0 * err / (SC ** 2 * n * d)          # derivative of the loss with respect to this step's z
        g, dx = mlp_backward(P, acts, SC * dz)
        for i in range(len(P)):
            grads[i][0] += g[i][0]
            grads[i][1] += g[i][1]
        carry = dz + dx[:, :d]                              # identity path plus the path through the network input
    return loss, grads


def adam_update(P, grads, state, lr, t, b1=0.9, b2=0.999, eps=1e-8):
    for i in range(len(P)):
        for j in range(2):
            g = grads[i][j]
            state["m"][i][j] = b1 * state["m"][i][j] + (1 - b1) * g
            state["v"][i][j] = b2 * state["v"][i][j] + (1 - b2) * g * g
            mh = state["m"][i][j] / (1 - b1 ** t)
            vh = state["v"][i][j] / (1 - b2 ** t)
            P[i][j] -= lr * mh / (np.sqrt(vh) + eps)


def train_model(data, kind="conserved", unroll=1, steps=1500, hidden=24, seed=0, batch=256, lr=6e-3, noise=0.0):
    """Train the one-step (unroll=1) or multi-step (unroll>1) surrogate on a dataset from make_dataset.
    `noise` adds Gaussian noise (in z units, relative to the data spread) to the stored states."""
    rng = np.random.default_rng(seed)
    Z = to_z(data["Y"], kind)                               # (n_steps + 1, n_traj, d)
    if noise > 0:
        Z = Z + noise * rng.standard_normal(Z.shape) * Z.reshape(-1, Z.shape[-1]).std(axis=0)
    n_steps, n_traj, d = Z.shape[0] - 1, Z.shape[1], Z.shape[2]
    P = init_mlp([d + 1, hidden, hidden, d], seed)
    state = dict(m=[[np.zeros_like(a) for a in layer] for layer in P], v=[[np.zeros_like(a) for a in layer] for layer in P])
    for t in range(1, steps + 1):
        j = rng.integers(0, n_steps - unroll + 1, batch)
        b = rng.integers(0, n_traj, batch)
        zt = np.stack([Z[j + u + 1, b] for u in range(unroll)])
        _, grads = unrolled_loss_grad(P, Z[j, b], data["k"][b], zt)
        lr_t = lr * 0.5 * (1 + np.cos(np.pi * t / steps))   # cosine decay of the learning rate
        adam_update(P, grads, state, lr_t, t)
    return dict(P=P, kind=kind, dt=data["dt"])


# %% [markdown]
# ## Step 4: one step, then a rollout
# A *rollout* feeds the network its own output again and again. Errors that are small for one step
# are fed back in and accumulate.

# %%
def surrogate_step(model, z, k1):
    return z + SC * mlp_forward(model["P"], features(z, k1))[-1]


def rollout(model, y0, k1, n_steps=N_STEPS):
    """Roll the surrogate forward from y0 (batch, 3): returns fractions of shape (n_steps + 1, batch, 3)."""
    z = to_z(y0, model["kind"])
    out = [z]
    for _ in range(n_steps):
        z = surrogate_step(model, z, k1)
        out.append(z)
    return from_z(np.stack(out), model["kind"])


def one_step_error(model, data):
    """Mean over all test pairs of the largest absolute error in y1 and y3 after one step from the TRUE state."""
    Y = data["Y"]
    k1 = np.tile(data["k"], Y.shape[0] - 1)
    z = to_z(Y[:-1].reshape(-1, 3), model["kind"])
    pred = from_z(surrogate_step(model, z, k1), model["kind"])
    true = Y[1:].reshape(-1, 3)
    return float(np.mean(np.max(np.abs(pred[:, [0, 2]] - true[:, [0, 2]]), axis=1)))


def rollout_error(R, Y):
    """Per step: mean over runs of the largest absolute error in y1 and y3 (shape (n_steps + 1,))."""
    return np.mean(np.max(np.abs(R[..., [0, 2]] - Y[..., [0, 2]]), axis=-1), axis=1)


def decade_error(R, Y):
    """Per step: mean over runs of |log10 y2_surrogate - log10 y2_true| (error of the tiny species in decades)."""
    return np.mean(np.abs(np.log10(R[..., 1] + FLOOR) - np.log10(Y[..., 1] + FLOOR)), axis=1)


def mass_drift(R):
    """Largest |y1 + y2 + y3 - 1| over the runs, per step."""
    return np.max(np.abs(R.sum(axis=-1) - 1.0), axis=1)


# %% [markdown]
# ## A hand-sized model of rollout error and mass drift
# Take one decaying substance `A -> B` with exact per-step factor `a = 0.95`. A surrogate with a
# relative error `eps` in its step predicts `A' = a (1 + eps) A` and `B' = B + (1 - a)(1 + eps) A`.
# Each step then adds `eps * A` of mass: after n steps the total has drifted by
# `eps * (1 - q^n) / (1 - q)` with `q = a (1 + eps)`. If instead `B` is computed as `1 - A`
# (conserved), the drift is exactly zero. The error in A after n steps is `|q^n - a^n|`.

# %%
A_STEP = 0.95


def toy_rollout(eps, n, a=A_STEP, conserved=False):
    """Returns (A_true, A_surrogate, total_mass_surrogate) after n steps, starting from A = 1, B = 0."""
    q = a * (1 + eps)
    A_true, A_sur = a ** n, q ** n
    if conserved:
        return A_true, A_sur, 1.0
    B = sum((1 - a) * (1 + eps) * q ** j for j in range(n))
    return A_true, A_sur, A_sur + B


def toy_drift_formula(eps, n, a=A_STEP):
    q = a * (1 + eps)
    return eps * (1 - q ** n) / (1 - q)


# %% [markdown]
# ## Step 5: the experiments (each trains one or more small networks)
# All use the same seeds, so the numbers below are reproducible.

# %%
@functools.lru_cache(maxsize=None)
def train_set(n=200, seed=1):
    return make_dataset(n, seed)


@functools.lru_cache(maxsize=None)
def test_set(seed=2, n=100, y1_range=Y1_TRAIN, k_range=K1_TRAIN):
    return make_dataset(n, seed, y1_range, k_range)


@functools.lru_cache(maxsize=None)
def trained(kind="conserved", unroll=1, n=200, noise=0.0, steps=1500):
    return train_model(train_set(n), kind=kind, unroll=unroll, noise=noise, steps=steps)


def evaluate(model, data):
    """Rollout from the true initial states of `data`: dict of error curves."""
    Y = data["Y"]
    R = rollout(model, Y[0], data["k"], Y.shape[0] - 1)
    return dict(R=R, lin=rollout_error(R, Y), dec=decade_error(R, Y), drift=mass_drift(R))


@functools.lru_cache(maxsize=None)
def sweep_model(n=200, noise=0.0):
    """A cheaper multi-step network (2-step training, 800 Adam steps) used for the sensitivity sweeps."""
    return trained("conserved", 2, n, noise, 800)


def mean_rollout_error(model, data):
    return float(np.mean(evaluate(model, data)["lin"][1:]))


@functools.lru_cache(maxsize=None)
def narrow_model():
    """Trained on a narrow range: y1_0 in [0.85, 1.0] and k1 in [0.035, 0.045]."""
    return train_model(make_dataset(200, 11, (0.85, 1.0), (0.035, 0.045)), "conserved", unroll=2, steps=800)


def extrapolation_errors():
    """Mean rollout error of the narrow-range network on test sets inside and outside its training range."""
    cases = {"inside (training range)": ((0.85, 1.0), (0.035, 0.045)), "y1_0 below the range": ((0.4, 0.6), (0.035, 0.045)),
             "k1 above the range": ((0.85, 1.0), (0.07, 0.09)), "both outside": ((0.4, 0.6), (0.07, 0.09))}
    m = narrow_model()
    return {name: mean_rollout_error(m, test_set(3, 100, y, k)) for name, (y, k) in cases.items()}


@functools.lru_cache(maxsize=None)
def dt_experiment(dt):
    """Train a conserved network for time step dt (2-step training); return (one-step error, mean rollout error)."""
    if dt == DT:
        return one_step_error(sweep_model(), test_set()), mean_rollout_error(sweep_model(), test_set())
    n = int(round(N_STEPS * DT / dt))
    tr, te = make_dataset(200, 1, dt=dt, n_steps=n), make_dataset(100, 2, dt=dt, n_steps=n)
    m = train_model(tr, "conserved", unroll=min(2, n), steps=800)
    return one_step_error(m, te), mean_rollout_error(m, te)


def error_by_step(model, data):
    """One-step error from the TRUE state at every step, averaged over runs: (y1/y3 error, y2 error in decades).
    Step 0 is the fast transient."""
    Y, k1 = data["Y"], data["k"]
    lin, dec = [], []
    for j in range(Y.shape[0] - 1):
        pred = from_z(surrogate_step(model, to_z(Y[j], model["kind"]), k1), model["kind"])
        lin.append(np.mean(np.max(np.abs(pred[:, [0, 2]] - Y[j + 1][:, [0, 2]]), axis=1)))
        dec.append(np.mean(np.abs(np.log10(pred[:, 1] + FLOOR) - np.log10(Y[j + 1][:, 1] + FLOOR))))
    return np.array(lin), np.array(dec)


def speed_test(model, n_runs=1000, repeats=3):
    """Seconds to produce n_runs rollouts: the true solver one run at a time (timed on 5 runs and scaled),
    the true solver vectorised (all runs at once), and the surrogate (all runs at once)."""
    y0, k1 = initial_states(n_runs, 5)
    t0 = time.perf_counter()
    for i in range(5):
        _march(y0[i:i + 1], k1[i:i + 1], DT, N_STEPS, 1)
    t_one = (time.perf_counter() - t0) / 5 * n_runs
    t0 = time.perf_counter()
    _march(y0, k1, DT, N_STEPS, 1)
    t_vec = time.perf_counter() - t0
    best = 1e9
    for _ in range(repeats):
        t0 = time.perf_counter()
        rollout(model, y0, k1)
        best = min(best, time.perf_counter() - t0)
    return dict(one_at_a_time=t_one, vectorised=t_vec, surrogate=best)




# %%
if __name__ == "__main__":
    import matplotlib.pyplot as plt

    OUT.mkdir(exist_ok=True)
    test = test_set()
    t0 = time.perf_counter()
    models = {"free, one-step training": trained("free"), "conserved, one-step training": trained("conserved"),
              "free, 2-step training": trained("free", 2), "conserved, 2-step training": trained("conserved", 2)}
    print(f"trained four networks in {time.perf_counter() - t0:.1f} s")
    ev = {name: evaluate(m, test) for name, m in models.items()}
    for name, e in ev.items():
        print(f"{name:30s} one-step err {one_step_error(models[name], test):.5f}  y1/y3 error at steps 1, 10, 40, 80: "
              f"{np.round(e['lin'][[1, 10, 40, 80]], 4)}  y2 error (decades) at 1, 80: {e['dec'][1]:.3f}, {e['dec'][80]:.3f}  "
              f"mass drift at 80: {e['drift'][80]:.2e}")
    lin0, dec0 = error_by_step(models["conserved, 2-step training"], test)
    print(f"error by step (conserved, 2-step): step 1 y2 {dec0[0]:.3f} decades, steps 2-80 mean {dec0[1:].mean():.3f}; "
          f"y1/y3 step 1 {lin0[0]:.4f}, steps 2-80 mean {lin0[1:].mean():.5f}")
    sp = speed_test(models["conserved, 2-step training"])
    print("seconds for 1000 runs:", {k: round(v, 3) for k, v in sp.items()},
          f"speed-up vs one-at-a-time {sp['one_at_a_time'] / sp['surrogate']:.0f}, vs vectorised {sp['vectorised'] / sp['surrogate']:.1f}")
    print("data size (mean rollout error):", {n: round(mean_rollout_error(sweep_model(n), test), 4) for n in (10, 30, 200)})
    print("noise (mean rollout error):", {z: round(mean_rollout_error(sweep_model(200, z), test), 4) for z in (0.0, 0.3, 1.0)})
    print("extrapolation:", {k: round(v, 3) for k, v in extrapolation_errors().items()})
    print("time step (one-step error, mean rollout error):", {dt: tuple(round(x, 4) for x in dt_experiment(dt)) for dt in (0.5, 2.0, 8.0, 20.0)})
    print(f"total {time.perf_counter() - t0:.1f} s")

    # figure 1: one held-out run, truth against the two conserved networks
    i = 7
    t = np.arange(N_STEPS + 1) * DT
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 4))
    for name, col in (("conserved, one-step training", "tab:red"), ("conserved, 2-step training", "tab:green")):
        R = ev[name]["R"]
        axes[0].plot(t, R[:, i, 0], color=col, label=name)
        axes[1].semilogy(t[1:], R[1:, i, 1], color=col, label=name)
    axes[0].plot(t, test["Y"][:, i, 0], "k--", label="true solver")
    axes[1].semilogy(t[1:], test["Y"][1:, i, 1], "k--", label="true solver")
    axes[0].set_ylabel("species A, y1 (fraction)")
    axes[1].set_ylabel("species B, y2 (fraction)")
    for ax in axes:
        ax.set_xlabel("time (s)")
        ax.grid(alpha=0.3, which="both")
    axes[0].legend(fontsize=8)
    axes[0].set_title("Held-out run: rollout of 80 steps")
    axes[1].set_title("Species B (log axis)")
    fig.tight_layout()
    fig.savefig(OUT / "rollout.png", dpi=120)

    # figure 2: error growth and mass drift
    fig2, axes = plt.subplots(1, 2, figsize=(9.5, 4))
    for name, e in ev.items():
        axes[0].semilogy(t[1:], e["lin"][1:], label=name)
        axes[1].semilogy(t[1:], np.maximum(e["drift"][1:], 1e-17), label=name)
    axes[0].set_ylabel("rollout error of y1, y3 (fraction)")
    axes[1].set_ylabel("mass drift |sum of fractions - 1|")
    axes[0].set_title("Error accumulates over the rollout")
    axes[1].set_title("Mass drift (floor 1e-17 = exact)")
    for ax in axes:
        ax.set_xlabel("time (s)")
        ax.grid(alpha=0.3, which="both")
    axes[0].legend(fontsize=7)
    fig2.tight_layout()
    fig2.savefig(OUT / "error_and_drift.png", dpi=120)

    # figure 3: the audit
    fig3, axes = plt.subplots(1, 3, figsize=(12, 3.8))
    ex = extrapolation_errors()
    axes[0].barh(list(ex)[::-1], list(ex.values())[::-1], color=["tab:red", "tab:red", "tab:orange", "tab:green"])
    axes[0].set_xlabel("mean rollout error (fraction)")
    axes[0].set_title("Outside the training range")
    sizes = (10, 30, 200)
    axes[1].loglog(sizes, [mean_rollout_error(sweep_model(n), test) for n in sizes], "o-")
    axes[1].set_xlabel("training runs")
    axes[1].set_ylabel("mean rollout error (fraction)")
    axes[1].set_title("Sensitivity to data size")
    dts = (0.5, 2.0, 8.0, 20.0)
    axes[2].loglog(dts, [dt_experiment(d)[0] for d in dts], "o-")
    axes[2].set_xlabel("time step dt (s)")
    axes[2].set_ylabel("one-step error (fraction)")
    axes[2].set_title("Larger dt, larger error per step")
    for ax in axes[1:]:
        ax.grid(alpha=0.3, which="both")
    fig3.tight_layout()
    fig3.savefig(OUT / "audit.png", dpi=120)

# %% [markdown]
# ## Where this stops
# The toy has three species and one slow parameter, and the solver is cheap. A real mechanism has tens
# of species, temperature and pressure as inputs, and a surrogate must be audited over all of them.
# The audit recipe is the same: held-out runs, rollouts (not only one step), a conservation check,
# a deliberate test outside the training range, and a measured speed-up.
