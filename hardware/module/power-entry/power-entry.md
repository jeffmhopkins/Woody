# Module power entry — schematic

**Status:** Drawn 2026-09-21. Fourth module page.

Everything from the rack connector to the module's rails, the rail fuses, and
the instrument's isolated supply that feeds the load switch sending +12 V up
the umbilical. This is the least conventional part of the module: no published
Eurorack design powers someone else's instrument from the bus, so most of the
prior art stops being applicable halfway down. **Since 2026-09-30 (ADR 0027)
the instrument's power is drawn from the rack rail to rail, through `U-ISO`,
and none of its current returns through the rack's ground.**

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
| `+12V`, `-12V`, `GND` on `J-PWR-EURO` | in | Eurorack bus board | — | 16-pin shrouded keyed IDC. `GND` is the star point, `BUS_GND` on the sheet — a net of this circuit only. **Its +5 V, CV and Gate pins are not used** — no-connects (owner, 2026-09-30; ADR 0023 point 3) |
| `MODULE ANALOG +12V` | out | `module/pitch-stage`, `module/breath-receive-stage`, `module/breath-output-stage`, `module/breath-response-shaper`, `module/mod-channels` | — | After `PTC-POS12`, `D1`, `FB1`, `C1`. The panel LED is not on it: it hangs on the load switch's output (`module/panel-led`) |
| `MODULE ANALOG −12V` | out | `module/pitch-stage`, `module/breath-receive-stage`, `module/breath-output-stage`, `module/breath-response-shaper`, `module/mod-channels` | — | After `PTC-NEG12`, `D3`, `FB3`, `C3` |
| `DAC AVDD` | out | `module/dac8568`, `module/breath-receive-stage`, `module/breath-output-stage`, `module/digital-and-supervision` | `dac-rail` | `U-REG-DAC`'s output, the LT3042 set by `R-SET-DAC`: inside the figure's floor on every part, with nothing to adjust — see *The DAC rail*. Also the supply of the 74AHCT125 (`U-LVL-MOD`) that drives the DAC's SPI pins, so they can never sit above it — see *The DAC rail's load* |
| `LOGIC_5V` | out | `module/digital-and-supervision` | — | `U-REG-LOGIC`'s output, made here from the analog +12 V: the SPI receiver `U-RX-MOD` and `CS_MOD`'s pull-up only — not the level shifter, which is on `DAC AVDD`. See *The logic 5 V* |
| `ISO_POS12` | out | `module/umbilical-load-switch` | `umbilical-current` | `U-ISO`'s isolated +12 V (ADR 0027): `U-LOADSW`'s `VCC`, the top of `R-ILIM` and of the `ON` divider hang off it. Until 2026-09-30 the load switch took the bus +12 V ahead of the diodes, `BUS_POS12_RAW`, which is now a net of this circuit only |
| `PWR_GND` | ref | `module/umbilical-load-switch`, `carrier/power-entry-instrument` | `umbilical-current`, `dig-gnd-topology` | `U-ISO`'s isolated return and the umbilical's pin 6, on its own layer-4 copper. It meets `DIG_GND` at the etherCON (`NT-UMB-MOD`) and nothing else — see *Grounding* |
| `AGND_MOD` | ref | `module/dac8568`, `module/pitch-stage`, `module/breath-receive-stage`, `module/breath-output-stage`, `module/breath-response-shaper`, `module/mod-channels`, `module/panel-led` | `dig-gnd-topology` | The module analog ground. Joins the star through `NT-AGND-MOD` and nowhere else — see *Grounding* |
| `DIG_GND` | ref | `module/digital-and-supervision`, `interfaces/spi-link` | `umbilical-pinmap`, `dig-gnd-topology` | `CS_MOD`'s return partner, down the umbilical. Joins the star through `NT-DIG-MOD` and nowhere else — see *Grounding* |
| The beads `FB1`, `FB2`, `FB3` and `FB4` | — | — | `ferrite-bias-impedance` | One bead per branch; the impedance each actually has under its own DC bias is the figure |

## The circuit

*Connectivity is **[`netlist.yaml`](netlist.yaml)**, not this drawing.
The drawing is a representation of it, `tools/check-netlist.py` checks that
the two agree, and where they do not the netlist wins.*

```
  16-pin shrouded keyed IDC (J-PWR-EURO)
       │
  +12V ├──[PTC-POS12]──[D1 1N5817]──[FB1]──[C1 100µF]──┬── MODULE ANALOG +12V
       │                                               │   OPA2197 ×7, INA828
       │                                               ├──[U-REG-DAC LT3042EMSE]── DAC AVDD
       │                                               │   set by [R-SET-DAC 52.3k 0.1%] ‖ [C-SET-DAC 100nF]
       │                                               └──[U-REG-LOGIC]── LOGIC_5V, the SPI receiver only
       │
       ├──[PTC-ISO]──[D2 1N5817]──[FB2]──[L-ISO-IN 22µH]──┐
       │                                                   │
       │               [L-CM-ISO 1mH], one winding in each leg, dots on the filter side
       │                                                   │
       │                                                   ├── ISO_VIN_POS
       │                   [C2 100µF] and [C-ISO-IN 4.7µF] across the 24 V
       │                                                   │
       │                                    ┌──────────────┴─────────┐
       │                                    │ Vin               +Vo ├──┬── ISO_POS12 ──► U-LOADSW
       │                                    │ [U-ISO RPA20-2412SAW]   │ [C-ISO-OUT 100µF]  (umbilical-load-switch)
       │                                    │ GND                0V ├──┴── PWR_GND ──► umbilical pin 6
       │                                    └──────────────┬─────────┘           │
       │                                                   │               [NT-UMB-MOD] at the etherCON
       │                                   [C-ISO-Y 22nF], ISO_VIN_POS to PWR_GND │
       │                                                   │               DIG_GND ──► umbilical pin 8
       │                                               ISO_VIN_NEG                │
       │                                   the choke's −12 V winding              │
       │                                                   │               [NT-DIG-MOD] at the star
  -12V ├──[D4 1N5817]──[FB4]───────────────────────────────┘                      │
       │   (cathode to the bus)                                                   │
       ├──[PTC-NEG12]──[D3 1N5817]──[FB3]──[C3 47µF]── MODULE ANALOG −12V         │
       │   (D3 cathode to the bus)                                                │
   +5V ×   pins 11–12 not used: the module makes its own 5 V                      │
       │                                                                          │
   GND └── BUS_GND, THE STAR ──[NT-AGND-MOD]── AGND_MOD                           │
                              └─────────────────────────────────────────────────┘
```

*The drawing was redrawn on 2026-09-30 for ADR 0027. The load switch it used
to show is on
[`umbilical-load-switch.md`](../umbilical-load-switch/umbilical-load-switch.md),
which draws it in full; it hangs on `ISO_POS12` and `PWR_GND` now, not on the
bus +12 V and the star.*

## Three diodes, not two, and the branch is before them

*Four since 2026-09-30: `D2` and `D4` are the two legs of `U-ISO`'s input
(ADR 0027), and `D4` is cathode-to-bus like `D3`. The instrument's current
still never shares a diode with the module's analog rails, which is what this
section is about.*

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
set by the DAC's *internal* reference, and AVDD comes from its own
regulator, so the real path is 120 mV → that regulator's line regulation →
AVDD → OPA2197 PSRR (**110.5 dB worst case** `[SBOS737C p.8: ±3 µV/V max]`) →
**0.00044 cents** `[calc]`, worked with the LM317L's 0.52 mV/V (62 µV on
AVDD). *(Since 2026-10-01 `U-REG-DAC` is the LT3042, at most 2 nA/V ×
52.3 kΩ + 3 µV/V = 0.108 mV/V `[ds ADI-LT3042.pdf p.3; calc]`, 13 µV: the
0.00044 cents is now an upper bound.)* *(The 114 dB this line carried is not in the
datasheet: TI specifies ±1 µV/V typ and ±3 µV/V max, i.e. 120 dB typ and
110.5 dB worst case. Using the guaranteed maximum rather than an unsourced
number scales the result by 1.50× and changes nothing.)* The
20-cent figure is a survival from the rail-divider topology ADR 0006
already deleted. Two reviewers reached this independently.

**Keep both diodes anyway**, for the reasons that do hold: fault isolation
between the exported rail and the analog rail, and HF isolation (`r_d`
~0.53 Ω in `D2` at 0.23 A and ~3.2 Ω in `D1` at the analog rails' draw, `diode-split-rationale`). Stated correctly they are still worth twenty cents. Left
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
> **Removed at the source, 2026-09-30 — ADR 0027.** The instrument's supply
> is now drawn rail to rail through an isolated converter, so its current is in
> none of those three segments; see *The instrument's supply* below, and the
> `gnd-*` sims in [`sim/`](sim/README.md), which put the old path at 4.2–21
> cents over the bus positions and swings they sweep and the new one below
> 10⁻⁷. The shield row never applied to this hardware: both etherCON shells are
> plastic with the G tab on no net (ADR 0021, ADR 0023).

`D3` protects −12 V, and it is the one of the three the other way round: a
negative rail's current flows out of the module into the bus, so its
**cathode is on the bus pin and its anode on the module side**. The sheet had
it the other way until 2026-09-30, which reverse-biased it in normal running
(found by the analog sims, [`sim/`](sim/README.md)). **There is no +5 V
branch**: the bus +5 V is not used.

**What the diodes protect against, and what they cannot.** A ribbon that swaps
+12 V and −12 V — the 10-pin case, or a plug one row off — lands on `D1`–`D4`
and nothing conducts. **A 16-pin cable fitted backwards at an unkeyed bus
header is different, and nothing on this module can stop it.** Module pin *k*
then meets bus pin 17 − *k* `[calc]`: the module's six ground pins (3–8) land
on the bus's CV, +5 V and +12 V (14–9), so `BUS_GND` copper shorts the rack's
+12 V to its +5 V and CV, upstream of every fuse and diode here. `D1`–`D4` keep
the module's own rails from conducting; the short is the rack's. Doepfer's own
warning is that a wrongly turned cable *"will destroy the module"*
`[ds DOEPFER-A100-TECHNICAL-DETAILS-a100t_e.html]`. This is the generic
16-pin Eurorack hazard, kept with the 16-pin header for commonality (ADR 0023
point 3); the header's keyed shroud prevents it at this end only. **Accepted
by the owner, 2026-10-01** (pre-layout review A3-2): all six ground pins stay
wired and no part is added — wiring fewer of them, so that a reversed cable
lands the module's ground on CV rather than on the rack's supplies, was the
alternative. The guard is the build: mark the red stripe at both ends of the
cable (`J-PWR-EURO`'s row).

## The instrument's supply — `U-ISO` (ADR 0027)

The owner, 2026-09-30: *"There needs to be another way to avoid the breath
affecting pitch. This is unacceptable. We are powering the controller through
the rack, there has to be a valid way to do this."* The way is an isolated
DC/DC converter whose **input is across the rack's +12 V and −12 V**: the
instrument's power then leaves the rack on +12 V and returns on −12 V, and the
rack's ground carries none of it. The comparison with a ground-sense conductor
and with a balanced dummy load, and the residual, are ADR 0027's.

**The part is RECOM's `RPA20-2412SAW`** `[ds RECOM-RPA20-AW.pdf]` (owner,
2026-09-30: *"I thought the point was to do a RECOM that was in stock"*):
9–36 V in, 12 V at 1670 mA out, 1.6 kVDC, 25.4 × 25.4 × 10.2 mm on 5.6 mm
pins `[PD-1, PD-5, PD-7, PD-8]`. **The plain part, no suffix: no CTRL pin**
— always on — **and a Trim pin**, left open for 12 V `[PD-1 Note 2]`. It is
end-of-life (last-time buy 6 July 2026), so spares are bought now, and its
successor the RP20-2412SAW drops into the same holes; both are ADR 0027's.
Its output,
`ISO_POS12`, feeds the load switch, which is unchanged
([`umbilical-load-switch.md`](../umbilical-load-switch/umbilical-load-switch.md));
its return is `PWR_GND`.

| | `[calc]` | Source |
|---|---|---|
| Input voltage | 24.0 V nominal across the rails, 22.8 V at −5 % on both; less `PTC-ISO` (≤ 0.40 Ω × 0.23 A = 0.09 V), `D2` and `D4` (~0.23 V each at 0.23 A) and the bead and inductor → **~23.4 V typical, ≥ 22.2 V** | `[ds BOURNS-MF-MSMF.pdf p.1]`, `D-REVPOL`'s row |
| Against its range | 9–36 V; under-voltage lockout on at 8–9 V, off at 7–8 V: **13 V of margin** at the bottom | `[ds PD-2]` |
| Typical play | `umbilical-current` × 12 V ≈ **4.5 W** out, 0.37 A of 1.67 A (~22 %); **~82 %** there (~81 % off the efficiency curve, ~0.97 W off the dissipation curve) → 5.47 W in → **~0.23 A on each of +12 V and −12 V** `[calc: 5.47 W / 23.4 V = 0.234 A]` | `[ds PD-3]`, the RPA20-2412SAW's own curves at 24 V in |
| Clamp-legal worst (ADR 0005's table) | ~6.95 W out (0.58 A), ~1.25 W lost → **~0.37 A per rail** at 22.2 V | `[ds PD-3]` |
| Overload held just under the load switch's minimum trip, 0.78 A | 9.4 W, ~1.5 W lost → **~0.49 A per rail** | `R-ILIM`'s row; `[ds PD-3]` |
| Hot-plug into a running module | `Q-INRUSH` holds the instrument's inrush, so `U-ISO` peaks at `hotplug-iso-ocp` out → **~0.37 A per rail** `[calc: 0.56 × 12 / 0.82 / 22.2]` | `hotplug-iso-ocp`; `[ds PD-3]` |
| An early replug, the load switch at its 1.10 A worst-case limit | 13.2 W, ~1.85 W lost, for tens of ms → **~0.68 A per rail** — the only case that reaches the limit (*Protection*, below) | `umbilical-load-switch.md`; `[ds PD-3]` |
| Toggle off | quiescent input **20 / 55 mA** typ/max | `[ds PD-2]` |
| Its limit against the load switch's | over-current protection at **110–160 %** of 1.67 A, hiccup: the minimum, 1.84 A, is above the LT1641's 1.10 A worst-case trip, so the LT1641 decides every start and fault **except a replug inside `Q-INRUSH`'s window**, where the carrier's `replug-early` sim reaches `U-ISO`'s threshold (`hotplug-iso-ocp`) — see *Protection* | `[ds PD-5]` |
| Output | 12 V: accuracy ± 2.0 % max, line ± 0.2 % max, load ± 0.1 %, 0.02 %/K → **~± 3.1 %** over 40 K; 50 mV p-p ripple; the load switch's `ON` and `PWRGD` thresholds sit below its minimum with more margin than they had on the bus | `[ds PD-2, PD-5]`; the `hot-plug` sim holds `VCC` above `ON`'s turn-off at every corner |
| RECOM's input fuse | *"Recommended fuse: 3A slow blow type"*, where *"input over-current protection is also required"* — `PTC-ISO` is it, sized for this branch | `[ds PD-5 Note 5]` |
| Loss in the module | ~0.95 W in `U-ISO`, ~0.1 W in `D2`/`D4`; 12.5 K/W on a board in still air, so **~+12 °C** on its case; over-temperature protection at 110 °C | `[ds PD-5, PD-6]` |

**The rack's −12 V carries the instrument now.** At typical play the module
draws ~0.27 A from +12 V and ~0.25 A from −12 V (its own `module-own-draw`,
from *Fuses on the rails* below, plus `U-ISO`'s ~0.23 A on each) `[calc]`,
where it drew ~0.40 A and ~0.04 A. Check the case's −12 V
rating: many Eurorack supplies give −12 V less than +12 V.

**The input filter.** `U-ISO` switches at 550 kHz `[ds PD-2]`; RECOM does
not publish its reflected ripple current. Its own filter, for EN55032 Class A,
is a fuse, a 1 µH choke and 47 µF/50 V electrolytic `[ds PD-7]` — no
common-mode choke. `L-ISO-IN` (22 µH) with `C2` (100 µF 50 V electrolytic)
and `C-ISO-IN` (4.7 µF) is that filter with more of both, and since
2026-10-01 `L-CM-ISO`'s leakage, 3.9 µH typ, is in series with it (*The
common mode*, below): at 550 kHz the
inductance is ~90 Ω against under 0.17 Ω of capacitor (`C-ISO-IN`'s 0.34 Ω at
100 kHz, falling above it, in parallel with `C2`'s 0.34 Ω impedance
`[ds NICHICON-UCM-SERIES-UCM1E101MCL1GS.pdf p.3]`), so **under 0.25 %** of
whatever it reflects reaches the rack `[calc]`. It is damped by `C2`'s ESR:
`f₀` = 1/(2π√(25.9 µH × 104.7 µF)) = 3.1 kHz, `Z₀` = √(L/C) = 0.50 Ω, against
the converter's negative input resistance `V²/P` = 23.4² / 5.26 =
**−104 Ω** — 200× the
filter's characteristic impedance, the same shape and margin as the
instrument's own input LC `[calc]`. **`C2` must stay an electrolytic.**
`power-entry/sim`'s `iso-input-z` runs the filter as netlisted, with the
diodes, the beads, `PTC-ISO`, the ribbon and the rack's supply behind it: the
impedance the converter sees never exceeds 1.8 Ω anywhere from 1 Hz to
2 MHz — it is highest at DC, set by the series resistance, so there is no
resonant peak left — which is **56× or more** inside the −104 Ω at every
corner of `C2`'s ESR, the ribbon, the choke and the supply; and 0.06 % of the
converter's 550 kHz input current reaches the rack's +12 V conductor.

**The LED row's PWM — `led-pwm-rail-ripple`.** The instrument's fourteen
WS2815B-V1 (`lighting.led_count`) pulse at 2 kHz scan / 4 kHz refresh `[ds WS2815B-V1.pdf p.1]`,
right on the filter's 3.1 kHz corner, and `U-ISO` passes whatever of that
current reaches it to its input. `power-entry/sim`'s `led-pwm` runs the row's
real waveform (each LED its share of `led-row-current`'s top end, in phase, at
every duty from 1/256 to 255/256, at 2–4 kHz, and as seven lit or as
all fourteen spread over the period) through `C-STRIP-BULK`, the umbilical, the
load switch, `U-ISO` as output power over efficiency, this filter and the
rack. Two things keep it small. **The filter has no gain in the band**: `D2`,
`D4`, `PTC-ISO` and the beads sit in series with `L-ISO-IN` and `C2`, so the
loop is overdamped and from 1 to 10 kHz at most 76 % of the converter's input
current reaches the rack (`iso-input-z`, `rack_band`); the corner is not a
resonance. **And the instrument keeps half or more of the row's current** in
`C-STRIP-BULK` (91 mA p-p of 182 reaches `U-ISO` at 2 kHz, less above).
Worst — all fourteen in phase at half duty, 2 kHz, `C2` at its highest ESR
and a 200 mΩ rack supply — the case's rails move **7.2 mV p-p at the header**
(3.1 mV nominal) and 5.8 mV at the bus where a neighbouring module taps
them; the module's analog rails 2.2 mV (+12 V) and 3.5 mV (−12 V); `DAC_AVDD`
0.2 µV at an assumed 80 dB for the LT3042; and the jacks: **pitch 0.0010
cents** (TI's OPA2197 model, with `DAC_AVDD`'s ripple passed whole to the
DAC; against the module's own ground — a receiver at the PSU end of the bus
sees `led-pwm-pitch`, `interfaces/system/sim`), mod 0.59 µV, breath 0.28 mV (through `R-OFFNEG` from −12 V). The
review's ~13 mV bound (A4-13) took `C2`'s ESR as the only damping; it is not
reached, and the filter needs no damper. On the review's own premise — no
instrument bulk, the whole row out of `U-ISO` — a 200 mΩ supply would take
the header to 15–19 mV (`led-pwm-at-iso`, recorded). The rack's copper and
supply are estimates; E6 scopes the case's ±12 V with the row at mid
brightness.

**The common mode — `L-CM-ISO` and `C-ISO-Y` (owner, 2026-10-01).** The
converter's switching drives current through its isolation capacitance,
1100 pF typ `[ds PD-5]`. The netlist gives that current two ways back to the
converter's input: `C-ISO-Y` (`ISO_VIN_POS` to `PWR_GND`, beside the
converter; RECOM's filter has none `[PD-7]`), or a loop round the module —
`NT-UMB-MOD`, `DIG_GND`, `NT-DIG-MOD`, the star, `NT-AGND-MOD`, `C3`, `FB3`,
`D3`, the bus, `D4`, `FB4` — which is a few ohms at 550 kHz. Without a choke
most of it took the loop and crossed the star, and a larger `C-ISO-Y` alone
resonated with it (the deck that found it is
`docs/review/2026-10-01-pre-layout-review/F3-u-iso-cm-loop/`; ADR 0027's
2026-10-01 amendments). **`L-CM-ISO`** — Bourns PM3700-40-RC, 1 mH minimum,
4 A, 0.020 Ω, between the filter and the converter's pins, one winding in each
leg `[ds BOURNS-PM3700-CM-CHOKE.pdf p.1]` — puts its common-mode impedance in
that loop, and **`C-ISO-Y` is 22 nF C0G** with it, so the current goes home
beside the converter. `power-entry/sim`'s `cm-loop` holds the share crossing
the star **under the owner's 10 %** at every corner of the choke's core loss
(500 Ω to 3.6 kΩ per winding — the datasheet gives only its 20 dB band from
500 kHz), its inductance (±30 %), the ribbon and `C-ISO-Y`: 0.6–5.4 % at
550 kHz, under 1.7 % at 1.65 MHz, under 0.2 % at 5.5 MHz, and no resonance
anywhere from 500 kHz to 30 MHz (peak 5.9 %). With the 1 nF the sheet carried
before, the same choke leaves 15–78 % on the star (`cm-loop-y-1n`). Every
copper parasitic in the deck is an estimate, and how much current it is
RECOM does not publish: **E6 probes it** at the star. At breath frequencies
the barrier carries nothing measurable: the `gnd-isolated` sim puts under
0.3 nA in the tie.

**Protection.** A reversed ribbon is blocked from both sides of the converter
by `D2` and `D4`. A fault inside `U-ISO` or its input network is below the
load switch, so it has its own fuse, `PTC-ISO` (next section) — RECOM's
input fuse `[PD-5 Note 5]`. `U-ISO`'s own short-circuit protection is
continuous and self-recovering, its over-current protection hiccups, and it
has over-temperature protection `[PD-5]`. **The load switch acts first on
every start and fault it sees from rest**, because it trips below `U-ISO`'s
1.84 A minimum. **The exception is a replug inside `Q-INRUSH`'s window**: the
carrier's `replug-early` sim (30 ms after an unplug) finds the instrument's
bulk still charged and `Q-INRUSH` still enhanced, so the first current edge is
set by `C-ISO-OUT`, the cable and the LT1641's loop response rather than its
static trip, and it reaches `U-ISO`'s threshold (`hotplug-iso-ocp`, a recorded
hazard). `U-ISO` then hiccups: at 1.84 A out its input is roughly
1.84 × 12 / 0.85 / 22.2 ≈ 1.2 A per rail `[calc]`, under `PTC-ISO`'s 1.5 A
trip, so probably benign — and the hiccup pulls `ON` under its turn-off, which
un-latches the LT1641-1 for a fresh start. **E6 scopes it**: `ISO_POS12` and
the LT1641's `ON` pin during a quick replug.

## Fuses on the rails — `PTC-POS12`, `PTC-NEG12`, `PTC-ISO`

The owner, 2026-09-30: *"You're good to add the PTCs."* They protect **the
rack from the module**: a short inside the module pulls on the case's supply
and browns out every module in it. Each sits at the header, **ahead of its
reverse diode** — so it also carries the current if the diode fails short —
and each is a Bourns MF-MSMF 1812 `[ds BOURNS-MF-MSMF.pdf]`.

**Where, and why three.** One on each analog rail, and one on the converter's
+12 V leg, because the load switch sits on `U-ISO`'s *output* and cannot see a
fault in the converter or its input network. One leg is enough there: the
branch is a series loop from +12 V through `U-ISO` to −12 V, and the only
element from it to ground, `C-ISO-Y`, hangs on the +12 V side of the fuse.

**The analog rails' load** `[calc]`, worst case: fourteen OPA2197 channels at
1.3 mA max `[ds OPA2197.pdf p.8]` = 18.2 mA on both rails; the INA828,
0.65 mA (0.85 mA over temperature) `[ds INA828IDR.pdf p.6]`, on both; on +12 V
only, the DAC rail's branch, ~8.2 mA (*The DAC rail's load*, below), and
`U-REG-LOGIC`'s ~5.1 mA. That is the figure `module-own-draw` with the jacks
open, and on +12 V **~92 mA** with all six jacks shorted at full scale through
their 1 kΩ `R-OUT-PROT` (6 × 10 mA) `[calc: 18.2 + 0.85 + 8.2 + 5.1 + 60]`.

| Part | Hold / trip at 23 °C | Hold at 50 / 60 °C | Must hold | Resistance → drop at the typical load | Voltage |
|---|---|---|---|---|---|
| `PTC-POS12`, `PTC-NEG12`: MF-MSMF020/60-2 | 0.20 / 0.40 A | **0.15 / 0.13 A** | 92 mA worst (+12 V) | 0.40 Ω min → **13 mV** at `module-own-draw`; 6.0 Ω an hour after a trip (R1max) → **≤ 0.19 V** | 60 V: a short between the two analog rails puts 24 V across the pair |
| `PTC-ISO`: MF-MSMF075/33X-2 | 0.75 / 1.5 A | **0.56 / 0.49 A** | 0.37 A clamp-legal worst; 0.49 A overload held under the load switch's trip (it holds at 50 °C and may trip at 60 °C — a fault state either way); ~0.37 A on a hot-plug, and 0.68 A on an early replug for tens of ms, below its trip current | 0.11–0.40 Ω → **≤ 0.09 V** at 0.23 A | 33 V: a shorted `U-ISO` input puts all 24 V across it |

`[ds p.1, p.9]`. The previous page's "~0.1 V" was from memory; the datasheet
gives 13 mV on a fitted part and 0.19 V at its worst `[calc: 0.40 and 6.0 Ω ×
32 mA]`. **At that worst the rails still work**: +12 V analog ≥ 11.4 − 0.19 −
`D1` − `FB1` ≈ 10.9 V (10.5 V with all six jacks shorted, 0.55 V across the
fuse), above the breath output's 10 V swing and the LT3042's and the
ADP7118's dropout. **The
load switch no longer sees any of it**: its `ON` divider is on `U-ISO`'s
regulated output, and `U-ISO`'s input has 13 V of margin. The `as-netlisted`
power-on sims run with the fuses at their fitted resistance, and `ptc-tripped`
at 6.0 Ω: `DAC AVDD` still comes up inside its window.

## The logic 5 V — `U-REG-LOGIC`

The owner, 2026-09-30: *"Create the 5v locally"*, and *"We keep the standard
header, we just don't use the 5 volt. This keeps commonality of all the
Eurorack cable connectors."* So `J-PWR-EURO` stays the 16-pin A-100 header
(ADR 0023 point 3), its +5 V pins are no-connects, and the 5 V loads on the
module's SPI receiver `U-RX-MOD` (74AHCT14) runs from `LOGIC_5V`, made here.
**`DAC AVDD` is not on it**: the DAC keeps its own rail, `dac-rail`, and
so does the 74AHCT125 (`U-LVL-MOD`) that drives the DAC's pins, because
`LOGIC_5V` comes up first and goes down last (owner, 2026-10-01;
[`digital-and-supervision.md`](../digital-and-supervision/digital-and-supervision.md),
*The buffer's supply*).

**The part is ADI's `ADP7118AUJZ-5.0`** (TSOT-5), off the protected analog
+12 V, `EN` tied to `VIN`, `SENSE` to `VOUT` at the part, ground on
`DIG_GND`, with `C-LOGIC-REG` (4.7 µF 50 V X7R, 1206) in and out.

| | `[calc]` | Source |
|---|---|---|
| Load | `I_CC` 20 µA for the 74AHCT14. `ΔI_CC` 1.5 mA per input held at 3.4 V × its 3 cable-side inputs = 4.5 mA; switching its 6 gate outputs × 10 pF × 5 V × 2 MHz ≈ 0.6 mA; `R-PULL-CS`, at most (5.0 − 3.3) V / 100 kΩ = 17 µA with an instrument holding `CS_MOD` high. **≈ 5.1 mA.** The cable-side inputs idle at about 3.0–3.2 V, below the 3.4 V the `ΔI_CC` row is stated at, where the supply-current curve is higher: the bench confirms it | `[ds SN74AHCT125.pdf p.4, SN74AHCT14.pdf p.5 and Figure 6-1]` |
| Headroom | Input ≥ 11.4 V − `D1` ≈ 11.0 V against 5.0 V out: 6 V, where the dropout is 30/60 mV typ/max at 10 mA | `[ds ADI-ADP7118.pdf p.3]` |
| Dissipation | (12.4 − 5.0) V × 5.1 mA = **38 mW**; θJA 170 °C/W gives **+6.4 °C** — at twice the load, still under +13 °C | `[ds p.5]` |
| Input rating | 20 V max against a 12.6 V bus maximum | `[ds p.3]` |
| Noise | 11 µV rms, 10 Hz–100 kHz — more than a logic rail needs | `[ds p.3]` |
| Capacitors | more than 1.5 µF in and out under all conditions; 4.7 µF X7R in 1206 keeps it at 12 V of DC bias | `[ds p.4]` |

The few milliamps come off the analog +12 V after `D1`/`FB1`/`C1`; the
op-amps on that rail reject it by their PSRR, and `U-REG-DAC` by its line
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
| `FB1`, `FB3` | the analog rails, tens of mA | **~580–614 Ω** |
| `FB2`, `FB4` | `U-ISO`'s input, ~0.23 A typical (~0.37 A clamp-legal) | **~440–480 Ω** (~310 Ω) |

`FB2` and `FB4` are the ones that matter, and they lose a quarter to a half of
the impedance the part number advertises, because they carry the instrument's
supply. *(Until ADR 0027 `FB2` carried all of `umbilical-current` and read
about half the nameplate.)* That is not a reason to change the part — it is a reason not to
believe "600 Ω" anywhere in this drawing. Read off the banked drawing rev E,
`datasheets/discrete-and-power/MI1206K601R-10-ferrite-bead.pdf`.

## The DAC rail — `U-REG-DAC`, set by `R-SET-DAC`

The owner, 2026-10-01: *a precision-set LDO that needs no adjustment, so
`DAC AVDD` lands inside the window on every part with no trimming and no way to
misadjust it.* It replaces the LM317L and the 50 Ω trimmer that was fitted
earlier the same day (`docs/review/2026-10-01-pre-layout-review/VERIFIED-F8.md`,
A8-8).

**Why the window, and why its floor is hard.** The DAC8568 C grade runs its
internal 2.5 V reference at gain 2 for a 0–5 V output, and TI specifies that
range only for `AVDD` ≥ 5 V — *"AVDD ≥ 5V; grades C and D: maximum output
voltage 5V when using internal reference"*, and the reference-input row
*"Grades C/D, AVDD = 5.0V to 5.5V"* `[ds DAC8568CIPW.pdf p.3, p.4]`. Under
5 V the output buffer cannot reach full scale and the top calibration point
lands in its compression (ADR 0004). The top is the part's 5.5 V operating
maximum; its absolute maximum is 6 V `[p.2]`. That is `dac-rail`'s `floor`.

**The part is ADI's LT3042** (`LT3042EMSE#TRPBF`, MSOP-10 with exposed pad,
machine-placed, LCSC C461518). It is a precision current reference followed by
a unity-gain buffer: the `SET` pin sources 100 µA into `R-SET-DAC` and `OUT`
follows `SET` `[ds ADI-LT3042.pdf p.14]`, so

`DAC AVDD = I_SET × R-SET-DAC + V_OS`

with no gain on any error, and `R-SET-DAC` is a 52.3 kΩ ±0.1 % ±25 ppm/°C
thin-film part, Viking ARG05BTC5232, 0805 `[ds VIKING-ARG-THIN-FILM-RESISTOR.pdf p.3]`.

| Term | Guaranteed limit | At the rail `[calc]` | Source |
|---|---|---|---|
| `I_SET` | 98–102 µA over 2–20 V in, 0–15 V out, 1–200 mA and temperature (99–101 µA at 25 °C) | ±105 mV | `[ds ADI-LT3042.pdf p.3]` |
| `V_OS`, `OUT` − `SET` | ±2 mV over the same | ±2 mV | `[p.3]` |
| `R-SET-DAC` | ±0.1 %, and ±25 ppm/°C over 40 °C of drift from 25 °C: ±0.2 % | ±10 mV | `[VIKING p.3]` |
| Leakage into or out of `SET` | 100 nA is 0.1 % `[p.14]`: `C-SET-DAC` (NP0, 5 GΩ minimum) is about 1 nA of it, the rest is the board, guarded | ±5 mV | `[WALSIN p.13]` |
| Line, load, input | inside the `I_SET` and `V_OS` rows' conditions: 10.8 V (a tripped fuse) to 12.6 V in, 2–9 mA out | — | `[p.3]` |

**At every corner of all of it, `DAC AVDD` is 5.11–5.35 V** — `dac-rail`'s
derivation has the arithmetic, and `power-entry/sim`'s `dac-rail-spread`
holds it, 65 corners, with at least 50 mV to spare at both ends of 5.00–5.50 V.
**Nothing is adjusted and nothing can be.** `R-SET-DAC` aged to its endurance
limit as well — ±0.5 % after 1000 h at full rated power and 70 °C `[VIKING
p.4]`, where it runs at 0.4 % of its rating `[calc: 5.23² / 52.3 kΩ = 0.52 mW
of 1/8 W]` — still lands inside (`dac-rail-aged`). The E grade is guaranteed from 0 °C to 125 °C, and −40 °C by
design `[p.4 Note 9]`, which covers a rack.

**How it is wired** `[ds ADI-LT3042.pdf p.12, p.18]`:

- `EN/UV` and `PGFB` tied to `IN`: always on, and **fast start-up off**.
  Fast start-up drives `SET` with 2 mA until `PGFB` crosses 300 mV; a power-good
  divider set near the top of this spread could fail to cross and leave it on,
  which drives the rail to the input. Tied to `IN` it cannot engage. `PG` open.
- `ILIM` to ground: the internal limit, 220 mA minimum `[p.4]`. The rail draws
  under 10 mA; a short on it dissipates about 2 W, inside the part's thermal
  limit.
- `C-REG-IN` and `C-REG-OUT`, 10 µF 50 V X7R 1206 (`C-REG-DAC`): at least 4.7 µF
  each, and at `OUT` an ESR under 50 mΩ and ESL under 2 nH for stability `[p.15,
  p.17]`; 50 V in 1206 so the 12 V input keeps over 4.7 µF of bias-derated
  capacitance `[from memory: no bias curve is banked for this part]`.
  `C-DEC-REG-IN` (100 nF) stays at the `IN` pins.
- `C-SET-DAC`, 100 nF **NP0** across `R-SET-DAC`. NP0 because a ceramic at
  `SET` with a piezoelectric dielectric turns vibration into hundreds of µV on
  the rail, and X7R also loses capacitance with bias `[p.16]`.
- **Layout**, for the board: `OUTS` Kelvin to `C-REG-OUT`; `R-SET-DAC`'s and
  `C-SET-DAC`'s grounds to `C-REG-OUT`'s ground; a guard ring round `SET` at
  `OUT`'s potential, both sides `[p.14–15]`; the exposed pad soldered to
  `AGND_MOD` copper.
- **Layout, `R-SET-DAC`'s placement on `module-main`** — the mitigation for the
  accepted open-circuit failure (*Its failures*), so it is a rule, not a
  preference. **Keep it away from the standoffs, the connectors and the board
  edges**, which is where a board bends when it is screwed down, plugged and
  unplugged; and **orient its long axis parallel to the board's long edge**, so
  the board's bending runs along the chip and not across its terminations. A
  stress-free chip resistor opens by flex cracking, and the part's own bending
  test goes to only 3 mm `[VIKING p.4]`. Inside the `SET` guard ring above,
  with `C-SET-DAC` beside it.

**Start-up.** `R-SET-DAC` × `C-SET-DAC` is 5.2 ms, and the rail follows `SET`
up: over 4.5 V in 10–12 ms and over the 5.00 V floor in 14–21 ms after the bus,
**with no overshoot** above its final value at any corner of `I_SET`,
`R-SET-DAC` and `C-SET-DAC` (`dac-rail-startup`). That is a few ms slower than
the LM317L it replaced and changes no order that matters:

- **The DAC's SPI pins** cannot sit above `DAC AVDD` at any rise time, because
  `U-LVL-MOD` runs from it (`digital-and-supervision/sim`, `rails-and-sync`,
  re-run on this regulator); `LOGIC_5V` still arrives first.
- **The DAC's power-on reset** holds every channel at zero scale until a valid
  write `[ds DAC8568CIPW.pdf p.38]`; the datasheet gives no ramp-rate limit.
  The instrument's supply comes through `U-ISO` and the load switch, whose start
  alone takes 42 ms or more (`umbilical-load-switch/sim`, `cold-start`), and
  firmware re-writes the reference-enable and clear-code registers periodically
  (`firmware/README.md`), so a word written into a rail still rising is
  rewritten.
- **The breath offset dividers** (`POT-OFFSET`, `TRIM-BREATH-ZERO`) are
  ratiometric on `DAC AVDD` and simply follow it up; the pitch jack stays
  within 100 mV of 0 V through the power-up (`dac-rail-startup`, `ptc-tripped`).

**Its failures.** A shorted `C-SET-DAC` or `R-SET-DAC` puts `SET` at ground and
the rail goes **down** (`dac-rail-short-cset`). **An open `R-SET-DAC` drives it
up**, to the input less the dropout, 10.5–12.3 V, over the DAC's 6 V absolute
maximum (`dac-rail-open-rset`, recorded). It is the one single failure that
does — as an open `R-REG-SET-LO` was for the LM317L — and it is a fixed
thin-film part with nothing to turn.

**ACCEPTED, with no protection circuit — the owner, 2026-10-01: *"Good to
accept them"*** (`dac-rail` at its nominal, and this failure). No clamp is
drawn: a zener cannot be guaranteed between 5.35 V and 6.0 V at the LT3042's
220 mA limit. It is mitigated two ways instead, and each is a rule:

1. **The layout:** `R-SET-DAC` placed away from flex and oriented along the
   board (*How it is wired*, Layout).
2. **The first build:** `DAC AVDD` is measured **before `U-DAC` is fitted**
   (and `U-LVL-MOD`, which runs from the same rail and has an absolute
   maximum `V_CC` of 7 V `[ds SN74AHCT125.pdf, absolute maximum ratings]`), so an open `R-SET-DAC` — the rail reading ~11 V —
   never reaches a DAC (ROADMAP E7). Both are machine-placed, so the first
   board's assembly order leaves them off and they are hand-fitted after the
   reading.

**No special-purpose part.** The owner, 2026-10-01: *"no need for these
specialized parts bifurcation"* — an anti-sulfur resistor here was judged
unnecessary, so `R-SET-DAC` is the ordinary thin-film part above, and the
mitigations are the placement and the first-build check.

### The DAC rail's load

| | `[calc]` | Source |
|---|---|---|
| The DAC and the dividers | the DAC8568's 2.0 mA max; `POT-OFFSET` (10 kΩ to `AGND_MOD`), 0.52 mA; `R-ZERO-TOP` and `TRIM-BREATH-ZERO` (52.2 kΩ), 0.10 mA; `R-PULL-SYNC`, 0.52 mA while `SYNC` is low. **≈ 3.1 mA** | `[ds DAC8568CIPW.pdf p.5]`; the netlists |
| `U-LVL-MOD` | `I_CC` 20 µA max; `SCLK_DAC` and `DIN` high into their 10 kΩ pull-downs, 0.52 mA each at `dac-rail`, **1.04 mA** with both high; switching 3 outputs × 10 pF × 5.2 V × 2 MHz ≈ 0.31 mA. **≈ 1.4 mA** at most, about half that on average | `[ds SN74AHCT125.pdf p.4]` |
| Its inputs | driven from `LOGIC_5V`, 5.0 V against a `VCC` of `dac-rail`: a fraction of a volt under `VCC`, where the input stage barely conducts `[from memory]`. The datasheet bounds it only at 3.4 V, 1.5 mA per input; three inputs at that bound would add **4.5 mA**, the ceiling below. The bench measures it at E7, with the rail | `[ds SN74AHCT125.pdf p.4]` |
| Total load | **≈ 4.5 mA**; 9.0 mA at the `ΔI_CC` ceiling. The LT3042 is rated to 200 mA and needs no minimum load above 1 V out | `[ds ADI-LT3042.pdf p.4 Note 13]` |
| From +12 V | the load, plus its GND current, 3.6 mA max at these loads (3.5 mA at 1 mA, 5 mA at 50 mA), plus the 0.1 mA `SET` current: **≈ 8.2 mA**, the branch `module-own-draw` carries | `[p.3]` |
| Dissipation | (12.4 − 5.23) V × 4.5 mA + 12.4 V × 3.6 mA = **77 mW**; 109 mW at the ceiling. θJA 33–35 °C/W on a four-layer board gives **+3 °C** | `[p.2, p.21]` |
| Dropout | input ≥ 10.9 V at the worst (a tripped fuse, *Fuses* above) against 5.35 V out at most: 5.5 V of headroom, against 300 mV maximum dropout | `[p.3]` |
| Load regulation | inside `V_OS`'s ±2 mV from 1 to 200 mA: the buffer's 1.4 mA moves `DAC AVDD` by well under that, and the spread above already carries it | `[p.3]` |

**The noise it adds to `DAC AVDD`.** The buffer's DC current changes with what
it is sending: `SCLK_DAC` and `DIN` swing 0 to 1.04 mA of pull-down current at
SPI rate, and its edges draw their charge (~52 pC per edge into 10 pF) from
`C-DEC-LVL`, about 0.5 mV on 100 nF, refilled before the next edge. The LT3042's
output impedance at frame rate is milliohms — its load regulation is
hundreds of µV over 200 mA `[ds ADI-LT3042.pdf p.14]` — so the frame-rate part
is microvolts; the LM317L it replaced put it at 0.55 mV. What it reaches:

- **The DAC's outputs** — through its internal reference, whose line
  regulation is under 10 µV/V `[ds DAC8568CIPW.pdf p.4, p.45]`: under 10⁻⁴ of a
  16-bit step even at the old 0.55 mV `[calc]`. Full scale is the reference's,
  not `AVDD`'s. The DAC's own logic sat on this rail already.
- **The ratiometric loads** — `POT-OFFSET` and `TRIM-BREATH-ZERO` take a
  fraction of `DAC AVDD` directly, in breath CV, not pitch: well under 1 mV on
  a 10 V swing.

So the buffer reaches `DAC AVDD` on **its own branch from `C-REG-OUT`**, with
`C-DEC-LVL` at its pin — never daisy-chained through the DAC's `AVDD` pin or
`C-DEC-DAC` — so its edges are not drawn through the copper the DAC sees.

## Grounding — four layers, one star (owner, 2026-09-30)

The owner, 2026-09-30: *"Four layer in the module board is fine."* So
`PCB-MODULE` is **four layers, 1.6 mm**, and the module's grounds meet the
rack's at **one point**, the star at `J-PWR-EURO`'s ground pins (`BUS_GND`) —
this is the figure `dig-gnd-topology`, amended by ADR 0027:

| Ground | Where it is | How it reaches the star |
|---|---|---|
| `PWR_GND` | `U-ISO`'s isolated return: its own copper on **layer 4**, from the etherCON's pin 6 to `U-ISO`'s 0V and the load switch, and no further | `NT-UMB-MOD` joins it to `DIG_GND` **at the etherCON**, between pins 6 and 8 — the mirror of the instrument's `NT-DIG` (ADR 0018) — and it reaches the star only that way |
| `DIG_GND` | a **layer-2 plane** under the etherCON, `U-LVL-MOD`, `U-REG-LOGIC` and the SPI traces, so `SCLK`/`MOSI`/`CS` return directly under themselves | `NT-DIG-MOD`, at the star — the isolated domain's only tie to the rack |
| `AGND_MOD` | a **layer-2 region** under the analog block — the DAC8568, every op-amp, the LT5400, the trimmers and `J-B2B-MOD` — kept apart from the `DIG_GND` plane | `NT-AGND-MOD`, at the star |

Layers 1 and 3 carry parts and signals; the analog rails route on layer 3
over the analog region. The DAC8568 sits at the boundary with its digital
pins toward the plane, and its one `GND` pin on the analog region.

**Why the instrument's return ties at the etherCON (ADR 0027).** Pins 6 and 8
are tied at the instrument (ADR 0018), so the instrument's current comes back
on both. With `NT-UMB-MOD` at the connector, the half on pin 8 steps across to
`PWR_GND` there and goes straight back to `U-ISO`: **no DC current of the
instrument's crosses the `DIG_GND` plane, the star or the ribbon**. What
`NT-DIG-MOD` carries is constant and the module's own — the level shifter's
few mA back to the analog +12 V, and the panel LED's ~4.2 mA (3.8–4.8 mA, `hardware/module/panel-led/sim`) the other way
(`module/panel-led` returns it to `AGND_MOD`) — plus the SPI edges' return.

**Why not the proposal that bridged `AGND_MOD` to the plane under the DAC.**
That was the obvious shape and it is wrong here, twice. The datasheet asks for
the opposite: the DAC's ground *"would be connected directly to an analog
ground plane. This plane would be separate from the ground connection for the
digital components until they were connected at the power-entry point of the
system"* `[ds DAC8568CIPW.pdf p.49]`. And the umbilical makes it worse than
usual: pin 8 (`DIG_GND`) and pin 6 (`PWR_GND`) are tied together at the
instrument (ADR 0018), so they are two parallel conductors carrying the
instrument's return, about half each `[calc: two equal 24 AWG conductors,
2 m]`. With a bridge under the DAC, that half would cross the analog region
and move the jacks' reference with every breath. Since ADR 0027 it does not
reach the plane beyond the etherCON at all.

**The jack board stays two layers.** It carries the jacks and pots and
one ground, `AGND_MOD`, which reaches it only on `J-B2B-MOD`'s five ground
pins; nothing on it needs a second reference, so there is nothing for a
second plane to separate (`PCB-MODULE-JACK`).

**The standoffs are metal** (owner, 2026-09-30), so they could tie the boards'
copper at more points. **Their pads are on `AGND_MOD` on the jack board
and on no net on the main board** — the main board's two low ones, which go to
the panel (`MECH-PANEL-STANDOFF-MOD`, ADR 0024 point 15), included, so the
panel is not a ground path either — a plated ring with clearance from every
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

- **`U-ISO`'s supply.** The RPA20-2412SAW is end-of-life: DigiKey had 20 on
  2026-09-30 (`U-ISO`'s row). **Decided by: the order** — buy spares now. The
  RP20-2412SAW drops into the same holes; moving to it swaps two pad numbers
  and re-checks its electrical deltas (ADR 0027).
- **The case's −12 V rating** against ~0.24 A typical and ~0.39 A clamp-legal
  from this module (`U-ISO` plus `module-own-draw`) `[calc: 0.225 + 0.020;
  0.37 + 0.020]`. **Decided by: the owner's supply**, measured at E6.
- **Where `U-ISO` sits on module-main**: on its rear face, 10.2 mm tall on
  5.6 mm pins, with its filter parts beside it — `config/module.yaml` holds
  the envelopes and the module CAD checks them. **`L-CM-ISO` has no envelope
  there yet**: 21.6 mm over its terminals, 17.78 mm body, 11.43 mm tall, SMD,
  between `L-ISO-IN` and the converter's input pins; and no footprint in
  `hardware/lib` yet (`woody:L_CommonModeChoke_Bourns_PM3700`, four 3.18 mm
  pads on a 21.59 mm cross, from the datasheet). **Decided by: the module
  CAD's placement**, before the module layout.
- **How much common-mode current `U-ISO` makes.** RECOM does not publish it,
  and every copper parasitic in `cm-loop` is an estimate. **Decided by: E6**,
  a current probe on the star tie with the converter loaded.
- **`C-REG-DAC`'s capacitance at 12 V of bias** is from memory: TDK's bias
  curve for CGA5L1X7R1H106K is not banked. **Decided by: banking it** (or a
  bench measurement at E6); the LT3042's 4.7 µF minimum is the bar.

*(The entry bulk — 100 µF on +12 V and 47 µF on −12 V — is 2–5× the
surveyed 10–22 µF, and it is kept: `C-BULK-RAIL` gives the reason. `C2`,
100 µF across the 24 V of `U-ISO`'s input, and `C-ISO-IN` add to the inrush at
rack power-on, and `U-ISO`'s own start-up charges `C-ISO-OUT`; together still a
few percent of a typical case's total.)*
