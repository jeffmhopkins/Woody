# MIDI out — schematic

**Status:** New 2026-10-04, issue #37 ([ADR 0015](../../../docs/decisions/0015-one-mcu-no-display.md),
*Amendment, 2026-10-04*). The instrument's external USB is gone, and MIDI
leaves on a 3.5 mm TRS jack in the oak bottom instead (owner: *"The only
requirement then would be a TRS connector on the bottom for midiout, and
adding a midi circuit to the main board"*; *"TRS should be able to be swapped
from TRS a to b, ideally just in firmware"*; *"I think you need it on the
bottom face, and then just do a connector to the main board instead of
actually mounting it to PCB"*). **The parts are on the sheet, in the BOM and
placed and routed on `main-board.kicad_pcb`** (issue #35 pass 2; *Placement*,
below, and the board's `layout.yaml` `parts:`). **Amended 2026-10-05 (#39):** `R-MIDI` is
182 Ω 1 % and the rail comes through an ideal-diode OR (*Amendment*, below).

**The sheet:** [`midi-out.sch.png`](midi-out.sch.png) (KiCad:
[`midi-out.kicad_sch`](midi-out.kicad_sch)) is the SOURCE for this circuit
(ADR 0019): edit it in KiCad 9, and [`netlist.yaml`](netlist.yaml) is
exported from it. The main board's project places it. The drawing below is a
representation of it.

Evidence marks as everywhere: `[ds <file> p.N]` a banked document, `[calc]`
the arithmetic shown, `[from memory]` unchecked.

## Interfaces

The `Dir` and `Peer` columns are defined once in
[`hardware/README.md`](../../README.md#the-interfaces-table).

| Node | Dir | Peer | Figure | Note |
|---|---|---|---|---|
| `MIDI_TIP_DRV` | in | `carrier/led-strip-drive` | — | `U-LVLSHIFT` gate B, driven by IO6 |
| `MIDI_RING_DRV` | in | `carrier/led-strip-drive` | — | `U-LVLSHIFT` gate C, driven by IO2 |
| `PWR_GND` | ref | `carrier/power-entry-instrument` | `dig-gnd-topology` | The jack's sleeve: MIDI pin 2, grounded at the transmitter only |

## The circuit

*Connectivity is **[`netlist.yaml`](netlist.yaml)**, not the drawing below.*

```
  ON THE MAIN BOARD                                                 IN THE OAK BOTTOM
  U-LVLSHIFT gate B (5 V) MIDI_TIP_DRV ──[R-MIDI-T 182R 1%]──[FB-MIDI-T 600R@100MHz]──┬── J-MIDI 1 ═╗
  U-LVLSHIFT gate C (5 V) MIDI_RING_DRV ─[R-MIDI-R 182R 1%]──[FB-MIDI-R 600R@100MHz]──┼── J-MIDI 2 ═╬═ CBL-MIDI ═ [J-MIDI-OUT SJ5-43502PM]
                                                                         [U-TVS-MIDI SP0504BAHTG]    ║    T = tip, R1 = ring,
  PWR_GND ─────────────────────────────────────────────────────────────────┴── J-MIDI 3 ═╝    R2 + S = sleeve
```

**CA-033's Figure 1, its 5 V row**: 220 Ω from the source to DIN pin 4 (RA)
and 220 Ω from the driver to pin 5 (RC), 0.25 W, with optional 1 kΩ-at-100 MHz
beads at the jack `[ds connectors/MIDI-CA-033-ELECTRICAL-SPEC-UPDATE-2014.pdf p.3]`.
The two lines here are identical, so each resistor is RA or RC according to
which line firmware makes the source. **They are 182 Ω 1 %, not 220 Ω 5 %,
since issue #39** (*Amendment*, below): CA-033's 5 V row assumes an ideal
driver, and this one has its own resistance, so the row's value is
re-sized against the gate's short-circuit rating. The beads are `FB-CHAIN`'s part, 600 Ω
rather than CA-033's example 1 kΩ: they are optional (p.6) and the board then
carries one bead part number.

**Why the 5 V row and not the 3.3 V one** (33 Ω and 10 Ω from 3.3 V,
`[ds p.3, p.5]`):

- **3.3 V here is the breath ADC's reference.** It is the Matrix's own LDO
  (`carrier.md`, *The key pull-ups and the ADC reference*), and a MIDI loop
  switching about 7 mA at the bit rate would move it, as the key pull-ups do.
- **A GPIO cannot drive the 3.3 V row.** CA-033 assumes an open-drain buffer
  and a 0.5 W RA `[ds p.5]`. A tip shorted to the sleeve through 10 Ω is
  hundreds of mA, and the ESP32-S3's pad is characterised at 40 mA source and
  28 mA sink `[ds logic/ESP32-S3-datasheet-v2.2.pdf p.65]`.
- **Gates B and C of `U-LVLSHIFT` were spare** and already run on the 5 V
  rail, push-pull, from 3.3 V inputs (TTL thresholds, `led-strip-drive.md`).
  Push-pull is what makes Type A/B a firmware choice: either output can be the
  source (high) or the sink (low).

## The loop current

The receiver, as CA-033 models it: 220 Ω and an opto LED of 1.9 V at most,
1.4 V typical `[ds p.4, p.5]`; it must turn on with under 5 mA `[ds p.2]`, and
CA-033 gives 4 mA as the PC900V's worst-case need `[ds p.4]`.

The driver: VOH ≥ 3.8 V at −8 mA and VOL ≤ 0.44 V at 8 mA, both at a 4.5 V
supply `[ds logic/SN74AHCT125.pdf p.4]`, which is about 87.5 Ω sourcing and
55 Ω sinking `[calc: (4.5 − 3.8) / 8 mA; 0.44 / 8 mA]`.

The rail: `INST_5V_A`, **4.625–5.325 V with the rack up** — the buck's
±6.5 % less the ideal-diode OR's 50 mV at most, both ends asserted by
`power-entry-instrument/sim`'s `or-rack` (`power-entry-instrument.md`, §1b).

```
worst  VCC 4.625 V, opto 1.9 V, R-MIDI 182 ohm at +1 % (183.8), the receiver's 220 at +5 % (231):
       (4.625 - 1.9) / (87.5 + 183.8 + 183.8 + 231 + 55) = 3.68 mA        [calc]
       CA-033's own 5 V row with an ideal driver: (4.5 - 1.9) / 693 = 3.75 mA   [calc]
typ    VCC 4.98 V, opto 1.4 V, resistors at value, driver ~115 ohm in all:
       (4.98 - 1.4) / (182 + 182 + 220 + 115) = 5.1 mA; 4.7 mA with a 1.7 V opto   [calc]
```

**Simulated** ([`sim/`](sim/sims.yaml), `type-a` and `type-b`, every corner of
VCC 4.625–5.325 V, both gate resistances, R-MIDI at ±1 %, the receiver's
220 Ω at ±5 %, the opto at 1.4–1.9 V and 1–3 m of cable): the worst corner is
**3.69 mA**, the nominal 5.14 mA and the strongest 6.24 mA; the
arithmetic above to within 0.5 %; the loop current's edges stay well under
CA-033's 2 µs, and Type B is Type A to the last digit, as the symmetric loop
says it must. **Recorded, not asserted, because it still does not pass:** the
worst corner is up from 3.11 mA with the SS14 and 220 Ω 5 %, but still below
CA-033's own 5 V transmitter at *its* worst corner (3.75 mA, above) and the
PC900V's 4 mA worst-case need `[ds p.4]`. The nominal is above both. CA-033
states no minimum for a transmitter, only that a receiver must turn on with
under 5 mA `[ds p.2]`. **What decides it:** an E-test with two real
receivers, a 6N138 DIN interface through an RP-054 adapter and a TRS-input
synth. **Accepted by the owner** (2026-10-05, chat), asked whether to add a
stronger driver: "Agreed" — no buffer; the two-receiver E-test stands, and a
failure there is a part swap on the main board (a lower-impedance driver
with TTL inputs and the resistors re-sized against its short-circuit
rating), not a redesign.

**On USB alone** (the bench) the rail is `VBUS` less the Matrix's `D1`,
4.2–4.3 V (`power-entry-instrument.md`, §1b), and the loop is weaker again;
that is not a playing configuration (no breath on USB alone, the same page).

**Why not lower resistors.** The resistors are sized to the gate's ±25 mA
absolute maximum `[ds SN74AHCT125.pdf p.3]` with a line shorted to the
sleeve, at the strongest corner: the rail's 5.325 V ceiling, the resistor at
−1 %, and the gate's own resistance at its minimum — 35 Ω, half its 25 °C
figure `[assumption: the datasheet gives no minimum]`:

```
5.325 / (0.99 R + 35) < 25 mA   ->   R > (213 - 35) / 0.99 = 179.8 ohm     [calc]
E96: 182 ohm. 5.325 / (180.2 + 35) = 24.7 mA, 0.11 W in the resistor       [calc]
     (180 ohm, E24: 24.98 mA, 0.1 % inside - too close to call; 182 at 5 %
     would be 25.6 mA)
```

It leans on that assumed minimum: with an ideal driver the same short is
5.325 / 180.2 = 29.5 mA `[calc]`. The 220 Ω it replaces held 23.9 mA with an
ideal driver at 5.0 V. Both lines shorted at once put 2 × 24.7 = 49.5 mA
through the package's `VCC`, inside its 50 mA `[ds p.3]` by 1 %
(`sim/`, `shorts`, asserts both).

## Amendment, 2026-10-05 — more loop current (issue #39)

The worst corner was 3.11 mA, below CA-033's own reference transmitter at its
worst corner (3.75 mA). Asked whether to tighten `R-MIDI` to 1 % and replace
`D-USBOR`'s Schottky with an ideal-diode OR, the owner: *"Let's go both, that
seems the best way to ensure we're good"* (chat, 2026-10-05).

- **The rail:** `U-USBOR` (LM74700-Q1) and `Q-USBOR` (DMN3404L) replace the
  SS14 (`power-entry-instrument.md`, §1b). `INST_5V_A` is 4.625–5.325 V with
  the rack up, from about 4.5–4.65 V.
- **The resistors:** 182 Ω 1 %, sized to that ceiling (*Why not lower
  resistors*, above).
- **The result:** the worst corner is 3.69 mA, up from 3.11 mA — **still
  under 3.75 mA**, so it stays recorded, not asserted, and the E-test above
  still decides. What is left between the two is the driver's own ~140 Ω
  and the rail's 4.625 V floor against CA-033's 4.5 V with none.

## Type A and Type B, in firmware

`[ds connectors/MIDI-RP-054-TRS-CONNECTORS.pdf p.1]` gives Type A: tip = DIN
pin 5 (the sink), ring = DIN pin 4 (the source), sleeve = pin 2. Type B
swaps the tip and ring `[from memory: a manufacturers' convention, not in
RP-054]`.

| Setting | Tip (IO6, gate B) | Ring (IO2, gate C) | UART1 TX routed to |
|---|---|---|---|
| **A** (default) | sink: TX | source: held high | IO6 |
| **B** | source: held high | sink: TX | IO2 |

Logical 0 is current on `[ds CA-033 p.2]`. UART idle is high, so with both
lines high no current flows. A start bit takes the sink low, and the loop
conducts. **No inversion is needed in either setting.** To swap, drive both
lines high, wait for the FIFO to empty plus one byte time, then re-route TX
through the GPIO matrix. A wrong setting reverse-biases the receiver's opto,
which its D1 (1N914, `[ds CA-033 p.3]`) clamps: no damage, no data.

The UART is UART1, free since the display link went (ADR 0015). The ESP32-S3
has three `[ds ESP32-S3-datasheet-v2.2.pdf p.51]`, and UART0 is the console.
The A/B setting lives with the rest of the configuration (deferred:
`firmware/README.md`, *Configuration mode and OTA*).

## The power-on default

IO6 and IO2 are high-impedance from reset through the bootloader window. The
gates' enables are tied low, so a floating input would put noise into the
loop. **`R-MIDI-PU-T` and `R-MIDI-PU-R` (10 kΩ to `DEV_3V3`, on
[`led-strip-drive`](../led-strip-drive/led-strip-drive.md)) hold both inputs
high.** Both outputs then sit at 5 V, tip and ring are at one voltage, and no
loop current flows, in either setting, before firmware has chosen one
(`sim/`, `power-on`: both inputs above VIH at every corner, against a 45 kΩ
pull-down on the pad as the bound).

**The pads' power-up glitch.** GPIO2 and GPIO6 are both on Espressif's list of
pins driven low for about 60 µs at power-up `[ds ESP32-S3-datasheet-v2.2.pdf
p.18, Table 2-2: "a low level output status"]`, and a 10 kΩ pull-up cannot
hold against a driven pin. Both gates' outputs then go low **together**, so
the loop stays dark: only the two glitches' *mismatch* conducts. At ±10 % on
each `[assumption: the datasheet gives a typical only]` the longest pulse is
about 12 µs `[sim: power-on]`, under half a bit, which a mid-bit-sampling UART
rejects as a false start `[from memory]`. A glitch on IO6 alone would put
60 µs of current on the loop in Type A: a start bit and D0 = 0, read as 0xFE,
Active Sensing `[calc]`. **What decides it:** scope IO6, IO2 and the loop
current at power-up, with a receiver attached (the E-test above). They pull to 3.3 V, not 5 V, because the ESP32-S3's
pads are not 5 V tolerant. Neither GPIO is a strapping pin. The straps are
GPIO0, 3, 45 and 46 `[ds ESP32-S3-datasheet-v2.2.pdf p.32]`.

## Protection

- **A short of either line to the sleeve:** 24.7 mA at 5.325 V with the
  gate's own resistance at its assumed minimum `[sim: shorts]`, inside the
  gate's 25 mA (above), and both lines shorted at once stay inside the
  package's 50 mA through VCC `[ds SN74AHCT125.pdf p.3]`. A mono plug does exactly this to the ring for as long as it
  is in.
- **Shorted to each other:** one gate high and one low, 12.7 mA at the
  strongest corner `[sim: shorts]`.
- **The wrong A/B setting:** the start bit reverse-biases the receiver's LED,
  and its D1 clamps it to about 0.68 V; the loop runs through D1 at under
  8 mA `[sim: wrong-ab]`. No damage, no data.
- **A DC-coupled headphone driver on the jack**, RP-054's named case
  `[ds RP-054 p.1]`: `R-MIDI` limits it the same way.
- **ESD:** `U-TVS-MIDI` at `J-MIDI`, CH1 the tip and CH2 the ring.
- **Ground:** the sleeve is `PWR_GND`. A MIDI receiver's input is
  opto-isolated, and its pin 2 has no DC path to its ground `[ds CA-033 p.3]`.
  So this output joins no second ground to the instrument. USB to a computer
  did, the caveat [ADR 0027](../../../docs/decisions/0027-isolated-instrument-supply.md)
  records.

## The ribbon conductors

The tip line is **IO6, on `J-MCU` pin 23**: on the Matrix carrier, `J-MCU-C`
pin 2, the header's front row at its tail end. That pin runs straight up the
carrier's bottom face, through one via, and into `HDR-MATRIX` J2.5
(`hardware/boards/matrix-carrier/carrier_routes.py`). The ring line is **IO2,
on `J-MCU` pin 5**, which was already routed as a spare shield. `J-MCU` pin 24
(`J-MCU-C` pin 1) was the other spare conductor, and it cannot be reached on
the carrier. It is the back row's last pin: the back row's ten lanes fill both
faces under it, the top face's via diagonal fences it to the east, and its
neighbour in the front row stands over it.

IO2 is static in the default Type A: held high, it still shields `IO1` (LED
data) from `IO7` (`SH/LD`) on the ribbon, as it did held low (`carrier.md`,
*The pin map*). **In Type B it is the line that switches**, at UART edges
between the LED data and the chain's load line. The chain's marker check
catches a corrupted frame (`firmware/README.md`, *SPI3*), and the GPIO's
drive strength can be set to its lowest for this pin. **E11 or E14 should
confirm that playing in Type B produces no marker errors.**

## The jack and its lead

`J-MIDI-OUT` is a Same Sky SJ5-43502PM: M7 × 0.75 thread, 4.5 long, with a
2.00 nut `[ds connectors/SAMESKY-SJ5-43502PM.pdf p.2]`. It mounts **through
the oak bottom**, from inside, in the lane beside the etherCON that the USB-C
receptacle used to stand in (config/body.yaml `midi`; mechanical/drc.echo
*"MIDI jack in the oak bottom"*). A counterbore from inside leaves the panel
the thread can clamp. Its four tabs take a three-conductor plug: the plug's
sleeve spans ring 2 and the sleeve, so both go to `PWR_GND`. It is wired to
**`CBL-MIDI`**, a three-way JST PH lead with tip and ring twisted, which plugs
into **`J-MIDI`** on the main board (drc.echo *"MIDI jack lead to J-MIDI"*
gives its run). It is fitted before the cassette drops in, and the lead is
plugged with the lid off, as `HDR-SERVICE` is reached.

## Placement (for the main board's layout, after #35)

The corner the USB-C receptacle's keep-out used to hold, past the right-hand
key board and beside the etherCON adapter. It is outside both key boards'
outlines, and nothing stands over it but the Matrix carrier
(`pcb-geometry.echo`, *main*, `J-MIDI`):

- **`J-MIDI` at about (293.5, 43), its pins along the body**, facing the lane,
  so the lead leaves toward the jack (`config/body.yaml` `midi.hdr_at`). A
  surface-mount PH, because the corner is over the bottom plate's end, where
  a through-hole header's tails would need a plate window.
- **`U-TVS-MIDI` beside it**, at the header pins, with its ground via in the
  `PWR_GND` pour.
- **`FB-MIDI-T` and `FB-MIDI-R` at the header**, `R-MIDI-T` and `R-MIDI-R`
  between them and `U-LVLSHIFT` (gates B and C, pins 6 and 8). The two drive
  traces run side by side as a pair back to the gate pins.
- **`R-MIDI-PU-T` and `R-MIDI-PU-R` at `U-LVLSHIFT`'s pins 5 and 9**, to the
  `DEV_3V3` track.

## Component table

| Ref | Value | Job | Confidence |
|---|---|---|---|
| `R-MIDI-T`, `R-MIDI-R` | 182 Ω 1 % 0.25 W, 1206 (UNI-ROYAL 1206W4F1820T5E, LCSC C247358) | RA/RC, either way round; **1 %, never 5 %** | `[ds CA-033 p.3]`, `[calc]`, `[sim]` |
| `FB-MIDI-T`, `FB-MIDI-R` | 600 Ω @ 100 MHz | CA-033's optional RF beads | `FB-CHAIN`'s part |
| `U-TVS-MIDI` | SP0504BAHTG | ESD at the header | `U-TVS-CHAIN`'s part |
| `J-MIDI` | JST B3B-PH-SM4-TB | The lead's header, surface mount: no tails over the bottom plate | `[from memory]` until JST's drawing is banked; LCSC code open |
| `J-MIDI-OUT` | SJ5-43502PM | The jack, panel-mounted | `[ds SAMESKY-SJ5-43502PM.pdf]`; panel thickness to confirm in hand |
| `CBL-MIDI` | PHR-3 lead | Jack to header | hand-built |

`R-MIDI-PU-T` and `R-MIDI-PU-R` are
[`led-strip-drive`](../led-strip-drive/led-strip-drive.md)'s.
