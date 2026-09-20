# D3 — Missing analog conditioning stages

**Scope.** What signal-conditioning stages *should* exist in Woody and do not. Not
an audit of the stages that do exist — other reviewers have that. This walks each
signal from its physical origin to its destination and asks at every boundary:
can the source drive what comes next, is the bandwidth limited where it must be,
is the level right, is the impedance right, is anything floating in any operating
state, and is one stage being asked to do two jobs.

**Sources read:** `README.md`, `ROADMAP.md`, all of `docs/decisions/`,
`docs/reference/`, `hardware/bom.csv`, `docs/review/`, `docs/log/`.

**Proportionality rule applied throughout:** this is a one-off for the author's
own rack, hand-assembled, with a full bench, rack power, and a body that is
bonded shut and cannot be reopened. Parts are cheap; board revisions are not;
anything inside the instrument is unretrofittable. Findings are weighted that
way, and six of the twenty are explicit ACCEPTs.

---

## Summary

| # | Missing stage | Sev | Verdict |
|---|---|---|---|
| 1 | Inverting/level-shift stage on the ambient-zero DAC channel | Critical | **ADD** |
| 2 | Buffered reference rail for every offset injection in the module | Critical | **ADD** |
| 3 | Pull-up and input filter on all 18 key switches | Critical | **ADD** |
| 4 | Common-mode bias return at the breath receiver | High | **ADD** |
| 5 | Input filter *ahead of* the in-amp (RFI + the module-end 500 Hz pole) | High | **ADD** |
| 6 | Buffer between the breath gain pot wiper and the summing stage | High | **ADD** |
| 7 | Sensor output RC and all analog decoupling on the carrier | High | **ADD** |
| 8 | Reconstruction filter components on all six CV outputs | Med-High | **ADD** |
| 9 | Presence-detector stage for the level shifter's OE gating | Med-High | **ADD** |
| 10 | Source termination on SCLK, CS and both LED data lines | Medium | **ADD** |
| 11 | Mute on the breath channel — the watchdog has no authority over it | Medium | **ADD** |
| 12 | ESD clamp at the *module* end of the umbilical | Medium | **ADD** |
| 13 | The 220 nF at the ADC is doing three jobs; the corner is 120 Hz | Med-Low | **ADD** (value) |
| 14 | ADC spare channel floats; no ratiometric reference | Low | **ADD** |
| 15 | Cable shield has no defined termination | Low | **ADD** |
| 16 | No tie-off rule for unused sections and control pins | Low, free | **ADD** |
| 17 | `R-OPAMP-IN` sits inside the gain network, not outside it | Medium | **ACCEPT** (absorb) |
| 18 | No filter between umbilical +12 V and the instrument's analog section | — | **ACCEPT** |
| 19 | No star-ground / Kelvin return scheme in the module | — | **ACCEPT** |
| 20 | No dedicated gate/trigger output stage | — | **ACCEPT** |

Net new active silicon: **zero new part numbers**. Findings 1, 2 and 6 want three
more OPA2197 channels; `U-OPA-PITCH` is already on the BOM at qty 5 (ten
channels) against eight currently accounted for, so the quantity goes to six
duals. Everything else is passives, one small-signal FET, and one supervisor.

---

## 1. **There is no stage that can make the ambient-zero subtract. A unipolar DAC channel is being asked to null a positive offset, and it can only add.**

**Severity: Critical.** This is not a precision issue — the primary expressive
channel cannot be zeroed at all as drawn.

**Boundary:** DAC channel 6 → `INA821` REF pin (module).

**What goes wrong.** An instrumentation amplifier's transfer function is additive
at REF, universally:

```
Vout = G · (V+ − V−) + Vref
```

At ambient the sensor sits at its own offset — `Vout = VS × 0.04` = **0.20 V**
nominal at VS = 5.000 V (the review's datasheet reading puts it at 0.26 V; either
way it is positive). With BREATH on `V+`, AGND on `V−` and G = 2.13:

```
Vout(ambient) = 2.13 × 0.20 V + Vref = 0.43 V + Vref
```

To null that, **Vref must be −0.43 V**. The DAC8568 spans 0 to +5 V and its
usable window is 0.25–4.75 V. It cannot produce a negative volt. The zero
correction can therefore only push the breath floor *up*.

Consequences, all of them structural rather than marginal:

- **A permanent 0.43–0.55 V floor on the breath jack**, 4.3–5.5 % of the 10 V
  span, into a VCA that is calibrated for 0–5 V that is **9–11 % open with no
  breath**. This is precisely the "VCA drones quietly" symptom the review chased
  through R12 and S5 and attributed to knob-dependence and thermal drift.
- **The continuous auto-zero of ADR 0006 is half-blind.** Thermal offset drift
  moves in both directions over a session; the correction has authority in one.
- The review flagged this sub-finding explicitly — *"a unipolar 0–5 V DAC channel
  summed additively can only add, and the sensor's offset needs subtracting. Not
  addressed anywhere"* (R12) — and it is still not addressed in ADR 0003,
  ADR 0006 or the resolution log. It survived because the *other* half of R12
  (do the subtraction in the instrument) was correctly rejected as unbuildable,
  and the rejection took this half with it.

The buffer that ADR 0003 already requires on this channel (*"driven from a
low-impedance buffer rather than a divider"*) is the stage that should have done
this job and is not configured for it. One op-amp channel, wired as a follower,
cannot invert. Wired as an inverter, it can.

**Circuit.** Reconfigure the already-budgeted buffer channel as an inverting
attenuator, with the smoothing pole ahead of it:

```
DAC ch6 ──[100k]──┬──[40k]──┐
                  │         │    ½ OPA2197 (±12 V)
                [1.5µF]     ├──|−\
                  │         │   |  >──── INA821 REF
                 GND    [10k]───|+/ ← +in to AGND-side analog ground
                                └─ 10k feedback
```

- Gain −0.25: DAC 0→4.75 V maps REF to 0→**−1.19 V**, covering the 0.43 V null
  plus 0.76 V of drift headroom in the correct direction.
- Resolution 1.19 V / 65536 = **18 µV per LSB** at the output, against a 153 µV
  LSB on the 10 V CV span — the zero is finer than the channel it corrects.
- 100 kΩ + 1.5 µF = τ 0.15 s, **1.06 Hz**, which is R12's requested pole on the
  zero channel and has never appeared in an ADR. It stops a re-zero command or a
  DAC glitch landing on the CV as a click.
- **The RC goes before the op-amp, never after.** A series resistor in the REF
  path unbalances the in-amp's output difference network and caps CMRR at
  roughly `20·log(R_ref_internal / R_series)` — a 100 kΩ RC there would leave
  ~ −20 dB. From the op-amp's closed-loop output impedance (<0.01 Ω at DC) the
  same expression gives >120 dB. This ordering is the whole reason the stage
  must be a real amplifier and not an RC plus a resistor.

**Verdict: ADD.** Two resistors, one capacitor, and a rewire of an op-amp channel
that is already on the BOM. Without it the breath channel has no zero.

---

## 2. **The module has no reference rail. Every DC offset in it — the pitch offset trimmer and the breath offset knob — has nothing to sit across but the ±12 V rack rails, which move with the instrument's LED current.**

**Severity: Critical.** This undoes the entire precision-pitch argument.

**Boundary:** wherever a fixed DC is injected — the pitch scaling stage's offset
trimmer, and the breath offset potentiometer.

**What goes wrong.** ADR 0006 resolves pitch offset authority by adding a
trimmer, and never says what voltage the trimmer trims *against*. There is no
reference in the module other than the DAC8568's internal 2.5 V (used internally
only) and the LM317's 5.25 V rail (which exists to feed AVDD). The default — and
what every schematic drawn from these ADRs will do — is a divider or a pot across
the ±12 V rails.

For a gain-2 stage over the 0.25–4.75 V DAC window, the offset term at the output
is **−2.5 V**. Derived proportionally from a rail, its error is
`2.5 V × ΔVrail / 12 V`:

| Rail movement | Offset error | Pitch error |
|---|---|---|
| 0.5 % | 12.5 mV | **15 cents** |
| 1 % | 25 mV | **30 cents** |
| ±5 % (Eurorack rail spec) | ±125 mV | **±150 cents** |

For scale: the LT5400 is called *"the single highest-value precision component in
the design"* and was bought to fight **5.4 cents**; BAV99 was chosen over BAT54S
to avoid **2.4 cents**.

And the rail does not merely drift — **it moves with the light show.** ADR 0004's
power tree puts the module's analog rail and the umbilical feed on the same
1N5817, downstream of it. A 1N5817 carrying the instrument's current drops
roughly 0.32 V at 200 mA and 0.40 V at 400 mA:

```
ΔVf ≈ 80 mV → 0.67 % of 12 V → 16.7 mV of offset error → 20 cents
```

The instrument's current swing is dominated by the WS2815 strips and the 8×8
matrix, and ADR 0014 makes **breath the default source for both**. So the pitch
channel detunes by up to 20 cents in sympathy with how hard the player is
blowing. That is a musical failure mode, correlated with playing, that no
calibration can remove.

The same omission on the breath offset knob is smaller but on the channel that
the whole AGND argument exists to keep clean: a rack's ±12 V rails typically
carry 10–50 mV of ripple and switching hash; through a ÷4.8 divider that is up to
**10 mV on the breath CV**, at supply-ripple frequencies, i.e. audible hum on a
sustained note. The review reached this (R26 second half) and marked it *"correct
and important. Keep it"* — and it was never written into an ADR.

**Circuit.** A buffered 2.5 V rail, taken from the DAC's own reference:

```
DAC8568 VREFIN/VREFOUT ──┬──|+\  ½ OPA2197 ──┬── VREF_MOD (+2.5 V)
                         │  |  >──┐          │
                         │  |−/   └──────────┘  (follower)
                        [100nF]
                                              ┌─[10k]─┐
                    VREF_MOD ──[10k]──|−\     │       │
                                      |  >────┴── VREF_MOD_N (−2.5 V)
                              GND ────|+/  ½ OPA2197   (inverter, only if a
                                                        bipolar breath offset
                                                        is wanted)
```

- Pitch offset trimmer: multiturn cermet across ±2.5 V, into the summing node
  through a fixed resistor, trim range 5–10 % per ADR 0006.
- **Both the gain and the offset now derive from the same reference**, so
  reference drift becomes a pure gain term on the whole 1 V/oct line: 5 ppm/°C ×
  10 K = 50 ppm = **0.09 cents**. Better than the trimmer's own 2.4 cents, so it
  stops being the limiting term.
- Breath offset pot across ±2.5 V (or 0…+2.5 V if the floor only ever goes up).
- **Rollback if the DAC's reference output proves too weak or too noisy to
  share:** a second REF5050AIDR — already a qualified part number in this project
  — off the protected +12 V. 3 ppm/°C, uncorrelated with the DAC's reference, so
  the combined drift is 8 ppm/°C = 0.24 cents. Still an order inside the trimmer.
- Reserve both footprints. The choice is a bench measurement at E7, not a
  judgement call now.

**Verdict: ADD.** One op-amp channel (two if bipolar offset is wanted), a
footprint for the fallback reference. This is the highest-value missing stage in
the module.

---

## 3. **Eighteen key switches drive CMOS inputs with no pull-up and no input filter. Every key input floats when its key is open.**

**Severity: Critical.** Also unretrofittable — these boards are bonded inside the
body.

**Boundary:** mechanical switch → 74LVC165 parallel input, on four satellite
boards, over a 14-inch loom sharing a side channel with WS2815 power and 800 kHz
data.

**What goes wrong.** A 74x165 parallel input has no internal pull-up. An SPST
switch to ground with no pull-up leaves the input **floating whenever the key is
not pressed**, which is most of the time for most keys. The BOM has no pull-up
line item; neither ADR 0001, 0002 nor 0010 mentions one. The only key-chain
passives specified are `R-TERM-CHAIN` (clock/latch termination) and
`C-DECOUPLE-165`.

Two compounding facts already established in this repo make a floating key input
worse here than in a generic design:

- ADR 0014 puts both LED strips in **the same two side channels as the looms**,
  which is the only route down the body.
- ADR 0001's asymmetric debounce **fires on the first closed sample**, so one
  corrupted bit is one spurious note-on at full velocity.

Arithmetic for the coupling. Two wires ~10 mm apart for ~350 mm give on the order
of 10–20 pF of mutual capacitance. A WS2815 PWM edge on the 12 V feed has a slew
of roughly 120 V/µs:

```
i = C · dV/dt = 15 pF × 120 V/µs = 1.8 mA
```

Into a node with **no defined impedance**, that is a full rail-to-rail excursion
clamped only by the input protection diodes. Even *with* a 10 kΩ pull-up and no
capacitor, 1.8 mA × 10 kΩ demands 18 V — the input sits at a false level for the
duration of every edge. If one of those coincides with `SH/LD` or with the
32-clock shift, ADR 0001's own analysis says what happens next.

This is also the other half of S8: the aluminium plate bonding fixes the
touch-injection path, and nothing fixes the coupling path.

**Circuit** — three parts per key, all 0805, on boards that are being designed
anyway:

```
3V3 ──[10k]──┬──── 74LVC165 input
             │
           [10nF]
             │
            GND      switch ──[100R]── same node, other side to GND
```

- **Press:** the 10 nF discharges through 100 Ω in ~1 µs. The leading edge stays
  instant, so the asymmetric debounce is preserved exactly.
- **Release:** the node rises with τ = 10 kΩ × 10 nF = 100 µs and crosses
  `V_IH` = 2.0 V at **93 µs** — a free hardware release filter, in the direction
  the design already wants it.
- **LED rejection:** pole at 1.6 kHz gives **−54 dB at 800 kHz**; the 180 pC of
  injected charge from a 12 V edge lands in 10 nF as **18 mV** instead of a logic
  level.
- Packaging: a 9-pin SIP resistor network per cluster board (or 8 × 0805) plus
  eight caps. Four boards. Under $5 total.

**Verdict: ADD.** The pull-ups are not optional — the chain does not work without
them — and the RC is the cheapest signal-integrity insurance in the project,
bought before the body closes.

---

## 4. **The breath receiver's inputs have no common-mode bias return. In the instrument's normal off state the in-amp's inputs are floating.**

**Severity: High.**

**Boundary:** umbilical BREATH/AGND pair → INA821 inputs (module).

**What goes wrong.** Three rules combine into a floating node, and each is
individually correct:

- R35, adopted into ADR 0003: *"At the module end [AGND] connects to the
  receiver's inverting input and nothing else — not to a ground pour, not to a
  stitching via."*
- ADR 0003: the pulldown goes **differentially** across BREATH–AGND, not on one
  leg.
- ADR 0003: the receiver is a buffered in-amp with gigaohm inputs.

The result is that the only DC connection between the in-amp's input pair and
module ground is... none. A 100 kΩ resistor *between* the two inputs sets the
differential voltage and does nothing for the common mode. ADR 0004 states that
"module alive, instrument off" is **the state the instrument spends most of its
life in**, and in that state the cable is unpowered or unplugged and both inputs
are open.

Input bias current then charges the common-mode node. At ~0.4 nA into the ~50 pF
of the input node and connector stub:

```
dV/dt = 0.4 nA / 50 pF = 8 V/s
```

The inputs leave the in-amp's common-mode range within about **1.5 seconds** and
the output parks against a rail or at an indeterminate level. ADR 0005's promise
— *"an instrument which is switched off — or unplugged — presents 0 V rather than
a floating buffer output"* — is not delivered by a differential pulldown alone.

**Circuit.** One resistor, plus a value and placement change on the pulldown that
is already specified:

```
etherCON pin 1 (BREATH) ──[10k]──┬──────────── INA821 +IN
                                 │
                               [1M]  ← differential, on the CONNECTOR side
                                 │
etherCON pin 2 (AGND) ───[10k]───┴──┬───────── INA821 −IN
                                    │
                                  [1M]  ← common-mode bias return
                                    │
                            module analog GND
```

- **Bias return, 1 MΩ.** At a 50 mV instrument-to-module ground difference it
  carries 50 nA, which develops **8.5 nV** along the AGND conductor's 0.17 Ω —
  against a 153 µV LSB, five orders of margin. R35's rule survives intact in
  substance; what it must not have is a *low-impedance* path, not *no* path.
- **Raise the differential pulldown from 100 kΩ to 1 MΩ and move it to the
  connector side of the protection resistors.** As specified, the 10 kΩ series
  resistors and a 100 kΩ pulldown form a divider: `100/(100+10+10)` = **0.833**,
  a silent 17 % attenuation of the breath channel sitting ahead of the gain
  trim, made of three ordinary 1 % parts. At 1 MΩ on the connector side it is
  **0.98** and the temperature coefficient of the attenuation stops mattering.
- Cost: input offset current (~0.5 nA) across 1 MΩ is 0.5 mV differential →
  1.1 mV at the in-amp output → well inside the ambient-zero's authority, which
  finding 1 restores.

**Verdict: ADD.** One resistor and a value change on one that already exists.

---

## 5. **There is no filter ahead of the in-amp. The "band-limit at both ends, around 500 Hz" that ADR 0003 requires has no components at either end, and at the module end a filter after the amplifier would not do the job anyway.**

**Severity: High.**

**Boundary:** the 2 m umbilical → INA821 inputs.

**What goes wrong.** ADR 0003 states the requirement — *"Band-limit at both ends,
around 500 Hz"* — and the BOM contains no capacitor implementing it anywhere in
the breath path except `C-AA-ADC`, which is on the ADC branch inside the
instrument and does nothing for the CV path or the receiver.

The module end is the one that cannot be deferred, because of *where* the filter
goes. An instrumentation amplifier's input stage rectifies RF: out-of-band energy
on the inputs is demodulated into a DC shift at the output, and a filter placed
after the amplifier cannot undo it. The review said this in one line — *"the two
ways it does become in-band are both design errors, not physics: rectification if
the filter sits downstream of the amplifier"* — and no ADR carried it forward.

The disturbers are not hypothetical. The instrument has a 2.4 GHz radio; ADR 0012
and the latency budget both anticipate WiFi TX bursts as the remaining coupling
path and plan to measure rail transients. But a TX burst is amplitude-modulated
at the packet envelope, so in-amp rectification converts it directly into an
**audio-band step on the breath CV**, by a mechanism that scoping the rail will
not find. The SPI pairs share the same jacket, and the cable's shield has no
defined termination (finding 15).

**Circuit.** The 10 kΩ protection resistors are already in each leg, so the
filter is two capacitor values:

```
+IN ──┬──[150pF]── AGND_MODULE
      │
   [15nF]          ← differential
      │
−IN ──┴──[150pF]── AGND_MODULE
```

- Differential pole: `1/(2π · 20 kΩ · 15 nF)` = **530 Hz** — this *is* the
  module-end band limit ADR 0003 asks for, placed in the only position where it
  also prevents rectification.
- Common-mode poles: `1/(2π · 10 kΩ · 150 pF)` = 106 kHz, with
  `C_diff / C_cm = 100`, so mismatch between the two CM capacitors cannot convert
  common mode into differential anywhere inside the passband. (Use 5 % C0G for
  the 150 pF parts; the 15 nF can be X7R.)
- **The CM capacitors return to the module's analog ground, not to AGND.**
  Returning them to AGND puts their current in the sense return.
- The instrument-end pole is the RC in finding 7: 1 kΩ + 330 nF at the sensor
  output = 482 Hz.

**One honest cost to record.** Two 500 Hz poles contribute `2 × 1/(2π·500)` =
**0.64 ms** of group delay, where the latency budget allots *"< 0.2 ms"* to
"buffer, cable, in-amp, output filter" combined. Breath at the jack becomes
~3.0 ms rather than 2.4 ms, against a 5 ms target and a 5–15 ms fastest gesture —
still comfortable, but the budget line understates the filters it mandates by 3×.
If that matters, put the instrument pole at 1 kHz (159 µs) and keep the module
pole at 500 Hz, for 0.48 ms total; the sensor's own 159 Hz corner means neither
choice costs signal.

**Verdict: ADD.** Four capacitors, and a documentation correction to the latency
budget.

---

## 6. **The breath gain potentiometer's wiper drives the offset summing stage directly. A pot wiper is a high-impedance node with no buffer.**

**Severity: High.**

**Boundary:** `POT-BREATH` (gain) wiper → offset summing stage → breath jack.

**What goes wrong.** ADR 0006 puts the knobs *"directly in the analog path"* with
*"gain first, then offset"*, and specifies the reverse ordering *"makes the two
controls fight each other"*. The ordering is right and the implementation is
missing: a 50 kΩ linear pot used as an attenuator has a wiper source impedance of
`α(1−α)·R`, worst case **12.5 kΩ at mid-rotation**. Driving a summing amplifier's
10 kΩ input resistor directly:

| Knob position | Intended attenuation | Wiper Zs | Actual |
|---|---|---|---|
| 100 % | 1.00 | 0 Ω | 1.00 |
| 50 % | 0.50 | 12.5 kΩ | **0.22** |
| 25 % | 0.25 | 9.4 kΩ | **0.13** |

So the control law is squashed into the top of the rotation — and, worse, the
*offset* knob's injection ratio into the same summing node is unchanged, so
turning the gain knob changes the relative weight of the two inputs. The two
controls fight through the summing node, which is exactly the failure the
gain-then-offset ordering exists to prevent, arriving by a different route.

A secondary point that matters in a one-off with panel hardware: the standard
failure mode of a potentiometer is an intermittent or open wiper, which leaves
the summing input floating.

**Circuit.** One op-amp channel:

```
in-amp out ──[POT 50k lin]── wiper ──┬──|+\  ½ OPA2197
                  │                  │  |  >──┬── to offset summing node (10k)
                 GND              [10nF]  |−/ │
                                     │    └───┘
                                  [10k to GND — fail-safe on an open wiper]
```

- Follower: the summing node now sees <0.01 Ω, so the law is the pot's own law
  and the two knobs stop interacting.
- 10 nF at the wiper: with the 12.5 kΩ worst-case source that is a 1.3 kHz pole —
  above the breath band, below anything that could couple in, and it removes
  wiper contact noise, which on a CV that drives a VCA is an audible scratch.
- 10 kΩ to ground makes an open wiper fail to zero output rather than to
  whatever the floating input drifts to.

**Verdict: ADD.** One op-amp channel and three passives, on the instrument's
primary expressive control.

---

## 7. **The sensor's own output conditioning is absent, and so is every decoupling capacitor on the carrier's analog section — including the one that *is* the ADC's voltage reference.**

**Severity: High.**

**Boundary:** MPXV4006DP VS and VOUT pins; MCP3202 VDD/VREF; REF5050 VOUT;
OPA2197 supply pin.

**What goes wrong.** Two separate omissions at the same node cluster.

**(a) The sensor.** NXP's recommended application circuit for this family shows
supply and output decoupling — 1.0 µF on VS and 0.01 µF on VOUT. Neither appears
in the BOM or in any ADR. The output capacitor exists because the part is an
amplified, laser-trimmed sensor whose output stage is not designed to drive an
arbitrary load or to be immune to what is coupled back into it; the supply
capacitor exists because the part is ratiometric and its supply *is* its scale
factor, a point ADR 0003 argues at length before providing the reference and
omitting its local reservoir.

**(b) The carrier.** `hardware/bom.csv` contains exactly one controller-side
decoupling line, `C-DECOUPLE-165`, qty 4, *"one per shift register board"*. The
**MCP3202, the REF5050 and the OPA2197 all sit on the carrier with no decoupling
at all.** The review's R48 said *"no controller-side decoupling in the BOM at
all"* and its central sentence was about the converter, not the registers: *"for
a VDD-referenced ADC the decoupling capacitor **is** the voltage reference."* The
fix was applied to the shift registers and not to the part it was written about.

Arithmetic for why that bites: the MCP3202 takes VREF from VDD, and VDD is the
real-time dev board's 3.3 V rail, shared with the 74LVC165 chain whose output
edges swing ±24 mA down a 14-inch loom. Any disturbance on that rail is a
full-scale error on the conversion:

```
100 mV on a 3.3 V reference = 100/3300 × 4096 = 124 LSB at 12 bits
```

— on the channel that decides when a note starts.

**Circuit.** A new BOM line, `C-DECOUPLE-CTRL`:

| Where | Value |
|---|---|
| MPXV4006DP VS | 1 µF X7R, at the pin |
| MPXV4006DP VOUT | 1 kΩ series + 330 nF to AGND (**this is also the instrument-end 482 Hz band limit of finding 5**; use 10 nF if the pole is placed elsewhere) |
| MCP3202 VDD/VREF | 100 nF X7R **+ 10 µF**, both at the pin |
| REF5050 VOUT | 10 µF + 100 nF (TI recommends 1–10 µF for stability and noise) |
| REF5050 NR/TRIM | 1 µF, to cut the reference's 1/f noise |
| OPA2197 V+ | 100 nF + 10 µF (it runs single-supply from raw +12 V) |

Note the sensor RC is placed *before* the buffer, so it band-limits both branches
— the umbilical copy and the ADC copy — and the 1 kΩ isolates the sensor's output
stage from 330 nF.

**Verdict: ADD.** Under a dollar of ceramics, inside a body that cannot be
reopened, on the one converter in the design whose reference is a capacitor.

---

## 8. **Not one of the six CV outputs has a reconstruction filter component. The corners are specified in prose; nothing implements them.**

**Severity: Medium-High.**

**Boundary:** op-amp output → 1 kΩ (`R-OUT-PROT`) → PJ398SM jack, six times.

**What goes wrong.** ADR 0006 specifies corner frequencies for all three classes
of output (pitch fast, breath ~500 Hz, mod ~2 kHz), the review argued them down
to 5 kHz on pitch, and the latency budget charges 160 µs to *"op-amp and
reconstruction filter"*. The BOM has `C-DECOUPLE` (100 nF at IC supply pins),
`C-REG-ADJ` (regulator) and `C-AA-ADC` (the ADC). **There is no filter capacitor
for any output.** The stage exists as a number in three documents and as zero
parts.

That is a parts omission on pitch and breath, where the topology is settled
(ADR 0006: *"the pitch output filter stays an ordinary series RC"*). On the mod
channels it is more than that, because the values were never derived:

- Mod update rate is 4 kHz. For a slow gesture source (IMU content below ~20 Hz)
  the first zero-order-hold image lands at 3980 Hz, attenuated by the hold's own
  sinc by about −50 dB; a 2 kHz pole adds only −6 dB. Fine.
- But **the mod channels are assignable and breath is an available source.** A
  160 Hz breath component puts its image at 3840 Hz with only ~−26 dB of sinc.
  A 2 kHz pole adds 6 dB → **−32 dB, about 2.5 % of the modulation depth**, at
  3.8 kHz, into a VCA. That is an audible whistle that appears only on certain
  routings — the worst kind of bug to find later.
- Moving the mod pole to 1 kHz costs nothing (the sources top out at 400 Hz ODR
  and far less in content) and gives −12 dB instead of −6 dB → −38 dB total.

**Circuit.** Capacitor to ground on the jack side of the existing 1 kΩ, which
also makes the 1 kΩ do its other legitimate job as a capacitive-load isolation
resistor:

| Output | R | C | Corner |
|---|---|---|---|
| Pitch | 1 kΩ (existing) | 33 nF C0G | 4.8 kHz — the review's resolved 5 kHz; settles a full-range step to 1 cent in ~300 µs |
| Breath | 1 kΩ | 330 nF X7R | 482 Hz |
| Mod 1–4 | 1 kΩ | 150 nF X7R | 1.06 kHz |

Use C0G on pitch: an X7R capacitor's voltage coefficient is a *signal-dependent*
capacitance, which on a filter is harmless but on a pitch channel where the
series resistor is already a calibrated gain term is an unnecessary variable.

Two placement rules worth writing down, because they are the ones the review's F2
warned get discovered late:

- The capacitor is at the jack, **after** the series resistor — so the corner
  moves ~1 % with a 100 kΩ load, which calibration absorbs, and the op-amp never
  drives the capacitance directly.
- ADR 0006 already declined the in-loop dual-feedback compensation, so **this
  capacitor and the `Cf` of that topology are not the same part and there is no
  conflict left to resolve.** Record the values now so nobody reopens it.

**Verdict: ADD.** Six capacitors, values stated before the board is fabbed.

---

## 9. **"Gate the 74AHCT125's OE from umbilical +12 V presence" has no circuit behind it. 12 V cannot drive a 5 V logic input, and a slow ramp into a non-Schmitt input recreates the failure the gating exists to prevent.**

**Severity: Medium-High.**

**Boundary:** umbilical +12 V (load-switch output) → 74AHCT125 OE, in the module.

**What goes wrong.** ADR 0004 makes this a requirement and ADR 0005 makes it the
reason the power switch had to move to the module — so the gating is
load-bearing, architecturally. There is no part, divider, comparator or
supervisor in the BOM for it, and two things break if it is drawn naively:

- **Level.** 74AHCT125 absolute maximum on an input is `VCC + 0.5` = **5.5 V**. A
  direct connection from a 12 V rail destroys the part.
- **Slope.** The TPS2553 *deliberately ramps* the umbilical rail — inrush
  limiting is the reason it is there. Through a plain 100 k/47 k divider a 1 ms
  ramp crosses the AHCT input's indeterminate band (0.8 V to 2.0 V) in

  ```
  (1.2 V / 3.83 V) × 1 ms = 313 µs
  ```

  During those 313 µs the buffer's outputs are undefined and it draws crowbar
  current — precisely the *"floating CMOS inputs oscillate and draw crowbar
  current… a stray edge on CS latches a garbage word into the pitch DAC"*
  condition the gating was added to eliminate, now occurring every time the
  instrument is switched on. The DAC's `CLR` watchdog bounds the consequence to
  N ms, which is why this is Medium-High and not Critical.

**Circuit.** Either of:

```
(a)  +12V_UMB ──[100k]──┬──[47k]── GND        (b)  +12V_UMB ──[100k]──┬─── G  2N7002
                        │                                             │        │D──┬── OE
                   MCP100-450 / MAX809 (SOT-23)                     [47k]      S   │
                        └── open drain ──┬── OE                       │       GND [10k]
                                    [10k to +5V]                     GND           │
                                                                                  +5V
                                                          + [1M] from D back to the
                                                            divider node for ~150 mV
                                                            of hysteresis
```

Add 100 nF across the lower divider leg for toggle bounce. OE is active-low, so
wire it such that **absent instrument = OE high = outputs disabled** — the
failure direction must be "disabled", not "enabled".

**Verdict: ADD.** One SOT-23 part and three passives, on a requirement that is
already load-bearing in two ADRs.

---

## 10. **Only MOSI gets source termination. SCLK — the fastest edge in the system — drives 2 m of cable raw, and both LED data lines drive 400 mm raw.**

**Severity: Medium.** The instrument-side resistors are unretrofittable.

**Boundary:** ESP32-S3 GPIO → umbilical (SCLK, CS); 74AHCT125 → WS2815 strip data.

**What goes wrong.** ADR 0004 specifies *"220 Ω in series on MOSI at the driving
end"* and stops there. The reasoning given is that it removes the need for SYNC
regeneration, which is true and is a different job from signal integrity. SCLK
runs the same 2 m through the same connector.

```
ESP32-S3 GPIO output impedance ≈ 25–40 Ω
Cat5e differential/pair impedance ≈ 100 Ω
source reflection coefficient = (25 − 100)/(25 + 100) = −0.6
far end (74AHCT125 input) = open → +1
round trip at 2 m, ~5 ns/m = 20 ns, against a ~2 ns edge
```

Every criterion for "terminate this" is met, on a **clock**. Ringing on a clock
is double-clocking, and a double clock shifts the DAC8568's entire 32-bit word by
one bit: the pitch channel receives a garbage code, and nothing detects it.
Undershoot also drives the AHCT input below its −0.5 V absolute maximum.

220 Ω on MOSI works because 220 Ω into ~100 pF of cable gives a 22 ns edge, ten
times slower than native — which incidentally is what keeps R36's MOSI→CS
crosstalk (they share one twisted pair) down to ~0.1 V. Applying the same
treatment to SCLK and CS costs two resistors.

On the LED side: 74AHCT125 outputs drive ~400 mm to the first WS2815 with no
series resistor. 220–470 Ω at the driver is universal practice for addressable
strips, and the part it protects is the first pixel of a strip inside a bonded
body.

**Circuit.**

- 68–220 Ω 1 % in series at the **driving end** of SCLK and CS, on the carrier.
  (Match MOSI's 220 Ω unless E11 says the edge is too slow; at 0.6 MHz there is
  no timing pressure.)
- 330 Ω in series at each 74AHCT125 LED data output.
- Free, in firmware: set the ESP32-S3's GPIO drive strength to the lowest setting
  that works. The review's V1 called this out as *"the real lever… free and
  mentioned by nobody"*, and it is still mentioned nowhere.
- Reserve the 74AHCT14 footprint at the module end that ADR 0004 already
  contemplates deciding at E11, rather than deciding it after the board is fabbed.

**Verdict: ADD.**

---

## 11. **The stuck-CV watchdog reaches five jacks. The sixth is analog, and nothing mutes it.**

**Severity: Medium.**

**Boundary:** the breath channel, between the in-amp and the jack.

**What goes wrong.** ADR 0004 makes the case plainly — *"A stuck CV is worse than
a dead one… the rack drones forever. Nothing in the design notices"* — and
answers it with a retriggerable monostable asserting `CLR`. `CLR` zeroes the DAC.
The breath CV never enters the DAC.

In the exact failure the watchdog exists for — the real-time board hangs
mid-note, instrument still powered — the sensor, the REF5050 and both OPA2197
halves are all alive and the breath jack carries a live signal. Worse, `CLR`
zeroes **DAC channel 6**, which is the ambient-zero, so the correction is removed
at the same moment:

```
breath floor = G × sensor offset = 2.13 × 0.20–0.26 V = 0.43–0.55 V
```

times the gain knob. Into a VCA calibrated for 0–5 V that is **9–11 % open,
indefinitely**, on an instrument that has stopped responding. That is the failure
ADR 0004 declares unacceptable, occurring on the primary expressive channel,
through the one path the failsafe cannot see.

The same stage fixes a second, smaller thing: ADR 0006's power-on table claims
breath sits at 0 V at rack power-on. True while the instrument is unpowered; once
it powers up and before firmware writes the zero, the jack sits at 0.43–0.55 V.

**Circuit.** Shunt the post-gain, pre-summing node — a defined ~10 kΩ impedance —
with a small-signal FET driven from the watchdog's complementary output:

```
gain buffer out ──[10k]──┬──── offset summing node
                         │
                        D│  2N7002
                         │
                    G ──[10k]── 74HC123 Q̄   (high = run, low = mute)
                        S
                       GND
```

- On-resistance ~5 Ω against 10 kΩ = **−66 dB** of mute.
- Off-state leakage: 2N7002 is typically ~1 nA at 25 °C (1 µA is the 125 °C
  maximum), so 10 µV–10 mV of added offset at that node; at the low end it is
  invisible, and at the worst case it is 0.1 % of a 10 V span. Fit a low-leakage
  part if it measures badly; an ADG419-class switch is the upgrade path.
- With no instrument attached, the watchdog is already in its "no frames" state,
  so the breath channel mutes — which also makes ADR 0006's power-on table true
  as written, rather than true only in one of its three cases.

**Verdict: ADD.** Two parts, and it closes the one hole in a failsafe the project
already decided it wanted.

---

## 12. **The umbilical has an ESD clamp at the instrument end and nothing at the module end.**

**Severity: Medium.**

**Boundary:** etherCON at the module → 74AHCT125 inputs, DAC reference ground,
INA821 inputs.

**What goes wrong.** `U-TVS-UMB` (SP3012-class) sits on the *controller*. The
module end has no protection line item at all — the eight conductors of a 2 m
cable land directly on the level shifter's inputs (protected only by 10 kΩ pulls)
and on the in-amp's inputs.

That is the wrong way round on exposure. ADR 0004 calls the cable **a
consumable** that is handled every session, flexes constantly, and gets replaced
at the first intermittency; the connector shell is touched by hand. The INA821 is
also the least replaceable analog part in the module.

Note also that the specified SP3012-06UTG is a **6-channel** array against **8**
conductors, so two are unprotected even at the instrument end.

**Circuit.**

- One SP3012-class 6-channel array at the module etherCON covering SCLK, MOSI,
  CS and +12 V, referenced to **PWR_GND** — never AGND, or the ESD return flows
  in the sense return.
- **BAV99 on BREATH and AGND, not the array.** Array leakage of ~1 µA through
  the 10 kΩ protection resistors is **10 mV** of temperature-dependent offset on
  the breath channel; BAV99's few-nanoamp leakage is ~25 µV. This is the same
  argument ADR 0006 already accepted for the CV jacks (BAV99, not BAT54S), and
  it applies here with 10× the series resistance.

**Verdict: ADD.** Two parts, on the connector that is designed to be abused.

---

## 13. **`C-AA-ADC` is being asked to be the anti-alias filter, the sample-capacitor reservoir *and* settle inside the loop period, from a source impedance chosen for a fourth reason. At the specified values the corner is 120 Hz, not 600 Hz.**

**Severity: Medium-Low** — but the stated number is wrong by 5× and it is
load-bearing in ADR 0003.

**Boundary:** breath buffer → 10 k/15 k divider → MCP3202 CH0.

**What goes wrong.** ADR 0003 claims *"220 nF gives a ~600 Hz corner and 58 dB at
500 kHz"*. With the divider it also specifies (`≥10 kΩ upper leg`, 10 k/15 k), the
Thevenin source impedance is `10k ∥ 15k` = **6 kΩ**:

```
f = 1/(2π × 6 kΩ × 220 nF) = 120.6 Hz
```

Five times lower than stated, and **below the sensor's own 159 Hz bandwidth** —
so the digital copy of breath is slower than the analog CV it is meant to track,
by a pole the design does not know it has. Group delay is 1.3 ms. Note gating
survives (a threshold at 10 % of span is crossed at `0.105τ` = 139 µs), but the
mod-channel, MIDI and display copies lag the jack visibly.

The single capacitor is carrying four coupled requirements: anti-aliasing against
buck folding, charge reservoir for the SAR's sample capacitor, settling inside
250 µs, and tolerating a divider impedance chosen to keep power-up sequencing
current out of the ESD clamp. The review's V4 noticed the last two conflicting
and declared this capacitor the keystone that resolves them; nobody then
recomputed the corner with the resistor value the resolution produced.

**Circuit.** Change the value to **47 nF**:

- Corner `1/(2π × 6 kΩ × 47 nF)` = **564 Hz** — what ADR 0003 intended.
- Attenuation at 496 kHz: `20·log(496 kHz / 564 Hz)` = **58.9 dB** — which is the
  58 dB the ADR claims, now actually true.
- Reservoir: 47 nF against a ~20 pF sample capacitor is a 2350:1 ratio, so
  charge-sharing costs 0.043 % (1.7 LSB at 12 bits), constant and calibrated out.
- Recharge τ = 282 µs against a 250 µs loop period leaves a steady ~0.03 % gain
  error — also constant.

If the 120 Hz pole is actually wanted (it is a defensible choice: the digital
copy only feeds thresholds, mods, MIDI and a display), then keep 220 nF and
**correct the number in ADR 0003**, because the next person to size this will
trust it.

**Verdict: ADD** (a value change and a documentation correction).

---

## 14. **The MCP3202's second channel is left floating, and the digital breath reading is the ratio of two unrelated regulators.**

**Severity: Low.**

**Boundary:** MCP3202 CH1.

**What goes wrong.** The BOM says *"One spare channel"* and nothing connects it.
A floating analog mux input is not harmful the way a floating logic input is, but
it is charge-coupled to the sampling network and it is free to tie.

The larger point is the one the review reached twice (R11, and V3's cheaper
version) and no ADR adopted: the MCP3202 has no separate VREF pin, so
`VREF = VDD` = the dev board's 3.3 V LDO, while the sensor's scale factor is a
5.000 V precision reference. The breath reading is the ratio of two unrelated
regulators.

Honest sizing, because this is easy to over-sell:

- Static: ±2 % of the breath *scale*. Almost nothing cares — thresholds and
  curves are fractions of the same scale, so the error largely cancels in use.
- Dynamic: a 160 mA step on the 5 V rail through ~0.2 Ω is 32 mV; the dev board's
  LDO gives roughly 40 dB of rejection in the audio band → ~0.3 mV on 3.3 V →
  **0.4 LSB**. The "LED-induced note-gate chatter" mechanism of ADR 0014/S6 is
  real but small.

So the argument for doing it is not the error size; it is that the channel, the
converter and the reference all already exist, and two resistors convert an
unquantified dependency into an exact cancellation.

**Circuit.** 10 k/15 k from the **buffered** 5.000 V node (not from the REF5050
output directly) into CH1, with a 47 nF to ground to match CH0's settling. Both
channels share `VREF = VDD`, so `breath_code / ref_code` is independent of VDD
exactly, and firmware divides.

At minimum, if this is declined: tie CH1 to ground.

**Verdict: ADD** (two resistors and a capacitor; the ground tie is the floor).

---

## 15. **The cable shield has no defined termination at either end.**

**Severity: Low.**

**Boundary:** Cat5e F/UTP shield ↔ etherCON shells ↔ instrument backing plate and
module panel.

**What goes wrong.** ADR 0004 says *"Shielded (STP/FTP) preferred… the shield is
free at this price"* and never says what it connects to. Both outcomes of leaving
it undecided are bad in different ways: bonded at neither end it is a
capacitively coupled antenna running the length of the bundle; bonded at both
ends — which the metal etherCON shells, the instrument's internal backing plate
and the module panel all make the *default* — it becomes a fourth conductor in
parallel with PWR_GND.

```
F/UTP drain wire ≈ 0.14 Ω/m → 0.28 Ω over 2 m
PWR_GND (1 conductor, 24 AWG, 2 m) ≈ 0.17 Ω
shield share of return current ≈ 0.17/(0.17+0.28) = 38 %
```

That does not hurt the breath channel — AGND is a sense return and is unaffected
— but it puts ~150 mA of instrument return current through the aluminium plate
under the player's hands at one end and into the rack chassis at the other, in a
large-area loop.

**Circuit,** as a written rule rather than a part:

- Shield → module panel / chassis at the module end, DC bonded.
- Shield → PWR_GND at the instrument end through **100 nF ∥ 1 MΩ**, so it is an
  HF shield and not a DC return.
- If the etherCON shell's mechanical mounting forces a DC bond at the instrument,
  invert it: put the 100 nF ∥ 1 MΩ at the module end instead.
- Verify the return split with a current probe at E11, which is already scheduled
  and already has the cable at length.

**Verdict: ADD** (two parts and one sentence in ADR 0004).

---

## 16. **Nothing in the design says what happens to unused op-amp sections, unused gates, or the DAC's control pins.**

**Severity: Low, cost zero.** Listed because this is the class of omission that
produces a hot IC and an oscillation nobody can find, on a hand-assembled
one-off.

**Boundary:** every unused input in the design.

**What goes wrong, and the rules.**

- **Unused OPA2197 halves.** Tie `+IN` to ground and short the output to `−IN` —
  a grounded follower. A floating op-amp input on ±12 V oscillates near its GBW
  and couples into the other half of the package through the shared supply pins
  and substrate. On a board whose whole purpose is a precision pitch channel,
  that is not a theoretical concern.
- **Unused 74AHCT125 gates.** Two spares on each of the two packages. Inputs to
  ground, OE tied inactive. This is ADR 0004's own argument about floating CMOS
  inputs drawing crowbar current *"inside the precision analog box"*, applied to
  the gates sitting in the same package as the ones it worried about.
- **Unused 74HC123 half.** Inputs tied to their inactive levels, outputs open.
- **DAC8568 `LDAC` and `CLR`.** Neither has a specified state anywhere in the
  repository. `LDAC` tied low (update on write) unless a synchronous update is
  wanted; `CLR` pulled to its inactive state through 10 kΩ so that the watchdog
  is the *only* thing that asserts it — and so that an unpopulated or failed
  watchdog leaves the DAC running rather than held in reset.
- **MCP3202 CH1** (finding 14).

**Verdict: ADD** — a schematic rule, no parts, no cost. Write it into ADR 0013's
package/build policy section where the rest of the assembly rules live.

---

## 17. **`R-OPAMP-IN` (1 kΩ on each DAC-driven op-amp input) is described as "outside the feedback path so it costs nothing in accuracy". On the mod channels and pitch it is inside the gain network.**

**Severity: Medium as an error, zero as a consequence.**

**Boundary:** DAC channel → op-amp input, five instances.

**What goes wrong.** The claim is true for a follower and false for a difference
amplifier. The mod stage is `Vout = 4 × (Vdac − Voff)`, which needs a divider on
the `+` input: with `R1` = 10 kΩ from the DAC and `R2` = 40 kΩ to ground,
inserting 1 kΩ in series makes `R1` = 11 kΩ:

```
V+ = Vdac × 40/51 = 0.784·Vdac   (instead of 0.800·Vdac)
Vout = 3.92·Vdac − 4·Voff        (instead of 4·Vdac − 4·Voff)
```

- Gain error **2 %**.
- The difference amplifier is now unbalanced (`R1/R2 ≠ R3/R4`), so at
  `Vdac = Voff = 2.5 V` the output is **−0.2 V** instead of 0 — a 1 % zero error
  on the ±10 V span.

Both are constant, and both are inside the authority of what already exists:
firmware scales the mod channels per ADR 0006, and the pitch channel has scale
and offset trimmers with full authority over exactly this class of error.

There is also a smaller point that argues against the part rather than for
fixing it: the divider's own 10 kΩ already limits clamp current into an
unpowered op-amp to `5 V / 10 kΩ` = **0.5 mA**, comfortably inside the ±2 mA
family limit the resistor was added to respect. On the difference stages the
extra 1 kΩ is not buying the protection it was specified for.

**Verdict: ACCEPT** — no new stage. Absorb it instead: make the input leg
9 kΩ + 1 kΩ so the network is correct by construction and the resistor still
exists as a discrete current limit if someone later wants it to. Keep the full
1 kΩ wherever the DAC really does drive a follower (the mod-offset buffer and the
ambient-zero stage), where the original reasoning holds exactly.

---

## 18. **There is no filter between the umbilical +12 V node and the instrument's analog section (REF5050, both OPA2197 halves).**

**Severity: —.**

**Boundary:** instrument +12 V node → analog supply pins.

**Why it is consciously unnecessary.** The same node feeds the WS2815 strips,
which modulate 200–400 mA at their ~2 kHz PWM rate through ~0.34 Ω of cable:

```
rail movement = 0.4 A × 0.34 Ω ≈ 136 mV at 2 kHz
```

Through the parts that are actually there:

- REF5050 line regulation ≈ 5 ppm/V → 136 mV → **0.7 µV** on the sensor's supply,
  and therefore 0.7 µV × 2.13 = 1.5 µV at the jack.
- OPA2197 PSRR ≈ 80 dB at 2 kHz → 136 mV → **13.6 µV** at the buffer output,
  29 µV after the 2.13× receiver.

Against a 153 µV LSB on the 10 V span that is a fifth of an LSB, and it sits at
2 kHz, above the 500 Hz band limit at *both* ends (finding 5). An RC (10 Ω +
10 µF = 1.6 kHz, 120 mV of drop at the 12 mA analog load) would improve it by
about 2× in band.

**Verdict: ACCEPT** — consciously unnecessary. The 100 nF and 10 µF at each
supply pin from finding 7 are still required; what is declined is a dedicated
filtered analog rail. Note this ACCEPT depends on finding 7 being taken: without
local bypass the PSRR figures above are optimistic, because PSRR is specified
with a decoupled supply.

---

## 19. **The module has no star-ground scheme and no Kelvin return from the pitch stage to the pitch jack's sleeve.**

**Severity: —.**

**Boundary:** module analog ground ↔ PJ398SM sleeve.

**Why it is consciously unnecessary.** The pitch CV's real reference is the jack
sleeve, because that is what the receiving VCO measures against. Any current in
the ground pour between the pitch stage's ground-side network and that sleeve is
an error:

```
module analog return ≈ 40 mA (−12 V) + 5 mA (DAC regulator) + 10 mA (shifter)
over ~30 mm of 1 oz pour: ≈ 1 mΩ
error ≈ 55 mA × 1 mΩ = 55 µV = 0.066 cents
```

Against 2.4 cents from the trimmer's tempco and ~3.5 cents/10 K from the VCO
itself, this is three orders below the limiting term. A 6 HP board is small
enough that no topology is needed.

**Verdict: ACCEPT** — no stage. One layout rule instead, which is free: return
the pitch stage's ground-side network to the pitch jack's sleeve node rather than
to the nearest via, and keep the 74AHCT125's and watchdog's return current out of
that path. The instrument end already has its star point defined (ADR 0003); the
module does not need one, and saying so explicitly stops someone deriving one
later.

---

## 20. **There is no dedicated gate or trigger output stage, on an instrument whose entire articulation model is breath crossing a threshold.**

**Severity: —** as an electrical gap; worth a build note.

**Boundary:** the musical requirement → the six jacks.

**What the prose promises and the electronics do not have.** ADR 0003 makes
threshold-and-gate the core of note articulation — *"Breath crossing a threshold
is what starts a note"* — and a Eurorack patch needs a gate to hear it. There is
no comparator, no logic, no gate jack. ADR 0006 covers it by allowing a mod
channel to be assigned a gate, and that genuinely works: the DAC can slew 0→+8 V
inside one 250 µs update.

The residual cost is the mod channel's own reconstruction pole. At 1 kHz
(finding 8) a gate's 10–90 % rise is `2.2τ` = **350 µs**. Every Eurorack envelope
generator and VCA will act on that; a minority of clocked or logic inputs
specifying fast edges may not.

Building a hardware gate — a comparator on the analog breath signal plus a
Schmitt — would also create a **second threshold authority**, independent of the
firmware threshold the player configures from the display. ADR 0013 avoids
split-brain state by rule, and this would reintroduce it in analog.

**Verdict: ACCEPT.** No stage. Two free build notes instead:

- Assign **Mod 4** as the gate by convention, and silkscreen the write-on strip
  accordingly.
- Reserve a footprint to cut Mod 4's filter capacitor to 10 nF (16 kHz, 22 µs
  rise) if a destination ever needs a fast edge. A footprint decided now costs
  nothing; a board spin later costs a month.

---

## Checked and genuinely not needed

Stated explicitly so nobody adds them later on the grounds that a reviewer did
not consider them:

- **A differential line driver on BREATH.** ADR 0003's analysis is right: with a
  dedicated sense return the umbilical is a patch cable, and full differential
  signalling buys ~6 dB against noise a 500 Hz channel does not have. Correctly
  declined.
- **In-loop `Riso` / dual-feedback compensation on pitch.** Declined in ADR 0006,
  and the review's F1 shows the naive version oscillates. Finding 8's ordinary
  series RC is the right stage and is now specified with values.
- **A sample-and-hold anywhere.** Nothing in this design has a signal that must
  be frozen: the DAC is itself a hold, and the SAR's internal sampling capacitor
  with finding 7's reservoir covers the converter side.
- **An instrumentation amplifier at the sensor.** The MPXV4006DP is internally
  conditioned to 0.2–4.8 V; ADR 0003 is right that the in-amp belongs at the
  *receiving* end instead.
- **A separate precision reference for the pitch DAC.** ADR 0006's arithmetic
  holds: the internal reference at 5 ppm/°C is 0.54 cents against the resistors'
  and trimmer's several. Finding 2 uses that same reference for the offset, which
  makes the argument stronger, not weaker.
- **Buffering the pitch output against the 1 kΩ / load divider.** Settled in
  ADR 0006 — it is a pure gain error with two independent authorities over it.
- **A +5 V fallback regulator in the module.** Out of scope by the README's own
  design-scope rule.

---

## What this costs, in total

| Class | Items |
|---|---|
| New part numbers | **0** active; one SOT-23 supervisor *or* a 2N7002 (finding 9), one 2N7002 (finding 11), one BAV99 pair + one TVS array (finding 12) |
| `U-OPA-PITCH` quantity | 5 duals → **6** (findings 1, 2, 6 need three more channels) |
| New BOM lines | `C-DECOUPLE-CTRL`, `C-OUT-FILTER` (×6), `R-KEY-PULLUP` + `C-KEY` + `R-KEY-SER` (×18), `R-BIAS-RETURN`, `C-RFI-BREATH`, `R-TERM-SPI` (×2), `R-LED-SER` (×2), `R-REF-BUF` network, `U-PRESENCE`, `Q-BREATH-MUTE`, `D-UMB-CLAMP-MOD` |
| Unretrofittable (inside the bonded body) | Findings **3, 7, 10** — key input networks, carrier decoupling and the sensor RC, SCLK/CS/LED series resistors |
| Documentation corrections | ADR 0003's 600 Hz ADC corner (finding 13); the latency budget's "<0.2 ms" for the filters it mandates (finding 5); ADR 0006's power-on breath state (finding 11) |

**If only three things are taken:** findings **1** (the zero cannot subtract),
**2** (no reference rail for the offsets) and **3** (no key pull-ups). The first
two are functional failures of the two channels the whole project is about; the
third is a functional failure of the key scan and is sealed inside the body the
day it closes.
