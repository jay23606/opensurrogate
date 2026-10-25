# Visualization catalog (generic chart vocabulary)

The learner wants to learn **all the best visualization charts, diagrams and analysis tools, and the
terms used for them**, taught with the same ladder as the science: remember → understand → apply →
analyze → evaluate → create. Domain-specific charts live in the pack's `<domain>-visualization.md`.
Palette/chart-form decisions beyond `assets/viz_style.py`: use the `dataviz` skill.

## Contents
1. How to teach a chart type (the 6-line card)
2. Catalog by question the chart answers
3. Choosing a chart: decision guide
4. Universal reading and integrity rules
5. Ladder for visualization itself

## 1. The 6-line card (use in every session's Section 8)
For each chart type used, give: **(1) name + synonyms**, **(2) the question it answers / data shape it
needs**, **(3) how to read it** (axes, marks, what "good" looks like), **(4) how it misleads**,
**(5) the matplotlib call**, **(6) where the learner already saw it** (session number) and one variation.
Then log it: `kb_update.py viz-add <kb> --chart "<name>" --session N --used-for "..."`.

## 2. Catalog by question

### A. How does y depend on x? (relationships)
| Chart | Use | Misleads when | matplotlib |
|---|---|---|---|
| Line plot | continuous trend, time series | too many series; unlabeled units; truncated axis | `ax.plot` |
| Scatter | pairwise relationship, clusters, outliers | overplotting hides density | `ax.scatter` (alpha, small `s`) |
| Log-log plot | power laws (slope = exponent) | reading offsets linearly | `ax.loglog`, `set_xscale('log')` |
| Semi-log plot | exponentials; wide dynamic range in one variable | zero/negative values impossible | `ax.semilogy` |
| Compensated plot | make a power law flat to reveal small deviations (e.g. `x^{5/3} y`) | choosing the wrong exponent hides trends | `ax.plot(x, y*x**p)` |
| Dual-axis plot | two units, same x | invents correlations; avoid; use two panels | `ax.twinx` |
| Slope/dumbbell chart | before-vs-after per item | many items | `ax.hlines` + `scatter` |

### B. How do model and reference compare? (evaluation)
| Chart | Use | Misleads when | matplotlib |
|---|---|---|---|
| **Parity plot** (predicted vs actual, 1:1 plot) | model accuracy at a glance: points on the y=x line are perfect | unequal axis limits; no identity line; log data on linear axes | `ax.scatter`, `ax.plot(lim, lim)`, `set_aspect('equal')` |
| Residual plot | structure left in errors (bias, heteroscedasticity) | forgetting a zero line | `ax.scatter(x, y - yhat)` |
| Error histogram / CDF | error distribution and tail | bin choice | `ax.hist`, `ax.ecdf` |
| Bland-Altman plot | agreement between two methods (diff vs mean) | ignoring limits of agreement | `ax.scatter((a+b)/2, a-b)` |
| QQ plot | is data drawn from a reference distribution | over-reading tails on small n | `scipy.stats.probplot` |
| Taylor diagram | correlation + std + RMS error of many models in one polar plot | unfamiliar to readers; needs legend | custom polar axes |
| Convergence plot (error vs h or vs iteration, log-log) | order of accuracy = slope; solver convergence | comparing on unequal cost | `ax.loglog` + slope triangle |

### C. What is the distribution? (statistics)
| Chart | Use | Misleads when | matplotlib |
|---|---|---|---|
| Histogram | shape of one variable | bin width; unnormalised comparisons | `ax.hist(density=True)` |
| KDE / density plot | smooth PDF estimate | bandwidth hides multimodality | `seaborn.kdeplot`, `scipy.stats.gaussian_kde` |
| Box plot | median, quartiles, outliers across groups | hides bimodality | `ax.boxplot` |
| Violin plot | box plot + density | KDE artefacts at edges | `ax.violinplot` |
| ECDF | full distribution without bins | unfamiliar | `ax.ecdf` |
| Joint / hexbin plot | 2-D density | colour-scale saturation | `ax.hexbin` |

### D. What is the structure of a table or matrix? (heatmaps)
| Chart | Use | Misleads when | matplotlib |
|---|---|---|---|
| **Heatmap** | matrix values (correlation, stress tensor, confusion) | colormap non-perceptual; no colorbar; annotation clutter | `ax.imshow` / `pcolormesh` + `colorbar` |
| Diverging heatmap | values with meaningful zero (e.g. correlations) | asymmetric limits move the "zero" colour | `cmap='RdBu_r'`, `vmin=-m, vmax=m` |
| Clustered heatmap | reorder to reveal groups | ordering is a modelling choice | `seaborn.clustermap` |
| Sensitivity/tornado chart | ranked one-at-a-time parameter effects | ignores interactions | `ax.barh` sorted |

### E. How large is each category? (comparison)
| Chart | Use | Misleads when | matplotlib |
|---|---|---|---|
| Bar chart | compare magnitudes across categories | truncated baseline | `ax.bar`, `ax.barh` |
| Grouped / stacked bar | sub-categories; stacked shows composition | stacked hides middle series | `ax.bar` with offsets / `bottom=` |
| Lollipop / dot plot | many categories, cleaner than bars | none serious | `ax.hlines`+`scatter` |
| Radar chart | multi-criteria profile | area/ordering illusions; use sparingly | `projection='polar'` |
| Pie/donut | 2-4 parts of a whole | angles are hard to compare; prefer bars | `ax.pie` |

### F. How does a field vary in space? (fields and geometry)
| Chart | Use | Misleads when | matplotlib |
|---|---|---|---|
| Contour / filled contour | scalar on 2-D grid | few levels hide gradients | `ax.contour(f)` |
| Colour map (pcolormesh) | scalar on structured/unstructured grid | rainbow maps; interpolation smoothing | `ax.pcolormesh`, `tripcolor` |
| Vector / quiver plot | direction and magnitude | dense arrows unreadable; scale confusion | `ax.quiver` |
| Streamline plot | flow topology (paths of a steady field) | seeds bias what you see | `ax.streamplot` |
| Line-integral convolution | dense texture of flow direction | not quantitative | external / custom |
| Slice / profile plot | 1-D cut through a field | cut location cherry-picked | `ax.plot` of `f[:, j]` |
| Isosurface / volume render | 3-D scalar | occlusion; perspective | `plotly`, `pyvista` (if installed) |
| Mesh / grid plot | discretisation quality | none; it is a diagnostic | `ax.triplot`, `pcolormesh(edgecolors='k')` |

### G. How does it vary in time or frequency? (signals)
| Chart | Use | Misleads when | matplotlib |
|---|---|---|---|
| Time trace | raw signal, transients | too long to see detail | `ax.plot` |
| Running mean / block average | convergence of statistics | window choice | `np.cumsum` based |
| Autocorrelation plot | memory, integral time scale | non-stationary data | `ax.plot(lag, rho)` |
| Power spectrum (log-log, PSD) | energy vs frequency/wavenumber; slopes = laws | windowing/leakage; aliasing | `scipy.signal.welch` + `loglog` |
| Spectrogram | frequency content changing in time | resolution trade-off | `ax.specgram` |
| Phase portrait / return map | dynamics, attractors | needs delay choice | `ax.plot(x[:-1], x[1:])` |
| Poincaré section | structure of chaotic systems | sampling choice | scatter |

### H. Uncertainty
| Chart | Use | matplotlib |
|---|---|---|
| Error bars | measurement uncertainty | `ax.errorbar` |
| Confidence / prediction band | model uncertainty | `ax.fill_between` |
| Ensemble spaghetti + mean | run-to-run variability | loop of `ax.plot`, alpha |
| Fan chart | growing forecast uncertainty | nested `fill_between` |

### I. Composition and flow of quantities
| Chart | Use | matplotlib |
|---|---|---|
| Stacked area | budget over time (energy budget terms) | `ax.stackplot` |
| Waterfall | how terms add to a total | bars with `bottom` |
| Sankey | flow of a conserved quantity between stages | `matplotlib.sankey` |
| Budget bar (terms vs position) | balance of equation terms | `ax.plot` of each term |

### J. Concept diagrams (not data)
Flow chart of a method, term-dependency graph (the term tree), block diagram of a model, schematic of
geometry with dimensions. Tools: matplotlib patches/annotations, `networkx` for term graphs, TikZ inside
the .tex for schematics (note: TikZ does not reach the .docx; use matplotlib PNGs when both must match).

## 3. Choosing a chart: decision guide
1. Compare model with reference → **parity** (magnitude) + **residual** (structure).
2. Power law or wide dynamic range → **log-log**, add a slope triangle and a **compensated** version.
3. A matrix of numbers → **heatmap** with a diverging map if zero is meaningful.
4. A field on a grid → **filled contour** + **streamlines/quiver** for vectors + **profile cuts** for numbers.
5. Statistics of a signal → **trace**, **histogram/PDF**, **autocorrelation**, **spectrum**.
6. Convergence/accuracy → **error vs resolution, log-log**, read the slope as the order.
7. Ranking of effects → **tornado / sorted bar**.

## 4. Universal reading and integrity rules
- Label axes with quantity **and units** (or "dimensionless"). Give every figure a caption that says what to look at.
- Use perceptually uniform, colour-blind-safe colormaps (`viridis`, `cividis`; diverging: `RdBu_r`, `coolwarm`). Never `jet`/rainbow for quantitative data.
- Always include the reference (identity line, theory curve, benchmark point) so "good" is visible.
- Same axes limits when panels are compared; state when they are not.
- Show uncertainty or resolution limits when they exist; show the data before the smooth curve.

## 5. Ladder for visualization itself
Remember the names → understand what each mark encodes → apply by producing it with real data →
analyze what it reveals and hides → evaluate alternatives for the same data (redraw one dataset three
ways and compare) → create a new composite figure (e.g. parity + residual + error-histogram panel).
