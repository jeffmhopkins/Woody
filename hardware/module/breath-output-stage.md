# Breath gain and offset stage — schematic

**Status:** Drawn 2026-09-21. Sixth module page, and the last block on the
board.

This stage was drawn as a box labelled "panel knobs" for as long as the module
existed, and in that time it produced findings in **five separate reviews**
while remaining undrawn. That is the pattern: whatever is a block is where the
defects hide.

## What it has to do

**Panel GAIN 0.5× to 4×, panel OFFSET −5 V to +5 V.** The offset range is the
interesting requirement — a breath CV that can rest anywhere in a ±5 V window
drives bipolar modulation inputs and inverted envelopes, not just a VCA.

What arrives from the receiver, with the pedestal nulled at the in-amp's `REF`
(`breath-receive-stage.md`):

| | Sensor | In-amp output |
|---|---|---|
| Rest | 0.200 V | **0.00 V** |
| Hard blow, real playing (~2.8 kPa) | 2.347 V | **−4.69 V** |
| Sensor full scale (6 kPa) | 4.800 V | −10.05 V |

**Real playing only reaches about 2.8 kPa against the sensor's 6 kPa range**
(ADR 0003), so the stage's working input is 0 to about −4.7 V. Reaching 10 V at
the jack from that needs **≈2.13×** — comfortably inside 0.5–4, which is the
point of specifying the range from playing rather than from the sensor.

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
