# Structural & Mathematical Audit: `openai/NavierStokesAndEuler`

This repository contains an architectural, mathematical, and code-level verification audit of the `openai/NavierStokesAndEuler` Lean 4 formalization and its accompanying LaTeX preprint. 

By tracing the dependency graph down to its leaf entry points and inspecting the core definitions across both the `./NavierStokes/` (Forced 3D Navier-Stokes) and `./Euler/` (Unforced 3D Euler) directories, this audit exposes critical mechanisms—including **tautological residual forcing**, **annular cutoff isolation**, **non-constructive diagonal cutoff absorption**, and **severe parameter scale discrepancies** between the LaTeX manuscript and the Lean 4 implementation.

---

## Executive Summary of Findings

| Sub-Project | Core Audit Finding | Primary Lean 4 Evidence |
| :--- | :--- | :--- |
| **`./NavierStokes/`**<br>*(Clay Option C / D)* | **1. Tautological External Forcing:** The initial velocity is identically zero ($u_0 \equiv 0$). On $t \in [0, 1)$, the external body force $f(t,x)$ is literally defined as the PDE residual of the synthetic velocity and pressure fields ($f := \partial_t u + (u \cdot \nabla)u - \nu \Delta u + \nabla p$). | `CandidateAssembly.lean`<br>`PeriodicResidualLimits.lean`<br>`ComparatorR3Theorem.lean` |
| **`./NavierStokes/`**<br>*(Blowup Core)* | **2. Annular Cutoff & Synthetic Axis Blowup:** Every infinite wave-packet correction stage vanishes identically in a neighborhood of the symmetry axis $r = 0$. The blowup at $(t=1, x=0)$ is driven purely by a prescribed self-similar base profile (`FinalSlowBase`). | `MixedAxisPreservation.lean`<br>`ActualCandidateAssembly.lean`<br>`ActualCycleResidualBounds.lean` |
| **`./NavierStokes/`**<br>*(Jet Convergence)* | **3. Exploding Harmonic Modes & Cutoff Absorption:** At cycle $j$, harmonic modes range up to $\|k\| \le 2^{j+1}$, causing derivative constants $C_{j,m}$ to blow up with $j$ and $m$. Smoothness across $t=1$ relies on a post-hoc diagonal cutoff schedule $a_j \to \infty$ that shrinks stage supports into an arbitrarily thin spacetime cusp. | `GluedStageEstimates.lean`<br>`MixedCandidateAssembly.lean`<br>`DiagonalJetBoundsNoOptions.lean` |
| **`./Euler/`**<br>*(3D Euler Blowup)* | **4. Stage $J$ Boundary & Coercivity Collapse:** The LaTeX preprint's explicit parameter prescription ($\log k_J = x_0 / J^2 = 100$ or moderate $x_0$) violates the Stage $J$ boundary and pressure Hessian coercivity bounds (`hbase` and `initial_shear`) by hundreds of orders of magnitude ($10^{698}$ spike). | `ph_bound_verification.jl`<br>`PacketInductionStage.lean`<br>`PacketSourceScaleActual.lean` |
| **`./Euler/`**<br>*(Scale Existence)* | **5. Non-Constructive Filter Escape in Lean:** To compile `exists_scales`, the Lean code abandons the paper's polynomial coupling of $x_0$ and $J$, fixes $J > 89,000$ and $D \ge 2000$ first, and invokes an asymptotic filter (`\forall^f X in atTop`) + `Classical.choice` to push $X \ge 10^{25}$ ($k_J \ge \exp(10^{15})$). | `PacketInductionScales.lean`<br>`PacketInfiniteConstruction.lean`<br>`PacketInitialScaleSummability.lean` |

---

## Part I: Audit of `./NavierStokes/` (Forced 3D Navier-Stokes)

### 1. The Manufactured Forcing Mechanism ($f := \text{NSResidual}(u, p)$)
In `ComparatorR3Theorem.lean` (Lines 22–35), the formalization addresses Clay Millennium Problem Option (C) (`option_C_of_compact_candidate`) by supplying an initial velocity field that is **identically zero**:

```lean
theorem option_C_of_compact_candidate
    {u : VelocityField} {p : PressureField} {f : VelocityField}
    (h : R3CompactCandidate.Properties u p f) (ν : ℝ) (hν : 0 < ν) :
    ∃ (u0 : Space → Space) (f : ℝ → Space → Space),
      Comparator.InitialVelocityConditionDecay u0 ∧ Comparator.ForceConditionDecay f ∧
      ¬ (∃ v p, Comparator.NavierStokesExistenceAndSmoothnessRn ν u0 f v p) := by
  refine ⟨fun _ => 0, toComparator (rescaledForce ν f),
    zero_initial_condition_decay, hFd, ?_⟩
```

Because $u_0(x) \equiv 0$, the homogeneous equation has the unique trivial solution $u \equiv 0, p \equiv 0$. The entire finite-time blowup at $T^* = 1$ is driven by the external forcing term $f(t,x)$.

Inspecting `CandidateAssembly.lean` (Lines 20–67) and `PeriodicResidualLimits.lean` (Lines 23–35, 336–365) reveals how this external force is constructed for $t \in [0, 1)$:

```lean
def assembledForce (u : VelocityField) (p : PressureField) (F : VelocityField) :
    VelocityField := fun z =>
  if z.1 < (7 / 8 : ℝ) then
    navierStokesResidual (activatedVelocity u) (activated Pressure p) z.1 z.2
  else F z

theorem assembledForce_eq_residual (u : VelocityField) (p : PressureField) (F : VelocityField)
    (hmatch : ∀ t ∈ Ioo (3 / 4 : ℝ) 1, ∀ x : Space, F (t, x) = navierStokesResidual u p t x)
    {t : ℝ} (ht : t ∈ Ioo (0 : ℝ) 1) (x : Space) :
    assembledForce u p F (t, x) =
      navierStokesResidual (activatedVelocity u) (activatedPressure p) t x
```

Rather than solving the Navier-Stokes PDE for a physically independent body force, the formalization constructs a synthetic blowing-up velocity field $u = \nabla \times A + B$ and defines the external force $f(t,x)$ on $[0, 1)$ to **literally equal the PDE residual**:

$$f(t,x) := \partial_t u + (u \cdot \nabla)u - \nu \Delta u + \nabla p$$

By weak-strong uniqueness (`ViscousUniqueness.lean`), any smooth solution $v$ sharing initial data $u_0 = 0$ and force $f$ must equal $u$ on $[0, T]$ for all $T < 1$, and thus blows up as $t \to 1^-$.

### 2. Annular Cutoff Isolation & The Blowup Core at $r = 0$
For the manufactured residual $f(t,x)$ to qualify as a valid forcing term in `ProblemStatement.lean`, it must extend smoothly ($C^\infty$) across the blowup time $t = 1$ on all of $[0, \infty) \times \mathbb{R}^3$ (`ContDiffOn ℝ ⊤ f futureDomain`).

In `MixedPeriodicAssembly.lean` (Lines 202–275) and `ActualCandidateAssembly.lean` (Lines 331–381, 525–547), the candidate fields `ASum`, `BSum`, and `PSum` are built using cutoff functions $\chi(a_j q(t,x))$, where $q(t,x)$ is a similarity scale (`PhysicalWaveSum.physicalQ h`) that vanishes only at the single spacetime point $(t=1, x=0)$.

* **Away from the origin ($x \neq 0$):** At $t = 1$, $q(1, x) > 0$. Because $a_j \to \infty$, only finitely many terms in the infinite series are active near $(1, x)$. Thus, the fields and their residual are trivially smooth across $t = 1$ for all $x \neq 0$.
* **At the origin ($x = 0$):** In `ActualCandidateAssembly.lean` (`axis_not_active`, Line 370) and `MixedAxisPreservation.lean` (`mixedDiagonal_eq_base_germ`, Line 212), all wave-packet increments are supported strictly inside an active radial annulus $r / q \in [\text{leftRadius}, \text{rightRadius}]$ with $\text{leftRadius} > 0$:

```lean
theorem axis_not_active {w : SpaceTime} (ht : w ∈ PhysicalWaveSum.preterminal)
    (ha : PhysicalGraphBounds.radialProjection w = 0) :
    w ∉ ActualPolarCoverage.active

theorem mixedDiagonal_eq_base_germ :
    mixedDiagonal base p D scales =ᶠ[𝓝 w] SpatialCurl.spatialCurl base
```

Consequently, in a neighborhood of the symmetry axis $r = 0$ (which includes the blowup point $(t=1, x=0)$), **all infinite wave-packet perturbations are identically zero**. The blowup along $x = 0$ (`periodicVelocity_speed_unbounded`, scaling as $(1-t)^{-A(h)}$) is produced entirely by the unperturbed Stage-0 self-similar profile (`FinalSlowBase`).

### 3. Exploding Harmonic Mode Constants & Diagonal Cutoff Absorption
Inside the active annulus $r / q \in [\text{leftRadius}, \text{rightRadius}]$, `FinalSlowBase` generates a non-zero stress error (`FinalSlowBase.stressForce`), which is iteratively canceled to order $q^{\text{gain}(J)}$ by high-frequency wave packets (`ActualCycleResidualBounds.lean` & `GluedStageEstimates.lean`).

Auditing `ActualCandidateConstruction.lean` (Line 79) and `GluedStageEstimates.lean` (Lines 184–195) exposes how derivative growth is handled during this iteration:
1. At cycle $j$, the active harmonic modes $k \in \mathbb{Z}$ range up to $|k| \le 2^{j+1}$ (`cycle_residualBand : (cycle B N0 j).coefficients.residualBand = 2 ^ (j + 1)`).
2. Differentiating the phase $\exp(i k \Phi(z))$ $m$ times introduces factors of $k^m \le (2^{j+1})^m$. Summing over the mode band in `localPotential_bound_of_modes` causes the stage derivative constants $C_{j,m}$ (`potentialConstant CA j m`) to grow exponentially with $j$ and $m$.
3. To prevent these exploding constants from destroying $C^\infty$ convergence at $(1,0)$ (`VanishingJointJets`), `MixedCandidateAssembly.lean` (Lines 36–60) and `DiagonalJetBoundsNoOptions.lean` (Line 133) select the cutoff sequence $a_j \to \infty$ (`exists_schedule`) *after* inspecting the sequence of constants $C_{j,m}$, shrinking the spatial-temporal support $\{q(t,x) < 1/a_j\}$ of stage $j$ rapidly enough to absorb $C_{j,m}$ for $m \le j+2$ into powers of $q(t,x)^{\text{gain}(j)}$.
4. Furthermore, `GluedStageEstimates.lean` (Line 298) and `ActualCycleResidualBounds.lean` (Line 473) parameterize the physical realization via an external structure `PhysicalFields` (`velocity_germ`), pulling back Fréchet jets from cylindrical graph coordinates (`polarGraph`) rather than constructing unconditional global primitives in physical coordinates.

---

## Part II: Audit of `./Euler/` (Unforced 3D Euler Blowup)

### 1. Stage $J$ Boundary Failure & Pressure Hessian Coercivity Collapse
In Section 5.2 and 5.7 of the preprint (and `PacketInductionStage.lean`, Line 110), the inductive stage bounds hardcode a base polynomial degree $D_0 = 1000$:

```lean
theorem core_cap : P.low.B ≤ gradientConstant * S.X ^ 1000 + 2
```

In `PacketSourceScaleSequence.lean` (Line 30) and `PacketSourceScaleChoice.lean` (Line 147), the initial shear at stage $n = 0$ (corresponding to stage $j = J$) is initialized at $h_{J-1} = X^{1000}$, and the positive pressure Hessian increment (`goodCost`) is given by:

$$\text{dH}_J = \delta_J \cdot h_J \cdot h_{J-1} = \exp\left(-\frac{X}{J^3}\right) \cdot \exp\left(\frac{X}{J^5}\right) \cdot X^{1000}$$

Meanwhile, the Stage $J$ boundary guard in `PacketSourceScaleActual.lean` (Line 217) and `NormalPacketFrequencyGuards.lean` (Line 68) requires:
* `initial_shear`: $X^{1000} \le \exp\left(\frac{X}{(J - 1)^7}\right)$
* `initial_frequency` (`hbase`): $X^D \le \exp\left(\frac{X}{(J - 1)^4}\right)$ with $D \ge 2000$
* Particle map / frequency smallness ratio at $j = J$: $\frac{80 J^2}{(J - 1)^4} \le 10^{-8} \implies J > 89,442$

**The Preprint Contradiction:**
* If one follows a moderate parameter initialization (e.g., $x_0 = 5.0, J = 3$, tested in `ph_bound_verification.jl`) or the preprint's polynomial scaling $\log(k_J) = x_0 / J^2 = 100$ ($x_0 = 100 J^2$), the inequalities fail catastrophically.
* Specifically, at $x_0 = 5.0, J = 3$, $\delta_3 = \exp(-5/27) \approx 0.831$, while $h_2 = 5^{1000} \approx 10^{698.97}$, resulting in a pressure Hessian blowup of $\text{dH}_3 \approx 9.33 \times 10^{698} \gg 1$.
* Even if $x_0 = 100 J^2$ with $J > 89,442$, we have $\frac{x_0}{(J-1)^4} \approx \frac{100}{J^2} \ll 1$, whereas $D \ln(x_0) > 2000$, violating `hbase` ($X^D \le \exp(X/(J-1)^4)$) by thousands of orders of magnitude.

### 2. How Lean Bypasses the Contradiction (`PacketInductionScales.lean`)
Inspecting `exists_scales` in `PacketInductionScales.lean` (Lines 123–160) and `PacketInfiniteConstruction.lean` (Line 66) shows how the Lean 4 formalization compiles despite the failure of the preprint's explicit parameter regime:

```lean
def constructionScales : ConstructionScales :=
  Classical.choice (exists_scales (requiredExponent : ℝ)
    (commonThreshold gradientConstant hessianConstant) (Nat.cast_nonneg _))
```

Inside `exists_scales`, Lean enforces a strict quantifier decoupling:
1. First, it fixes $D \ge 2000$ via `exists_base_power`.
2. Second, it fixes $J > 89,442$ via `exists_common_guards` after replacing the true polynomial boundary terms $X^{1000}$ and $X^D$ with the exponential upper bounds $\exp(X/(J-1)^7)$ and $\exp(X/(J-1)^4)$, making the exponent ratios depend solely on $J$.
3. Third, holding $J$ and $D$ constant, it invokes an asymptotic filter (`\forall^f X : ℝ in atTop`) to assert the existence of an $X$ large enough that $X^D \le \exp(X / (J-1)^4)$ and $X^{1000} \le \exp(X / (J-1)^7)$.

Because $J > 89,442 \implies (J-1)^4 \approx 6.4 \times 10^{19}$ and $D \ge 2000$, satisfying $\frac{X}{\ln X} \ge D(J-1)^4$ requires pushing the initial scale parameter to:

$$X \ge 10^{25} \implies k_J = \exp\left(\frac{X}{J^2}\right) \ge \exp(10^{15})$$

### 3. The $C^\infty$ Derivative Majorant (`PacketInitialScaleSummability.lean`)
In `PacketInitialScaleSummability.lean` (Lines 14–31), the $m$-th spatial derivative majorant (`highMajorant`) of the initial wave-packet series scales with frequency $k_n^m = \exp(m x_n / (J+n)^2)$. Because the spike parameter $\delta_n = \exp(-x_n / (J+n)^3)$ has a weaker cubic denominator $(J+n)^{-3} \ll (J+n)^{-2}$, $\delta_n$ alone cannot damp spatial derivatives as $n \to \infty$.

Lean resolves this in `high_expansion` by bounding the initial amplitude at $t=0$ (`primaryAmplitude_polynomial` in `PacketGeometryInitialAmplitude.lean`, Line 48) using a backward dispersive decay factor $\exp(-x_n / 8)$:

$$\text{highMajorant} \propto \exp\left(x_n \left[ -\frac{1}{8} + \frac{m}{(J+n)^2} + \frac{m}{(J+n)^{7/2}} + \frac{Nc}{(J-1+n)^3} \right]\right)$$

Because $-1/8$ is independent of $n$, the bracket becomes strictly negative once $(J+n)^2 > 16m$, leaving the first $n \le \sqrt{16m} - J$ stages as a finite sum of smooth functions whose norm blows up super-exponentially with $m$.

---

## Repository Contents & Verification Scripts

* `README.md`: This comprehensive technical audit report.
* `ph_bound_verification.jl`: Arbitrary-precision (8000-bit `BigFloat`) Julia script testing the Section 5.2 / 5.7 parameter recursion, demonstrating the $10^{698}$ pressure Hessian coercivity collapse at Stage $J$.
* `extract_lean.v2.py` & `trace.py`: Python extraction scripts filtering `.lake` dependencies to trace forcing and velocity declarations.
* `extract_scales_audit.py`: Python audit script extracting `exists_scales`, `ActualBounds`, `goodCost`, `highMajorant`, and scanning for `Classical.choice` / `sorry` across the repository.
* `extract_ns_toplevel.py`, `dump_final_four.py`, `dump_theorem_1_1.py`, `dump_actual_candidate.py`, `dump_core_residual.py`: Dependency-graph and leaf-module extraction scripts exposing the exact theorem chains in `./NavierStokes/`.
* `scales_and_summability_trace.txt`, `ns_toplevel_trace.txt`, `final_four_dump.txt`, `theorem_1_1_dump.txt`, `actual_candidate_dump.txt`, `core_residual_dump.txt`: Raw extracted Lean 4 source code proofs verifying every citation in this report.
