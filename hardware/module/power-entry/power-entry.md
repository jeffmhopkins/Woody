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
| `DAC AVDD` | out | `module/dac8568`, `module/breath-receive-stage`, `module/breath-output-stage`, `module/digital-and-supervision` | `dac-rail` | The LM317 output. Selected on the bench, per the figure's floor. Also the supply of the 74AHCT125 (`U-LVL-MOD`) that drives the DAC's SPI pins, so they can never sit above it — see *The DAC rail's load* |
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
       │                                               ├──[U-REG-DAC LM317LZ]── DAC AVDD
       │                                               └──[U-REG-LOGIC]── LOGIC_5V, the SPI receiver only
       │
       ├──[PTC-ISO]──[D2 1N5817]──[FB2]──[L-ISO-IN 22µH]──┬── ISO_VIN_POS
       │                                                   │
       │                   [C2 100µF] and [C-ISO-IN 4.7µF] across the 24 V
       │                                                   │
       │                                    ┌──────────────┴─────────┐
       │                                    │ Vin               +Vo ├──┬── ISO_POS12 ──► U-LOADSW
       │                                    │ [U-ISO RPA20-2412SAW]   │ [C-ISO-OUT 100µF]  (umbilical-load-switch)
       │                                    │ GND                0V ├──┴── PWR_GND ──► umbilical pin 6
       │                                    └──────────────┬─────────┘           │
       │                                                   │               [NT-UMB-MOD] at the etherCON
       │                                    [C-ISO-Y 1nF], ISO_VIN_POS to PWR_GND │
       │                                                   │               DIG_GND ──► umbilical pin 8
       │                                               ISO_VIN_NEG                │
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
point 3); the header's keyed shroud prevents it at this end only. **Open, the
owner's:** whether to wire fewer of the ground pins so that a reversed cable
lands the module's ground on CV rather than on the rack's supplies
(pre-layout review A3-2).

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
| Input voltage | 24.0 V nominal across the rails, 22.8 V at −5 % on both; less `PTC-ISO` (≤ 0.40 Ω × 0.22 A = 0.09 V), `D2` and `D4` (~0.23 V each at 0.22 A) and the bead and inductor → **~23.4 V typical, ≥ 22.2 V** | `[ds BOURNS-MF-MSMF.pdf p.1]`, `D-REVPOL`'s row |
| Against its range | 9–36 V; under-voltage lockout on at 8–9 V, off at 7–8 V: **13 V of margin** at the bottom | `[ds PD-2]` |
| Typical play | `umbilical-current` × 12 V ≈ **4.3 W** out, 0.36 A of 1.67 A (~21 %); **~82 %** there (~81 % off the efficiency curve, ~0.95 W off the dissipation curve) → 5.26 W in → **~0.22 A on each of +12 V and −12 V** | `[ds PD-3]`, the RPA20-2412SAW's own curves at 24 V in |
| Clamp-legal worst (ADR 0005's table) | ~6.95 W out (0.58 A), ~1.25 W lost → **~0.37 A per rail** at 22.2 V | `[ds PD-3]` |
| Overload held just under the load switch's minimum trip, 0.78 A | 9.4 W, ~1.5 W lost → **~0.49 A per rail** | `R-ILIM`'s row; `[ds PD-3]` |
| Hot-plug into a running module | `Q-INRUSH` holds the instrument's inrush, so `U-ISO` peaks at `hotplug-iso-ocp`, 0.49–0.54 A out → **~0.36 A per rail** `[calc: 0.54 × 12 / 0.82 / 22.2]` | `hotplug-iso-ocp`; `[ds PD-3]` |
| An early replug, the load switch at its 1.10 A worst-case limit | 13.2 W, ~1.85 W lost, for tens of ms → **~0.68 A per rail** — the only case that reaches the limit (*Protection*, below) | `umbilical-load-switch.md`; `[ds PD-3]` |
| Toggle off | quiescent input **20 / 55 mA** typ/max | `[ds PD-2]` |
| Its limit against the load switch's | over-current protection at **110–160 %** of 1.67 A, hiccup: the minimum, 1.84 A, is above the LT1641's 1.10 A worst-case trip, so the LT1641 decides every start and fault **except a replug inside `Q-INRUSH`'s window**, where the carrier's `replug-early` sim reaches `U-ISO`'s threshold (`hotplug-iso-ocp`) — see *Protection* | `[ds PD-5]` |
| Output | 12 V: accuracy ± 2.0 % max, line ± 0.2 % max, load ± 0.1 %, 0.02 %/K → **~± 3.1 %** over 40 K; 50 mV p-p ripple; the load switch's `ON` and `PWRGD` thresholds sit below its minimum with more margin than they had on the bus | `[ds PD-2, PD-5]`; the `hot-plug` sim holds `VCC` above `ON`'s turn-off at every corner |
| RECOM's input fuse | *"Recommended fuse: 3A slow blow type"*, where *"input over-current protection is also required"* — `PTC-ISO` is it, sized for this branch | `[ds PD-5 Note 5]` |
| Loss in the module | ~0.95 W in `U-ISO`, ~0.1 W in `D2`/`D4`; 12.5 K/W on a board in still air, so **~+12 °C** on its case; over-temperature protection at 110 °C | `[ds PD-5, PD-6]` |

**The rack's −12 V carries the instrument now.** At typical play the module
draws ~0.26 A from +12 V and ~0.24 A from −12 V (its own `module-own-draw`,
from *Fuses on the rails* below, plus `U-ISO`'s ~0.22 A on each) `[calc]`,
where it drew ~0.40 A and ~0.04 A. Check the case's −12 V
rating: many Eurorack supplies give −12 V less than +12 V.

**The input filter.** `U-ISO` switches at 550 kHz `[ds PD-2]`; RECOM does
not publish its reflected ripple current. Its own filter, for EN55032 Class A,
is a fuse, a 1 µH choke and 47 µF/50 V electrolytic `[ds PD-7]` — no
common-mode choke. `L-ISO-IN` (22 µH) with `C2` (100 µF 50 V electrolytic)
and `C-ISO-IN` (4.7 µF) is that filter with more of both: at 550 kHz the
inductor is 76 Ω against under 0.17 Ω of capacitor (`C-ISO-IN`'s 0.34 Ω at
100 kHz, falling above it, in parallel with `C2`'s 0.34 Ω impedance
`[ds NICHICON-UCM-SERIES-UCM1E101MCL1GS.pdf p.3]`), so **under 0.25 %** of
whatever it reflects reaches the rack `[calc]`. It is damped by `C2`'s ESR:
`f₀` = 1/(2π√(22 µH × 104.7 µF)) = 3.3 kHz, `Z₀` = √(L/C) = 0.46 Ω, against
the converter's negative input resistance `V²/P` = 23.4² / 5.26 =
**−104 Ω** — over 200× the
filter's characteristic impedance, the same shape and margin as the
instrument's own input LC `[calc]`. **`C2` must stay an electrolytic.**

**The common mode.** The converter's switching drives current through its
isolation capacitance, 1100 pF typ `[ds PD-5]`. `C-ISO-Y` (1 nF,
`ISO_VIN_POS` to `PWR_GND`, beside the converter; RECOM's filter has none
`[PD-7]`) gives it a
way home there, instead of round `DIG_GND`, the star and the ribbon. At breath
frequencies the barrier carries nothing measurable: the `gnd-isolated` sim puts
under 0.3 nA in the tie.

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
only, the LM317 branch, ~12.4 mA (*The DAC rail's load*, below), and
`U-REG-LOGIC`'s ~5.1 mA. That is
**~37 mA on +12 V and ~20 mA on −12 V** with the jacks open — the figure
`module-own-draw` — and on +12 V
**~97 mA** with all six jacks shorted at full scale through their 1 kΩ
`R-OUT-PROT` (6 × 10 mA).

| Part | Hold / trip at 23 °C | Hold at 50 / 60 °C | Must hold | Resistance → drop at the typical load | Voltage |
|---|---|---|---|---|---|
| `PTC-POS12`, `PTC-NEG12`: MF-MSMF020/60-2 | 0.20 / 0.40 A | **0.15 / 0.13 A** | 97 mA worst (+12 V) | 0.40 Ω min → **15 mV** at `module-own-draw`; 6.0 Ω an hour after a trip (R1max) → **≤ 0.27 V** | 60 V: a short between the two analog rails puts 24 V across the pair |
| `PTC-ISO`: MF-MSMF075/33X-2 | 0.75 / 1.5 A | **0.56 / 0.49 A** | 0.37 A clamp-legal worst; 0.49 A overload held under the load switch's trip (it holds at 50 °C and may trip at 60 °C — a fault state either way); ~0.36 A on a hot-plug, and 0.68 A on an early replug for tens of ms, below its trip current | 0.11–0.40 Ω → **≤ 0.09 V** at 0.22 A | 33 V: a shorted `U-ISO` input puts all 24 V across it |

`[ds p.1, p.9]`. The previous page's "~0.1 V" was from memory; the datasheet
says 18 mV on a fitted part and 0.27 V at its worst. **At that worst the
rails still work**: +12 V analog ≥ 11.4 − 0.27 − `D1` − `FB1` ≈ 10.9 V
(10.5 V with all six jacks shorted, 0.58 V across the fuse), above the
breath output's 10 V swing and the LM317's and the ADP7118's dropout. **The
load switch no longer sees any of it**: its `ON` divider is on `U-ISO`'s
regulated output, and `U-ISO`'s input has 13 V of margin. The `as-netlisted`
power-on sims run with the fuses at their fitted resistance; TI's LM317L
model will not converge with 6.0 Ω in series, so the post-trip case is the
arithmetic above.

## The logic 5 V — `U-REG-LOGIC`

The owner, 2026-09-30: *"Create the 5v locally"*, and *"We keep the standard
header, we just don't use the 5 volt. This keeps commonality of all the
Eurorack cable connectors."* So `J-PWR-EURO` stays the 16-pin A-100 header
(ADR 0023 point 3), its +5 V pins are no-connects, and the 5 V loads on the
module's SPI receiver `U-RX-MOD` (74AHCT14) runs from `LOGIC_5V`, made here.
**`DAC AVDD` is not on it**: the DAC keeps its own LM317 rail, `dac-rail`, and
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
| `FB1`, `FB3` | the analog rails, tens of mA | **~580–614 Ω** |
| `FB2`, `FB4` | `U-ISO`'s input, ~0.22 A typical (~0.37 A clamp-legal) | **~440–480 Ω** (~310 Ω) |

`FB2` and `FB4` are the ones that matter, and they lose a quarter to a half of
the impedance the part number advertises, because they carry the instrument's
supply. *(Until ADR 0027 `FB2` carried all of `umbilical-current` and read
about half the nameplate.)* That is not a reason to change the part — it is a reason not to
believe "600 Ω" anywhere in this drawing. Read off the banked drawing rev E,
`datasheets/discrete-and-power/MI1206K601R-10-ferrite-bead.pdf`.

## The DAC rail's load — `U-REG-DAC`

`U-REG-DAC` is TI's LM317L in TO-92 (`LM317LZ`), set to `dac-rail` by
`R-REG-SET-HI` (150 Ω, `OUT` to `ADJ`) and `R-REG-SET-LO` (475 Ω, `ADJ` to
ground, the one E7 selects). Since 2026-10-01 it also supplies `U-LVL-MOD`,
the 74AHCT125 that drives the DAC's `SYNC`, `SCLK` and `DIN`
([`digital-and-supervision.md`](../digital-and-supervision/digital-and-supervision.md),
*The buffer's supply*).

| | `[calc]` | Source |
|---|---|---|
| The DAC and the dividers | the DAC8568's 2.0 mA max; the set divider, 5.21 V / 625 Ω = 8.3 mA; `POT-OFFSET` (10 kΩ to `AGND_MOD`), 0.52 mA; `R-ZERO-TOP` and `TRIM-BREATH-ZERO` (52.2 kΩ), 0.10 mA. `R-PULL-SYNC` draws 0.52 mA while `SYNC` is low, as it always did. **≈ 11.0 mA** | `[ds DAC8568CIPW.pdf p.5]`; the netlists |
| `U-LVL-MOD` | `I_CC` 20 µA max; `SCLK_DAC` and `DIN` high into their 10 kΩ pull-downs, 5.21 / 10k = 0.52 mA each, **1.04 mA** with both high; switching 3 outputs × 10 pF × 5.21 V × 2 MHz ≈ 0.31 mA. **≈ 1.4 mA** at most, about half that on average | `[ds SN74AHCT125.pdf p.4]` |
| Its inputs | driven from `LOGIC_5V`, 5.0 V against a `VCC` of 5.21 V: a fraction of a volt under `VCC`, where the input stage barely conducts `[from memory]`. The datasheet bounds it only at 3.4 V, 1.5 mA per input; three inputs at that bound would add **4.5 mA**, the ceiling below. The bench measures it at E7, with the rail | `[ds SN74AHCT125.pdf p.4]` |
| Total | **≈ 12.4 mA**; 16.9 mA at the `ΔI_CC` ceiling. The LM317L is rated to 100 mA and needs 2.5 mA at most to regulate, which the set divider alone draws | `[ds LM317LZ.pdf p.4, p.5]` |
| Dissipation | (12.4 − 5.21) V × 12.4 mA = **89 mW**; 122 mW at the ceiling. θJA 139.5 °C/W in TO-92 (LP) gives **+12 °C**, +17 °C at the ceiling (it was 79 mW, +11 °C, without the buffer) | `[ds LM317LZ.pdf p.4]` |
| Dropout | input ≥ 10.9 V at the worst (a tripped fuse, *Fuses* above) against 5.21 V out: 5.7 V, over the 2.5 V minimum differential at any of these currents | `[ds LM317LZ.pdf p.4]` |
| Load regulation | 5 mV/V typ at 25 °C and 10 mV/V typ over temperature, at `VO` ≥ 5 V, for 2.5–100 mA and 5–35 V in together (TI gives no maximum): 26 / 52 mV over 97.5 mA, so at most **0.27 / 0.53 mV/mA**. The buffer's 1.4 mA moves `dac-rail` by 0.37 / 0.75 mV — set at E7 with the buffer fitted, so it is inside the selection | `[ds LM317LZ.pdf p.5]` |

**The noise it adds to `DAC AVDD`.** The buffer's DC current changes with what
it is sending: `SCLK_DAC` and `DIN` swing 0 to 1.04 mA of pull-down current at
SPI rate, and its edges draw their charge (~52 pC per edge into 10 pF) from
`C-DEC-LVL`, about 0.5 mV on 100 nF, refilled before the next edge. Through the
LM317L's output resistance the frame-rate part is at most **0.55 mV**. What it
reaches:

- **The DAC's outputs** — through its internal reference, whose line
  regulation is under 10 µV/V `[ds DAC8568CIPW.pdf p.4, p.45]`: 0.55 mV ×
  10 µV/V = **5.5 nV**, under 10⁻⁴ of a 16-bit step `[calc]`. Full scale is
  the reference's, not `AVDD`'s. The DAC's own logic sat on this rail already.
- **The ratiometric loads** — `POT-OFFSET` and `TRIM-BREATH-ZERO` take a
  fraction of `DAC AVDD` directly, so 0.55 mV is 105 ppm of their setting, in
  breath CV, not pitch, at most ~1 mV on a 10 V swing.

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
few mA back to the analog +12 V, and the panel LED's 4.5 mA the other way
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

- **`U-ISO`'s supply.** The RPA20-2412SAW is end-of-life: DigiKey had 20 on
  2026-09-30 (`U-ISO`'s row). **Decided by: the order** — buy spares now. The
  RP20-2412SAW drops into the same holes; moving to it swaps two pad numbers
  and re-checks its electrical deltas (ADR 0027).
- **The case's −12 V rating** against ~0.24 A typical and ~0.39 A clamp-legal
  from this module (`U-ISO` plus `module-own-draw`) `[calc: 0.225 + 0.020;
  0.37 + 0.020]`. **Decided by: the owner's supply**, measured at E6.
- **Where `U-ISO` sits on module-main**: on its rear face, 10.2 mm tall on
  5.6 mm pins, with its filter parts beside it — `config/module.yaml` holds
  the envelopes and the module CAD checks them.

*(The entry bulk — 100 µF on +12 V and 47 µF on −12 V — is 2–5× the
surveyed 10–22 µF, and it is kept: `C-BULK-RAIL` gives the reason. `C2`,
100 µF across the 24 V of `U-ISO`'s input, and `C-ISO-IN` add to the inrush at
rack power-on, and `U-ISO`'s own start-up charges `C-ISO-OUT`; together still a
few percent of a typical case's total.)*
