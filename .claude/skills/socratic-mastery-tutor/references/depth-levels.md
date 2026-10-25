# Depth levels and regime ladders

The same word means different things at different depths. "Motion" for a child is "things moving"; for a
PhD student it is a curve in a symplectic manifold or a geodesic in curved spacetime. And every law has a
**regime**: Newton's motion is excellent at 30 m/s and wrong at 0.9 c. A learner who wants to understand
*anything from the basics* needs both axes:

- **Depth level (L0-L6)**: how deep the explanation goes: audience, mathematical toolkit, rigour.
- **Regime ladder**: how far each governing parameter is pushed, and which theory takes over at each extreme.

Read this when planning a session, when the learner asks "explain X at level Y" or "explain X at all
levels", and in quick-explain mode.

## Contents
1. The seven depth levels
2. How levels fit the stages and tiers
3. Rules for a correct level ladder
4. The regime ladder method
5. Worked example: "Motion" at every level
6. Worked example: "Motion" through its regimes
7. Short ladders for other subjects
8. Placing the learner on the ladder

## 1. The seven depth levels

| Level | Name | Audience | Mathematical toolkit | "Explained" means the learner can... | Typical sources |
|:--|:--|:--|:--|:--|:--|
| **L0** | Intuition | curious child, total newcomer | none: pictures, stories, everyday objects | say what it is in their own words, recognise it around them | picture books, demos, analogies |
| **L1** | School | ages ~11-15 | arithmetic, ratios, simple formulas, graphs | use the core formula on a number problem; read a simple graph | school textbooks |
| **L2** | Advanced school | ages ~16-18, pre-university | algebra, trigonometry, vectors, intro calculus | solve multi-step problems; derive simple results; use vectors | A-level / AP / IB, Halliday-level intros |
| **L3** | College | undergraduate | calculus, ODEs/PDEs, linear algebra, probability | derive the standard theory and solve the canonical problems | standard undergraduate texts |
| **L4** | Master's | graduate coursework | variational methods, tensors, complex analysis, numerical methods, advanced statistics | reformulate the theory abstractly, generalise it, compute non-trivial cases | graduate texts (e.g. Goldstein, Jackson, Sakurai for physics) |
| **L5** | PhD | researcher in training | the field's modern formalism (differential geometry, functional analysis, group theory, field theory...) | read and critique current papers; prove results; know where the textbooks stop | monographs, review articles, recent papers |
| **L6** | Frontier | the research community | whatever the open problem needs; often not yet settled | state what is unknown, why it is hard, and the competing ideas | recent reviews, conference talks, preprints (flag as unsettled) |

Level names in the KB are `L0` ... `L6`; a range is `L1..L3` (same syntax as tier ranges). The learner's default level
lives in STATE.md (`kb_update.py set-level <kb> L3`); a node's `level:` field is the range the curriculum plans to teach;
`levels_done:` records the ones taught (`kb_update.py set-status <kb> ID doing --levels L1,L2`).

## 2. How levels fit the stages and tiers

Three axes, never confused:

| Axis | Question it answers | Values | Lives in |
|:--|:--|:--|:--|
| **Stage** (Bloom) | *What* does the learner do with the idea? | Terms, Remember, Understand, Apply, Analyze, Evaluate, Create | the 11 session sections |
| **Tier** | In what *order* inside one session? | easy → medium → medium-hard → hard → hardest | Section 3.1-3.5, `tier:` / `tiers_done:` |
| **Level** | *How deep* is the whole treatment? | L0 → L6 | Section 3.6, `level:` / `levels_done:`, Learner level in STATE |

A session is taught **at** a level range: all seven stages and the tier order apply *within* that range. An L1 session
still has an "Analyze" stage (what happens if the speed doubles?) and a "hardest" tier (why can't anything go faster
than light, at L1 language?). An L5 session still starts with Terms. Section 3.6 always shows the *whole* staircase in
one line per level, so the learner sees what lies above and below.

Rough correspondence for planning (not a rule): easy ≈ the bottom level of the range, hardest ≈ one level above the top.

## 3. Rules for a correct level ladder

1. **Lower levels simplify; they never lie.** "Speed is distance divided by time" is a true statement about average
   speed. "Heavier things fall faster" is false at every level: never teach it. When a simplification has a limit, say so
   at that level ("this works when nothing is close to the speed of light").
2. **Each level names what the next one corrects or adds.** That one sentence is the bridge the learner climbs.
3. **The toolkit is honest.** Do not use calculus at L1 or skip it at L3. If a level needs a tool the learner lacks, that
   tool is a term: grep the glossary, recurse (pedagogy.md §3), or `discover` it.
4. **Notation is stable across levels.** Introduce the symbol once (e.g. $v$ for speed) and keep it; at higher levels add
   decorations ($\mathbf v$, $v^\mu$, $\dot q$) and say how they reduce to the old symbol.
5. **Every level gets a figure or a number** (visual-first). At L0 a picture; at L1 a hand calculation; from L2 code.
6. **Above L4, cite.** L5 and L6 statements carry a reference (book + section + page or paper); L6 statements are
   labelled as settled / mainstream / speculative. Never invent a reference.
7. **Recap below, teach the range, preview above.** Levels below the session range: a 3-line recap linking the session
   that taught them. Levels above: one line each in the 3.6 table.

## 4. The regime ladder method

For topic X:

1. **List the governing parameters**: the quantities whose size decides which description is right.
2. **Form the dimensionless signal** for each: compare the parameter with the scale at which new physics (or new
   mathematics, economics, biology...) appears.
3. **Walk each parameter from small to extreme**, and at each step state: what changes, what the old theory predicts,
   what the new theory predicts, and the experiment that showed the difference.
4. **Plot the breakdown**: old and new predictions on one axis versus the signal number (log axis when the range is
   wide). This is the figure for Section 3.7.

Common signals in physical science:

| Parameter | Signal | Regime change when the signal is... | Theory that takes over |
|:--|:--|:--|:--|
| speed | $\beta = v/c$ | not $\ll 1$ (≳ 0.1 for percent-level effects) | special relativity |
| gravity | $\Phi/c^2 = GM/(rc^2)$ | not $\ll 1$ | general relativity |
| size / action | $S/\hbar$, or size vs de Broglie length $\lambda = h/p$ | ~1 | quantum mechanics |
| energy vs rest energy | $E/(mc^2)$ | ≳ 1 (particle creation) | quantum field theory |
| everything at once | length vs Planck length $\ell_P = \sqrt{\hbar G/c^3} \approx 1.6\times10^{-35}$ m | ~1 | unknown (quantum gravity) |
| particle number | $N$ | ≫ 1 | statistical mechanics, continuum mechanics |
| mean free path | Knudsen number $Kn = \lambda_{mfp}/L$ | ≳ 0.1 | kinetic theory (Boltzmann) instead of continuum |
| inertia vs viscosity | Reynolds number $Re = UL/\nu$ | ≳ $10^3$ (pipe flow ~2300) | turbulence |
| sensitivity | Lyapunov time vs prediction horizon | horizon ≫ Lyapunov time | chaos: statistical prediction only |
| temperature | $k_BT$ vs level spacing / interaction energy | ~1 | phase transitions, quantum statistics |

Outside physics the same method works with the field's own signals: sample size vs effect size (statistics), market
size vs agent count (economics), population size vs mutation rate (evolution), input size $n$ vs constant factors
(algorithms: asymptotics only bite for large $n$).

## 5. Worked example: "Motion" at every level

| Level | The idea at this level | Key equation / tool | What the next level corrects or adds |
|:--|:--|:--|:--|
| **L0** | Something moves when it is in a different place a moment later. Fast = covers a lot of ground quickly. | a toy car, a stopwatch, a picture of footprints | "fast" needs a number |
| **L1** | Speed is distance ÷ time. A distance-time graph: steeper line = faster; flat line = stopped. | $v = d/t$; 100 m in 10 s → 10 m/s | direction matters; speed can change |
| **L2** | Position, displacement and velocity are vectors; acceleration is the rate of change of velocity. Constant-acceleration (SUVAT) equations; projectiles. Velocity is the slope of $x(t)$: a derivative. | $v = \frac{dx}{dt}$, $a = \frac{dv}{dt}$, $x = x_0 + v_0 t + \tfrac12 a t^2$ | *why* does velocity change? Forces. |
| **L3** | Newton's laws: $\mathbf F = m\mathbf a$ turns motion into an ODE. Momentum, energy and angular-momentum conservation; non-inertial frames (centrifugal, Coriolis); oscillators; central forces and Kepler orbits. | $m\ddot{\mathbf r} = \mathbf F(\mathbf r, \dot{\mathbf r}, t)$; numerical integration in code | forces are awkward with constraints and odd coordinates |
| **L4** | Lagrangian and Hamiltonian mechanics: the path makes the action stationary. Noether's theorem: every continuous symmetry gives a conserved quantity. Phase space, canonical transformations, small oscillations, rigid bodies; Galilean vs Lorentz invariance. | $S = \int L\,dt$, $\frac{d}{dt}\frac{\partial L}{\partial \dot q} = \frac{\partial L}{\partial q}$; $\dot q = \partial H/\partial p$, $\dot p = -\partial H/\partial q$ | the geometry behind the equations; what happens when the classical picture fails |
| **L5** | Motion as geometry: Hamiltonian flow on a symplectic manifold (Liouville, KAM theorem, integrability vs chaos); free fall as a geodesic of curved spacetime in general relativity; quantum motion as a sum over all paths (Feynman path integral), with the classical path as the stationary-phase limit. | $\omega = dp \wedge dq$; $\frac{d^2x^\mu}{d\tau^2} + \Gamma^\mu_{\alpha\beta}\frac{dx^\alpha}{d\tau}\frac{dx^\beta}{d\tau} = 0$; $\langle x_f|e^{-iHt/\hbar}|x_i\rangle = \int \mathcal D x\, e^{iS/\hbar}$ | these descriptions disagree at the Planck scale |
| **L6** | What is motion when spacetime itself is quantum? Background-independent theories (loop quantum gravity), string theory, emergent spacetime; the "problem of time" (the Wheeler-DeWitt equation has no time parameter). **Status: open; no experimentally confirmed theory.** | $\hat H\Psi = 0$ (Wheeler-DeWitt); Planck length $\ell_P \approx 1.6\times10^{-35}$ m | (the frontier) |

Disambiguate neighbours at every level: speed vs velocity (L2), distance vs displacement (L2), mass vs weight (L3),
proper time vs coordinate time (L5). Cross-disciplinary senses of "motion": a motion in a parliament, motion in music
(voice leading), Zeno's paradoxes and Aristotle's *kinesis* in philosophy, motion pictures (persistence of vision). New
terms met on the way (derivative, vector, action, manifold, geodesic) are recursion targets.

## 6. Worked example: "Motion" through its regimes

| Parameter pushed | Regime | Signal | What changes | Theory that takes over | Evidence |
|:--|:--|:--|:--|:--|:--|
| speed | everyday (car, 30 m/s) | $\beta = 10^{-7}$ | nothing measurable | Newton | daily life |
| speed | GPS satellites (3.9 km/s) | $\beta \approx 1.3\times10^{-5}$ | clocks run ~7 μs/day slow (velocity) | special relativity | GPS clock corrections |
| speed | particle accelerators, cosmic rays | $\beta \to 1$, $\gamma = 1/\sqrt{1-\beta^2} \gg 1$ | momentum $p = \gamma m v$ grows without bound; nothing reaches $c$; time dilates, lengths contract | special relativity | muon lifetimes extended by $\gamma$; LHC protons at $\gamma \approx 7000$ |
| speed | massless particles | $\beta = 1$ exactly | no rest frame; $E = pc$ | special relativity / QFT | photons |
| gravity | Earth's surface vs GPS orbit | $\Phi/c^2 \sim 10^{-9}$ | clocks higher up run fast (~45 μs/day) | general relativity | GPS (net ≈ +38 μs/day) |
| gravity | Mercury's orbit | $\sim 10^{-8}$ | perihelion advances 43″/century beyond Newton | general relativity | Le Verrier / Einstein 1915 |
| gravity | near a black hole | $\Phi/c^2 \to 1/2$ (horizon) | no stable orbit inside $r = 6GM/c^2$; light bends into a ring | general relativity | Event Horizon Telescope images; LIGO waveforms |
| size | atoms | $\lambda_{dB}$ ~ size of the system | no trajectory: position and momentum obey $\Delta x\,\Delta p \ge \hbar/2$ | quantum mechanics | electron diffraction |
| size + energy | particle collisions | $E \gtrsim mc^2$ | particles are created and destroyed | quantum field theory | pair production |
| everything | Planck scale | length ~ $\ell_P$ | spacetime may not be smooth | unknown | none yet |
| number | a gas ($N \sim 10^{23}$) | $N \gg 1$ | track averages, not particles: pressure, temperature | statistical mechanics | ideal-gas law |
| number + collisions | fluids | $Kn \ll 1$ | continuum velocity field $\mathbf u(\mathbf x, t)$ | Navier-Stokes | engineering |
| sensitivity | three bodies, weather | horizon ≫ Lyapunov time | tiny errors grow exponentially | chaos theory | Lorenz 1963 |

The figure for this table: kinetic energy versus $\beta$ on a log axis, Newton $\tfrac12 mv^2$ against relativistic
$(\gamma - 1)mc^2$; the curves agree for $\beta \lesssim 0.1$ and separate sharply as $\beta \to 1$, where the
relativistic energy diverges and the Newtonian one stays finite (≈ 0.5 mc² at β = 1).

## 7. Short ladders for other subjects (shape only; fill in per session)

- **Number**: L0 counting → L1 fractions, negatives → L2 reals, functions → L3 complex numbers, proof, $\epsilon$-$\delta$
  → L4 fields, rings, cardinality → L5 constructions of $\mathbb R$, $p$-adics, set-theoretic foundations → L6 open
  problems (Riemann hypothesis, independence results).
- **Heat**: L0 hot/cold → L1 temperature scale, conduction → L2 specific heat, gas laws → L3 thermodynamic laws,
  entropy, heat equation → L4 statistical mechanics, partition functions → L5 non-equilibrium, fluctuation theorems,
  QFT at finite temperature → L6 black-hole thermodynamics, information paradox.
- **Algorithm**: L0 a recipe → L1 step-by-step instructions, loops → L2 searching/sorting, big-O by counting → L3 data
  structures, recurrences, graph algorithms → L4 complexity classes, randomised / approximation algorithms → L5
  lower bounds, PCP, fine-grained complexity → L6 P vs NP.
- **Money**: L0 swapping things → L1 prices, saving → L2 interest, supply and demand → L3 micro/macro models,
  elasticity → L4 general equilibrium, game theory, econometrics → L5 DSGE, mechanism design, market microstructure
  → L6 open questions in monetary theory, crises.

## 8. Placing the learner on the ladder

At the first session (or when the learner asks "explain X" without saying a level):
1. Ask one or two diagnostic questions *one level apart* (e.g. "Can you differentiate $x^2$?" separates L1 from L2+;
   "Have you met the Lagrangian?" separates L3 from L4).
2. Record it: `kb_update.py set-level <kb> L3`; note the evidence in the Learner profile.
3. Teach at the recorded level; climb one level when the learner answers that level's Section 9 hard/hardest exercise
   unaided; drop one level (and record why) when two consecutive explanations needed a lower-level refresher.
4. If the learner asks for a level explicitly ("explain at PhD level", "explain like I'm five"), that wins for the
   current explanation; do not change the stored level unless they say it is their new default.
