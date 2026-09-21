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
bonded stack that cannot be reopened, is a liability for no benefit.

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
  LED does not kill everything downstream of it. In a bonded laminated body that
  cannot be opened casually (ADR 0002), that matters more than it would in a
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

**Verify the WS2815's data threshold against its datasheet before committing.**
It is a 12 V part, and if its logic threshold is referenced to 12 V rather than
an internal rail, 5 V shifting will not be enough and the part choice needs
revisiting. Most 12 V addressable strips accept 5 V logic, but "most" is not a
basis for a sealed build.

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

WS2812C-2020 draws **5 mA per channel**, so 15 mA per LED at full white and
960 mA for all 64. Converted to the +12 V umbilical through the buck (×0.49):

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
