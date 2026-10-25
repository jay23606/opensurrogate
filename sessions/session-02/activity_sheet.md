# Activity sheet: opensurrogate, Session 2: A stiff chemical toy, an implicit solver and a fitted surrogate

Name: ____________________   Date: ____________

**Objectives**

- Explain stiffness: a fast reaction forces tiny steps on an explicit solver but not on an implicit one.
- Write a backward Euler solver with Newton's method and validate it on a case with an exact solution.
- Generate training data from seeded Latin hypercube runs and fit a least-squares polynomial surrogate.
- Show that log scaling helps a species that changes by decades, and size the number of training runs for a target error.

## Before you start: predict
In your own words, what do you think will happen when you change the main slider in the live app?

______________________________________________________________

## Worked example (fill in as you go)
For the fast step dy/dt = -10000 y with y(0) = 1 and a step h = 0.01 s, compute one explicit and one implicit Euler step by hand. Which one makes sense?

1. ______________________________  (hint: k h = 10000 x 0.01 = 100....)
2. ______________________________  (hint: Explicit: y1 = (1 - k h) y0 = (1 - 100) x 1 = -99. The solution should...)
3. ______________________________  (hint: Implicit: y1 = y0 / (1 + k h) = 1 / 101 = 0.0099. It decays, as the ex...)
4. ______________________________  (hint: Rule of thumb: explicit needs k h below 2, here h below 2e-4 s; implic...)

Final answer: ____________________

## Questions
**A. Conceptual.** Why is the explicit stability limit set by the fastest reaction even when we only care about the slow behaviour afterwards?

Answer: ______________________________________________


**B. Numerical.** For dy/dt = -2000 y and h = 0.002 s, compute k h, the explicit factor and the implicit factor. Is explicit Euler stable?

Answer: ______________________________________________


**C. Graph and simulation interpretation.** In the error graph, how does the held-out error change from 10 to 20 to 30 training runs, and why does it stop falling? Is the log fit always better?

Answer: ______________________________________________


**D. Design and optimisation challenge.** Design: you need the held-out RMS error of y1 below 0.003, and below 0.0005. How many runs (from 10, 20, 30, ...) do you need for each? What would you change if you needed 0.0001?

Answer: ______________________________________________

## Self-check
- [ ] I can explain the key idea to a friend
- [ ] My checkpoint printed PASS
- [ ] I tried one change of my own and wrote what happened: ____________________
