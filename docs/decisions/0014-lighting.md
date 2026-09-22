# 0014 — Lighting

**Status:** Accepted

## Requirement

An addressable LED run down the length of the instrument, driven by breath and
other instrument state, diffused through the frosted acrylic side panels
(ADR 0009).

**Two light sources, not one.** The side strips above, and the **8×8 RGB matrix
on the real-time board** (ADR 0007), which faces out through a window in the
underside at the tail. The matrix was originally counted as dead weight — 64 LED
drivers that would never be lit, costing current and heat for nothing. Pointing
it at a window turns that into the instrument's only two-dimensional display.

They are covered by one ADR because they share a current budget, a clamp rule
and a blank-at-boot rule, and because the easiest way to get those wrong is to
design them separately.

## Geometry: two runs, one chain

A single strip "down the middle" is not available — switch bodies occupy the
centreline for the full length of both key runs (ADR 0009, ADR 0013). The free
volume is the **two side channels flanking the switch column**, which is also
exactly where the light needs to be: immediately behind the acrylic it has to
illuminate.

So: **one run per side**, roughly 420 mm each, 0.84 m total.

**Both channels carry LEDs, and the wiring looms share them.** ADR 0009
previously assigned these same channels to the looms — a contradiction between
two accepted decisions. It resolves because the breath sensor moved to the
bottom of the instrument (ADR 0003), so no analog signal traverses the body and
the looms carry only digital traffic. The instruction below to keep LED runs
away from the breath wiring now costs nothing, because the breath wiring is not
in the body.

### Two independent strips, not one chained pair

Three ways to wire two runs:

| | GPIO | Crossover wire | Sides can differ |
|---|---|---|---|
| **A** — chained, data loops end to end | 1 | **yes** | yes |
| **B** — two independent data lines | 2 | no | yes |
| **C** — parallel, same data to both | 1 | no | no, always mirrored |

**B.** The deciding factor is physical: chaining needs a data wire crossing the
cavity at one end of the runs, and **both ends are the congested ones** — the
display board and breath sensor at the top, the real-time board, IMU and
umbilical connector at the bottom. Adding a signal wire across either, inside a
stack that is stripped down to reach (ADR 0009), is a liability for no benefit.

Two data lines cost one extra GPIO, against roughly 17 broken out and 12 needed
on the real-time board (ADR 0007). The ESP32-S3 drives both on separate RMT
channels without effort.

Splitting also means each run installs and is replaced independently during
assembly, and each gets its own power feed, which halves the current per tap.

**C is the fallback if GPIO ever gets tight.** A single GPIO can drive both
strips' data inputs in parallel with no extra parts — each strip's first LED is
a high-impedance input. The cost is that the two sides can never show different
content, which for a symmetric instrument light is probably not a loss. It is
worth knowing the option exists rather than treating one GPIO as a constraint.

Buy one 1 m strip and cut two 420 mm runs from it.

## Rail: use a 12 V strip

The instrument has +12 V from the umbilical and derives 3.3 V locally
(ADR 0005). A 5 V strip would need a third rail for nothing but LEDs.

**WS2815 (12 V, individually addressable)** avoids that, and wins on three
counts:

- **No extra rail.** Runs directly from the umbilical supply.
- **Half the current** for the same light, because the power arrives at 12 V
  rather than 5 V.
- **Backup data line.** WS2815 carries a redundant data path, so a single failed
  LED does not kill everything downstream of it. In a body that is not opened
  casually — six fasteners, a loom and a gasket (ADR 0009) — that matters more
  than it would in a
  serviceable build.

Against: slightly less common and a little more expensive than WS2812B/SK6812.
Worth it here.

## There is no LED driver, but there is a level shifter

Addressable strips carry a controller in every LED, so no external constant-
current driver, no multiplexing and no PWM generator is needed. One GPIO per
strip is the whole interface.

**What is needed is level shifting on the data line.** The ESP32-S3 drives
3.3 V logic; addressable strips generally want a logic high near 0.7 × their
supply. A **74AHCT125** is the standard answer — powered from 5 V with TTL input
thresholds, so a 3.3 V input reads as high and it outputs a clean 5 V edge. One
package covers both strips.

> **Verified 2026-09-21, and the answer is yes.** `V_IH ≥ 0.7 VDD` in a table
> whose header declares `VDD = 4.5…5.5 V` — so **3.15 to 3.85 V**, and the
> 74AHCT125 at 5 V clears it (Worldsemi WS2815 V1.1,
> `datasheets/led/WS2815.pdf`). The worry below was the right worry:
> reading `0.7 × VDD` with pin 2's +12 V meaning gives **8.4 V**, an impossible
> threshold, and the datasheet does reuse the symbol for both nets. The
> conditions line governs. The part choice stands, on a document rather than on
> "most strips".

It is a 12 V part, and if its logic threshold had been referenced to 12 V
rather than an internal rail, 5 V shifting would not have been enough and the
part choice would have needed revisiting. Most 12 V addressable strips accept
5 V logic, but "most" is not a basis for a sealed build.

This is a classic source of intermittent, maddening LED behaviour — strips that
work on the bench and glitch in the build — so it is worth getting right rather
than discovering empirically.

## Power budget, and the cap that is not optional

**470–1000 µF at each strip feed point.** Bulk capacitance belongs where the
current swings, not at the module end of a 14-inch cable — a WS2815 run
modulates its draw by hundreds of milliamps at the ~2 kHz PWM rate, and a
ferrite bead is effectively a wire at that frequency (ADR 0004).


0.84 m total, by density and use:

| Density | Full white | Single hue, full | Single hue, 40% |
|---|---|---|---|
| 30/m (25 LEDs) | 0.50 A | 0.17 A | **0.07 A** |
| 60/m (50 LEDs) | 1.01 A | 0.34 A | **0.13 A** |

> **This table is computed at ~20.2 mA per LED at full white, and that figure
> is not the WS2815's.** `datasheets/led/WS2815.pdf` p.3 states *RGB Channel
> Constant Current **15 mA***, i.e. **45 mA per LED** across three channels
> — **2.23×** the number above. At 45 mA/LED the 60/m row is **2.25 A**, and
> the "both strips full white" row below becomes roughly **27 W and ~81 K**
> rather than 12.1 W and ~36 K.
>
> Note the same page's *Quiescent Current **2.1 mA*** reproduces ADR 0005's
> 123 mA figure exactly, so the two numbers in this corpus came from
> different sources and only the quiescent one came from the datasheet.
>
> **This ADR already says this**, 284 lines below, about the *matrix*: "this
> is the wrong part's figure and it is at least 2.4× too low". The refutation
> landed where the editing was happening and not where the reader looks —
> which is this project's named failure mode, in the ADR that owns lighting.
> The table is left as drawn rather than silently rewritten, because
> `matrix-led-current` is `blocked` on a bench measurement and the strip
> figure needs the same treatment: measured, not re-derived. **What is
> settled is that the ~3 W clamp was sized against a load case that is 2.23×
> understated.**

### The constraint is not the rack. It never really was.

Earlier revisions of this section argued from the rack supply: *"Eurorack
supplies commonly provide 1–3 A on +12 V for the entire case, and full white at
60/m would take a third to a whole rail."* **The target rack's supply is
generous** (see the design scope in the README), so that argument is withdrawn.

Withdrawing it does not relax the clamp. It **replaces a soft constraint with
two harder ones that were sitting underneath it**, and the binding one is
tighter than the rack ever was.

**Heat, which is the one that actually binds.** The body is oak and acrylic —
both insulators — sealed, with the aluminium plate as the only real path out and
the player's hands covering part of it. The existing electronics dissipate
roughly 5 W for an interior rise of 10–20 K, so call it **~3 K per watt**.

| Lighting state | Power | Interior rise it would add |
|---|---|---|
| Realistic use — single hue tracking breath | ~1.5 W | ~4 K |
| Both strips full white at 60/m | 12.1 W | ~36 K |
| Matrix full white as well | ~17.7 W | **~53 K** |

A pathological state is not a brownout any more. It is an instrument too hot to
hold, an acrylic bond at its service limit, and a gauge sensor whose zero is
chasing the room. **The rack supply would have delivered it happily.**

**The instrument's own regulator, which is a 1 A part.** The matrix hangs on the
R-78E5.0-1.0 alongside both dev boards, and at full field it asks for 960 mA on
its own. The rack's headroom is on the far side of a 2 m cable and a switching
regulator; neither cares how large the supply behind them is.

**And fault current, which a larger supply makes worse.** A short in the
umbilical now has more energy available, not less. That is the module load
switch's job (ADR 0005) and it is unaffected by any of this — except that it
matters slightly more than it did.

### The clamp, restated on thermal grounds

**A single instrument-wide lighting budget of ~3 W**, summed across both strips
and the matrix, enforced in firmware before any write. When the commanded total
exceeds it, **scale everything down proportionally** rather than refusing the
write.

3 W is twice realistic use and about a sixth of the pathological case, and it
costs roughly 9 K of interior rise — inside what the design already tolerates.
It is generous visually: on the strips it is a quarter of full white or a single
hue at ~75 %; on the matrix it is a sparse display at full brightness or a full
field at around 60 % of one channel.

**Validate it at M8's thermal soak**, which exists anyway, rather than trusting
3 K/W. That figure is a bounding estimate, not a measurement.

Proportional scaling is what makes a full-field breath bar behave: it arrives
dimmer than a single dot would, which is also what looks right.

### The firmware clamp used to be the only defence, and it did not survive

A design review found the failure the clamp guards against is precisely the one
in which the clamp is not running:

> LED current ↑ → umbilical current ↑ → the polyfuse self-heats and its
> resistance rises → the rail sags → the buck draws more input current → the
> polyfuse heats further → brownout → **the MCU resets** → the WS2815s **hold
> their last latched colour** → the load does not fall.

A polyfuse above its hold current does not trip cleanly; it gradually
current-limits, so the MCU misbehaves at reduced voltage before it resets. And
once it has reset, the strips are latched and there is no firmware left to
clamp anything.

**Three things break that loop, and the first two are already decided:**

- **The module's current-limited load switch** (ADR 0005) replaces a slow,
  self-heating, thermally-hysteretic protection device with a fast fixed limit
  that does not run away. The positive feedback term disappears with the
  thermal one. **"Replaces" now means it** — this ADR added the load switch and
  left the polyfuse in the BOM, so for a while the design carried both and the
  runaway term with them. The polyfuse is deleted (ADR 0005).
- **The load switch is at the module, not the instrument**, so the limit holds
  whatever the instrument's MCU is doing — including nothing.
- **Blank both strips *and the matrix* as the first act at boot**, before
  anything else initialises. A reset then clears a latched state in a few
  hundred milliseconds rather than leaving it until something happens to
  overwrite it. The matrix is on the MCU that resets, so it latches too.

**The firmware clamp is a comfort feature against the electrical failure, and a
real one against the thermal failure.** The load switch bounds current whatever
the firmware is doing; nothing but firmware bounds a *sustained* bright state
that is electrically legal and thermally not. Those are different failures and
the clamp is only redundant against one of them.

### Density: 60/m

The density question was open on a budget argument — 30/m stays inside a rack
budget unconditionally, 60/m needs a clamp to. **That argument is withdrawn with
the rest of the rack framing**, and the thermal clamp applies identically to
both, so nothing distinguishes them on current any more.

Which leaves appearance, where 60/m was already the preference: denser LEDs
diffuse more smoothly behind the acrylic. **60/m.**

Realistic use — a single hue tracking breath at moderate brightness — sits
around **0.13 A** there, which is unremarkable against a 3 W budget.

The diffusion prototype at M6 can still downgrade this if 30/m turns out to look
identical through the panels, but it is now a question of appearance and cost
rather than one the electrical design has a stake in.

## The LEDs do reach the breath channel, but not the way expected

The loop was traced in both directions and neither is an oscillation.

**Through the CV path it is negative feedback.** More breath → brighter LEDs →
`AGND` rises → the CV reads lower. Loop gain is around 0.004, so the effect is
**0.4 % of gain compression** — a slight softening of the top of the breath
range, and nothing more.

**Through the ADC it is positive feedback**, via reference depression from
shared-ground LED current. Still far from instability — **but the symptom is not
gain error, it is note-gate chatter.** Right at the breath threshold, LEDs
lighting shifts the reading in the direction that keeps them lit. Below
threshold nothing happens; at threshold the gate latches on one side and
chatters on the other.

Two fixes, both free:

- **Size the note-on/note-off hysteresis from the measured LED-induced step**,
  not from a guessed value. Measure the step at E4 with the strips running.
- **Drive the LEDs from the post-gate, slew-limited breath value, not from the
  raw ADC sample.** The strips then cannot respond fast enough to close the loop
  within a gate decision.

The second one is the real fix and it is a single line about which variable
feeds the animation.

### The lights read the instrument's own copy, and nothing else

Stated explicitly because it was never written down and the alternative is
tempting: **the strips and the matrix are driven from the MCU's digitised
breath value, full stop.** They do not — and must not — respond to anything
that has travelled two metres to the module, through the panel GAIN and OFFSET
knobs, and back.

There is no path for that anyway: the umbilical is write-only. But the point is
that there is no *reason* to want one either.

**The lights show what the player is doing, not what the jack is emitting.**
That is the more useful of the two, and it has a consequence worth stating:
**turning the panel gain knob does not change the lights.** The knob scales the
CV for whatever it is patched into; the lights are the instrument's own
indicator of breath effort and stay put. If the two ever appear to disagree,
they are answering different questions.

It also means the whole lighting response is firmware, with no hardware in it.

### Zero, deadband and span — all firmware, all settable

| | |
|---|---|
| **Zero** | The power-on ADC capture, which firmware already takes (ADR 0006) |
| **Deadband** | Zero **plus a noise margin**, below which the lights stay dark |
| **Span** | The breath value that reaches full scale — **a setting**, not a constant |

The deadband is the part that earns its keep. Without it the bottom LED
flickers on sensor noise with nobody blowing, which reads as a fault and is
merely arithmetic. Size it from the **measured** noise at E2 — a few times the
standard deviation — rather than guessing, and the same figure is already
needed for the auto-zero's "quiet" gate, so it is one measurement serving two
rules.

Span as a setting matters because the sensor's 6 kPa range is roughly twice
what real playing produces (ADR 0003), so a fixed full-scale mapping would
leave the top of the display unreachable. The player sets where full brightness
lands, on the display or in the web app, like any other per-channel setting.

## The 8×8 matrix

The real-time board sits at the very bottom tip of the instrument — where
ADR 0007 wants it for maximum acceleration sensitivity — with its LED face
directed out through a window in the oak underside, below the right-hand key
run. Facing the player's downward glance, not the audience.

### It is a generic assignable surface, defaulting to breath

The same shape as the mod channels in ADR 0006: a **sink with a configurable
source**, set from the display and the web app rather than wired to one thing.

| | |
|---|---|
| **Default source** | **Breath** |
| Other sources | IMU tilt, IMU roll, acceleration, note/pitch, any mod channel value, playing state |
| Render modes | Level bar, 2-D dot against a captured zero, centre bloom, whole-field brightness, glyph |
| Per assignment | Palette, orientation, and which edge reads as zero |

**Orientation is configuration, not construction.** Which edge of the grid is
"up" depends on how the board lands in the body at M4, and nobody should have to
rotate a PCB to fix a display that reads sideways. One config field.

**What it can do that nothing else in the instrument can is two dimensions.**
The AMOLED at the top is text, and you are not looking at the far end mid-phrase;
the side strips are a one-dimensional glow. Tilt and roll are two axes, and
ADR 0007's capture-on-press gating means there is a captured zero and a live
deviation from it — which is a dot moving against a centre mark, **with the
deadband drawn on the grid.** That is the assignment to reach for once breath
gets boring, and it is the reason to keep pixel definition in the diffuser
below.

### Alarms are not assignable away

One reserved behaviour on an otherwise generic surface: **alarm states preempt
whatever is assigned.**

The roadmap requires an uncalibrated instrument to be unmissable, stuck-key
suspects to be reported, and the key-chain marker error count to be visible —
because each of those otherwise fails silently and gets blamed on the player for
years. A full-field red X is unmissable and needs no menu.

If the surface were fully generic, a configuration could hide exactly the
information that exists to be impossible to hide. So it cannot be configured
off, in the same way and for the same reason that the brightness cap below is a
hard limit rather than a setting.

### Current: sparse is free, full field is not

> **⚠ 2026-09-21: THE PART IS NOT A WS2812C, AND 960 mA IS OPTIMISTIC BY AT
> LEAST 2.4×.** The Waveshare schematic was unobtainable through four review
> waves and is now banked at
> `datasheets/mechanical/WAVESHARE-ESP32-S3-MATRIX-SCHEMATIC.pdf`. It carries
> **64 instances of `WS2812B-0807`**, `U1`–`U64` — verified by hand, 64
> occurrences in the extracted text, and Waveshare's own wiki says the board
> "is based on RGB **WS2812B**", never the C.
>
> **5 mA per channel is the WS2812C's figure. 12 mA is the WS2812B family's**,
> and both documents are already in this repo:
> `datasheets/led/WS2812C.pdf` — *"The working current of each channel is
> 5mA"*; `datasheets/led/WS2812B-2020.pdf` p.4 — *"Quiescent Current：
> <0.6mA … Working Current **12mA**"*. Read by hand from both.
>
> | per channel | source | 64 LEDs at full white |
> |---|---|---|
> | 5 mA | WS2812**C**-2020 — **the wrong part**, and what the table below uses | 960 mA |
> | **12 mA** | Worldsemi WS2812**B**-2020, banked | **2304 mA** |
> | **12 mA** | XINGLIGHT XL-0807RGBC-WS2812B (2022 rev), an 0807-package WS2812B-protocol part | **2304 mA** |
> | 19 mA | same part, 2024 rev — default 19 mA, settable 1.75–19 mA in 16 steps | 3648 mA |
>
> **Worldsemi does not publish a WS2812B-0807 datasheet at all**, and that is
> established rather than assumed: their site's own machine-readable datasheet
> index enumerates 68 keys covering every published part — `ws2812b-v6/-v7`,
> `-mini`, `-1313`, `-2020`, `-2427`, `-4020`, all of `ws2812c/d/e` — and **there
> is no `0807` key**, while the control URL for `ws2812b-2020-v6` returns a real
> 1.26 MB PDF. The XINGLIGHT parts are banked as **surrogates, named as such**,
> and must never be cited as the 0807's datasheet. `matrix-led-current` stays
> **blocked** in `config/figures.yaml`.
>
> **This ADR reaches the right conclusion through the wrong number — and the
> binding constraint is not the one it names.** The 1 A R-78E5.0 is not what
> stops the matrix first. On the dev board itself, all 64 LEDs draw through a
> single **`B5819WS` Schottky in SOD-323**, whose datasheet
> (`datasheets/discrete-and-power/B5819WS.pdf`) gives `I_F(AV)` 1 A but
> **`P_D` = 200 mW and `RθJA` = 500 °C/W**. `[calc]` At `V_F` ≈ 0.46 V that is
> **435 mA at 25 °C and 283 mA at a 60 °C interior** — five to thirteen times
> under the real full-field current, and two to three times under even the
> 960 mA below. Behind it, the `ME6217C33M5G` LDO's printed 800 mA is
> *"guaranteed by design"* and not production-tested (its own Note 4), and
> derates to **~250–500 mA** on a SOT-23-5 at 210 °C/W.
>
> **So the brightness cap is right and its justification should change.** It is
> not "the matrix nearly exhausts the instrument's regulator"; it is "the matrix
> at full field is several times what the dev board's own power path can pass".
> Which is exactly what Waveshare's wiki warns, five times on one page: *"the
> LED brightness should not be set too high, it will cause a rapid temperature
> increase, which can result in damage to the board."* **Rewrite the argument
> against the real constraint; measure the actual draw at E1, which now beats
> any further document hunt.**
>
> What the schematic settles firmly: **the 64 LEDs run from 5 V, not 3V3** —
> every VDD on net `VCC_5V`, no regulator or switch in between. That was a
> strong inference and is now read off a schematic. But `VCC_5V` is USB `VBUS`
> through the `B5819WS`, so it is a diode drop below 5 V, and there is **no
> decoupling anywhere inside the array** — total `VCC_5V` capacitance is
> 11.1 µF, all clustered on the back.

WS2812C-2020 draws **5 mA per channel**, so 15 mA per LED at full white and
960 mA for all 64 — **this is the wrong part's figure and it is at least 2.4×
too low; see the note above.** Converted to the +12 V umbilical through the
buck (×0.49):

| Matrix state | mA @ 5 V | ≈ mA @ 12 V |
|---|---|---|
| Idle — all off, drivers powered | ~40–64 *(estimated, measure at E1)* | ~20–31 |
| One dot at full brightness | +5 | +2 |
| Eight-pixel bar at 25 % | +10 | +5 |
| Breath bar, full field, single hue at 50 % | +160 | +78 |
| **Full field white** | **+960** | **+470** |

**The useful content is nearly free; the pathological content is not.** A dot or
a bar costs single-digit milliamps on top of an idle draw that is being spent
either way. Full-field white is 4.8 W at the LEDs — on its own, roughly the
dissipation of the entire rest of the instrument.

It is also **more than the instrument's 5 V regulator can supply.** The matrix
shares the 1 A R-78E5.0 with both dev boards, which take roughly 330–400 mA
between them, so a full-field matrix would ask for about 1.36 A from a 1 A part.
The rack's supply is on the far side of a 2 m cable and that regulator, and has
no say in the matter.

**So the clamp is the shared thermal budget above, not a per-device brightness
cap.** This ADR previously clamped only the strips, which was wrong in two ways:
it left the matrix uncovered, and a per-device cap cannot see that both are
drawing at once.

**And the blank-at-boot rule matters more here than for the strips.** The
failure in the strips' case was that a brownout resets the MCU and the WS2815s
latch. The matrix is physically *on* the MCU that resets, so it latches too, and
it is the more visible of the two. Blanking both is the first act at boot.

### The diffuser is a different problem from the side panels

The side panels are **frosted** precisely to blur the strips into a glow. An 8×8
wants the opposite: enough diffusion to kill hot spots, little enough to keep 64
pixels distinguishable. At 2.6 mm LED pitch a 10 mm standoff blends adjacent
pixels into mush.

**The default assignment is forgiving and the interesting one is not.** A breath
bar reads perfectly well through heavy diffusion; a 2-D IMU dot against a
deadband does not. So prototype against the demanding case — board close to the
window, a thin diffuser rather than a thick frost, possibly a light-guide grid —
and fall back to the forgiving one only if that proves impossible.

### Construction constraints, which belong in CAD now

- **The carrier needs a ~22 mm cutout** under the board, because the LED face
  points at the carrier and the light has to pass through it. Free on a 2-layer
  board, impossible to add later.
- **Confirm which face carries the matrix relative to the header rows** when the
  board arrives. If the geometry is wrong, the fallback is mounting the board on
  the carrier's underside, and failing that a flying harness for 14 signals,
  which is ugly enough to be worth checking early.
- **A window in the oak underside** below the right-hand key run, clear of the
  thumb keys and the U-bolt. It is a through-cut in a flat part, so the
  laminated construction gives it for free (ADR 0009).
- **A USB-C slot at the tail**, which the instrument needs regardless — flashing
  and USB MIDI both require it in a body that cannot be opened. Keep that edge
  of the board at the tail face.

## Diffusion is a prototype question

Frosted acrylic close to an LED shows the LED. Even illumination needs either
distance between emitter and diffuser, or enough density that the dots overlap
before they reach it.

The cavity gives roughly 20 mm to play with. Whether 60/m at that distance reads
as a continuous glow or a row of points is not answerable from here, and it is
cheap to settle: a length of strip and an offcut of the intended acrylic,
held at a few distances. Do that before committing to a density or a channel
depth.

Visible points are not automatically wrong — a row of discrete lights can look
deliberate. But it should be a choice.

## Grounding

LED current is switched and pulsed, and its return flows in `PWR_GND` alongside
the instrument's other power current.

**This is precisely why the analog breath channel has its own sense return**
(ADR 0003). Without `AGND`, the light show would appear on the breath CV — a
34 mV ground offset that moves with the animation. The lighting decision
validates that choice rather than complicating it.

The breath buffer and sensor now live at the bottom with the real-time board
(ADR 0003), so there is no long analog run to keep clear of. Keep the LED return
off the analog section's local ground at that end, and give the SPI key chain
its own ground return per signal where it shares a channel with the strips.

### Breath is protected. Pitch is not — so hold the current constant.

`AGND` protects the breath channel and does nothing for pitch, which is two
metres away in the module and reached through the +12 V rail rather than
through a ground. Four independent routes were found by which LED current
reaches the pitch jack — the offset reference divider, a shared reverse-polarity
diode, the module's internal ground and the rack's bus ground — adding to more
than every static term in ADR 0006's precision budget put together, and unlike
those terms **they move while you play**. ADR 0006 fixes the two large ones in
hardware.

This ADR owns the cheapest fix, and it is a firmware rule:

> **Animate by moving light, not by changing how much of it there is.** Render
> a dot, a bar or a field whose *total current* is held constant, and move or
> recolour it. Fades, pulses and whole-field brightness sweeps modulate the
> supply that pitch is referenced to.

It removes the drive term instead of treating the couplings, it costs one line,
and it is also what the thermal clamp wants: a constant-current field is a
budget that is never exceeded rather than one policed after the fact.

Where a fade is genuinely wanted — the boot sequence, a preset change — take it
while no note is sounding.

## Open

- **What the side strips actually do.** Breath level is the obvious driver;
  note, active mod channels and config-mode state are all available. The 8×8
  matrix is settled — generic and assignable, defaulting to breath — and the
  strips could reasonably take the same treatment, which would make this a
  firmware question rather than a design one.
- Diffusion gap and material for the side panels, and separately for the matrix
  window, which wants pixel definition rather than blur. Both are M6 prototype
  questions.

*(Density is settled at 60/m, and the clamp is settled as a shared thermal
budget. Both were listed here before the rack-supply framing was withdrawn.)*
