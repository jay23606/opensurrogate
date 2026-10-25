# Quality checklist

Every session in this repo is released only when all ten checks hold.

| # | Check (from the master list) | How this repo meets it |
|---|---|---|
| 1 | Learning objectives and prerequisites are stated clearly | Every session README starts with both |
| 2 | Equations, units, assumptions and variable definitions are correct | Section B of each session; reviewed before release |
| 3 | Graphs have labelled axes, units, legends and sensible scales | The shared app engine draws labelled axes with units; `verify.py` runs every graph |
| 4 | Changing an input correctly updates every dependent output | `verify.py` sweeps every slider and fails on dead controls |
| 5 | Numerical results match hand calculations or trusted references | Section E worked example is re-checked by each `checkpoint.py` |
| 6 | Edge cases, zero and extreme inputs are handled | `verify.py` runs every control at min, default and max and rejects NaN or Infinity |
| 7 | The visual model is clearly distinguished from real behaviour | Every session and app carries the simplified-model notice; Section E compares model with experiment |
| 8 | Worked examples, answers and hints have been reviewed | Section F has a hint and step-by-step solution for each question; independent review before release |
| 9 | Controls are accessible and work on mobile and desktop | Labelled sliders, keyboard focus, responsive layout, light and dark mode |
| 10 | Safety limits and professional-design constraints are stated | Simplified-model notice in every session and app |
