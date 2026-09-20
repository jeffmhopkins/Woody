# B3 — Pitch CV chain: independent analog review

Scope: DAC → scaling stage → trim → filter → jack, for channel 1 only.
Sources read: `README.md`, `ROADMAP.md`, `docs/decisions/0001`–`0014`,
`docs/reference/latency-budget.md`, `hardware/bom.csv`, `config/key-layout.yaml`.
`docs/review/` and `docs/log/` were deliberately not read.

---

## 0. Units, and the chain as I reconstruct it

The documents never write the pitch transfer function down in one place, so this
is my reconstruction. Everything below depends on it; if it is wrong, say so and
most of the arithmetic moves.

- 1 semitone = 83.333 mV → **1 cent = 0.8333 mV → 1 mV = 1.200 cents**
- 1 V = 1 octave = 1200 cents → **a fractional gain error `g` costs `1200·g`
  cents per octave measured from its own pivot**. 100 ppm = 0.120 cents/octave.
- **An offset error is a constant transposition at 1.2 cents/mV**, everywhere,
  with no pivot and no way to hide it.
- Reference for "worth fixing": a well-compensated VCO drifts ~0.35 cents/K,
  i.e. **3.5 cents over a 10 K swing**. Anything an order of magnitude under
  that is noise in the argument.

Reconstructed chain:

```
DAC8568C, internal 2.5 V ref, ×2 gain  → 0 … 5.000 V full scale, AVDD 5.25 V (LM317LZ)
used code window 0.25 … 4.75 V         → codes 3277 … 62259 (58 982 codes)
scaling stage, gain 2.000, offset −2.500 V  → −2.000 … +7.000 V
  2 × 0.25 − 2.5 = −2.000 ✓     2 × 4.75 − 2.5 = +7.000 ✓
1 kΩ series (R-OUT-PROT) + shunt C ≈ 10 nF (15.9 kHz) + BAV99 + PJ398SM
```

Resolution: DAC LSB 76.29 µV, ×2 = **152.6 µV at the jack = 0.183 cents/LSB**.
Quantisation is ±0.092 cents. It is not a term in anything that follows.

Datasheet figures used below and how I got them:

| Figure | Value | Provenance |
|---|---|---|
| DAC8568 INL | ±4 LSB | web-verified (TI product page / datasheet summary) |
| DAC8568 internal ref drift | 2 ppm/°C typ, **5 ppm/°C max** | web-verified |
| DAC8568 internal ref initial accuracy | 0.004 % typ | web-verified |
| DAC8568 VREFIN/VREFOUT | ref is **externally available, sources up to 20 mA** | web-verified (TI summary); confirm against the datasheet's reference section |
| OPA197 Vos | ±100 µV max | web-verified |
| OPA197 Vos drift | **±2.5 µV/°C max** | web-verified |
| OPA197 voltage noise | 5.5 nV/√Hz @ 1 kHz | web-verified |
| LT5400 matching drift | 0.2 ppm/°C typ, 1 ppm/°C max | web-verified |
| LT5400 **absolute** TC | **8 ppm/°C** | web-verified |
| Bourns 3296 TC | ±100 ppm/°C | web-verified |
| Bourns 3296 setting stability | ~±1 % of R after environmental stress | **from memory**, verify |
| 1N5817 dynamic resistance ~0.3 Ω at 0.3–0.6 A | | **from memory**, from the Vf curve |
| OPA197 PSRR ≥80 dB at 2 kHz | | **from memory**, extrapolated from the DC figure |
| DAC8568 zero-code / gain error, glitch energy, guaranteed-linear code range | | **not obtained** — ti.com and octopart are blocked from this session |

---

## 1. The pitch offset has no specified voltage reference, and the obvious implementation hangs the whole instrument's tuning on the rack's +12 V rail

**Severity: MAJOR**

**Where.** ADR 0006 names the authority but never the source:

> "the **trimmer** is the offset authority for pitch, the **DAC channel** is the
> offset authority for the mod channels"

and

> "**Trimmers set gain and offset.** Two per pitch channel, multiturn cermet."

Nothing in ADR 0004, ADR 0005, ADR 0006 or `bom.csv` says what voltage the
offset trimmer divides down. The BOM row is `TRIM-PITCH … "multiturn cermet
trimmer, 5-10% of ratio" … Pitch scale and offset trimmers` — a trimmer and
nothing to trim against.

**Why it matters.** The pitch stage needs a −2.500 V offset. In the topology the
documents imply (non-inverting gain of 2, offset injected at the bottom of the
feedback divider — which is what `R-OPAMP-IN`, "1 kΩ in series with each op-amp's
**non-inverting** input where the DAC drives it", commits to), the offset is
`−Vref_off × Rf/Rg` with `Rf = Rg`, so **Vref_off = +2.5 V**. The only +2.5 V
that exists on the module unless one is created is a divider from **+12 V**.

Sensitivity is then `2.5/12 = 0.2083 V/V`, and at 1.2 cents/mV:

| +12 V node moves by | Pitch offset moves | Musical effect |
|---|---|---|
| 12 mV (100 ppm/°C rail over 10 K) | 2.50 mV | **3.0 cents** transposition |
| 50 mV (another module powers up in the case) | 10.4 mV | **12.5 cents**, instant, untracked |
| 90 mV p-p (see below) | 18.8 mV p-p | **22.5 cents p-p of FM** |

That last row is the one that matters. ADR 0004 states the mechanism itself:

> "The WS2815 strips modulate their current at the PWM rate, around 2 kHz."
> "a 200–400 mA square wave"
> "**both branches are common upstream at the bus header**. Filtering downstream
> of a shared node does not isolate that node."

A 1N5817's dynamic resistance in the 0.3–0.6 A region is ~0.3 Ω (from its Vf
curve, from memory), and that diode is upstream of the branch point. A 300 mA
square wave across it is ~90 mV p-p at ~2 kHz on the module's protected +12 V
node. The analog branch's ferrite (a few hundred mΩ at 2 kHz, as ADR 0004 itself
concedes) against 47 µF (1.7 Ω at 2 kHz) attenuates that by only ~15 %.

So if the offset reference divides that node, **the instrument's own lighting
frequency-modulates its own pitch by ~20 cents peak-to-peak at 2 kHz, and the
depth tracks whatever the 8×8 matrix is displaying — which ADR 0014 says is
breath by default.** Pitch wobble proportional to how hard you are blowing.

The sharpest way to put it: ADR 0004 worried about exactly this rail, but
defended the wrong node.

> "the buck's pulsed draw is absorbed locally instead of modulating the rail the
> pitch scaling stage is **referenced to** — … since this module's analog
> section is precision"

The op-amp's *supply* pins have ≥80 dB of PSRR at 2 kHz (from memory): 90 mV ×
10⁻⁴ = 9 µV = 0.011 cents. Irrelevant, as ADR 0004 half-concludes ("survivable
by accident"). The *offset reference* has a transfer function of 0.2083, i.e.
**−13.6 dB**. The design is protecting a node that is 86 dB quieter than the one
it left unspecified.

There is a second limb. ADR 0006's power-on table says:

> "**Pitch** | Bottom of its range, below −2 V | Subsonic. A VCO there is inaudible"

That is only true if the offset source is alive before firmware runs. A
rail-divider satisfies it; a DAC-derived source does not (the internal reference
is disabled at reset, so both terms would be zero and pitch parks at **0 V** — an
audible note, not a subsonic one). The claimed power-on behaviour therefore
silently depends on the unspecified choice. It cannot be verified as written.

**Proposal.** Take the offset from the DAC8568's own reference pin. TI's
material says the internal 2.5 V is available at VREFIN/VREFOUT and sources up to
20 mA — it is already on the board, already at exactly 2.500 V, already 2 ppm/°C
typ / 5 ppm/°C max. Three consequences, all good:

1. **Drift collapses.** 2.5 V × 50 ppm (10 K, max spec) = 125 µV = 0.15 cents.
2. **It is ratiometric.** With `Vdac = 2·Vref·d` and offset `= Vref`, the whole
   transfer is `Vout = Vref(4d − 1)`, which is zero at `Vout = 0 V`. Reference
   drift therefore becomes a **pure gain error pivoting at 0 V** — 0.060
   cents/octave at 50 ppm — instead of a transposition. Reference drift stops
   being an offset term at all.
3. **Zero parts, zero rail exposure.**

Two details: buffer VREFOUT with the spare OPA2197 half if you want the DAC's own
reference node kept clean (the offset leg draws a code-dependent ±0.23 mA through
a 10 kΩ leg; against a ~0.5 Ω source impedance that is 0.11 mV of code-dependent
shift = 0.13 cents, and it is proportional to Vdac so the gain trim absorbs it —
but it is worth not having). And accept that pitch then parks at **0 V** at
power-on and on watchdog `CLR`, not subsonic.

If the subsonic park is genuinely wanted, the alternative is a **REF5025** — the
same family as the already-specified `U-REF-BREATH` REF5050, so no new supplier —
on +12 V, alive from rack power-on: 2.5 V × 30 ppm = 75 µV = 0.09 cents.

Either way the rule is: **not a rail.** I would take VREFOUT and give up the
subsonic park, because the park's value is small — breath parks at 0 V, so the
VCA is shut and nothing is heard regardless of where pitch sits.

**Confidence: high** that the offset source is unspecified and that a rail
divider is the natural default; **medium-high** on the 90 mV ripple figure, which
rests on a remembered diode curve and an assumed bulk value.

**Falsified by:** scoping the module's protected +12 V node (after the 1N5817,
after the analog-branch ferrite and bulk) while the WS2815 strips run a
mid-brightness animation, AC-coupled, 1 mV/div. If the ~2 kHz component there is
below ~4 mV p-p, the FM limb of this finding collapses to ~1 cent and only the
thermal and load-step limbs remain. This is already half-scheduled as E6's "Rack
rail ripple, both directions" — it needs the LED strips running, which E6 as
written does not require.

---

## 2. "The 1 kΩ output resistor is a pure gain error the trimmer cancels" is false, and the firmware scale-factor mitigation leaves 29–59 cents that nothing can remove

**Severity: MAJOR**

**Where.** ADR 0006, the section "The pitch output keeps its 1 kΩ series
resistor":

> "**It is a pure gain error, and the gain trimmer has full authority over it.**
> … A resistive divider is entirely `a` — it multiplies the whole transfer
> function by a constant. Both the trimmer and the firmware scale factor can
> cancel it exactly, at any magnitude. Nothing is lost that cannot be recovered."

and the mitigation:

> "**Firmware carries a per-load scale factor.** Firmware could never implement
> `b`, but it has always been able to implement `a`. A named scale preset per
> patch — 'one VCO', 'two multed' — is a stored float and a display line, and it
> reaches loads the trimmer was not set for without touching a screwdriver."

**Why it is wrong.** The divider multiplies the whole transfer function — offset
included. That is precisely why a scale factor cannot undo it.

Trim against load A (`k_A = R_L/(R_L+1k)`) so the jack reads `V = 2·D − 2.5`
exactly. The amplifier is then `G = 2/k_A`, `B = −2.5/k_A`. Patch load B and let
`r = k_B/k_A`:

```
V_jack = r·(2·D − 2.5)
```

Firmware applies a scale factor `s` to the commanded DAC volts `D`:

```
V_jack = 2rs·D − 2.5r
```

Choosing `s = 1/r` corrects the slope exactly, as the ADR says. It leaves the
constant term at `−2.5r` instead of `−2.5`:

```
residual offset = 2.5·(1 − r)   volts, constant at every note
```

| Change of load | r | Residual | Cents |
|---|---|---|---|
| trimmed open-circuit → 100 kΩ VCO | 0.99010 | +24.8 mV | **+29.7** |
| 100 kΩ → 50 kΩ (the ADR's own "two multed" case) | 0.99019 | +24.5 mV | **+29.4** |
| 100 kΩ → 33 kΩ (three VCOs) | 0.98029 | +49.3 mV | **+59.1** |

The ADR quotes 58 cents at five octaves for the 100 k → 50 k re-patch and offers
the scale preset as the fix. The scale preset takes that from a progressive
−23.5 cents/octave error to a **flat +29 cents sharp on every note** — better in
magnitude, worse in character (a progressive error can be mistaken for a VCO that
tracks badly; a flat 29 cents is the whole instrument out of tune against the
rest of the patch), and still six times the entire thermal budget and eight times
the VCO's own 10 K drift.

Note that the ADR's own uncorrected figures are right: 1k/101k = −0.9901 % =
**−11.9 cents/octave**, and −23.5 for 50 kΩ. I re-derived both. The error is not
in the arithmetic, it is in the claim that the residual is recoverable.

**The deeper point, and the good news.** The ADR's founding premise —

> "**Firmware calibration has no offset authority.** A two-point fit is
> `y = a·x + b`. Scaling the DAC code implements `a`. **Nothing implemented `b`.**"

— is a property of the *calibration model*, not of the hardware, and it has
already been fixed by accident elsewhere in the same ADR. The decision to

> "**Use the DAC's 0.25–4.75 V window rather than its full 0–5 V span.**"

reserves 3277 codes at each end. At the DAC that is 0.25 V; through a gain of 2
it is **±0.5 V = ±600 cents of firmware offset authority at the jack**. The
worst case above needs 24.6 mV of DAC-side shift = **323 LSB**, about a tenth of
the reserved window.

So firmware has `b`. It simply has to be allowed to use it: the stored
calibration must be an affine pair, not a float.

```
code = round( (V_target − b_hw) / a_hw )     per load preset: (a, b)
```

with `b = 1.25·(1 − 1/r)` volts of DAC-side shift for a load change, or — better
— with both numbers just measured directly at E9 against each patch.

**Proposal.**

1. Change the calibration model from "a stored float" to a stored `(gain,
   offset)` pair per load preset, and change the multi-point NVS table from
   code-scale entries to absolute target volts per anchor. This is a firmware
   change and costs nothing.
2. Correct ADR 0006's claim: the 1 kΩ divider is recoverable, but it takes *both*
   coefficients, not one. It stays at 1 kΩ — I agree with keeping it, and with
   rejecting the in-loop dual-feedback alternative on stability grounds.
3. Keep the "use a buffered mult" advice. It remains the actual fix; the above is
   what happens when someone does not.

**Confidence: very high.** This is algebra, not component behaviour. The only
assumption is that the hardware offset is injected *before* the 1 kΩ, which it
must be — the ADR's own divider table presumes it.

**Falsified by:** E9's "Pitch DC load sweep: open / 100k / 50k / 33k", which the
roadmap already schedules. Trim at open circuit, then patch 50 kΩ and apply the
scale factor that makes the top anchor correct. If the bottom anchor is then
still correct, I am wrong. Prediction: it will read ~25 mV high, uniformly.

---

## 3. The gain trim range is sized against the wrong constraint, and ADR 0006's own trimmer-tempco table is ~5× pessimistic relative to the implementation the same section recommends

**Severity: MINOR** (but it is the finding that pays for Finding 2)

**Where.** ADR 0006:

> | Trim range | Net ratio tempco | Drift over 10 °C |
> | 5 % | 22 ppm/°C | **2.4 cents** |
> | 10 % | 34 ppm/°C | 3.7 cents |
> | 20 % | 58 ppm/°C | 6.3 cents |
>
> "That is worse than a matched network (0.11 cents) … **Keep the trim range
> small — 5 to 10 % — around a fixed precision resistor.** The LT5400 can still
> set the nominal ratio exactly, with the trimmer providing only the adjustment"

**Two errors, in opposite directions.**

*The table is too pessimistic.* It is computed against "a fixed 0.1 % 10 ppm/°C
resistor" — a discrete. The very next paragraph instead puts the trimmer on an
LT5400 leg. For a trimmer of fraction `f` in series with one leg of a matched
pair, the ratio drift is not the weighted average of absolute tempcos; the
matched pair's own absolute tempco **cancels out of the ratio** and only the
*difference* survives:

```
d(ratio)/ratio per K  =  f · (α_trim − α_network)
```

With the verified figures — Bourns 3296 at ±100 ppm/°C, LT5400 absolute at
8 ppm/°C:

| Trim fraction | Net ratio TC | cents/octave over 10 K | cents at 5 octaves |
|---|---|---|---|
| ±1.5 % | 1.4 ppm/°C | 0.017 | **0.08** |
| ±5 % | 4.6 ppm/°C | 0.055 | **0.28** |
| ±10 % | 9.2 ppm/°C | 0.110 | **0.55** |

So the honest cost of a 5 % trim is **0.28 cents over 10 K**, not 2.4. The
trimmer is not "comparable to discrete resistors (5.4 cents)"; it is within a
factor of five of the bare matched network. The section's conclusion (accept the
trimmer) is right; its arithmetic understates how right.

*The range is too narrow for what the ADR asks it to do.* ADR 0006 simultaneously
requires the gain trim to absorb the load divider:

> "The resistor stays at 1 kΩ, and calibration absorbs it."

A 33 kΩ load needs **+3.03 %** of gain. If "5 % trim range" means ±2.5 %, the
trimmer **cannot reach it**. If it means ±5 %, it reaches it with 1.97 % left
over for the DAC's reference initial accuracy, the DAC's gain error and the
stage's tolerances — thin, and the specification is ambiguous between the two
readings.

**Proposal.** Invert the split. Once firmware has `b` (Finding 2), it owns the
load correction entirely — that is the coefficient pair that actually cancels it.
The trimmer then only has to absorb component tolerance: DAC internal-reference
initial accuracy (0.004 % typ, worst case some tenths of a percent), DAC gain
error, and the LT5400 ratio (0.01 % — nothing). **±1.5 % is ample.** That halves
the tempco term to 0.08 cents and, more usefully, shrinks the setting-stability
term below:

| | ADR as written (±5 %, discrete) | Recommended (±1.5 %, on an LT5400 leg) |
|---|---|---|
| Tempco over 10 K | 1.32 cents @ 5 oct | 0.08 cents @ 5 oct |
| Setting stability (1 % of trimmer R, post-stress) | 0.60 cents/oct = 3.0 @ 5 oct | 0.18 cents/oct = 0.90 @ 5 oct |

Setting stability, not tempco, is the trimmer's real cost — and it is the only
term in the corrected budget that is the same order as the VCO's own drift.
Standard practice applies: lock the screws with a dab of lacquer after E9.

**Confidence: high** on the tempco arithmetic (all inputs web-verified);
**medium** on the setting-stability figure, which is from memory and is a
post-environmental-stress spec, not a per-year drift. **High** that the ±2.5 % vs
±5 % ambiguity needs resolving in writing.

**Falsified by:** measuring the assembled stage's gain in a 10 K oven step with
the trimmer at each end of its travel. If the ratio moves more than ~50 ppm over
10 K with a 5 % trim on an LT5400 leg, my cancellation model is wrong and the
ADR's table is right.

---

## 4. Trimming and the NVS table both own gain, with no rule that says which is stale

**Severity: MINOR**

**Where.** ADR 0006 is careful about offset authority —

> "**Two offset authorities in series would be a split-brain failure**, so they
> are kept apart deliberately"

— but immediately creates the same situation for gain and does not notice:

> "**Trimmers set gain and offset.** … **Firmware handles what trimmers cannot:**
> DAC integral nonlinearity … Use a **multi-point** table, roughly one point per
> octave"

A per-octave table of correction points is not only an INL correction. It is a
piecewise-linear map, and it carries local gain and offset inside every segment.
Turn the gain trimmer after the table is built and every entry in the table is
wrong by the amount you turned it, silently.

The ROADMAP already identifies the adjacent failure:

> "**Blank or corrupt NVS → default calibration** | The instrument plays. It
> sounds like an instrument. It is just badly out of tune, with no indication
> anything is wrong | CRC the calibration blob"

A CRC does not catch this. The blob is intact; it is stale.

**Why it matters, in cents.** A quarter-turn of a 25-turn ±5 % trimmer is 0.2 %
of gain = **2.4 cents/octave = 12 cents at five octaves**, applied on top of a
table that is still correcting for the old setting. This is a slow-burn error: it
appears after routine maintenance, months after calibration, and presents as
"tracking has drifted."

**Proposal.**
- Store a **trim epoch** with the calibration blob — a monotonic counter bumped
  by hand (or a menu item) whenever a trimmer is touched — and refuse to apply
  the multi-point table if the epoch does not match the one the table was built
  under. Show `UNCALIBRATED` on the display, exactly as the ROADMAP already
  specifies for a failed CRC.
- Write the calibration order into the E9 milestone as a procedure, not an
  outcome: *trim gain → trim offset (or set firmware offset) → build the
  multi-point table → lock the screws → bump the epoch.* E9's "done when" is
  currently a result, not a repeatable method.
- State the authority split in one line in ADR 0006: **hardware owns coarse gain;
  firmware owns offset, fine gain and curvature.**

**Confidence: high** that the ambiguity exists in the documents; **medium** on
how often it would bite in practice on a one-off instrument.

**Falsified by:** nothing measurable — this is a process finding. It is refuted
if the author's intent is that the table is always rebuilt after any trim, in
which case the fix is one sentence in ADR 0006 rather than a firmware feature.

---

## 5. An open trimmer wiper drives pitch to the positive rail; the BOM does not tie the unused terminal

**Severity: MINOR**

**Where.** `bom.csv`: `TRIM-PITCH,module,"multiturn cermet trimmer, 5-10% of
ratio",,Pitch scale and offset trimmers,THROUGH-HOLE,2`. No connection note.
Nothing in ADR 0006 either.

**Why.** A cermet wiper is a mechanical contact. Used as a two-terminal rheostat
in the feedback leg, an intermittent or open wiper is an infinite feedback
resistance: the stage's gain goes to infinity and the output slams to
**+11.9 V** (OPA2197 RRIO on the post-diode +11.65 V rail). At the jack, through
1 kΩ, that is a VCO pinned at the top of its range — roughly **+58 semitones**
above the top of the intended span, and audible as a shriek the instant it
happens, then intermittently.

No damage results (a Eurorack 1 V/oct input is a resistor into a summing node and
tolerates the rails), but it is a failure that presents as an intermittent glitch
rather than as a broken part, which is the expensive kind.

**Proposal.** Two PCB nets, zero cost:
- **Tie each trimmer's unused end terminal to its wiper.** An open wiper then
  degrades to the fixed end-to-end resistance rather than to an open circuit. The
  failure becomes a bounded gain error (≤5 %, ≤60 cents/octave) instead of a rail
  slam, and it is the standard way to wire a trimmer as a rheostat.
- Orient the trimmer so that **clockwise = sharp**, and silkscreen it. A
  screwdriver adjustment whose direction is not obvious gets made twice.

**Confidence: very high** on the mechanism (it is textbook); **medium** on
whether the author already intends the standard wiring and simply has not written
it down — it is not in the BOM, and the BOM is otherwise extremely detailed about
exactly this class of thing (`R-PD-BREATH` specifies "DIFFERENTIAL across
BREATH-AGND not one leg", `D-JACK-CLAMP` specifies "SILICON not Schottky").

**Falsified by:** the schematic, once it exists. Nothing to measure.

---

## 6. The pitch DAC word has no readback and no integrity check, and MISO was deleted from the umbilical

**Severity: MINOR**

**Where.** ADR 0004 removes the return path:

> "MISO goes, and with it the planned module-ID line. No loss worth engineering
> around"

and the frame watchdog only detects *absence* of traffic:

> "**Assert `CLR` at the module when no valid frame has arrived for N
> milliseconds.**"

**Why.** SPI runs ~0.6 MHz over 2 m of Cat5e with 220 Ω of source termination on
MOSI only. A single corrupted bit in a pitch word lands as a wrong voltage held
until the next 4 kHz pass — **250 µs**, through a 15.9 kHz filter, i.e. a
full-amplitude 250 µs pitch blip. An MSB error is 2.5 V at the DAC = 5 V at the
jack = five octaves. That is a click or a chirp, not a subtle error, and the
self-repeating 4 kHz loop means it heals itself and leaves no trace.

Worse: the DAC8568's 32-bit word is command-plus-data with no CRC. A corrupted
bit in the *command* field can write the control register — the same register
that holds the internal-reference enable that ADR 0006 already flags as a
bring-up trap. A stray write there changes the reference mode and detunes every
channel at once, permanently, until reboot. The watchdog does not see it because
frames are still arriving.

The ROADMAP's integrity instrumentation is on the wrong bus:

> "**Key-chain error counter over an hour, LEDs and WiFi active** | E4 | The
> marker pattern's whole purpose."

The key chain is inside the instrument, a few centimetres long. The DAC path is
the 2 m cable, and it has no equivalent.

**Proposal.** Cheap, in firmware and one resistor's worth of thought:
- **Rewrite the DAC's control register every N passes** (say once per 100 ms)
  from the loop, so a corrupted control write self-heals on the same timescale as
  a corrupted data write.
- **Periodically read back one pitch word.** This needs MISO, which is deleted —
  so instead, at E11, run a soak: drive a known static pitch code for an hour with
  LEDs, display and WiFi active and a frequency counter on the VCO. Count events.
  That is the DAC-path equivalent of E4's error counter and it is missing from the
  measurement list.
- If E11 shows errors, the ADR already names the fallback (74AHCT14 Schmitt
  buffer at the module end) — this finding is only asking that the measurement
  exist so the fallback is triggered by data.

**Confidence: medium.** The mechanism is certain; the *rate* at 0.6 MHz over
shielded twisted pair with the power pair acting as a guard (a genuinely good
pin-mapping decision, see §7) may well be zero errors per week, in which case
this costs nothing to have checked and nothing to fix.

**Falsified by:** the E11 soak above. Zero counted events in an hour with the
LEDs animating and WiFi transmitting, and this drops to a NIT.

---

## 7. Where the design is correct

These are checked, not assumed, and several are better than the documents claim.

**The 0.25–4.75 V window makes the gain exactly 2.000, which the ADR does not
notice.** ADR 0006 introduces the window to dodge DAC saturation and says the
trimmer "absorbs the resulting gain change". In fact `4.5 V → 9 V` is gain
**2.000 exactly**, and the offset is **−2.500 V exactly**. That kills the
original objection outright:

> "**The gain ratio was not buildable.** The 1.8× gain needed for a 0–5 V DAC span
> to become −2…+7 V is 9/5, which cannot be made from a matched resistor quad."

A gain of 2 *can* be made from a matched quad — `Rf = Rg` in a non-inverting
stage, or two legs in series against one — so the LT5400 sets the nominal ratio
to 0.01 % and the trimmer only adjusts. This should be written down explicitly,
because it is load-bearing for Finding 3 and because it is currently arrived at
by accident. **It also means several cents figures in ADR 0006 are stale**: the
INL numbers ("±4 LSB typical is 0.66 cents, ±12 LSB is 2.0 cents") were computed
at 1.8×; at 2.0× they are **0.73 and 2.20 cents**. Small, but the document should
not contain two different gains.

**The LM317 decision is right, and the window alone would not have saved it.**
With the internal 2.5 V reference in ×2 mode, full scale is 5.000 V regardless of
AVDD — it merely *requires* AVDD above it plus buffer headroom. At the +5 V bus
rail sagging to 4.75 V, the top of the window (4.75 V) sits exactly at the rail.
Both fixes — the local 5.25 V regulator *and* the reduced window — are needed,
and the ADR has both. (Minor note: ADR 0004 says "the DAC's full-scale output *is*
its supply", which is not quite the mechanism — it is a headroom limit, not a
ratiometric one. The conclusion is unaffected.) At AVDD = 5.25 V the real
headroom at the top of the window is 500 mV, not the 250 mV the ADR claims, so
the design is more conservative than it thinks.

**The LM317's minimum-load requirement is met without thinking about it.** The
240 Ω/768 Ω setting divider draws 1.25 V/240 Ω = **5.2 mA**, which is above the
LM317L's minimum load on its own, before the DAC's own AVDD current. (The BOM's
"~5 mA load, 135 mW" is internally inconsistent — 6.75 V × 7 mA is ~47 mW, not
135 — but in the safe direction.)

**The out-of-loop RC is the right filter and the arithmetic works.** 1 kΩ × 10 nF
= **15.9 kHz**, τ = 10.0 µs, matching the latency budget's "~10 µs" and ADR
0006's "10–20 kHz". A one-octave leap settles to within **1 cent in 71 µs** —
inaudible against a 5–15 ms tongued attack, and 70× inside the 5 ms target. Because
the 1 kΩ is outside the feedback loop, no patch-cable capacitance can destabilise
it; the ROADMAP's E9 stability check will confirm this and cannot fail. The
zero-order-hold images that force the mod channels to a 2 kHz corner do not apply
to pitch, because pitch is static between notes — the ADR reaches the right
answer for the right reason. Dielectric absorption in an X7R filter cap is also a
non-issue here: the cap is a shunt driven from a 1 kΩ source, so soakage current
of order nA produces microvolts.

*One ambiguity to close:* ADR 0006 says "the filter's corner is set by **its own R**
and C", but `bom.csv` lists only `R-OUT-PROT` (1 kΩ × 6) and no filter resistor.
If a separate filter R exists in series, the output impedance doubles and the
load-divider error doubles with it — 2 kΩ into 100 kΩ is **−23.5 cents/octave**,
not −11.9. State that the 1 kΩ protection resistor *is* the filter resistor and
the cap hangs on the jack node.

**The BAV99-over-BAT54S call is right and I re-derived it.** 2 µA × 1 kΩ = 2 mV =
**2.40 cents** — the ADR's figure exactly. BAV99 at ~1 nA is 0.0012 cents. This
is the single most cost-effective decision in the chain.

**The op-amp is not, and never was, a term.** OPA197 at ±2.5 µV/°C max, noise gain
2, over 10 K: 50 µV = **0.060 cents**. Noise: 5.5 nV/√Hz × 2 × √(15.9 kHz × 1.57)
= 1.74 µV RMS = **0.0021 cents**. Output swing −2…+7 V against ±11.65 V post-diode
— 4.65 V of margin. The `R-OPAMP-IN` 1 kΩ costs nothing because the OPA197 is a
CMOS-input part (bias current × 1 kΩ is nanovolts), exactly as claimed.

Honest correction to one sentence: "Still use a low-drift op-amp (OPA2197-class,
not TL072) — offset drift on pitch is drift in tuning." True, but not
load-bearing. A TL072 at ~10 µV/°C would contribute ~0.24 cents over 10 K, still
below every other term. The OPA2197 is justified by part-number uniformity and
by output swing on the mod channels, not by pitch drift. Keep it; do not believe
it is buying accuracy.

**The conductor pin mapping is a genuinely good piece of work.** Putting the DC
power pair between the analog pair and both digital pairs, with SCLK at the far
end, is correct for the untwisted ~13 mm inside an RJ45 plug, and it is the
reason Finding 6 is a MINOR rather than a MAJOR.

**"Anchor inside the musically used range" is right,** and understated. A 9 V span
is nine octaves; no VCO tracks over more than about five. The designed extremes
are unreachable in practice, which is another reason the window's 10 % span cost
is free — it trades resolution nobody can use (0.183 cents/LSB either way) for
±600 cents of firmware offset authority (Finding 2).

**Deleting the "design the gain 5 % high" kludge is correct.** A trimmer plus an
affine firmware fit goes both ways; a one-directional bias was always a hack.

---

## 8. Error budget, in cents

Conditions: 10 K ambient swing after calibration; musically used range taken as
**0 V to +5 V at the jack** (five octaves — the layout has four left-thumb
register keys, so five is a fair working span); errors quoted at the top of that
range, which is the worst point for gain-character terms. Gain terms pivot at
`Vout = 0 V` when the offset is ratiometric (Finding 1), at `−2.5 V` when it is
not.

### As specified today

| Term | Character | Cents @ 5 oct |
|---|---|---|
| **Load change, firmware scale-factor "fix" (100 k → 50 k)** | transposition | **29.4** |
| **Load change (100 k → 33 k)** | transposition | **59.1** |
| **Offset ref from +12 V: LED PWM ripple, ~90 mV p-p @ 2 kHz** | FM, p-p | **22.5** |
| **Offset ref from +12 V: 50 mV rail load step** | transposition | **12.5** |
| Offset ref from +12 V: rail thermal, 100 ppm/°C × 10 K | transposition | 3.0 |
| Gain trimmer setting stability (±5 %, 1 % of R) | 0.60 c/oct | 3.0 |
| Gain trimmer tempco, ±5 % on an LT5400 leg (4.6 ppm/°C) | 0.055 c/oct | 0.28 |
| *(ADR's own estimate for the same, 22 ppm/°C)* | *0.26 c/oct* | *1.32* |
| DAC INL ±4 LSB max, before the multi-point table | curvature | 0.73 |
| DAC internal reference, 5 ppm/°C max × 10 K | 0.06 c/oct + 0.15 | 0.45 |
| LT5400 matching, 1 ppm/°C max × 10 K | 0.012 c/oct | 0.06 |
| Op-amp Vos drift, ±2.5 µV/°C max × NG 2 | transposition | 0.06 |
| DAC quantisation, ±0.5 LSB | random | 0.09 |
| Op-amp + DAC noise | random | 0.002 |
| BAV99 leakage ~1 nA × 1 kΩ | transposition | 0.001 |
| **VCO's own drift, for reference (0.35 cents/K × 10 K)** | | **3.5** |

### After the three fixes (offset from VREFOUT, affine firmware calibration, ±1.5 % trim)

| Term | Cents @ 5 oct |
|---|---|
| Gain trimmer setting stability (±1.5 %) | 0.90 |
| DAC internal reference (now ratiometric → pure gain about 0 V) | 0.30 |
| DAC INL residual after a 12-point table | ~0.2 |
| Gain trimmer tempco (1.4 ppm/°C) | 0.08 |
| LT5400 matching | 0.06 |
| Op-amp Vos drift | 0.06 |
| Quantisation | 0.09 |
| Everything else | <0.01 |
| **RSS total** | **≈ 1.0 cent** |

### What dominates, and what is audible

**As specified, the budget is dominated entirely by offset-character terms — and
every one of them is invisible to the calibration model the ADR describes.** The
load-change residual (29–59 cents) and the offset reference's rail exposure
(3 cents thermal, 12.5 cents per rail step, ~22 cents p-p of LED-synchronous FM)
are between one and two orders of magnitude larger than everything the ADR spent
effort on.

The terms the design worked hardest for — the matched network, the internal
reference, the op-amp grade, the trimmer tempco — **sum by RSS to about 0.8
cents over 10 K**, comfortably under the 3.5 cents the VCO does by itself. ADR
0006's own conclusion, that "the precision-network argument was over-engineering
relative to the load it feeds", is correct and if anything understated.

So the one-line verdict: **the design has optimised the terms that do not matter
and left the two that do unspecified.** Offset source, and offset authority.

On audibility: ~5 cents is roughly the just-noticeable difference for successive
steady tones; beating against a second oscillator exposes 1–2 cents. The fixed
budget at ~1 cent is inaudible under any condition. 29 cents is a quarter of a
semitone — audible to anyone, on every note. 22 cents p-p of 2 kHz FM is not a
tuning error at all, it is a timbral buzz that will be blamed on the VCO.

### The unrecoverability table the brief asked for

| Error | Trimmer can fix? | Firmware can fix? | Notes |
|---|---|---|---|
| Stage gain tolerance | yes | yes (`a`) | fully recoverable either way |
| Offset initial value | yes | **yes, ±600 cents** — via the reserved 0.25 V code window, *if* the model is affine | today's model is scale-only, so **no** |
| 1 kΩ load divider, fixed load | yes (both trimmers together, load connected) | yes, if affine | ADR's "gain trimmer has full authority" is wrong; it takes both |
| 1 kΩ load divider, **changed** load | yes, with a screwdriver, per patch | yes, if affine; **no** as specified | this is the 29–59 cent term |
| DAC INL | no | yes (multi-point table) | correctly assigned |
| Gain drift with temperature | no (live) | no (live) | 0.08–0.28 cents — below the VCO, fine |
| **Offset drift with temperature or rail motion** | **no (live)** | **no (live)** | **the only genuinely unrecoverable term. Fix it at the source.** |

That last row is the whole argument for Finding 1. Every other error in this
chain has an owner. Offset drift has none — so it has to be designed out of the
hardware rather than corrected, and the cost of doing so is zero parts.

---

## 9. Summary of proposals, cheapest first

1. **Name the pitch offset reference in ADR 0006, and make it the DAC8568's own
   VREFIN/VREFOUT pin** (or a REF5025 if the subsonic power-on park is worth
   keeping). Never a rail divider. *Zero parts.* — Finding 1
2. **Make the firmware calibration an affine `(gain, offset)` pair, and the
   multi-point table absolute volts per anchor.** *Firmware only.* — Finding 2
3. **Shrink the gain trim to ±1.5 % and put it on an LT5400 leg**, having handed
   the load correction to firmware. *Cheaper part.* — Finding 3
4. **Tie each trimmer's unused terminal to its wiper; silkscreen the sharp
   direction.** *Two nets.* — Finding 5
5. **Add a trim epoch to the calibration blob and a written E9 procedure.** —
   Finding 4
6. **Add two measurements to the roadmap**: (a) E6 rail ripple *with the LED
   strips animating*, scoped at the module's protected +12 V node; (b) an E11
   one-hour static-pitch soak with a frequency counter, LEDs and WiFi active, as
   the DAC-path equivalent of E4's key-chain error counter. — Findings 1, 6
7. **Editorial:** state the gain is exactly 2.000 and the offset exactly
   −2.500 V; restate the INL cents figures at 2.0× (0.73 / 2.20, not 0.66 / 2.0);
   confirm the 1 kΩ protection resistor *is* the filter resistor; resolve whether
   "5 % trim range" means ±2.5 % or ±5 %. — §7
