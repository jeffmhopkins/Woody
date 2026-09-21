# A3 — Break "one zero authority per representation", and the `REF` trimmer

**Verdict: BROKEN.**

**State-at-writing note, and it matters.** This repo was edited by at least one
parallel reviewer *while this document was being written* (`git log`:
`7b424c6`, plus untracked `A1-break-jack-feedback.md` and `C1-breath-stage.md`
alongside this file). **Two of the three hard defects below were partially fixed
mid-review — each in one document, leaving the others stale.** Every claim here
was re-verified against the files on disk at the end of the pass, and each
finding is marked **LIVE**, **HALF-FIXED** or **CLOSED**. The fact that two
independent reviewers converged on §1 and §2 from different directions is itself
evidence that they were real.

Not the principle — the principle is sound and I could not break it in the
abstract. What is broken is the arrangement as it stands on disk:

1. **§1 CLOSED mid-review — the trimmer's range did not cover the sensor's own stated
   offset spread.** The page states the pedestal spec as 0.152–0.378 V; nulling
   the top needs **+0.817 V**, and the range was **0 to ~+0.6 V**. A unit at the
   top of its own spec could not be nulled, leaving **1.3–5.5 % of span** standing
   at the jack — inside the same band as the original showstopper the trimmer
   replaced ("4–9 % of full scale"). **Now corrected to 0 → +1.0 V in both
   `breath-receive-stage.md` and `hardware/bom.csv`, mid-review. §1 is CLOSED**
   — the arithmetic is kept below because it is what sets the range, and because
   one clause of it is still wrong (the new row's "+1.0 V covers 0.458 V" uses
   the raw gain and omits the bias-pair divider; it is **0.463 V**).
2. **§2 HALF-FIXED, with a live remainder — the breath jack still depends on a
   DAC register.** The trimmer was specified "from `VREFOUT`", the DAC8568's
   internal reference, which ADR 0006 states twice is **disabled until firmware
   writes an enable**. ADR 0003 and the BOM have since moved it to the LM317
   5.21 V rail. **The schematic still draws "from VREFOUT"** — on a page that
   declares "**where it disagrees with ADR 0003's prose, this page wins**". And
   the remainder is untouched: the same page nominates *"the buffered `VREFOUT`
   created for pitch"* as the downstream **`OFFSET`** reference, which puts the
   breath jack's resting position back on the same disabled-at-boot register by
   a different route — with a larger step (§2b).
3. **§3 LIVE — the presence comparator is broken for the second time by a change
   to this node, its diagnosis in the repo is wrong, and the fix the BOM has
   already adopted is broken too** — by the bias current of the comparator the
   BOM still specifies, and by a CMRR cost this design's own framework forbids.
   As written it reads "absent" always, which disables the level shifter's `OE`
   and takes every CV output with it.
4. **§4 LIVE — a framing failure that is load-bearing.** "Each authority can
   measure what it corrects" is true for firmware and **false for the trimmer**.
   Firmware can measure roughly 90 % of the analog path's zero error — it shares
   the sensor — and it is the only thing in the design that measures it more than
   once. The trimmer measures nothing; a technician's meter measured once, cold,
   at a temperature the instrument spends most of its life away from.

---

## Evidence key and method

Every claim is marked. `[repo]` names the file. `[calc]` shows the arithmetic in
full. `[datasheet]` means a figure I could verify. `[from memory]` means I could
not, and the conclusion is gated on it explicitly.

The proxy blocks nxp.com and all distributors, so no MPXV4006DP figure could be
checked. **§0 names the single parameter this whole review forks on** and gates
both branches.

Files read in full or in relevant part: `hardware/module/breath-receive-stage.md`,
`docs/decisions/0003-breath-sensing-path.md`,
`docs/decisions/0006-cv-channel-allocation.md`, `firmware/README.md`,
`hardware/module/digital-and-supervision.md`, `hardware/module/pitch-stage.md`,
`hardware/bom.csv`, `docs/decisions/0007-imu-selection.md`,
`docs/review/2026-09-20-cold-review/verification/V4-fix-conflicts.md`.

---

## §0 — The parameter the argument forks on, and the gate

**The parameter: what the 0.152–0.378 V figure in `breath-receive-stage.md`
actually is.** The page says the MPXV4006DP "sits at +0.2 V at zero pressure by
design (spec range 0.152–0.378 V)" `[repo: hardware/module/breath-receive-stage.md]`.
That spread is **−48 mV / +178 mV around 0.200 V** — grossly asymmetric, which
is not the shape of a unit-to-unit offset distribution. It is the shape of a
**combined error band** (offset + sensitivity + temperature + linearity) quoted
over a temperature range.

`[from memory]` NXP's integrated MPX/MPXV series typically specifies a combined
**"Temperature Error"** or **"Accuracy"** band as a percentage of full-scale
span over 0–85 °C, and does **not** break out an offset temperature coefficient
in mV/K. ADR 0003's own honesty marker agrees: "**That figure is unverified**:
it rests on an offset tempco of ~0.5 mV/K that the sensor family's datasheet
apparently does not break out" `[repo: hardware/module/breath-receive-stage.md]`.

**The fork, and both branches damage the arrangement:**

| If 0.152–0.378 V is… | Then… |
|---|---|
| **Unit-to-unit offset at 25 °C** | The trimmer's 0–0.6 V range does not cover it (§1). A max-offset unit cannot be commissioned. |
| **A combined band including temperature** | A 25 °C unit sits much closer to 0.200 V and §1 softens — but the *thermal* share is then up to **+178 mV at the sensor**, against the **10 mV** the design assumes. Every "a quarter turn you will never touch" claim in ADR 0003 and ADR 0006 is wrong by **10–17×**. |

`[calc]` Temperature-inclusive branch, worst case: 178 mV at the sensor ×
effective gain 2.1611 = **385 mV at the in-amp output**; through the downstream
0.6–2.5× = **0.23–0.96 V at the jack**, i.e. **2.3–9.7 % of the 9.94 V span**,
against the **0.23 %** ADR 0003 claims. The whole "fixed commissioning trim is
sufficient because drift is only 23 mV" argument dies in this branch.

**The gate:** the arrangement's thermal defence is sound **only if** the
MPXV4006DP's offset drift over a 20 K rise is ≤ ~10 mV *and* the 0.152–0.378 V
figure is a 25 °C unit-to-unit spread. **Both must hold.** Nobody in this
project has established either. Named parameters to check the moment nxp.com is
reachable, in priority order:

1. **Offset stability / "Temperature Error" band, in %VFSS over the operating
   range** — decides the fork above.
2. **TCVoff (offset temperature coefficient, mV/K)** if it is broken out at all
   — the 0.5 mV/K figure ADR 0003 leans on.
3. **Zero-pressure offset, min/typ/max at 25 °C** — decides §1 outright.
4. **Turn-on / warm-up drift and self-heating settling time** — decides §7.
5. **Long-term offset stability (per year)** — decides whether "set once at
   build" survives the instrument's service life at all.

Until (1) and (3) are known, the trimmer's range is unspecifiable and the
review below should be read as conditional in that one respect. **Nothing else
in this document depends on an unreachable datasheet.**

---

## §1 — CLOSED during this review: the trimmer could not null the sensor it is for

**Status: corrected in `hardware/module/breath-receive-stage.md` and in
`hardware/bom.csv` while this document was being written, by a parallel
reviewer, to the same range this arithmetic gives.** The working is kept in full
because it is what sets the range, because one clause of the new BOM row is
still wrong, and because two of the three defects in this section were **not**
fixed.

`[repo]` The page gives every term needed:

- pedestal at the sensor: 0.200 V nominal, **spec 0.152–0.378 V**
- bias-pair loss: 2 × 1 MΩ against 2 × 11 kΩ → **×0.98912**
- in-amp raw gain: `G = 1 + 50k/42.2k` = **2.1848**
- `Vout = −G·(V_BREATH − V_AGND) + V_REF`

`[calc]` Required `V_REF` to null, per unit:

```
V_REF = G × V_ped × 0.98912
  V_ped = 0.152 V → 2.1848 × 0.152 × 0.98912 = 0.3285 V
  V_ped = 0.200 V → 2.1848 × 0.200 × 0.98912 = 0.4322 V
  V_ped = 0.378 V → 2.1848 × 0.378 × 0.98912 = 0.8169 V
```

**Required range: 0.33 → 0.82 V. Range as specified this morning: 0 → ~+0.6 V.**
`[calc]` A unit at 0.378 V was left with 0.8169 − 0.600 = **0.217 V standing at
the in-amp output**, which the downstream 0.6–2.5× turns into **0.130–0.542 V at
the jack — 1.3 % to 5.5 % of the 9.94 V span**, permanently, into a VCA. The
showstopper this trimmer replaced was described as leaving "4–9 % of full scale
standing at the jack at rest" `[repo]`. **The replacement reproduced the bottom
two-thirds of the defect it was introduced to remove.**

Both `breath-receive-stage.md` and `hardware/bom.csv` now read **0 → +1.0 V**
with the band given as 0.332–0.826 V `[repo, verified on disk]` — the same
conclusion, reached independently. **Closed.**

`[calc]` One clause of the new BOM row is still wrong: *"+1.0V covers 0.458V
with margin"*. The pedestal a 1.0 V ceiling can null is
1.0 / (2.1848 × 0.98912) = **0.4627 V**, not 0.458 V — the 0.458 figure omits
the bias-pair divider, the same slip as the 0.437-vs-0.432 one below. The
conclusion (comfortable margin over 0.378 V) is unaffected.

**Second defect in the same row, still live, and it is an honesty marker
inverted.** The page justifies deleting the polarity finding with: *"polarity is
a non-issue because a trimmer goes both ways"* `[repo]`. **The specified trimmer
does not go both ways.** Its range is 0 → +1.0 V — strictly one-sided, exactly
like the unipolar DAC channel whose one-sidedness was the showstopper. It is in
the *correct* one-sided direction only because the inputs were swapped, and the
page itself records that the swap's original justification was deleted. **The
swap is now load-bearing for the trimmer's polarity, and the page does not say
so.** A future reader who un-swaps the inputs on the grounds that the DAC reason
is gone gets a trimmer that cannot null anything.

**Third, still live: the +0.437 V figure in the drawing is inconsistent with the
drawing's own gain derivation.** `[calc]` 2.1848 × 0.200 = 0.43696 ≈ 0.437 V —
the *raw* gain against the *undivided* pedestal. The same page derives an
**effective** gain of 2.1611 two sections earlier and uses it for the span. Using
it here gives **0.4322 V**. The 4.8 mV difference is small (2.9–12 mV at the
jack) but it is 22 % of the entire thermal drift budget the design calls
negligible, and it means the number in the schematic is not the number the
trimmer will be set to. The corrected range band (0.332–0.826 V) carries the same
error: `[calc]` with the effective gain it is 0.328–0.817 V.

**Remaining fix:** update `hardware/bom.csv` row `TRIM-BREATH-ZERO` to
0 → +1.0 V; state the nominal as **0.432 V** in both places; record that the
input swap is now a precondition for the trimmer's polarity.

## §2 — HALF-FIXED, with a live remainder: the breath jack still depends on a DAC register

### 2a — The `REF` trimmer's reference: fixed in two documents, stale in the governing one

`[repo: hardware/bom.csv, TRIM-BREATH-ZERO — as it read this morning]` "Range
0 to ~+0.6V **from VREFOUT**".

`[repo: docs/decisions/0006-cv-channel-allocation.md]` "**the internal reference
is disabled by default** and needs an explicit enable write at boot … the outputs
sit at 0 V from rack power-on until firmware enables the reference", and again
under firmware defaults: "**Enable the DAC's internal reference explicitly at
boot.** It is disabled by default. Nothing works until this write happens, and
the failure looks like dead hardware."

`[calc]` With `V_REF = 0` and a live instrument at rest: in-amp output
= −2.1611 × 0.200 = **−0.432 V**; through the inverting downstream 0.6–2.5× the
jack sits at **+0.26 V to +1.08 V** — **2.6 % to 10.9 % of span, into a VCA** —
for the whole boot window, and **indefinitely** if firmware fails to boot, is
rolled back by `CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE`, or sits in download mode
on the recovery header.

**Status: corrected during this review** in `docs/decisions/0003-breath-sensing-path.md`
("**That trimmer is referenced to the LM317's 5.21 V rail, deliberately, and not
to the DAC's `VREFOUT`**") and in `hardware/bom.csv` ("FROM THE LM317'S 5.21V,
NOT VREFOUT"). Both verified on disk. **That is the right fix** — it is the one
this review would have recommended, and the LM317 rail is up whenever +12 V is.

**But the schematic still says `from VREFOUT`** `[repo:
hardware/module/breath-receive-stage.md:54, verified on disk]` — and that page
opens with: *"Where it disagrees with ADR 0003's prose, **this page wins** and
the ADR gets corrected."* **By the project's own precedence rule, the stale
drawing beats the corrected ADR and the corrected BOM.** This is not pedantry:
the whole page exists because "two expert reviewers built two *different*
schematics from the same ADR prose", and the remedy adopted was to make the
drawing authoritative. A drawing that is authoritative and wrong is worse than
prose that is wrong.

**Two consequences worth recording against the new reference, neither fatal:**

- `[calc]` The LM317 rail's own value is **deliberately unspecified and
  bench-selected per unit**: `[repo: hardware/bom.csv, R-REG-SET]` "R2 is
  **SELECTED ON THE BENCH at E7** (this is a population of one), and the value
  here is the starting point", because E7 picks it from where the DAC's top codes
  compress. So **the breath zero's reference is set at E7 and the breath zero is
  trimmed at commissioning — and nothing states the order.** If the rail is moved
  by 100 mV after the trim, `V_REF` moves by 100 mV × (0.432/5.21) = **8.3 mV**,
  i.e. 5–21 mV at the jack. Small, but it is a free error: **add "after
  `R-REG-SET` is selected" to the commissioning procedure.**
- `[calc]` Load regulation is a non-issue and I could not make it one. The DAC's
  AVDD current swing is a couple of mA against the LM317's rating; at ~0.1 %
  load regulation over a full-scale load change the rail moves well under 1 mV
  for that swing, → under 0.1 mV at `REF`. **Concede.**

### 2b — The live remainder: the `OFFSET` knob's reference is still `VREFOUT`

`[repo: hardware/module/breath-receive-stage.md, §Still open, verified on disk]`
— *"its offset reference (**the buffered `VREFOUT` created for pitch** is the
obvious node)"*.

**Moving the trimmer off `VREFOUT` while leaving the `OFFSET` injection on it
does not remove the DAC dependency. It moves it to the larger term.** The
trimmer contributes 0.432 V at the in-amp. The `OFFSET` knob positions the jack's
**floor across the usable span** — ADR 0006 defaults breath to 0–8 V with bipolar
opt-in, so the offset term is volts, not hundreds of millivolts.

`[calc]` If the offset reference is zero until firmware enables `VREFOUT`, then
at every rack power-on, for the whole ESP32-S3 boot window, **the breath jack
rests at the gain path's output (≈0 V) instead of wherever the player parked the
floor** — and steps to the parked position when the enable write lands. For a
player who has set the floor at +2 V, that is a **2 V step on the breath CV at
every boot**; for a bipolar patch parked at −5 V, a **5 V step**. Into a VCA, or
into whatever the breath CV is patched to. That is an order of magnitude larger
than the 0.26–1.08 V that 2a was about.

And it reopens the watchdog question that `digital-and-supervision.md` and
`firmware/README.md` both declare settled. `[from memory: on the DAC8568 I
believe the hardware `CLR` pin loads the clear-code value into the DAC registers
and does not touch the reference-setup register, while a **software** reset does
clear it — unverified, ti.com is blocked]`. **Gate:** if `CLR` or a software
reset clears the reference-setup register, every watchdog event steps the breath
jack by the parked offset. If it does not, the defect is confined to power-on
and firmware-not-running — which still falsifies all three of these:

| Statement | File | Verified on disk |
|---|---|---|
| "now that `REF` carries a trimmer rather than a DAC channel, `CLR` touches the breath stage in no way at all" | `hardware/module/digital-and-supervision.md` | still present |
| "**Breath is outside all of this.** … no DAC register touches the breath jack at all" | `firmware/README.md` | still present |
| "**Breath \| 0 V \|** The receiver's differential pulldown holds it there" (power-on table) | `docs/decisions/0006-cv-channel-allocation.md:158` | still present |

The third row is stale twice over: the differential pulldown was **deleted**
(replaced by the R4/R5 common-mode bias return `[repo: breath-receive-stage.md]`),
and the value is wrong.

`firmware/README.md` itself names the class: *"The same shape of bug is latent in
every other register the DAC holds that firmware writes once: **the
internal-reference enable**, and the clear-code register itself."* The breath
jack's floor is still hung on precisely that register.

**And this is the failure the cold review already resolved once.**
`[repo: docs/review/2026-09-20-cold-review/verification/V4-fix-conflicts.md, C1]`
found that hanging power-on-critical DC on `VREFOUT` parks a channel wrong
because the reference is off at reset, and recommended a series REF5025.

**Why `VREFOUT` is right for pitch and wrong for breath — the asymmetry nobody
states.** `[repo: hardware/module/pitch-stage.md]`: for pitch,
`Vout = 2·Vdac(1+δ) − 2.500(1+δ) = (1+δ)(2·Vdac − 2.500)` — a reference drift
becomes a **pure gain error** because both terms ride the same reference. On the
breath channel the signal is ratiometric to the **REF5050** and the offset term
would be ratiometric to **`VREFOUT`**: two different references, no cancellation,
so `VREFOUT` error appears as **pure offset**. Whoever nominated the node reused
it without reusing the reasoning.

`[calc]` In fairness the *drift* is negligible either way: `VREFOUT` at
5 ppm/°C over 20 K = 2.5 × 5e-6 × 20 = 250 µV; scaled by 0.432/2.5 that is
**43 µV** at `REF`. **The problem is the reference's absence, not its drift.**

**Fix:** (i) correct `breath-receive-stage.md:54` to the LM317 rail; (ii) rule
out `VREFOUT` for the downstream `OFFSET` reference in the same sentence that
currently nominates it, and specify the LM317 rail or a series reference there
too. Only then is `firmware/README.md`'s claim true. It is not true today.

## §3 — BREAK: the presence comparator, broken a second time, and the proposed fix is broken too

`[repo: hardware/module/digital-and-supervision.md]` already admits the first
half: *"that is a problem this drawing created … Now that `TRIM-BREATH-ZERO`
nulls the pedestal, both states sit at 0 V and the detect stops working."*

**The stated diagnosis is wrong in detail, and that matters.** `[calc]` With the
trimmer fitted and the tap at the in-amp output:

| State | In-amp output |
|---|---|
| Cable unplugged (R4/R5 hold both inputs at AGND, differential 0) | `V_REF` = **+0.432 V** |
| Instrument alive, at rest | **≈ 0 V** |
| Instrument alive, blowing | **down to −9.6 V** |

The two states are **not both at 0 V**. They are still separated by the full
432 mV — the split is still generated by the instrument, as it must be — but the
**sense is inverted**: the old arrangement had alive *below* unplugged by
−437 mV; the new one has alive *below* unplugged by −432 mV around a pedestal
that moved up by `V_REF`. The comparator does not need a new tap point. **It
needs its threshold moved from −200 mV to +216 mV.** The repo's own diagnosis
sent it to a more expensive fix than the defect required.

**And the fix the BOM has already adopted is broken by the comparator the BOM
still specifies.** `[repo: hardware/bom.csv, U-PRESENCE / R-PRESENCE]`: sense the
module end of `BREATH` against `AGND` — the in-amp's `IN−` node — with an
**LM311**, threshold ~+100 mV.

`[calc]` That node is held at 0 V when unplugged **only by R4 = 1 MΩ**. The
LM311 is a bipolar-input part; `[from memory: LM311 input bias current is ~100 nA
typical, 250 nA maximum at 25 °C, and it is not a low-Ib part — this is the
number to check if national/ti is ever reachable]`:

```
100 nA × 1 MΩ = 100 mV
250 nA × 1 MΩ = 250 mV
```

against an alive/absent discriminating signal of **198 mV**
`[calc: 0.200 × 0.98912]`. **The comparator's own input current is 50 %–126 % of
the signal it is discriminating.** At the max figure it pulls the unplugged node
clean through a +100 mV threshold and the detector reads "**instrument
present**" with nothing plugged in — **the exact failure that caused the detect
to be moved off umbilical +12 V in the first place** `[repo:
digital-and-supervision.md: "It failed in exactly the state it existed for"]`.
Third time on the same detector.

**Gate:** this break holds if LM311 Ib ≥ ~50 nA. If a CMOS comparator (pA bias)
is substituted, it disappears — and the tap-ahead-of-trim node is always
positive, so the LM311's separate-emitter / see-below-V− property, the entire
reason it was chosen, is **no longer needed**. Two individually correct
decisions — "move the tap to the high-impedance node" and "use an LM311 because
it must see below V−" — compose into a detector that fails open. Neither
document notices, because they were written at different times.

**Second break of the same fix: it costs the CMRR budget the page spends two
sections defending.** The tap is a single-ended load on **one input leg**, which
is the page's own named cardinal sin ("a single-ended capacitor on one input
leg is a common-mode-to-differential converter").

`[calc]` Each leg is a divider `α = R_bias/(R_bias + R_series)` with
R_series = 10 kΩ. Balanced: α = 1M/1.01M = 0.990099. For the pair mismatch to
stay inside a 60 dB CMRR budget, Δα ≤ 1e−3, so the loaded leg must keep
α ≥ 0.989099, i.e. R_eff ≥ 10k × 0.989099/0.010901 = **907 kΩ**. With R4 = 1 MΩ
already there:

```
1/907k = 1/1M + 1/R_c  →  1/R_c = 1.1025e-6 − 1.0e-6 = 1.025e-7
R_c = 9.75 MΩ
```

**The comparator tap must present ≥ ~10 MΩ to that leg** or it eats the 60 dB
budget. A 100 kΩ threshold network tapped onto the node presents 100 kΩ.
`[calc]` At R_c = 100 kΩ: R_eff = 90.9 kΩ, α = 0.9009, Δα = 0.0892, CMRR limit
= **21 dB** — worse than the 19 dB single-leg-shunt mistake the design already
deleted once, and far worse than the 15 dB single-ended-cap mistake it warns
about.

**Fix, and it is simpler than what the repo proposes:** leave the comparator on
the in-amp **output** (a low-impedance node — no bias current problem, no CMRR
cost, no new net) and derive its threshold from the **buffered trim output**:

```
threshold = V_REF/2 − 50 mV      (a 2:1 divider off the trim buffer, plus a small fixed offset)
```

`[calc]` It self-centres on whatever the trim was set to — alive ≈ 0 V, unplugged
= `V_REF`, threshold always midway — so it survives §1's unit-to-unit spread
(`V_REF` = 0.33 → 0.82 V) with no re-tuning, which a fixed +100 mV threshold does
not. Blowing drives the output negative, still below threshold, still "alive". A
dead sensor, a dead REF5050, a dead buffer or a shorted conductor all collapse
the differential to zero → output = `V_REF` → "absent", correctly. One divider
and one resistor, on a low-impedance node. The threshold is positive in normal
operation, so the negative reference is still not needed.

`[calc]` The −50 mV term is not cosmetic: it is what makes the detector degrade
correctly if `V_REF` is ever lost (§2a's failure mode, now fixed for `REF` but
still live for the `OFFSET` reference). With `V_REF` = 0: threshold = −50 mV,
alive = −0.432 V (below → "alive", correct), unplugged = 0 V (above → "absent",
correct). Without it the two states meet at zero and the detector is ambiguous.

**Third: the specified `R-PRESENCE` values do not produce the threshold the row
asks for, on any rail in the module.** `[repo]` "100k / 10k / 1M", threshold
"~+100 mV":

```
[calc] from 5.21 V:  5.21 × 10/110 = 0.4736 V
       from +12 V:   12   × 10/110 = 1.0909 V
       from 2.5 V:   2.5  × 10/110 = 0.2273 V
```

Every candidate is **above the 198 mV alive level**, so the comparator reads
"absent" with a perfectly healthy instrument. To get 100 mV from 5.21 V needs
100k/1.96k. The three values are a leftover from the −200 mV arrangement and
were never recomputed; the row's "Final values at E10" note does not cover a
value that is wrong by 4.7×.

**Consequence if it ships as written:** `U-PRESENCE` is open-collector into
`R-OE-PU` driving four `74AHCT125` `OE` pins, active low
`[repo: hardware/bom.csv, R-OE-PU / U-LVL-MOD]`. Permanently "absent" ⇒ `OE`
high ⇒ **buffer disabled ⇒ no SPI reaches the DAC ⇒ every CV output dead**,
with the panel LED dark. Fail-safe in direction, catastrophic in effect, and it
presents at E7 as a dead board.

`[calc]` Hysteresis, for completeness: 1 MΩ from output to the threshold node,
Thevenin 100k‖10k = 9.091 kΩ, swing ≈ 5.01 V →
5.01 × 9.091k/(1M + 9.091k) = **45 mV**. Appropriate against a 198 mV split;
keep it.

**Also: the two documents now disagree about whether this is done.**
`digital-and-supervision.md` lists the tap point under "**Still open** … It needs
the one-line change described and a corrected `R-PRESENCE` row", and states "the
BOM's `R-PRESENCE` note still describes the old −200 mV arrangement and is
wrong" — but `hardware/bom.csv` has **already been rewritten** to the new tap
(both `U-PRESENCE` and `R-PRESENCE` describe sensing ahead of the trim). The
schematic page thinks the BOM is stale; the BOM is ahead of it. One of the two
must be corrected or the next reader applies the change twice.

---

## §4 — "Calibration" vs "performance" is a label. Here is the sequence where they fight

**The rule, as the project states it elsewhere:** "Two offset authorities in
series would be a split-brain failure … neither channel group has both"
`[repo: docs/decisions/0006-cv-channel-allocation.md]`.

**What breath now has:** `TRIM-BREATH-ZERO` at `REF` and the panel `OFFSET`
knob, both adjustable, both on the analog path, in series. The defence is a job
label in a three-row table `[repo: breath-receive-stage.md]`. Test the label:

**The table's own analogy does not hold.** It claims "the same split as pitch's":

| | Calibration | Performance |
|---|---|---|
| Pitch | `TRIM-OFFSET`, set once | firmware's per-load affine |
| Breath | `TRIM-BREATH-ZERO`, set once | the panel `OFFSET` knob |

These are not the same split. In the pitch row, the performance authority is
**firmware acting on the analog output through the DAC** — i.e. firmware
*correcting an analog signal it cannot directly measure*, verified open-loop by a
human against a frequency counter at E9 `[repo: ADR 0006]`. That is precisely the
thing the breath row deletes a DAC channel to forbid. The table puts two
structurally opposite arrangements in the same column and calls them a pattern.

**The real distinction is topological, not vocational, and the design has the
right idea under the wrong name.** What makes the two elements non-redundant is
that one sits **ahead of** the gain pot and the other **after** it. Pre-gain null
and post-gain positioning are genuinely different jobs. "Calibration vs
performance" is a statement about *who turns the knob*, which is enforced by
nothing: the trimmer is inside the module (rack removal), the `OFFSET` knob is on
the panel. **The player will always reach for the knob.**

### The sequence

1. **Commission.** `TRIM-BREATH-ZERO` set so the in-amp reads 0 V, cold, at the
   bench. Residual ε ≈ 0.
2. **Patch.** `GAIN` set to α₁ = 0.6× for a patch that wants a gentle span;
   `OFFSET` set so the jack rests at 0 V. Correct.
3. **Play for twenty minutes.** Body rises 10–20 K. `[calc]` Sensor offset drift
   at the design's assumed 0.5 mV/K × 20 K = 10 mV → × 2.1611 = **ε = 21.6 mV at
   the in-amp**. Jack rests at 21.6 mV × 0.6 = 13 mV. The player notices the VCA
   is not quite shut — or does not, and the next step happens anyway.
4. **The player nudges `OFFSET`** to re-zero the jack by ear. **This is the
   moment the rule breaks.** `OFFSET` is now carrying a correction that belongs
   to the pre-gain null. The analog path has two zero authorities in series and
   nothing in the design detects, prevents or records it.
5. **Next session, new patch: `GAIN` to α₂ = 2.5×.** The pre-gain residual ε is
   scaled by the new gain; `OFFSET`'s compensation, being post-gain, is not.
   `[calc]` Jack rest shifts by ε × (α₂ − α₁) = 21.6 mV × 1.9 = **41 mV**. The
   player turns `OFFSET` again.
6. **Repeat.** This is the Yamaha WX5 interaction — *"Wind Zero may change
   slightly when Wind Gain is adjusted, so you may have to repeat"* `[repo]` —
   the exact behaviour the trimmer was added to abolish, back, at 1/20 the
   magnitude.

`[calc]` The reduction factor: untrimmed, the pedestal at the in-amp is 0.432 V
and sweeping gain moves the jack by 0.432 × 1.9 = **821 mV**. Trimmed to a 21.6 mV
residual it moves **41 mV**. **Ratio 20×.**

**So the honest statement is: the trimmer reduces the knob interaction by the
ratio of residual to pedestal. It does not eliminate it.** The page claims
elimination twice — "which is what makes the panel knobs independent"
`[repo: breath-receive-stage.md, component table and BOM]` and "step 2 no longer
disturbs this" `[repo: commissioning step 3]`. Both are overclaims. The correct
sentence is *"reduces the interaction by ~20× at the commissioned temperature,
proportionally less as the residual grows"* — and under §0's temperature-inclusive
branch the residual is 385 mV, the reduction factor is **1.1×**, and the trimmer
buys essentially nothing.

**Verdict on this sub-question: the distinction is real but misnamed, and the
name is what fails.** Rename the rows *"pre-gain null (fixed)"* and *"post-gain
position (adjustable)"*, and state the rule as **"one *adjustable* zero authority
per representation; fixed nulls are not authorities"** — which is exactly the
amendment V4's C1 already demanded for pitch ("**Record explicitly that a fixed
reference plus a trimmer is not the two offset authorities in series that ADR 0006
forbids — otherwise someone deletes one of them later**"). Under that amended
rule the arrangement is legal **only if the trimmer is genuinely fixed**, which
§1 (range), §2 (reference off at boot) and §9 (commissioned at the wrong
temperature) each independently prevent today.

---

## §5 — Does the trimmer decouple the knobs? The algebra through the undrawn block

The downstream stage is drawn as a block, and the page's own "Still open"
concedes: *"**The downstream gain/offset stage** is drawn as a block. Its own
values, its offset reference … and whether the gain pot's wiper needs a buffer
are E10 work."* `[repo]`

**The decoupling claim is therefore asserted about a circuit that has not been
drawn.** Work it for the two plausible realisations of "inverting gain + offset,
`POT-GAIN` then `POT-OFFSET`, one op-amp half":

**(a) Gain pot as an input attenuator into a summing node** (the form the page's
prose implies — "two pots into one virtual ground"):

```
V_jack = −(Rf/Rg)·α·V_inamp − (Rf/Ro)·V_wiper_offset
∂V_jack(rest)/∂α = −(Rf/Rg)·ε
```

`[calc]` Zero **iff ε = 0**. The trimmer decouples the knobs at exactly one
operating point, at one temperature, on one sensor unit. Everywhere else the
coupling is proportional to ε, as §4 step 5 shows.

Note also this form needs fixed gain ≥ 2.5 with the pot attenuating 0.24→1.0 to
reach the 0.6–2.5× the commissioning section asks for, and the wiper is loaded by
Rg so α is not the mechanical fraction — which is the "does the wiper need a
buffer" question the page leaves open. If the answer is yes, that is a **twelfth**
op-amp half and the BOM's "one spare" `[repo: U-OPA-PITCH]` is gone.

**(b) Gain pot as a rheostat in the feedback path** (the cheaper single-op-amp
way to get a >4:1 range):

```
V_jack = −(Rf(α)/Rg)·V_inamp − (Rf(α)/Ro)·V_offset
```

**Both terms scale with the gain setting.** The offset knob's contribution now
moves with `GAIN` **regardless of ε**, and the trimmer decouples nothing at all.
This realisation is not excluded by anything drawn or written.

**Conclusion:** the claim *"nulling the pedestal ahead of the gain pot is what
makes the panel knobs independent"* is **(a) conditional on ε = 0, which is never
true, and (b) conditional on a topology choice that has not been made.** It must
be demoted to a *requirement on E10* — "the downstream stage shall place `GAIN`
ahead of the summing resistor and inject `OFFSET` as an independent summing
current; a feedback-rheostat gain control is forbidden" — rather than stated as
an accomplished property.

**One more coupling the block hides.** The page nominates *"the buffered
`VREFOUT` created for pitch"* as the offset reference `[repo]`. But `[repo:
hardware/bom.csv, TRIM-OFFSET]` that follower's input is **after** the pitch
offset trimmer — "`TRIM-OFFSET`, module, Pitch offset trimmer, **AHEAD of the
VREFOUT follower**". So the "buffered `VREFOUT`" node is a *trimmed* 2.500 V that
a technician adjusts to calibrate **pitch**. `[calc]` `TRIM-OFFSET`'s range is
"~50 mV on a 2.5 V reference" = 2 %; hung on breath's `OFFSET` injection that is
2 % of the offset term, and **a pitch recalibration moves the breath jack's rest
point**. Two "independent" calibration authorities, cross-linked through a shared
node, on two channels that share nothing else. Take breath's offset reference
from raw buffered `VREFOUT` or from its own divider — not from the pitch-trimmed
node.

`[repo]` And 0006's own rule for the pitch trimmer — *"Hanging a **trimmer**
directly on `VREFOUT` would make the reference move as the trimmer is turned,
coupling the offset adjustment into the DAC's full-scale span. A follower breaks
that."* — is not restated for `TRIM-BREATH-ZERO`, which is a 10 kΩ pot plus
divider **on `VREFOUT`**, buffered only at the wiper. It is safe **only** if
wired as a potentiometer with a constant end-to-end load. **Nowhere does any page
say so.** Wired as a rheostat, turning the breath zero trimmer detunes pitch.
One sentence, missing.

---

## §6 — The two representations diverge. The interesting number is not 23 mV

The design's stated worst case is 23 mV in 10 V — 0.23 %, "a quarter turn of a
knob you will probably never touch" `[repo: ADR 0003 and ADR 0006]`. **In the
thermal case that is approximately right and I could not break it.**

`[calc]` 0.5 mV/K × 20 K = 10 mV at the sensor; × 2.1611 = 21.6 mV at the in-amp;
× (0.6…2.5) = **13–54 mV at the jack**, 0.13–0.54 % of span. On a linear VCA,
inaudible. **Concede.**

**The divergence that breaks the arrangement is not thermal and is not bounded.**

`[repo: ADR 0006]` The firmware zero is *"decayed toward the current reading"*.
Each decay step moves the baseline, and the sub-threshold test is taken against
the *new* baseline — so a drift slower than the decay is absorbed **without
limit**, one step at a time. Nothing in the rule caps the total. The analog path
absorbs **none** of it. So the divergence between the two representations is
bounded only by the sensor's range.

The design names the three mechanisms itself `[repo: ADR 0006]`: *"a partially
blocked PTFE restrictor, a cavity that has started sealing, or a shifted sensor
offset"*. And `[repo: ADR 0003]` quantifies the second: a sealed cavity warming
15 K gains **5.2 kPa**, "eighty-six percent of range".

`[calc]` Take just **2 %** of that — a cavity that has started to seal, or a
restrictor 2 % occluded — i.e. 104 Pa:

```
104 Pa × 0.766 V/kPa = 79.7 mV at the sensor
× 2.1611                = 172 mV at the in-amp
× 0.6 … 2.5             = 0.10 – 0.43 V at the jack
```

At 10 % (520 Pa): **0.52 – 2.15 V at the jack**, standing, with

- the **display reading zero** (firmware has absorbed it),
- **USB MIDI CC reading zero**,
- **note gating silent** (the threshold moved with the baseline),
- and the **VCA open**.

**The consequences, named:**

- **Note gating fires at a jack level the player did not intend.** The gate is
  computed on the zeroed digital copy; the jack is not zeroed. At the instant the
  gate opens, the jack is already at the absorbed offset plus the threshold. The
  attack transient the instrument produces is therefore not the attack the player
  produced, and the error grows across a session.
- **MIDI and CV disagree by an unbounded amount.** `firmware/README.md` calls
  USB MIDI "a bring-up tool, not a feature", which limits the blast radius for a
  player — but E5 validates *"keys, fingering and breath response … in a DAW
  before any analog hardware exists"* `[repo]`, so the divergence is invisible in
  precisely the milestone that is supposed to establish breath response is right.
- **The logged correction does not mean what the player sees.** ADR 0006 claims
  the log is *"now an **honest** diagnostic … Applied only to the copy firmware
  actually measures, it can only mean the first [a real fault]"* `[repo]`. **That
  is backwards.** The correction now conflates (i) ordinary thermal drift, which
  is the *reason the mechanism exists* and happens every session, with (ii) the
  three faults. A number that walks every single session for benign reasons is not
  a fault indicator. Worse, firmware has **no return path over the umbilical**
  `[repo: ADR 0006: "no return path needed over the umbilical"]`, so it does not
  know `GAIN` or `OFFSET` and **cannot express the correction in the units the
  player sees at the jack**. The only action the number suggests — "turn the
  `OFFSET` knob" — is the action that creates §4's second zero authority.
- **The player's last cross-check was explicitly removed.** `[repo:
  breath-receive-stage.md]`: *"**E10 scopes the jack**, not the display. The two
  representations are calibrated separately on purpose, so **a flat bar on the
  screen is no longer evidence about the output.**"* That sentence is correct and
  it is the problem: the design deleted the display as evidence about the jack and
  put **nothing** in its place. After commissioning, **nothing in this instrument
  ever measures the breath jack again.**

**The reframing that actually breaks the arrangement's central claim:** the rule
is *"each authority can measure what it corrects"*. Firmware and the analog path
**share the sensor, the buffer and R1** — the divider tap is on the buffer's own
output `[repo: breath-receive-stage.md schematic]`. So firmware's ADC copy
contains the **dominant, drifting** term of the analog path's zero error.

`[calc]` The digital copy's resolution, to show it can see it: MCP3202, 12-bit,
VDD-referenced at 3.3 V `[repo: hardware/bom.csv, U-ADC]`, behind a 0.6× divider
`[repo: R-ADCDIV, 10k/15k]`:

```
1 LSB = 3.3 V / 4096      = 805.7 µV at the ADC
      / 0.6               = 1.343 mV at the sensor
      / 0.766 V/kPa       = 1.753 Pa of breath
Thermal drift 10 mV at the sensor = 7.45 LSB — six times its own noise floor.
```

**Firmware measures, at 7 LSB of resolution, the error the trimmer is charged
with correcting and cannot see.** The only terms it *cannot* see are the
module-side static ones (cable, in-amp offset, trim setting) — and those are
exactly the terms a set-once trimmer is *good* at. **The authority assignment
gives each authority the error it is worst at:** the set-once trimmer gets the
drifting term; the continuously-measuring firmware is forbidden from touching it.

Deleting the DAC channel remains **right** — two authorities in series on one
path is a genuine failure, and a correction injected downstream of the
measurement point is open-loop. But the *stated* reason ("firmware corrects a
signal it cannot measure") is **false**, and stating it falsely licenses the next,
worse inference: that firmware has nothing to say about the jack. It has a live
measurement of the jack's dominant zero error, and the design throws it away.

**Fix, and it costs nothing:** firmware must not *drive* the analog zero, but it
must **report** it. Publish the accumulated correction as a **pre-gain error in
volts at the in-amp** (gain-independent, so the missing knob readback does not
matter) and as a **percentage of span**, alarm above a fixed fraction of the note
threshold, and log rate as well as total so thermal drift and a developing
occlusion are distinguishable. That turns §6's unbounded silent divergence into
the diagnostic ADR 0006 claims it already is.

---

## §7 — The power-on seed

`[repo: ADR 0006]` *"**Seed it from an ADC capture at power-on**"*. There is no
validity check of any kind on that capture.

**(a) The player is already blowing at power-on.** Entirely ordinary — the
instrument is tethered and powered from the rack; the player picks it up when
the rack comes on, mouthpiece at the lips. `[calc]` A moderate 1.5 kPa at the
seed instant = 1.149 V at the sensor above pedestal = 855 LSB adopted as zero.
Consequences: the digital copy reads 0 while the player blows 1.5 kPa; **note
gating requires 1.5 kPa + threshold to fire**; releasing the breath drives the
copy negative into a clamp. The analog jack, meanwhile, is correct throughout, so
the jack produces a full note while the instrument insists nothing is happening.

Does the auto-zero recover it? Yes — when the player stops, the signal is quiet
and (trivially) below the shifted threshold, so the decay pulls the zero back.
**How long is unspecified.** The decay must be *"slow enough that it cannot chase
a held note"* `[repo]`; a held note is 5–20 s, so τ is plausibly tens of seconds,
and recovery from an 855 LSB error takes several τ. **One to three minutes of an
instrument that appears dead, with no message explaining why**, every time
someone powers up mid-breath.

**This is free to fix and the design already has the means.** The sensor is
ratiometric to a REF5050 at 5.000 V ±0.05 % and the divider is 0.6 with 1 %
resistors, so the **absolute** ADC code at zero pressure is predictable:
`[calc]` 0.200 V × 0.6 = 0.120 V = **148.9 LSB**, with the spec spread
0.152–0.378 V mapping to **113–281 LSB**. **Reject any seed outside a plausible
ambient window**; on rejection, fall back to the last-known-good zero from NVS
(which the real-time board already owns and persists `[repo: firmware/README.md]`)
and say so on the display. Nothing in the repo does this.

**(b) Cold car, twenty-minute warm-up.** The digital copy tracks it — that is the
mechanism working as designed, and I cannot break it. The analog path does not,
and §0's fork decides whether the residual is 13–54 mV (fine) or 0.23–0.96 V (not
fine). **But there is a second mechanism specific to a cold start that neither
representation handles and nobody has measured:** the cavity. `[repo: ADR 0003]`
a 15 K rise in a *sealed* cavity gives 5.2 kPa; the cavity is argued to leak
"fast enough that the thermal rise over 10–20 minutes never builds pressure". A
first-order leak does not give zero — it gives a **lag proportional to the leak
time constant**.

`[calc]` Thermal pressure generation rate = 5.2 kPa over 20 min = **4.3 Pa/s**.
Steady-state lag through a leak of time constant τ:

```
τ =  10 s →  43 Pa →  33 mV sensor →  71 mV in-amp → 0.04 – 0.18 V at the jack
τ =  60 s → 260 Pa → 199 mV sensor → 430 mV in-amp → 0.26 – 1.08 V at the jack
τ = 300 s → 1.3 kPa → clipping territory
```

**τ has never been measured.** ADR 0003 asserts the cavity leaks through
"eighteen unsealed switch cutouts and the seams" and calls the safety "not
lucky", resting on M8's thermal soak to check it. That soak is the right test —
but it is scheduled *after* the design is committed, and the analog path has no
authority that can absorb this at all. **The digital copy will quietly eat it
(§8) and the jack will pass it.** Add τ to M8's measurement list explicitly, and
add "watch the *jack* during the soak, not the display" — which the E10 note
currently forbids conflating, correctly, but nobody scheduled.

**(c) The sensor needs warm-up before its output is valid.** `[from memory]`
integrated silicon pressure sensors commonly specify a **turn-on / warm-up
drift** separately from tempco, on the order of hundreds of microseconds to
milliseconds for the amplifier but longer for self-heating equilibrium.
**Gate:** if the MPXV4006DP specifies a warm-up or turn-on drift longer than the
ESP32-S3's boot time (a few hundred ms), then the power-on seed is taken **before
the sensor's output is valid** and the whole session starts from a bad number. The
fix is the same one as (a): the plausibility window, plus a mandatory settle
delay before the seed. **Named parameter: turn-on drift / warm-up time to
specified accuracy.**

**(d) The one case nobody has considered: the analog path has no seed at all.**
Every power-on, the digital copy gets a fresh (if unvalidated) zero. The analog
path gets whatever a technician set months ago. §0's fork decides whether that
matters; the asymmetry is structural either way.

---

## §8 — "Sub-threshold AND quiet", defeated in both directions

`[repo: ADR 0006]` — decay when breath has been sub-threshold for ~2 s **and**
the signal's standard deviation is below **~2× a commissioning value**, "the same
stillness-gated estimator ADR 0007 already uses for IMU bias, applied to a
different sensor."

**The structural flaw first, because it makes both directions worse.** It is
*not* the same estimator. `[repo: docs/decisions/0007-imu-selection.md]` the IMU's
bias update is gated on **gyro stillness** — a detector on a *different physical
quantity* from the bias being estimated. The breath version judges "quiet" using
**the same signal it is about to redefine**. **A fault that shifts the DC without
adding noise is invisible to it by construction** — and all three faults the gate
exists to catch (blocked restrictor, sealing cavity, shifted sensor offset) are
exactly that: DC shifts with no noise signature. **The gate cannot detect the
class of fault it was added to detect.**

### Direction A: playing it adopts as zero

**A1 — the slow crescendo, with positive feedback.** The threshold gate tests
*level*; the quiet gate tests *variance*. A slow ramp has low variance.

`[calc]` σ of a linear ramp of slope *m* over an estimator window *W* is
`m·W/√12`. With W = 2 s and a commissioning σ_c of 1 LSB (the ADC's own floor
behind a 564 Hz anti-alias `[repo: C-AA-ADC]`), the gate passes while:

```
m·W/√12 < 2·σ_c
m < 2 × 1 LSB × √12 / 2 s = 3.46 LSB/s
  = 3.46 × 1.343 mV = 4.65 mV/s at the sensor
  = 3.46 × 1.753 Pa = 6.1 Pa/s
```

**Any swell slower than ~6 Pa/s is invisible to the quiet gate.** And the failure
is not passive — it is **positive feedback**: the zero chases the rising signal,
which keeps the signal sub-threshold, which keeps the gate open, which lets the
zero chase further. `[calc]` Reaching a 100 Pa note threshold at 6 Pa/s takes
16 s. **A niente entrance on a long tone, or a messa di voce from silence, is
eaten** — the note starts late, quiet, or not at all, while the jack (which has
no auto-zero) plays it correctly. The two representations disagree about whether
a note happened.

**A2 — the mouthpiece at rest on the lip.** Standard technique between phrases.
Lip pressure and warm exhaled air in a dead-ended 400 mm tube give a small,
**extremely steady** DC — low σ, sub-threshold. Adopted as zero within 2 s +
decay. On the next attack the threshold is referenced to a too-high zero; on lip
release the copy goes negative and clamps. This cycles all session.

**A3 — the restrictor's tail defeats the 2 s window.** After a phrase the tube
does not return to ambient instantly; it decays through the PTFE restrictor
`[repo: MECH-PTFE, "Size the orifice at E2"]`. **If the restrictor's pneumatic
time constant exceeds ~2 s, the "sub-threshold for 2 s" window opens on a
still-decaying positive tail** and the decay adopts a positive residual after
every phrase — a ratchet in one direction only, because breath is unipolar.
The restrictor τ is `[repo]` explicitly unmeasured ("the restrictor is still
unmeasured and is the term most able to break it", ADR 0003 §latency).

**A4 — the discriminator is filtered by the design's own components.** The gate
depends on "a held pianissimo has breath noise in it" `[repo]`. Turbulence noise
is broadband and mostly **above** the corner of the pneumatic path (restrictor +
trap volume), the 564 Hz anti-alias, and firmware's per-channel smoothing
`[repo: firmware/README.md]`. **The design low-passes away the very quantity the
gate uses as evidence of playing**, and nobody has measured what survives. If
the surviving σ of a supported pianissimo is under 2 σ_c, A1's blind slope
becomes the whole pianissimo, not just its onset.

### Direction B: drift it refuses to track

**B1 — σ_c is measured under the one condition that never occurs while playing.**
`[repo: ADR 0006]`: *"A held pianissimo has breath noise in it; **an instrument on
a stand does not**."* That sentence is the calibration condition. An instrument
**in the player's hands** has hand tremor, handling noise, the player's own
nasal breathing coupling through the open mouthpiece, and body motion — the
instrument has an IMU precisely because it moves. All of that raises σ **above**
2 σ_c, so the gate closes.

**The gate therefore tracks when drift is least and refuses when drift is
greatest.** The 10–20 K interior rise happens *because* the instrument is being
played and held; the auto-zero only runs when it has been put down. `[repo:
ADR 0006]` the interior rise is "10–20 K over the first 10–20 minutes of a
session" — i.e. entirely inside the window when the instrument is in hands. **The
mechanism is anti-correlated with its own purpose.**

**B2 — a continuous set defeats it outright.** A player who performs for 40
minutes with only short, held-in-hand rests never satisfies both conditions
simultaneously. The zero remains the power-on seed for the whole session —
**startup-only zeroing, in precisely the case ADR 0006 opened by declaring
startup-only zeroing insufficient**: *"A zero captured once at startup is wrong by
the time the first piece ends."*

**B3 — and the log goes quiet exactly when the fault is present.** The
accumulated correction only accumulates when the gate is open. A developing
occlusion produces its symptom **while playing**, when the gate is shut. The
"number that walks" walks only when the instrument is idle, which is when nobody
is looking at it.

### Fixes, using parts already in the instrument

- **Gate on IMU stillness, not on the breath signal's own variance.** The
  instrument has an IMU and ADR 0007 already maintains a stillness detector. That
  is an **orthogonal** detector, which is what makes the IMU's own bias estimator
  sound and what the breath version lacks. "On a stand" then means *on a stand*,
  which is what the prose already says it means.
- **Measure σ_c in the player's hands at rest, not on a stand**, and validate the
  2× multiplier against both conditions at E2.
- **Band the variance estimator** (e.g. 2–20 Hz) so a slow ramp contributes to it
  rather than being averaged out — this closes A1 directly.
- **Rate-limit and total-limit the correction**, and alarm rather than absorb when
  either is exceeded. An auto-zero with no clamp is a fault-concealment machine
  regardless of its gate, which is ADR 0006's own phrase.
- **Specify σ_c, the window W and the decay τ as numbers.** None of the three
  appears anywhere in the repo. **As written the rule is not a specification** —
  every quantitative statement in this section scales linearly with σ_c and
  inversely with W, so whether the arrangement is safe is currently undetermined
  by the documents.

---

## §9 — "Until the in-amp output reads 0 V" — against what, at what temperature

`[repo: breath-receive-stage.md, Commissioning]` — *"With the body at room
temperature and no breath at the mouthpiece: `TRIM-BREATH-ZERO`, internal, until
the in-amp output reads 0 V. Once, at build."*

**The instrument does not specify an instrument.** `[calc]` A 3½-digit DMM on
autorange reads the 2 V range at 1 mV resolution; 1 mV at the in-amp is 0.6–2.5 mV
at the jack — irrelevant. **Measurement resolution is not the problem.** Three
other things are:

1. **It is commissioned at the one temperature the instrument is never in.**
   "Room temperature" is the instrument's *cold* state. It spends the bulk of
   every session 10–20 K warmer `[repo: ADR 0003, ADR 0006]`. So the trim is
   deliberately set at one end of the drift range, making the residual
   **one-sided: 0 at the start and +21.6 mV after warm-up**. `[calc]` Trimming
   **after a 20-minute warm-up with the body assembled**, or at the midpoint,
   halves the worst-case residual to **±10.8 mV** — and §4's gain-knob
   interaction halves with it, from 41 mV to 21 mV. **Free.** The procedure gets
   this exactly backwards and the page says "with the body at room temperature"
   as though it were a precision, when it is the choice that doubles the error.
2. **The node is not specified either.** "The in-amp output" is a pin on an IC
   on an assembled module. There is no named test point in the BOM. `[repo:
   docs/review/2026-09-20-cold-review/D2-missing-testability.md]` exists for
   exactly this class of gap. Add `TP-BREATH-INAMP` and `TP-AGND-MOD`.
3. **What "no breath at the mouthpiece" means is not stated, and it matters
   more than the meter.** The mouthpiece must be *open to the room and not held*,
   because §8-A2's lip-rest bias and §7(b)'s cavity lag both appear at this node.
   The instrument must be assembled (the cavity is part of the pressure
   reference) and thermally settled. None of that is in the three-step procedure.
4. **Nothing re-verifies it, ever.** `[from memory]` silicon pressure sensors
   specify **long-term offset stability** — typically a fraction of %FSS per year.
   `[calc]` At 0.25 %VFSS/yr on a 4.6 V span that is 11.5 mV/yr at the sensor =
   25 mV/yr at the in-amp = **15–62 mV/yr at the jack**, cumulative, with no
   mechanism anywhere in the design to notice. **Named parameter:** long-term
   offset stability, %VFSS per year. The instrument body is **bonded** and the
   module trimmer needs rack removal, so "re-trim annually" is a real ask. §6's
   reporting fix is what makes it visible, and is the only thing that would.

---

## §10 — Staleness sweep: every file was re-checked on disk at the end of the pass

The trimmer went in this morning. Parts of the claim it replaced are still there,
and the corrections that landed mid-review landed unevenly. **Verified against
the working tree, not from memory of an earlier read:**

| File | Text | State |
|---|---|---|
| `hardware/module/breath-receive-stage.md:68` | section heading "**`REF` ties to ground**, and the polarity question dissolved twice" — on the page that introduces the trimmer, 34 lines above the section titled "Why `REF` is trimmed rather than grounded" | **still present** |
| `hardware/module/breath-receive-stage.md:223` | "now that `REF` is **grounded** it touches the breath stage in no way at all" — **same file contradicts itself**, and it is the watchdog-scope argument (§2b) | **still present** |
| `hardware/module/breath-receive-stage.md:54` | trimmer drawn "**from VREFOUT**" after ADR 0003 and the BOM moved it to the LM317 rail — on the page that declares itself authoritative over the ADR | **still present** (§2a) |
| `hardware/module/breath-receive-stage.md:~234` | downstream `OFFSET` reference nominated as "the buffered `VREFOUT` created for pitch" | **still present** (§2b, §5) |
| `firmware/README.md:70` | "since the in-amp's `REF` pin is **grounded** rather than driven by a firmware zero (ADR 0003), no DAC register touches the breath jack at all" — **false twice over** per §2b | **still present** |
| `hardware/bom.csv`, `U-DIFFRX` | "**REF ties HARD to module AGND - no divider**" — the same CSV's `TRIM-BREATH-ZERO` row specifies a trimmer plus divider into a buffer on that pin | **still present** |
| `hardware/bom.csv`, `TRIM-BREATH-ZERO` | range, and the `VREFOUT` reference | **corrected mid-review** ✓ (§1, §2a) |
| `docs/decisions/0006-cv-channel-allocation.md:158` | power-on table: "**Breath \| 0 V \|** The receiver's differential pulldown holds it there" — the pulldown was deleted, and the value is wrong | **still present** |
| `hardware/module/digital-and-supervision.md` | "the BOM's `R-PRESENCE` note still describes the old −200 mV arrangement and is wrong" — the BOM was rewritten to the new tap; the schematic page has not noticed | **still present** (§3) |
| `docs/decisions/0003-breath-sensing-path.md` | "`REF` ties to module analog ground" ×2 | **corrected mid-review** ✓ |

`hardware/bom.csv` rows `U-DIFFRX` and `TRIM-BREATH-ZERO` are **directly
contradictory rows in the same file**. Whichever is read first wins at layout.

**Two further internal inconsistencies found while checking:**

- `[repo: hardware/bom.csv, U-OPA-PITCH]` claims "Twelve halves, **eleven
  used**" and then lists ten: pitch, mod 1–4, mod offset buffer, breath gain,
  breath offset, `VREFOUT` follower, breath `REF`-zero buffer. The count is off
  by one. Separately, the BOM allocates **two** halves ("breath gain", "breath
  offset") where `breath-receive-stage.md` draws **one** ("an inverting summer
  does gain and offset with two pots into one virtual ground … ½ OPA2197"). The
  schematic's single-half version is also the justification for the input swap,
  so this is not bookkeeping — and §5(a) raises the possibility that the gain
  wiper needs a buffer, which would consume the claimed spare.
- `[repo: ADR 0003]` justifies firmware zeroing partly on *"sensor offset and
  **atmospheric pressure** both drift"*. The MPXV4006DP is a **differential**
  part with its reference port open to the cavity `[repo: ADR 0003, "the
  reference port stays open to the cavity"]`, so barometric change appears on
  **both** faces of the diaphragm and cancels. The atmospheric-drift
  justification is **not valid for this part** — and it was not valid for the
  gauge variant either, for the same reason. Only the *differential transient*
  between the tube and the cavity (two leak paths, two time constants, §7b) is
  real. The stated reason is wrong; the conclusion survives on the other reason.

## §11 — What survives, stated fairly

I was asked to break it. These parts I could not break:

- **The rule itself, amended.** "One zero authority per representation" is sound.
  Its failure here is in *counting*: a fixed null is not an authority, and the
  design already established that language in V4's C1 and did not reuse it.
- **Deleting DAC channel 6.** Correct, for the correct structural reason (an
  injection downstream of the measurement is open-loop, and two adjustable
  authorities in series on one path is a split brain). The *stated* reason
  ("cannot measure it") is false — see §6 — but the decision is right.
- **The pedestal must be nulled ahead of the gain pot.** The WX5 citation is
  apposite and the reasoning is correct. Grounding `REF` genuinely does make the
  knobs interact, and the earlier revision that claimed otherwise was wrong.
  `[calc]` untrimmed, sweeping `GAIN` 0.6→2.5 moves the jack rest by
  0.432 × 1.9 = **821 mV**. That is a real defect and the trimmer is the right
  *shape* of fix.
- **Buffering `REF`.** Unambiguously right; a bare divider there would spend the
  CMRR budget one-for-one.
- **The 23 mV thermal figure, in its own branch.** If §0 resolves to "0.5 mV/K,
  unit spread at 25 °C", then 13–54 mV at the jack is genuinely a quarter turn
  nobody will touch, and I could not make that number bigger by any legitimate
  route.
- **`C_diff` ten times `C_cm`, the filter ahead of the in-amp, R4/R5 as a
  common-mode bias return.** All correct, all well argued, and §3's CMRR
  arithmetic uses the same framework to show why the presence tap violates it.

---

## §12 — Is there a simpler arrangement, with fewer authorities?

**Fewer *elements*: no. Fewer *authorities*: yes, and it is the right answer.**

Two elements are **structurally required**, and this is provable rather than a
preference. `[calc]` The player needs the jack's floor positioned **after** the
gain stage (otherwise `GAIN` scales the floor). The pedestal must be nulled
**before** the gain stage (otherwise `GAIN` scales the pedestal). Pre-gain and
post-gain are different nodes, so no single element can do both.

Candidates considered and rejected:

- **Put `OFFSET` pre-gain and drop the trimmer.** `V_jack = G·(V_in + V_off)` —
  perfectly decoupled at rest for all G, one authority. **Rejected:** the player
  can then no longer position the floor independently of span, which is the
  knob's entire job and is ADR 0006's "gain first, then offset".
- **Null at the source, at the instrument.** Make the instrument-side buffer a
  difference stage subtracting 0.200 V derived from the *same REF5050* that
  supplies the sensor. `[calc]` The null then tracks the supply **exactly**
  (both ratiometric to one reference), costs zero extra parts (two resistors on
  an op-amp half already present), sits ahead of everything, and removes a
  module-side element entirely. **Rejected as a sole fix:** it subtracts the
  *nominal* 0.200 V, leaving the unit-to-unit spread of §0/§1 (up to ±0.18 V)
  uncorrected — worse than a trimmer that can be set per unit. **But it is worth
  adopting alongside**, because it removes the *ratiometric* and *reference-loss*
  error terms that §2 is about, leaving the trimmer with only the small
  unit-to-unit residual, which in turn makes the trimmer's range problem (§1)
  disappear.
- **Firmware drives the null through the deleted DAC channel.** Already correctly
  rejected. Do not reopen it.

**The correct arrangement is the one the design has, with the vocabulary fixed
and four defects closed:**

> **One *adjustable* zero authority per representation.** Fixed nulls are not
> authorities. The analog CV's single adjustable authority is the panel `OFFSET`
> knob; `TRIM-BREATH-ZERO` is a **fixed pre-gain null**, set at build and never
> touched. The digital copy's single authority is firmware.

That rule is legal only if the trimmer is genuinely fixed and genuinely
sufficient — which requires, all four:

1. **Range 0 → +1.0 V**, covering the sensor's own specified pedestal spread (§1).
2. **A reference that is alive with the rails**, not `VREFOUT` — for the trimmer
   (done, §2a, except in the drawing) **and for the downstream `OFFSET`
   injection** (not done, §2b). Both, or `firmware/README.md`'s "no DAC register
   touches the breath jack" stays false.
3. **Commissioned warm, at a named test point, with the body assembled** (§9).
4. **Firmware reports the pre-gain zero error it already measures**, in span
   percent, with rate and total, so a drifting fixed null is *visible* without
   being *corrected* (§6). This is what replaces the cross-check the E10 note
   correctly removed.

---

## §13 — Actions, ranked

| # | Action | Where | Severity |
|---|---|---|---|
| 1 | Rule `VREFOUT` **out** for the downstream `OFFSET` reference — it is still nominated there, and it puts a **volts-scale** step on the breath jack at every boot. This is the largest surviving defect | `breath-receive-stage.md` §Still open | **Showstopper** (§2b) |
| 2 | Correct the schematic: `TRIM-BREATH-ZERO` is from the **LM317 5.21 V rail**, not `VREFOUT`. The page declares itself authoritative over the ADR, so the stale drawing currently wins | `breath-receive-stage.md:54` | **Showstopper** (§2a) |
| 2b | Nominal is **0.432 V** not 0.437 V, and 1.0 V covers **0.463 V** of pedestal not 0.458 V — both omit the bias-pair divider the same page derives | `breath-receive-stage.md`, `hardware/bom.csv` | Low (§1) |
| 3 | Correct `R-PRESENCE`: with 100k/10k the threshold is **0.47 V** against a 0.198 V signal — `OE` stays disabled and the whole module is dead at E7 | `hardware/bom.csv` row 100 | **Showstopper** (§3) |
| 4 | Presence comparator: keep it on the **in-amp output**, threshold = **`V_REF`/2 − 50 mV** from the trim buffer. Do **not** tap the `IN−` node with an LM311 — Ib × 1 MΩ = 100–250 mV against a 198 mV signal, and the single-leg load costs ~39 dB of CMRR | `digital-and-supervision.md`, `hardware/bom.csv` rows 99–100 | **High** (§3) |
| 5 | Resolve §0's fork the moment nxp.com is reachable; the 23 mV thermal claim and the trimmer range both depend on it | ADR 0003, `breath-receive-stage.md` | **High** (§0) |
| 6 | Validate the power-on seed against a plausible-ambient window (**113–281 LSB**); fall back to NVS and say so | `firmware/README.md`, ADR 0006 | **High** (§7) |
| 7 | Gate the auto-zero decay on **IMU stillness**, not the breath signal's own variance; band the estimator; clamp total and rate | ADR 0006 | **High** (§8) |
| 8 | Publish the accumulated correction as **pre-gain error in span percent**, with rate — the replacement for the cross-check E10 removed | `firmware/README.md`, ADR 0006 | **High** (§6) |
| 9 | Commission **warm**, at a named test point, body assembled, **and after `R-REG-SET` is bench-selected at E7** | `breath-receive-stage.md` §Commissioning | Medium (§9) |
| 10 | Specify σ_c, the window W and the decay τ as **numbers**. The rule is not currently a specification | ADR 0006 | Medium (§8) |
| 11 | Write the downstream stage's decoupling requirement as a **constraint on E10** (gain ahead of the summing resistor; feedback-rheostat gain forbidden), not as an accomplished property | `breath-receive-stage.md` §Still open | Medium (§5) |
| 12 | Take breath's `OFFSET` reference from raw buffered `VREFOUT`, **not** the pitch-trimmed node; state that `TRIM-BREATH-ZERO` must be wired as a constant-load potentiometer | `breath-receive-stage.md`, `hardware/bom.csv` | Medium (§5) |
| 13 | Retitle `breath-receive-stage.md:68`; fix line 223; fix ADR 0003:370 and :574; fix `firmware/README.md:67`; fix `bom.csv` row 28 (`U-DIFFRX`); fix ADR 0006's power-on table row for breath | six files | Medium (§10) |
| 14 | Reconcile the op-amp half count (10 vs 11) and the one-half-vs-two-halves disagreement between the schematic and the BOM | `hardware/bom.csv` row 13 | Low (§10) |
| 15 | Add cavity leak τ to M8's soak, and watch the **jack** during it | ADR 0003, ROADMAP M8 | Medium (§7b) |
| 16 | Delete the "atmospheric pressure drifts" justification — it does not apply to a differential part with an open reference port | ADR 0003 | Low (§10) |
| 17 | Reconcile `digital-and-supervision.md`'s "Still open / the BOM is wrong" against a BOM that has already been changed | two files | Low (§3) |

---

## §14 — What would have made me say SURVIVES

Stated plainly, because the brief asks for it:

- If `TRIM-BREATH-ZERO`'s range had been ≥ 0.82 V, its reference had been the
  LM317 rail, the **`OFFSET` knob's reference had been ruled off `VREFOUT` in
  the same breath**, and the commissioning step had been "after a twenty-minute
  warm-up, at `TP-BREATH-INAMP`, after E7 selects `R-REG-SET`", then §1, §2 and
  §9 all go away and the trimmer is a genuine fixed null. **Three of those four
  were done during this review, by a parallel reviewer, in one document each.
  The fourth — the `OFFSET` reference — is untouched, and it is the one with a
  volts-scale consequence.**
- If the table had said *"one **adjustable** zero authority per representation;
  `TRIM-BREATH-ZERO` is a fixed pre-gain null, not an authority"* — which is the
  language V4's C1 already demanded for pitch — §4 becomes a naming quibble
  instead of a split-brain finding.
- If the auto-zero had been gated on the IMU stillness signal the instrument
  already computes, with σ_c, W and τ specified as numbers, §8 would have been
  a request for measurement rather than a break.
- If firmware had been required to **report** the pre-gain zero error it already
  measures, §6's unbounded silent divergence would be a visible number instead of
  an absent one, and the design's claim that the log "can only mean a real fault"
  would become true instead of backwards.

**None of those is expensive.** Three are one line of text and two are a resistor
value. The arrangement is one honest revision away from surviving, and today it
does not — and the churn this document had to be re-verified against is itself
the argument for finishing the propagation rather than fixing each claim in
whichever file the reviewer happened to be reading.
