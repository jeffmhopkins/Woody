# Instrument power entry — schematic

**Status:** Split out of `carrier.md` 2026-09-21 (Phase B), and edited since.
**The KiCad sheet `power-entry-instrument.kicad_sch` is the source** (ADR 0019);
placed on the main board
([`../../boards/main-board/README.md`](../../boards/main-board/README.md)), its
datasheets banked. The
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
| `UMBILICAL +12V` at `J-UMB` | in | `module/umbilical-load-switch` | `umbilical-pinmap`, `umbilical-current` | Arrives down the umbilical from the module's load switch. On this board it is `J-UMB` pin 3, `D-REVSHUNT`, `D-TVS-PWR` and `Q-INRUSH`'s source and gate network — **nothing that stores charge** (§1a) |
| `PWR_GND` at `J-UMB` | ref | `module/power-entry` | `umbilical-pinmap`, `dig-gnd-topology` | This board's only supply return, down the umbilical to `U-ISO`'s 0V at the module (ADR 0027). It reaches the module's star only through `DIG_GND` and `NT-DIG-MOD`, and none of this board's DC current crosses the star (`dig-gnd-topology`) |
| `INST_POS12`, the LED row feed | out | `carrier/led-strip-drive` | `led-row-current` | `Q-INRUSH`'s drain (§1a), which `C-STRIP-BULK`, this circuit's part, sits on. Nothing is in series between the drain and this tap |
| `INST_POS12`, analog | out | `carrier/breath-excitation-reference` | — | REF5050 `VIN`, and the V+ of both OPA2197 halves. **The same node as the row above**, for the same reason |
| 5 V, buck A | out | `J-MCU`, `carrier/led-strip-drive` | `matrix-led-current` | Through `D-USBOR` and `J-MCU`, down three conductors of `CBL-MCU-RIBBON` onto the dev board's 5 V pad and `TP2`, and on to the 74AHCT125 |
| `PWR_GND` pour | ref | `carrier/service-uart`, `carrier/led-strip-drive`, `carrier/carrier`, `interfaces/breath-sense-link` | `dig-gnd-topology` | Layer 2, §2. The whole board returns here, and the breath link's two clamps, and so do the plates: the bottom plate through this board's mounts, the key plate through the cassette's columns to the same mounts (ADR 0022, ADR 0025). **`carrier/breath-adc` and `carrier/breath-excitation-reference` are no longer listed**: both of those pages say their return is `AGND_INST`, which reaches this pour on the **single tie** and is a different node everywhere else — and that distinction is the whole point of the star |

## §1 Power entry

*Connectivity is **[`netlist.yaml`](netlist.yaml)**, not this drawing.
The drawing is a representation of it, `tools/check-netlist.py` checks that
the two agree, and where they do not the netlist wins.*


```
 J-UMB pin 3  +12V ──┬──[D-REVSHUNT SS34]──┐
 (UMBILICAL_POS12)   │   cathode to +12V   │
                     ├──[D-TVS-PWR SMAJ15A]┤
                     │                     │
                  [Q-INRUSH AO3401A]       │    source up, drain down; its gate
                     │                     │    network is drawn in §1a
      INST_POS12 ────┤                     │
                     ├─────────────────────┼──── the LED row, direct
                     │                     │     (every D-LED, lighting.led_count)
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

**`D-REVSHUNT` goes at the connector, ahead of `Q-INRUSH` and `L-BUCK-IN`.** Its job is a
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

The 11.4 V is ADR 0005's arriving voltage, which still subtracts the module's
Schottky; since ADR 0027 that diode is on U-ISO's input, and the instrument
sees U-ISO's 12 V less the load switch, the cable and Q-INRUSH, ~11.8 V
(§1a). 11.4 V is the conservative side here: a lower input is a smaller
|R_neg|, so the margin at ~11.8 V is larger, ~130×   [calc: 11.8² / 1.26 = 110 Ω]
```

> **This result depends on `C-BUCK-IN` being an electrolytic with real ESR.**
> Substituting a low-ESR ceramic raises Q and the paragraph stops being true.
> The BOM row says electrolytic; keep it that way.

**Simulated 2026-09-30** (`sim/`). The margin holds — `instrument-input-z-margin`
— but not for the reason above. The ESR range above is two datasheet
*maxima*, and a real part sits below its maximum, so it is not a worst case.
The run sweeps `C-BUCK-IN`'s ESR down to a third of its 100 kHz maximum and
adds what this derivation leaves out: `C-STRIP-BULK` at the input node ahead of
the LC, and the umbilical's resistance behind it. Those set the peak. Keep
the electrolytic anyway.

**Start-up, from the module's isolated converter** (ADR 0027), also in `sim/`:
cold and hot-plugged, through the load switch, the cable, `Q-INRUSH` and this
input, the instrument starts at every corner and the buck's input never falls
back once it is running. A hot-plug into a running module keeps `U-ISO` under
its lowest over-current threshold — `hotplug-iso-ocp` — because of §1a.

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

**Counted from the bottom up it is higher** (#18 E4) `[calc]`: the whole
lighting budget on the matrix (3 W at 5 V, 600 mA; ADR 0014), the 64 matrix
LEDs' idle draw (~32–64 mA `[from memory]`), the ESP32-S3 and its PSRAM
through the ME6217 (~100–160 mA, radio off, ADR 0015) and the level shifter
give **≈ 0.82 A, 82 %**. The R-78E5.0-1.0 carries full load to 60 °C ambient
and derates linearly to 60 % at 85 °C `[ds R-78E5.0-1.0.pdf p.3, Derating
Graph]`, so 82 % holds to about 71 °C at the part `[calc: 60 + (100 − 82) /
40 × 25]`. That is the number to carry until E6 measures the rail, and the
reason the M8 soak should put a thermocouple on `U-BUCK` (#18 E2/E4; open,
the owner's).

**Rack and USB together: the share is not controlled** (#18 E1; open, the
owner's decision). With the rack up and a USB host plugged in — the
configuration and telemetry case, `firmware/README.md` — `VCC_5V` is fed from
both sides: the buck through `D-USBOR` (SS14, `V_F` 0.50 V max at 1 A
`[ds SS14.pdf]`) and `VBUS` through the Matrix's own `D1` (B5819WS, 0.60 V
max at 1 A `[ds B5819WS.pdf]`). The sources are 5.0 V ± 5 % (`[ds
R-78E5.0-1.0.pdf p.2]`) and USB's 4.75–5.25 V `[from memory: USB 2.0]`, so
which one carries the load is set by tens of millivolts, and at the corners
`VBUS` carries all of it. All of it is up to the ~0.82 A above, and `D1` is
rated `P_D` 200 mW at `RθJA` 500 °C/W `[ds B5819WS.pdf]` — about 0.45 W
would be twice that, and more than a USB 2.0 port's 500 mA. The analyses
above and ADR 0005/0014 cover rack alone and USB alone, never both. What
decides it: a firmware cap on the matrix while a USB host is attached, an
ideal-diode OR in place of `D-USBOR`, or `D1` lifted in the instrument build
(which gives up bench running on USB, ADR 0005).

---

## §1a Hot-plug inrush — `Q-INRUSH`

*Added 2026-09-30. Simulated in `sim/` (`hot-plug`, `replug-late`,
`replug-early`); the figure is `hotplug-iso-ocp`.*

**Why it is here.** The module's load switch (`module/umbilical-load-switch`)
has its FET enhanced whenever the module runs, instrument or not. A plug-in
therefore used to put everything on this board that holds charge straight
onto `U-ISO`'s output through 2 m of cable, and the LT1641's current limit had
to pull back a gate that `C-GATE-LOADSW` was holding up. The simulation had
`U-ISO` at its over-current threshold for over a hundred microseconds at every
corner; whether the RPA20 then hiccups is unpublished. The fix belongs here,
at the capacitors, not at the module: nothing the LT1641 does can be fast
enough when its FET is already on, and the module cannot tell whether an
instrument is attached (every umbilical conductor is spoken for,
`umbilical-pinmap`).

```
 UMBILICAL_POS12 ─┬──────────────────────┬────────────────────── S
  (J-UMB pin 3)   │                      │                       │
          [C-INRUSH-GS 1uF]      [R-INRUSH-GS 1M]       [Q-INRUSH AO3401A]
                  │                      │              G ───────┤
 INRUSH_GATE ─────┴────────┬─────────────┴───────┬──────┘        │
                           │                     │               │
                  [C-INRUSH-GD 22nF]     [R-INRUSH-G 1M]         │
                           │                     │               │
                  [R-INRUSH-GD 22R]              ├──[D-INRUSH-RST 1N4148W]── cathode to INRUSH_GATE
                           │                     │               │
 INST_POS12 ───────────────┴─────────────────────┼────────────── D ── C-STRIP-BULK, L-BUCK-IN,
                                                 │                    the LED row, the analog block
 PWR_GND ────────────────────────────────────────┘
```

A P-channel FET with its **source at the connector** and its drain on
`INST_POS12`, the node that carries every capacitor on the instrument's 12 V:
its body diode points back at `J-UMB`, so nothing charges except through the
channel. `C-INRUSH-GD` from gate to drain makes it a Miller integrator: once
the gate reaches its plateau, the drain can rise only as fast as
`R-INRUSH-G`'s current can charge `C-INRUSH-GD`. `D-REVSHUNT` and `D-TVS-PWR`
stay at the connector, ahead of it.

**The numbers** `[calc]`, each checked by the run:

```
Charge behind it: C-STRIP-BULK 470 µF + C-BUCK-IN 100 µF
                  + 14 × C-LED 100 nF                          ≈ 571 µF
The plug-in step: J-UMB jumps 0 → 12 V in microseconds. The gate follows
  through C-INRUSH-GS and is held back through C-INRUSH-GD:
  ΔV_GS = −12 V × (22 nF + 55 pF) / (1 µF + 645 pF + 22 nF + 55 pF)
        = −0.26 V, against V_GS(th) −0.5 V minimum           [ds AO3401A p.2]
The delay: the gate relaxes towards −V_in/2 through R-INRUSH-GS ∥ R-INRUSH-G
  τ = 0.5 MΩ × 1.02 µF = 0.51 s; to a −1.5 V plateau from 0 of −5.9 V:
  0.51 × ln(5.9 / 4.4) = 0.15 s
The ramp: at the plateau the gate is ~10.3 V above ground
  I = 10.3 V / 1 MΩ − 1.5 V / 1 MΩ = 8.8 µA
  dV/dt = 8.8 µA / 22 nF = 400 V/s → 571 µF × 400 V/s = 0.23 A, ~30 ms
On:  V_GS = −V_in / 2 = −5.9 V at 11.8 V; R_DS(on) ≤ 60 mΩ at −4.5 V [ds p.2]
  at `umbilical-current`, 0.36 A × 60 mΩ ≈ 22 mV; at the LT1641's 1.10 A
  worst-case trip, 66 mV and 73 mW
Its ratings: V_DS −30 V against D-TVS-PWR's 24.4 V clamp [ds SMAJ15A p.2];
  V_GS ±12 V against half the input — a surge does not reach the gate,
  C-INRUSH-GS carries the source's jump to it
```

The run agrees with all of it and says more: `U-ISO` peaks at `hotplug-iso-ocp`
on a hot-plug at 65 corners — the peak is the ramp's end,
not the plug — `VCC` at the load switch does not move, the instrument is up in
94–183 ms, and the ramp takes about 50 ms 10–90 %, slower than the arithmetic
above because the loads come on during it. **`Q-INRUSH` dissipates 1.8 W at
most, ~85 mJ a start**: the AO3401A's single-pulse rating at 50 ms is about
12 W and its transient impedance there about 12 K/W `[ds p.4 Figures 10–11,
read off the curves]`, so ~20 K of rise, once, at plug-in.

**Two parts are there for the plug itself, not the ramp.**
- **`R-INRUSH-GD`** damps `J-UMB`'s node. With the FET off, the plug is the
  cable's inductance into `D-TVS-PWR`'s capacitance and the gate network;
  undamped that rings to twice the rail, past `D-TVS-PWR`'s 15 V standoff.
  With 22 Ω in the Miller leg the run peaks at 14.2 V at its worst corner.
- **`D-INRUSH-RST`** resets the gate after an unplug. `C-INRUSH-GS` keeps
  `V_GS` while the instrument drains, so the source falls to ground with the
  gate still below it; the diode pulls the gate back up to −0.4 V once the
  input is down, and the next plug-in starts from off (`replug-late`, 200 ms
  after an unplug). Silicon, not Schottky: a small Schottky's leakage is
  comparable to the 8.8 µA that sets the ramp.

**What it does not cover: a replug within tens of milliseconds.** While the
bulk still holds a few volts, `C-INRUSH-GS` is still holding `Q-INRUSH` on,
and a replug is a hot-plug without the limiter — `replug-early` (30 ms)
records `U-ISO` reaching its threshold, as every plug-in did before. The
window narrows at both ends: 3 ms after an unplug the bulk has barely fallen
and the run touches the threshold for about 2 µs; 200 ms after, it has
drained and the replug starts from off. How long the window lasts is set by
how fast the instrument drains, which the model's loads set. **E6 decides**,
with a current probe on `U-ISO` during a quick replug.

**What else was tried, and why not** (`sim/`'s deck with the instrument as it
was, at the same corners, 2026-09-30):

| Candidate | `U-ISO` at its threshold | Why not |
|---|---|---|
| none (as it was) | 114–157 µs | — |
| `C-ISO-OUT` 330 µF, the largest standard value the RPA20's 1000 µF capacitive-load limit leaves room for with ~571 µF behind the switch | 93–134 µs | the converter still supplies the plug |
| 2.2 Ω in `C-STRIP-BULK`'s leg | up to 188 µs, and some corners never start | `C-BUCK-IN` and the loads are still on the plug |
| 4.7 Ω in the line | 3–60 µs, and the start never reaches 90 % | 1.7 V dropped at the run current |
| 100 µH in the line | over 100 µs, and a 16 V ring | the LT1641's limit still overshoots |
| `C-GATE-LOADSW` 10 nF | 8–13 µs | shorter, not gone; the cold-start ramp is 8× faster |
| `C-GATE-LOADSW` 150 nF | 209–305 µs | **a bigger gate capacitor makes it worse**: it holds the gate up |
| `R-GATE-COMP` 10 kΩ | the model stops starting | ten times the datasheet's own 1 kΩ, and the datasheet gives no stability guidance to move it by |
| a 5.1 V zener from `C-GATE-LOADSW`'s node to the output | 2 µs | the best module-side part, and it still reaches the threshold |

At the LT1641's highest gate drive (`dV_GATE` 15 V, where `D-GATE-CLAMP`
holds it) the unlimited hot-plug was 270–364 µs and pulled `VCC` to 10.15 V,
0.25 V above the `ON` pin's turn-off: the old hazard was worse than the
figure that recorded it, which was taken at the minimum gate drive.

### The 13.5 V rating on this rail

**The LED row's `VDD` absolute maximum is 13.5 V** `[ds
datasheets/led/WS2815B-V1.pdf p.2]`, the lowest rating on `INST_POS12`, and
**nothing on this board holds the rail below it**: `D-TVS-PWR`'s breakdown is
16.7 V minimum `[ds LITTELFUSE-SMAJ-SERIES-SMAJ15A.pdf]`, and `U-ISO`'s own
over-voltage protection starts at 13.8 V `[ds RECOM-RPA20-AW.pdf PD-5]`. In
operation the rail is `U-ISO`'s regulation, 12 V +3.1 % at worst
(`power-entry.md`), and a surge through the on FET into ~571 µF moves it by
tenths of a volt; the plug's ring lands on `J-UMB` while `Q-INRUSH` is off
(§1a). **What is not covered is a converter that fails regulating high**,
anywhere between 13.5 V and its OVP: fourteen LEDs that cannot be reworked
after reflow (ADR 0028) would see it unclamped. **Accepted by the owner,
2026-10-01** (pre-layout review A4-4): a converter that fails regulating high
is out of scope, and no clamp is added (ADR 0027, its 2026-10-01 amendment).

### On USB power alone

ADR 0005 keeps the USB OR so the instrument runs on the bench without a rack.
**Since the analog block and the LED row moved to `INST_POS12`, USB alone runs
the MCU, the matrix and the keys only**: no breath (the sensor, `U-REF-BREATH`
and `U-BUF` are on `INST_POS12`) and no LED supply. The LED buffer
`U-LVLSHIFT` is on the Matrix's own 5 V (`INST_5V_A`), which USB feeds, so it
is live, and a write to the row would drive 5 V edges through `R-LED-SER`
into LEDs with no supply, past their input rating referred to a supply that is
absent `[ds WS2815B-V1.pdf p.2]`. **There is no 12 V sense; firmware gates the
row on the breath reading instead** — with the rail up the ADC reads the
sensor's zero-pressure offset, with it down near zero (`firmware/README.md`,
*What the hardware requires*, *The lights*). Recorded 2026-10-01 (A4-15).

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

## Bulk at the LED row's feed

**`C-STRIP-BULK` (470 µF 25 V) sits at the LED row's feed end**, on
this board — "bulk capacitance belongs where the current swings" `[repo] 0014`.
The lights are LEDs on this board since ADR 0028 (`lighting.led_count`, the
last added in the tail corner on 2026-10-02), each with its own
100 nF (`C-LED`), which take the edges; this one takes the row's PWM step.
The row switches its whole current at the LEDs' PWM rate: at
`led-row-current`'s upper end, a 250 µs half-period drawn from this
capacitor alone would sag it by about 0.1 V `[calc: 0.210 A × 250 µs /
470 µF = 0.11 V]` — the umbilical and the load switch supply most of it, so
that is the worst case, and the value stays. The ~2 kHz rate is the WS2815's
`[ds datasheets/led/WS2815B-V1.pdf p.1, 'scan frequency is of 2KHz']`. A 10 × 10 mm SMD can is a height
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
| `C-STRIP-BULK` | 470 µF 25 V (UCW1E471MNL1GS) | At the LED row's feed end, on this board (ADR 0028) | `[repo]`, `[calc]` |
| `Q-INRUSH` | AO3401A P-FET, SOT-23 | Hot-plug inrush limiter: source at `J-UMB`, drain on `INST_POS12` (§1a) | `[ds]`, `[calc]`, `[sim]` |
| `R-INRUSH-GS`, `R-INRUSH-G` | 1 MΩ 1 % each | Its gate divider: `V_GS` half the input when on; `R-INRUSH-G` sets the ramp | `[calc]` |
| `C-INRUSH-GS` | 1 µF 50 V X7R | Gate to source: the gate follows the plug-in step. **At least 45× `C-INRUSH-GD`** | `[calc]`, `[sim]` |
| `C-INRUSH-GD`, `R-INRUSH-GD` | 22 nF 50 V X7R, 22 Ω | The Miller ramp, and the damping of `J-UMB`'s node at the plug | `[calc]`, `[sim]` |
| `D-INRUSH-RST` | 1N4148W | Resets the gate after an unplug | `[sim]` |

---

## Still open

*Moved verbatim from `carrier.md`'s `Still open` list.*

- ~~**A low-profile regulator.**~~ **Closed by ADR 0017**: on the one main
  board the R-78E fits upright where it stands, under a key board included
  (`mechanical/drc.echo` "regulator block fits where it stands"). Re-open only
  if that rule fails.
