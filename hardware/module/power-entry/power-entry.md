# Module power entry — schematic

**Status:** Drawn 2026-09-21. Fourth module page.

Everything from the rack connector to the four rails, plus the load switch that
sends +12 V up the umbilical. This is the least conventional part of the module:
no published Eurorack design passes 360 mA of someone else's load through its
entry diode, so most of the prior art stops being applicable halfway down.

*Split 2026-09-21. The load switch moved to
[`umbilical-load-switch/`](../umbilical-load-switch/umbilical-load-switch.md)
and the indicator to [`panel-led/`](../panel-led/panel-led.md). The drawing
below is unchanged and still shows all three, because it is one drawing.*

## Interfaces

Every net that crosses this circuit's boundary. Quantities appear **only** as a
citation into `config/figures.yaml` — this table names nodes, it does not
restate values.

The `Dir` and `Peer` columns are defined once in
[`hardware/README.md`](../../README.md#the-interfaces-table).

| Node | Dir | Peer | Figure | Note |
|---|---|---|---|---|
| `+12V`, `-12V`, `GND` on `J-PWR-EURO` | in | Eurorack bus board | — | 16-pin shrouded keyed IDC. `GND` is the star point. **Its +5 V, CV and Gate pins are not used** — no-connects (owner, 2026-09-30; ADR 0023 point 3) |
| `MODULE ANALOG +12V` | out | `module/pitch-stage`, `module/breath-receive-stage`, `module/breath-output-stage`, `module/breath-response-shaper`, `module/mod-channels` | — | After `D1`, `FB1`, `C1`. The panel LED is not on it: it hangs on the load switch's output (`module/panel-led`) |
| `MODULE ANALOG −12V` | out | `module/pitch-stage`, `module/breath-receive-stage`, `module/breath-output-stage`, `module/breath-response-shaper`, `module/mod-channels` | — | After `D3`, `FB3`, `C3` |
| `DAC AVDD` | out | `module/dac8568`, `module/breath-receive-stage`, `module/breath-output-stage`, `interfaces/spi-link` | `dac-rail` | The LM317 output. Selected on the bench, per the figure's floor. **Not `module/digital-and-supervision`**, whose 74AHCT125 runs from `LOGIC_5V` |
| `LOGIC_5V` | out | `module/digital-and-supervision` | — | `U-REG-LOGIC`'s output, made here from the analog +12 V: the level shifter only. See *The logic 5 V* |
| `+12V` ahead of `D1`/`D2` | out | `module/umbilical-load-switch` | — | The branch is taken **before** the diodes; `U-LOADSW`'s `VCC` and the top of `R-ILIM` hang off it |
| `PWR_GND` | ref | `module/umbilical-load-switch`, `carrier/power-entry-instrument` | `umbilical-current`, `dig-gnd-topology` | The umbilical return, on its own layer-4 copper from the etherCON's pin 6 to the star |
| `AGND_MOD` | ref | `module/dac8568`, `module/pitch-stage`, `module/breath-receive-stage`, `module/breath-output-stage`, `module/breath-response-shaper`, `module/mod-channels`, `module/panel-led` | `dig-gnd-topology` | The module analog ground. Joins the star through `NT-AGND-MOD` and nowhere else — see *Grounding* |
| `DIG_GND` | ref | `module/digital-and-supervision`, `interfaces/spi-link` | `umbilical-pinmap`, `dig-gnd-topology` | `CS_MOD`'s return partner, down the umbilical. Joins the star through `NT-DIG-MOD` and nowhere else — see *Grounding* |
| `FB1`–`FB3` | — | — | `ferrite-bias-impedance` | One bead per branch; the impedance each actually has under its own DC bias is the figure |

## The circuit

*Connectivity is **[`netlist.yaml`](netlist.yaml)**, not this drawing.
The drawing is a representation of it, `tools/check-netlist.py` checks that
the two agree, and where they do not the netlist wins.*

```
  16-pin shrouded keyed IDC (J-PWR-EURO)
       │
  +12V ├───┬──[D1 1N5817]──[FB1]──[C1 100µF]──┬── MODULE ANALOG +12V
       │   │                                  │   OPA2197 ×6, INA828
       │   │                                  │
       │   │                                  └──[LM317LZ]──┬── DAC AVDD 5.21V
       │   │                                   150R/475R    │
       │   │                                   0.1%      [C 1µF]
       │   │                                                │
       │   └──[D2 1N5817]──[FB2]──[C2 47µF]──┬──────── PWR_GND (star)
       │                                      │
       │                    ┌─────────────┴──────────────┐
       │                    │      [R-ILIM 50mΩ]         │
       │                    │            │               │
       │                    │       ┌────┴────┐          │
       │                    │       │ VCC SENSE│         │
       │        panel ──────┼───────┤ ON       │         │
       │        toggle      │       │ LT1641-1 │         │
       │                    │       │   IS8    │         │
       │                    │       │ TIMER GATE├──┬──[R-GATE-SER 10Ω]──┐
       │                    │       │  FB      │   │                    │
       │                    │       └──┬────┬──┘   │             ┌──────┴──┐
       │                    │          │    │  [R-GATE-COMP 1k]  │ Q-LOADSW│ LFPAK56
       │                    │  [C-TIMER 10µF]│      │            │         │
       │                    │          │    │  [C-GATE 82nF]     └────┬────┘
       │                    └──────────┴────┼──────┴──────────────────┼── PWR_GND
       │                                    │                         │
       │                          [R-FB-HI 35.7k 1%]                  │
       │                                    ├─────────────────────────┤
       │                          [R-FB-LO 5.11k 1%]                  │
       │                                    │                         │
       │                                PWR_GND                       │
       │                                                              │
       │                                      UMBILICAL +12V ─────────► instrument
       │
  -12V ├───[D3 1N5817]──[FB3]──[C3 47µF]────────── MODULE ANALOG −12V
       │
   +5V ×   pins 11–12 not used: the module makes its own 5 V
       │
       │   MODULE ANALOG +12V ──[U-REG-LOGIC ADP7118AUJZ-5.0]── LOGIC_5V, 74AHCT125 only
       │
   GND └───────────────────────────────────────────── STAR POINT
```

## Three diodes, not two, and the branch is before them

**`D1` and `D2` are right, and the reason given for them was wrong.** An
earlier revision branched the two +12 V paths *after* a single shared
Schottky, so the instrument's current flowed through the same diode as the
module's analog rail and modulated its forward voltage by **120 mV**:
**0.24 V at 245 mA → 0.36 V at 612 mA** `[repo, digitised from Fig. 2 of
Diodes Inc DS23001 Rev.8]`.

> **This page said ~80 mV, and a reviewer's independent estimate said 75 mV.**
> Both were estimates. 120 mV is read off the actual forward-characteristics
> curve in `datasheets/discrete-and-power/1N5817.pdf`, and the extraction is
> calibrated against the two points the datasheet *guarantees*: the same
> method returns 0.454 V at 1.0 A and 0.746 V at 3.0 A against specified
> maxima of 0.450 V and 0.750 V. So it is good to about ±0.01 V — and the
> plotted curve sits essentially **on** the max spec, which means these are
> typical-to-max rather than typical. **60 % larger, and it changes nothing**
> — see below.

**The figure that followed it does not survive.** This page used to say the
modulation was worth "about 20 cents of breath-correlated pitch bend".
It implies ~21 % pitch sensitivity to the +12 V rail. Pitch full scale is
set by the DAC's *internal* reference, and AVDD comes from the LM317, so
the real path is 120 mV → LM317 line regulation (0.52 mV/V) → 62 µV on AVDD
→ OPA2197 PSRR (**110.5 dB worst case** `[SBOS737C p.8: ±3 µV/V max]`) →
**0.00044 cents** `[calc]`. *(The 114 dB this line carried is not in the
datasheet: TI specifies ±1 µV/V typ and ±3 µV/V max, i.e. 120 dB typ and
110.5 dB worst case. Using the guaranteed maximum rather than an unsourced
number scales the result by 1.50× and changes nothing.)* The
20-cent figure is a survival from the rail-divider topology ADR 0006
already deleted. Two reviewers reached this independently.

**Keep both diodes anyway**, for the reasons that do hold: fault isolation
between the exported rail and the analog rail, and HF isolation (`r_d` is
69 mΩ at 392 mA). Stated correctly they are still worth twenty cents. Left
as it was, the next reviewer who checks the arithmetic deletes the part.

> ### The ground path this section dismisses is the real one
>
> This page says the diode effect needs "no ground path at all". That was
> offered as a reason the diode split matters. It is also the reason the
> **larger** effect was never looked for — and three reviewers found it
> independently, in three different segments of the return path:
>
> | Segment | Effect |
> |---|---|
> | The power ribbon's six ground conductors, ≈17 mΩ | 6.2 mV → **7.4 cents** (24 on a flying bus) |
> | ~20–40 mΩ of busboard ground to a neighbouring module | 7–15 mV → **8–18 cents** |
> | The cable shield, if the etherCON shell bonds to the 10HP panel | **~7 cents** |
>
> All three are **breath-correlated**, because they are driven by the
> instrument's own supply current. `pitch-stage.md` puts the pitch stage's
> own drift at `pitch-cents-budget`. **The carefully engineered part of the pitch
> path is an order of magnitude below an effect that appeared in no
> document**, and because it tracks breath it will not sound like noise —
> it will sound like an intentional feature that has gone wrong.
>
> Not fixed here. It is a grounding and shield-bonding decision, and the
> shield policy is sixteen words in the whole repo.

`D3` protects −12 V, and it is the one of the three the other way round: a
negative rail's current flows out of the module into the bus, so its
**cathode is on the bus pin and its anode on the module side**. The sheet had
it the other way until 2026-09-30, which reverse-biased it in normal running
(found by the analog sims, [`sim/`](sim/README.md)). **There is no +5 V
branch**: the bus +5 V is not used, so a reversed ribbon has no unprotected
rail to land on — the gap this paragraph used to accept is closed.

## The logic 5 V — `U-REG-LOGIC`

The owner, 2026-09-30: *"Create the 5v locally"*, and *"We keep the standard
header, we just don't use the 5 volt. This keeps commonality of all the
Eurorack cable connectors."* So `J-PWR-EURO` stays the 16-pin A-100 header
(ADR 0023 point 3), its +5 V pins are no-connects, and the one 5 V load on the
module — the 74AHCT125 (`U-LVL-MOD`) — runs from `LOGIC_5V`, made here.
**`DAC AVDD` is not on it**: the DAC keeps its own LM317 rail, `dac-rail`.

**The part is ADI's `ADP7118AUJZ-5.0`** (TSOT-5), off the protected analog
+12 V, `EN` tied to `VIN`, `SENSE` to `VOUT` at the part, ground on
`DIG_GND`, with `C-LOGIC-REG` (4.7 µF 50 V X7R, 1206) in and out.

| | `[calc]` | Source |
|---|---|---|
| Load | 74AHCT125 `I_CC` 20 µA, plus `ΔI_CC` 1.5 mA per input held at 3.4 V × 3 driven inputs = 4.5 mA; two 10 kΩ pull-downs on `SCLK_DAC`/`DIN` at 5 V, 1 mA when high; switching 3 × 10 pF × 5 V × 2 MHz ≈ 0.3 mA. **≤ 6 mA** | `[ds SN74AHCT125.pdf p.4]` |
| Headroom | Input ≥ 11.4 V − `D1` ≈ 11.0 V against 5.0 V out: 6 V, where the dropout is 30/60 mV typ/max at 10 mA | `[ds ADI-ADP7118.pdf p.3]` |
| Dissipation | (12.4 − 5.0) V × 6 mA = **44 mW**; θJA 170 °C/W gives **+7.5 °C** | `[ds p.5]` |
| Input rating | 20 V max against a 12.6 V bus maximum | `[ds p.3]` |
| Noise | 11 µV rms, 10 Hz–100 kHz — more than a logic rail needs; it keeps the level shifter's supply from being the noisiest node beside the DAC | `[ds p.3]` |
| Capacitors | more than 1.5 µF in and out under all conditions; 4.7 µF X7R in 1206 keeps it at 12 V of DC bias | `[ds p.4]` |

The few milliamps come off the analog +12 V after `D1`/`FB1`/`C1`; the
op-amps on that rail reject it by their PSRR, and the LM317 by its line
regulation (see *Three diodes* above for how small that path is).

**Beads, not resistors, and the rating is the part that matters.** A ≥1 A bead
is specified because the common 0805 600 Ω part is ~300 mA and **a saturated
bead is a wire**. Package does not set the rating — the *series* does: within
one vendor's 0805 600 Ω line there are 600 mA and 2.3 A versions, and another
"600" part is 60 Ω at 3 A. Read the series, not the footprint.

**What each bead is actually worth under its own DC bias** — the figure this
page owns, `ferrite-bias-impedance`. The Laird MI1206K601R-10's "600 Ω" is
its zero-bias number, and the impedance-under-bias curve family collapses it
badly at current:

| Bead | Carries | Impedance at 100 MHz |
|---|---|---|
| `FB1`, `FB3` | the low-current rails | **~580–614 Ω** |
| `FB2` | `umbilical-current` | **~280–310 Ω** |

`FB2` is the one that matters and it has roughly **half** the impedance the
part number advertises, because it is the bead carrying the umbilical's
current. That is not a reason to change the part — it is a reason not to
believe "600 Ω" anywhere in this drawing. Read off the banked drawing rev E,
`datasheets/discrete-and-power/MI1206K601R-10-ferrite-bead.pdf`.

## Grounding — four layers, one star (owner, 2026-09-30)

The owner, 2026-09-30: *"Four layer in the module board is fine."* So
`PCB-MODULE` is **four layers, 1.6 mm**, and the three module grounds meet at
**one point**, the star at `J-PWR-EURO`'s ground pins — this is the figure
`dig-gnd-topology`:

| Ground | Where it is | How it reaches the star |
|---|---|---|
| `PWR_GND` | its own copper on **layer 4**, from the etherCON's pin 6 to the header's ground pins, touching nothing on the way (ADR 0004) | it *is* the star's copper |
| `DIG_GND` | a **layer-2 plane** under the etherCON, `U-LVL-MOD`, `U-REG-LOGIC` and the SPI traces, so `SCLK`/`MOSI`/`CS` return directly under themselves | `NT-DIG-MOD`, at the star |
| `AGND_MOD` | a **layer-2 region** under the analog block — the DAC8568, every op-amp, the LT5400, the trimmers and `J-B2B-MOD` — kept apart from the `DIG_GND` plane | `NT-AGND-MOD`, at the star |

Layers 1 and 3 carry parts and signals; the analog rails route on layer 3
over the analog region. The DAC8568 sits at the boundary with its digital
pins toward the plane, and its one `GND` pin on the analog region.

**Why not the proposal that bridged `AGND_MOD` to the plane under the DAC.**
That was the obvious shape and it is wrong here, twice. The datasheet asks for
the opposite: the DAC's ground *"would be connected directly to an analog
ground plane. This plane would be separate from the ground connection for the
digital components until they were connected at the power-entry point of the
system"* `[ds DAC8568CIPW.pdf p.49]`. And the umbilical makes it worse than
usual: pin 8 (`DIG_GND`) and pin 6 (`PWR_GND`) are tied together at the
instrument (ADR 0018), so they are two parallel conductors carrying the
instrument's return, about half each `[calc: two equal 24 AWG conductors,
2 m]`. With a bridge under the DAC, that half would cross the analog region on
its way to the star and move the jacks' reference with every breath. With the
ties at the star, it crosses only the `DIG_GND` plane, where a millivolt
harms nothing.

**The jack board stays two layers.** It carries the jacks, pots and LED and
one ground, `AGND_MOD`, which reaches it only on `J-B2B-MOD`'s five ground
pins; nothing on it needs a second reference, so there is nothing for a
second plane to separate (`PCB-MODULE-JACK`).

**The standoffs are metal** (owner, 2026-09-30), so they could tie the boards'
copper at four more points. **Their pads are on `AGND_MOD` on the jack board
and on no net on the main board** — a plated ring with clearance from every
plane. On the jack board `AGND_MOD` is the only ground there is; on the main
board any net would be a second inter-board tie: to `AGND_MOD` a parallel
loop around the header's five ground pins, to `DIG_GND` or `PWR_GND` a second
junction with the analog ground away from the star. Mechanical only, and
one-ended electrically (`MECH-STANDOFF-MOD`).

`AGND` — no suffix — is not a ground at all: it is an in-amp input
(ADR 0003).

## Still open

*(`L-BUCK-IN` and the umbilical's input LC moved with the load switch — they
are in [`umbilical-load-switch.md`](../umbilical-load-switch/umbilical-load-switch.md).)*

- **The ribbon's own ground drop is breath-correlated** (the table under
  *The ground path this section dismisses*): the umbilical's return reaches
  the rack's supply through the power ribbon and the busboard, so the star
  moves against the rest of the case with the instrument's current. The
  shield row of that table no longer applies — the NE8FAV's shell is plastic
  and its G tab is on no net (ADR 0023; `module-main` README) — but the ribbon
  and busboard rows do, and no layout inside the module removes them.
  **Decided by: owner** — accept it, or take the instrument's supply around
  the rack (its own adapter, or a dedicated cable to the PSU).
- **No fuse on the analog rails.** The load switch covers only the umbilical
  branch. Mutable, Telex and others fit PTCs on their entry rails; ADR 0005's
  deletion argument was about the *instrument-end* polyfuse and does not reach
  these. **Decided by: owner** — a PTC per rail (≈50 mA hold) costs ≈0.1 V on
  each rail and protects the rack from a module-internal short; the case's
  own supply protection is the alternative.

*(The entry bulk — 100 µF on +12 V and 47 µF on the other two — is 2–5× the
surveyed 10–22 µF, and it is kept: `C-BULK-RAIL` gives the reason, and the
added inrush at rack power-on is 194 µF, a few percent of a typical case's
total.)*
