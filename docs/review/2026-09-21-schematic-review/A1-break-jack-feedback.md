# A1 — Adversarial: break the jack-side pitch feedback

**Target decision (2026-09-21):** pitch DC feedback moves to the *jack* side of
`R-OUT-PROT`; `C-FB-PITCH` (1 nF, op-amp output → inverting input) hands the
loop back to the op-amp above ~16 kHz and "doubles as the reconstruction
filter"; `C-FILT-PITCH` (10 nF to ground at the jack) is **deleted**.

Sources read: `hardware/module/pitch-stage.md`, `docs/decisions/0006-cv-channel-allocation.md`
(lines ~300–645), `hardware/bom.csv`. Brief: assume it is a mistake and break it.

---

## VERDICT

**Split. The tap SURVIVES; the deletion is BROKEN.**

| Half of the decision | Verdict |
|---|---|
| **Tap DC feedback at the jack, compensate with a feedback cap** | **SURVIVES.** I could not break it. Loop phase margin is 73–77° and *load-independent* across every load I could construct, from a bare jack to 330 nF. The DC benefit is exactly real: gain at the jack is 2.020000 for every load from open to 2 kΩ. |
| **"One part doing both jobs" — `C-FILT-PITCH` deleted, `C-FB-PITCH` 1 nF is now the reconstruction filter** | **BROKEN.** A feedback capacitor around a **gain-of-2 non-inverting** stage cannot attenuate more than **6.02 dB — ever, at any frequency, for any capacitor value.** It is a shelf, not a pole. The module now has **no filter of any kind anywhere in the pitch signal path.** This break needs no datasheet. |
| **Conditional riders** | Closed-loop **ringing** at the jack for C_load ≳ 10 nF (reachable from this module's own MOD and BREATH jacks via a passive mult); short-circuit behaviour changes from benign to **rail-and-recover**; `R-OUT-PROT` worst-case dissipation rises 2.5×; `TRIM-GAIN`'s stated rationale is invalidated by the same change that shrank it. |

**One sentence:** the change is electrically sound and the ADR was wrong to
decline it — but it was sold with a second claim that is arithmetically false,
and it silently deleted the only capacitor in the pitch path to do it.

---

## 0. What I modelled, and what is gated

Op-amp model (`[from memory]`, ti.com proxy-blocked, so every number below that
uses it is gated):

| Parameter | Value used | Gated? |
|---|---|---|
| OPA2197 GBW | 10 MHz | **Yes.** Phase-margin numbers scale with it. |
| Second pole | 30 MHz (→ ~72° unity-gain PM) and 10 MHz (→ ~45°), both run | **Yes** |
| Open-loop R_out | swept 50 / 100 / 300 Ω | **Yes**, but the result is insensitive across that range |
| Output current, slew rate | 20 V/µs assumed for one calculation | **Yes**, flagged where used |
| Input-pin abs-max current / HBM rating | not assumed | **Yes**, §6 conclusion left open |

Circuit as drawn `[repo: pitch-stage.md:13–37]`: R1 = 10 k (N→V_ref),
R2 + TRIM-GAIN = 10.2 k (N→jack), C_fb = 1 nF (N→op-amp output),
R_p = 1 kΩ (op-amp output→jack), BAV99 on the op-amp-output side.

Solved as a 3-node complex nodal system (N, op-amp output, jack) with the amp as
`A(s)` behind `R_ol`; loop gain by breaking at the inverting input. Script in
the session scratchpad; all results below are reproducible from the component
values given.

---

## 1. The attack that failed: stability. It does not oscillate.

I went after this hardest because it is where ADR 0006 originally balked
(`[repo: 0006:474–479]` "real stability work, on a board without one").

**Loop phase margin, GBW 10 MHz, second pole 30 MHz, R_ol = 100 Ω** `[calc]`:

| Load at the jack | `C_fb` = 1 nF (as drawn) | `C_fb` = 22 pF (the prior art) | `C_fb` = 0 |
|---|---|---|---|
| open jack, no cable | f_c 9.5 MHz, **PM 73°** | 9.4 MHz, 77° | 4.6 MHz, 81° |
| one 100 k VCO, 2 m cable (200 pF) | 8.6 MHz, **PM 74°** | 8.4 MHz, 83° | 1.8 MHz, **20°** |
| four VCOs on a passive mult, 8 m (800 pF, 25 k) | 8.6 MHz, **PM 74°** | 8.5 MHz, 84° | 0.94 MHz, **10°** |
| passive mult with a 1 nF input | 8.6 MHz, **PM 74°** | 8.5 MHz, 84° | 0.77 MHz, **8°** |
| 10 nF at the jack | 8.6 MHz, **PM 74°** | 8.5 MHz, 84° | 0.27 MHz, **3°** |
| this module's MOD out (1 k ∥ 82 nF) | 8.6 MHz, **PM 74°** | 0.035 MHz, 51° | 0.09 MHz, **2°** |
| this module's BREATH out (1 k ∥ 330 nF) | 8.6 MHz, **PM 74°** | 0.017 MHz, **24°** | 0.05 MHz, **1°** |

Three things fall out, and none of them help the attack:

1. **The 1 nF column is flat.** Crossover and phase margin are the *same* for a
   bare jack and for 330 nF — a 1650:1 range of load capacitance. That is
   exactly what in-loop compensation is supposed to do, and it does it. Above
   ~16 kHz the loop is closed locally at the op-amp and `R-OUT-PROT` isolates
   everything beyond it. I could not find a load that moves it.
2. **The chosen value is more conservative than the prior art.** 22 pF hands
   over at 1/(2π·10.2k·22p) = **709 kHz** `[calc]`; 1 nF hands over at
   **15.6 kHz** `[calc]`. Handing over 45× earlier means the R_p·C_L lag is 45×
   further outside the loop. At 330 nF the 22 pF version is down to 24° PM and
   the 1 nF version is untouched. **1 nF is the safer part, not the risky one.**
3. **The `C_fb` = 0 column is the real finding here:** without the cap this
   stage is marginal into *one VCO on one cable* (20° PM) and unstable-looking
   into anything bigger. So `C-FB-PITCH` is genuinely load-bearing — a DNP, a
   wrong value, or an open solder joint turns the pitch output into an
   oscillator. `[repo: pitch-stage.md:173–175]` already calls this the
   highest-risk item; that framing is correct and should stay.

Repeating with the second pole at GBW (a deliberately worse amp, ~45° unity-gain
PM) drops every 1 nF entry to ~52–60° and still leaves the column flat. **Gated
on GBW and on OPA2197 being unity-gain stable** — but both of those are also
required for the *existing* mod channels, so nothing new is being risked.

**I cannot break this on stability. What would have broken it:** an op-amp whose
open-loop output resistance were high enough (≥ ~3 kΩ) that `R-OUT-PROT` stopped
dominating the isolation, or a `C_fb` small enough to hand over above the R_p·C_L
pole. Neither is the case here.

---

## 2. The break: the cap cannot do the second job. Ever.

`[repo: pitch-stage.md:167–169]` — "The 15.9 kHz reconstruction pole comes from
`C-FB-PITCH` instead, **which is the same corner in a better place**."
`[repo: 0006:601–602]` — "which is also the reconstruction pole, **so it is one
part doing both jobs**."

Same corner, yes. Same filter, no — and this is arithmetic, not a judgement call.

For a non-inverting stage with R1 = R2 = R and C across the feedback leg:

```
Gain(s) = 1 + Z2/R1,   Z2 = R ∥ 1/sC
        = 1 + [R/(1+sRC)]/R
        = (2 + sRC) / (1 + sRC)
```

`[calc]` A **pole** at 1/(2πRC) = 15.9 kHz and a **zero** at 2/(2πRC) =
**31.8 kHz — exactly one octave above it.** DC gain 2, high-frequency gain
**1**, and it stays at 1 forever. Total attenuation available:

```
20·log10(A_DC / A_HF) = 20·log10(2/1) = 6.02 dB
```

**A feedback capacitor cannot take a non-inverting amplifier's gain below unity.**
That is topology, not component choice: at C → ∞ the stage is a follower, gain 1.
For a gain-of-2 stage — which pitch is, exactly and by construction
`[repo: pitch-stage.md:50]` "Slope 9 V / 4.5 V = exactly 2.000" — the ceiling is
6.02 dB. Picking a different capacitor moves the corner and changes nothing else.

What that costs against the part that was deleted, both normalised to DC gain
`[calc, 3-node solve, one 100 k VCO on 2 m of cable]`:

| Frequency | `C-FB-PITCH` 1 nF (new) | `C-FILT-PITCH` 10 nF at jack (deleted) | Attenuation lost |
|---|---|---|---|
| 4 kHz (the ZOH image) | −0.24 dB | −0.27 dB | 0.02 dB |
| 16 kHz | −2.35 dB | −3.03 dB | 0.68 dB |
| 31.8 kHz | −4.27 dB | −6.98 dB | 2.71 dB |
| 100 kHz | **−5.86 dB** | −16.07 dB | **10.2 dB** |
| 1 MHz | **−9.65 dB** | −35.96 dB | **26.3 dB** |
| 10 MHz | −28.3 dB | −55.96 dB | 27.7 dB |

(The new response does eventually roll off again above ~900 kHz — but only
because the *patch cable's* 200 pF works against R_p. **Unplug the cable and
the pitch output is flat at −6 dB from 31.8 kHz to the op-amp's own bandwidth.**
The design's only remaining HF rolloff is supplied by the user's cable.)

**And there is nothing else.** Grepping every `C-` row in `hardware/bom.csv`:
the pitch signal path contains **exactly one capacitor, `C-FB-PITCH`**
`[repo: bom.csv]`. There is no anti-alias cap on the DAC output, none on
`R-OPAMP-IN`, none at the jack. Breath has 330 nF, mod has 82 nF, pitch now has
a 6 dB shelf.

**Honest scoping — the loss is not "reconstruction".** At the 4 kHz update rate
`[repo: 0006:183]` both parts attenuate the image by ~0.25 dB, i.e. nothing, and
ADR 0006 already concedes this (`[repo: 0006:198–200]` "a 15 kHz reconstruction
filter attenuates that by 0.07 dB, which is nothing"). So the deleted 10 nF was
never a reconstruction filter either. What it actually was, and what was
actually lost, is **the only low-impedance shunt at the connector**:

- 10–26 dB of DAC code-transition glitch and SPI-clock feedthrough in the
  100 kHz–1 MHz decade, where that energy lives.
- The only capacitive sink for RF arriving *in* on a 2 m unshielded patch cable.
  The project makes exactly this argument against itself elsewhere:
  `[repo: bom.csv C-FILT-BREATH]` "AHEAD of the amp, not after — a filter after
  it cannot stop RF rectification from a 2.4 GHz radio 2 m away." The pitch jack
  is now a 2 m antenna wired through 10.2 kΩ into a precision inverting input
  with no shunt at the connector. Whether that rectifies is **gated on the
  OPA2197's EMIRR**, which I cannot read.
- Edge-rounding on hot-patch transients (§5).

**So the correct statement is not "same corner in a better place." It is: the
compensation job is done well, the filter job is not done at all, and no value
of `C-FB-PITCH` can do it.**

---

## 3. The prior art cited does not do what was done

`[repo: 0006:597–598]` — "All four surveyed DAC-driven designs do both, **with a
single 18–22 pF part**."
`[repo: pitch-stage.md:158]` — "They are not the same part, and **three of those
four designs ship both**."

The survey is used to license the change and then contradicted twice by it:

1. **Value.** The prior art's lead cap is 18–22 pF. This design ships **1 nF —
   45× to 55× larger** — precisely so it can claim the filtering job. Nothing in
   the corpus supports 1 nF. (For stability 1 nF is *better*, per §1; the
   deviation is fine on its merits, but it is not what the citation says.)
2. **Deletion.** "Three of those four ship **both**" is offered as proof that a
   compensation cap and an output filter can coexist — and the very next section
   deletes the output filter. `[repo: 0006:590–592]` says where prior art
   filters hard "it does so **upstream of the output stage or actively**." This
   design has no upstream filter and no active filter. **The three designs that
   "ship both" have a real filter somewhere. This one now has none.**

That is the cleanest form of the break: the argument proves that both parts can
exist, and is then used to justify removing one of them.

---

## 4. It does not oscillate — it rings. And the load that makes it ring is on this module's own panel.

Loop stability (§1) and the response *at the jack* are different transfer
functions. Solving the closed loop exactly gives, for the jack node:

```
V_jack/V_dac = (2 + sτ₂) / (1 + sτ₂ + s²τ₁τ₂)
    τ₂ = R2·C_fb = 10.2 µs      τ₁ = R_eff·C_load,  R_eff = R_p ∥ R2 ∥ R_load
    Q = √(τ₁/τ₂)
```

`[calc]` — a second-order response whose damping is set by the *ratio* of the
load time constant to the feedback time constant. Exact 3-node solve `[calc]`:

| Load at the jack | C_load | Q | Peak | Step overshoot |
|---|---|---|---|---|
| 2 m cable, one VCO | 200 pF | 0.13 | +0.00 dB | 0% |
| 8 m, four VCOs on a passive mult | 800 pF | 0.26 | +0.00 dB | 0% |
| passive mult with a 2.2 nF input | 2.2 nF | 0.44 | +0.00 dB | 0% |
| **10 nF (= the deleted `C-FILT-PITCH`)** | 10 nF | 0.94 | **+1.13 dB @ 10.9 kHz** | 14% |
| 22 nF | 22 nF | 1.39 | +3.46 dB | 30% |
| **this module's MOD out (1 k ∥ 82 nF)** | 82 nF | 1.96 | **+3.36 dB @ 4.7 kHz** | **44%** |
| **this module's BREATH out (1 k ∥ 330 nF)** | 330 nF | 3.93 | **+8.83 dB @ 2.6 kHz** | **67%** |

Read this two ways.

**(a) The headline attack still fails.** Patch cable capacitance *cannot* get
there. 100 pF/m × 8 m of cable is 800 pF and Q = 0.26 — overdamped. To reach
Q = 1 you need ~11 nF at the jack; to reach Q = 2, ~45 nF. **No stack of cables
and VCO inputs reaches that.** The brief's "what does a stack of patched
destinations do?" — answer: nothing. Four destinations on 8 m of cable is
Q = 0.26 and 0% overshoot.

**(b) But two jacks on this module's own front panel do.** `C-FILT-MOD` is
82 nF and `C-OUT-BREATH` is 330 nF, both specified **"ON THE JACK SIDE of
`R-OUT-PROT`"** `[repo: bom.csv, both rows]`. Join PITCH to MOD 1 or to BREATH —
with a passive mult, or by output-to-output patching, which the `R-OUT-PROT` row
explicitly exists to survive (`[repo: bom.csv R-OUT-PROT]` "survives shorts and
output-to-output patching") — and the pitch output rings at 44% or 67%
overshoot on every note change. 67% of a 1 V octave step is **9 semitones of
transient pitch overshoot**, decaying over ~200 µs at 2.6 kHz. That is an
audible chirp on every note.

This is not a break of the decision — it is still stable, and it needs a
mis-patch — but it is a **new failure mode that did not exist before today**.
Under op-amp-side feedback, `R-OUT-PROT` isolates any load capacitance
completely and the worst a mult with MOD can do is a DC divider. It is worth one
line in the page: *the pitch output is no longer safe to passively mult against
another capacitively-loaded output.*

Related behavioural change, unstated anywhere: **the pitch jack's DC source
impedance is now ~0 Ω, not 1 kΩ.** Up to 16 kHz the loop makes it a stiff
voltage source. Anyone passively mixing two CVs by joining outputs — a common
rack hack, and the case the 1 kΩ was chosen for — now has pitch *fighting* the
other source instead of blending with it (§5 numbers).

---

## 5. Short circuit and hot-patching: benign → rail-and-recover

This one does bite, and it is not written down anywhere.

**With the jack at 0 V, the DC feedback factor is exactly zero.** β_DC =
(R1/(R1+R2))·H, and H = V_jack/V_op-amp = 0 into a short. There is no DC loop at
all. The inverting input is then held by the divider from V_ref:

```
V(−) = V_ref · R2/(R1+R2) = 2.500 × 10.2/20.2 = 1.262 V   [calc]
V(+) = V_dac ∈ [0.25, 4.75] V
```

`[calc]` So for every note whose output is **below 0 V** (V_dac < 1.262 V — i.e.
the bottom two octaves of the −2…+7 V range) the amp slams to **−11.9 V**, and
for every note above it slams to **+11.9 V**. The op-amp saturates on every
short, at both ends.

| | Old (feedback at op-amp output) | New (feedback at jack) |
|---|---|---|
| Jack shorted, op-amp output | its target, ≤ +7.5 V | **±11.9 V (rail)** |
| Current in `R-OUT-PROT` | 7.5 mA | **11.9 mA** |
| Dissipation in `R-OUT-PROT` | **56 mW** | **142 mW** |
| Out-to-out against a 220 Ω output held at −5 V | 10.2 mA, **105 mW** | 13.9 mA, **192 mW** |

`[calc: V²/1 kΩ; out-to-out solved as a two-source divider]`

Two consequences.

**(a) `hardware/bom.csv`'s power-rating analysis is now stale.** The
`R-OUT-PROT` row reads "A mod channel at 10.05 V into a short is 101 mW, against
~125 mW for an 0805 — no margin… 1206 at 250 mW" `[repo: bom.csv]`. As of today
**pitch is the worst case, not a mod channel**: 142 mW shorted, 192 mW
output-to-output. The 1206/250 mW part still holds, but the margin the row
argues from drops from 2.5× to **1.3×**, and the stated worst case is wrong. The
row should be re-derived.

**(b) Every plug insertion is now a full-rail event.** A 3.5 mm plug shorts tip
to sleeve as it slides past the sleeve contact — for tens of milliseconds on
every patch-in. Sequence under the new topology: short → loop opens → amp rails
to ±11.9 V → contact completes → **the jack is presented with ±11.9 V** until
the loop recovers from saturation. Under the old topology the same insertion
produced the *correct* voltage throughout and a clean make.

Magnitude: recovery is slew-limited, so ~1 µs at 20 V/µs plus overload-recovery
delay `[gated on OPA2197 slew rate and overload recovery time]`. Small — but
**the same change deleted the 10 nF that would have rounded that edge** (τ =
10 µs), so it is now as fast as the amplifier can make it, into a VCO's 1 V/oct
input at up to ±11.9 V, i.e. a ~10-octave spike. A click at best; on a VCO with
a fast exponential converter it is a very loud blip. Worth a bench check at E9
alongside the cable-capacitance row.

---

## 6. Power-up, back-powering and ESD: one new path, and it survives the arithmetic

**The clamps-inside-the-loop angle does not fire.** I tried. `D-JACK-CLAMP` is a
BAV99 to ±12 V on the op-amp-output side `[repo: bom.csv D-JACK-CLAMP]`. It
conducts only above +12.7 V or below −12.7 V. An RRIO OPA2197 on ±12 V reaches
~±11.9 V `[repo: bom.csv U-OPA-PITCH]`, so in normal operation, in the
short-circuit case (§5, ±11.9 V) and when absorbing external back-drive, **the
clamp never conducts.** There is no "conducting clamp inside the loop" scenario
that the module's own rails can produce. The only way in is an external source
beyond ±12.7 V, i.e. ESD or a +15 V system, at which point the amp is saturated
anyway and the loop is already open. **Could not break it.** What would have
broken it: clamps to *ground* (which `[repo: bom.csv D-JACK-CLAMP]` notes every
surveyed design uses) — those would conduct inside the normal signal range and
the loop would fight them. This design's rail clamps are the safe choice here.

**Power-up.** With the module's ±12 V absent and a neighbour driving 10 V into
the jack, there is now a *second* back-power path the ADR's analysis does not
cover: jack → R2 (10.2 kΩ) → inverting input → the op-amp's input ESD diode →
the dead +12 V rail. `[calc]` (10 − 0.7)/10.2 k = **0.91 mA** per jack, against
the 7.6 mA/jack through `R-OUT-PROT` and the BAV99 that
`[repo: bom.csv D-JACK-CLAMP]` already counts. So it adds ~12% to a number the
ADR just spent a decision fixing, and it puts ~0.9 mA into a precision op-amp
input pin (typical abs-max ±10 mA `[from memory, gated]`). **Survivable, but
uncounted.** Add it to the row.

**ESD — I expected this to break and it does not.** Today's change creates a new
path from the panel jack straight into the inverting input through 10.2 kΩ, with
**no clamp on that branch** (the BAV99 is on the other side of `R-OUT-PROT`),
and the same change deleted the 10 nF that was the only energy sink at the
connector. Working, HBM (100 pF / 1.5 kΩ), 8 kV at the tip, jack clamped at
~12.7 V through R_p:

```
R_parallel = 1 kΩ ∥ 10.2 kΩ = 911 Ω
I_total    = (8000 − 12.7) / (1500 + 911) = 3.31 A
V_jack     = 12.7 + 3.31 × 911 = 3028 V
I_into_input = (3028 − 12.7)/10200 = 0.296 A,  τ = 100 pF × 2411 Ω = 241 ns
Q_into_input = 800 nC × (1/11.2) = 71 nC
```

`[calc]` Against a 2 kV HBM-rated pin, which absorbs 200 nC at 1.33 A peak: the
input sees **71 nC at 0.30 A — the equivalent of about a 710 V direct strike.**
**Survivable.** Under IEC 61000-4-2 contact discharge (150 pF / 330 Ω, 8 kV) the
same arithmetic gives 0.58 A for ~190 ns and 107 nC, which I cannot bound
without the datasheet — **gated on the OPA2197 input-pin ESD and abs-max
ratings.** The honest statement: a path exists today that did not exist
yesterday, it carries ~9% of a strike, and on the HBM model it computes clear.

---

## 7. Is the claimed benefit real? Yes — and the arithmetic checks

**The load-divider numbers are right.** `[repo: 0006:445–446]`

```
100 kΩ: k = 100/101 = 0.990099 → (k−1)×1200 = −11.88 cents/octave  ✓ (−11.9)
 50 kΩ: k = 50/51  = 0.980392 → (k−1)×1200 = −23.53 cents/octave  ✓ (−23.5)
```

`[calc]` The linear form is the correct one for 1 V/oct (a 1.000 V octave
arriving as 0.9901 V is 0.9901 octaves). Both published figures check out.

**And the deletion is exact.** Exact 3-node DC solve `[calc]`:

| R_load | gain at the jack | deviation |
|---|---|---|
| open | 2.020000 | 0.0000 cents/oct |
| 100 kΩ | 2.020000 | 0.0000 |
| 50 kΩ | 2.020000 | 0.0000 |
| 25 kΩ | 2.020000 | 0.0000 |
| 10 kΩ | 2.020000 | 0.0000 |
| 2 kΩ | 2.020000 | 0.0000 |

Residual from finite open-loop gain: with A_OL ≈ 126 dB `[from memory, gated]`
and β ≈ 0.5, error ≈ 1/(1+T) ≈ **1 ppm ≈ 0.0012 cents/oct**. The benefit is real
and it is two to three orders of magnitude larger than anything it costs at DC.

**What is left over.**

- **Minimum load for full range.** The amp must now drive the jack *through*
  R_p, so V_opamp = V_jack·(1 + R_p/R_load). At V_jack = +7.5 V and ±11.9 V of
  headroom, the break-even is R_load ≥ 1 kΩ × 0.6303/0.3697 = **1.71 kΩ**
  `[calc]`. Below that the top of the range clips. Every Eurorack CV input is
  ≥ 20 kΩ, so this does not bite — but it is a real new bound and it is
  unwritten.
- **Ground is still not in the loop.** The loop servos tip-to-*our*-AGND; the
  VCO measures tip-to-*its*-ground. ADR 0006's own 5.7–7.2 cents (module ground)
  and ~4.8 cents (rack bus ground) `[repo: 0006:553–554]` are untouched by this
  change, and the page does not claim otherwise. Fine, but note that those are
  now **larger than every static term left in the budget** — the change removed
  the 12–24 cent term and the ground terms are what is now on top.
- **`TRIM-GAIN`'s rationale is invalidated by the same change that shrank it.**
  `[repo: pitch-stage.md:130]` — "a series trimmer can only add. **That is the
  right direction for the load divider, which only ever reduces gain.**" Delete
  the divider and nominal gain is dead-on 2.000, so the trimmer's range becomes
  [2.000, +2%] with **zero authority to trim gain *down***. Any negative gain
  error — LT5400 ratio in the wrong direction, a high DAC reference, a VCO whose
  own scale reads high — is now uncorrectable by the screwdriver, where before
  there was a guaranteed 1–2% of headroom in the needed direction. And the same
  decision **shrank** the trimmer from 1 kΩ to 200 Ω `[repo: bom.csv TRIM-GAIN;
  0006:611]`, cutting the remaining range from +5 % to +2 %. Firmware can still scale either way, so this
  is recoverable — but the trimmer now sits at the end of its range by
  construction, and the page still states the obsolete reason for its
  one-sidedness.
- **20 mA of feedback-cap charging current.** On a note-change step the amp must
  charge 1 nF at its slew rate: I = C·dV/dt = 1 nF × 20 V/µs = **20 mA**
  `[calc, gated on the OPA2197 slew rate]`, versus 0.4 mA for the prior art's
  22 pF. That is a material fraction of a precision op-amp's output current on
  every note, and it is also what limits recovery in §5. Worth confirming at E9.

---

## 8. Contradictions the change left in the repo today

Cheap, certain, and all `[repo]`:

| Where | What it still says | Should say |
|---|---|---|
| `pitch-stage.md:135` | **`C-FILT-PITCH` \| 10 nF C0G \| 15.9 kHz, jack side of the 1 kΩ** — a live row in the component table | Deleted (as the prose at :166 says) |
| `pitch-stage.md:130` | `TRIM-GAIN` **1 kΩ**, "0 → +5 % of ratio" | **200 Ω, 0 → +2 %** per `bom.csv` and `0006:611` |
| `pitch-stage.md:207–209` | "Trim with the real patch connected… the 1 kΩ output resistor divides against whatever is plugged in, and that error is what the gain trim's **±5 %** range exists to absorb" | The error no longer exists; and :130 on the same page says the range is not ±5 % |
| `pitch-stage.md:215` | "Cermet… contributing **~5 %** of the ratio" → the 0.4–2.4 cent tempco line | 2 %, so the tempco line needs re-deriving too |
| `pitch-stage.md:230` | Still open: "**Whether `TRIM-GAIN` is 1 kΩ or 500 Ω**" | Both superseded by 200 Ω |
| `0006:629–631` | "**The capacitor goes on the jack side**, so the resistor isolates the op-amp from it… This is the one place in the review where an unspecified *placement* is a functional hazard" | Twenty lines after adopting the opposite for pitch |
| `0006:639–641` | Filter table: **Pitch \| 1 kΩ \| 10 nF C0G \| 15.9 kHz** | Pitch has no jack-side RC |
| `0006:450–500` | "The resistor stays at 1 kΩ, **and calibration absorbs it**"; "store an affine (gain, offset) pair per load preset"; "**Calibrate with the real patch connected**"; "**Use a buffered mult for pitch**"; "Two numbers, not one" — all still written as live policy | Historical; `0006:609` says so but the prose above it was not rewritten |

---

## 9. What I would change, in order

1. **Stop claiming `C-FB-PITCH` is the reconstruction filter.** It is a 6.02 dB
   shelf with a zero one octave above its pole. Rewrite `pitch-stage.md:167–169`
   and `0006:601–602`. This is the actual break and it is free to fix in words.
2. **Put a filter back somewhere legal.** Three options, none of which touch the
   feedback node: (a) an RC *ahead* of the op-amp, on `R-OPAMP-IN` — 1 kΩ is
   already there, add 10 nF to AGND for a 15.9 kHz pole on a node with no loop
   around it, which is what `0006:590–592` says the prior art actually does;
   (b) split `R-OUT-PROT` into 470 Ω + 470 Ω, tap feedback at the midpoint and
   put the cap at the jack behind the second 470 Ω — keeps most of the divider
   correction and restores a jack-side shunt; (c) accept no filter and say so.
   **(a) is the cheap one and it is the one the corpus supports.**
3. **Re-derive the `R-OUT-PROT` power row.** Pitch shorted is 142 mW and
   output-to-output is 192 mW; the row's 101 mW worst case is stale.
4. **Write down the hot-patch rail excursion** and add it to E9 next to the
   cable-capacitance row.
5. **Add the ringing bound to the page:** Q = √(R_eff·C_load / R2·C_fb); safe to
   ~10 nF at the jack; do not passively mult pitch against MOD or BREATH.
6. **Fix `TRIM-GAIN`'s stated rationale** — the direction argument died with the
   load divider — and reconcile the 1 kΩ/200 Ω and ±5 %/+2 % contradictions.
7. **Add the R2 back-power path** (0.91 mA/jack) to the `D-JACK-CLAMP` row.

---

## What would have broken the decision, and did not

Stated plainly, because these were the attacks and they failed:

- **An oscillation.** There is none. Phase margin is 73–77° and flat across
  1650:1 of load capacitance. The chosen 1 nF is *more* conservative than the
  18–22 pF the cited prior art uses.
- **A cable-capacitance case.** 8 m and four destinations gives Q = 0.26 and 0%
  overshoot. Cables cannot reach the ringing regime; only another module's
  jack-side capacitor can.
- **A conducting clamp inside the loop.** The rail clamps cannot conduct within
  the op-amp's own output range. Ground-referenced clamps would have broken it;
  these do not.
- **An ESD kill.** The new 10.2 kΩ path into the inverting input computes to a
  ~710 V-equivalent HBM strike at 8 kV at the tip. Under IEC contact discharge
  it is unresolved and gated on the datasheet.
- **A bad benefit.** The −11.9 and −23.5 cents/octave arithmetic is correct, and
  the deletion is exact to 1 ppm for every load from open to 2 kΩ.

**ADR 0006's original refusal — "that is real stability work, on a board without
one" — was wrong, and today's reversal is right.** The work turned out to be
easy and the result is robust. The mistake is not in the tap. It is in the
sentence that came with it.
