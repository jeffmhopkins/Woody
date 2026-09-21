# 0006 — CV channel allocation and calibration

**Status:** Accepted

## Decision

**Six channels from an octal DAC, two dedicated and four assignable.**

| Output | Source | Range | Panel control | Precision |
|---|---|---|---|---|
| **Pitch** | DAC ch 1 | −2 to +7V, 1V/oct | none | Calibrated |
| **Breath** | **analog, differential over the umbilical** | 0–10V, **offsettable ±5 V** | GAIN 0.5–4×, OFFSET ±5 V | Trimmed |
| **Mod 1–4** | DAC ch 2–5 | **−10…+10V** | none — configured on the instrument | Trimmed |
| *(internal)* | DAC ch 6 | — | — | **Spare** — was the breath ambient-zero |
| *(internal)* | DAC ch 7 | — | — | Shared **3.3333 V** offset for mod 1–4 |

Six jacks on the panel as before, but only five of them come from the DAC.
**Breath never enters the digital path on its way out** — it is the one channel
where output steps reach the ear, so it stays analog end to end (ADR 0003).
One further DAC channel drives an offset rather than a jack: the shared
reference point the mod channels subtract from, **3.3333 V** now that they use
the two-resistor form (`mod-channels.md`). **Six of eight channels used,
two spare.**

**Channel 6 was freed deliberately.** It drove a firmware ambient-zero into the
breath in-amp's `REF` pin, and firmware reads breath *before* the umbilical
while that injection happens *after* it — so it was correcting a signal it could
not measure. The analog path's zero authority is now the panel offset knob,
which can see the jack; firmware's zero authority is its own ADC copy, which it
can also see. One authority per representation (ADR 0003). Nothing claims the
freed channel; leaving it unclaimed is the point.

Use an **octal** 16-bit DAC (DAC8568 or AD5676) and populate six. Eight-channel
parts cost barely more than quads and occupy the same board area; there is no
reason to design into a hard limit of four.

Mod channels are generic rather than fixed-function — a gate can be assigned to
one if wanted, without the design being *limited* to a gate. Per-channel source,
scale, offset, curve and slew are set on the instrument's display.

## Why dedicating pitch and breath is better than full genericity

Fully assignable channels were considered and rejected, because output filtering
cannot be generic:

- **Pitch must not be filtered slowly.** A soft filter on pitch CV is an audible
  glide on every note change. Corner it around 10–20 kHz — enough to kill DAC
  step glitches, fast enough that notes land instantly. Portamento belongs in
  firmware where it can be switched off.
- **Breath wants a gentler filter**, ~2 kHz. It is an inherently slow signal and
  the steps should be smoothed in hardware.
- **Mod 1–4** get a uniform **~2 kHz** filter with smoothing applied in
  software, per-channel, according to what each is assigned to. An earlier
  revision called this a "uniform fast filter"; a fast corner leaves the
  zero-order-hold image audible, and their sources top out around 400 Hz so a
  2 kHz corner costs nothing in signal. See the update-rate section below.

Dedicating the first two channels means they get optimal analog treatment rather
than a compromise, and only the generic four need the uniform-filter-plus-
software approach.

Stepping artefacts on the generic channels are not a concern: **step size is
bounded by slew rate, not full scale.** A signal moving over ~10 ms sampled at
4 kHz changes by a fortieth of its excursion per sample, and one LSB at 16-bit
over 10V is ~150 µV. The only large step is a deliberate note change, which
should be fast anyway.

## Mod channels are bipolar, −10 to +10 V

An earlier revision made the mod stage unipolar 0–10 V. That would have been
permanent in hardware: no ±5 V LFO, no negative excursion, no through-zero
modulation, ever, with firmware unable to recover any of it. **The stage is
bipolar instead, spanning −10 to +10 V.**

The point is not to *output* ±10 V routinely — it is to be **able** to, with
firmware selecting the actual range per channel from the instrument's display:
0–5 V, 0–8 V, 0–10 V, ±5 V, ±2.5 V. Most patches will use 0–8 V or ±5 V, which
are the de-facto Eurorack conventions; the extra span is headroom, not a default.

### The topology falls out neatly

> **Drawn now**, in `hardware/module/`: the
> [pitch stage](../../hardware/module/pitch-stage/pitch-stage.md) and the
> [mod channels](../../hardware/module/mod-channels/mod-channels.md). Where those pages
> disagree with the prose here, they win — that is the rule the breath page
> established and the reason it exists.
>
> Pitch is **two matched resistors** in a non-inverting stage with the reference
> at the bottom of the feedback divider — not the four-resistor difference amp
> this ADR's prose implies. `gain = 1 + k`, `intercept = k·V_ref`, and the free
> parameter is `V_ref`, not the ratio. **The mod channels can take the same
> form** at `k = 3` with the offset channel writing 3.3333 V. **They do — it is
> adopted and drawn** (`mod-channels.md`, "Adopted, and it is drawn above";
> `R-MODGAIN` is eight 10k/30k discretes in `bom.csv`, not sixteen). This
> sentence read "whether they do is open" until 2026-09-21, after the question
> had been settled.
>
> *(An earlier version of this note called `A = 1 + B` a boundary that pitch
> luckily landed on. It is the topology's defining identity, true for every
> ratio — Winterbloom's Sol ships the same circuit with its reference divided
> to 1.190 V. Recorded because the wrong version made the mod channels look
> like they needed four resistors, which they do not.)*

```
Vout = 4 × Vdac − 3 × V_ref          V_ref = 3.3333 V, from DAC channel 7

  Vdac 0.00 V  →  −10 V
  Vdac 2.50 V  →    0 V
  Vdac 5.00 V  →  +10 V
```

> **This block read `Vout = 4 × (Vdac − 2.5 V)` until 2026-09-21.** The three
> endpoints are unchanged — that is why it survived so long — but the mechanism
> is not. `4 × (Vdac − V_off)` is the four-resistor difference amp, which
> `mod-channels.md` replaced with the two-resistor non-inverting form at
> `k = 3`. Against the built 10k/30k network the offset channel must carry
> **3.3333 V**; firmware that writes the old 2.5 V there gets a
> **−7.5 … +12.5 V window and clips positive** (`firmware/README.md`).

Three things make this cheap rather than awkward:

- **Superseded.** This bullet used to claim a gain of 4 from an LT5400 ratio —
  **superseded 2026-09-21.** The mod channels are built from `R-MODGAIN` 10k/30k
  1 % discretes in a two-resistor non-inverting form at **k = 3**, referenced to
  **3.3333 V**. `pitch-stage.md` also shows the LT5400 route is arithmetically
  impossible here — pitch already uses two of its four sections.
- **The 3.3333 V reference point comes from a buffered DAC channel**, not
  directly from the internal reference. (It was 2.5 V while the mod channels
  were a four-resistor difference amp; the two-resistor form needs `3 × V_ref`
  to equal the same 10 V of offset.) Both routes track the same reference — the gain
  is a resistor ratio and does not involve the reference at all — so the drift
  argument is a wash, and the DAC channel wins on the power-on state below. One
  buffered channel serves all four mod channels. (This is now the *only*
  offset driven from a DAC channel; the breath ambient-zero that used to share
  the pattern is deleted.)
- **Headroom is ample.** ±12 V rails less ~0.35 V of Schottky leaves ±11.65 V,
  and an OPA2197 reaches ~±11.45 V — 1.45 V of margin at ±10 V.

### The cost

Resolution goes from 153 µV/LSB on a 10 V span to **305 µV/LSB** on 20 V. That is
0.003 % of full scale, and irrelevant against anything a modulation CV drives.

### Resolved: what the outputs do at power-on

This looked like a conflict. With a fixed offset from a fixed reference, the
mod outputs park at **−10 V** on a zero-scale reset and at **0 V** on a midscale
reset — and the DAC8568's reset state is set by its grade, one chip shared with
pitch, whose preferred reset is the opposite one. A and C reset to zero scale;
B and D reset to midscale.

**Taking the offset from a DAC channel dissolves it**, because the offset term
then resets with everything else. On a zero-scale reset both terms are zero:

```
Vout = 4 × Vdac − 3 × V_ref = 4 × 0 − 3 × 0 = 0 V
```

So specify a **C grade** part — zero-scale reset — and the power-on state is
the best available on every channel at once:

> **This safety is now topology-dependent, and it was not before.** The
> four-resistor difference form gave `4X − 4X = 0` for *any* uniform reset
> state X, so the grade did not matter to it. The two-resistor form gives
> `4X − 3X = X`. With the locked C grade X is 0 V and the result is identical;
> a B or D part would put **+2.5 V on all four mod jacks** where the old
> topology gave 0 V regardless (`mod-channels.md`). The C-grade lock therefore
> now carries this as well as the reference-gain requirement below — it has
> two independent reasons, and this is the newer one.

**Not "A or C", which this line used to say.** The grade letter selects the
**reference gain** as well as the reset state: A/B are gain 1 (2.500 V full
scale) and C/D are gain 2 (5.000 V). An A-grade part halves every output —
pitch becomes −2…+2.25 V, the mods ±5 V, and channel 7 cannot reach its
reference voltage at all. Only C satisfies both requirements. `bom.csv` is
locked to `DAC8568CIPW`.

> **Confirmed 2026-09-21 against SBAS430E**, now held at
> `datasheets/texas-instruments/DAC8568CIPW.pdf`. This paragraph asked for
> that check because no browser in the sandbox could reach `ti.com`; the
> datasheet says what the ADR guessed, verbatim: *"For device grades A and C
> on power-up, all DAC registers are filled with zeros and the output voltages
> of all DAC channels are set to zero scale."* A/B are 2.5 V full scale, C/D
> are 5 V.
>
> **And it carries a requirement the ADR did not know: the C grade is
> specified only for AVDD = 5.0 V to 5.5 V**, where A/B are specified from
> 2.7 V. The LM317 sits at 5.21 V nominal so this passes — but E7 selects the
> divider *on the bench* across a 0.66 V worst-case spread, and a selection
> below 5.00 V puts the part out of spec. **5.00 V is a hard floor on that
> bench step**, which nothing in the roadmap said. `bom.csv` carries it now.
>
> *(A second rider, not binding today: on C/D an external `VREFIN` must stay
> below AVDD/2. The internal reference is used, so this only forecloses a
> future external-reference retrofit above ~2.6 V.)*

| Output | At rack power-on, before firmware writes | Why that is right |
|---|---|---|
| **Pitch** | Bottom of its range, below −2 V | Subsonic. A VCO there is inaudible |
| **Mod 1–4** | **Exactly 0 V** | Both terms of the difference are zero |
| **Breath** | **Wherever the panel OFFSET knob was left, anywhere in ±5 V** | **Not a defined state — see below.** Breath never passes through the DAC, so no reset reaches it |

> **The breath row said "0 V — the receiver's differential pulldown holds it
> there" until 2026-09-21, and both halves were wrong.** `R-PD-BREATH` is
> deleted (ADR 0003 replaced it with the `R-BIAS-INAMP` common-mode return,
> because a purely differential shunt gives the in-amp's inputs no DC path to
> ground at all). And the replacement does not produce 0 V at the jack: the two
> 1 MΩ bias resistors hold the in-amp's *inputs* at module `AGND`, so with the
> instrument absent the in-amp rests at `V_REF` ≈ +0.437 V — the trimmed null
> for a sensor pedestal that is not there — and the gain-and-offset stage then
> puts the jack at the **OFFSET knob's position less 0.2 to 1.7 V**, depending
> on where GAIN is set (`breath-receive-stage.md`,
> `breath-output-stage.md`).
>
> **Five of six outputs have a defined power-on state; breath does not, and
> that is accepted.** The alternative is a defeat switch or a relay on the jack,
> which is a part and a failure mode for a condition — rack powered, instrument
> absent — in which nothing is being played. What it costs is that a patch left
> connected can wake with up to 5 V of standing breath CV. E10 is where that
> gets observed rather than discovered (`ROADMAP.md`).

**Specify the full orderable part number in the BOM**, not "DAC8568". The grade
letter is the whole decision and it is invisible in the generic name.

A second trap in the same part: **the internal reference is disabled by default**
and needs an explicit enable write at boot. This is a known DAC8568 bring-up
surprise — a board that looks dead at E7 with every channel reading 0 V is
usually this, not a soldering fault. It also means the outputs sit at 0 V from
rack power-on until firmware enables the reference, which happens to reinforce
the table above.

**Two offset authorities in series would be a split-brain failure**, so they are
kept apart deliberately: the **trimmer** is the offset authority for pitch, the
**DAC channel** is the offset authority for the mod channels, and neither
channel group has both.

## Channels do not share an update rate

Breath needs a high output rate to keep staircase ripple out of the audio band
(ADR 0003). The others do not, and giving them one would waste the umbilical's
entire bandwidth budget.

| Channel | Rate | Why |
|---|---|---|
| Pitch | **4 kHz**, plus **immediate update on note change** | Static between notes; what matters is latency at the transition, not rate |
| Mod 1–4 | **4 kHz** | See below — 2 kHz leaves an audible image |
| Breath zero offset | continuous, slow | See the auto-zero rule below |
| Mod offset (ch 7) | **refreshed every pass, like the other five** | The shared **3.3333 V** reference. This row said "written once at boot" and "2.5 V" until 2026-09-21; `firmware/README.md` spells out that writing 2.5 V into ch 7 against the current 10k/30k network gives a -7.5...+12.5 V window that clips positive |

Pitch is the subtle one: it needs no *rate*, but it must not wait for its turn
in a round-robin. Push it the instant the note resolves.

**The table used to say 2 kHz and it was wrong twice over.** It contradicted
this ADR's own bounding argument, which cites 4 kHz, and it contradicted the
loop budget, which already assumes six DAC channels serviced every 250 µs pass.
Nothing is saved by updating at half the rate the loop already pays for.

It also conflated amplitude quantisation with time quantisation. **Software
smoothing band-limits the content; it cannot remove the images the DAC creates
after it.** At a 2 kHz update a 400 Hz IMU signal puts its first zero-order-hold
image at 1.6 kHz, only **12.6 dB** below the modulation — and a 15 kHz
reconstruction filter attenuates that by 0.07 dB, which is nothing.

At 4 kHz the image moves to 3.6 kHz and drops to −19.2 dB. Better, and still not
enough on its own, so:

**Give the mod channels a lower reconstruction corner than pitch — around
2 kHz.** Their sources top out near 400 Hz, so the corner costs nothing in
signal and puts real attenuation on the image. Pitch keeps its fast corner
because a slow one is an audible glide on every note; these are different
channels with different needs, which is the same argument that made them
dedicated rather than generic in the first place.

### Ambient zero is continuous, not startup-only — on the digital copy

The breath sensor is a gauge part with a temperature-dependent offset, sitting
inside a sealed oak-and-acrylic body — both insulators — warmed by breath, by
the LEDs and by its own electronics. The interior rises on the order of 10–20 K
over the first 10–20 minutes of a session, and the aluminium plate is the only
real heat path out of it, partly covered by the player's hands.

**A zero captured once at startup is wrong by the time the first piece ends** —
for the *digital* copy, which is what this section is about. The analog CV at
the jack is a separate representation with a separate authority (the panel
offset knob), and its drift is ~23 mV in 10 V over a full warm-up: a quarter
turn, once, if it bothers you at all. See ADR 0003.

The mechanism is a subtraction in software, which needs no converter because the
digital copy is already a number. **Seed it from an ADC capture at power-on**,
then **decay it toward the current reading whenever breath has been
sub-threshold for about 2 seconds** — slow enough that it cannot chase a held
note, fast enough to track a warming body.

**Sub-threshold is not enough of a condition, and an auto-zero that never
reports is a fault-concealment machine.** Two reviewers found the same thing
from different directions, and both are right:

- The rule as written eats a sustained pianissimo, and it re-zeros during the
  catch-breath of a circular-breathing passage — both of which are quiet on
  purpose and are the player doing something.
- Continuous auto-zero cannot tell thermal drift from **a partially blocked
  PTFE restrictor, a cavity that has started sealing, or a shifted sensor
  offset** — which are exactly the three failures the DP reference-port
  decision depends on being able to see (ADR 0003). It absorbs them silently
  and presents them later as an instrument that has gone vague.

**Gate the decay on "sub-threshold *and* quiet".** Quiet means the signal's
standard deviation is below about 2× what it measured at commissioning — the
same stillness-gated estimator ADR 0007 already uses for IMU bias, applied to a
different sensor. A held pianissimo has breath noise in it; an instrument on a
stand does not.

**And log the accumulated correction.** The zero is allowed to move; it is not
allowed to move silently. A running total, visible on the display and in the
web app, turns all three concealed failures into a number that walks — which is
the diagnostic the design otherwise does not have.

It is also now an *honest* diagnostic, which it was not before. While the same
correction was being driven into the analog path, a walking number meant either
a real fault or an accumulating error between two representations nobody could
compare. Applied only to the copy firmware actually measures, it can only mean
the first.

A 96 kHz breath channel was specified before the output went analog, which
implied sub-10 µs DAC settling and ~6.8 MHz on the umbilical. **Both
requirements are withdrawn** — nothing left on the DAC needs that rate
(ADR 0003).

## Breath knobs are analog, in the signal path

With breath locked to channel 2 there is no genericity conflict, so the knobs
sit directly in the analog path: zero latency, tactile, no firmware involvement,
and **no return path needed over the umbilical**.

**Order is gain first, then offset.** Scale how much of the 0–10V span the
breath covers, then position where the floor sits. The reverse ordering makes
the two controls fight each other.

Firmware still shapes the response curve upstream of the DAC. The knobs fit the
*range* to the patch; the firmware shapes the *feel*.

## Calibration effort concentrates on one channel

**Only channel 1 needs to be musically accurate.** 1V/oct tracking, a per-unit
calibration table in NVS, and a two-point fit verified against a real VCO — not
just a meter, because a meter will not catch a scaling error that sounds wrong.

Channels 2–6 need only to be linear and repeatable. Nobody's ear cares whether a
modulation CV is 2% off.

So the precision parts concentrate on channel 1. But **where** that budget goes
is worth checking rather than assuming, and the arithmetic is not what it looks
like.

Over a 10 °C swing on a 9 V span, against one semitone at 83.3 mV:

| Source | Drift | Cents |
|---|---|---|
| DAC internal reference, 5 ppm/°C | 0.45 mV | 0.54 |
| **Discrete resistors, 25 ppm/°C each, drifting oppositely** | **4.50 mV** | **5.40** |
| Matched network, 1 ppm/°C tracking | 0.09 mV | 0.11 |

**Resistor tracking dominates reference drift by roughly ten to one.** The gain
of a scaling stage is a resistor *ratio*, so what matters is not each resistor's
absolute tempco but how well the two track each other — and two discrete parts
do not track at all.

Consequences:

- **Use a matched resistor network for the pitch scaling stage** (LT5400 class,
  MSOP-8), not discrete 0.1% parts. This is the single highest-value precision
  component in the design. **The ratio is 1:1** — see
  [the pitch stage schematic](../../hardware/module/pitch-stage/pitch-stage.md), which is
  where the topology finally got drawn and turned out to be a non-inverting amp
  with the reference at the bottom of the feedback divider, not the difference
  amp everyone had been assuming. Two matched resistors, not four, and the
  easiest ratio there is to match.
- **The DAC's internal reference is sufficient.** At 0.54 cents over 10 °C it is
  an order of magnitude inside the resistors, so a separate precision reference
  buys nothing measurable. One fewer part.
- Still use a low-drift op-amp (OPA2197-class, not TL072) — offset drift on
  pitch is drift in tuning.

Channels 2–6 run on ordinary 1% discretes; nobody's ear cares whether a
modulation CV moves a few cents' equivalent with temperature.

This is materially less expensive and less work than treating all six as
precision outputs.

## Pitch gets trim pots. Calibration is hardware first, firmware second.

An earlier revision of this ADR specified **no trimmers anywhere**, on the
grounds that a stored firmware fit is better than a screwdriver adjustment. A
design review found two independent reasons that does not work, and the decision
is reversed for the pitch channel.

### Why firmware alone was not enough

**Firmware calibration has no offset authority.** A two-point fit is
`y = a·x + b`. Scaling the DAC code implements `a`. **Nothing implemented `b`.**
If the hardware offset came out at −1.90 V instead of −2.00 V, firmware could
not reach −2 V at all — and the ADR prescribed a deliberate +5 % *gain* bias
while saying nothing about the offset, whose safe bias direction is the opposite
one.

**The gain ratio was not buildable.** The 1.8× gain needed for a 0–5 V DAC span
to become −2…+7 V is 9/5, which cannot be made from a matched resistor quad. Any
external resistor added to reach it puts its absolute tempco inside the ratio —
exactly the failure the matched network was bought to prevent.

A trimmer solves both directly.

**This paragraph used to end "which is also why every commercial 1 V/oct module
has scale and offset trimmers", and that is false.** Two independent surveys of
published designs found **zero trimmers** on DAC-derived CV outputs — Yarns,
Marbles, Stages, Ornament & Crime, Winterbloom Sol, Befaco MIDI Thing, MTM
Workshop Computer and Westlicht PER|FORMER all calibrate in firmware, typically
with an 11-point-per-channel table at one point per octave. Trimmers are
universal on **analog** V/oct *inputs* — expo converters — which is a different
circuit solving a different problem. Mutable reaches 1–2 cents with plain 1 %
resistors and no screwdriver anywhere.

Both of the original reasons for Woody's trimmers have since been withdrawn by
this ADR itself: "firmware has no offset authority" was retracted when the
per-load affine model went in, and "the ratio is not buildable" was retracted
when the pitch stage turned out to be an exact 1:1. **The trimmers stay**, and the objection is answered by shrinking them rather
than by deleting them. This ADR's own sentence — "any external resistor added
to reach it puts its absolute tempco inside the ratio, exactly the failure the
matched network was bought to prevent" — was a fair charge against a 1 kΩ
trimmer contributing 5 % of the ratio. At **200 Ω** it contributes 2 %, which
is ~2 ppm/°C against the LT5400's own drift, and it is no longer the largest
term in the budget.

Two percent is enough because jack-side feedback removed the load divider,
which was what the ±5 % range existed to absorb.

The offset trimmer also moved **ahead of the reference buffer**, where it scales
`V_ref` and therefore the intercept alone. In its first position it injected
into the inverting node and was never a pure offset at all — in a non-inverting
stage that node sits at `Vdac`, not at a virtual ground, so it carried about
1 % of gain with it and its span was half what was claimed.

### What it costs, honestly

The trimmer is in the gain ratio, so its tempco is too. Against a fixed 0.1 %
10 ppm/°C resistor:

| Trim range | Net ratio tempco | Drift over 10 °C |
|---|---|---|
| 5 % | 22 ppm/°C | **2.4 cents** |
| 10 % | 34 ppm/°C | 3.7 cents |
| 20 % | 58 ppm/°C | 6.3 cents |

That is worse than a matched network (0.11 cents) and comparable to discrete
resistors (5.4 cents). **It is also comparable to what the VCO being driven does
on its own** — a well-compensated analog VCO drifts around 0.35 cents/K, so
3.5 cents over the same 10 °C. The trimmer is therefore not the limiting term in
the system, and the precision-network argument was over-engineering relative to
the load it feeds.

**Keep the trim range small — 5 to 10 % — around a fixed precision resistor.**
The LT5400 can still set the nominal ratio exactly, with the trimmer providing
only the adjustment; that keeps most of the matched-network benefit and adds
trimmability.

### The division of labour

- **Trimmers set gain and offset.** Two per pitch channel, multiturn cermet.
  **The offset trimmer divides down the DAC's buffered `VREFOUT`, not a supply
  rail** — see below. This ADR named the trimmer "the offset authority for
  pitch" and never said what it divides, and three reviewers independently
  found that the only source in the committed topology was a bare divider off
  ±12 V.
- **Firmware handles what trimmers cannot:** DAC integral nonlinearity, which is
  curvature no gain-and-offset adjustment can remove (±4 LSB typical is
  0.66 cents, ±12 LSB is 2.0 cents). Use a **multi-point** table, roughly one
  point per octave — Mutable's Yarns uses **eleven** (`kNumOctaves = 11`), as do
  Ornament & Crime and the PER|FORMER. An earlier revision of this line said
  twelve.

These are complementary, not alternatives. Hardware gets the line straight;
firmware straightens the bow in it.

### Consequences elsewhere

- **The "design the gain 5 % high" kludge is deleted.** It existed only because
  firmware could scale in one direction. A trimmer goes both ways.
> **What the reserve is, because it is easy to misread.** The 0.25–4.75 V
> window leaves 0.5 V at each end, and that is **calibration headroom** — room
> for firmware's per-load affine correction to shift codes without running out
> at the extremes of the *used musical range*. It is **not** a limit on
> transposition. The instrument's fingering spans roughly 2.5–3 octaves inside
> a 9 V output range, so there are six-odd octaves of unused span and firmware
> can move the whole mapping up or down freely. This was briefly misread as
> "firmware cannot transpose by a full octave", which is wrong, and it nearly
> bought an analog octave switch the module does not need.

- **Use the DAC's 0.25–4.75 V window rather than its full 0–5 V span.** That
  leaves 250 mV of headroom at both rails — the DAC8568 at AVDD = 5 V cannot
  reliably swing to its own supply — and the trimmer absorbs the resulting gain
  change. This achieves the same benefit as respeccing the output range, without
  needing an exactly-constructible resistor ratio.
- **Mod channels stay trimmer-free.** They need to be linear and repeatable, not
  musically accurate; firmware scaling is sufficient there and nobody's ear
  cares about a few cents' equivalent on a modulation CV.

## The pitch output keeps its 1 kΩ series resistor

Every CV output in this design gets a 1 kΩ series resistor — standard Eurorack
practice, and what makes the module survive a short to ground or someone
patching output to output. A design review argued that on the pitch jack
specifically the resistor should be removed or shrunk, because it forms a
divider against whatever is plugged in:

| Load | Divider | Tracking error |
|---|---|---|
| 100 kΩ (one typical VCO) | 0.9901 | **−11.9 cents/octave** |
| 50 kΩ (two VCOs, passive mult) | 0.9804 | **−23.5 cents/octave** |

Five octaves up, that is 59.4 cents and 117.6 cents respectively.

**The resistor stays at 1 kΩ, and calibration absorbs it.** Two reasons.

**The trimmer has full authority over it, and firmware needs two numbers to
match — not one.** The sentence that used to stand here said the divider "is a
pure gain error", and that is false. The pitch stage generates its own offset
*upstream* of the 1 kΩ, so the divider scales the offset too:

```
Vout = k · (2·Vdac − 2.5)        k = R_load / (R_load + 1 k)
```

Correcting only the slope — scaling the DAC code by `1/k` — recovers the octave
spacing and leaves the offset short by `(1 − k_new/k_trim) × 2.5 V`. Trimmed
against 100 kΩ and then played into 50 kΩ, that is **+29 cents sharp on every
note**; into 33 kΩ, **+59 cents**. A one-number correction therefore converts a
progressive tracking error into a *constant* transposition, which is worse to
play than the error it replaced.

The trimmer is unaffected — it is a physical offset adjustment and has always
had both authorities. The defect is in the calibration *model*, not the
hardware, and the hardware authority already exists: the 0.25–4.75 V window
reserves ±600 cents of firmware offset precisely because firmware can shift the
DAC code. "Nothing implemented `b`" was true of the model and never of the
part.

**So store an affine `(gain, offset)` pair per load preset, not a scale
factor.** It is a second stored float and no new hardware.

The 1 kΩ still stays. The decision survives; only its stated reasoning does
not.

**The alternatives each cost more than they return.** Dropping to 100 Ω gives up
an order of magnitude of short-circuit protection to reduce, not remove, an
error that calibration removes entirely. Feeding the op-amp's feedback from the
jack side eliminates the error properly but puts the patch cable's capacitance
inside the loop, and the correct compensated version of that (TI's dual-feedback
topology) has to be designed as one piece with the output filter it replaces.
That is real stability work, on a board without one, to fix something a
screwdriver already fixes.

### What this costs, and how it is paid

**The calibration is specific to the load it was made against.** Re-patching
pitch from one VCO to two on a passive mult changes the gain by 0.98 % — about
**58 cents at five octaves up**, which is audible and then some.

Three things pay for it, none of them hardware:

- **Calibrate with the real patch connected.** E9 already verifies against a
  real VCO rather than a meter; it now also means *the* VCO, loaded the way it
  will be played.
- **Use a buffered mult for pitch, not a passive one.** A buffered mult presents
  one constant high-impedance load no matter how many oscillators hang off it,
  which makes the whole problem disappear at the patch level. This is the actual
  fix and it costs nothing, because the rack already has the option.
- **Firmware carries a per-load affine `(gain, offset)` pair.** A named preset
  per patch — "one VCO", "two multed" — is two stored floats and a display
  line, and it reaches loads the trimmer was not set for without touching a
  screwdriver. **Two numbers, not one**: see above for why a scale factor alone
  leaves the whole instrument a fixed 29–59 cents sharp.

### The offset reference is `VREFOUT`, buffered — not the rail

This is the largest single pitch error in the design, and the only class of
pitch error that **moves while you play**.

A trimmer dividing a bare ±12 V rail has a sensitivity of roughly 0.21 V/V, so
everything that happens to that rail lands on pitch with no rejection at all:

| On the rail | At the pitch jack |
|---|---|
| 12 mV of thermal drift | 3.0 cents |
| 50 mV step when another module powers up | **12.5 cents of transposition** |
| The WS2815 square wave | **~22 cents p-p of pitch FM** |

ADR 0004 worried about this exact rail and defended the *op-amp's supply pins*
for 80 dB of PSRR and 0.011 cents, while leaving the offset reference a bare
divider on the same rail. **Sixty-six decibels off the right node** — the ratio of 22 cents to 0.011 is 2000, which is 66 dB, not the 86 this line used to claim.

**Divide the offset trimmer from the DAC8568's `VREFOUT` instead**, buffered by
the spare OPA2197 half. Three things follow, and the third is the good one:

- `VREFOUT` is a 2.5 V reference inside the part, off the LM317's own 5.21 V —
  it does not carry LED current and it does not move when a neighbouring module
  powers up.
- Buffering it matters, and not only for drive. Hanging a *trimmer* directly on
  `VREFOUT` would make the reference move as the trimmer is turned, coupling
  the offset adjustment into the DAC's full-scale span. A follower breaks that.
- **The offset now tracks the DAC's own scale**, because the DAC's full scale
  *is* `2 × VREFOUT`. A drift in the reference moves gain and offset together,
  where the trimmer cancels both at once instead of fighting them separately.

Cost: two resistors and the last spare op-amp half in `U-OPA-PITCH`. Free at
layout, impossible after fab.

### And stop modulating the rail in the first place

Two more mechanisms land on the same jack, and they add to the one above:

| Route | Magnitude |
|---|---|
| Offset reference rail + WS2815 ripple (above) | ~22 cents p-p |
| ~~**The module's analog rail and the umbilical feed share one 1N5817**, so instrument current modulates its V_f~~ | ~~**~20 cents**~~ **refuted — see `diode-split-rationale`** |
| The module's internal ground | 5.7–7.2 cents |
| The rack's shared bus ground | ~4.8 cents |

> **The 1N5817 row is refuted and struck through, 2026-09-21.** The `V_f`
> modulation is real and independently confirmed. The **20 cents is not**: it
> implies ~21 % pitch sensitivity to the +12 V rail, and pitch full scale is
> set by the DAC's *internal* reference off the LM317, not by +12 V. The real
> path runs through the LM317's line regulation and the OPA2197's guaranteed
> worst-case PSRR, and lands **five orders of magnitude below the smallest
> other term in this table**. Every number in that chain is the tracked figure
> `diode-split-rationale`, owned by `power-entry.md`, and is deliberately not
> restated here. The 20 cents was a survival from the rail-divider offset
> topology this ADR itself deleted.
>
> *(This block restated the whole chain — "80 mV", "75 mV", "39 µV",
> "0.00027 cents" — until 2026-09-21. The modulation was later re-read off the
> banked 1N5817 curve as a different number, and none of the four terms here
> followed. Four documents held four different values for one quantity.)*
>
> **`D-REVPOL` still goes to three, on the reasons that hold**: fault isolation
> between the exported umbilical rail and the module's own analog rail, so a
> short in the instrument cannot pull the analog supply down with it, and HF
> isolation between the two branches (`power-entry.md`). The part was never in
> doubt; only this justification for it was.

The remaining rows are larger than every term in this ADR's precision budget,
and they are the only *dynamic* ones. Two fixes, both free:

- **Separate the Schottkys.** The shared diode is visible by inspection of
  ADR 0004's own power-tree diagram and needs no ground path to do its damage —
  the branch point is *downstream* of the diode. `D-REVPOL` goes to three: one
  for the module's analog +12 V, one for the umbilical feed, one for −12 V.
- **Drive the lighting as a moving dot or bar on a constant-total-current
  field**, rather than by modulating brightness (ADR 0014). One firmware line.
  It removes the drive term from the two mechanisms above rather than treating
  them.

**And schedule the test that is missing.** The one measurement in the plan for
this class of problem scopes the *breath* jack — the channel that is immune,
because it never passes through the DAC or its reference. **Scope pitch while
sweeping the LEDs**, at E9 and again at M8.

### Consequence elsewhere

**The pitch output filter stays an ordinary series RC** — for now, and on
weaker ground than this section used to claim.

**The claim that "the in-loop `Cf` and the separate output filter are
physically the same part and cannot both exist" is false**, and a decision was
built on it. They are different parts in different places:

| Placement | What it is | Verdict |
|---|---|---|
| Cap to ground **at the op-amp output**, before the series R | A capacitive load inside the loop | Genuinely dangerous; correctly avoided |
| Cap **across the feedback resistor** | A *lead* network — it **raises** phase margin | Not the same thing, and not in conflict with anything |
| Cap to ground **at the jack**, after the series R | What this design currently specifies | Safe, but see below |

Seven surveyed designs carry **both** a feedback lead capacitor and a bare
series resistor at the jack, and two annotate both corners on the drawing.
Meanwhile **no DAC-driven module in the corpus puts a capacitor on the jack
side of the series resistor** — where prior art filters hard it does so
upstream of the output stage or actively.

This matters beyond tidiness because it is entangled with the load-divider
decision below: tapping DC feedback at the jack side removes the divider error
entirely, and that is exactly the arrangement that needs a feedback lead
capacitor to be stable. All four surveyed DAC-driven designs do both, with a
single 18–22 pF part. **This ADR declined that as "real stability work" on the
strength of a conflict that does not exist.**

**Adopted.** Pitch now closes its DC loop at the jack, with `C-FB-PITCH`
(**2.2 nF, from the op-amp OUTPUT to the (−) input**) taking the loop back to
the op-amp output above the handover. It is a compensation part, not a filter.
`C-AA-PITCH` (10 nF against `R-OPAMP-IN`, ahead of the op-amp and outside every
loop) is the reconstruction filter, and `C-FILT-PITCH` (10 nF) stays at the
jack as the low-impedance shunt at the connector.

> **This paragraph carried three errors until 2026-09-21, and
> `pitch-stage.md` wins over all three.**
>
> 1. **"1 nF across the feedback resistor"** — wrong net *and* wrong value. With
>    the DC tap at the jack, `R2` spans jack-to-(−), so a cap *across `R2`*
>    connects those same two nodes and leaves `R-OUT-PROT` inside the loop at
>    every frequency: **18° of phase margin with 2 m of cable, under 10° with
>    four destinations**. The part goes from the op-amp **output** to the (−)
>    input, and it is **2.2 nF** now that the jack cap is back.
> 2. **"which is also the reconstruction pole"** — it cannot be. A capacitor in
>    the feedback of a *non-inverting* stage gives
>    `G(s) = (2 + sRC)/(1 + sRC)`: a pole with a zero an octave above it,
>    flattening at unity. **6.02 dB of attenuation, maximum, for any value.**
>    It is a shelf, not a pole. Two independent reviews found this separately.
> 3. **"`C-FILT-PITCH` is deleted"** — **the deletion was reversed and this ADR
>    was not updated.** Two loop analyses put 10 nF at the jack and found phase
>    margin *unchanged*, because `C-FB-PITCH` ties the (−) input to the op-amp
>    output so `β(∞) = 1` and `R-OUT-PROT` isolates the jack above the handover.
>    Deleting it cost 30 dB at 1 MHz and left the connector with no shunt at
>    all.

Consequences, all good:

- **The load-divider error is gone**, for any load. The −11.9 and −23.5
  cents/octave figures below become historical.
- **`TRIM-GAIN` shrinks to 200 Ω** (0 → +2 %), which drops its tempco
  contribution to ~2 ppm/°C — *comparable to* the LT5400 instead of 4–20× it.
  That answers this ADR's own objection to its own trimmer.
- **The per-load affine preset stops being load-bearing.** It stays as a
  firmware convenience; it is no longer the only thing standing between the
  player and 59 cents.

**This is the highest-risk change in the module**, and E9's "pitch stability
into worst-case cable capacitance" row was already in the measurement table. It
is now a gate rather than a reassurance. The mod channels are unaffected — their
feedback comes from the op-amp output, so `R-OUT-PROT` isolates their jack-side
capacitors exactly as intended.

**Two things about that capacitor have to be written down, and only one of them
was.** The review found the C of every one of these RCs missing from the BOM,
with no value anywhere in the repository. It is now there — but the value is
the easy half:

- **Which side of the 1 kΩ.** On the **mod and breath** outputs the capacitor
  goes on the **jack side**, so the resistor isolates the op-amp from it; on
  the op-amp side it is a capacitive load inside the loop. **Pitch is now the
  exception** — its feedback is tapped at the jack, so that node is the
  feedback node and carries no capacitor at all. Its filter sits *ahead* of the
  op-amp instead (`C-AA-PITCH`), on a node with no loop around it.
- **Dielectric: C0G or film, never X7R.** X7R's DC-bias coefficient moves the
  corner by ~30 % at 10 V, and X7R is piezoelectric — in a pitch reconstruction
  filter that is a literal microphonic detuning element. Same price, same
  footprint.

| Output | R | C | Corner |
|---|---|---|---|
| Pitch | `R-OPAMP-IN` 1 kΩ, **ahead of the stage** | 10 nF C0G | 15.9 kHz |
| Mod 1–4 | 1 kΩ | 82 nF C0G | 1.94 kHz |
| Breath | 1 kΩ | 330 nF film | ~480 Hz |

Breath is the odd one because it never passes through the DAC: it has no
zero-order-hold image to attenuate, and it is already a 482 Hz channel by the
time it reaches the module (`hardware/module/breath-receive-stage/breath-receive-stage.md`). This
ADR's earlier "~2 kHz for breath" is superseded by that page.

## Firmware defaults and bring-up rules

Small things, but each is the difference between a first power-on that behaves
and one that surprises someone holding an instrument.

**Enable the DAC's internal reference explicitly at boot.** It is disabled by
default. Nothing works until this write happens, and the failure looks like dead
hardware.

**Default every mod and breath range to 0–8 V.** The mod channels *can* do
±10 V, but that is headroom, not a default — 0–8 V is the de-facto Eurorack
convention and is what most patches want. **Bipolar is opt-in per channel**, set
explicitly from the display, so nothing sends a negative voltage into a patch
that was not asked to receive one.

**Put the two pitch calibration anchor points inside the musically used range**,
not at the −2 V and +7 V extremes. A two-point fit is only as good as its
anchors, and no VCO tracks well at the far ends of its own range — anchoring
there fits the line to the worst two points available. Anchor around the
octaves actually played; the multi-point NVS table handles the rest.

## Small protective parts on the module

Three items that are cheap, are invisible once the board is fabbed, and cannot
be added afterwards.

**1 kΩ in series with each op-amp's non-inverting input where the DAC drives
it.** The DAC runs from its own 5.21 V regulator and the op-amps from ±12 V, so
the two supplies do not come up or collapse together. A driven DAC output into
an op-amp whose rails are absent forces current through the input clamp
structure; 1 kΩ bounds it, and it is outside the feedback path so it costs
nothing in accuracy.

**BAV99 clamp diodes at the CV jacks — silicon, not Schottky.** With a long
external umbilical these are worth the six parts. The part choice matters more
than it looks: a BAT54S's ~2 µA of Schottky leakage through the 1 kΩ output
resistor is 2 mV, which is **2.4 cents of temperature-dependent pitch error** —
reintroducing exactly what the matched network and the trimmers were bought to
remove. BAV99 leakage is orders of magnitude lower.

**Ferrite beads rated ≥1 A, in 1206 or 1210.** The common 0805 600 Ω part is
rated around 300 mA and both +12 V branches now exceed that. A saturated bead
does not degrade gracefully — it loses its impedance entirely and becomes a wire.

## Labelling

Channels 1 and 2 are silkscreened. Mod 1–4 are numbered with a write-on strip,
with the instrument's display as the authority on what is actually routed where.

Optional later: an LED per jack tracking that channel's value, for instant
visual confirmation of what is doing what. Costs a driver and six LEDs; not
worth designing in now.

## Test equipment

Resolved — a full bench is available: oscilloscopes, logic analysers,
multimeters, signal generators and RF gear. E9 is not gated on tooling.

This raises what is achievable at several milestones. Rather than trusting
datasheet figures, the assumed numbers in
[the latency budget](../reference/latency-budget.md) should be measured; see
the characterisation section there.

For calibration specifically: take the two-point fit with the meter, then verify
tracking against a real VCO by ear and by frequency counter. A meter confirms
the voltage is what was commanded; only the VCO confirms the voltage is
musically right.
