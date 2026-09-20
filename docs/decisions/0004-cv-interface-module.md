# 0004 — CV interface module and umbilical

**Status:** Accepted

## Context

The instrument's output target is a Eurorack system. The original plan put the
DAC, analog scaling, bipolar supply and jacks inside the instrument body, on
battery power (see ADR 0005, superseded).

Putting the analog section in a rack module instead — connected to the
instrument by a single cable — solves several problems at once.

## Decision

**A 6HP Eurorack module holding all analog output hardware, connected to the
instrument by an 8-conductor ruggedised umbilical.**

The instrument becomes purely digital: no analog signal path, no battery, no
jacks. It takes power from the rack and sends channel data down the same cable.

### What goes over the cable

Digital down, analog stays in the module:

```
+12V, GND, GND      power (3.3V derived locally in the instrument, small buck)
SCLK, MOSI, CS      SPI to the DAC, ~2 MHz
MISO                unused today — module ID and presence detect
spare               reserved
```

No −12V goes up the cable; nothing in the instrument is bipolar any more.

With real Cat5/6 each signal sits against a ground in its own twisted pair.

**Bandwidth is modest again.** A 96 kHz digital breath channel would have
needed ~6.8 MHz on the wire and probably RS-485 transceivers. With breath going
analog instead (ADR 0003), the digital link carries only pitch, four mod
channels and the zero offset at 2 kHz:

| | Payload | SPI clock at 50% use |
|---|---|---|
| Breath digital at 96 kHz + 5 channels | 3.39 Mbit/s | ~6.8 MHz |
| **Breath analog, 5 channels at 2 kHz** | **0.32 Mbit/s** | **~0.6 MHz** |

Plain single-ended SPI at well under 1 MHz over twisted pair is unremarkable.
**RS-485 returns to contingency status**, not a likely requirement.

### Revised conductor budget

```
+12V      / PWR_GND     power, and the presence signal
SCLK      / DIG_GND     SPI to the DAC, ~1 MHz
MOSI      / CS
BREATH    / AGND        analog, band-limited ~500 Hz, sense return
```

Eight of eight, paired to suit Cat5's four twists. **`AGND` carries no power
current** — it is a sense reference only, which is the whole reason the analog
channel survives the cable (ADR 0003). Keep it twisted with `BREATH` and away
from the SPI clock pair.

MISO goes, and with it the planned module-ID line. No loss worth engineering
around: the instrument is rack-powered, so +12V on the umbilical is itself
evidence the module is connected, and the only other case is sitting on the
bench under USB power during development.

### Why this partitioning is right

- Deletes the entire battery subsystem (ADR 0005).
- Moves precision analog into a shielded metal box inches from its jacks,
  instead of running pitch CV down two feet of wooden instrument alongside LED
  power.
- Splits the project into two deliverables with different risk profiles that can
  be built in parallel: the instrument's risk is mechanical, the module's is
  analog precision.
- **The module can be brought up entirely standalone** — driven from any dev
  board with a test pattern and a multimeter — long before the instrument
  exists. This de-risks the whole CV problem on its own schedule.
- The module is independently useful. "Digital controller to six-channel CV over
  Cat5" stands on its own.

### The module needs its own logic rail

Easy to miss: **the DAC8568 is a 2.7–5.5 V part and cannot run on the rack
rails.** The module therefore derives a low-voltage rail from +12 V, and the
choice of which interacts with noise more than it looks:

| DAC VDD | Output span | Gain the scaling stage must supply |
|---|---|---|
| 3.3 V | 0–2.5 V (ref × 1) | **3.6×** |
| **5 V** | **0–5 V (ref × 2)** | **1.8×** |

Everything the scaling stage amplifies — op-amp noise, offset, drift — is
amplified by that factor. **5 V halves it.**

The cost is that a 5 V DAC wants roughly 3.5 V for a logic high while the
instrument sends 3.3 V, so SPI needs shifting. That turns out to be free in
parts terms:

- **A local 5.25 V regulator off the protected +12 V rail** for the DAC's AVDD
  — not the rack's +5 V bus. See below.
- **74AHCT125** for the shifter, running from the **bus +5 V rail** — the *same
  part* as the instrument's LED data lines (ADR 0014), with a spare gate left
  over.

One part number shared across both boards rather than one more to source.

### The DAC gets a local regulator; the level shifter keeps the bus rail

The obvious move is to take the module's 5 V straight from the rack. It is
inches from the bus board, the load is milliamps, and the rail is right there on
the 16-pin header. That was the original decision, and it is wrong for the DAC.

**The rack's +5 V is the least-regulated rail in Eurorack** — ±5 % is normal, and
it moves with whatever else in the case is drawing from it. Two consequences:

- **The DAC's full-scale output is its supply.** DAC8568 at internal reference
  × 2 spans 0–5 V, so full scale *equals* AVDD. TI does not specify the headroom
  needed to actually reach it, and wants AVDD ≈ 5.5 V for a true 5 V full scale.
  At a bus rail sagging to 4.75 V the DAC saturates somewhere around 4.55–4.65 V
  — and the top calibration point lands in the nonlinear region, which corrupts
  the whole two-point fit rather than just clipping the top.
- **It puts a rail the rack moves underneath the pitch calibration.** Pitch is
  calibrated once against a real VCO (ADR 0006). A supply that shifts when
  another module powers up shifts the calibration with it.

**So: an LM317LZ set to 5.25 V, fed from +12 V downstream of the module's
reverse-protection diode.** TO-92, two resistors and two capacitors, a few
milliamps of load, 135 mW dissipated — the lowest-effort regulator that exists,
and it buys back both properties. 5.25 V nominal keeps worst-case tolerance
(±4 % on the LM317 reference) inside the DAC's 5.5 V recommended maximum while
staying above the 4.75 V top of the used output window (ADR 0006).

**The 74AHCT125 stays on the bus +5 V rail.** Its job is to get 3.3 V logic over
the DAC's 0.7 × AVDD input threshold — 3.68 V at AVDD = 5.25 V. An AHCT gate on
a rail sagging to 4.75 V still drives 4.6 V, with a volt of margin. Leaving it
there keeps its switching current off the DAC's supply, and it means the only
thing hanging on the unprotected bus +5 V pin is a $0.30 buffer. A reversed or
row-offset ribbon that puts +12 V onto that pin kills the buffer and nothing
else, which is why the +5 V entry gets no protection network of its own.

### Module parts, chosen for build ease

**One op-amp part throughout: OPA2197.** Pitch scaling, all four mod channels
and the breath stage use the same dual RRIO part. It is rated to ±18 V, so on
±12 V it reaches roughly 11.9 V — comfortably past the 10 V output. Using a
cheaper part for the non-precision channels would save a few dollars on a
one-off and introduce a whole class of "which chip goes here" assembly error.
Not worth it.

**INA134 for the breath difference amp.** On-chip matched resistors give ~90 dB
CMRR against the 60 dB needed (ADR 0003), with no external matching network to
place or match.

**Standard eurorack hardware elsewhere:** PJ398SM jacks, Alpha 9 mm vertical
pots (linear taper — predictable for CV scaling), a rated SPST toggle for power,
and a 16-pin shrouded keyed IDC power header with Schottky diodes behind it.
Reversed ribbon cable is the classic Eurorack failure and the keying alone is
not worth trusting.

**1 kΩ series resistors on every CV output.** Standard practice, and it means
the module survives a short or someone patching output to output.

**The 6HP panel is laser or waterjet cut from DXF — same vendor and ideally the
same order as the aluminium key plate** (ADR 0009). Which also disposes of the
last objection to etherCON: its cutout is more complex than a round hole, and on
a laser-cut panel complexity is free.

### Power entry, and why this module is not a typical one

Eurorack practice for module power entry is well settled, and converges on:

- **Series Schottky diodes** on +12 V and −12 V for reverse polarity, 1N5817
  being the common choice for its low drop at module currents
- **A ferrite bead** in series for RF suppression — or, in many designs, a small
  series resistor of 2.2–10 Ω instead
- **Bulk electrolytics**, typically 10–100 µF per rail, for ripple and as a
  local reservoir
- **100 nF ceramics** at every IC

Two things make this module unusual, and both change the answer.

**It passes the instrument's current.** A typical module draws 20–100 mA. This
one draws its own analog current *plus* everything the instrument consumes:

| Rail | Draw |
|---|---|
| +12 V | ~295 mA (45 module incl. the DAC regulator, 250 instrument) |
| −12 V | ~40 mA |
| +5 V | ~10 mA (level shifter only) |

That is about 15% of a modern rack supply's +12 V capacity — unremarkable, but
it **rules out the series-resistor variant**, which is harmless at 50 mA and is
not at 290 mA:

| Series R | Drop at 290 mA |
|---|---|
| 2.2 Ω | 0.64 V |
| 10 Ω | 2.90 V |

**So: ferrite beads, not resistors.** A 1N5817 drops roughly 0.3–0.4 V at this
current, leaving ~11.5 V at the instrument after cable drop, against a buck that
needs more than 6 V in. Ample.

**It has two filtering jobs, not one.** Most modules only need to keep rack hash
out of themselves. This one also has to keep *itself* out of the rack, because
the instrument's buck converter is a switching load drawing pulsed current
through this module.

Those are different problems and they want separate treatment:

```
bus +12V ──[1N5817]──┬──[ferrite]──[bulk]──┬── module analog (op-amps)
                     │                      │
                     │                      └──[LM317LZ 5.25V]── DAC AVDD
                     │
                     └──[ferrite]──[bulk]── umbilical +12V to the instrument

bus -12V ──[1N5817]─────[ferrite]──[bulk]── module analog
bus +5V  ────────────────[ferrite]──[bulk]── 74AHCT125 level shifter only
```

**Branch the two +12 V paths after the protection diode, each with its own
ferrite and bulk capacitance.** That way the buck's pulsed draw is absorbed
locally instead of modulating the rail the pitch scaling stage is referenced to
— which is the whole point, since this module's analog section is precision and
most modules' are not.

Sources: Doepfer's A-100 technical documentation for the bus and supply
conventions; ModWiggler's module-power-entry threads for the community consensus
on diodes, ferrites and reservoir values.

### Module design principles

**The module is dumb.** Jacks, knobs, connector, power switch, analog. No menu,
no encoder, no screen. All UI lives on the instrument, which already has a
display and a processor. This is what keeps the panel inside 6HP.

Input filtering on the +12V rail so the instrument's local buck converter does
not inject switching noise back into the rack.

### Panel, top to bottom

Connector, power switch and LED, two breath knobs, then six jacks in two
columns: **PITCH** and **BREATH** silkscreened, **MOD 1–4** numbered with a
write-on strip. Roughly 107 mm of ~110 mm usable height — full but workable.

Print the panel at 1:1 on paper and check it is actually usable before cutting.

## Open

**Connector choice**, pending a fit check against the real datasheet cutout:

| Option | Panel | Trade |
|---|---|---|
| **etherCON** (Neutrik) | ~24 mm — fits 6HP with ~3 mm margin each side | Any Ethernet patch cable works. Tight |
| **M12 8-pin** | ~14 mm | Rugged, cheap, fits easily. Industrial-looking custom cable |
| **Hirose HR10** | ~14 mm | Push-pull lock, elegant, pricier. Custom cable |
| Rear-mount | n/a | Frees the panel entirely; worse to plug and unplug |

Bare 8P8C is rejected — the retention tab is the most-broken connector in the
industry and it has no strain relief. That matters here not because of stages or
trip hazards, but because **the instrument moves constantly while being played**
and the cable flexes at the connector every time. That is true in a studio.

The argument for etherCON is that any Ethernet cable works and spares are
everywhere. M12 and HR10 both mean a custom cable to make and keep track of.
