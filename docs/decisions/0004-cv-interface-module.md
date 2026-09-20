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
