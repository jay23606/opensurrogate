# Roadmap: the path to the opensurrogate Target

This is the path, not the code. Each milestone says what you learn, what you build, and how you know it works. Pick one and open a pull request. See [CONTRIBUTING.md](../CONTRIBUTING.md).

## Session 4: Know when you are outside

**You will learn:** Ensembles of networks and how disagreement between members signals extrapolation.

**You will build:** An ensemble of five networks with a flag that raises an alarm for inputs outside the training range.

**Checkpoint (not met by the shipped code):** Flag at least 90 percent of the test runs with k1 in 0.07 to 0.09 (where the shipped network errs by about 0.96) while flagging fewer than 10 percent of in-range runs (the shipped code flags none).

**Difficulty:** intermediate

## Session 5: Tame the worst case

**You will learn:** Why the worst held-out run, not the mean, decides whether a surrogate can be used.

**You will build:** A training recipe (more rollout steps, loss weights on the fast transient, a better loss for species B) aimed at the worst case.

**Checkpoint (not met by the shipped code):** Worst-case y1 error below 0.02 over 100 held-out runs and 80 steps, with exact mass (the shipped conserved network has 0.056).

**Difficulty:** intermediate

## Session 6: One network for many time steps

**You will learn:** Time step as an input, and the trade-off between step size and error per step.

**You will build:** A network that takes dt as an extra input and works from dt = 0.5 s to 20 s.

**Checkpoint (not met by the shipped code):** One-step error below 0.005 at dt = 20 s (the shipped network trained for 20 s has 0.031).

**Difficulty:** advanced

## Session 7: Beat the vectorised solver

**You will learn:** Fair benchmarking: what to compare a surrogate with, and where the time goes.

**You will build:** A faster surrogate (smaller or batched in a smarter way) and a careful timing report.

**Checkpoint (not met by the shipped code):** At least 30 times faster than the vectorised implicit solver for 1000 runs (the shipped network is about 5 times faster), with the timing method written down.

**Difficulty:** advanced

## Session 8: Real hydrogen kinetics and element conservation

**You will learn:** Real mechanisms conserve elements (H and O), not a plain sum of fractions.

**You will build:** The same pipeline for an 8-species hydrogen-oxygen mechanism, with a conservation-aware output layer for each element.

**Checkpoint (not met by the shipped code):** Element drift below 1e-6 over 100 steps with a mean held-out error below 5 percent (the shipped code handles 3 species and conserves only the sum).

**Difficulty:** advanced

## The final step

Combine the milestones: a conservation-aware network that flags its own extrapolation, works across time steps, beats the vectorised solver and is audited on a real mechanism. If your result looks like the Target animation, open a pull request and tell us how you did it.
