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

**Bandwidth is no longer trivial.** The 96 kHz breath rate (ADR 0003, ADR 0006)
raises what the link has to carry by roughly an order of magnitude:

| Channel rates | Payload | SPI clock at 50% use |
|---|---|---|
| all six at 4 kHz | 0.77 Mbit/s | ~1.5 MHz |
| breath 48 kHz, rest 2 kHz | 1.86 Mbit/s | ~3.7 MHz |
| **breath 96 kHz, rest 2 kHz** | **3.39 Mbit/s** | **~6.8 MHz** |
| breath 192 kHz, rest 2 kHz | 6.46 Mbit/s | ~12.9 MHz |

Per-channel rates are what make this affordable at all — running all six at
96 kHz would need three times the bandwidth for no benefit.

**This promotes RS-485 from contingency to likely requirement.** Single-ended
SPI at ~7 MHz over a couple of metres of cable, in a rack full of switching
supplies, is not something to assume will work. Differential signalling on a
twisted pair handles that rate comfortably and is immune to ground offsets
between rack and instrument, which single-ended SPI is not.

Bench the plain-SPI version first since it is simpler, but expect to escalate,
and lay the module out so transceivers can be fitted without a respin. If the
link will not hold 96 kHz, **48 kHz is the graceful fallback** — 55 dB of image
rejection instead of 67 dB, which is still far better than the 12 dB that 4 kHz
would have given.

**Wire MISO even though nothing uses it.** It is free, and it lets the
instrument detect whether the module is connected at all — so an unplugged
instrument can fall back to USB MIDI mode automatically instead of quietly
sending CV into nothing.

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

Bare 8P8C is rejected outright — the retention tab is the most-broken connector
in the industry and it has no strain relief. On a moving instrument tethered to
a rack, that is a matter of when.

The argument for etherCON despite the tightness is real: any Ethernet cable
works, and spares are everywhere. M12 and HR10 both mean a custom cable to make,
order, and remember to bring.

Also worth considering a deliberate **breakaway** at the instrument end — better
to lose the connection than to pull the rack off the shelf.
