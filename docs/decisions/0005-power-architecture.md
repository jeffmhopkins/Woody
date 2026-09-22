# 0005 — Power architecture

**Status:** Accepted

## Context

Output requirements are 0–10V on breath and modulation channels and −2 to +7V on
pitch. Both need rails beyond what USB or a single cell provides directly.

## Superseded approach: onboard battery

The original plan was an onboard rechargeable cell with USB charging, making the
instrument fully self-contained. It was abandoned, and the reasoning is kept
here because it was real work and the constraints could return.

From a single Li-ion cell at 3.0–4.2V it would have required:

- A boost converter to roughly +15V, since a +12V output needs headroom above it
- An inverting supply for the negative rail
- A power-path charger IC (BQ24074-class, not a bare TP4056) so the instrument
  runs while charging instead of browning out
- Cell protection, and lithium safety handling for a cell sealed in a wooden box
  held against the player's face

Three problems bit:

- **Noise.** Switching converters put ripple on the rails and that ripple lands
  directly on the CV outputs — as tuning instability on pitch, as hiss on
  breath. The fix (boost to +18V, LDO down to +15V for the analog rail) costs
  efficiency.
- **Power budget.** ESP32-S3 40–80 mA, display backlight 20–100 mA, op-amps
  10–20 mA, and the acrylic LEDs potentially dwarfing all of it at ~60 mA per
  WS2812 at full white. Boosting is lossy. Roughly 400 mA reflected at the cell,
  around 5 hours from 2000 mAh.
- **Weight and balance.** The cell is the single heaviest component, and a
  nose-heavy wind controller is exhausting within twenty minutes.

## Decision

**Power the instrument from the Eurorack supply, over the umbilical (ADR 0004).
No battery.**

The rack already provides ±12V, regulated and filtered. The instrument takes
+12V up the cable and derives 3.3V locally with a small buck converter.

### Physics settles the output range

A rail-to-rail op-amp on a +12V rail swings to roughly +11.5V under light load;
conventional parts considerably less. **0–12V is not achievable from rack power
— the design target is 0–10V.** That is also what Eurorack inputs actually
expect, so the outputs are now in spec rather than above it.

Pitch at −2 to +7V is comfortable on ±12V with ample headroom.

A local boost in the module could raise the rails, but it would reintroduce
exactly the switching noise this decision escapes. Not worth it.

### The breath sensor is not on the 5 V rail at all

The section below was written when the breath sensor shared the buck's 5 V rail
with both dev boards. **It no longer does.** The MPXV4006DP is ratiometric to
its supply and the breath path is analog to the jack, so it runs from a REF5050
precision reference buffered by half an OPA2197, straight off +12 V — see
ADR 0003. The breath buffer moved to that same +12 V package.

What remains below still holds for what is left on the 5 V rail: the two dev
boards and the LED data level shifter.

### The rail that matters is 5 V, not 3.3 V

An earlier revision of this ADR specified a 12 V to 3.3 V buck. **That is
wrong**, and the reason is the breath sensor.

The MPXV4006DP is a 5 V part whose output reaches `sensor-full-scale`
(ADR 0003). A buffer
running on 3.3 V would clip the top 30% of the breath range. So the analog front
end needs 5 V, and a rail-to-rail op-amp on 5 V clears `sensor-full-scale`
with margin to spare.

Feeding the dev boards 5 V is also the right way round. Both carry their own
3.3 V regulators and their own USB power paths; driving their `5V`/`VBUS` pins
lets that circuitry do its job, rather than backfeeding a `3V3` pin and
contending with USB when it is plugged in for flashing.

### Why 12 V goes up the umbilical, not 5 V

The rack supplies a regulated +5 V rail alongside ±12 V, so sending 5 V up the
cable and deleting the instrument's buck converter looks attractive. **The drop
maths says otherwise.**

The instrument's load is **~4.1 W in typical play** (the load table below; an
earlier revision of this ADR said 3 W). Over 2 m of 24 AWG, round trip ~0.34 Ω:

| Delivered at | Current | Drop | Arrives as | Error |
|---|---|---|---|---|
| **12 V** | 359 mA | 122 mV cable + 400 mV Schottky + 60 mV | **~11.4 V** | **5%** |
| 5 V | 862 mA | ~290 mV cable alone | ~4.7 V | 6%+ |

The same power at a lower voltage means proportionally more current, and drop
scales with current. At 5 V the instrument would see **~4.7 V** — *outside* the
MPXV4006DP's 5.00 ±0.25 V specification, and that sensor is **ratiometric**, so
supply variation reads directly as breath variation. The earlier revision put
this at 4.80 V, just inside the window, on the 3 W load figure that was wrong.

That argument is now historical rather than load-bearing: the sensor no longer
runs from the buck's 5 V rail at all (see above; it runs from a REF5050 off
+12 V). What survives is the general point, which still decides the umbilical.

This is simply why power distribution uses higher voltages, and it applies at
two metres as much as at two kilometres.

Two further reasons the question does not arise:

- **The WS2815 strips need 12 V anyway** (ADR 0014). A 5 V-only umbilical would
  force 5 V strips, giving up the backup data line that matters in a sealed
  body — and drawing more current while doing it.
- **The R-78E5.0 is a 3-pin through-hole module**, among the lowest-effort parts
  in the design. Deleting it saves almost no build effort to begin with.

### The module's 5 V splits: bus rail for logic, local regulator for the DAC

The module sits in the rack on a short ribbon with negligible drop, so the bus
+5 V rail is free and convenient. It is used — but **only for the 74AHCT125
level shifter**, around 10 mA.

**The DAC gets its own LM317LZ set to ~5.21 V, off its own reverse-protection
diode on the +12 V rail.** Its divider value is selected on the bench at E7, not
from a tolerance stack — see ADR 0004.

**The reason is headroom, not accuracy**, and this ADR said the opposite. It
claimed "the DAC8568's full-scale output *is* its supply, so a rail the rack is
allowed to move ±5 % moves the top of the pitch range and the pitch calibration
with it." That is true of a DAC run from its supply as its reference, and the
DAC8568 is not run that way: its **internal 2.5 V reference with reference gain
2** puts full scale at 5.000 V, set by the reference and not by AVDD (ADR 0006).

What AVDD does decide is whether the output buffer can *reach* 5.000 V. The
rack's +5 V rail at −5 % is 4.75 V, which cannot, and the top of the pitch
range would quietly compress. So the local regulator stays, and the number that
matters is a floor with a 5.5 V ceiling above it — which is exactly the thing
E7 measures, and exactly why a tolerance stack was the wrong tool.

The target rack supplies +5 V, so the level shifter's rail is a **requirement,
not an option**. No jumper, no unpopulated fallback footprint. A module that
also worked in cases without a +5 V rail would be engineering for a case this
instrument is never in (see the design scope in the README).

### The load table, measured against nothing yet

Every number in this section was low. ADR 0005 originally said 250 mA and
ADR 0004 ~275 mA; five independent rebuilds during review came back between
390 and 650 mA, and an adjudication pass settled it. **Those figures were a good
estimate of a different instrument** — one with no 8×8 matrix, no WS2815
quiescent current, and no lighting clamp.

| State | 5 V rail | 12 V direct | **Umbilical** | Body heat |
|---|---|---|---|---|
| Quiescent — booted, radio off, LEDs blanked | 180 mA | 123 mA | **212 mA** | 2.4 W |
| Typical play | 226 mA | 248 mA | **359 mA** | 4.1 W |
| Typical + live config over WiFi | 336 mA | 248 mA | **414 mA** | 4.7 W |
| **Clamp-legal worst** | 928 mA | 119 mA | **579 mA** | 6.5 W |
| Clamp fails, strips latched full white | 1023 mA | 1023 mA | **~1522 mA** | ~17 W |

**The 5 V rail is where the danger is, not the umbilical.** The same 3 W of
light costs 531 mA on the umbilical if it is spent on the strips and 579 mA if
spent on the matrix — a **9 %** difference. But on the 5 V rail it is **328 mA
versus 928 mA**, a factor of three, because the strips run from 12 V directly
and the matrix runs through the buck. The 1 A regulator lives on that rail.

Two arithmetic conventions to keep: convert at the **arriving** voltage, not
12.00 V, because the 5 V branch is a constant-power load and only ~11.4 V
arrives; and the buck is **~90 % efficient** at a 12 V input, not the 85 % this
document used — 85 % is the 28 V-input figure.

*(ADR 0014's ×0.49 umbilical conversion factor survives by coincidence: two ~6 %
errors in opposite directions.)*

**None of this is measured.** E6 measures the real draw with a current probe,
and every number above is superseded the moment it does.

### Power tree

```
umbilical +12V ──┬── WS2815 LED strips          (direct, no conversion)
                 │
                 ├── REF5050 5.000V ──[OPA2197 ½]── MPXV4006DP breath sensor
                 │
                 ├── OPA2197 V+  (½ reference buffer, ½ breath buffer)
                 │
                 ├── 12V→5V buck A ─┬── real-time board 5V pin
                 │                  ├── 8×8 matrix (via that board)
                 │                  └── LED data level shifter
                 │
                 ├── 12V→5V buck B ──── display board 5V pin
                 │
                 └── TVS array / LC filter at entry  (no fuse — see below)

real-time board 3V3 out ──┬── 74HC165 chain
                          ├── breath ADC
                          └── I2C pull-ups
```

**3.3 V does not need its own converter.** The loads on it are the shift register
chain (microamps), the ADC (milliamps) and pull-ups, all comfortably inside the
headroom of the real-time board's onboard regulator.

**Two bucks, not one.** ADR 0013 asks for a regulator per board so the display
board's WiFi bursts are absorbed locally instead of reaching the analog section,
and the load table above gives the second reason: 928 mA of clamp-legal worst
case does not fit behind one 1 A part. Split, the real-time side carries the
matrix and the display side carries its own transients, and neither is near its
rating. The R-78E5.0 is a three-pin module — the second one costs a footprint.

**There is no fuse at the umbilical entry.** An earlier revision of this ADR put
a polyfuse here to stop an internal short pulling on the rack's +12 V rail. That
job is done — better, faster and without the thermal hysteresis — by the
module's load switch, which sits at the *source* end of the umbilical where the
instrument's own faults cannot bypass it. See "Set the limit at 1.0 A, and
delete the polyfuse" below for why keeping both was worse than keeping one.

### There is no power switch on the instrument. Switching happens at the module.

An earlier revision of this ADR specified a panel switch on the instrument that
**switched the buck converter's enable pin, not the +12 V rail** — carrying no
current, so it could be a tiny slide switch anywhere convenient. A design review
found that it cannot be built as written and would not work if it could.

**The regulator has no enable pin.** The Recom R-78E5.0 is a 3-pin SIP on a 7805
footprint: IN, GND, OUT. The switch as specified has nothing to switch.

**And switching the buck would not turn the instrument off.** The WS2815 strips
run on raw umbilical +12 V, *upstream* of the buck, because they need 12 V and
the buck makes 5 V. Killing the buck leaves roughly 120 mA of strip quiescent
draw and the strips **holding their last latched colours** — an instrument still
lit, still drawing current, with its logic dead.

The version that actually works is a high-side P-FET on raw +12 V, which means a
FET, a gate network, and a fat conductor routed to a panel location inside a
body that has to be opened up to change the decision (ADR 0009).

**So `SW-PWR-INST` is deleted.** Nothing on the instrument switches anything.

### The module's toggle drives a current-limited load switch

The module panel already carries a rated SPST toggle (ADR 0004), one reach away
in the same rack the instrument is patched into. That is upgraded rather than
duplicated.

**The toggle drives a current-limited load switch on the umbilical +12 V
feed**, rather than breaking the current itself. (The part is settled below,
and it is *not* a TPS2553.) That buys two
things the bare toggle does not have:

- **Inrush limiting.** The instrument's bulk capacitance is a near-short at the
  instant of connection. A toggle takes that surge across its contacts every
  time; a load switch ramps the output instead.
- **Short-circuit foldback.** A fault in the umbilical — a crushed cable, a
  connector half-inserted — is current-limited at the module instead of pulling
  on the rack's +12 V rail and browning out every other module in the case.

### Set the limit at 1.0 A, and delete the polyfuse

**1.0 A, latch-off, with a programmed ramp — and the ramp is the tracked
figure `loadswitch-gate-cap`, not a number stated here.**

> This line specified **50–100 ms** until 2026-09-22. It was not achievable
> with the chosen part and had not been since the datasheet was banked; the
> warning below said so while the specification above it went on asserting
> it. A decision record that states a spec its own next paragraph refutes
> has two readers: one who stops at the bold line, and one who does not.
> The bold line now cites the figure, so it cannot drift again.

> **⚠ The ramp half of that specification is not achievable with the chosen
> part, 2026-09-21.** `164112fc.pdf` is now banked
> (`datasheets/discrete-and-power/LT1641.pdf`) and the LT1641's `GATE` pull-up
> is specified **−5 / −10 / −20 µA** `[p.2]`, corroborated by the DC1354A demo
> guide. That is a **4:1** current window, and no single gate capacitor can hold
> a ramp inside a 2:1 time window when the current that drives it varies 4:1.
> `C-GATE` at 82 nF centres the *typical* at 98 ms, inside this spec; the
> **guaranteed envelope is 49–197 ms** (`hardware/module/power-entry/power-entry.md`).
>
> **This ADR has to choose.** Either widen the specification to **50–200 ms**,
> which costs nothing the analysis below depends on — the 75 ms start it cites
> is a *current-limited* start, not a ramped one, and the fault timer is sized
> against the 47.5 ms hot-plug case rather than against the ramp — or program
> the ramp with something other than the part's internal pull-up. **Not decided
> here; raised against this ADR by the wave that read the datasheet.**
>
> The 1.0 A half is confirmed and sharpened: the sense threshold is
> **39 / 47 / 55 mV** `[p.2]`, so `R-ILIM` at 50 mΩ gives **0.78 / 0.94 /
> 1.10 A**. The E6 bench measurement this section already calls for is what
> closes that, and the ±17 % spread is a stronger reason for it than the one
> given.

**The upper bound this used to quote was arithmetic from a broken row.** It said
0.9–1.13 A, with 1.13 A taken as what a brownout-latched full-white strip set
draws — but that row of the load table was inconsistent three ways (its two
component currents summed to 1522 mA, not 1132; and its own power figure did
not follow from either). Corrected, a latched full-white failure is **~1.5 A**,
which is *above* the etherCON contact's 1.5 A rating rather than comfortably
below it.

So the limit is not bracketed from above by that state any more — it is set
from below, by the clamp-legal worst case of ~630 mA plus ramp current, and
from above by the connector. **1.0 A sits between them**, and the consequence
of the correction is that a latched-full-white instrument now *trips the
limiter* instead of sitting just under it, which is the behaviour wanted. E6
measures the trip as well as the load.

**500 mA was below typical play**, never mind the clamp-legal worst. Reviewers
also disagreed about whether it would prevent boot: one showed it would not,
because available current exceeds demand at every point on the way up so the
node rises monotonically and the buck starts at ~17 ms. **It boots — in about
75 ms of constant-current start**, which is long enough to trip a USB-class
fault timer. The prescription is the same either way: a programmed ramp and a
fault timer longer than it.

**And the instrument-end polyfuse is deleted.** An earlier revision of this ADR
called it complementary to the load switch. It is not:

- Its hold current derates to **~350–375 mA** at the documented interior rise —
  *below typical play*.
- It sits **downstream of the module's limiter**, so it can never reach its trip
  current and protects nothing.
- A polyfuse above hold does not trip cleanly; it creeps into current-limiting,
  which is the first term in the thermal-runaway loop ADR 0014 describes and
  believes it deleted. **ADR 0014 added the load switch and never removed the
  device it named as the problem.**
- The obvious part number is a 6 V-rated part on a 12 V rail.

Deleting it is a negative-cost change: one fewer part, 50 mW less inside the
sealed body, and one less nuisance-trip mechanism.

**The part is not a TPS2553.** That is a **2.5–6.5 V USB power switch** with a
7 V absolute maximum, specified here on a +12 V rail — roughly 66 % over
abs-max, and it would not survive first power-on. Five review documents found it
independently. An earlier revision of this ADR defended it on *package* grounds
and never stated its voltage rating, which is the tell.

The replacement is not a substitution, because **every modern one-chip 12 V
eFuse checked fails the package policy** — TPS2592Ax is VSON-10, TPS27S100 is
HTSSOP with a thermal pad, ST's STEF01 is HTSSOP-14 with a pad. So:

**LT1641-1CS8 (SO-8, 9–80 V) driving an external N-FET, with a sense resistor.**
Note the suffix: **`-1` latches off and `-2` auto-retries**, and auto-retry into
a persistent fault reproduces the oscillating-protection behaviour this design
exists to avoid.

> **⚠ LM5069MM and LTC4210 are NOT interchangeable with the LT1641 any more,
> 2026-09-22 — this line used to say they were "equally valid".** That was
> true while this was a package-policy survey and false from the moment the
> design started taking numbers out of one datasheet. **Every constant in the
> load switch is LT1641-specific**: `C-GATE-LOADSW` from `I_GATE` −5/−10/−20 µA
> `[p.2]`, `C-TIMER-LOADSW` from the 3 µA/80 µA TIMER pair into a 1.233 V
> threshold `[p.8]`, `R-FB-HI`/`R-FB-LO` from `V_FB` 0.5 V and `V_FBH` 1.313 V
> being set by the *same* divider, `R-ILIM` from the 39/47/55 mV sense window,
> and the 240 mA foldback floor from the 47 mV → 12 mV law `[p.5, Fig. 7 p.9]`.
> The LTC4210 has no FB foldback pin in this form, so the fixed 0.381 ratio
> does not exist for it; the LM5069's thresholds and timer currents are
> different numbers entirely. **Swapping the part discards all five values and
> silently re-opens the ramp arithmetic.** Neither alternative is banked in
> `datasheets/MANIFEST.csv`, and this sentence was the only mention of either
> part anywhere in the corpus.

Programmable ramp rate and a programmable fault timer come with the part, which
is what the 75 ms start above needs. **Both are now programmed**:
`C-GATE-LOADSW` and `C-TIMER-LOADSW` — the tracked figures
`loadswitch-gate-cap` and `loadswitch-timer`, sized in
`hardware/module/umbilical-load-switch/umbilical-load-switch.md` against
the datasheet rather than against search results, with the ramp caveat above.
The fault timer's binding case turned out to be the **hot-plug** — 47.5 ms
entirely in current limit, against a worst-case timer of 95.6 ms — and not the
cold start at all.

The toggle now carries no load current, so its rating stops mattering — it
drives an enable pin. It stays a rated part anyway because it is already
specified and costs nothing to keep.

**The honest cost of deleting the instrument switch:** there is no way to kill
the instrument without reaching the rack. For a tethered instrument whose
outputs go nowhere but that rack, there is nowhere else to be standing (see the
design scope in the README).

> ~~**Pull down the module's breath receive input**, so that an instrument which
> is switched off — or unplugged — presents 0 V rather than a floating buffer
> output. One resistor, and it means powering down the instrument silences the
> patch instead of leaving a stuck level (ADR 0003).~~
>
> **Withdrawn 2026-09-21. Do not fit this resistor.** `R-PD-BREATH` was a
> single 100 kΩ element *across* the in-amp's two inputs, and ADR 0003 deleted
> it for two reasons: it attenuated the signal by 1–17 % depending on where the
> gain sat, and a purely differential element gives the in-amp's inputs **no DC
> path to ground at all**, so with the instrument unplugged input bias current
> ramps both inputs until the amplifier saturates — a rail, not the 0 V this
> paragraph promised.
>
> **What replaces it:** `R-BIAS-INAMP`, two 1 MΩ resistors from each input to
> module `AGND` — a common-mode return, not a differential shunt
> (`breath-receive-stage.md`). It gives the bias current its path and costs no
> signal.
>
> **And it does not deliver 0 V at the jack either**, which is the part this
> paragraph got wrong independently of the part choice. With the instrument
> absent the in-amp rests at its trimmed `V_REF`, and the panel gain-and-offset
> stage puts the jack at the OFFSET knob's position, anywhere in ±5 V. That is
> now recorded as an accepted consequence in ADR 0006's power-on table rather
> than promised away here.

### USB power for the bench, not as a feature

**OR the umbilical power with USB power** — it costs a diode, and it means the
instrument runs on the bench during development without a rack attached. That
is worth a diode.

It is not a standalone mode and should not be designed toward. The instrument's
outputs are CV; unplugged from the module it has nowhere to send them.

## Consequences

- The highest-risk electrical subsystem in the project is deleted outright.
- The instrument is tethered during CV use. Accepted — it is playing into a rack.
- Rack current draw needs budgeting, including the acrylic LEDs, which are the
  least predictable line item.
- Balance is no longer dominated by a battery, but strap attachment points still
  need designing into the oak rather than being added later — with left-thumb
  keys on the underside, the left hand both supports and actuates.
