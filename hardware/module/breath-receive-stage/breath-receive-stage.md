# Breath receive stage — schematic

**Status:** Drawn 2026-09-21. This page did not exist, and its absence was the
single largest source of findings in the cold review.

Five separate findings — the zero's polarity, the missing bias return, the
missing gain resistor, the open-loop zero correction, and half of "nothing mutes
breath" — turned out to be **five symptoms of one absent document**. Two expert
reviewers built two *different* schematics from the same ADR prose and disagreed
on the resistor count; six different in-amp gains were derived, each
arithmetically correct for a different reading. The ADR names the parts and none
of the topology.

This is the topology. Where it disagrees with ADR 0003's prose, this page wins
and the ADR gets corrected.

## Interfaces

Every net and every part that crosses this circuit's boundary. Quantities
appear **only** as a citation into `config/figures.yaml` — this table names
nodes, it does not restate values.

**This circuit is one half of a chain that crosses two boards.** The sensor,
its excitation buffer and `R1`/`R1b` sit on the carrier, at the far end of the
umbilical; the differential pole, the effective gain and the CMRR budget
derived on this page are derived from them. Every row with a `carrier/…` peer
is a number this page uses and does not own — and every part in one is
instrument-side, and replacing one means opening the body (ADR 0009):
expensive rather than impossible, which is still a reason to get it right
first.

*(That paragraph is as it was written earlier on 2026-09-21. Those derivations
are no longer on this page: they moved to
[`../../interfaces/breath-sense-link/`](../../interfaces/breath-sense-link/breath-sense-link.md)
with the instrument-side half they depend on — see the pointer below the `REF`
section. The table below is unchanged and still names this circuit's boundary.)*

The `Dir` and `Peer` columns are defined once in
[`hardware/README.md`](../../README.md#the-interfaces-table).

| Node / part | Dir | Peer | Figure | Note |
|---|---|---|---|---|
| `BREATH_SENSE` | in | `interfaces/breath-sense-link` | `umbilical-pinmap`, `sensor-full-scale` | The sensor's buffered output, arriving on `J-UMBILICAL` (`J-UMB-MOD` in the spi-link netlist) through the instrument-side `R1`. Drives `IN−` through `R3`. **Not `BREATH_OUT`**, the module's jack |
| `AGND_SENSE` | in | `interfaces/breath-sense-link` | `umbilical-pinmap` | The instrument's analog star, arriving through the instrument-side `R1b`. Drives `IN+` through `R2`: on this page it is **a signal leg, not a local ground**, and the twisted pair's other conductor. The drawing labels it `AGND (pin 2)`. **Not `AGND_MOD`** |
| `R1`, `R1b` (`R-SER-BREATH-INST`) | — | `interfaces/breath-sense-link` | — | Both legs' series resistance sets the differential pole against `C_diff`, and their match is what the bias pair's balance is measured against. Neither part is on this board |
| `MPXV4006DP` and its `VS` reference buffer | — | `interfaces/breath-sense-link` | `sensor-full-scale`, `riso-ref-topology`, `cref-out-node`, `opa2197-output-impedance` | Sets the span this page multiplies and the pedestal `TRIM-BREATH-ZERO` nulls. Not this page's circuit — see [`notes.md`](notes.md) |
| in-amp output | out | `module/breath-response-shaper`, `interfaces/breath-sense-link` | `inamp-full-scale` | **Owned here.** Into the response shaper, whose output (`BREATH_SHAPED`, equal to this node at centre detent) feeds the panel GAIN/OFFSET stage, which inverts |
| `DAC AVDD` | in | `module/power-entry` | `dac-rail` | Feeds `TRIM-BREATH-ZERO` and its buffer. Never `VREFOUT`, which is disabled until firmware enables it. The drawing calls this node `dac-rail` |
| `MODULE ANALOG +12V`, `MODULE ANALOG −12V` | in | `module/power-entry` | — | The INA828, both OPA2197 halves, and the BAV99 legs on the input pair and at the jack |
| `AGND_MOD` | ref | `module/power-entry` | `dig-gnd-topology` | The module analog star, drawn `AGND(module)`. Where `R4`, `R5`, both `C_cm` and the output RC return |
| `CLR` | — | — | — | **Reaches no part of this circuit**, which is the whole of what the `CLR` section below settles. It is `module/dac8568`'s |
| `BREATH_OUT` | in | `module/breath-output-stage` | — | The breath summer's output, inside its loop and ahead of `R-OUT-PROT`: what the jack carries. Read by the breath LED's driver (*The breath LED*, below) through a 110 kΩ divider. **Not `BREATH_SENSE`** and not the jack itself |
| `SW-BREATH-BW`, `LED-BREATH` | — | `module/panel` | `panel-toggle-hole`, `panel-height-budget` | Panel-mounted, this circuit's parts, each wired to the main board (`SW-BREATH-BW`'s three solder pads, `J-LED-BREATH`). Their holes and where they sit are `module/panel`'s, *Two parts waiting for the layout* |

## The circuit

*Connectivity is **[`netlist.yaml`](netlist.yaml)**, not this drawing.
The drawing is a representation of it, `tools/check-netlist.py` checks that
the two agree, and where they do not the netlist wins.*

```
  INSTRUMENT (main board)                           |  2 m Cat5  |   MODULE
                                                    |            |
   MPXV4006DP ──┬── ½ OPA2197 ───[R1 1k]──────────── BREATH (pin 1) ──┐
                 │                          ↓ to IN−, via R3            │
   (VS = REF5050 5.000 V)                            (twisted pair)   │
                 │                                                    │
                 └── 0.6× divider ── C-AA-ADC ── MCP3202 CH0          │
                                                                      │
   analog star ──[R1b 1k]──────────────────────── AGND   (pin 2) ──┐ │
   (no power current)                       ↑ to IN+, via R2        │ │
                                                                    │ │
  ──────────────────────────────────────────────────────────────────┼─┼───────
                                                                    │ │
                              [D-CLAMP-BREATH] BAV99 to ±12 V, both legs  ◄──────────┼─┤
                                                                    │ │
                                    ┌───[R2 10k 0.1%]───────────────┘ │
                                    │                                 │
                                    │       ┌───[R3 10k 0.1%]─────────┘
                                    │       │
                                    ├──[C_cm 68pF]── AGND(module)
                                    │       │
                                    ├───────┼──[C_diff 680pF]──┐  fixed: the WIDE corner, ~10 kHz
                                    ├───────┼──[C-DIFF-BW-1K5 3.9nF]─┤  switched by U-BW-SW on BW1: 1.5 kHz and 500 Hz
                                    ├───────┼──[C-DIFF-BW-500 10nF]─┤  switched by U-BW-SW on BW0: 500 Hz only
                                    │       │                  │
                                    │       ├──[C_cm 68pF]── AGND(module)
                                    │       │                  │
                    [R4 1M]─────────┤       ├──────[R5 1M]     │
                         │          │       │           │      │
                    AGND(module)    │       │      AGND(module) │
                                    │       │                  │
                                 ┌──▼───────▼──┐               │
                                 │  IN+     IN− │  INA828       │
                                 │              │               │
                                 │  R_G 42.2k   │◄── G = 2.185  │   raw
                                 │              │               │
                                 │  REF ◄───────┼── ½ OPA2197 ◄─[TRIM-BREATH-ZERO]
                                 │              │   buffered    from U-REG-DAC, dac-rail
                                 └──────┬───────┘   `breath-zero-ref` nulls it
                                        │  Vout = −2.16106·(V_BREATH − V_AGND) + V_REF
                                        │       = 0 V at rest, `inamp-full-scale` at full
                                        │  2.16106 is the EFFECTIVE gain: the raw 2.185
                                        │  times the 1M/(1M+11k) bias divider.
                                        │  Superseded: this line carried −10.05 V, the
                                        │  raw gain, which is not the result beside it.
                                        │
                                  ┌─────▼──────────────────────┐
                                  │  RESPONSE SHAPER (curve)   │
                                  │  POT-RESP, U-RESP: ×1 at   │
                                  │  its click, log ↔ exp      │
                                  │  either side               │
                                  └─────┬──────────────────────┘
                                        │  BREATH_SHAPED
                                  ┌─────▼──────────────────────┐
                                  │  INVERTING gain + offset   │
                                  │  POT-GAIN (buffered        │
                                  │  attenuator) then          │
                                  │  POT-OFFSET summing        │
                                  │  TWO × ½ OPA2197 — one     │
                                  │  half cannot do both       │
                                  │  independently             │
                                  └─────┬──────────────────────┘
                                        │
                                        ├──[R-LEDB-TOP 100k]──┬──[R-LEDB-BOT 10k]── AGND(module)
                                        │   BREATH_OUT        └─► ½ OPA2197 (U-REF-BUF B) and Q-LEDB:
                                        │                         LED-BREATH, 0.505 mA per volt
                                        │
                                   [1k]─┼─[C 10nF]── AGND(module)
                                        │
                                   [D-JACK-CLAMP BAV99]── ±12 V
                                        │
                                   BREATH jack
```

## The bandwidth toggle — 500 Hz / 1.5 kHz / WIDE (#32)

**The owner, 2026-10-04:** *"Let's go ahead and just put the filter to 1.5 khz"*
— to track growl and flutter-tongue — and then, asked whether the filter could
be switchable, *"Panel 3-way toggle"* with the modes *"500 Hz / 1.5 kHz /
wide"*, wide at about 10 kHz and still filtering RF and switching hash ahead of
the in-amp. ADR 0003 and ADR 0004 carry the amendments, with their reasons.

**Only `C_diff` is switched, and the analog pair never leaves this board.**

```
   IN+ ──┬──────────────┬─────────────────┬────────────────────┬── INA828 IN+
         │              │                 │                    │
     [C_cm 68pF]   [C-DIFF-BREATH 680pF]  D1 ┐ U-BW-SW         D3 ┐ U-BW-SW
         │              │                 S1 [C-DIFF-BW-1K5 3.9nF] S3 [C-DIFF-BW-500 10nF]
     AGND(module)       │                 S2 ┘ (SEL1, SEL2 = BW1) S4 ┘ (SEL3, SEL4 = BW0)
         │              │                 D2                   D4
   IN− ──┴──────────────┴─────────────────┴────────────────────┴── INA828 IN−
  [C_cm 68pF] to AGND(module) on this leg too

   +12V ─[R-BW-COM 4.7k]─ SW-BREATH-BW commons (lugs 2+5)
                            lug 4 ─┬─[R-BW-FILT1 100k]─┬─ BW1 → SEL1, SEL2
                                [R-BW-PD1 10k]   [C-BW-FILT1 100nF]
                            lug 1 ─┬─[R-BW-FILT0 100k]─┬─ BW0 → SEL3, SEL4
                                [R-BW-PD0 10k]   [C-BW-FILT0 100nF]
                            (lugs 3 and 6 not wired)
```

| Lever (NKK's position) | Lugs made | BW1 | BW0 | `C_diff` across the pair | Corner `[calc]` |
|---|---|---|---|---|---|
| **Left** (Up) — **500 Hz** | 2-1, 5-4 | on | on | 680 pF + 3.9 nF + 10 nF | 1/(2π × 22 kΩ × 14.61 nF) = **495 Hz** |
| **Centre** (Center) — **1.5 kHz** | 2-3, 5-4 | on | off | 680 pF + 3.9 nF | 1/(2π × 22 kΩ × 4.61 nF) = **1.57 kHz** |
| **Right** (Down) — **WIDE** | 2-3, 5-6 | off | off | 680 pF | 1/(2π × 22 kΩ × 714 pF) = **10.1 kHz** |

(Each sum includes the two `C_cm` in series, 34 pF.) The simulated corners,
with the switch's `R_ON` and capacitance in them, are the sim README's.

**Why the common-mode capacitors had to shrink.** The corner is 2 × 11 kΩ
against `C_diff + C_cm/2`. With `C_cm` at 1.5 nF on each leg — what this page
had — WIDE could not pass 9.6 kHz even with no `C_diff`, and the 1.5 kHz mode
missed the link's 58.5 dB at its own top (about 53.6 dB) `[calc]`, because the
pair's mismatch converts common mode in proportion to frequency. At 68 pF,
still a matched pair, WIDE is the textbook in-amp RFI filter: `C_diff` ten
times `C_cm`, a ~10 kHz differential corner and a ~213 kHz common-mode one
`[calc: 1/(2π × 11 kΩ × 68 pF)]`. The ratio only grows in the other modes.
**`C_cm` and the switch are the same in every mode**, so at any one frequency
the CMRR does not depend on the toggle; what changes is how far the band
reaches. The cost is at high frequency: common-mode energy from ~70 kHz to
1 MHz now reaches the in-amp less filtered (*Still open*, below).

**What the link achieves in each mode**, the requirement held over each mode's
own band at every tolerance corner, is the table in
[`sim/README.md`](sim/README.md); the headline at mains is `breath-link-cmrr`.

**`U-BW-SW` is a TMUX6112** `[ds datasheets/analog/TMUX6112-ti-scds383f.pdf]`,
four normally-open channels, checked against this circuit:

- **Supplies.** It runs on the module's ±12 V (VDD − VSS = 24 V of its
  10–34 V), `GND` on `AGND_MOD`. The pair sits inside ±10 V and the
  `D-CLAMP-BREATH` diodes hold it within a diode of the rails, the switch's
  own analog range.
- **Logic.** `SEL` reads 2 V high, 0.8 V low, and takes up to VDD `[ds p.6]`.
  The toggle's lines come from +12 V through `R-BW-COM` and `R-BW-PD`: 8.2 V
  with one line on, 6.2 V with both `[calc]` — never above VDD, and never
  ahead of it at power-up, because they are made from the switch's own
  supply. 0.8 mA through each closed contact, above the gold contacts' 0.1 mA
  minimum `[ds NKK-SERIES-M-TOGGLE.pdf]`; `R-BW-FILT`/`C-BW-FILT` (10 ms) make
  bounce and anything coupled onto the panel wiring a slow DC level.
- **`R_ON`** (120 Ω typ, 210 Ω max over ±10 V and 85 °C `[ds p.6]`) is in series
  with a switched capacitor: it puts a zero at 1/(2π × 2 × 210 Ω × 3.9 nF) =
  97 kHz `[calc]`, far above the corner it belongs to, and the fixed 680 pF —
  never behind the switch — carries the RF filtering in every mode.
- **Capacitance.** Each channel's pins add 2.4–3.1 pF off and 4.2–6.0 pF on to
  ground `[ds p.7]`. Each switched capacitor has a channel **at both ends**,
  one D pin on each leg, so this is common-mode capacitance and loads the two
  legs alike. Its channel-to-channel match is not in the datasheet: the sim
  takes ±10 % per leg, and a what-if at the typ-to-max spread. **Lay the two
  legs out as mirror images**, `U-BW-SW` beside the INA828 with the S-side
  nets short.
- **Leakage**: 0.02 nA max at 25 °C, 0.14 nA to 85 °C `[ds p.6]`, into 11 kΩ —
  2 µV at the worst `[calc]`, inside what `TRIM-BREATH-ZERO` nulls.
- **Charge injection**, 0.6 pC `[ds p.7]`, onto at least 0.7 nF across the
  pair: under 1 mV for a moment at the in-amp's input, and only when the
  toggle moves.

**`SW-BREATH-BW`** is an NKK M2024, ON-ON-ON on a double-pole base: Down makes
2-3 and 5-6, Center 2-3 and 5-4, Up 2-1 and 5-4 `[ds NKK-SERIES-M-TOGGLE.pdf
p.5, the 3-throw table]`. **It throws left–right, like `SW-POWER`** (owner,
2026-10-04: *"full left being 500 full right being wide is the intuitive
placement because it matches the on off of the power switch"*; ADR 0024 point
18, the module re-layout's). **Mounted as `SW-POWER` is, its D-flat on the
left**, the lever thrown right is NKK's Down and thrown left is NKK's Up — the
same reading `SW-POWER`'s row makes, where Down is its ON, to the right. So,
with the commons (2, 5) jumpered and fed: **lug 1** is made only at Up (lever
left) and is **BW0**; **lug 4** is made at Up and Center and is **BW1**; Down
(lever right) makes only 2-3 and 5-6, which go nowhere, so right is WIDE. A
thermometer code with no logic, and the order the table above reads left to
right. The panel carries no position words, so this wiring is the mapping:
**buzz it on arrival** — lever left, pad 1 to pads 2 and 3; centre, pad 1 to
pad 2 only; right, neither. Same series, bushing and hole as `SW-POWER`, but a
double-pole body: 12.7 mm across against `SW-POWER`'s 7.9, the same 9.4 mm
behind the bushing, two rows of lugs 4.8 mm apart `[ds p.11, the solder-lug
drawings]`; panel-mounted and wired to this board.

## The breath LED (#32)

**The owner, 2026-10-04:** a second panel LED, on the other side of the power
toggle from the power LED, whose brightness follows the breath CV. Driven as a
current from one of the module's two spare op-amp halves, `U-REF-BUF` B:

```
   BREATH_OUT ──[R-LEDB-TOP 100k]──┬──[R-LEDB-BOT 10k]── AGND(module)
   (summer output,                 │
    inside its loop)          ½ OPA2197 (+)        +12V ─[R-LEDB-A 1k]─ J-LED-BREATH 1 ─┐
                              U-REF-BUF B ─[R-LEDB-BASE 1k]─[D-LEDB]─┐            LED-BREATH
                                   (−)◄──────────────────┐            │                  │
                                                         └── Q-LEDB E ┤ B   C ─ J-LED-BREATH 2
                                                         [R-LEDB-SENSE 180R]
                                                              AGND(module)
```

- **Brightness proportional to the jack**: the loop holds `Q-LEDB`'s emitter at
  `BREATH_OUT`/11, so the LED current is `BREATH_OUT`/11/180 Ω = 0.505 mA per
  volt — 5.05 mA at 10 V, about `LED-PANEL`'s 4.1–4.5 mA — whatever the LED's
  own drop or the lead's.
- **Off at rest.** At 0 V and below it is dark: the op-amp's output goes low,
  and `D-LEDB` keeps −12 V off the transistor's base-emitter junction (VEBO
  6 V `[ds NEXPERIA-MMBT3904.pdf]`). The LED follows the jack, so an OFFSET
  that lifts the jack at rest lights it at rest.
- **The cap is the summer's own swing**: 11.9 V gives 6.0 mA, inside both
  catalogues' ratings (15 and 20 mA).
- **No load or error on the CV.** The divider sits on the summer's output,
  inside its feedback loop, where 110 kΩ moves nothing; the jack is behind
  `R-OUT-PROT` either way.
- **Its current returns on its own trace** from `R-LEDB-SENSE` to the star,
  and its anode is fed from +12 V through `R-LEDB-A`, which limits a lead
  shorted to the panel to 12 mA.

Simulated with the output stage, a twin of the stage without the driver
beside it (`../breath-output-stage/sim`, `led`): the driver moves the jack by
under 1 µV anywhere in its unclipped range, against the 153 µV of 1 LSB of
10 V at 16 bits; 5.0 mA at 10 V, 6.0 mA at the clip, dark (under 5 nA) at and
below 0 V, and its own loop settles a fast edge with under 3 % overshoot, at
both ends of `Q-LEDB`'s beta and with either catalogue's LED.

## `REF` carries a trimmer, and the polarity question dissolved twice

*(The showstopper this heading names, the input swap it forced, and the two
separate premises that were then withdrawn from under the swap — [`notes.md`](notes.md).)*

**`REF` is driven from a buffered trimmer** set once at commissioning.
**+0.573 V** nulls a *typical* +0.265 V pedestal — this page owns
`breath-zero-ref` and so states it rather than citing it *(the line was wrong
at +0.579 V until 2026-09-21: the same gain with the 1 MΩ bias divider
omitted, which is the error `inamp-full-scale` already records for itself)* — but the pedestal is a **spec band, not a
number**: 0.152–0.378 V, which needs `REF` anywhere from **0.328 V to
0.817 V** `[calc: 0.152 × 2.16106, 0.378 × 2.16106]`. The band is the datasheet's own `V_off` min/typ/max
`[datasheet MPXV4006DP p.4: "Voff 0.152 0.265 0.378 V"]`, and **its typical is
0.265 V** — see `sensor-full-scale`. **Range the trimmer 0 → +1.0 V** — `R-ZERO-TOP`, 42.2 kΩ above the 10 kΩ track, does it: `dac-rail` × 10/52.2 = 0.996 V at the top, 0.914 V with the track 10 % low `[calc]`, still above the band's 0.817 V. An earlier revision specified
0 → +0.6 V, which covers pedestals only to 0.275 V; a sensor at the top of its
own datasheet band would have been un-nullable, leaving 1.4–5.6 % of span
standing at the jack — the same band as the polarity showstopper this trimmer
was added to fix. The in-amp then
rests at 0 V and reaches −9.94 V at full sensor range — about −4.7 V in real
playing.

**The downstream stage is inverting**, which is the topology that wants a
negative-going input. Now that it is drawn (`breath-output-stage.md`) that is
a buffered attenuator ahead of a fixed ×4 summer, with the offset injected at
the summing node — *not* two pots sharing a virtual ground, which is what an
earlier version of this sentence described and which would have made the knobs
fight.

### Why `REF` is trimmed rather than grounded

**Grounding it makes the panel knobs interact, and an earlier revision of this
page claimed the opposite.** With `REF` at 0 V the sensor's pedestal stays in
the signal, *upstream of the gain pot*, and gets multiplied by it: trim the jack
to zero at unity gain, turn GAIN to 2.4×, and the jack idles around **+0.6 V —
into a VCA**. The Yamaha WX5's manual documents this exact interaction on a
shipping instrument ("Wind Zero may change slightly when Wind Gain is adjusted,
so you may have to repeat").

Nulling the pedestal *ahead* of the gain stage is what makes "gain first, then
offset" (ADR 0006) true in hardware rather than only in intent.

**This does not reopen the split-authority rule.** There is still exactly one
zero authority per representation — what changes is that the analog path's
authority is now split by *job*, the same way pitch's is:

| | Calibration | Performance |
|---|---|---|
| Pitch | `TRIM-OFFSET`, set once | firmware's per-load affine |
| **Breath** | **`TRIM-BREATH-ZERO`, set once** | **the panel OFFSET knob** |
| Digital copy | — | firmware, from its own ADC |

What is *not* reintroduced is the DAC channel: firmware still corrects only the
representation it can measure, which is the finding that closed W12.

**The buffer is not optional.** Source impedance on an in-amp's `REF` pin adds
directly to its internal network and degrades CMRR one-for-one, so a bare
trimmer there would spend the entire 60 dB budget. It costs the last spare
OPA2197 half, and `U-OPA-PITCH` goes to six packages so there is still one.

**`REF` must tie *hard*, or to a buffer — never through a divider.** Source
impedance at an in-amp's `REF` pin adds directly to its internal resistor
network and degrades CMRR one-for-one. It is the same class of mistake as a
single-ended capacitor on one input leg, and it is easy to make because `REF`
looks like an input.

*Component values, the gain derivation, the `R1`/`R1b` argument, the bias
return, the `C_diff`/`C_cm` ratio and the filter's position moved verbatim to
[`../../interfaces/breath-sense-link/`](../../interfaces/breath-sense-link/breath-sense-link.md)
on 2026-09-21. Every one of them is derived from parts fitted on the other
board, and they now sit beside the instrument-side half they depend on,
together with `carrier.md` §2's own account of `R1b` — including the
disagreement between the two, which was moved and flagged rather than settled.
The drawing above stays here: it spans the ADC divider and the output stage as
well as this link, and dividing it would mean redrawing it.*

*(The cold review's findings and the table recording how the drawing closed
them — [`notes.md`](notes.md).)*

## Commissioning

With the body at room temperature and no breath at the mouthpiece:

1. **`TRIM-BREATH-ZERO`**, internal, until the in-amp output reads 0 V. Once,
   at build.
2. **Panel GAIN** for the span the patch wants, with the curve knob at its
   centre click. The knob does more work than this page used to say: real
   playing tops out well under the sensor's 6 kPa range — how far is
   `breath-working-point`, disputed until E2; at its 2.8 kPa candidate a hard
   blow reaches about **−4.7 V** at the in-amp, not −10. The downstream stage
   is **0.5× to 4×** (`breath-output-stage.md`), which puts the working point
   near 2.16× — at noon rather than at an end stop. Moving the curve knob
   afterwards moves the level too (`breath-output-stage.md`, *Headroom*).
3. **Panel OFFSET** for where you want the jack to rest — **±5 V, clockwise
   positive, zero about 19° counter-clockwise of centre** (the wiper is
   unbuffered; `breath-output-stage.md`). Because step 1 nulled the pedestal
   ahead of the gain pot, step 2 no longer disturbs this.

**The zero afterwards is the sensor's, and nothing auto-zeroes it.** Only the
digital copy re-zeroes in firmware (ADR 0003); the analog path is trimmed once,
here. The sensor's datasheet bounds its whole error at **±2.46 % of `V_FSS`
with auto-zero — and only within ±5 °C of the temperature it was zeroed at —
and ±5.0 % without** `[ds MPXV4006DP.pdf p.4, Table 1 and Notes 4–5]`. Through
the commissioned gain, sensor to jack ×4.66 `[calc: 2.16106 × 2.156]`, those
are about **±0.53 V and ±1.07 V at the jack** `[calc: 0.0246 × 4.6 V × 4.66;
0.050 × 4.6 V × 4.66]`. They are total-accuracy bounds, not a drift
specification (the datasheet gives no `TcOffset` figure on its own), but they
are the only bound banked, and the body warms by more than 5 °C. Every
electronic term after the sensor comes to under 3 mV at the jack over 20 K
(pre-layout review A1, 2026-10-01), so the zero budget is the sensor's. An
earlier version of this paragraph said "on the order of 20 mV", from an
unsourced ~0.5 mV/K; nothing supports that figure. **Open, decided by E2:** log
the jack at rest across the 20-minute warm-up, at the commissioned gain, and set
the pass threshold there — a positive drift holds a VCA open at rest, which is
what `TRIM-BREATH-ZERO` exists to prevent. A bench drift beyond the threshold
is answered by a lower GAIN or by re-trimming warm, not by a part.

**Noise at the jack** is the sensor's too: `breath-jack-noise`, simulated
sensor to jack across every stage (`../breath-output-stage/sim/`, `noise`),
which also gives each stage's share. Every electronic term together is under
a tenth of the sensor's, and the largest of them is not this page's in-amp
but `DAC_AVDD`'s own noise, reaching the jack through `TRIM-BREATH-ZERO` and
`POT-OFFSET`. The sensor's term rests on an assumption — no MPXV4006DP sheet
states a noise figure, so the sim takes NXP's AN1646, measured on the
MPX5006 `[ds MPXV4006-AN1646.pdf p.1]` — and **E11's scope of the jack is the
measurement**. No page sets a limit; what decides one is what the breath CV
drives (the sim's README).

**E10 scopes the jack**, not the display. The two representations are calibrated
separately on purpose, so a flat bar on the screen is no longer evidence about
the output.

## What the jack does on a `CLR` — settled

**Nothing, and that is correct.** `CLR` reaches the DAC channels; breath touches
none of them. `REF` is driven by `TRIM-BREATH-ZERO` through a buffer off the
DAC rail — not by a DAC channel — so there is no path by which a `CLR` can
yank the zero out from under the stage. An analog path cannot latch at a level
the player is not producing: it follows the sensor, and the sensor follows the
room.

*(Two statements in this section that were stale until 2026-09-21, and why the
conclusion is unchanged under either correction — [`notes.md`](notes.md).)*

**E10 verifies it** by pulling the umbilical mid-note with the mouthpiece at
rest — and note that the same pull leaves pitch and the four mod jacks holding
their last value indefinitely, which is the accepted cost of deleting the
watchdog (`ROADMAP.md`, E10).

## The downstream stage — settled

The gain/offset stage this page used to carry as three open points is drawn
(`hardware/module/breath-output-stage/breath-output-stage.md`) and meets all
three: its offset comes from the DAC rail (`DAC AVDD`), not `VREFOUT`, so
the jack does not step when firmware enables the DAC's reference; it spends two
op-amp halves, a buffered attenuator ahead of the summer, so GAIN and OFFSET do
not interact; and since 2026-09-30 the response shaper sits between this
page's in-amp and that stage's `POT-GAIN`
(`hardware/module/breath-response-shaper/breath-response-shaper.md`).

*(The instrument-side reference buffer, which is not this page's circuit but
sets the number this page multiplies, settled 2026-09-21 — [`notes.md`](notes.md).)*

## Still open (#32)

Each of these is the owner's to decide (#32); none was settled by moving a
number.

- **WIDE misses the CMRR requirement at its top.** The worst corner holds
  58.5 dB to about 7.4 kHz and reaches about 56 dB at 10 kHz
  (`sim/README.md`, `cmrr-wide`, with the three ways out: WIDE at ~7 kHz, a
  stated band for WIDE's requirement, or a tighter match). The 500 Hz and
  1.5 kHz modes hold it with margin.
- **High-frequency common mode is less filtered.** With `C_cm` at 68 pF the
  common-mode pole is ~213 kHz rather than ~9.6 kHz, so `PWR_GND` noise from
  ~70 kHz to 1 MHz reaches the in-amp's output at up to about −37 dB through
  the TVS diodes' mismatch (`../../interfaces/breath-sense-link/sim`,
  `with-tvs-*`: its "under −60 dB at every frequency to 1 MHz" now fails in
  every mode). The shaper, the output stage and the jack's RC take it down
  again; `interfaces/system/sim` holds the jack end to end.
- **The noise grows with the band** and no page sets a limit
  (`breath-jack-noise`): in WIDE the audio-band noise is above the −80 dB of
  10 V that figure's note offers as an example.
- **The LED row's PWM on −12 V reaches the jack** through `R-BREATH-OFFNEG`
  now that the jack's RC is at 15.9 kHz: 1.14 mV p-p at the worst corner,
  over `power-entry/sim`'s 1 mV bar (`../breath-output-stage/breath-output-stage.md`,
  *Why −12 V is acceptable here*, which proposes an RC on that leg).
- **The switch's channel match is unstated** by its datasheet; the sim
  assumes 20 % between legs. E11's measurement of the pair in WIDE is the check.
- **Where the toggle and the LED sit** is the module re-layout's
  (`../panel/panel.md`, *Two parts waiting for the layout*).
