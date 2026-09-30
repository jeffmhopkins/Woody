# Instrument power entry — schematic

**Status:** Split out of `carrier.md` 2026-09-21 (Phase B). Every line below was
moved verbatim; nothing was reworded and no value was touched in the move. The
board-level context this circuit sits in — the dev board's connector `J-MCU`,
the umbilical's `J-UMB`, the block diagram, the board outline — stays on
[`carrier.md`](../carrier.md).

> **One buck, not two (2026-09-26, ADR 0015).** The second regulator ("buck
> B") fed the display board, which was removed; its row, its diode, its
> input capacitor and `C-BULK-DISP` went with it. What is below is the one
> that is left.

## Interfaces

Every net that crosses this circuit's boundary. Quantities appear **only** as a
citation into `config/figures.yaml` — this table names nodes, it does not
restate values.

The `Dir` and `Peer` columns are defined once in
[`hardware/README.md`](../../README.md#the-interfaces-table).

| Node | Dir | Peer | Figure | Note |
|---|---|---|---|---|
| `UMBILICAL +12V` at `J-UMB` | in | `module/umbilical-load-switch` | `umbilical-pinmap`, `umbilical-current` | Arrives down the umbilical from the module's load switch. `D-REVSHUNT` sits at the connector, ahead of `L-BUCK-IN` |
| `PWR_GND` at `J-UMB` | ref | `module/power-entry` | `umbilical-pinmap` | This board's only supply return, down the umbilical to the module star |
| `+12V` strip feed | out | `carrier/led-strip-drive` | — | Taken direct off the input node. `C-STRIP-BULK` is this circuit's part. **The same net as the row above** — `D-REVSHUNT` is a shunt and `D-TVS-PWR` a clamp, so nothing is in series between `J-UMB` pin 3 and this tap |
| `+12V` analog | out | `carrier/breath-excitation-reference` | — | REF5050 `VIN`, and the V+ of both OPA2197 halves. **Also the same net**, for the same reason |
| 5 V, buck A | out | `J-MCU`, `carrier/led-strip-drive` | `matrix-led-current` | Through `D-USBOR` and `J-MCU`, down three conductors of `CBL-MCU-RIBBON` onto the dev board's 5 V pad and `TP2`, and on to the 74AHCT125 |
| `PWR_GND` pour | ref | `carrier/service-uart`, `carrier/led-strip-drive`, `carrier/carrier`, `interfaces/breath-sense-link` | `dig-gnd-topology` | Layer 2, §2. The whole board returns here, and the breath link's two clamps, and so do the plates: the bottom plate through this board's mounts, the key plate through the cassette's columns to the same mounts (ADR 0022, ADR 0025). **`carrier/breath-adc` and `carrier/breath-excitation-reference` are no longer listed**: both of those pages say their return is `AGND_INST`, which reaches this pour on the **single tie** and is a different node everywhere else — and that distinction is the whole point of the star |

## §1 Power entry

*Connectivity is **[`netlist.yaml`](netlist.yaml)**, not this drawing.
The drawing is a representation of it, `tools/check-netlist.py` checks that
the two agree, and where they do not the netlist wins.*


```
 J-UMB pin 3  +12V ──┬──[D-REVSHUNT SS34]──┐
                     │   cathode to +12V   │
                     ├──[D-TVS-PWR SMAJ15A]┤
                     │                     │
                     ├─────────────────────┼──── WS2815 strip, direct
                     │                     │     (J-LED)
                     │                     │     [C-STRIP-BULK 470 µF 25V]
                     │                     │
                     ├──[REF5050]──┬────────┼──── §2 analog (its VIN through R-REF-IN and a
                     │   in  out   │        │     15 V clamp: breath-excitation-reference.md)
                     │   │    [C-REF-OUT#2] │
                     │  [C-REF-OUT#1]       │
                     │                      │
                     ├── OPA2197 V+ ────────┤
                     │                      │
                     ├──[L-BUCK-IN]──┬──────┼──[R-78E5.0 A]──▷|──┬── dev board 5V
                     │   22 µH       │      │                 D-USBOR  ├── 74AHCT125
                     │   [C-BUCK-IN 100µF]  │                         └── (8×8 matrix,
                     │      25V, real ESR   │                              via the board)
                     │                      │
 J-UMB pin 6 PWR_GND ┴──────────────────────┴──── PWR_GND pour
```

**`D-REVSHUNT` goes at the connector, ahead of `L-BUCK-IN`.** Its job is a
rollover patch lead swapping pins 3 and 6 `[repo] 0004`; it has to conduct
immediately and let the module's LT1641-1 latch off. An inductor between the
fault and the diode is the wrong way round.

**There is no fuse and no power switch on this board** (ADR 0005). The current
limit is at the module.

**The aluminium plates bond to `PWR_GND`, never to `AGND`** `[repo] 0009`.
The bottom plate bonds through this board's mounts (ADR 0022). The key plate
bonds through the cassette's columns, whose standoffs stand on the same
plated mounts (ADR 0025); no key board's `GND_CHAIN` touches either plate.

### Derivations

**The input LC is stable** `[calc]`, which partly closes `power-entry.md`'s
"damping the input LC" open item — for the instrument end only:

```
L = 22 µH (L-BUCK-IN, SWPA6028S220MT), C = 100 µF (C-BUCK-IN, UCM1E101MCL1GS)
f0 = 1/(2π√LC) = 3.39 kHz
Z0 = √(L/C)    = 0.469 Ω
ESR of the UCM: ≤ 0.26 Ω at 100 kHz (its impedance limit) and
  ≤ tanδ/(2π·120·C) = 0.14/0.0754 = 1.86 Ω at 120 Hz
  [ds NICHICON-UCM-SERIES-UCM1E101MCL1GS.pdf p.2]
  → at f0 it lies between, so Q = Z0/ESR lies between 0.25 and 1.8
  → worst case mild peaking: filter output impedance ≤ Q·Z0 = 0.85 Ω

Constant-power load at typical play:
  226 mA × 5 V = 1.13 W out ÷ 0.90 = 1.26 W in at 11.4 V   [repo] 0005
  R_neg = −V²/P = −103 Ω
Margin: |R_neg| / Z_peak = 103 / 0.85 ≈ 120× (42 dB), worst case
```

> **This result depends on `C-BUCK-IN` being an electrolytic with real ESR.**
> Substituting a low-ESR ceramic raises Q and the paragraph stops being true.
> The BOM row says electrolytic; keep it that way.

**Regulator loading** `[calc]`, from ADR 0005's load table:

```
Clamp-legal worst on the 5 V rail, as ADR 0005 tabled it         928 mA  [repo] 0005
Less the display board's share (removed, ADR 0015)          ~150–250 mA  ESTIMATED
The one buck (real-time board + matrix + 74AHCT125)          ~680–780 mA
R-78E5.0-1.0 rating                                            1000 mA
                                                              → 68–78 %
```

Seventy-odd percent, inside a body running 10–20 K above ambient, is near
enough to want the derating curve. **The display board's share was only ever
estimated**, so the figure is a range until E6 measures the rail.

---

## §2 The ground, on four layers

The main board is four layers — signal / ground / power / signal, 1.6 mm
(owner, 2026-09-29, [ADR 0017](../../../docs/decisions/0017-one-main-board.md)
amendment of that date). This is the ground those layers carry. It decides
the **instrument end** of `dig-gnd-topology`; the module end is that figure's,
and it is not settled by this board.

- **Layer 2 is `PWR_GND`, one unbroken plane** from `J-UMB` to the mouth end,
  under every SPI, chain and LED-data trace. `J-UMB` pin 6 (`PWR_GND`) and
  pin 8 (`DIG_GND`, through `NT-DIG`, ADR 0018) land on it at the header. So
  each SPI edge on `SCLK`, `MOSI` and `CS_MOD` returns in the plane directly
  under its own trace to pin 8 — the return an SPI link wants, and the
  layout rule `interfaces/spi-link` states. Layer 3 carries the rails; no
  signal is routed on layer 3 across a gap in layer 2.
- **`AGND_INST` is an island on layer 2 under the analog block only**:
  `U-BREATH`, `U-REF-BREATH`, `U-BUF`, the reference's feedback network,
  `R-ADCDIV-U`/`-L`, `C-AA-ADC` and the analog side of `U-ADC`. A moat
  surrounds it, bridged at one point by **`NT-AGND`**. The ~13 mA the
  reference, the buffer and the sensor return (derived on
  `breath-sense-link.md`) flows across the island to that tie and nowhere
  else, so no `PWR_GND` current — umbilical, LED or logic — shares copper
  with the analog references.
- **`NT-AGND` sits under `U-ADC`**, between its `VSS` (pin 4) and its digital
  pins. The ADC is the one part with a pin on each side: its `CLK`, `DIN`,
  `DOUT` and `CS` edges return through the tie straight into the plane under
  their traces to `J-MCU`, and no digital trace crosses the moat anywhere
  else `[calc]`: a tie at the far end of the board, at `J-UMB`, would make
  those edges return along the island and back up the plane, a loop the
  length of the board.
- **The breath pair crosses the moat as a pair.** `BREATH_SENSE` and
  `AGND_SENSE` run side by side over the plane to `J-UMB` pins 1 and 2.
  `AGND_SENSE` is taken at the sensor's own `GND` pin
  (`breath-sense-link.md`, *Where it sits*), so any voltage between the island
  and the plane is common to both legs and is the module in-amp's to reject.
  This is what frees the tie to sit at the ADC rather than at the connector.
- **The clamps return to the plane at the connector**: `D-TVS-PWR`,
  `D-REVSHUNT`, `U-TVS-SPI` and both `D-TVS-BREATH` diodes, so a strike at
  `J-UMB` never crosses the island.
- **The plates bond to the plane** (ADR 0009, ADR 0022), never to the island.

E11 is the test: the breath reading at rest with the LEDs sweeping and the
keys scanning, at both ends of the link.

---

## Strip bulk at the feed points

*Moved verbatim from `carrier.md`'s LED section, now `led-strip-drive.md`,
where it sat beside the LED data drive.*

**`C-STRIP-BULK` (470 µF 25 V) sits at the strip feed point**, which is on
this board — "bulk capacitance belongs where the current swings" `[repo] 0014`.
One strip since ADR 0016, so one capacitor. A 10 × 10 mm SMD can is a height
item; it goes in the regulator block (`config/body.yaml` `boards.tall_h`) and
`mechanical/drc.echo` says whether that fits.

---

## Component table

*Rows moved verbatim from `carrier.md`'s component table. Existing BOM rows are
named as they stand; **proposed** rows have no BOM entry yet.*

| Ref | Value | Job | Confidence |
|---|---|---|---|
| `U-BUCK` | R-78E5.0-1.0 SIP-3 | The one dev board, the matrix, the level shifter. **10.4 mm tall upright**, which fits anywhere on the main board, under the key boards included (`mechanical/drc.echo` "main board parts room under the key boards", and "regulator block fits where it stands") | `[repo]` |
| `L-BUCK-IN` | 22 µH ≥1 A (SWPA6028S220MT) | The L of the input LC, one per buck (one buck) | `[repo]` + `[calc]` |
| `C-BUCK-IN` | 100 µF 25 V electrolytic (UCM1E101MCL1GS) | **Must have real ESR; a ceramic breaks the damping** | `[ds]` + `[calc]` |
| `D-USBOR` | SS14 | **Between the buck and the dev board's 5V pin** — the OR node is that pin, and USB can back-feed it | `[repo]` |
| `D-REVSHUNT` | SS34 | At the connector, ahead of `L-BUCK-IN` | `[repo]` |
| `D-TVS-PWR` | SMAJ15A | Across the power pair | `[repo]` |
| `C-STRIP-BULK` | 470 µF 25 V (UCW1E471MNL1GS) | At the strip feed point, which is this board (one strip, ADR 0016) | `[repo]` |

---

## Still open

*Moved verbatim from `carrier.md`'s `Still open` list.*

- ~~**A low-profile regulator.**~~ **Closed by ADR 0017**: on the one main
  board the R-78E fits upright where it stands, under a key board included
  (`mechanical/drc.echo` "regulator block fits where it stands"). Re-open only
  if that rule fails.
