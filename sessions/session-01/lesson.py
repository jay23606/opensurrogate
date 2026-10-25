"""Session 1 (Level 1): a slow simulation replaced by a fast stand-in learned from a few runs.

Run:  python start.py 1
"""
# %% [markdown]
# # Session 1: a fast stand-in for a slow simulation
# **A. Real-world problem.** Some simulations are slow: a combustion engineer may need the answer
# for thousands of fuel mixtures, and each run takes minutes. A *surrogate* is a cheap stand-in:
# run the slow simulation for a modest number of well-chosen inputs, then learn the pattern
# "inputs in, answer out" and use the learned pattern for every other input.
#
# **Plan.** (1) a slow simulation with one input, (2) a surrogate learned from N runs, (3) measure
# the error against the true answer, (4) ask how many runs are enough.
#
# **Still a toy.** The "simulation" here is a single decaying substance, so you can see the
# whole picture. Sessions 2 and 3 use a genuinely stiff chemical system.

# %%
import pathlib
import time

import numpy as np

# where figures are saved (works as a script and in Jupyter/Colab)
OUT = (pathlib.Path(__file__).resolve().parent if "__file__" in globals() else pathlib.Path(".")) / "out"

T_END = 1.0                 # the simulation runs for 1 second
K_LO, K_HI = 0.0, 5.0       # input range: decay rate k in 1/s


# %% [markdown]
# ## Step 1: the slow simulation
# A substance decays at rate `k` (units 1/s): `dy/dt = -k y`, starting from `y = 1` (100 percent).
# The simulation takes many tiny steps (explicit Euler: `y <- y - k y dt`). The *input* is `k`; the
# *answer* is the fraction left after 1 second. The exact answer is `exp(-k)`, which lets us judge
# every surrogate.

# %%
def slow_simulation(k, steps=20000):
    """Fraction left after T_END seconds, by many small Euler steps."""
    dt = T_END / steps
    y = 1.0
    for _ in range(steps):
        y = y - k * y * dt
    return y


def exact_answer(k):
    return np.exp(-np.asarray(k, dtype=float) * T_END)


# %% [markdown]
# ## Step 2: the surrogate = connect the dots
# Run the slow simulation for `n` evenly spaced inputs (the *training runs*). The surrogate answers
# any new input by drawing straight lines between neighbouring training runs (`np.interp`). This is
# the simplest "learned" stand-in; Sessions 2 and 3 replace it by fitted formulas and a neural network.

# %%
def training_runs(n):
    k = np.linspace(K_LO, K_HI, n)
    y = np.array([slow_simulation(v) for v in k])
    return k, y


def make_surrogate(n):
    k, y = training_runs(n)
    return lambda q: np.interp(q, k, y)


def max_error(n, n_test=501):
    """Largest absolute error over a fine grid of test inputs (the fraction left is between 0 and 1)."""
    q = np.linspace(K_LO, K_HI, n_test)
    s = make_surrogate(n)
    return float(np.max(np.abs(s(q) - exact_answer(q))))


def runs_needed(target, n_max=200):
    """Smallest number of training runs whose worst-case error is below `target`."""
    for n in range(2, n_max + 1):
        if max_error(n) < target:
            return n
    return None


# %% [markdown]
# ## Step 3: cost and error
# Building the surrogate costs `n` slow runs once. Every later answer costs almost nothing.

# %%
def time_per_call(fn, repeats):
    t0 = time.perf_counter()
    for i in range(repeats):
        fn(0.5 + 4.0 * (i % 7) / 7.0)
    return (time.perf_counter() - t0) / repeats


# %%
if __name__ == "__main__":
    import matplotlib.pyplot as plt

    OUT.mkdir(exist_ok=True)
    q = np.linspace(K_LO, K_HI, 501)
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.2))
    for n, col in ((3, "tab:red"), (6, "tab:orange"), (18, "tab:green")):
        k, y = training_runs(n)
        axes[0].plot(q, make_surrogate(n)(q), color=col, label=f"surrogate, {n} runs")
        axes[0].plot(k, y, "o", color=col, ms=4)
        axes[1].semilogy(q, np.abs(make_surrogate(n)(q) - exact_answer(q)) + 1e-12, color=col, label=f"{n} runs")
        print(f"{n:3d} training runs: worst-case error {max_error(n):.4f}")
    axes[0].plot(q, exact_answer(q), "k--", label="true answer exp(-k)")
    axes[0].set_xlabel("decay rate k (1/s)")
    axes[0].set_ylabel("fraction left after 1 s")
    axes[0].set_title("Surrogate from N runs (dots)")
    axes[1].set_xlabel("decay rate k (1/s)")
    axes[1].set_ylabel("absolute error (fraction)")
    axes[1].set_title("Error of the surrogate")
    axes[1].set_ylim(1e-6, 1)
    for ax in axes:
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "surrogate_fit.png", dpi=120)

    ns = np.arange(2, 41)
    errs = [max_error(int(n)) for n in ns]
    fig2, ax2 = plt.subplots(figsize=(6, 4))
    ax2.semilogy(ns, errs, "o-", ms=4)
    ax2.axhline(0.01, color="red", ls="--", label="target 0.01")
    ax2.set_xlabel("number of training runs N")
    ax2.set_ylabel("worst-case error (fraction)")
    ax2.set_title("More runs, smaller error")
    ax2.grid(alpha=0.3)
    ax2.legend()
    fig2.tight_layout()
    fig2.savefig(OUT / "error_vs_runs.png", dpi=120)
    print("runs needed for error below 0.01:", runs_needed(0.01))
    t_sim = time_per_call(slow_simulation, 20)
    s = make_surrogate(18)
    t_sur = time_per_call(s, 2000)
    print(f"one slow run {t_sim * 1e3:.2f} ms, one surrogate answer {t_sur * 1e6:.1f} us, ratio {t_sim / t_sur:.0f}")

# %% [markdown]
# ## Where this stops
# Connecting dots needs many runs when there are several inputs (a grid of 18 values per input
# needs 324 runs for two inputs and 5832 for three). Session 2 fixes this with fitted formulas, and
# applies it to a stiff chemical system, where a fast simulation is hard to build in the first place.
