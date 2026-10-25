# Project form (Hello FOSS)

**Project name:** opensurrogate

**Short description:** Build a neural surrogate for stiff kinetics in plain NumPy and audit its rollout error, mass drift and failures, in 3 sessions.

**Full description:** opensurrogate is a beginner-friendly learning repo about surrogate models: cheap learned stand-ins for slow simulations. In three short sessions you go from a lookup table that replaces a slow run, to a stiff three-species chemical system with your own implicit solver and a least-squares surrogate, to a small neural network written in plain NumPy (backpropagation and Adam by hand) that jumps the chemistry forward one time step at a time. You then audit it the way a researcher must: error growth over a rollout, mass conservation, speed-up, and honest failure cases such as extrapolation. Every session follows the same six steps (real-world problem, theory, visual explanation, interactive simulation, worked example, assessment), and has a lesson script, a Colab notebook, a live slider app and a checkpoint that prints PASS or FAIL. The repo is intentionally incomplete: a Target animation and a roadmap show where the community can take it next, such as uncertainty flags, real hydrogen kinetics and element-wise conservation.

**Technologies (comma-separated):** Python, NumPy, Matplotlib, JavaScript, LaTeX

**Repository link:** https://github.com/KrunalPanchal1995/opensurrogate
