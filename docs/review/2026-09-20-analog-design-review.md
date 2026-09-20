# Analog design review — 2026-09-20

Six independent adversarial review agents were run against the analog design,
each given one slice, told to hunt for what is wrong rather than confirm what is
fine, and told to check claims against datasheets and real-world practice.

**Status: all 6 reported. Review pass in progress. No design changes made yet —
one coherent revision follows the review.**

This file is a capture of findings, not a set of decisions. Nothing here is
accepted until it survives review and is written into the relevant ADR.

## Why confidence is high on some of these

Several findings were reached **independently by agents given different scopes
and no knowledge of each other**. Convergence is noted per finding. Where three
agents hit the same thing from three directions, it is almost certainly real.

---

## P0 — breaks a stated requirement or a stated design goal

### R1. No bleed path. The instrument may not be playable as specified.
*Breath agent. Not electrical, and more consequential than anything that is.*

ADR 0003 specifies a closed, dead-ended pneumatic system. No commercial wind
controller works this way:

- **Akai EWI** plugs the sensor tube at the mouthpiece end and drills a 1.5 mm
  hole through its side wall, then runs a **second tube dangling free from the
  bottom of the instrument** for restricted airflow — explicitly to improve
  tonguing response and to carry moisture away from the electronics.
- **Yamaha WX** has a drain hole with **swappable plugs** that partially block
  it "to create a tighter blowing feel" — an adjustable bleed as the primary
  feel control — plus a dedicated air-inlet elbow (P/N VF096100) whose only job
  is keeping moisture off the breath sensor.

Against a full occlusion an adult produces **15–20 kPa**, 2.5–3× the sensor's
full scale. With no escape the player cannot exhale through the instrument, and
tonguing articulation is muted because articulation works by interrupting flow.

**Proposed:** adjustable bleed feeding a drain out of the body, with the sensor
**teed off upstream through a restrictor**, so the sensor branch stays
dead-ended relative to the flow. Preserves the no-droplet-transport property and
gives the player somewhere to breathe.

**Couples to range:** 0–6 kPa cannot be settled until the bleed is. Measured
playing pressures: clarinet 2–4.5 kPa, saxophone up to 8 kPa loud, literature
range 1–12 kPa across wind instruments.

**Needs a decision from the project owner — it contradicts a stated design
assumption.**

### R2. MPXV4006GP is discontinued, and the architecture is single-sourced on it
*Breath agent.*

NXP PCN 202009013DN: last-time-buy **15 May 2021**. Distributor stock only.

This is architectural rather than a sourcing note, because **every modern
replacement is ASIC-plus-internal-DAC**: Honeywell ABP updates at ~1 kHz, ABP2
at ~200 Hz. A 200 Hz staircase into a VCA is exactly the artefact ADR 0003's
analog path exists to prevent, and a 500 Hz filter does nothing to it.

So "swap the sensor later" is not available. **The sensor choice and the
analog-breath decision are one decision.**

**Actions:** buy 3–5 units now; record the dependency in ADR 0003; document a
fallback that preserves continuity — raw piezoresistive bridge plus
instrumentation amp (the MPX2010-class topology ADR 0003 dismissed, which is now
arguably the better topology anyway since the in-amp's REF pin does the zero
subtraction and bridge excitation from the same reference makes the chain
ratiometric by construction).

### R3. The 1 kΩ series resistor destroys pitch accuracy, load-dependently
*CV output agent and pitch agent, independently. Verified locally.*

1 kΩ in series into a Eurorack input forms a divider:

| Destination | Pitch error at 5 V |
|---|---|
| Open circuit (DMM during calibration) | 0 |
| One 100 k input | **−59.4 cents** |
| Multed to two VCOs (50 k) | **−117.6 cents** |
| Multed to three (33 k) | −176.5 cents |

Calibrating against one VCO absorbs the nominal value; the **variation with what
is patched** does not calibrate out. Calibrate into one VCO then add a second on
a mult and the rack detunes by **58 cents**.

For scale, the LT5400 matched network is bought to fight 5.4 cents of tempco
drift. This throws away 59 cents, 5 mm downstream.

**Proposed:** take the op-amp's feedback from the **jack side** of the series
resistor so it sits inside the loop — output impedance collapses, fault current
limiting is unchanged. Needs compensation design and a bench phase-margin check.
Fallback with zero design risk: **100 Ω on pitch only** (6 cents), 1 kΩ retained
on breath and the mod channels where it is correct.

### R4. An LT5400 cannot build a gain of 1.8
*Pitch agent.*

Matched networks come as 1:1:1:1 or 10:1. From four equal resistors you can make
1, 2, 3, ½, ⅔, 3/2 — **9/5 is not available**. Landing on 1.8 requires an
external resistor whose *absolute* tempco then sits inside the gain ratio, which
is precisely the failure ADR 0006 bought the network to prevent. The part the
ADR calls "the single highest-value precision component in the design" cannot do
the job as specified.

**Proposed, and it resolves four findings at once:** respec pitch to
**−2.5…+7.5 V** and use `Vout = 2·Vdac − Voff` with `R1 = R2` from one matched
quad.

- Gain is exactly 2 by construction, set only by matching
- −2 V and +7 V land at Vdac = 0.25 V and 4.75 V — **250 mV of DAC headroom at
  both rails**, which fixes R5
- Offset becomes a DAC channel, so calibration gains **two-sided authority**,
  which fixes R6
- Deletes the "design the gain 5 % high" kludge entirely
- The spec is unchanged: −2.5…+7.5 contains −2…+7

### R5. DAC8568 at AVDD = 5 V cannot reliably reach its own full scale
*Pitch agent.*

Internal 2.5 V reference at gain 2 gives a 0–5 V span from a 5 V supply — full
scale *equals* AVDD. TI's position is that the required headroom is not defined
in the datasheet and that AVDD ≈ 5.5 V is wanted for a true 5 V full scale. The
rack +5 V bus is ±5 % and is the least-regulated rail in Eurorack.

At AVDD = 4.75 V the DAC saturates around 4.55–4.65 V, losing ~3.7 semitones off
the top — and worse, the top calibration point lands in the nonlinear region,
which corrupts the whole fit rather than just the top.

Fixed by R4's topology, which moves the used window to 0.25–4.75 V.

### R6. "Firmware can only scale down" is half true; the missing half is unrecoverable
*Pitch agent.*

A two-point fit is `y = a·x + b`. Code scaling implements `a`. **Nothing in the
design implements `b`.** ADR 0006 prescribes a deliberate +5 % gain bias and says
nothing about the offset — whose safe bias direction is the opposite one. If the
hardware offset lands at −1.90 V instead of −2.00 V, firmware cannot reach −2 V
at all.

Fixed by R4 (offset from a DAC channel, plus 0.5 V of slack at each end).

### R7. The Recom R-78E5.0 has no enable pin
*Power agent. Provable from this repo's own BOM.*

The BOM says `SIP-3 THROUGH-HOLE`, "3-pin SIP on a 7805 footprint" — IN, GND,
OUT. ADR 0005's instrument power switch says "switch the buck converter's enable
pin." **That pin does not exist and the switch as specified cannot be built.**

And it would not work even if it did: the WS2815 strips hang on raw umbilical
+12 V **upstream of the buck**. Switching the buck off leaves ~120 mA of strip
quiescent draw and the strips holding their last latched colours. "Off" would be
a lit instrument drawing a third of its running current.

**Proposed:** P-channel MOSFET high-side switch on the instrument's 12 V rail,
gate pulled down through the panel switch, RC on the gate. One part gets a switch
carrying no current (the original intent), a real power-off that kills the LEDs,
and a soft-start ramp that also addresses R9.

### R8. The ratiometric path is ~30 dB worse than the one that was analysed
*Breath agent.*

MPXV4006 is explicitly ratiometric: `Vout = VS × (0.1533·P + 0.04)`. The sensor
shares the 5 V buck with both dev boards. Nothing downstream tracks VS, and
firmware cannot correct an analog path.

| 5 V rail excursion | Error at the jack |
|---|---|
| 0.4 % (a modest load step) | 21 mV (−54 dBFS) |
| 1 % | 52 mV (−46 dBFS) |
| 2 % (R-78E initial tolerance) | 104 mV (−40 dBFS) |

The AGND common-mode path that ADR 0003 spends pages on contributes **0.13 mV**.
The disturbers are the same ones — AMOLED current steps, WiFi TX bursts — on the
same rail, with millisecond envelopes that pass straight through the 500 Hz
filter.

**Proposed:** dedicated precision 5.000 V reference (MAX6350, 15 mA) fed from
the umbilical +12 V, powering the sensor and its buffer. Single highest-leverage
change in the breath path. The ADC can share it — see R11.

---

## P1 — significant

### R9. No inrush limiting anywhere
*Power agent.*

ADR 0004 rules out the conventional 2.2–10 Ω series resistor on DC-drop grounds.
The arithmetic is right and the conclusion is right — **but that resistor is also
the standard Eurorack inrush limiter, and nothing replaced it.** Ferrite beads
are ~0.2–0.35 Ω and provide no controlled limiting.

Estimated 300–1500 µF total through ~1 Ω → **~12 A peak**. Doepfer's PSU3 is
documented to stall on +12 V from module bypass capacitance; the WMD Soft Start
module exists solely for this.

Three trigger events, the worst being **the module's own panel toggle flipped
with the rack live** — contacts arcing into a capacitive load every time.

Note the internal inconsistency: ADR 0005 argues at length that the instrument
should never switch a few hundred mA with a panel switch, then ADR 0004 puts
exactly such a switch in the module.

### R10. INA134 cannot deliver the CMRR it is credited with
*CV agent and breath agent, independently.*

A difference amplifier's CMRR is set by **source-impedance balance**, not by the
chip. INA134 presents 50 k on +IN and 25 k on −IN.

| Source imbalance | Achieved CMRR |
|---|---|
| 1.6 Ω | 90 dB (the datasheet figure) |
| 100 Ω | 54 dB |
| **1 kΩ** (a plausible protection resistor) | **34 dB** |

ADR 0003 specifies a series protection resistor on BREATH and nothing on AGND —
and a 100 k pulldown on one leg only, which alone caps CMRR at 40 dB. Combined,
~31 dB against the 60 dB the ADR says is needed. **Missed by ~30 dB.**

Worse, R14 shows the protection requirement and the CMRR requirement are in
direct conflict as specified.

**Proposed:** replace with a true instrumentation amp (INA821/INA828) whose
buffered GΩ inputs make CMRR independent of source impedance. That also absorbs
a gain stage and gives proper DC offset/drift specs — the INA134 is an audio
part spec'd for AC. Alternative if keeping it: matched 0.1 % resistors on **both**
legs, pulldown mirrored on both legs, pulldown at the connector.

### R11. The ADC is not ratiometric with the sensor, and the divider is too stiff
*Breath agent and ADC agent.*

MCP3202 has **no separate VREF pin** — pin 8 is VDD/VREF. With VDD = 3.3 V from
a dev board LDO and the sensor on the 5 V buck, the digital breath reading is the
ratio of two unrelated regulators (±2 % each). That moves the note-on threshold,
the mod-channel depth and the MIDI CC.

Separately, Microchip specifies source impedance below ~1 kΩ; a natural 0.6 %
divider (10 k/15 k) gives 6 kΩ — 6× over.

**Proposed:** run the MCP3202 from the same precision 5.0 V as the sensor. Then
VREF = VS, **supply variation cancels exactly**, the divider **disappears
entirely**, and 40 % of ADC range is recovered. Costs a DOUT level-shift to
3.3 V. Cheapest partial fix: digitise the 5 V rail on the MCP3202's spare
channel and ratio in firmware.

### R12. Ambient zero is knob-dependent and the loop is open
*Three agents independently.*

The sensor's zero enters **before** the panel gain pot; the DAC zero-correction
is summed **after** it. The correct null is `0.2 V × G`, where G is a passive pot
the firmware cannot read — ADR 0004 deleted MISO, so the module reports nothing.

Zero at startup, then turn the gain knob, and the zero is wrong by `0.2 V × ΔG`
— at full gain, **435 mV stuck offset**, i.e. an open VCA droning with no breath.

Also: a unipolar 0–5 V DAC channel summed additively **can only add**, and the
sensor's offset needs subtracting. Not addressed anywhere.

**Proposed:** do the zero subtraction **in the instrument, ahead of the cable and
ahead of all gain**. One zero, one truth, and the ADC copy sees the same zeroed
signal. Put a ~1 Hz RC on the zero DAC so its update steps do not land on the CV.

### R13. Floating SPI inputs at the module whenever the instrument is off
*All three of pitch, power and CV agents.*

`SW-POWER` cuts +12 V to the umbilical while the module stays powered from the
bus. So the normal "off" state is: module alive, DAC alive, SCLK/MOSI/CS floating
at the 74AHCT125. This is a **designed-in operating mode, not a fault.**

Floating CMOS inputs oscillate and draw crowbar current inside the precision
analog box — and a stray edge on CS latches a garbage word into the pitch DAC.

**Proposed:** CS pulled to +5 V, SCLK and MOSI pulled to ground, at the module.
Gate the 74AHCT125's OE from umbilical +12 V presence so "instrument absent" is a
designed state. Note the 74AHCT125 is a plain buffer, not a Schmitt — if edge
integrity needs help, that wants a 74AHCT14.

### R14. The breath protection resistor requirement conflicts with the CMRR requirement
*Breath agent.*

A sustained +12 V on the BREATH conductor drives the MCP6002 output through the
series resistor into its 5 V rail: through 1 kΩ that is 6.4 mA against a ~2 mA
clamp rating. **Needs ≥3.3 kΩ.** But 3.3 kΩ unmatched leaves 24 dB CMRR (R10).

The two requirements are incompatible as specified and the ADR resolves neither.

**Proposed:** decouple the jobs — clamp diodes take the fault current, the
resistor merely limits it; keep the resistor small and **matched on both legs**.
Or adopt the in-amp from R10, which makes the whole conflict disappear.

### R15. Current budget understated ~50 %, and three ADRs disagree
*Power agent.*

ADR 0005 says 250 mA, ADR 0004 says 290 mA, ADR 0003's table runs to 350 mA, the
BOM says 350 mA in two places.

Missing loads, largest first:

- **WS2815 quiescent ~113–140 mA, always** — every pixel carries a second
  always-powered backup driver, which is the exact feature ADR 0014 bought the
  part for. ADR 0014's table is emission-only.
- **The ESP32-S3-Matrix's onboard 8×8 RGB matrix** — 64 addressable LEDs nobody
  budgeted, disabled or unpowered
- Buck conversion loss (~12 % of the 5 V branch)
- WiFi TX peaks to ~0.5 A

Corrected: **~410–430 mA on +12 V typical**, not 290 — about 34 % of a 1.2 A
Doepfer rail, not the "about 15 %, unremarkable" ADR 0004 claims. Everything
sized against 290 mA needs re-deriving.

### R16. Mod channels are unipolar-only — a permanent hardware limitation
*CV agent.*

MOD 1–4 are described as generic and assignable, but the analog stage is 0–10 V
only. They cannot produce a bipolar CV at all — no ±5 V LFO, no negative
excursion, no through-zero modulation. That forecloses a large part of what
"assignable modulation" means in a rack, permanently, in hardware.

**Proposed:** design the mod scaling for **−5…+10 V** (same fixed-offset trick
pitch already uses) and let firmware select the range per channel from the
display: 0–5 V, 0–8 V, 0–10 V, ±5 V. Costs 229 µV/LSB instead of 153 µV.

Also: research says the de-facto unipolar convention is **0–8 V** (Doepfer), with
0–10 V legitimate but aggressive. A 0–10 V breath CV into a destination
calibrated for 5 V reaches full effect at 50 % breath — the top of the dynamic
range does nothing, on the one channel where that matters most.

### R17. The polyfuse is at the wrong end, undersized, and its drop is unbudgeted
*Power agent.*

It sits at the **instrument's** umbilical entry, leaving 2 m of constantly-flexing
cable and both connectors — by far the most likely failure — upstream and
unprotected. ADR 0005's own stated purpose is stopping a fault from pulling on
the rack rail; a crushed cable does exactly that, on the far side of the fuse.

500 mA hold against a corrected 370–500 mA is 1.0–1.35×; standard practice is
≥2×, and PPTC hold derates ~−0.5 %/°C in a sealed warm body. Its 0.6–1.4 Ω
initial resistance is **0.24–0.56 V at 0.4 A** — several times the 84 mV cable
drop the entire 12-V-delivery argument was built on, and absent from the table.
Voltage rating is unspecified; a 6 V part on a 12 V rail fails destructively.

**Proposed:** move protection to the **module end** so the cable is inside the
protected zone, size for ≥2×, ≥16 V rated. Better: an eFuse / current-limited
load switch, which also provides the soft-start R9 needs.

---

## P0 — added by the final two reviews

### R31. The 74x165 chain and the MCP3202 cannot share MISO. Show-stopper.
*ADC agent. Verified independently.*

The 74x165 — any family — has **QH as a permanently driven totem-pole output
with no output-enable pin**. It is not an SPI peripheral and cannot be taken off
the bus. The MCP3202's DOUT does tri-state on CS high, so the shift register
wins the line unconditionally: **the ADC can never be read**, and two push-pull
drivers fight continuously (±24 mA on an LVC part).

This invalidates the stated justification in ADR 0003 for placing the breath
sensor at the top: *"Putting the breath ADC up there therefore shares an existing
bus. It costs a chip select, plus MOSI if the converter takes commands."* That
sentence is wrong, and the 0.09 ms tube delay follows from it.

**Fix is free.** ADR 0013 moved the display to the other MCU, so **both of the
S3's general-purpose SPI hosts are now unused on the real-time board**. Put the
DAC and the MCP3202 on one (both tri-state-friendly) and the 165 chain alone on
the other — it needs only MISO, SCK and a latch GPIO. One extra pin against 16
of headroom. ADR 0013's pin table also needs correcting.

### R32. Fire-on-first-sample removes the only thing hiding key-chain read errors
*ADC agent.*

Two individually defensible decisions are jointly dangerous. Asymmetric debounce
fires on the first closed sample, so **one corrupted 32-bit read produces one
spurious note-on at full velocity with zero filtering**. A conventional 20 ms
symmetric window silently absorbs single-sample bus errors; this design
deliberately removes it — and raises the chain's integrity requirement from
"mostly right" to "never wrong" without saying so.

Meanwhile the chain as specified has four weaknesses:

- **No ground return specified.** ADR 0001 says "four wires running the length of
  the body". Return current finds its own path — most likely through analog
  ground, injecting SCK edges into the breath path. The exact failure ADR 0003
  eliminates on the umbilical, reintroduced inside the instrument.
- **Electrically long and unterminated.** Round trip 3.6–4.0 ns at 14 in against
  1–2 ns LVC edges. Terminate when round-trip exceeds rise time — so yes. **This
  is an edge-rate problem, not a frequency problem: slowing the clock does not
  fix ringing.**
- **The BOM's reason for choosing LVC over HC is backwards.** On an unterminated
  line, LVC's stronger drive and faster edges are *worse*. 74HC165 at 3.3 V has
  ~±4 mA and 6–15 ns edges (no termination needed) and roughly **2× the input
  noise margin**. Either part works; the recorded rationale does not.
- **SH/LD is asynchronous and level-sensitive.** Any glitch below V_IL during the
  32-clock shift **re-loads all four registers and corrupts the whole word** —
  which, per the interaction above, becomes a spurious note.

**Fixes:** ground return per signal (highest value); chain the topology rather
than star it; 33–68 Ω series termination at the MCU; **order the chain so serial
data flows toward the clock source** so skew eats setup margin (recoverable by
slowing down) rather than hold margin (not recoverable at any speed); require
**2 consecutive agreeing samples** before a note-on (125 µs at 8 kHz, inaudible);
and use 4–6 of the 14 spare chain bits as a **fixed marker pattern** so a
corrupted frame is detectable and countable rather than silently becoming a note.
That last one costs nothing — the pins, wires and devices already exist.

### R33. The complementary filter is the wrong estimator, by ADR 0007's own logic
*ADC agent.*

Gyro noise is irrelevant — 0.026° over a 3 s gesture. **Bias is the entire
story**, and a complementary filter's steady-state error from bias is exactly
`b·τ`. Published practice sets τ = 0.5–5 s to reject linear-acceleration
contamination, which produces a pincer:

- At τ ≥ 0.5 s the accel correction has barely acted inside a gesture anyway —
  **inside the gate window it is already approximately gyro-only**
- But it still carries the accel term's contamination: a 0.5 g jab makes
  accel-derived tilt read **26.6° wrong**, injecting ~10° of bogus tilt exactly
  when the player is making the gesture
- Shortening τ makes contamination worse

ADR 0007 rejects the BNO085 because "fusion works against the signal of
interest" — then selects a crude fusion with **no acceleration gating at all**.
The reasoning, followed properly, eliminates the filter it chose.

**Proposed:** three independent estimators that do not fight.
**Gated tilt: bias-snapshot gyro integration, no accelerometer** — average the
gyro for 0.2 s before the gate press to estimate bias, giving **~0.1–0.2° over a
3 s gesture** and complete immunity to linear acceleration. **Roll: low-passed
accelerometer only.** **Shake: high-passed raw accelerometer.**

### R34. The IMU read does not fit the loop, and the budget has no row for it
*ADC agent.*

The ESP32-S3-Matrix wires the QMI8658 to **I2C** (SPI not brought out). A 12-byte
accel+gyro read at 400 kHz is **~363 µs** — does not fit a 250 µs loop, let alone
125 µs. And an I2C read is blocking and clock-stretchable, so a stuck bus stalls
the output loop.

**Fix:** decouple entirely — read at 200–500 Hz in a lower-priority task,
**match the QMI8658's ODR to the read rate** (reading a 1 kHz stream at 250 Hz
aliases the IMU), use FIFO + INT, non-blocking driver with a timeout. Add an IMU
row to the latency budget.

### R35. AGND must be bonded at one end only, and nothing says so
*Umbilical agent.*

If AGND lands on the module's ground plane — the natural thing for anyone reading
the schematic — the three ground conductors become parallel returns. AGND then
carries ~97 mA of the 290 mA, and the INA134 sees **18.1 mV of breath-correlated
offset** (it tracks LED brightness, which tracks breath) → ~40 mV on the CV.

**The two versions look identical on a netlist.** This must be a written rule,
not a note:

> `AGND` connects to the instrument's analog ground star point **at the
> instrument end only**. At the module end it connects to **the receiver's
> inverting input and nothing else** — not to a ground pour, not to a stitching
> via.

## P1 — added by the final two reviews

### R36. MOSI/CS sharing one twist with no return is a functional failure risk
*Umbilical agent.*

Two independent signals in one twisted pair is the textbook worst case — the
twist exists to couple them to each other. Backward-crosstalk coefficient
≈ 0.3–0.4, so **a 3.3 V MOSI edge puts ~1 V on CS for ~20 ns**, against the
74AHCT125's 0.8 V V_IL. CS is static exactly when MOSI is the aggressor. A false
SYNC edge on the DAC8568 corrupts frame alignment and writes garbage to a CV
output.

It is also the only pair in the cable that radiates, turning a balanced-pair
problem into a common-mode problem on the whole bundle — rejected only by the
receiver's CMRR **at MHz**, which is ~40–50 dB, not 90.

**Proposed reassignment** (recommended): recover the CS conductor by regenerating
SYNC at the module from clock idle, then every signal has its own return:

```
Orange 1,2   +12V / PWR_GND      keep together - this pairing is correct
Blue   4,5   SCLK / DIG_GND_A
Green  3,6   MOSI / DIG_GND_B
Brown  7,8   BREATH / AGND       max pin distance from the power pair
```

**Crosstalk SPI→breath is a non-problem** and the design is over-worried about
it: Cat5e NEXT is 65.3 dB at 1 MHz, and rising/falling edge areas cancel through
a 500 Hz pole to ~0.3 µV against a 153 µV LSB. The two ways it *does* become
in-band are both design errors, not physics: rectification if the filter sits
downstream of the amplifier, and common-mode conversion from the unbalanced
twist.

### R37. Hot-plug: 30 A inrush into a 1.5 A contact
*Umbilical agent.*

etherCON has **no sequenced contacts** — all 8 mate within ~1 mm in unpredictable
order. With a 0.4 Ω loop, peak inrush is **~30 A, 20× the NE8FDP's 1.5 A per
contact rating**. It arcs, and gold flash erodes fast over the few hundred plug
cycles an instrument sees. It also drags the rack rail down hard enough to glitch
other modules.

Moving the make to the module's toggle does not fix it — it just arcs a 6 mm
toggle instead.

### R38. Solid-core Cat5 will fatigue-fracture; no cable is specified at all
*Umbilical agent.*

ADR 0004's whole etherCON argument is "any Ethernet patch cable works", and most
cheap Cat5e is **solid core** — which work-hardens and fractures under repeated
flex. ADR 0004 itself says the cable flexes at the connector every time the
instrument is played. A broken strand in AGND is an intermittent 54 mV breath
offset: the worst possible fault, because it will look like a firmware bug.

**The BOM has no cable line item and no etherCON cable carriers (NE8MC-1).**
Specify: stranded, flexible/tour-grade **F/UTP** Cat5e, 2 m, made up with
etherCON carriers at both ends. Shield terminated **both ends** (the usual
one-end advice is moot — three ground conductors already tie the ends together)
and bonded to the aluminium key plate at the instrument end, which also stops
that plate floating against the player's face.

### R39. No anti-alias filter before the ADC
*ADC agent.*

The signal is band-limited by the sensor (~159 Hz); the **noise is not** — the
MCP6002 has ~1 MHz GBW and passes switching ripple, SPI crosstalk, WS2815 data at
800 kHz. A buck at 500 kHz sampled at 8 kHz folds to **4.0 kHz**; at 496.1 kHz it
folds to **100 Hz — directly into the breath band**, indistinguishable from
playing, and the alias frequency moves with the converter's load-dependent
switching frequency.

**Fix:** one 220 nF cap at the ADC pin → ~600 Hz corner, **58 dB at 500 kHz**,
and it doubles as the charge reservoir for the MCP3202's sample capacitor,
fixing the source-impedance problem at the same time.

## P2 — added by the final two reviews

- **R40. The SAR-vs-delta-sigma rule is wrong by 10× as written.** *(ADC agent.)*
  A sinc³ decimator at 8 kHz ODR costs **187 µs**, not "potentially
  milliseconds" — the folklore comes from 50 Hz weigh-scale parts. And the rule
  is self-inconsistent: firmware oversample-and-average *is* a sinc¹ decimator,
  and N=8 at 8 kHz costs **440 µs — more than a sinc³ at the same output rate**.
  Keep the SAR (right call on cost and simplicity) but **restate the rule as a
  number** — "converter group delay under 200 µs" — or it will wrongly veto a
  better part later.
- **R41. MCP3202 cannot take 2 MHz SPI at 3.3 V.** f_CLK ≤0.9 MHz at 2.7 V,
  ≤1.8 MHz at 5 V → **~1.1 MHz at 3.3 V**, against ADR 0001's 2 MHz bus. Not a
  redesign (per-device clock rates are supported) but it must be written down or
  it returns subtly wrong codes with no error.
- **R42. 12 bits bites in exactly one place: the bottom of a gamma curve.** At
  γ=0.5 and 1 % of full scale, low-end steps are magnified 5× — a 2.44 mV DAC
  step becomes **14.6 cents**, audible on quiet passages. Free fix: **two taps
  off one sample stream** — raw for the note gate (needs speed), N=8 decimated
  (+1.5 bits, 0.44 ms) for mod/MIDI/display (needs bits).
- **R43. Sensor range is wrong in the docs.** MPXV4006GP is **0.26–4.86 V at
  Vs=5.00 V**, not 0.2–4.7 V. At Vs=5.25 V the divided max is 3.06 V into a 3.3 V
  reference — it fits, with less margin than the document implies.
- **R44. ADR 0007's "no onboard fusion" is factually wrong.** The QMI8658 has an
  on-chip Motion Co-Processor with a 6DOF/9DOF AttitudeEngine. Does not change
  the decision; the record should be right.
- **R45. Package policy conflicts with the IMU upgrade path.** The obvious better
  parts (ICM-42688-P, LSM6DSV) are 0.5 mm LGA/QFN, which ADR 0013 explicitly
  lists as avoid. So "put a better part on the custom board later" is not
  actually available under current policy. Note the exception or accept the
  QMI8658 as the long-term part.
- **R46. Accel gain is pivot-dependent.** The pivot moves between neck strap,
  hands and wrists, so the same jab reads **2–3× differently** between postures.
  Normalise the shake channel against its own recent peak — the same class of fix
  as the capture-on-press gate.
- **R47. Ambient zeroing should be continuous, not startup-only.** A gauge sensor
  with temperature-dependent offset, in a body warmed by breath and LEDs, over a
  session. The mechanism already exists (the spare DAC offset channel); decay the
  zero toward the current reading whenever breath has been sub-threshold for ~2 s.
- **R48. No controller-side decoupling in the BOM at all.** The only
  `C-DECOUPLE` line is module-side. **For a VDD-referenced ADC the decoupling
  capacitor *is* the voltage reference.** Each remote 165 board needs its own
  100 nF or its ±24 mA edges brown out the local rail on every clock.
- **R49. 5 V-before-3.3 V sequencing drives ~2.5 mA into the ADC's ESD diode**,
  at or over the family-typical ±2 mA clamp limit. Size the upper divider
  resistor ≥10 kΩ (which needs R39's cap to still settle).
- **R50. Three documents disagree on the umbilical rate**, and the 8 kHz end of
  "4–8 kHz" does not close: ADC 24 µs + keys 16 µs + six DAC channels 96 µs =
  **136 µs against a 125 µs period.** Either state the loop is 4 kHz or re-derive.
- **R51. The latency budget omits the sampling period entirely.** Sampling at
  4 kHz adds 0–250 µs of age before conversion, so real ADC-path latency is
  ~150–280 µs, not the 50–200 µs stated.
- **R52. Release latency is not free on a woodwind.** Fingerings are
  combinational — lifting a finger is how you *start* the next note. A 10 ms
  release window delays the new note by 10 ms, landing in the territory the
  attack-latency work was protecting. Apply the release filter to the **note
  decision**, not to each key independently.
- **R53. The release window is being sized from the wrong measurement.** For an
  MX-style switch the dominant release-side number is the **actuation/reset
  hysteresis gap**, not contact bounce. A slow deliberate release — exactly what
  a woodwind player does on a legato phrase — can park the plunger in that gap
  and chatter for tens of ms. Gateron publishes neither figure for the KS-33.
  Extend the M1 measurement to slow press, slow release, and a worn switch.

## P2 — worth fixing, lower stakes

- **R18. Two-point calibration does not remove DAC INL.** *(CV + pitch agents.)*
  ±4 LSB typ / ±12 LSB max = 0.66–2.0 cents of curvature no two-point fit can
  touch. Mutable's Yarns uses a **12-point** table for exactly this. Make the NVS
  table multi-point (~one per octave, ~40 bytes). Also put the two anchor points
  **inside the musically used range**, not at −2/+7 where no VCO tracks well.
- **R19. DAC8568 grade unspecified.** A/C grades reset to zero scale, **B/D reset
  to midscale**. The BOM says only "DAC8568". At midscale the pitch output parks
  a VCO octaves up and all four mod outputs sit at half scale from rack power-on
  until firmware writes. Specify the full orderable part number. Also: the
  internal reference is **disabled by default** and needs an explicit enable
  write — a known DAC8568 bring-up trap.
- **R20. No clamp diodes at the CV jacks.** *(CV + power agents.)* Defensible —
  most modules rely on the series resistor plus the op-amp's ESD structures. But
  with a long external umbilical it is ~6 parts. **Use BAV99 (silicon), not
  BAT54S (Schottky):** Schottky leakage of 2 µA through 1 kΩ is 2 mV = **2.4
  cents of temperature-dependent pitch error**, reintroducing exactly what the
  LT5400 was bought to remove.
- **R21. My tube resonance model was wrong.** I used quarter-wave (c/4L) giving
  2858 Hz. With a trap volume at the end it is a **Helmholtz resonator**: at 3 mL
  it lands at **323 Hz — below the 500 Hz filter corner**, so it passes straight
  through. Trap volume and response time are coupled and the ADR treats them as
  independent. Fix with a deliberate restrictor (~0.4 mm orifice → 788 Hz pole)
  and specify trap volume ≤1 mL. A porous PTFE plug does this and doubles as the
  moisture barrier.
- **R22. Condensation is underestimated in kind.** NXP states this sensor family
  is qualified on **dry air**, is "NOT compatible with water or water vapors",
  and that the **gel die coat swells when wet, causing unreliable readings**.
  Exhaled breath is ~100 % RH. At 6 kPa the tube air compresses ~6 %, so every
  note pumps saturated air toward the die. Add a **hydrophobic PTFE membrane
  vent** at the sensor port, not just a trap.
- **R23. 2 kHz on the mod channels leaves audible ZOH images.** *(CV agent.)*
  Software smoothing band-limits content; it cannot remove images the DAC creates
  after it. A 400 Hz IMU signal puts an image at 1.6 kHz only **12.6 dB** below
  the modulation, and a 15 kHz filter adds −0.07 dB. My own bounding argument in
  ADR 0006 cites 4 kHz while the table specifies 2 kHz, and conflates amplitude
  quantisation with time quantisation. **Raise mod to 8 kHz and/or give the mod
  channels a 2-pole filter at 500 Hz–1 kHz** — they want a *slower* filter than
  pitch, not the same one. The ADR has it backwards.
- **R24. Pitch at 2 kHz contradicts portamento.** *(Pitch agent.)* A 1-octave
  glide in 100 ms at 2 kHz is 5 mV steps = **6 cents per step** at an audio-band
  rate, which is the staircase argument used to keep breath analog. Run pitch at
  8–16 kHz at least while moving; the link budget allows it easily.
- **R25. My stated reason for the fast pitch filter is wrong.** *(CV agent.)* A
  2 kHz corner settles a 1 V step to 1 cent in 0.56 ms — inaudible as glide. You
  would need a corner below ~100 Hz for "audible glide" to be true. The filter is
  a DAC-glitch snubber, not a reconstruction filter, and choosing 10–20 kHz for a
  reason that does not apply forfeits free image rejection. Restate the
  requirement as settling time and set 2–5 kHz. *(Note: the pitch agent argues
  10–20 kHz is fine. Disagreement — resolve in review.)*
- **R26. Panel pot control law and reference.** *(CV agent.)* If the gain pot is a
  plain 0–1 attenuator ahead of a fixed 2.2× stage, every useful setting lives in
  the top 45 % of rotation. Add a series resistor at the bottom of the pot to
  reshape the law. **And never reference the offset pot to the raw ±12 V bus** —
  rack ripple would land on the breath CV as DC wander, on the one channel most
  work went into keeping clean.
- **R27. +5 V has no protection while ±12 V does.** A row-offset insertion on the
  16-pin header can land +12 V on the +5 V pins. DAC8568 absolute max VDD is 6 V.
  ADR 0004 says shrouding and keying are "not worth trusting" for ±12 V and then
  trusts them completely for +5 V. **Clamp** (5.6 V zener / TVS after the
  ferrite), do not add series drop — the DAC span was hard won.
- **R28. Hot-plug mating order.** etherCON contacts mate in arbitrary order. If
  +12 V makes before PWR_GND, the full return current finds its way home through
  DIG_GND or AGND — i.e. through the INA134's reference input.
- **R29. Ferrite bead current rating.** 0805 600 Ω parts are commonly rated
  **300 mA**; both +12 V branches now exceed that at the corrected budget, and a
  saturated bead loses its impedance entirely. Use 1206/1210 rated ≥1 A.
- **R30. The branching scheme does not work at the frequencies that matter.** A
  ferrite bead is a wire at the WS2815's ~2 kHz PWM rate, and 47 µF does not hold
  the rail against a 200–400 mA square wave. Outcome is probably survivable
  (~90 dB PSRR at 2 kHz) but **the reasoning in ADR 0004 is wrong**, and the
  second claimed job — keeping the module out of the rack — is not done at all,
  since both branches are common upstream at the bus header. **Bulk belongs at
  the load:** 470–1000 µF at each WS2815 feed point, and a real LC (10–47 µH, not
  a bead) between the umbilical node and the buck input.

---

## S — Systems review (cross-subsystem; invisible to the siloed reviews)

*These sit between the six agents' scopes. Several invalidate the premise of a
finding another agent made. There was no mechanical, thermal or failure-mode
agent, and that is where the damage concentrated.*

### S1. ADR 0009 and ADR 0014 assign the same two side channels to different things. **Both Accepted.**

- **ADR 0009:** the two side channels flanking the switch column are *"the natural
  route for the wiring looms."* ADR 0013 repeats it.
- **ADR 0014:** *"the free volume is the two side channels … one run per side"* —
  for the LED strips.

There are two channels. The LEDs claim both. ADR 0014 then instructs *"keep the
LED runs and their return physically away from the breath buffer and its wiring
inside the instrument"* — **which is unsatisfiable given the geometry both ADRs
describe.** Everything that runs the length of the body has one route, shared
with the pulsed LED current.

**This defeats the AGND argument mechanically, and it is unfixable after
bonding.** Highest-priority contradiction in the project.

### S2. The analog-return rule stops at the connector. Inside the body there is none.

ADR 0003 proves at length that the breath pair needs a return carrying no power
current over 2 m of umbilical. **The identical problem exists over ~400 mm inside
the instrument and no ADR addresses it.** Sensor at the top, connector at the
bottom — the analog signal traverses the whole body.

R35's rule says AGND bonds to *"the instrument's analog ground star point"* —
**no such star point is defined anywhere in the documentation.** The rule
references an object that does not exist.

### S3. ADR 0003's sensor placement has lost its rationale.

Option A (sensor at top, 30 mm tube) was chosen because *"putting the breath ADC
up there shares an existing bus."* **R31 proved that false** — and R31's own fix
moves the ADC to a separate SPI host. The reason is gone.

Three forces now push the sensor *away* from the top: routing (S1), thermal (S5
— the display board with AMOLED and WiFi is the hottest item and ADR 0013 puts
it in the same zone as a temperature-sensitive gauge sensor), and serviceability
(the EOL, moisture-sensitive, most-likely-to-fail part is sealed into a body
that cannot be reopened).

**Decision needs re-taking.** Candidate: a serviceable mouthpiece sub-assembly
external to the bonded lamination, with only a shielded pair entering the body.

### S4. The LED safety clamp does not survive the failure it guards.

A positive-feedback path closes through the protection device:

> LED current ↑ → umbilical current ↑ → PPTC self-heats, resistance rises → rail
> sags → buck draws more input current → PPTC heats further → brownout → MCU
> resets → **strips hold their last latched colour** → load does not fall

Corrected budget 410–430 mA against a 500 mA part that derates ~0.5 %/°C in a
10–20 K interior: **~0.95× hold before any transient.** Above hold a PPTC does
not trip cleanly, it gradually current-limits, so the MCU misbehaves at reduced
voltage before it resets.

**And ADR 0014's firmware brightness clamp is the only thing between a display
bug and a rack brownout — it is gone the instant the MCU is what failed, and
WS2815s latch.** Fix by bounding the worst case in hardware: choose strip
density so all-white is inside budget (30/m ≈ 0.5 A vs 60/m ≈ 1.0 A), treat the
firmware clamp as aesthetic only, and blank the strips as the first act at boot.

### S5. Thermal: ~5 W in a sealed insulator, and the breath zero is the casualty.

Oak (k≈0.16) and acrylic (k≈0.19) are insulators; the aluminium plate is the only
real path and **the player's hands cover part of it**. Bounding case ~21 K; call
it **10–20 K interior rise over 10–20 minutes.**

**This promotes R47 (continuous auto-zero) from P2 to required** — the startup
zero is captured cold and goes stale. Combined with R12's knob-dependence, this
is the mechanism behind "the VCA drones quietly after twenty minutes."

Counter-intuitively the rise is *protective* against condensation at steady state
(exhaled dew point ~34 °C). **The danger windows are the first ten minutes and
the cool-down**, when the cavity contracts and pumps humid air back in through 18
unsealed switch cutouts.

### S6. The LED/breath loop is real, but the symptom is not what was expected.

Traced both ways. **Through the CV path it is negative** — more breath → brighter
LEDs → AGND rises → CV reads lower. Loop gain ≈0.004, so a 0.4 % gain
compression, never an oscillation.

**Through the ADC it is positive**, via VREF depression from shared-ground LED
current. Also far from instability — **but the symptom is note-gate chatter, not
gain error.** At the breath threshold, LEDs lighting shifts the reading in the
direction that keeps them lit: latch on one side, chatter on the other.

Two free fixes: **size note-on/off hysteresis from the measured LED-induced
step**, and **drive the LEDs from the post-gate slew-limited value, not the raw
ADC sample.**

### S7. R12's proposed fix is not implementable.

R12 says *"do the zero subtraction in the instrument."* **The instrument has no
DAC** — ADR 0013 states it in bold, and the S3 dropped the original ESP32's DACs.
The fix needs PWM + RC off the S3 (viable; R12 already wants a ~1 Hz pole) or a
small SPI DAC on the carrier. **State which, or R12 silently does not get built.**

Root cause: ADR 0004 claims the instrument is *"purely digital: no analog signal
path"*, which is already false — it carries the sensor, the buffer and the analog
drive. That false claim is what let R12 through.

### S8. The aluminium plate is unbonded, and which ground it bonds to is undecided.

Nothing bonds the plate. It floats under the player's hands, 1–2 mm from 18
switch pins, wired to shift-register inputs. **R32 established that asymmetric
debounce turns one corrupted read into one spurious note-on at full velocity.**
So the instrument fires random notes when touched in a dry room — and it will be
blamed on firmware forever.

**It must bond to `PWR_GND`, never `AGND`.** Bonding to AGND puts the player's
body capacitance directly onto the breath channel's voltage reference.

### S9. Silent failure modes — the top three are free to fix and none is on the roadmap

Ranked by how silently they fail:

1. **Blank or corrupt NVS → default calibration.** Defaults are `a=1, b=0`
   against an analog stage deliberately built 5 % high → **plays, sounds like an
   instrument, is ~85 cents out, with zero indication.** More silent than a crash
   because everything works. *(Partly superseded — the 5 % bias is deleted by the
   trim-pot decision — but an uncalibrated state still needs to be loud.)*
   → CRC the cal blob; a hard UNCALIBRATED state the player cannot miss.
2. **Stuck-closed switch.** Does not kill a note — silently returns *different*
   notes for every fingering involving it. Presents as "some fingerings feel
   wrong." Unfalsifiable by ear, in a body that cannot be opened.
   → Flag any key closed at boot or held > N seconds as suspect, and report it.
3. **Stale breath zero from thermal drift** (S5) + knob-dependence (R12).
   → R47 continuous auto-zero, now required.

Also notable: **E9 calibration performed into the wrong load** (R3) — the
milestone the ROADMAP calls decisive **passes while being wrong**.

### S10. Bring-up sequence problems

- **E11 tests a ground topology that will not exist in the finished instrument.**
  At E11 (Phase 3) the LED strips are not installed — they arrive at M6, Phase 4
  — and the body is not bonded, so the loom under test is not the final loom.
  **The single test validating the entire analog-breath decision runs on a
  topology that changes afterwards, and cannot be re-run after M7 without
  unbonding.** → Add a gate: re-run the full E11 breath-noise test on the final
  harness, in the assembled-but-unbonded body, as the last act before closing.
  **Most important missing milestone in the project.**
- **E8's done-when would reject a corrected board** — it requires gain ~5 % over
  target, which the trim-pot decision deletes. Rewrite it.
- **E2 cannot validate what it claims.** "Stable reading" is achievable with a
  syringe and proves nothing about the pneumatic system, where the risk is.
  Re-scope to require a mouthpiece, tube, trap and a human playing for 20 minutes.
- **M5 cuts the aluminium plate (Phase 3) before the carrier PCB exists (E13,
  Phase 4)** — the most expensive irreversible part is committed before the board
  layout it constrains is designed.
- **E13 and M7 are in the same phase with a hard dependency** — you cannot mount
  electronics before the carrier exists, and the carrier *will* spin (R31 alone
  changes its SPI topology). → Rule: **the body does not close until the carrier
  is revision-final and burned in.**
- **Nothing is re-proven on the carrier.** E1–E11 all run on dev boards.
- **No thermal soak, no two-hour play test, no failure injection, no pre-bond
  self-test.**

### S11. Structurally absent

- **No self-test / diagnostic mode.** Nothing exercises all 18 switches, both LED
  strips, the IMU, six CV channels and the umbilical before the body is bonded
  shut. **Highest-value missing firmware in the project — build it before M7.**
- **No error reporting path to the player.** The display is "status only". No
  channel for uncalibrated, config rejected, CRC errors, stuck key, brownout,
  version mismatch. **Every silent failure above is silent partly because this
  does not exist.**
- **No watchdog / stuck-CV failsafe.** If the real-time board hangs mid-note the
  DAC holds its last value and the rack drones forever. → "no valid frame for
  N ms → assert CLR" at the module is a few gates.
- **No umbilical presence detect.** ADR 0004 deleted MISO arguing *"+12 V is
  itself evidence"* — **but nothing senses +12 V.** The evidence exists and is
  not read.
- **No spare-conductor policy.** Internal looms are hand-built once into a stack
  that cannot be reopened. **Run two spares in every internal loom — free now,
  impossible later.**
- **No conformal coating anywhere in the BOM**, for a body breathed into for
  hours behind 18 unsealed switch cutouts.
- **The U-bolt adjustability requirement is impossible as written.** ADR 0009
  requires a slot *"so balance can be tuned empirically after assembly"* — and
  the backing plate is inside a bonded cavity. Either it is reachable from
  outside, or the stack must be **dry-assembled, hung, balanced, and only then
  bonded**. Nobody wrote that sequence down.

### S12. Proportionality — what to consciously decline

*(This is the part worth heeding: 53+ findings can kill a hobby project.)*

**Decline outright:** the in-loop feedback compensation for R3 (take the 100 Ω
fallback — it saves 5 cents for a compensation redesign and a phase-margin
check); a 12-point calibration procedure (leave the NVS schema able to hold N
points and stop); clamp diodes at the jacks; CS regeneration at the module (take
series resistors + a Schmitt receiver instead); the LC redesign beyond bulk at
the LED feeds; the filter-corner argument between agents (neither is audible —
take the two free actions and stop).

**Delete the instrument power switch entirely.** It cannot be built as specified,
its replacement is a P-FET circuit with an RC, it creates a third undefined "off"
state, and the module toggle two metres away already does the job at the source.
**One fewer thing inside a body that cannot be opened.** The one place where the
right answer to a P0 is "remove the feature."

**Hold the line on not designing a custom ESP32-S3 carrier.** ADR 0013 already
declined it. Every finding that makes the carrier more complex is an argument
someone will use to reopen it, and it is the single biggest scope risk here.

## F — Stress-test of the proposed fixes

*Eight proposed remedies were stress-tested for whether they work, what they
break, and whether anything simpler exists. Three changed materially.*

### F1. "Feedback from the jack side" would oscillate as described

Putting Riso inside the loop puts the `Riso·C_load` pole inside the loop too:

| Load | Pole |
|---|---|
| 2 m patch cable (~200 pF) | 796 kHz |
| Multed, 3 cables (~600 pF) | 265 kHz |
| Cable + a destination input cap (~2 nF) | **80 kHz** |

OPA2197 crosses ~5 MHz at noise gain 2, so that pole contributes 80–89° of excess
phase at crossover. **Naked in-loop 1 kΩ is unconditionally unstable into a patch
cable** — a several-MHz oscillation that rectifies in the destination VCO's input
and shows up as *a tuning offset that changes when you touch the cable.*

**But the correct version is cheap, not risky.** TI's Riso + dual-feedback needs
**one capacitor, and that capacitor replaces the separate pitch output RC** —
which was going to be fitted anyway. So it is not an added part.

**It also closes the R24/R25 filter-corner disagreement**: the dual-feedback Cf
sets the corner at ~3.4 kHz by construction, and the requirement becomes a
settling-time number rather than an argument.

**Reserve footprints for both the Cf and a 100 Ω rollback**, and let the bench
decide.

### F2. Four pairs of fixes are mutually incompatible

This is the section that matters most, and none of it is visible from inside a
single finding.

1. **SYNC regeneration (R36's conductor saving) and the SPI split (R31) are
   directly incompatible.** The split puts the ADC on the same host as the DAC, so
   a clock-idle-derived SYNC would assert during every ADC read. **Adopt the
   split, reject SYNC regeneration.**
2. **An instrument-side power switch and R13's OE gating are incompatible.** With
   the switch at the instrument, *"+12 V present on the umbilical"* no longer means
   *"instrument alive"* — so gating the level shifter's OE from +12 V presence
   fails in exactly the state it exists for. **Moving the switch to the module
   resolves both**, which is why the relocation matters more than the part choice.
3. **The in-loop Cf and ADR 0006's separate 10–20 kHz pitch output filter are the
   same component and must not both be built.** The reconstruction cap after the
   1 kΩ *is* the C_L inside the compensation design. Design them together or you
   get a filter you did not intend and a phase margin you did not compute.
4. **A DAC-channel offset and the pitch offset trimmer are alternatives, not
   additions.** Two offset authorities in series is the split-brain failure
   ADR 0013 avoids by rule elsewhere. **Trimmer for pitch** (already decided);
   **DAC channel for the four mod channels** — and that has a property nobody
   claimed for it: it makes the mod outputs **park at 0 V at rack power-on rather
   than −5 V.**

### F3. Verdicts on the eight

| Fix | Verdict |
|---|---|
| In-loop Riso (pitch) | **Adopt as dual-feedback**, not as described. One cap, replaces the output RC |
| Respec to −2.5…+7.5 V | **Superseded** by the trim-pot decision. The 0.25–4.75 V window already gives the headroom |
| Mod channels −5…+10 V | **Adopt.** Costs less than claimed; take the DAC-channel offset with it |
| Split the SPI | **Adopt.** Unambiguously right, free, and it improves the loop budget |
| Bias-snapshot gyro | **Adopt the conclusion, reject the mechanism** — see F4 |
| P-FET power switch | **Adopt the intent, reject the location.** Load-switch IC at the *module* |
| Marker bits in spare chain bits | **Adopt, and be honest about the blind spot** — see F5 |
| SYNC regeneration | **Reject outright.** Unsound, silent failure mode, incompatible with the SPI split |

### F4. The bias snapshot was naive; the correct version is the hybrid

A fixed 0.2 s pre-press window fails if the player is already moving when they
press the gate — which is exactly when they would. **Correct version: a
continuously-maintained, stillness-gated bias estimate**, with the pre-press
window ending ~50 ms before the press and a validity check. Same cost, no
runaway. This is the hybrid between "gyro only" and "complementary filter".

### F5. The marker pattern is a framing check, not an error-detecting code

It catches nearly all of the dominant failure modes — a glitch on the
level-sensitive SH/LD reloading mid-shift, double-clocks, clock-count errors —
and **roughly 80 % of isolated single-bit data errors are invisible to it.**

Write that limitation into the ADR rather than letting it imply frame integrity,
and pair it with the two-consecutive-samples rule, which is what actually covers
the blind spot. Use mixed polarity — one high and one low per package.

### F6. Accept-and-document, rather than engineer

- **If the 100 Ω rollback is taken:** *"Pitch output impedance is 100 Ω.
  Calibrate against the patch you will use. Changing how pitch is multed shifts
  tuning by up to 6 cents."* A real, liveable constraint for one person's rack.
- **The top of the pitch range**, if the DAC runs from rack +5 V: measure the
  actual saturation code at the actual rail and **document the achievable
  maximum as a measured number** rather than claiming +7 V.
- **The mod channels' non-exact zero** — a few millivolts, calibrated once into
  NVS. Not worth hardware.

### F7. Build order, for a one-off

**Tier 0, before any PCB is drawn** — permanent, unrecoverable in firmware:
split the SPI (and correct ADR 0013's pin table: +2 pins, not +1); mod channels
at −5…+10 V with a DAC-channel offset; move the power switch to the module as a
current-limited load-switch IC and **delete `SW-PWR-INST`**; in-loop dual
feedback designed together with the filter it replaces, with a 100 Ω rollback
footprint; and **decide the DAC's AVDD source** — rack +5 V and document the
top-of-range loss, or a local 5.0–5.5 V regulator that fixes R5 properly and
neutralises R27.

**Tier 1, same board revision:** R13's pull resistors; R39's 220 nF at the ADC;
R48's 100 nF per shift register; 220 Ω series on MOSI (which makes SYNC
regeneration unnecessary); 1 kΩ on the pitch op-amp's + input; ferrites rated
≥1 A; 470–1000 µF at each strip feed; marker bits wired now, since they cannot be
retrofitted into a bonded body.

**Tier 2, firmware before the first play test:** stillness-gated bias estimate;
two-consecutive-samples rule; marker check with hold-previous-frame and a visible
error counter; enable the DAC's internal reference at boot; default all mod and
breath ranges to **0–8 V**, bipolar explicit per channel.

**Tier 3, bench, in order:** DAC saturation vs AVDD; pitch DC load sweep across
open/100 k/50 k/33 k; pitch stability into worst-case cable capacitance; inrush
with a current probe on both switch-on and hot-plug; gate-press-while-moving IMU
test; key-chain error counter over an hour with LEDs and WiFi active.

**One note on priority:** the stress-test flags that **R8's precision 5 V
reference for the breath sensor has a better cost/benefit than several of the
eight fixes** — it addresses ~30 dB of ratiometric error, against the 0.13 mV
the AGND path contributes that the ADRs spend pages on.

## V — Verification pass: what survives, what does not

*A seventh agent was told to falsify the others rather than extend them. Several
findings do not survive, including one this document asserted confidently.*

### V1. Contradictions, resolved

**Pitch filter corner: 5 kHz — and it should never have been a finding.** Any
corner from 3 to 20 kHz satisfies every real requirement; 5 kHz settles a
full-range step to 1 cent in 296 µs, 30× inside the glide-perception threshold,
with 4× better glitch and EMI snubbing than 20 kHz. **What is wrong is the
stated reason in two documents, not the number** — for a corner to produce
perceptible glide you would need ~74 Hz, so "audible glide" is wrong by 2.3
decades. Image rejection is *not* a criterion on pitch: a ZOH DAC emits no image
energy at constant code, and during a bend the result is FM at ~−110 dBc.
Restate the requirement as a settling-time number and the argument disappears.

**Breath receiver: (c), a true in-amp (INA821/INA828).** And **my objection to
buffering both legs was backwards** — buffering does not defeat the sense
return, it *perfects* it: the INA134's −IN leg draws ~160 µA through AGND today;
an OPA2197 input draws ~5 pA. Seven orders of magnitude.

R10 is **confirmed against TI's own datasheet**, which states a 10 Ω mismatch
degrades INA134 CMRR to ~74 dB — exactly 50 kΩ/10 Ω. But R10 **understates its
own case**: a 100 kΩ pulldown on +IN parallels the internal 25 kΩ to give
CMRR ≈ **19 dB**, not the 40 dB claimed. And **R10's own proposed patch is
wrong** — mirroring the pulldown on AGND does not symmetrise the way a series
element does. The correct fix is a pulldown **differentially across
BREATH–AGND**. With an in-amp, R14's protection-vs-CMRR conflict evaporates
entirely and its REF pin becomes the natural injection point for the ambient
zero.

**74LVC165 vs 74HC165: keep LVC, fix the rationale.** Neither agent was right.
The decisive point both missed: **SCK and SH/LD are driven by the ESP32, not by
the registers** — so family choice affects only the last QH→MISO hop, the least
critical line in the chain. The signals that actually ring keep their 1–2 ns MCU
edges either way. The "2× noise margin" claim is wrong (it compares HC at 5 V
against LVC at 3.3 V; at 3.3 V LVC has the better HIGH margin and HC the better
LOW). **The real levers are series termination and the S3's configurable GPIO
drive strength** — the latter free and mentioned by nobody.

**Current: 300 mA typical, 600 mA peak, ~1.25 A ceiling.** The WS2815 idle
figure is **unresolved by 17×** between two secondary sources, and R15 took the
high one from a snippet. R15's "410–430 mA" is only true if that figure is right
— mark it a **precondition**, not a finding. Also: ADR 0004's "about 15 %,
unremarkable" is wrong either way — honest figures are ~25 % typical, ~50 % peak.

### V2. Findings that are WRONG

- **R4's premise is false.** "Matched networks come as 1:1:1:1 or 10:1" is not
  true — the LT5400 family includes 1:1, 1:4, 1:5, 1:9 and 1:10, and the
  LT5400-7 (1.25 k/5 k) builds a gain of **exactly 1.800** from on-chip resistors
  alone. **The recommendation survives for a different reason:** gain 1.8 needs
  the *full* 0–5 V DAC span, which walks into R5; gain 2 makes 9 V from a 4.5 V
  window and buys 250 mV of headroom at each rail. *(Already superseded by the
  trim-pot decision, which reaches the same place — but the reasoning recorded
  in this document was wrong.)*
- **R37's arcing claim is physically impossible.** The minimum arc voltage for
  gold contacts is ~15 V. **A 12 V rail cannot sustain an arc on gold.** There is
  molten-bridge transfer and mechanical wear over a few hundred cycles; there is
  no arc. The 30 A figure is also overstated ~4× — it assumed a zero-impedance
  loop, while the review's own findings supply 1.6–3 Ω of it. Real peak 4–7.5 A.
  **P1 → P2.**
- **R33's central argument is self-defeating.** `b·τ` is the complementary
  filter's bias-induced error — but it is a **steady-state constant, and
  capture-on-press subtracts exactly that.** The error the finding is built on is
  already cancelled by the design it criticises. Worse, **the prescribed fix
  fails catastrophically**: the gate is pressed at the start of a bend, when the
  instrument is already rotating, and 20 °/s captured as "bias" and integrated
  for 3 s gives **60° of error** with no recovery — an order of magnitude worse
  than the filter it replaces. The accel-contamination figure is also overstated
  5–8× (1.3°, not ~10°). **The one real sub-finding: ADR 0007's filter has no
  acceleration gating.** Keep the complementary filter, freeze the accel
  correction when ‖a‖ deviates from 1 g, state τ = 1–2 s. **P0 → P2.**
- **R27 — drop the mechanism.** Getting +12 V onto the module's +5 V pins needs a
  *three-pair* offset, which the shrouded keyed header already specified
  physically prevents. A 5.6 V TVS is ten cents and worth fitting as blanket
  insurance, but not as a named failure mode.
- **R26 first half — drop.** "Every useful setting lives in the top 45 % of
  rotation" assumes gain below 1× is useless. It is not: the lower half produces
  0–5 V and 0–8 V, which R16's own research says are the *more* common
  conventions. *(The second half — never reference the offset pot to the raw
  ±12 V bus — is correct and important. Keep it.)*
- **R16 second half — drop.** A 0–10 V breath CV into a 5 V destination is fixed
  by turning down the panel gain knob. A configuration question presented as a
  hardware limitation. *(The bipolar limitation in the first half is real. Keep.)*
- **R28 — merge into R35.** Conditional on R35 being violated; with AGND
  connected only to the receiver's inverting input, a 25 kΩ input limits the
  return path to microamps.

### V3. Findings that are OVERSTATED

- **R23 by ~37 dB.** The −12.6 dB figure used 400 Hz, which is the IMU's *ODR*,
  not its signal bandwidth. Real gesture content is under 20 Hz → first image at
  1980 Hz, **−50 dB**. *(The structural half is right and worth keeping: the mod
  channels are given a faster filter than breath, which is backwards, and the
  ADR's internal 4 kHz-vs-2 kHz inconsistency is real.)*
- **R24 — the analogy to breath is false by ~60 dB.** A staircase on *breath* is
  AM into a VCA and audible. The same staircase on *pitch* is FM into a VCO at
  modulation index 1.7e−4 → sidebands near **−81 dBc**. Raising the pitch rate is
  nearly free so the action stands, but delete the breath comparison.
- **R8/R11 — the honest gap is 21–27 dB, not 30.** R8's millivolt figures are
  *sensor-referred* while labelled "at the jack", so it **understates its own
  case** by the scaling gain; and the 0.13 mV quoted for the common-mode path is
  not reconstructible — at R10's realistic 31–34 dB CMRR it is ~1.7 mV. **R8 and
  R10 cannot both be quoted at full strength in the same document.**
- **R11's "run the ADC at 5 V" is more expensive than stated** — MCP3202 VIH at
  5 V is 3.5 V, so CLK, DIN *and* CS all need shifting up, not just DOUT down.
  **Better and cheaper: keep the ADC at 3.3 V and digitise the precision
  reference on the spare channel.** Both channels share VREF = VDD, so the ratio
  `breath_code / ref_code` is independent of VDD **exactly**. Two resistors.
- **R50 — the timing failure is not real.** Its premise (six DAC channels every
  loop) contradicts ADR 0006, which specifies mod at 2 kHz and pitch on demand.
  Real per-loop cost is ~72 µs, and after R31 the two buses overlap via DMA.
  *(The documentation inconsistency about "4–8 kHz" is real. Downgrade to a
  documentation fix.)*
- **R9's 12 A, R42's cents figure, R29's 300 mA bead rating, R17's framing**
  (the PPTC drop matters because **the WS2815 strips hang on unregulated +12 V
  downstream of it** — the buck regulates its own drop away; the LEDs cannot),
  and **R21's 788 Hz restrictor** (a restrictor *lowers* the Helmholtz frequency
  and works by viscous damping; the number needs a stated orifice geometry).

### V4. A conflict nobody noticed

**R11 and R49 contradict each other.** R11 wants the ADC divider's source
impedance *lower* (6 kΩ is 6× the MCP3202's limit); R49 wants the upper resistor
*higher* (≥10 kΩ to keep sequencing current out of the ESD diode).

**Both are resolved by R39's single capacitor**, which decouples the converter's
sampling-charge demand from the divider's DC impedance. **R39 is the keystone of
that cluster** and should be cross-referenced from R11, R43 and R49 rather than
sitting alone as a P1.

### V5. Called out as the strongest work in the register

R35 (the "identical on a netlist" observation — the highest-value free fix),
R40 (the best-argued finding), R32's marker pattern and hold-margin chain
ordering (the best ideas in the review, and they cost nothing), R39's
single-capacitor fix, and R20's BAV99-not-BAT54S catch.

## Resolved by the project owner

### R1 — REJECTED. The closed tube is correct.
The reviewer's evidence about commercial instruments was accurate; the premise
about this instrument was not. **The player vents through the corners of the
mouth around the mouthpiece**, which is also what makes circular breathing
possible. Air leaves continuously — it simply never enters the sensor tube. The
sealed sensor branch stays. Recorded in ADR 0003 so it is not re-raised.

The moisture finding (R22) and the Helmholtz resonance finding (R21) are
independent of the bleed question and remain open.

### R4 / R6 — RESOLVED by adding pitch trim pots.
Rather than respeccing the output range to reach an exactly-constructible gain,
**the pitch channel gets scale and offset trimmers**, which is what every
commercial 1V/oct module does. That directly fixes the missing offset authority
(R6) and removes the need for a buildable 1.8 ratio (R4).

Cost is honest and acceptable: a 5–10 % trim range contributes 2.4–3.7 cents per
10 °C, **comparable to the drift of the VCO being driven** (~3.5 cents/10 °C), so
it is not the limiting term. Keep the LT5400 setting the nominal ratio with the
trimmer providing only the adjustment.

Knock-on effects: the "design the gain 5 % high" kludge is deleted; the DAC now
uses its 0.25–4.75 V window for headroom (R5) with the trimmer absorbing the gain
change; **R18's multi-point INL table is still needed** — trimmers straighten the
line, firmware straightens the bow.

## Not acting on

- **Adding a +5 V fallback regulator to the module.** Two agents recommend it for
  cases without the rail. The project owner has explicitly decided +5 V is
  required and told this project to stop hedging for racks it will never be in
  (see the design scope in the README). **The decision stands.** The legitimate
  sub-finding is that ADR 0004 still claims the module is "independently useful",
  which is now inconsistent — fix the claim, not the decision.

---

## Open for the project owner

1. **The bleed path (R1).** Contradicts a stated design assumption. Strong
   evidence from every commercial wind controller plus the physiology.
2. **Buy MPXV4006GP stock now (R2)** — EOL, distributor stock only.
3. **Pitch range −2.5…+7.5 V (R4)** — accepting this unlocks R5 and R6 too.
4. **Mod channels bipolar-capable (R16)** — a one-time PCB decision that cannot
   be recovered in firmware later.

---

## Bench measurements this review added

- MPXV4006GP output noise — the only non-negligible noise term in the chain, and
  not obtainable from any accessible datasheet mirror
- MPXV4006GP burst pressure vs a 15–20 kPa cough into a sealed mouthpiece
- WS2815 quiescent draw on the actual strip purchased, all pixels black
- R-78E5.0 **load-step response** (not its ripple spec) — the audio-band settling
  envelope after a WiFi burst is what reaches the breath CV
- Waveshare ESP32-S3-Matrix: **is the header `5V` pin raw USB VBUS?** If so,
  driving it from the buck while USB is connected for flashing parallels two
  supplies. Highest bench-damage risk in the project.
- LilyGO T-Display-S3 AMOLED: its SY6970 PMU is documented unstable on 5 V
  **without a battery** — in a deliberately battery-free design
- DAC8568 output headroom vs code near full scale at AVDD = 4.75 V
- Target rack's actual +5 V presence, voltage and ripple under full case load

## Documentation contradictions to fix

- `docs/reference/latency-budget.md` still describes breath as "a differential
  analog signal" with a "differential driver" and a "~2 kHz corner" — all three
  superseded by ADR 0003 (buffer, sense return, 500 Hz both ends)
- The same table still charges the breath path for SAR conversion, SPI-to-DAC and
  DAC settling — stages that no longer exist for the CV output. Honest number is
  ~1.75 ms
- ADR 0003 says the sensor "reaches 4.7 V"; it is **4.8 V** at 6 kPa — and that is
  the number that sizes the divider
- BOM `U-BREATH` package is wrong: MPXV4006GP is **SOP-8 SMT, side port**, not
  "ported case, THT leads"
- BOM `R-PD-BREATH` note claims the pulldown is "high enough not to load the
  INA134 input network" — loading was never the issue, **balance** is (R10)
