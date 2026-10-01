# Breath gain and offset stage — schematic

**Status:** Drawn 2026-09-21. Sixth module page, and the last block on the
board.

This stage was drawn as a box labelled "panel knobs" for as long as the module
existed, and in that time it produced findings in **five separate reviews**
while remaining undrawn. That is the pattern: whatever is a block is where the
defects hide.

## Interfaces

Every net that crosses this circuit's boundary. Quantities appear **only** as a
citation into `config/figures.yaml` — this table names nodes, it does not
restate values.

The `Dir` and `Peer` columns are defined once in
[`hardware/README.md`](../../README.md#the-interfaces-table).

| Node | Dir | Peer | Figure | Note |
|---|---|---|---|---|
| `BREATH_SHAPED` | in | `module/breath-response-shaper` | `inamp-full-scale`, `breath-working-point` | The in-amp's output after the response shaper, into the top of `POT-GAIN`; equal to it at `POT-RESP`'s centre detent, so everything below that quotes the in-amp column holds there. Resting at 0 V, because the pedestal is nulled at the in-amp's `REF` |
| `DAC AVDD` | in | `module/power-entry` | `dac-rail` | `POT-OFFSET`'s counter-clockwise end, straight from `U-REG-DAC` — no buffer of its own — and the positive leg of the offset pair. The drawing labels the node with the figure's name; the value belongs to `dac-rail` and not to a net name |
| `MODULE ANALOG +12V`, `MODULE ANALOG −12V` | in | `module/power-entry` | — | Op-amp supplies, and `D-JACK-CLAMP` returns to both rails. `R-OFFNEG`'s fixed leg is on −12 V. Both rails carry the instrument's supply current since ADR 0027, so neither is quiet; what that costs at the jack is under *Offset* |
| `AGND_MOD` | ref | `module/power-entry` | `dig-gnd-topology` | The module analog star, drawn `AGND(module)`. `R-GAIN-FLOOR`, the summer's (+) input and `C-OUT-BREATH` all return here. It meets the module's other grounds only at the star — see the figure |
| `BREATH_OUT` | out | `module/panel` | — | The panel jack. Feedback comes from the op-amp output, so `R-OUT-PROT` isolates `C-OUT-BREATH` from the loop. **Not `BREATH_SENSE`**, the umbilical conductor that arrives at the in-amp |
| `POT-GAIN`, `POT-OFFSET` | — | `module/panel` | `panel-width`, `panel-height-budget` | Two of the three panel pots — a panel cutout and a knob envelope, not a net that leaves this circuit. Row and knob geometry belongs to the panel page, not here |

## What it has to do

**Panel GAIN 0.5× to 4×, panel OFFSET −5 V to +5 V.** The offset range is the
interesting requirement — a breath CV that can rest anywhere in a ±5 V window
drives bipolar modulation inputs and inverted envelopes, not just a VCA.

What arrives from the receiver, with the pedestal nulled at the in-amp's `REF`
(`breath-receive-stage.md`):

| | Sensor | In-amp output |
|---|---|---|
| Rest | 0.265 V | **0.00 V** |
| Hard blow at 2.8 kPa, one candidate of `breath-working-point` (open until E2) | 2.411 V | **−4.64 V** |
| Sensor full scale (6 kPa) | 4.864 V | −9.94 V |

**Real playing reaches well under the sensor's 6 kPa range.** How far is
`breath-working-point`, disputed and open until E2's manometer test (ADR 0003);
this page designs to its 2.8 kPa candidate, so the stage's working input is 0 to
about −4.7 V. Reaching 10 V at the jack from that needs **≈2.16×** — inside
0.5–4, which is the point of specifying the range from playing rather than from
the sensor. At the 3–4 kPa candidate the same 10 V needs 2.01–1.51×
`[calc: 10 / (3.0 or 4.0 × 0.7665 × 2.16106)]`, still on the knob.

> **Corrected 2026-09-21** against `sensor-full-scale`. The sensor column moved
> with the pedestal (0.200 → 0.265 V) and the full-scale figure (4.80 → 4.86 V).
> **The in-amp column moved for a second, independent reason**: −4.69 V was
> computed with the in-amp's *raw* 2.18483, and the working point is the
> *effective* 2.1611 that the bias pair leaves — the same gain the −9.94 V in
> the row below already uses. The span is unchanged, so −9.94 V is untouched.
> `[calc]` `(2.411 − 0.265) × 2.1611 = 4.638`; `10 / 4.638 = 2.156`.

## The circuit

*Connectivity is **[`netlist.yaml`](netlist.yaml)**, not this drawing.
The drawing is a representation of it, `tools/check-netlist.py` checks that
the two agree, and where they do not the netlist wins.*

```
   BREATH_SHAPED                      ┌──────────────┐
   0 … −4.7 V ──────[POT-GAIN 50k]────┤ +            │
   (rest at 0)            │           │  ½ OPA2197   ├──┬── buffered
                          │           │  follower    │  │   attenuator
                     [R-GAIN-FLOOR]   └──────────────┘  │   0.125 … 1.000
                        7.15k         └────────────────┘│
                          │                              │
                     AGND(module)                  [R-IN 10k]
                                                         │
   DAC AVDD ──────────[POT-OFFSET 10k]                   │
   (`dac-rail`)             │ wiper                      │
                            │                            │
                       [R-OFF 21.0k]────────────────┬────┤
                                                    │    │
              −12 V ────[R-OFFNEG 95.3k]────────────┘    │
                                                         │
                                            ┌────────────┴───┐
                                            │ −          ┌───┤
                                            │  ½ OPA2197 │   │
                                            │ +          └───┤
                                            └────┬───────────┘
                                          AGND   │
                                                 ├──[R-FB 40.2k]── (to −)
                                                 │
                                    [D-JACK-CLAMP BAV99]── ±12 V
                                                 │
                                   [R-OUT-PROT 1k 500mW]
                                                 │
                                                 ├──[C-OUT-BREATH 330nF film]── AGND
                                                 │
                                           BREATH jack
```

## Gain: a buffered attenuator ahead of a fixed ×4

**Not a rheostat in the feedback path**, which is the obvious way and the wrong
one — it makes the gain and the offset share a resistor, so the knobs fight.
That is the same coupling the `REF` trimmer was added to remove one stage
upstream, and putting it back here would be the third time this project
relocated that defect rather than fixing it.

Instead the pot attenuates *before* the summing node, where it cannot touch the
offset at all:

```
attenuation = 0.125 … 1.000      ×  fixed gain R-FB/R-IN = 4      =  0.5 … 4.0
```

`R-GAIN-FLOOR` (7.15 kΩ under a 50 kΩ track) sets the bottom: `7.15/57.15` =
0.125. Without it the knob reaches zero gain, which is a mute nobody asked for
and an easy way to think the instrument is dead.

**The wiper must be buffered.** It drives `R-IN`, so an unbuffered wiper makes
the attenuation depend on a source impedance that varies with rotation — a gain
error, not just a feel. One op-amp half, and it is the only one this stage adds
beyond the summer.

## Offset: bipolar, from rails that are already there

The summing node takes two more currents — one fixed and negative, one variable
and positive — and their sum crosses zero at mid-rotation:

| Pot | Wiper | Wiper source R | Offset at the jack |
|---|---|---|---|
| Full CCW | `dac-rail` | 0 | **−4.89 V** |
| **Centre** | 2.60 V | **2.5 kΩ** | **+0.61 V** |
| Full CW | 0 V | 0 | **+5.06 V** |
| **True zero** | — | 2.5 kΩ | **0 V at ~19° counter-clockwise of centre** |

**Clockwise is positive.** `POT-OFFSET`'s CW end is on `AGND_MOD` and its CCW
end on `DAC AVDD`: the summer inverts, so the wiper falling toward 0 V moves the
jack up, and the panel's `+` mark at the CW end stop (ADR 0026) is true
`[sim, offset]`. Until 2026-10-01 the ends were the other way round and turning
toward `+` drove the jack to −4.91 V.

> **The centre row is not zero, and the reason is in the third column.**
> `POT-OFFSET`'s wiper is unbuffered, so its own source impedance —
> `R_pot·p·(1−p)`, zero at both ends and **R/4 = 2.5 kΩ at centre** — sits in
> series with `R-OFF`. The endpoints are exact because that term vanishes
> there; the middle does not. `[calc]` `−40.2k × (2.60/(21.0k + 2.5k) −
> 12/95.3k)` = **+0.614 V**, and the zero crossing lands where the wiper is 0.568
> of the way from 0 V to `DAC AVDD`: rotation p = 0.432 from CCW, **19.0°
> counter-clockwise of centre on the R0904N's 280° track** `[ds R0904N-thonk.pdf:
> 280° ± 10°]` — `(0.5 − 0.432) × 280°`. The distance matches `panel.md`'s
> independent derivation; the side is the one the 2026-10-01 swap of the pot's
> ends gives.
>
> This table omitted the source-impedance term and read **+0.07 V at centre**
> until 2026-09-22, and the paragraph below dismissed that impedance as "feel,
> not error". **A centre detent would therefore click ~19° away from actual
> zero**, which is worse than no detent — so `POT-OFFSET` has none (its row).

`R-OFFNEG` pulls a constant from −12 V; `R-OFF` pushes a variable from the
DAC rail, `dac-rail`. **No extra op-amp half, and no negative reference to
generate** — which is what makes ±5 V cost two resistors instead of a part.

**This wiper does *not* need buffering.** Its source impedance varies from 0 at
either end to `R/4` at centre, so the endpoints are exact and the middle is
slightly non-linear in rotation. For an offset knob that is feel, not error.

**Why −12 V is acceptable here and would not be on pitch.** ADR 0006 moved the
*pitch* offset off a rail divider because 50 mV of rail movement is 12.5 cents
of transposition. Here 50 mV moves the jack by `40.2k/95.3k × 50 mV` = **21 mV,
0.21 % of span**. The −12 V rail does carry the instrument's LED current
now: `U-ISO` draws rail to rail (ADR 0027), so both rails move with breath,
by 9.7 mV at the header (ADR 0027's residual table). Through this divider
that is `40.2k/95.3k × 9.7 mV` = **4.1 mV, 0.04 % of span** `[calc]`, and it
follows breath, as this output does.

## Values

| Ref | Value | Job |
|---|---|---|
| **POT-GAIN** | 50 kΩ **linear** | Attenuator, 0.125 → 1.000 — linear in rotation, see *Still open* for why |
| **R-GAIN-FLOOR** | 7.15 kΩ 1 % | Sets the 0.5× floor |
| **R-IN** | 10 kΩ 1 % | Summer input |
| **R-FB** | 40.2 kΩ 1 % | Fixed ×4. **Not** the same value as `R-MODGAIN-IN`/`R-MODGAIN-FB`, which are 10k/30k — this row claimed a shared reel until 2026-09-22 |
| **POT-OFFSET** | 10 kΩ linear | ±5 V, clockwise positive; **zero sits ~19° counter-clockwise of centre**, see above |
| **R-OFF** | 21.0 kΩ 1 % | Variable positive leg |
| **R-OFFNEG** | 95.3 kΩ 1 % | Fixed negative leg from −12 V |
| **R-OUT-PROT** | 1 kΩ, 1206 ≥500 mW | Shared spec with the other five outputs |
| **C-OUT-BREATH** | 330 nF film | ~482 Hz with `R-OUT-PROT`, jack side, feedback from the op-amp |

**Two op-amp halves**, which settles a count that has been wrong in the BOM
twice: gain buffer and summer. Ten of the twelve halves in the six
`U-OPA-PITCH` packages are used, two spare (`U-REF-BUF` B, `U-MOD-C` B); the
response shaper is its own package, `U-RESP`.

## Headroom, and the combination that clips

Gain and offset are independent, which means they can be set to a combination
the rails cannot deliver: **offset at +5 V and gain at 4× puts a hard blow at
+23 V**, and the OPA2197 stops at about ±11.5 V.

That is the player's business and it is what the gain knob is for — but it is
worth knowing that the clip is a *rail* clip with no soft region, so it will
sound like a wall rather than compression. The honest usable rule: the offset
sets where breath rests, and the gain sets how far it travels from there; their
sum has to fit in ±11.5 V.

**The curve knob is in that sum too.** `POT-RESP` sits ahead of `POT-GAIN`, and
the response shaper is not only a shape: at a hard blow it multiplies the
in-amp's output by ×0.49 at its log end and by `shaper-exp-gain` at its exp end
(both with `TRIM-RESP` as commissioned, `breath-response-shaper.md`).
With GAIN left at the noon the commissioning steps below set, turning the curve
knob fully clockwise puts `BREATH_OUT` on the rail inside real playing — from
about four-fifths of a hard blow, `breath-chain-curve-clip` `[sim, chain]`; a
`TRIM-RESP` left at either end of its travel moves that clip, and the figure
gives both ends. At the log end even GAIN's 4× top leaves a hard blow near 9 V
`[calc: 0.49 × 4.64 × 4.02 = 9.1]`. Until the owner
settles how commissioning and the curve knob relate (open, decided by the owner:
`docs/review/2026-10-01-pre-layout-review/VERIFIED-F1.md`, A1-1, which carries
the options with numbers), **re-set GAIN after moving the curve knob.**

## Settled 2026-09-30

- **`POT-GAIN` is linear.** With `R-GAIN-FLOOR` under the track the
  attenuation is `(7.15 k + 50 k·p) / 57.15 k`, linear in rotation `p`, so the
  gain at the jack runs 0.5× → 4× in equal steps. The working gain this stage
  is designed around, ≈2.16× (*What it has to do*), sits at
  `p = (2.156/4 × 57.15 − 7.15)/50` = **0.47, i.e. at noon** `[calc]`. The
  worry this bullet used to carry — "linear does most of its work in the last
  quarter turn" — is backwards for an attenuator with a floor: in decibels the
  first quarter turn moves the gain 8.8 dB (0.5× → 1.38×) and the last 2.1 dB
  (3.13× → 4×). A log track would put the working gain three-quarters of the
  way round. How it *feels* is still worth a minute at E10; nothing about the
  part waits for it.
- **`POT-OFFSET` has no centre detent**, because its zero is not at centre
  (above). A detent would need the wiper buffered first.
- **Commissioning order** is four steps: `TRIM-BREATH-ZERO` for the
  pedestal, `TRIM-RESP` for the curve's exp end (`breath-response-shaper.md`,
  *Commissioning*), then GAIN for the span, then OFFSET for where it rests — and
  `POT-RESP` at its centre click while doing it. The first is internal and
  set once; the others are performance controls. **Moving `POT-RESP` afterwards
  moves the level as well as the curve** (*Headroom*, above): which curve
  setting GAIN should be commissioned at is open, with the owner (A1-1).
