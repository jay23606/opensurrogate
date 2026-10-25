# Activity sheet: opensurrogate, Session 1: A fast stand-in for a slow simulation

Name: ____________________   Date: ____________

**Objectives**

- Explain what a surrogate is: inputs in, answer out, learned from runs of a slow simulation.
- Build a lookup-table surrogate from N training runs and measure its error on new inputs.
- Read the error against the number of runs and decide how many runs are enough.
- Say why a surrogate cannot be trusted outside the inputs it was built from.

## Before you start: predict
In your own words, what do you think will happen when you change the main slider in the live app?

______________________________________________________________

## Worked example (fill in as you go)
Build the surrogate from 6 runs (k = 0, 1, 2, 3, 4, 5). What does it answer at k = 2.5, what is the true answer, and what is the error?

1. ______________________________  (hint: The nearest training runs are k = 2 and k = 3: exp(-2) = 0.1353 and ex...)
2. ______________________________  (hint: k = 2.5 is exactly half way, so the surrogate answer is the average: (...)
3. ______________________________  (hint: The true answer is exp(-2.5) = 0.0821....)
4. ______________________________  (hint: Error = 0.0926 - 0.0821 = 0.0105 (a bit above 0.01, so 6 runs are not ...)

Final answer: ____________________

## Questions
**A. Conceptual.** Why can a surrogate built from runs at k = 0 to 5 not be trusted at k = 6? What does it actually answer there?

Answer: ______________________________________________


**B. Numerical.** A surrogate is built from 3 runs (k = 0, 2.5, 5). Find its answer and its error at k = 1.25.

Answer: ______________________________________________


**C. Graph and simulation interpretation.** In the error graph, where is the error largest, and why? What happens to that peak when you add runs?

Answer: ______________________________________________


**D. Design and optimisation challenge.** Each slow run takes 2 minutes. Design: how many runs do you need for a worst-case error below 0.01, and below 0.001? What does the tighter target cost in time? What changes if there are two inputs on a grid with the same spacing?

Answer: ______________________________________________

## Self-check
- [ ] I can explain the key idea to a friend
- [ ] My checkpoint printed PASS
- [ ] I tried one change of my own and wrote what happened: ____________________
