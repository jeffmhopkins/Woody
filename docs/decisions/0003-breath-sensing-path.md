# 0003 — Breath sensing signal path

**Status:** Accepted

## Context

Breath is the primary expressive control. With binary keys (ADR 0002) it carries
most of the instrument's expression, so its speed and resolution matter more
here than they would on a keyboard-style controller.

The initial instinct was to keep breath analog end to end — sensor straight
through a gain stage to the jack, never touching the MCU — on the grounds that
digitising would cost resolution and speed.

## The latency budget

Measured against the real chain rather than intuition:

| Stage | Time |
|---|---|
| Pressure transducer response | **~1 ms** |
| SAR ADC conversion | ~50–200 µs |
| SPI to MCU, firmware | < 20 µs |
| SPI to DAC over the umbilical | ~50 µs |
| DAC settling | ~10 µs |
| Op-amp and reconstruction filter | ~160 µs |
| **Total** | **< 1.5 ms** |

**The transducer dominates.** The entire digital path costs less than the
sensor's own settling time. Going fully analog would save roughly 400 µs against
a 1 ms floor.

For scale: the fastest physical gesture available is a hard tongue attack, with
a rise time somewhere around 5–15 ms. The digitised path comes to **~3.1 ms**
against a 5 ms target — **about 1.6×, not the 10× this sentence used to claim**.
The old figure came from a table that left out the filter poles this design
specifies, the sampling period, and the pneumatic restrictor. See
[the latency budget](../reference/latency-budget.md); the restrictor is still
unmeasured and is the term most able to break it.

On resolution: a 16-bit path gives 65,536 steps. The noise floor of human breath
— turbulence, diaphragm tremor — sits orders of magnitude above that. The
previous instrument ran a 10-bit ADC into 7-bit MIDI CC and played fine. There
is no resolution being left on the table.

## Decision

**Analog sensor → fast external SAR ADC → firmware → DAC → analog scaling → jack.**

The analog *sensor* is kept — and this is a point in favour of the original
instinct. Digital I2C pressure sensors have conversion times of several
milliseconds plus bus overhead; they are *slower* than an analog transducer read
by a fast ADC. The fast configuration genuinely is an analog front end.

**Use a SAR converter, not delta-sigma.** A delta-sigma at high oversampling has
real group delay in its digital decimation filter — potentially milliseconds,
which would consume the entire budget above. SAR converters have essentially
zero latency.

Loop rate: 4 kHz (settled — see the latency budget for why 8 kHz does not close).

### The ADC specification needs revisiting

MCP33131-10 (16-bit, 500 ksps) was chosen when the breath **output** was going
to be digitised. It no longer is — the CV path is analog end to end.

What the ADC actually serves now is much less demanding: breath threshold and
note gating, a modulation source for the mod channels, the display, and USB
MIDI. Only the mod-channel use benefits from real resolution, and MIDI CC is
7 bits.

So 16 bits at 500 ksps is considerable overkill, and a cheaper, simpler part at
12–16 bits and a few tens of ksps would do. The SAR-not-delta-sigma rule still
holds — the threshold that starts a note is on the latency-critical path.

Still worth keeping it external rather than using the ESP32's internal ADC,
which is noisy and nonlinear enough to be visible on a modulation output.

## What digitising buys

These are the reasons the fully-analog path was rejected, and none of them are
recoverable in hardware:

- **Curve shaping.** The previous firmware had `breath_gamma` and a `lin_to_log`
  mapping. This is the difference between a breath response that feels like an
  instrument and one that feels like a volume knob.
- **Ambient zeroing** — *for the digital copy*. The old code sampled
  `ambient_breath_reading` at startup for good reason: sensor offset and
  atmospheric pressure both drift, and note gating fires off a threshold. The
  analog CV at the jack is zeroed separately, by the panel knob, because that is
  the representation the knob can actually see (below).
- **Threshold logic.** Breath crossing a threshold is what starts a note.
- **Noise.** Filtering in software is free. Amplifying raw sensor noise across an
  entire chain to a jack is not.

Panel knobs (ADR 0006) handle *range fitting*; firmware handles *response feel*.
Different jobs, both kept.

## Sensor: MPXV4006DP

0–6 kPa, integrated signal conditioning, ~0.2–4.80 V out. Directly usable by a
SAR ADC with no instrumentation amplifier.

The old repository contradicted itself — its README said MPXV4006GP while
`src/owp/owp.ino` said MPX2010GS, which is uncompensated and unamplified at
~25 mV full scale and would have needed an instrumentation amp. That question is
moot now that parts are being bought new.

**The part is the DP, not the GP, and that is a sourcing decision rather than a
technical one.**

| | MPXV4006**GP** | MPXV4006**DP** |
|---|---|---|
| Lifecycle | **Obsolete**, distributor stock only | **Production**, supported through at least 2028 |
| Sensitivity | 766 mV/kPa | 766 mV/kPa |
| Output span | 0.2–4.80 V | 0.2–4.80 V |
| Supply | 4.75–5.25 V, 10 mA | 4.75–5.25 V, 10 mA |
| Case | 1369-01, single side port | **1351-01, dual ports, same side** |

**The transfer function is identical**, and it verifies against this ADR's own
figures: `Vout = VS × (0.1533·P + 0.04)` at VS = 5 V is 0.7665 V/kPa with 0.20 V
at zero — the DP's published numbers exactly. Same die, same datasheet, same
ratiometric behaviour, so nothing downstream changes: the REF5050 supply
decision, the 400 mm tube, the in-amp receiver and the analog path are all
untouched.

What changes is that **the project's largest sourcing risk goes away.** The GP
had been EOL since 2021 and the standing action item was to hoard three to five
before stock disappeared. The DP needs no hoarding — buy two, as ordinary spares
for a part that gets breathed into for years.

The cost is a different footprint, and it is free because the carrier has not
been laid out. **Design for case 1351-01.**

The 0–6 kPa range was well chosen in 2021 and stands. Normal wind-controller
playing sits around 0–5 kPa.

### The reference port stays open to the cavity

**The second port is the other face of the same diaphragm, not an outlet.** The
die has one silicon diaphragm with a chamber on each side, sealed from each
other by the diaphragm itself, and the output is proportional to the difference
across it. No air passes between the ports. **The breath tube remains as closed
and dead-ended as it has always been** (see below) — nothing escapes through P2,
and none of this changes the closed-system decision.

The only difference from a gauge part is *where the reference chamber gets its
air*. A gauge vents that chamber through the package; the DP brings it out to a
port stub. Leaving the stub unconnected reproduces the gauge's behaviour exactly.

So it is left open **inside the instrument**, connected to nothing — no extra
tube, vent or plug.

**That is a dependency, not a non-decision, and it is worth stating plainly
because it was never written down while the part was a gauge:**

> **The cavity must leak.** A gauge reference is the air around the sensor. If
> the cavity were airtight, warming it 15 K would raise its pressure by ΔT/T —
> 5.1 % of 101.3 kPa, or **5.2 kPa against a 6 kPa full scale.** Eighty-six
> percent of range, from nothing but the instrument warming up.

It does leak, through eighteen unsealed switch cutouts and the seams, fast
enough that the thermal rise over 10–20 minutes never builds pressure. Two
things make that safe rather than lucky:

- **Continuous auto-zero absorbs anything slow** (ADR 0006). The zero decays
  toward the current reading whenever breath has been sub-threshold for ~2 s, so
  a partial leak presents as drift the instrument is already correcting.
- **M8's thermal soak tests it directly.** The soak already puts a thermocouple
  at the breath sensor; watching the breath zero during the same run costs
  nothing and is exactly the measurement that would catch a cavity sealing more
  than assumed.

**And it constrains one future decision: do not gasket the switch cutouts.** The
review wants moisture control inside a body breathed into for hours, and sealing
those cutouts is the obvious move. It would silently break the pressure
reference. If moisture control ever pushes that way, the reference port gets
vented to outside through its own filtered stub first — which the DP makes
possible and the GP did not.

The decision is also recoverable, which is why it is safe to take now: **M8 is
pre-bond.** If the soak shows the zero walking with temperature, the vent can
still be added with the instrument open in front of you.

**Confirm which port is P1 before layout**, from the datasheet, and verify with
a syringe at E2. This is a unidirectional 0–6 kPa part, so a reversed connection
does not read backwards — it reads zero, which is easy to mistake for a dead
sensor.

### Assembly rule: the reference port must never be blocked

"Open to the cavity" is a requirement on the build, not just an absence of
plumbing, and there is already something in the design that could violate it.

If the reference chamber gets sealed — tape, adhesive wicking in during
lamination, potting, or **the conformal coating this project specifies for the
in-body boards** (ADR 0009) — it becomes a trapped volume inside a body that
warms 10–20 K. That air gains roughly **5.2 kPa** by the same arithmetic as the
cavity case above. The output is P1 − P2, so the reading goes *negative* by
5.2 kPa, and a unidirectional part simply clips:

> **The instrument sits at 0.2 V and looks dead** — or needs implausible breath
> pressure to register anything at all. And because it tracks temperature, it
> reads correctly from cold and fails after ten minutes of playing.

That is a far more confusing failure than a drifting zero, and it is an
*assembly* mistake rather than a design one, which is the kind that actually
gets made. Three rules follow:

- **Mask both ports before coating.** The pressure port takes a tube; the
  reference port takes nothing and must stay open to air.
- **Keep adhesive away from the sensor during lamination**, and orient the part
  so neither port faces a glue line.
- **The E2 warm-up check catches it.** Run the sensor from cold through twenty
  minutes of playing and watch for output that falls rather than drifts. A
  falling output under warming is a blocked reference chamber; a drifting one is
  ordinary thermal offset that auto-zero handles.

## Sensor placement: at the bottom, with the real-time board

**Decided after review. This reverses an earlier placement whose justification
turned out to be false.**

An earlier revision put the sensor at the top on a 30 mm tube, reasoning that
*"the SPI bus already runs the full length of the body … putting the breath ADC
up there shares an existing bus."* **That is wrong.** The 74x165's QH is a
permanently driven output with no output-enable pin, so the shift register chain
and the MCP3202 cannot share MISO at all — the ADC could never have been read.
The stated reason for the short tube did not exist.

With that gone, three things push the sensor down:

- **Routing.** At the top, the analog pair must traverse the whole body through
  side channels shared with pulsed LED current. At the bottom it sits where the
  umbilical leaves, and **there is no internal analog run at all.** That deletes
  the problem rather than managing it — and the internal equivalent of the AGND
  sense-return rule, which no ADR ever wrote, stops being needed.
- **Thermal.** The display board (AMOLED + WiFi) is the hottest single item in
  the instrument and lives in the top zone. The interior rises 10–20 K over
  10–20 minutes, and this is a **gauge sensor with a temperature-dependent
  offset whose zero is captured once at cold startup.** Putting it next to the
  heat source is the worst available placement for both.
- **Serviceability.** The sensor is moisture-sensitive (below), and the
  most likely part to fail, in a body that cannot be reopened. At the bottom it
  is at least near the one face that is not a key surface.

### The cost, and why it is affordable

| Tube | Delay | First resonance |
|---|---|---|
| 30 mm (old) | 0.09 ms | ~2.9 kHz |
| **400 mm (chosen)** | **1.17 ms** | **214–429 Hz** |

Breath path goes from ~1.5 ms to ~2.6 ms against a 5 ms target. The tube
displaces the transducer as the dominant term, but there is ample margin against
the 5–15 ms rise of the fastest gesture available.

**The resonance needs handling, and the model this ADR used was invalid.** An
earlier revision called it a **Helmholtz resonator** at ~320 Hz and prescribed a
trap volume to place it. A Helmholtz model requires the neck volume to be small
against the cavity, and here it is the other way round: at a 3 mm bore the
400 mm tube holds **2.83 mL**, which is larger than the ≤1 mL trap. The lumped
assumption is violated backwards.

The correct model is a **distributed pipe**: 214 Hz closed at the sensor and
open at the mouth, 429 Hz with the mouth sealed on the mouthpiece. Two things
follow, and the second is the one that changes what gets built:

- It sits **below the 500 Hz filter corner either way**, so the electrical
  filter does not help. That was already true and the old model got it right by
  luck.
- It is **independent of trap volume.** No restrictor *size* moves it. The
  previous prescription — size the trap to place the resonance — cannot work,
  and neither can tube length within any range this instrument has.

**So the intent is damping, not placement.** The PTFE restrictor stays and its
job is restated: add acoustic resistance so the pipe mode is damped wherever it
lands, rather than tuned to somewhere convenient. The same plug still doubles as
the moisture barrier, which is why it is specified as porous PTFE rather than as
an orifice.

- **Specify the trap volume at ≤1 mL**, still — but for response time and
  clearability, which is what it was always actually buying.
- **Specify the bore** (below), because until this revision the two resonance
  figures in the repository described different tubes.
- **E2 measures the damped response**, not the resonant frequency: tap the
  mouthpiece end and watch the sensor ring down. One time constant, or a
  decaying oscillation that needs a denser plug.

## Breath output is analog, sent differentially

Breath is the one channel where output steppiness reaches the ear: it modulates
continuously, usually into a VCA, so staircase ripple becomes amplitude
modulation. Pitch is static between notes and mod channels are slow, so neither
has the same problem.

**So the breath CV never gets digitised on its way to the jack.** The sensor's
buffered output is driven down the umbilical as an analog signal and scaled in
the module. Zero steps, by construction, at any rate.

### Why a Eurorack patch cable gets away with this, and what to copy

A patch cable carries single-ended CV between modules with no trouble at all,
and understanding *why* is what makes this work here.

**A module's power returns through the bus board's ground rail, not through the
patch cable.** The patch cable's ground carries only the signal current flowing
into a high-impedance input — microamps — so it develops essentially no IR drop
and acts as a pure voltage reference.

| Receiving input | Signal current | Drop across 2 m of 24 AWG |
|---|---|---|
| 100 kΩ | 50 µA | 8.4 µV |
| 1 MΩ | 5 µA | 0.8 µV |

Against a 153 µV LSB on a 10 V output, that is nothing. The patch cable works
because **its ground does exactly one job.**

### The failure mode is a shared conductor, not a cable

The umbilical breaks that condition only if one ground conductor does both jobs.
The instrument draws its power down the same cable, and that return current
through a shared ground develops a real, *moving* offset:

| Instrument draw | Offset on a shared ground |
|---|---|
| 100 mA | 16.8 mV |
| 200 mA | 33.7 mV |
| 350 mA | 58.9 mV |

It moves with display brightness, LED animation and WiFi bursts — breath CV
modulated by the light show.

### So separate the grounds and it is a patch cable again

**Give the analog signal its own return conductor that carries no power
current**, and have the module sense `BREATH` against `AGND` rather than against
its own local ground. `AGND` then sits at true instrument-ground potential at
both ends, and the error falls back to the microvolts in the table above.

This restores exactly the Eurorack condition inside the umbilical, and it means
the instrument end needs **only a buffer** — an op-amp follower, band-limited,
with a series resistor for protection. No differential line driver.

The module end must sense `BREATH` against `AGND` rather than against local
ground — that part is not optional, since sensing against local ground puts the
shared-ground offset straight back in.

**But the receiver is a true instrumentation amplifier — settled as the
INA828 (`hardware/module/breath-receive-stage.md`) — not a difference
amplifier.** A difference amp's CMRR is set by **source-impedance
balance, not by the chip**: TI's own datasheet states that a 10 Ω mismatch
degrades the INA134 to ~74 dB, and this design's own protection resistor and
pulldown would have left roughly **19–34 dB against the 60 dB the scheme needs.**

The two requirements were also incompatible as specified: protecting the buffer
against a sustained +12 V fault on the BREATH conductor needs **≥3.3 kΩ** of
series resistance, and 3.3 kΩ unmatched leaves ~24 dB of CMRR.

**A buffered-input in-amp dissolves that conflict entirely** — gigaohm inputs
make source impedance irrelevant, so protection resistors can be 10 kΩ and
unmatched with no CMRR penalty. (Moving the buffer to a +12 V rail, below,
removes the ≥3.3 kΩ requirement at its source as well. The two fixes attack
opposite ends of the same conflict and neither depends on the other.) Two further benefits: it **absorbs the ~2.13×
scaling stage** so net part count is flat or lower, and it has **real DC offset
and drift specifications**, where the INA134 is an audio part characterised for
AC feeding what is here a DC-accurate output.

*(A third benefit used to be listed here — the `REF` pin as an injection point
for a firmware ambient-zero. That mechanism is deleted; `REF` carries a
**commissioning trimmer**, buffered, derived from the LM317's 5.21 V rail. It must tie **hard**, or to a buffer: source impedance on an
in-amp's `REF` pin adds directly to its internal network and degrades CMRR
one-for-one, so a divider there would have been the same class of mistake as a
single-ended capacitor on one input leg.)*

**The pulldown is deleted and replaced by a common-mode bias return.** The
original rule — put it differentially across BREATH–AGND, never on one leg,
because a single-leg shunt caps CMRR near 19 dB — is correct as far as it goes,
and it was not far enough. **A purely differential element gives the in-amp's
inputs no DC path to ground at all.** Unplugged, input bias current ramps both
inputs until the amplifier saturates, so the breath jack goes to a rail rather
than to the 0 V ADR 0005 promises.

Two 1 MΩ resistors, one from each input to module analog ground, provide the
return *and* the differential path, symmetrically, without the 1–17 % signal
attenuation the 100 kΩ shunt imposed. They divert tens of nanoamps against a
~350 mA power return — about 0.2 ppm, so the sense-return rule survives in
substance. **That rule must now be read as "no *power* current", which is what
it always meant**, because as literally written it forbids the thing that makes
the receiver work.

Values, derivation and the full topology are in
[the schematic](../../hardware/module/breath-receive-stage.md).

Full differential signalling was considered and is not needed: it buys about
6 dB against induced noise, which a twisted pair band-limited to 500 Hz does not
need, at the cost of a driver in the instrument.

### Impedance and bandwidth are non-problems

Drive low-impedance, receive high-impedance, standard practice. With ~200 pF of
cable and a 100 Ω source the corner sits at 8 MHz against a 160 Hz signal — six
orders of margin. Transmission-line behaviour is irrelevant at this bandwidth.

**Band-limit at both ends, around 500 Hz.** The sensor only has ~159 Hz of real
bandwidth, so a narrow channel costs nothing and rejects almost everything that
could couple in — SPI edges, LED PWM, WiFi bursts and switching-supply hash all
live far above it. A low-bandwidth analog channel is much easier to keep clean
than a wide one.

### It pays for itself on the digital link

| | Payload | SPI clock |
|---|---|---|
| Breath digital at 96 kHz + 5 channels at 2 kHz | 3.39 Mbit/s | ~6.8 MHz |
| **Breath analog, 7 channels at 4 kHz** | **0.90 Mbit/s** | **2 MHz** |

*(The 0.6 MHz this table used to give came from a 2 kHz mod rate and five
channels; ADR 0006 moved to 4 kHz and the loop refreshes seven. It did not
close. The conclusion below is unaffected — 2 MHz is still a long way from
6.8 MHz.)*

This **cancels the RS-485 escalation** in ADR 0004 and **removes the sub-10 µs
DAC settling requirement** in ADR 0006. Both of those existed only to carry a
96 kHz breath channel that no longer exists.

### The sensor runs from a precision reference, not the shared 5 V rail

**The MPXV4006DP is ratiometric by specification:**

```
Vout = VS × (0.1533 · P + 0.04)
```

Its output is a *fraction of its own supply*. Put it on a rail that moves, and
the breath CV moves with it — and since the output path is analog end to end,
nothing downstream can correct it.

The original design fed the sensor from the same 12 V→5 V buck as both dev
boards. That rail carries AMOLED current steps, WiFi TX bursts and key-LED
transitions:

| 5 V rail excursion | Error at the breath jack |
|---|---|
| 0.4 % (a modest load step) | 21 mV |
| 1 % | 52 mV |
| 2 % | 104 mV |

For scale: the AGND common-mode path that this ADR spends several pages
resolving contributes **0.13 mV**. The ratiometric path is roughly **30 dB
worse** than the one that was analysed.

**The usual free fix does not apply here.** Normally you reference the ADC to
the same rail as the sensor, and the ratio cancels in the digital reading. That
works for a digital breath path. This one is analog to the jack by design, so
there is no division to cancel in.

**Absolute accuracy is not what matters.** Breath is zeroed at ambient and the
module's gain knob sets the span, so a rail that is 4.93 V instead of 5.00 V
calibrates out on the first breath. What does not calibrate out is *dynamic*
excursion — load steps with millisecond envelopes, which pass straight through
the 500 Hz filter as amplitude modulation correlated with whatever the display
happens to be doing.

**So the sensor gets its own supply:**

```
umbilical +12V ──[REF5050 5.000V]──[OPA2197 ½ buffer]──┬── MPXV4006DP VS
                                                       └── (10 mA available)
```

- **REF5050**, SOIC-8, 7–18 V in, 5.000 V out at ±0.05 % and 3 ppm/°C, with line
  regulation around 5 ppm/V — so a full volt of movement on +12 V shifts the
  sensor supply by ~25 µV.
- **Buffered by half an OPA2197** running on +12 V. The reference alone can
  source 10 mA against the sensor's ~10 mA, which is inside its rating and has
  no margin; the buffer removes the question and costs nothing, because the
  other half of the package is the breath buffer itself.

### The breath buffer moves to +12 V, which dissolves the protection conflict

The buffer was an MCP6002 on the 5 V rail. It becomes **the second half of the
OPA2197**, running from +12 V.

That is partly tidiness — one part number instead of two, and the same part
number the module already uses — but the real reason is that it resolves a
conflict this ADR could not otherwise settle.

**The conflict:** a sustained +12 V fault on the BREATH conductor drives the
buffer's output back through its series resistor into the buffer's own supply
rail. Through 1 kΩ into a 5 V rail that is 6.4 mA against a ~2 mA clamp rating,
so protection needs **≥3.3 kΩ** — and 3.3 kΩ unmatched leaves only ~24 dB of
CMRR against the 60 dB the link needs. The two requirements were incompatible as
specified.

**With the buffer on +12 V there is no conflict, because there is no fault
current.** A +12 V conductor against a +12 V rail is at the rail, not above it.
The clamp never conducts, the series resistor is free to stay at the value CMRR
wants, and the worst case is the op-amp sinking a few milliamps within its
linear output range. The umbilical's highest voltage is +12 V, so this covers
the realistic fault rather than an arbitrary one.

The buffer still has to reach 0.2 V at the bottom of the sensor's range. An
OPA2197 is rail-to-rail on a single +12 V supply and reaches within ~30 mV of
ground, so the requirement that drove the original RRIO-on-5 V choice is met
with far more headroom than before.

**The ADC stays on 3.3 V.** The obvious follow-on — move the ADC to the buffered
5.000 V rail too, so the digital reading becomes ratiometric — is wrong here.
The MCP3202 takes its reference from VDD, so a 5 V VDD also means 5 V logic on
DOUT into an ESP32-S3 pin that is not 5 V tolerant. That trades an analog
divider for a level shifter. The 0.6× divider below stays.

### The ADC does not go away

The sensor's buffered output splits two ways:

- **To the umbilical buffer** — full scale, 0.2–4.80 V, for the CV output.
- **To the SAR ADC** — for breath threshold and note gating, as a modulation
  source for the mod channels, for the display, and for USB MIDI.

**The ADC branch needs attenuating.** The sensor reaches 4.7 V while the ADC
runs on 3.3 V, so that branch takes a divided copy — roughly 0.6× — to land
inside the converter's input range. The umbilical branch stays full scale.
Divide *after* the buffer, not before, so the divider does not load the sensor.

**Size the upper divider resistor at ≥10 kΩ.** On a cold start the 5 V rail
comes up before the real-time board's 3.3 V regulator, so for a few milliseconds
the divider drives the ADC input above its own supply and current flows through
the ESD clamp. A low-impedance divider puts ~2.5 mA into that diode, at or over
the family-typical ±2 mA limit, on **every power-up**.

**And put a 47 nF cap at the ADC input pin.** This is the highest-value passive
in the breath path and it does three jobs at once:

- **Anti-aliasing, which is otherwise absent.** The *signal* is band-limited by
  the sensor to ~159 Hz. The *noise* is not — the buffer has ~1 MHz of bandwidth
  and passes switching ripple, SPI crosstalk and WS2815 data at 800 kHz. A buck
  running at 500 kHz sampled at 4 kHz folds to DC; at 498 kHz it folds to
  **2 kHz**, and at 496.1 kHz to **100 Hz — directly into the breath band**,
  indistinguishable from playing. Worse, the alias frequency *moves* with the
  converter's load-dependent switching frequency, so it is a wandering tone
  rather than a fixed one. 47 nF gives a ~564 Hz corner and **58 dB at
  500 kHz**.
- **It is the charge reservoir for the MCP3202's sample capacitor**, which fixes
  the source-impedance problem that the ≥10 kΩ divider above would otherwise
  create.
- Together with the divider it settles well inside the 250 µs loop period.

So curve shaping, thresholds and ambient zeroing still exist in firmware; they
just no longer sit in the path to the breath jack.

### What the analog path gives up, and what replaces it

**Curve shaping on the breath output.** Genuinely lost — `breath_gamma` cannot
apply to a signal firmware never touches. In a modular context this is arguably
correct: sending raw breath and shaping it with the rack's own tools is the
idiom, and the panel gain and offset knobs (ADR 0006) are exactly the Pulp
Logic model. Shaping still applies to the digital copy driving mod channels and
MIDI.

**Ambient zeroing — one authority per representation.** There are two breath
signals, not one: the **analog CV at the jack**, and the **digital copy** the
ADC sees inside the instrument. Each gets exactly one zero authority, and each
authority can measure the thing it corrects.

| Representation | Zero authority | Can it see what it corrects? |
|---|---|---|
| **Analog CV at the jack** | The module's panel **offset knob** | Yes — the player's ear, and a meter at commissioning |
| **Digital copy** | Firmware, from the ADC reading | Yes — that *is* the ADC reading |

Firmware seeds the digital zero from an ADC capture at power-on, exactly as the
2021 code did, and then keeps tracking it (ADR 0006). The analog path is not
touched by firmware at all: the in-amp's `REF` pin carries a trimmer set once at
commissioning, and the panel OFFSET knob is the performance control
(`hardware/module/breath-receive-stage.md`).

**That trimmer is referenced to the LM317's 5.21 V rail, deliberately, and not
to the DAC's `VREFOUT`.** `VREFOUT` is the DAC8568's internal reference, which
is *disabled at power-on until firmware writes an enable* — deriving the breath
zero from it would make the analog breath path depend on a DAC register, which
is exactly what this section says it does not. The LM317 rail is up whenever
+12 V is.

**An earlier revision drove `REF` from DAC channel 6** and called it "digital
control of an analog signal path, for the cost of one already-paid-for channel."
The channel was paid for; the control was not. Firmware reads the ADC *before*
the umbilical and was injecting *after* it, so it could null its own copy
perfectly while the jack sat at a standing offset — **correcting a signal it
cannot measure, and reporting success about a different one.** It also put two
offset authorities in series on the same channel, which this design calls a
split-brain failure everywhere else (ADR 0006).

What the injection was actually buying: the MPXV4006DP's offset drifts roughly
0.5 mV/K, so a 20 K interior rise moves the jack about **23 mV out of 10 V —
0.23 %**, well under any note-gating threshold. That is a quarter-turn of a knob
you will probably never touch, and it was being paid for with a DAC channel, an
op-amp half, a word in every loop pass, and an unverifiable correction.

*(A further defect in the old text, kept because it is instructive: it said
"analog summing stage" in one place and "REF pin" 174 lines away — two mutually
exclusive injection points in the ADR that owned the decision, and a review
built a showstopper on one of the readings. Neither is the answer now.)*

### Parts

A precision op-amp differential driver and receiver pair is sufficient at this
bandwidth — no audio-specialty part is required, though THAT1606/THAT1200 or
DRV134/INA1650 are drop-in options if convenient. What matters is the receiver's
CMRR and low offset drift, since this feeds a 0–10 V output.

## The closed tube is correct, and why

A design review raised this as a likely error, on good evidence: no commercial
wind controller uses a sealed pneumatic path. The Akai EWI plugs its sensor tube
and drills a side hole, then runs a second tube dangling free for restricted
airflow. The Yamaha WX has a drain hole with swappable plugs that set blowing
resistance. Against a full occlusion an adult produces 15–20 kPa, and the
reviewer concluded the player could not exhale through the instrument at all.

**The premise was wrong, because the exhale path is not the instrument.** The
player vents through the corners of the mouth, around the mouthpiece — which is
also what makes **circular breathing** possible. Air leaves continuously; it just
never enters the sensor tube.

So the tube to the sensor stays **completely closed**, and this is a deliberate
choice rather than an oversight:

- Embouchure controls pressure directly, with no bleed orifice in series to
  blunt it
- Nothing to clog, tune, or get wrong as a manufacturing tolerance
- No flow through the sensor branch at all, which is the property the
  condensation handling below depends on

**Recorded so it is not re-raised.** The commercial designs solve a problem this
playing technique does not have.

Two consequences that do *not* follow from the bleed question and remain open:
the moisture handling below, and the tube resonance model.

## The analog ground star point, defined

Several rules in this ADR refer to bonding `AGND` to "the instrument's analog
ground star point". A review pointed out that **no such point was defined
anywhere**, so the rules referenced an object that did not exist.

It exists now, and moving the sensor to the bottom is what made it trivial:

> **The star point is the analog ground pour on the bottom cluster board, at the
> sensor and reference, immediately adjacent to the umbilical connector.**

Everything analog in the instrument — the sensor, the REF5050, both halves of
the OPA2197, the ADC divider — sits on that one board within a few centimetres
of each other and of the connector. `AGND` leaves the board straight into the
umbilical.

**The same problem used to exist inside the body and was never addressed.** With
the sensor at the top and the connector at the bottom, the analog pair had to
traverse ~400 mm of interior alongside LED power and an 800 kHz data line — the
identical problem this ADR argues at length about over the 2 m umbilical, with
none of the same care applied to it. The sensor move deleted that run rather
than solving it, which is the better outcome and was not the reason the move was
made.

**What replaced it is a 400 mm pneumatic run**, whose failure modes are delay
and condensation rather than common-mode noise, and both of those are handled
above.

### The ambient-zero injection point, which no longer exists

A review finding proposed doing the zero subtraction *in the instrument*, and it
was declined on the grounds that **the instrument has no DAC** — the ESP32-S3
dropped the original's DACs and ADR 0013 puts the only DAC at the module.

That reasoning was sound and the conclusion it defended has since been deleted
anyway. **There is no ambient-zero injection at either end.** Firmware zeroes
the digital copy, which needs no converter because it is already a number; the
analog path is zeroed by the panel knob. The finding, the rebuttal and the
mechanism all went away together.

The claim that let the finding through is worth correcting explicitly, because
it appears in ADR 0004: the instrument is **not** "purely digital with no analog
signal path". It carries the sensor, a precision reference, two op-amp stages
and the analog drive. It is where most of the project's analog risk lives.

## The mouthpiece

A review found that the mouthpiece **did not exist anywhere in the design** — the
word appears only as a reference point ("from the mouthpiece", 40 mm of length
budget, the reason the cable exits at the far end), while ROADMAP E2's acceptance
test requires one. It is the part the player's mouth touches and it had no part
number, no dimension and no decision.

**It is deliberately the simplest thing that works.**

- **No bite or lip sensor.** Settled early and unchanged. There is no embouchure
  axis and none is wanted.
- **A raw tube end is acceptable**, so the mouthpiece is not a precondition for
  playing — E2 and E5 can proceed on a bare tube.
- **A small nib at the end** is the expected final form: a lip locator and a
  mechanical stop, so the tube cannot slide and the lips have something to
  register against without looking.
- **The player vents around the corners of the mouth**, which is what makes
  circular breathing work on a dead-ended tube. That is a *constraint on the
  outside diameter*: it must be narrow enough that sealing the centre still
  leaves the corners open. A tube the lips cannot get around defeats the whole
  breathing technique.
- **Removable and cleanable**, for the obvious reason, on a 400 mm tube that runs
  to a sealed body.

### It also settles the tube bore, which nothing else did

The bore is specified nowhere in this ADR, and two things depend on it: the
acoustics below, and whether the lips can vent around it.

**Specify the bore at the mouthpiece end and let the tube follow it.** The
acoustic analysis says the bore moves the tube's first resonance by 20–40 Hz and
never changes the verdict, so **the bore is a mouth-fit decision, not an acoustic
one** — which is the useful way round. Settle it at E2 by playing a bare tube in
two or three sizes and choosing the one the corners of the mouth clear
comfortably.

## Condensation, in proportion

**This is a closed, dead-ended system** — the tube terminates at the sensor and
no air flows through it. Pressure transmits without bulk flow.

An earlier revision of this ADR called saliva reaching the sensor a certainty
and the most likely thing to ruin the instrument. That was overstated: it
assumed a flow path carrying droplets along, which a sealed dead-end does not
have. What actually happens is **condensation forming slowly on the tube walls**
as warm breath meets cooler surfaces.

Still worth handling, cheaply:

- A **small dead-volume trap at the sensor end** catches what does accumulate.
  Low cost, no downside, and it works regardless of where the sensor sits.
- Make it **clearable without disassembly**. Not a drain plumbed through the
  body — just access.
- Short tubes accumulate less, which Option A gives for free.

Not a stack-level design problem, and not a reason to choose one sensor position
over another.

### But the vapour problem is underestimated in *kind*, not just in degree

The section above is about liquid. The datasheet's objection is not:

- NXP qualifies this sensor family on **dry air** and states it is **"NOT
  compatible with water or water vapors"**.
- The **gel die coat swells when wet**, which shows up as unreliable readings
  rather than as a dead part.
- Exhaled breath is **~100 % RH**, and at 6 kPa the air in the tube compresses
  about 6 % — so every note pumps a little saturated air toward the die.

A dead-volume trap catches liquid and does nothing about vapour, and **vapour
cannot be eliminated from a closed tube that is breathed into.** So the honest
handling is three partial measures rather than one fix:

- **A porous hydrophobic PTFE plug at the sensor port.** It blocks liquid water
  and it is *the same part as the Helmholtz restrictor above* — one component
  doing both jobs, which is why the restrictor should be specified as a PTFE
  plug rather than a drilled orifice.
- **The restrictor limits the pumping itself**, since the ~6 % volume exchange
  per note has to pass through it.
- **Treat the sensor as a wear part.** It is socketed or otherwise replaceable,
  and the trap is clearable without disassembly. **Buy two** — ordinary spares
  for a part that gets breathed into for years.

That last one is the real mitigation. The first two slow the mechanism down; only
spares make it survivable.

This used to be urgent. An earlier revision specified the MPXV4006**GP**, EOL
since 2021 and available only from remaining distributor stock, and said to buy
three to five immediately against the part disappearing entirely. **The DP is in
production**, so the spares are now just spares.

