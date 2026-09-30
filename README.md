# Structural Audit of OpenAI's Lean 4 Formalization for 3D Forced Navier–Stokes

An examination of OpenAI’s Lean 4 formalization for 3D forced Navier–Stokes (`openai/NavierStokesAndEuler`) reveals an internal structural contradiction between their bounded forcing theorems and the evolution equations used in their blowup mechanism[cite: 85].

---

## 1. The Codebase Contradiction

* **The Bounded Forcing Assumption (`ContinuousAccelerationForcing.lean`, Line 37):** In `forcing_bound`, the proof explicitly caps the iterated derivatives of the acceleration forcing $f$ by a finite prefactor $F$[cite: 85]:
  $$\Vert\text{iteratedFDeriv } \mathbb{R}\ n\ (\text{forcing } Q\ Q_1\ f\ v)\ x\Vert \le (3 \cdot C_0 \cdot (F + 6 \cdot C_1 \cdot V)) \cdot \text{majorant } R\ d\ n$$
* **The Forcing Injection (`TransverseMomentumRegularity.lean`, Line 35):** In `momentumForcing`, the code explicitly injects $+ (\text{timeMultiplier } T\ hT\ Q).\text{adjoint } f$ into the momentum equation[cite: 85].
* **The Evolution Balance (`MeanVelocityPressure.lean`, Line 115):** In `velocity_evolution`, the L2 evolution theorem balances directly to this external forcing function $f$[cite: 85]:
  $$\text{s.velocityDerivative} + \text{timeMultiplier } T\ hT\ M\ \text{s.velocityField} + \text{s.pressureResidual} = f$$

---

## 2. Structural Failure Modes

* **Scenario A:** If $f$ remains bounded by $F$ as proved in `ContinuousAccelerationForcing.lean` (Line 37), $f$ cannot supply the energy required to drive a singularity at high gradients[cite: 85]. Enstrophy remains bounded, and no blowup occurs[cite: 85].
* **Scenario B:** If $f$ forces a blowup, $f$ and its energy density must diverge to $+\infty$[cite: 85]. This violates the $C^\infty$ smoothness and uniform boundedness conditions required for Statement C of the Clay Millennium problem, while directly violating OpenAI's own `forcing_bound` theorem on Line 37[cite: 85].

---

## 3. Repository Contents

* `full_forcing_trace.txt`: Complete algebraic extraction tracing the exact definition blocks for `momentumForcing`, `forcing`, `angularMeanForcing`, and `velocity_evolution` across the primary Lean files[cite: 85].
* `extract_lean.v2.py`: Python extraction utility used to parse the repository and filter out external library dependencies (`.lake` directory)[cite: 81].
* `trace.py`: Extraction script used to isolate top-level declaration blocks matching target forcing terms[cite: 86].

---

## 4. Usage

To run the extraction pipeline locally on a clone of `openai/NavierStokesAndEuler`:

```bash
python extract_lean.v2.py
python trace.py
