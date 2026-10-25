# Python in 10 minutes (for opensurrogate)

You do not need to be a programmer. This page covers everything the lessons assume.

## 1. Run a file
In a terminal inside the repo folder:
```
python start.py 1
```
This sets everything up the first time and then runs Session 1.

## 2. Reading a lesson
Open `sessions/session-01/lesson.py`. Lines starting with `# %% [markdown]` are explanation. Lines starting with `# %%` start a small step of code. Read top to bottom. In VS Code each step has a "Run Cell" button.

## 3. The five ideas you need
**Variables** hold values.
```python
voltage = 12.0      # volts
resistance = 6.0    # ohms
current = voltage / resistance
print(current)      # 2.0
```

**Functions** package a calculation so you can reuse it.
```python
def power(v, i):
    return v * i
print(power(12, 2))   # 24
```

**Lists and arrays.** A NumPy array holds many numbers and does maths on all of them at once.
```python
import numpy as np
t = np.array([0, 1, 2, 3])
print(3 * t + 2)      # [ 2  5  8 11]
```

**Plots.** Matplotlib draws graphs.
```python
import matplotlib.pyplot as plt
plt.plot(t, 3 * t + 2)
plt.xlabel("time (s)"); plt.ylabel("distance (m)")
plt.savefig("my_plot.png")
```

**Matrices.** A matrix is a grid of numbers. `A @ v` multiplies a matrix `A` by a vector `v`: each output is a row of `A` multiplied term by term with `v` and added up.
```python
A = np.array([[0, -1],
              [1,  0]])    # turns a point by 90 degrees
v = np.array([1, 0])
print(A @ v)               # [0 1]
```

## 4. What to do when something breaks
1. Read the **last line** of the red error text. It names the problem.
2. Check spelling and brackets in the line it points to.
3. Ask on the issue thread or in the Hello FOSS Discord. Paste the full error and say what you tried.

## 5. Your first change
Change one number in a lesson, predict the result, run `python start.py 1` again, and compare. That is how scientists and engineers learn.
