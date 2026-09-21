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

`Dir` is this circuit's side of the net — `in`, `out`, `in/out`, `ref` (a
return or reference) or `—` (no connection here, the row is context). `Peer`
is a bare `board/circuit` id when the other end is a circuit in this tree, a
reference designator or part name when it is not, and `—` when there is
nothing on the other end.

| Node | Dir | Peer | Figure | Note |
|---|---|---|---|---|
| in-amp output | in | `module/breath-receive-stage`, `interfaces/breath-sense-link`, `module/breath-response-shaper` | `inamp-full-scale`, `breath-working-point` | The drawing's `from the INA828`, resting at 0 V because the pedestal is nulled at the in-amp's `REF`. `module/breath-response-shaper` is *proposed* to insert here, ahead of `POT-GAIN` |
| `DAC AVDD` | in | `module/power-entry` | `dac-rail` | The top of `POT-OFFSET`, buffered — the positive leg of the offset pair. The drawing below labels this node as the buffered LM317 rail and restates the figure's value in the label; the value belongs to `dac-rail` and not to a net name |
| `MODULE ANALOG +12V`, `MODULE ANALOG −12V` | in | `module/power-entry` | — | Op-amp supplies, and `D-JACK-CLAMP` returns to both rails. `R-OFFNEG`'s fixed leg is on −12 V, chosen over +12 V because that rail carries no LED current |
| `AGND_MOD` | ref | `module/power-entry` | `dig-gnd-topology` | The module analog star, drawn `AGND(module)`. `R-GAIN-FLOOR`, the summer's (+) input and `C-OUT-BREATH` all return here. The module ground plan is unsettled — see the figure |
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
| Hard blow, real playing (~2.8 kPa) | 2.411 V | **−4.64 V** |
| Sensor full scale (6 kPa) | 4.864 V | −9.94 V |

**Real playing only reaches about 2.8 kPa against the sensor's 6 kPa range**
(ADR 0003), so the stage's working input is 0 to about −4.7 V. Reaching 10 V at
the jack from that needs **≈2.16×** — comfortably inside 0.5–4, which is the
point of specifying the range from playing rather than from the sensor.

> **Corrected 2026-09-21** against `sensor-full-scale`. The sensor column moved
> with the pedestal (0.200 → 0.265 V) and the full-scale figure (4.80 → 4.86 V).
> **The in-amp column moved for a second, independent reason**: −4.69 V was
> computed with the in-amp's *raw* 2.18483, and the working point is the
> *effective* 2.1611 that the bias pair leaves — the same gain the −9.94 V in
> the row below already uses. The span is unchanged, so −9.94 V is untouched.
> `[calc]` `(2.411 − 0.265) × 2.1611 = 4.638`; `10 / 4.638 = 2.156`.

## The circuit

```
   from the INA828                    ┌──────────────┐
   0 … −4.7 V ──────[POT-GAIN 50k]────┤ +            │
   (rest at 0)            │           │  ½ OPA2197   ├──┬── buffered
                          │           │  follower    │  │   attenuator
                     [R-GAIN-FLOOR]   └──────────────┘  │   0.125 … 1.000
                        7.15k         └────────────────┘│
                          │                              │
                     AGND(module)                  [R-IN 10k]
                                                         │
   buffered +5.21 V ──[POT-OFFSET 10k]                   │
   (LM317 rail)             │ wiper                      │
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
                                                 ├──[R-FB 40k]── (to −)
                                                 │
                                    [D-JACK-CLAMP BAV99]── ±12 V
                                                 │
                                   [R-OUT-PROT 1k, 1206]
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

| Pot | Wiper | Offset at the jack |
|---|---|---|
| Full CCW | 0 V | **+5.04 V** |
| **Centre** | 2.605 V | **+0.07 V** |
| Full CW | 5.21 V | **−4.89 V** |

`R-OFFNEG` pulls a constant from −12 V; `R-OFF` pushes a variable from the
buffered 5.21 V. **No extra op-amp half, and no negative reference to
generate** — which is what makes ±5 V cost two resistors instead of a part.

**This wiper does *not* need buffering.** Its source impedance varies from 0 at
either end to `R/4` at centre, so the endpoints are exact and the middle is
slightly non-linear in rotation. For an offset knob that is feel, not error.

**Why −12 V is acceptable here and would not be on pitch.** ADR 0006 moved the
*pitch* offset off a rail divider because 50 mV of rail movement is 12.5 cents
of transposition. Here 50 mV moves the jack by `40k/95.3k × 50 mV` = **21 mV,
0.21 % of span** — and the −12 V rail carries no LED current, because the
strips run from +12 V.

## Values

| Ref | Value | Job |
|---|---|---|
| **POT-GAIN** | 50 kΩ, **taper from the bench** | Attenuator, 0.125 → 1.000 |
| **R-GAIN-FLOOR** | 7.15 kΩ 1 % | Sets the 0.5× floor |
| **R-IN** | 10 kΩ 1 % | Summer input |
| **R-FB** | 40.2 kΩ 1 % | Fixed ×4. Same E96 part as `R-MODGAIN` |
| **POT-OFFSET** | 10 kΩ linear | ±5 V, zero at centre |
| **R-OFF** | 21.0 kΩ 1 % | Variable positive leg |
| **R-OFFNEG** | 95.3 kΩ 1 % | Fixed negative leg from −12 V |
| **R-OUT-PROT** | 1 kΩ, 1206 ≥500 mW | Shared spec with the other five outputs |
| **C-OUT-BREATH** | 330 nF film | ~482 Hz, jack side, feedback from the op-amp |

**Two op-amp halves**, which settles a count that has been wrong in the BOM
twice: gain buffer and summer. Ten of twelve halves used across the module,
two spare.

## Headroom, and the combination that clips

Gain and offset are independent, which means they can be set to a combination
the rails cannot deliver: **offset at +5 V and gain at 4× puts a hard blow at
+23 V**, and the OPA2197 stops at about ±11.5 V.

That is the player's business and it is what the gain knob is for — but it is
worth knowing that the clip is a *rail* clip with no soft region, so it will
sound like a wall rather than compression. The honest usable rule: the offset
sets where breath rests, and the gain sets how far it travels from there; their
sum has to fit in ±11.5 V.

## Still open

- **`POT-GAIN`'s taper.** Linear gives a knob that does most of its work in the
  last quarter turn. A log or pseudo-log taper (or a second floor resistor
  across part of the track) is a feel question, and feel is a bench question —
  E10, with a real sensor and someone blowing into it.
- **`POT-OFFSET` detent at centre**, which is now a meaningful position rather
  than an arbitrary one. A centre-detent pot would make "no offset" findable in
  the dark; whether that is worth the part is an E10 call.
- **Commissioning order** is now three steps, not two: `TRIM-BREATH-ZERO` for
  the pedestal, then GAIN for the span, then OFFSET for where it rests. The
  first is internal and set once; the other two are performance controls.

---
