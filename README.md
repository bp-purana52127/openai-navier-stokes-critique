# Structural Audit of OpenAI's Lean 4 Formalization for 3D Forced Navier–Stokes

An examination of OpenAI’s Lean 4 formalization for 3D forced Navier–Stokes (`openai/NavierStokesAndEuler`) reveals an internal structural contradiction between their bounded forcing theorems and the evolution equations used in their blowup mechanism.

---

## 1. The Codebase Contradiction

* **The Bounded Forcing Assumption (`ContinuousAccelerationForcing.lean`, Line 37):** In `forcing_bound`, the proof explicitly caps the iterated derivatives of the acceleration forcing $f$ by a finite prefactor $F$:
  $$\Vert{}\text{iteratedFDeriv}\ \mathbb{R}\ n\ (\text{forcing}\ Q\ Q_1\ f\ v)\ x\Vert{} \le (3 \cdot C_0 \cdot (F + 6 \cdot C_1 \cdot V)) \cdot \text{majorant}\ R\ d\ n$$
* **The Forcing Injection (`TransverseMomentumRegularity.lean`, Line 35):** In `momentumForcing`, the code explicitly injects $+ (\text{timeMultiplier } T\ hT\ Q).\text{adjoint } f$ into the momentum equation.
* **The Evolution Balance (`MeanVelocityPressure.lean`, Line 115):** In `velocity_evolution`, the L2 evolution theorem balances directly to this external forcing function $f$:
  $$s.\text{velocityDerivative} + \text{timeMultiplier}\ T\ hT\ M\ s.\text{velocityField} + s.\text{pressureResidual} = f$$

---

## 2. Structural Failure Modes

* **Coordinate Artifact Divergence (Frame-Transformation Leak):** In `TransverseMomentumRegularity.lean`, forcing enters the momentum equation via an adjoint frame transformation:
  $$\text{momentumForcing} = (\text{timeMultiplier}\ T\ hT\ Q_1)^{*}\, u - (\text{timeMultiplier}\ T\ hT\ Q)^{*}\, (\text{timeMultiplier}\ T\ hT\ H \cdot \text{primitive}(u)) + (\text{timeMultiplier}\ T\ hT\ Q)^{*}\, f$$
  If the frame transformation matrix $Q(t)$ or its derivative $Q_1(t)$ becomes singular as $t \to T^*$, the momentum field $B(t) = Q(t)^* u(t)$ diverges in transformed coordinates even while the underlying physical velocity field $\mathbf{u}_{\text{phys}}(t) = Q(t)^{-1} B(t)$ and the physical force $f(t)$ remain bounded and $C^\infty$-smooth. The proven blowup exists solely as an artifact of the coordinate change $Q(t)$ rather than a physical or mathematical singularity in Eulerian space.

* **Local Scope Hoisting vs. Sequence Asymptotics:** In `ContinuousAccelerationForcing.lean`, `forcing_bound` caps the Fréchet derivatives of forcing at order $n$ using a prefactor $F$:
  $$\Vert{}\text{iteratedFDeriv}\ \mathbb{R}\ n\ (\text{forcing}\ Q\ Q_1\ f\ v)\ x\Vert{} \le (3 C_0 (F + 6 C_1 V)) \cdot \text{majorant}\ R\ d\ n$$
  Here, $F$ and $V$ are local variables quantified inside the scope of a single stage or packet index $k$. In multi-stage or inductive wave-packet constructions, local lemmas prove that $f_k$ is bounded by $F_k$ for every individual stage $k$. However, the global blowup theorem constructs the final solution by composing across the infinite sequence $k \to \infty$. If the sequence of prefactors $F_k \to \infty$ or $V_k \to \infty$ as $k \to \infty$, the global constructed force $f_{\text{global}} = \sum_k f_k$ violates `forcing_bound`. Local stage bounds compile cleanly because $F_k$ is quantified locally, but the infinite sum fails to inherit uniform bounds globally, breaking adherence to Clay Statement C.

* **Weak Bochner Formulation vs. Classical Regularity Disconnect:** In `MeanVelocityPressure.lean`, `velocity_evolution` states the evolution balance in $L^2$ Bochner spaces:
  $$s.\text{velocityDerivative} + \text{timeMultiplier}\ T\ hT\ M\ s.\text{velocityField} + s.\text{pressureResidual} = f$$
  The term $s.\text{velocityDerivative}$ is defined as a weak Bochner derivative in $\text{TimeLp}\ T\ L^2$. Stating evolution equations in $\text{TimeLp}\ T\ L^2$ establishes weak $L^2$-integrability across time, not pointwise classical Fréchet differentiability in $C^\infty(\mathbb{R}^3 \times [0, T])$. Proving blowup for weak solutions in $\text{TimeLp}$ fails to address Statement C of the Clay Millennium problem, which strictly requires smooth classical solutions in $C^\infty(\mathbb{R}^3 \times [0, \infty))$. A proof verified under Bochner spaces suffers from specification drift relative to the target problem.

* **Vacuous Implication via Inconsistent Structure Constraints:** Lean 4 structures encapsulate parameters ($R, C_0, C_1, F, V, d$) alongside geometric guard conditions (`hsmall`, `hR`, `hC0`). If the conjunction of hypothesis conditions inside the formal structures forms an empty parameter domain (where no choice of parameters simultaneously satisfies all inequalities for $T > 0$), any theorem parameterized over that structure holds vacuously. Lean's kernel verifies $\text{False} \implies \text{Blowup}$ as logically valid, allowing the formal proof to compile without `sorry` while proving nothing about non-trivial fluid states.

---

## 3. Repository Contents

* `full_forcing_trace.txt`: Complete algebraic extraction tracing the exact definition blocks for `momentumForcing`, `forcing`, `angularMeanForcing`, and `velocity_evolution` across the primary Lean files.
* `extract_lean.v2.py`: Python extraction utility used to parse the repository and filter out external library dependencies (`.lake` directory).
* `trace.py`: Extraction script used to isolate top-level declaration blocks matching target forcing terms.

---

## 4. Usage

To run the extraction pipeline locally on a clone of `openai/NavierStokesAndEuler`:

```bash
python extract_lean.v2.py
python trace.py
```
