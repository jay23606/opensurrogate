# Activity sheet: opensurrogate, Session 3: A neural surrogate and its honest audit

Name: ____________________   Date: ____________

**Objectives**

- Build a small neural network with hand-coded backpropagation and Adam, and check its gradients numerically.
- Use it as a one-step surrogate, roll it out, and show how the error accumulates over the rollout.
- Remove the mass drift with a conservation-aware output, and compare one-step with multi-step training.
- Audit the surrogate: held-out validation, speed-up, extrapolation failure, data size, noise, time step.

## Before you start: predict
In your own words, what do you think will happen when you change the main slider in the live app?

______________________________________________________________

## Worked example (fill in as you go)
In the toy model (a = 0.95 per step, relative step error eps = 2 percent) compute the true A, the surrogate A and the total-mass drift after 50 steps, with a free output.

1. ______________________________  (hint: True A = 0.95^50 = 0.0769....)
2. ______________________________  (hint: Surrogate factor q = 0.95 x 1.02 = 0.969, so surrogate A = 0.969^50 = ...)
3. ______________________________  (hint: Each step adds eps x A of mass, so drift = eps (1 - q^50) / (1 - q) = ...)
4. ______________________________  (hint: The free network has created 51 percent more mass than exists; a conse...)

Final answer: ____________________

## Questions
**A. Conceptual.** A surrogate has a one-step error of 0.0005 but a rollout error of 0.2 after 80 steps. How is that possible, and what two remedies does this session test?

Answer: ______________________________________________


**B. Numerical.** In the toy with a = 0.95 and eps = 1 percent, how much mass has been created after 100 steps with a free output? What if the output were conserved?

Answer: ______________________________________________


**C. Graph and simulation interpretation.** In the error figure, compare the one-step-trained and the 2-step-trained conserved networks. What do the curves say about error growth and about the mass drift of each?

Answer: ______________________________________________


**D. Design and optimisation challenge.** Design: you must deliver a surrogate with every held-out y1 error below 0.06 over 80 steps, mass drift below 1e-12, and a measured speed-up of at least 50 times over a one-at-a-time solver. Which options from this session do you choose, and which would you avoid? Justify with the numbers.

Answer: ______________________________________________

## Self-check
- [ ] I can explain the key idea to a friend
- [ ] My checkpoint printed PASS
- [ ] I tried one change of my own and wrote what happened: ____________________
