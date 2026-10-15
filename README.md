# Structural & Mathematical Audit: `openai/NavierStokesAndEuler`

This repository contains an architectural, mathematical, and code-level verification audit of the `openai/NavierStokesAndEuler` Lean 4 formalization and its accompanying LaTeX preprint.

By tracing the dependency graph down to its leaf entry points and inspecting the core definitions across both `./NavierStokes/` (Forced 3D Navier-Stokes) and `./Euler/` (Unforced 3D Euler), this audit documents the exact architectural mechanisms used in the formalization—specifically **manuscript-to-codebase specification gaps**, **conditional structure hypotheses (`PhysicalFields`, `StageEstimates`)**, **annular zero-germ cutoffs**, **post-hoc diagonal cutoff schedules**, and a **$10^{25}$ parameter scale divergence** between the LaTeX preprint's explicit constants and Lean's non-constructive `atTop` filter.

---

## Executive Summary of Audit Findings

| Audit Area | Target Directory & Primary Files | Core Technical & Verification Finding |
| :--- | :--- | :--- |
| **1. Documented Manuscript vs. Codebase Gaps** | `./NavierStokes/`<br>`GraphRestriction.lean`<br>`CycleContinuationInvariant.lean`<br>`DiagonalJetBoundsNoOptions.lean` | Multiple modules explicitly document in their headers that they do **not** supply the manuscript's unconditional all-order estimates. Notably, `GraphRestriction.lean` proves a counterexample (`zero_mean_does_not_force_zero`) showing that zero auxiliary mean on the torus does not force zero after restricting to the graph. |
| **2. External Realization Hypotheses & Conditional Assembly** | `./NavierStokes/`<br>`ActualCycleResidualBounds.lean`<br>`GluedStageEstimates.lean`<br>`CandidateAssembly.lean`<br>`MixedCandidateAssembly.lean` | In `ActualCycleResidualBounds.lean` and `GluedStageEstimates.lean`, the physical realization of the stage velocity and pressure fields is passed as an external structure hypothesis (`PhysicalFields` / `PhysicalData`: *"Only the actual physical realization remains external"*). |
| **3. Annular Zero-Germ Cutoffs & Residual Forcing Architecture** | `./NavierStokes/`<br>`ComparatorR3Theorem.lean`<br>`PeriodicResidualLimits.lean`<br>`MixedAxisPreservation.lean`<br>`ActualCandidateAssembly.lean` | Clay Statement (C) (`option_C_of_compact_candidate`) is formalized with $u_0 \equiv 0$ by defining the external force $f(t,x)$ on $[0, 1)$ as the PDE residual $\partial_t u + (u\cdot\nabla)u - \nu\Delta u + \nabla p$. All infinite wave-packet perturbations have a **zero germ on the symmetry axis $r = 0$** (`mixedDiagonal_eq_base_germ`), isolating the blowup at $(t=1, x=0)$ entirely to the Stage-0 self-similar profile `FinalSlowBase`. |
| **4. Exponential Mode Growth & Post-Hoc Cutoff Schedules** | `./NavierStokes/`<br>`ActualCandidateConstruction.lean`<br>`GluedStageEstimates.lean`<br>`MixedCandidateAssembly.lean` | At cycle $j$, active harmonic modes scale up to $\Vert{}k\Vert{} \le 2^{j+1}$ (`cycle_residualBand`), causing stage derivative constants $C_{j,m}$ to grow exponentially with $j$ and $m$. To establish `VanishingJointJets` at $(1,0)$, `exists_schedule` selects a diagonal cutoff sequence $a_j \to \infty$ *after* inspecting the sequence of constants $C_{j,m}$, shrinking stage supports $\{q(t,x) < 1/a_j\}$ into an arbitrarily thin cusp. |
| **5. Preprint Parameter Collapse vs. Non-Constructive `atTop` Filter** | `./Euler/`<br>`PacketInductionScales.lean`<br>`PacketSourceScaleActual.lean`<br>`ph_bound_verification.jl` | Evaluating the preprint's explicit parameter regime ($\log k_J = x_0/J^2 = 100$ or moderate $x_0 = 5.0, J = 3$) violates Lean's own Stage $J$ boundary guards (`initial_shear` and `initial_frequency`) by hundreds of orders of magnitude ($10^{698}$ pressure Hessian spike). Lean's `exists_scales` compiles only by decoupling $X$ from $J$, fixing $J > 89,442$ and $D \ge 2000$ first, and invoking a non-constructive `∀ᶠ X in atTop` filter that pushes $X \ge 10^{25}$ ($k_J \ge \exp(10^{15})$). |
| **6. Upstream Comparator Challenge Disconnect** | `./ComparatorChallenges/`<br>`NavierStokes.lean`<br>`Euler.lean` | The upstream reference files in `ComparatorChallenges/` retain `sorry` placeholders on `EulerExistenceAndSmoothnessR3`, `navier_stokes_breakdown_periodic`, and `NavierStokesExistenceAndSmoothnessRn`, noting: *"Neither the proof root nor the submission imports this reference."* |

---

## Part I: Audit of `./NavierStokes/` (Forced 3D Navier-Stokes)

### 1. Self-Documented Gaps Between the Manuscript and the Lean Code
A direct audit of the module docstrings and theorem statements in `./NavierStokes/` reveals several places where the formalization explicitly diverges from or weakens the unconditional claims of the written manuscript:

* **`GraphRestriction.lean` (Lines 16–18):**
  > *"None of these statements supplies the manuscript's claimed all-order residual estimates."*
  
  Furthermore, `GraphRestriction.lean` formalizes an explicit counterexample (`zero_mean_does_not_force_zero`), demonstrating that a zero auxiliary mean on the torus does **not** force a zero value after restriction to the graph.
* **`CycleContinuationInvariant.lean` (Lines 12–17):**
  > *"This file does not infer that input from smooth incoming primitives alone: an inverse covariance factor may grow at a flat annulus edge, so such an inference would require additional weighted estimates. In particular, the declarations below are a reconstruction algebra, not an unconditional iteration theorem or an assumed physical endpoint extension."*
* **`DiagonalJetBoundsNoOptions.lean` (Lines 9–12):**
  > *"Pointwise stage estimates then give quantitative tail estimates. The stage estimates themselves are explicit hypotheses, not conclusions of the numerical cutoff selection."*
* **`CandidateAssembly.lean` (Lines 10–14, 214):**
  > *"The theorem proves all `CandidateProperties` for these explicit outputs. It does not construct the input fields or the future force... A conditional implication, not a proof that its analytic inputs exist."*

---

### 2. External `PhysicalFields` Hypotheses in Stage Residual Bounds
To prove Clay Statement (C) via the method of manufactured solutions (`option_C_of_compact_candidate` in `ComparatorR3Theorem.lean`, Lines 22–35), the formalization sets the initial velocity to identically zero ($u_0 \equiv 0$) and defines the external body force $f(t,x)$ on $t \in [0, 1)$ as the Navier-Stokes residual of the candidate fields $(u, p)$ (`assembledForce` in `CandidateAssembly.lean`, Lines 20–67; `periodicResidual` in `PeriodicResidualLimits.lean`, Lines 23–35):

$$f(t,x) := \partial_t u + (u \cdot \nabla)u - \nu \Delta u + \nabla p$$

Under Fefferman's Statement (C) formulation, defining $f$ as the PDE residual of a blowing-up field $u$ is valid **if and only if** one proves that all spacetime derivatives of the residual cancel to infinite order at the singularity $(t=1, x=0)$ (`VanishingJointJets`), allowing $f$ to extend smoothly ($C^\infty$) across $t = 1$ via Borel/Whitney extension (`CandidateFromLimits.force` in `MixedPeriodicAssembly.lean`, Line 268).

In `MixedCandidateAssembly.lean` (Lines 52–60), `VanishingJointJets` depends entirely on supplying a witness for `StageEstimates.finite_residual`:

```lean
finite_residual : ∀ J m,
  JetRate (𝓝[SpacetimeEndpoint.openPast 1] (1, (0 : Space))) (PhysicalWaveSum.physicalQ h)
    (fun z => navierStokesResidual (MixedDiagonalResidual.uncutVelocity A B J)
      (DiagonalJetBounds.uncutPrefix P (J + 1)) z.1 z.2) m (gain J - residualLoss m)
```

Tracing `finite_residual` to its provider in `GluedStageEstimates.lean` (Line 298) and `ActualCycleResidualBounds.lean` (Line 473) reveals that `actualStageEstimates` is parameterized by an explicit external realization input `d`:

```lean
(d : ∀ J, ActualCycleResidualBounds.PhysicalData B (N0 + 1)
  (ActualCyclePreservation.state B N0 J).state
  (MixedDiagonalResidual.uncutVelocity A Bdirect J)
  (DiagonalJetBounds.uncutPrefix P (J + 1)))
```

And in `ActualCycleResidualBounds.lean` (Line 473), `PhysicalFields` (which underlies `PhysicalData`) is documented as:

```lean
/-- Only the actual physical realization remains external. Native regularity,
the fixed base equation, and all size estimates are derived in this module. -/
structure PhysicalFields (B N : ℕ) (U : Set Cylinder) (s : StatePoint)
    (u : VelocityField) (P : PressureField) : Prop where
  velocity_germ : ∀ n, N ≤ n → ∀ z ∈ preterminal,
    z ∈ PhysicalResidualTZ.graphSourceTZ (actualBandGraph n) U → ...
```

Rather than unconditionally constructing the global physical primitives in Cartesian coordinates, the residual module assumes `velocity_germ` to identify the Cartesian fields with the cylindrical graph pullback (`polarGraph`) on each dyadic band.

---

### 3. Annular Zero-Germ Isolation & Post-Hoc Cutoff Absorption
Inspecting `ActualCandidateAssembly.lean` (Lines 331–381) and `MixedAxisPreservation.lean` (Lines 33, 115, 212) clarifies how the blowup at $(t=1, x=0)$ interacts with the infinite wave-packet series:

```lean
theorem axis_not_active {w : SpaceTime} (ht : w ∈ PhysicalWaveSum.preterminal)
    (ha : PhysicalGraphBounds.radialProjection w = 0) :
    w ∉ ActualPolarCoverage.active

theorem mixedDiagonal_eq_base_germ :
    mixedDiagonal base p D scales =ᶠ[𝓝 w] SpatialCurl.spatialCurl base
```

1. **Zero Germ on the Blowup Axis ($r = 0$):** Every wave-packet perturbation stage (`particularPotential`, `signedPotential`, `directStages`) is supported strictly inside an active radial annulus $r / q \in [\text{leftRadius}, \text{rightRadius}]$ with $\text{leftRadius} > 0$ (`PrimaryTargetBounds.leftRadius_pos`). Consequently, in a neighborhood of the symmetry axis $r = 0$, all infinite wave-packet corrections vanish identically. The blowup along $x = 0$ (`periodicVelocity_speed_unbounded`, scaling as $(1-t)^{-A(h)}$) is generated purely by the unperturbed Stage-0 self-similar profile `FinalSlowBase`.
2. **Exploding Harmonic Modes in the Active Annulus:** Inside the active annulus $r / q \in [\text{leftRadius}, \text{rightRadius}]$, `FinalSlowBase` produces a non-zero stress error (`stressForce`), which the wave packets iteratively cancel. In `ActualCandidateConstruction.lean` (Line 79), the harmonic mode band doubles at each cycle $j$:
   ```lean
   theorem cycle_residualBand (B N0 j : ℕ) :
       (cycle B N0 j).coefficients.residualBand = 2 ^ (j + 1)
   ```
   Differentiating the harmonic phases $\exp(i k \Phi(z))$ up to order $m$ for $\vert{}k\vert{} \le 2^{j+1}$ introduces factors of $\vert{}k\vert{}^m \le 2^{(j+1)m}$. Summing over these modes in `GluedStageEstimates.lean` (Line 192, `localPotential_bound_of_modes`) causes the stage derivative constants $C_{j,m}$ (`potentialConstant CA j m`) to grow exponentially with $j$ and $m$.
3. **Post-Hoc Diagonal Cutoff Schedule (`exists_schedule`):** To prevent $C_{j,m}$ from breaking convergence as $j \to \infty$, `MixedCandidateAssembly.lean` (Lines 36–46) invokes `exists_schedule` *after* the sequence of constants $C_{j,m}$ is defined, selecting a rapidly growing sequence $a_j \to \infty$ so that the similarity factor $q(t,x)^{\text{gain}(j)}$ absorbs $C_{j,m}$ for $m \le j+2$ on the shrinking sublevel set $\{q(t,x) < 1/a_j\}$.

---

## Part II: Audit of `./Euler/` (3D Euler Parameter Hierarchy)

### 1. Discrepancy Between the Preprint's Explicit Constants and Lean's `ActualBounds`
In Section 5.2 and 5.7 of the LaTeX preprint (and `PacketInductionStage.lean`, Line 110), the base core polynomial degree is hardcoded at $D_0 = 1000$:

```lean
theorem core_cap : P.low.B ≤ gradientConstant * S.X ^ 1000 + 2
```

In `PacketSourceScaleSequence.lean` (Line 30) and `PacketSourceScaleChoice.lean` (Line 147), the previous shear at Stage $J$ ($n = 0$) is initialized at $h_{J-1} = X^{1000}$, and the positive pressure Hessian increment (`goodCost`) is:

$$\text{dH}_J = \delta_J \cdot h_J \cdot h_{J-1} = \exp\left(-\frac{X}{J^3}\right) \cdot \exp\left(\frac{X}{J^5}\right) \cdot X^{1000}$$

Simultaneously, `ActualBounds` in `PacketSourceScaleActual.lean` (Line 217) and `NormalPacketFrequencyGuards.lean` (Line 68) require at Stage $J$:

```lean
structure ActualBounds (J D : ℕ) (C c X θ : ℝ) : Prop where
  normal : UniformBounds J C c 60 (scaleSequence J X) θ
  initial_shear : X ^ 1000 ≤ exp (X / ((J - 1 : ℕ) : ℝ) ^ 7)
  initial_frequency : X ^ D ≤ exp (X / ((J - 1 : ℕ) : ℝ) ^ 4)
```

along with the frequency ratio guard $\frac{80 J^2}{(J-1)^4} \le 10^{-8}$, which forces $J > 89,442$.

**What Our Numerical Audit (`ph_bound_verification.jl`) Proves:**
* **Failure of Moderate / Polynomially Coupled Parameters:** In the written preprint, the initial scale parameter $x_0$ ($X$) is described via moderate prescriptions such as $\log(k_J) = x_0 / J^2 = 100$ (i.e., $x_0 = 100 J^2$). If $x_0 = 100 J^2$ with $J > 89,442$, then $\frac{x_0}{(J-1)^4} \approx \frac{100}{J^2} \ll 1$, whereas $D \ln(x_0) > 2000$ (since $D \ge 2000$), violating `initial_frequency` ($X^D \le \exp(X/(J-1)^4)$) and `initial_shear` ($X^{1000} \le \exp(X/(J-1)^7)$) by thousands of orders of magnitude. Similarly, testing sub-asymptotic parameters ($x_0 = 5.0, J = 3$ in `ph_bound_verification.jl`) yields $\text{dH}_3 \approx 9.33 \times 10^{698} \gg 1$.
* **How Lean's `exists_scales` Sidesteps the Preprint's Coupling (`PacketInductionScales.lean`, Lines 123–160):**
  Lean does **not** use $X = 100 J^2$. Instead, `exists_scales` decouples the quantifiers:
  1. First, it fixes $D \ge 2000$ (`exists_base_power`).
  2. Second, it fixes $J > 89,442$ (`exists_common_guards`) by replacing $X^{1000}$ and $X^D$ with their exponential upper bounds $\exp(X/(J-1)^7)$ and $\exp(X/(J-1)^4)$, eliminating $X$ and $D$ from the stage ratio inequalities.
  3. Third, holding $J$ and $D$ completely fixed, it invokes the asymptotic filter `∀ᶠ X : ℝ in atTop` (`eventually_atTop`) + `Classical.choice` (`PacketInfiniteConstruction.lean`, Line 66) to select an $X$ where the exponential $\exp(X/(J-1)^4)$ eventually overtakes the polynomial $X^D$.
* **The Implied Scale Magnitude:** Because $J > 89,442 \implies (J-1)^4 \approx 6.4 \times 10^{19}$ and $D \ge 2000$, satisfying $\frac{X}{\ln X} \ge D(J-1)^4$ requires:

$$X \ge 10^{25} \implies k_J = \exp\left(\frac{X}{J^2}\right) \ge \exp(10^{15})$$

### 2. How Lean Handles the $t = 0$ $C^\infty$ Derivative Penalty (`PacketInitialScaleSummability.lean`)
At $t = 0$, the $m$-th spatial derivative of the $n$-th wave packet scales with $k_n^m = \exp(m x_n / (J+n)^2)$, which grows faster in $x_n$ than the cubic spike parameter $\delta_n = \exp(-x_n / (J+n)^3)$ decays.

Inspecting `PacketInitialScaleSummability.lean` (Lines 14–31) shows that Lean avoids relying on $\delta_n$ at $t = 0$ by incorporating a uniform backward dispersive decay factor $\exp(-x_n / 8)$ into the initial amplitude (`primaryAmplitude_polynomial` in `PacketGeometryInitialAmplitude.lean`, Line 48):

```lean
theorem high_expansion (J : ℕ) (C c K : ℝ) (p q N m : ℕ) (X : ℝ) (n : ℕ) :
    highMajorant J C c K p q N m X n =
      (K * C ^ N) * ((J + n : ℕ) : ℝ) ^ (p * N) * (scaleSequence J X n) ^ (q * N) *
        exp (-(scaleSequence J X n / 8) +
          (m : ℝ) * (scaleSequence J X n / ((J + n : ℕ) : ℝ) ^ 2) +
          (m : ℝ) * (scaleSequence J X n / ((J + n : ℕ) : ℝ) ^ (7 / 2 : ℝ)) +
          (N : ℝ) * (c * (scaleSequence J X n / ((J - 1 + n : ℕ) : ℝ) ^ 3)))
```

Because $-1/8$ is independent of $n$, the bracket in the exponent becomes strictly negative ($< -1/16$) in the asymptotic tail $(J+n)^2 > 16m$, while the finitely many initial stages $(J+n)^2 \le 16m$ remain a finite sum of smooth functions whose $H^m$ norm grows super-exponentially with $m$.

---

## Repository Contents & Verification Scripts

* `README.md`: This technical audit report.
* `ph_bound_verification.jl`: Arbitrary-precision (8000-bit `BigFloat`) Julia script evaluating the Section 5.2 / 5.7 parameter recursion, demonstrating the $10^{698}$ pressure Hessian coercivity collapse when $h_{J-1} = x_0^{1000}$ is evaluated outside the $X \ge 10^{25}$ regime.
* `extract_lean.v2.py` & `trace.py`: Python extraction scripts filtering `.lake` dependencies to trace forcing and velocity declarations.
* `extract_scales_audit.py`: Python audit script extracting `exists_scales`, `ActualBounds`, `goodCost`, `highMajorant`, and scanning for `Classical.choice` / `sorry` across the repository.
* `extract_ns_toplevel.py`, `dump_final_four.py`, `dump_theorem_1_1.py`, `dump_actual_candidate.py`, `dump_core_residual.py`: Dependency-graph and leaf-module extraction scripts exposing the exact theorem chains in `./NavierStokes/`.
* `scales_and_summability_trace.txt`, `ns_toplevel_trace.txt`, `final_four_dump.txt`, `theorem_1_1_dump.txt`, `actual_candidate_dump.txt`, `core_residual_dump.txt`: Raw extracted Lean 4 source code proofs verifying every citation in this report.
---

## License

This project is licensed under the [Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)](LICENSE) license. Commercial use is prohibited; academic and public citations are required.
