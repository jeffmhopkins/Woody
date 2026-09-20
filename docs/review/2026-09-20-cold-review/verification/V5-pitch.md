# V5 — Falsification of W4 "Blow harder, the pitch bends"

Target: `docs/review/2026-09-20-cold-review/README.md` §W4, and its feeders W2 and W3.
Sources re-read in full: `B3-pitch-chain.md` §1–2, `B5-module-power.md` §3,
`B7-grounding.md` F1, `D3-missing-conditioning.md` §2, `C2-passives.md` F14,
`B4-mod-channels.md` (the missing fifth source, see §1.4), ADRs 0004/0005/0006/0014,
`hardware/bom.csv`, `docs/reference/latency-budget.md`.

No repository file was modified.

**Headline.** The symptom is real. The finding as registered is not. There are not four
independent routes — there is **one aggressor and two mechanisms**, one of which is
contingent on a topology nobody has chosen. The registered total (~52 cents implied by
the table) is **4–8× too high**. My honest figure is **5–15 cents of breath-correlated
sharpening**, and the 2 kHz limb — the single largest entry in the table — is musically
**zero** for a reason none of the five agents tested.

---

## 0. Verdict table

| Route as registered | Claimed | My independent figure | Verdict |
|---|---|---|---|
| 1. Offset ref divider + WS2815 2 kHz ripple | ~22 cents p-p | 1.4–2.2 cents p-p at the node, and **−63 to −88 dBc** as FM. Inaudible at *any* plausible amplitude | **FALSE** (as a musical symptom) |
| 2. Shared 1N5817, ΔV_f with instrument current | ~20 cents | 7–17 cents, centre ~9; **same diode, same node, same divider as route 1** | **DOUBLE-COUNTED with 1**, and **OVERSTATED ~2×** |
| 3. Module internal ground | 5.7–7.2 cents | 3.4–7.7 cents breath-rate; the "7.2" is a *different agent's 2 kHz number* spliced in | **SURVIVES**, range mis-assembled |
| 4. Rack shared bus ground | ~4.8 cents | 1.0–3.5 cents at a common aggressor; **shares the module ribbon with route 3** | **OVERSTATED / partly DOUBLE-COUNTED with 3** |
| W3 "no specified voltage reference" | — | Confirmed by grep: no REF5025/LM4040/VREFOUT/2.5 V pitch source anywhere outside `docs/review/` | **SURVIVES** |
| W3 "a divider from ±12 V is the topology" | — | Not the only possibility, not the default, and the agents disagree on *which* rail | **OVERSTATED — premise unproven** |
| W2 "1 kΩ is a pure gain error" is false | 29.1 / 58.5 / −29.7 cents | 29.4 / 59.1 / **+29.7** cents — algebra re-derived exactly | **SURVIVES** (README's sign on row 3 is wrong) |
| W2 "±600 cents of firmware offset authority" | ±600 | 600 cents arithmetically; ~±400–500 usable | **SURVIVES**, mildly optimistic |

---

## 1. Are the four routes independent? No. One aggressor, two mechanisms.

### 1.1 Routes 1 and 2 are the same route

Trace both to physical origin:

| | Aggressor | Coupling element | Victim node | Transfer |
|---|---|---|---|---|
| Route 1 (B3 §1) | WS2815 current | **1N5817** incremental r, at 2 kHz | offset-reference divider | ×0.208 |
| Route 2 (D3 §2) | WS2815 current | **the same 1N5817**, large-signal ΔV_f | **the same divider** | ×0.208 |

Identical aggressor, identical series element, identical victim, identical transfer
function. ADR 0004's power tree has exactly one `1N5817` on +12 V, with the module-analog
and umbilical branches taken off *downstream* of it — both agents read the same diagram
and described the same node. They differ only in which **frequency component of one
current waveform** they measured: route 2 is the mean of the WS2815 PWM square wave,
route 1 is its peak-to-peak swing. Adding them is like adding a signal's DC term to its
peak-to-peak and calling it two errors.

Worse, the two magnitudes are *mutually inconsistent*. B3 puts 90 mV p-p on the module's
post-diode node at 2 kHz. B5, analysing the same node with the same aggressor, gets
**6.0 mV p-p** — a 15× disagreement that the register resolved by adopting B3's number
for route 1 and B5's model for route 3, from the same table. Both cannot be right.

**Verdict: routes 1 and 2 are one route. Route 1's contribution to it is negligible.**

### 1.2 Routes 3 and 4 are series segments of one path, sharing one conductor

The pitch CV is single-ended against module analog ground; the VCO reads it against its
own. The error is the potential between those two grounds, and the path is:

```
etherCON PWR_GND → [module copper] → 16-pin header GND pins → [module ribbon]
                 → bus board → (VCO's ribbon, carrying ~nothing) → VCO ground
```

B5's route 3 is `20 mΩ module copper + 12.6 mΩ module ribbon = 32.6 mΩ`.
B7's route 4 is `16 mΩ, "module tap to PSU", 4 × 28 AWG over 300 mm`.

**The module ribbon is inside both.** B5 counts it as 6 × 28 AWG at 356 mm (12.6 mΩ);
B7 counts it as part of 4 × 28 AWG at 300 mm (16 mΩ). Same physical connector-to-bus-board
ribbon, two different assumptions, added together.

They are also quoted at **different aggressor currents** — B5 at 145 mA, B7 at 250 mA —
so the register's 5.7 + 4.8 is not even a sum over a common stimulus. Normalised to a
common 150 mA and de-duplicated, the honest series total is **~7.3 cents**, not 10.5.

**Verdict: routes 3 and 4 are one path in two segments. They do add, minus one ribbon.**

### 1.3 So the real structure is

```
ONE aggressor:  breath-modulated WS2815 + matrix current, 130–250 mA

  ├─ Mechanism A (supply side):  ΔI × (diode r + rail series R) × 0.21  → only if the
  │                               pitch offset divides from +12 V        [CONTINGENT]
  └─ Mechanism B (return side):  ΔI × (module copper + ribbon + bus)  × ~1.0
                                                                        [UNCONDITIONAL]
```

The tell is the register's own recommended fix: *one firmware line* — a constant-total-
current animation — kills all four rows at once. Four independent mechanisms do not
share a single point of failure.

### 1.4 The "5.7–7.2 cents" range has a fifth author and the wrong units

`grep` finds no "7.2 cents" in `B5-module-power.md`. It is in
`B4-mod-channels.md:589` — a *different* agent, computing `300 mA p-p × 20 mΩ = 6 mV p-p`
of **2 kHz warble** on the module ground. B5's own two numbers are 5.7 (etherCON tap,
breath-rate) and **2.2** (Kelvin'd to the header). So the register built a range for a
breath-rate error by taking one agent's breath-rate figure as the floor and another
agent's 2 kHz figure as the ceiling, discarding the floor that would have halved it.

This matters for the convergence argument. Four agents did not converge on one number.
Five agents produced numbers spanning 0.36 to 22.5 cents at three different frequencies,
and the register selected the top of each.

---

## 2. Do they add? Yes in sign, no in the way the table implies

Everything traces to one current, so the terms are **perfectly correlated in time** — an
RSS would be wrong. Signs:

- **Mechanism B:** I_LED ↑ → module ground rises above VCO ground → the VCO sees the CV
  *higher* → **sharp**.
- **Mechanism A:** I_LED ↑ → V_f ↑ → post-diode +12 V falls → the divider's +2.5 V falls →
  `Vout = 2·Vdac − Vref_off` rises → **sharp**.

Same sign. They do add coherently where both exist. The register's *composition* claim is
directionally correct even though its enumeration is not.

One second-order term nobody has: the ground rise also lowers the bus +12 V *as seen from
module ground*, so mechanism B is amplified by (1 + 0.21) = **1.21×** when the offset
divides from +12 V. Small, and it argues for the fix rather than against it.

Route 1 does **not** add to any of them — it is at 2 kHz, six decades away in musical terms
(§3.2).

---

## 3. Is each magnitude right? Redone from components.

Conversion: 1 V/oct → 83.333 mV/semitone → **1 mV = 1.200 cents**.

### 3.1 The aggressor current — the one number every route multiplies by

ADR 0014 clamps total lighting at **~3 W** (= 250 mA at 12 V) and calls realistic use
"single hue tracking breath, ~1.5 W" (= 125 mA); the 60/m table gives 0.13 A for that
state. ADR 0005 notes ~120 mA of WS2815 *quiescent* draw, which is constant and not part
of the swing.

So the breath-correlated modulation is **130 mA realistic, 250 mA at the clamp ceiling**.
B5's 145 mA and B7's 150 mA are fine; B7's 250 mA is the ceiling, not "realistic
modulation", and should not be the headline.

### 3.2 Route 1 — 2 kHz WS2815 ripple: **FALSE**

Two independent reasons, either of which is fatal.

**(a) Every ripple number in the review ignores `C-STRIP-BULK`.** B3 computes
`300 mA × 0.3 Ω(diode) = 90 mV` at the module node. B1 computes
`300 mA × 0.93 Ω = 280 mV` at the instrument node. B4 computes `300 mA p-p × 20 mΩ` of
module ground drop. All three pass the *entire* LED AC current up the cable — but ADR 0014
and the BOM specify **470–1000 µF at each of two strip feed points**, precisely so that it
does not. Solving the divider (940 µF ‖ ESR = 0.131 Ω at 2 kHz against ~0.5 Ω of return
path, then the module's own 470 µF umbilical-branch bulk, then the analog branch's
bead + bulk):

| Aggressor | I reaching module node | V at post-diode node | V at analog rail | Offset error |
|---|---|---|---|---|
| 250 mA p-p | 20 mA p-p | 6.7 mV p-p | 5.4 mV p-p | **1.4 cents p-p** |
| 400 mA p-p | 32 mA p-p | 10.6 mV p-p | 8.6 mV p-p | **2.2 cents p-p** |

B5's independent 6.0 mV p-p at the same node corroborates this within 10 %.
**B3's 22.5 cents is overstated by 10–16×.**

**(b) It would be inaudible even at B3's own number.** Nobody computed the modulation
index. FM sidebands need β = Δf/f_m, and f_m here is 2000 Hz:

| Depth | β on a 440 Hz carrier | First sideband |
|---|---|---|
| 1.4 cents p-p (mine) | 0.00009 | **−87 dBc** |
| 22.5 cents p-p (B3's) | 0.00143 | **−63 dBc** |

B7 did exactly this calculation for its own 10–40 Hz case and drew the right conclusion.
B3 asserted "a timbral buzz that will be blamed on the VCO" without it. At −63 dBc it is
not a buzz; it is 40 dB below the DAC's own quantisation floor in perceptual terms. The
divider is linear, so there is no demodulation of the 2 kHz envelope down to breath rate;
the VCO's exponential converter contributes ~0.03 cents of rectified DC at B3's depth.

**3× sensitivity test:** at 3× my ripple the result is 4.2 cents p-p → −78 dBc. At 10×
(i.e. B3's own figure) it is −63 dBc. **The finding does not survive at any amplitude**,
because the killer is the frequency, not the magnitude.

### 3.3 Route 2 — the shared 1N5817: **OVERSTATED ~2×, and contingent**

D3 asserts "roughly 0.32 V at 200 mA and 0.40 V at 400 mA", i.e. ΔV_f ≈ 80 mV and an
implied incremental resistance of **0.4 Ω**. That is too high for a 1 A Schottky. Fitting
`V_f = n·V_T·ln(I/Is) + I·R_s` to the 1N5817 curve the repository itself quotes
(C2: 0.33 V at 0.29 A, 0.40 V at 0.43 A; datasheet max 0.45 V at 1.0 A) gives
n ≈ 1.1, **R_s ≈ 0.135 Ω**, i.e. r_d ≈ 0.21 Ω at 400 mA — of which the log term is a third.

Baseline diode current with LEDs dark: module analog ~45 mA + instrument base
(dev boards 330–400 mA at 5 V → ~180 mA at 12 V, strip quiescent 120 mA, analog ~10 mA)
≈ **345 mA**.

| Aggressor | R_s = 0.05 | **R_s = 0.135 (best fit)** | R_s = 0.30 |
|---|---|---|---|
| +130 mA (realistic) | 4.0 cents | **6.9 cents** | 12.4 |
| +250 mA (clamp) | 7.2 | **12.7 cents** | 23.3 |
| D3's own 200→400 mA | 7.7 | **12.0** | 20.5 |

Adding the rest of the series rail impedance upstream of the branch point (+12 V ribbon
2 × 28 AWG ≈ 38 mΩ, bus board ≈ 20 mΩ, PSU ≈ 10 mΩ) raises the best-fit figures to
**9.1 cents realistic / 17.1 cents at the clamp**.

So: **~9 cents, not 20.** D3's arithmetic is off by ~2× because it took the diode's
incremental resistance from the *chord* of the V_f curve including the logarithmic region.

**3× sensitivity:** at 3× R_s the route gives 21–38 cents and clearly survives; at 1/3×
it gives 4 cents and is marginal. The route is therefore **sensitive to a single
remembered number** (B5's own value for the same diode, 0.057 Ω, is 4× *lower* than my
fit and would give 4 cents). Two agents in this review used diode resistances differing by
**7×** for the same part.

### 3.4 Routes 3+4 — ground IR: **SURVIVES, correctly sized at 3–8 cents**

De-duplicated single model, breath-modulated current only (the DC term is removed by the
offset trimmer at E9 and is not a finding):

| Layout scenario | R total | 130 mA | 250 mA |
|---|---|---|---|
| Naive: analog ref at etherCON, 1 mm trace, VCO mid-rack (20 + 12.6 + 8 mΩ) | 40.6 mΩ | **6.3 cents** | 12.2 |
| Good: Kelvin to header pins, pour (5 + 12.6 + 8) | 25.6 mΩ | **4.0 cents** | 7.7 |
| Best: Kelvin, VCO beyond the module from the PSU (5 + 12.6 + 0) | 17.6 mΩ | 2.7 | 5.3 |
| Bad: thin trace + 2-conductor flying bus (40 + 38 + 25) | 103 mΩ | 16 | 31 |

(Multiply by 1.21 if the offset also divides from +12 V — see §2.)

The patch cable's sleeve shunt changes this by <10 %, as B5 found; I get the same.

**3× sensitivity:** the span *is* 6×, from Kelvin-to-header on a pour with a short bus to
a 1 mm trace on a long flying bus. This is the most robust of the four routes precisely
because it is resistive, unfiltered, and DC-to-daylight — but its magnitude is a **layout
decision that has not been taken**, not a property of the design as committed. B4 says the
same thing in one line: "the good outcome and the bad outcome differ by 20×."

**Where B5 overstates:** its headline 19 cents is the **DC** offset at 485 mA. That is
removed by calibration and is not a dynamic error. Its own dynamic figure is 5.7, and
2.2 with the Kelvin connection it recommends in the same paragraph.

**Where B7 overstates:** it uses 250 mA (the clamp ceiling) and the *whole* module-to-PSU
run, and its 16 mΩ includes the ribbon B5 has already counted.

---

## 4. Is the premise right? No — and this is the strongest attack.

Routes 1 and 2 both require the pitch offset reference to be **a divider from the +12 V
rail**. Checking the repository:

- ADR 0006 names the trimmer as "the offset authority for pitch" and never says what it
  divides. Confirmed.
- `grep -r "REF5025|LM4040|VREFOUT|VREFIN"` outside `docs/review/` returns **nothing**.
  W3's premise — no specified reference — **is correct**.

But "unspecified" is not "the worst case is the default". Four observations:

1. **The agents do not agree on which rail.** B3 and D3 assume **+12 V**. C2 F14 assumes
   **−12 V** and computes 5–12 cents from rack ripple on that basis. Only the +12 V rail
   carries instrument current; the −12 V `1N5817` (BOM `D-REVPOL` qty 2) passes only the
   module's ~40 mA. **Under C2's assumption, routes 1 and 2 are exactly zero** for
   breath-correlated error. Three reviewers, three different topologies, and the register
   picked the one that makes the finding largest.

2. **The design already contains the pattern for this, in the same ADR.** ADR 0006 §"mod
   channels" specifies a **buffered 2.5 V from DAC channel 7** as the shared offset for
   mod 1–4, and argues for it explicitly ("both routes track the same reference"). A
   builder who has just wired that node for four channels reaching for a raw rail divider
   on the fifth — the precision one — is not the default case. It is the *careless* case.

3. **The DAC8568's own VREFOUT is at exactly 2.500 V, on the board, at 2 ppm/°C, sourcing
   20 mA.** Both B3 and D3 identify it as the fix. A reference that is already present,
   already the right voltage, and costs zero parts is at least as likely a default as
   inventing a divider.

4. **Even a rail divider would normally be bypassed.** A 10 kΩ divider with a 10 µF cap on
   the wiper is a 1.6 Hz corner: −62 dB at 2 kHz (route 1 gone outright) and ~6× down at
   a 10 Hz breath envelope (route 2 reduced to ~1.5 cents). This is ordinary practice and
   costs one capacitor.

**So mechanism A is contingent on a choice that has not been made, is not the design's own
pattern, and is removed for free.** Mechanism B (ground IR) is the opposite: it follows
unconditionally from ADR 0004's decision that the module passes the instrument's current,
and no reference choice affects it.

That inversion matters for what the register should say. The durable finding is the
**ground topology**, which is undocumented and unretrofittable. The offset reference is a
*writing* problem, not a circuit problem — and W3 is right that it should be written down.

---

## 5. Is the symptom right? Yes for the ground route, with two caveats.

**Does the LED animation track breath?** Yes, and it is designed to. ADR 0014 makes breath
the default source for both strips and matrix, and the matrix is "generic and assignable,
defaulting to breath". The correlation is real.

**Is it fast enough to matter musically?** The coupling is the question, and it passes:

- Ground IR is purely resistive — DC to MHz, no filter anywhere. Full transmission at
  breath rate.
- The rail path's analog-branch bulk (470 µF into ~0.34 Ω) corners at ~1 kHz, so it
  attenuates nothing at 1–20 Hz.

So both mechanisms are flat across the breath band. β at 6–10 cents and 10 Hz is
0.08–0.13 → **−24 to −28 dBc**, which is audible as a pitch lean, not a texture. B7's
audibility table is the one piece of this analysis that is done correctly.

**Caveat 1 — ADR 0014 slew-limits the drive.** "Drive the LEDs from the post-gate,
slew-limited breath value, not from the raw ADC sample." The slew rate is **not specified
anywhere**. If it is set aggressively (say full-scale in 200 ms) the modulation is pushed
below ~5 Hz, where β rises and the sidebands get *closer* to the carrier — i.e. it sounds
more like drift and less like buzz, but it does not go away. Slew limiting cannot fix this;
only constant-total-current can.

**Caveat 2 — the direction is the musically natural one.** The error is *sharp on
crescendo*, which is what a real wind instrument does. A player may not read 6 cents as a
fault. What they will read as a fault is that the instrument is 6–15 cents flat against
the rest of the patch at *pp* and in tune at *ff*, or vice versa depending on where E9
was calibrated — which leads to the one recommendation nobody made:
**calibrate at E9 with the animation at its mid-state, not blank.**

**On "nobody ever scopes pitch while sweeping the LEDs":** substantially right but
overstated. `docs/reference/latency-budget.md:99` does schedule *"Rack rail ripple, both
directions — scope +12 V at the module with the instrument running"*, which would catch
mechanism A. It does not require the LEDs to be swept, and there is no test at all for
mechanism B. The register's sharper claim (only the breath jack is tested) is wrong in
letter, right in substance.

---

## 6. Is the 1 kΩ refutation right? Yes. Re-derived independently.

Hardware: `V_op = 2·D − 2.5`; jack `V = k·(2D − 2.5)`, `k = R_L/(R_L + 1k)`.
Trim at load A ⇒ `G = 2/k_A`, `B = −2.5/k_A`. At load B with `r = k_B/k_A`:
`V = r(2D − 2.5)`. Firmware scale `s = 1/r` corrects the slope and leaves
**`2.5(1 − r)` volts constant**.

| Trim → play | r | Residual | Cents | DAC-side shift to null it |
|---|---|---|---|---|
| open → 100 kΩ | 0.990099 | +24.75 mV | **+29.7** | 162 LSB |
| 100 k → 50 k | 0.990196 | +24.51 mV | **+29.4** | 161 LSB |
| 100 k → 33 k | 0.980294 | +49.26 mV | **+59.1** | 323 LSB |
| 100 k → open | 1.010000 | −25.00 mV | **−30.0** | −164 LSB |

B3's arithmetic is exact, including its "24.6 mV of DAC-side shift = 323 LSB" (that is the
33 kΩ row, and it checks). **The README's table has a sign error**: it lists
"open → 100 kΩ | −29.7 cents"; it is **+29.7** — loading the output *down* from the trim
condition makes the instrument sharp, not flat. B3's own table says +29.7.

**Does gain trim + offset trim together recover it fully?** Yes, completely. Two trimmers
span a 2-parameter affine map; the offset correction needed is 24.5 mV on a 2.5 V offset
= **0.98 %**, well inside the 5–10 % trim range ADR 0006 specifies. This is worth stating
because it narrows the finding: ADR 0006's **first** mitigation — "calibrate with the real
patch connected" — is unaffected and fully sufficient, as is its second ("use a buffered
mult"). What is false is specifically (a) "it is a pure gain error", (b) "the gain trimmer
has full authority over it", and (c) "the firmware scale factor can cancel it exactly".
The 29 cents only materialises if the player *re-patches to a different load* **and** uses
the scale-factor preset the ADR offers as its third mitigation. That is a smaller failure
than "29 cents sharp on every note" implies, and it is still a real documentation defect,
because the third mitigation is the only one that does not require a screwdriver and is
therefore the one that will actually get used.

**Is ±600 cents of firmware offset authority real?** Arithmetically yes: 0.25 V of
reserved DAC code × gain 2 = 0.5 V at the jack = 600 cents; 3277 LSB of reserve against
161–323 LSB needed. Practically it is ~±400–500 cents, because consuming the full reserve
drives the DAC to 0 or 5.000 V — exactly the saturation and end-of-range nonlinearity the
window was created to avoid, with only 250 mV of AVDD headroom left at the top. The margin
over what is needed is still ~20×, so the conclusion holds.

**W2 verdict: SURVIVES**, with a README sign error and a narrower practical scope.

---

## 7. One honest combined figure

All four rows share one aggressor, so the composition is a coherent sum of at most two
terms, not an RSS of four. At **realistic animation (1.5 W, 130 mA of breath-correlated
swing)**:

| Scenario | Mechanism A (rail) | Mechanism B (ground) | Total, breath-correlated |
|---|---|---|---|
| Offset from a reference (DAC VREFOUT / DAC ch7 / REF5025), Kelvin'd ground | 0 | 4.0 | **~4 cents** |
| Offset from a reference, naive ground | 0 | 6.3 | **~6 cents** |
| Offset divides from +12 V, Kelvin'd ground | 9.1 | 4.8 | **~14 cents** |
| Offset divides from +12 V, naive ground | 9.1 | 7.7 | **~17 cents** |
| Worst credible: +12 V divider, naive ground, full 3 W clamp animation, R_s = 0.3 Ω | 23 | 15 | ~38 cents |
| Offset from −12 V (C2's reading), Kelvin'd ground | 0 | 4.0 | **~4 cents** |

**What a player would actually hear: 5–15 cents of sharpening that tracks the breath
envelope at 1–20 Hz, most likely 6–8 cents.** Plus, separately, a **static** 10–20 cents
if E9 is calibrated with the LEDs dark and the instrument is played with them lit.

The 2 kHz limb contributes **nothing audible** and should be struck from the register.

**Against the design's own yardstick:** the VCO does 3.5 cents over 10 K as slow drift,
and ~3 cents is the static inaudibility floor. 6–8 cents that moves in time with the
player is above both, is the only dynamic term in the budget, and is worth fixing. The
finding's *conclusion* is right. Its arithmetic, its enumeration and its headline number
are not.

**Confidence.**
- That a breath-correlated pitch error exists at all: **very high** (mechanism B is
  unconditional given ADR 0004's decision to pass instrument current through the module).
- That it lands in the 5–15 cent band: **medium**. It is dominated by two numbers nobody
  has: the module's ground-copper geometry (a layout not yet done, 6× span) and whether
  the offset reference is a rail (an undecided topology, 0 or +9 cents).
- That the 2 kHz limb is musically zero: **high**. Two independent reasons, and B5 and B7
  each supply one of them inside this same review.
- That the registered ~52 cents is wrong: **high**.

---

## 8. The one measurement that settles all of it

Ten minutes at E6, with the module in the rack and a dummy load on the umbilical — or at
E9 with the real instrument:

> Hold pitch at a fixed DAC code. Patch pitch into the actual VCO. Scope the **pitch jack**
> DC-coupled at 1 mV/div, **with the scope's ground at the VCO's ground, not the module's**.
> On channel 2, measure module-0 V to VCO-0 V. Ramp the LED field from blank to the 3 W
> clamp at ~1 Hz, then at ~10 Hz.

Reading it:

- **Ch1 moves, Ch2 tracks it 1:1** → mechanism B (ground). Fix at layout: Kelvin the
  analog reference to the header ground pins, pour the umbilical return.
- **Ch1 moves, Ch2 does not** → mechanism A (the offset reference is on a rail). Fix in
  the schematic: take the offset from VREFOUT or the existing buffered DAC ch7 node.
- **Ch1 below 0.5 mV (0.6 cents) with both** → the whole of W4 is wrong for this rack.

A third channel AC-coupled at 2 kHz on the module's post-diode +12 V node settles B3
against B5 directly: if it reads 90 mV, B3 is right about the node and still wrong about
audibility; if it reads ~6 mV, `C-STRIP-BULK` is doing its job and route 1 is dead twice.

**And the fix worth taking before any measurement**, because it is one firmware line and
disarms every row of the table simultaneously: drive the animation as a moving dot or bar
on a **constant-total-current field**. The register already recommends it. The fact that
one line closes all four "independent" routes is the cleanest proof that there were never
four.
