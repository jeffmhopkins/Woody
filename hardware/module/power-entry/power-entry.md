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

| Node | Dir | Peer | Figure | Note |
|---|---|---|---|---|
| `+12V`, `-12V`, `+5V`, `GND` on `J-PWR-EURO` | in | Eurorack bus board | — | 16-pin shrouded keyed IDC. `GND` is the star point |
| `MODULE ANALOG +12V` | out | `module/pitch-stage`, `module/breath-receive-stage`, `module/breath-output-stage`, `module/mod-channels` | — | After `D1`, `FB1`, `C1` |
| `MODULE ANALOG −12V` | out | the same four analog pages | — | After `D3`, `FB3`, `C3` |
| `DAC AVDD` | out | `module/digital-and-supervision` | `dac-rail` | The LM317 output. Selected on the bench, per the figure's floor |
| bus `+5V` after `FB4`/`C4` | out | `module/digital-and-supervision` | — | The level shifter only, and it is the one rail with no diode |
| `+12V` ahead of `D1`/`D2` | out | `module/umbilical-load-switch` | — | The branch is taken **before** the diodes; `U-LOADSW`'s `VCC` and the top of `R-ILIM` hang off it |
| `+12 V analog` | out | `module/panel-led` | — | Feeds `R-LED-PANEL`, and that is the whole of why the indicator cannot say what it was kept to say |
| `PWR_GND` | ref | `module/umbilical-load-switch`, the instrument | `umbilical-current` | The umbilical return, on its own copper to the star |
| `AGND` / `DIG_GND` | ref | `module/breath-receive-stage`, `module/digital-and-supervision` | `dig-gnd-topology` | Where each returns is the disputed part — see the figure |
| `FB1`–`FB4` | — | — | `ferrite-bias-impedance` | One bead per rail; the impedance each actually has under its own DC bias is the figure |

## The circuit

```
  16-pin shrouded keyed IDC (J-PWR-EURO)
       │
  +12V ├───┬──[D1 1N5817]──[FB1]──[C1 47µF]──┬── MODULE ANALOG +12V
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
       │                    │       │   CS8    │         │
       │                    │       │ TIMER GATE├──┬──[R-GATE-SER 10Ω]──┐
       │                    │       │  FB      │   │                    │
       │                    │       └──┬────┬──┘   │             ┌──────┴──┐
       │                    │          │    │  [R-GATE-COMP 1k]  │  N-FET  │ DPAK
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
   +5V ├───[FB4]──[C4 47µF]──────────────────────── 74AHCT125 only
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
> instrument's own supply current. `pitch-stage.md` puts the entire pitch
> error budget at 0.42 cents. **The carefully engineered part of the pitch
> path is one to two orders of magnitude below an effect that appears in no
> document**, and because it tracks breath it will not sound like noise —
> it will sound like an intentional feature that has gone wrong.
>
> Not fixed here. It is a grounding and shield-bonding decision, and the
> shield policy is sixteen words in the whole repo.

`D3` protects −12 V. The bus +5 V pin gets no diode: the only thing on it is a
$0.30 buffer, and a reversed ribbon that kills the buffer and nothing else is
an acceptable outcome (ADR 0004).

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
| `FB1`, `FB3`, `FB4` | the low-current rails | **~580–614 Ω** |
| `FB2` | `umbilical-current` | **~280–310 Ω** |

`FB2` is the one that matters and it has roughly **half** the impedance the
part number advertises, because it is the bead carrying the umbilical's
current. That is not a reason to change the part — it is a reason not to
believe "600 Ω" anywhere in this drawing. Read off the banked drawing rev E,
`datasheets/discrete-and-power/MI1206K601R-10-ferrite-bead.pdf`.

## Grounding

One origin, at the IDC's ground pin. `PWR_GND` — the ~360 mA umbilical return
— runs to it on its own copper and touches nothing else on the way. The analog
return is its own region joining at the star. **`DIG_GND` is *not* given its
own path to the star**, which an earlier revision of ADR 0004 asked for: a
2 MHz SPI return wants the pour directly under its trace, and routing it to a
distant star point is the classic split-plane mistake. `AGND` is not a ground
at all — it is an in-amp input (ADR 0003).

Full reasoning, and the arithmetic for why `PWR_GND` is the one that must be
isolated, is in ADR 0004.

## Still open

*(`L-BUCK-IN` and the umbilical's input LC moved with the load switch — they
are in [`umbilical-load-switch.md`](../umbilical-load-switch/umbilical-load-switch.md).)*

- **No fuse on the analog rails.** The load switch covers only the umbilical
  branch. Mutable, Telex and others fit PTCs on their entry rails; ADR 0005's
  deletion argument was about the *instrument-end* polyfuse and does not reach
  these. Deliberately left open rather than silently omitted.
- **Entry bulk is 4 × 47 µF**, which is 2–5× the surveyed norm of 10–22 µF.
  Harmless except for case-wide inrush at rack power-on, where it adds to
  everything else in the case.
