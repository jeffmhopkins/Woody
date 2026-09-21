# Module power entry — schematic

**Status:** Drawn 2026-09-21. Fourth module page.

Everything from the rack connector to the four rails, plus the load switch that
sends +12 V up the umbilical. This is the least conventional part of the module:
no published Eurorack design passes 360 mA of someone else's load through its
entry diode, so most of the prior art stops being applicable halfway down.

## The circuit

```
  16-pin shrouded keyed IDC (J-PWR-EURO)
       │
  +12V ├───┬──[D1 1N5817]──[FB1]──[C1 47µF]──┬── MODULE ANALOG +12V
       │   │                                  │   OPA2197 ×6, INA828, LM311
       │   │                                  │
       │   │                                  └──[LM317LZ]──┬── DAC AVDD 5.21V
       │   │                                   150R/475R    │
       │   │                                   0.1%      [C 1µF]
       │   │                                                │
       │   └──[D2 1N5817]──[FB2]──[C2 47µF]──┬──────── PWR_GND (star)
       │                                      │
       │                          ┌───────────┴───────────┐
       │                          │  [R-ILIM 50mΩ]        │
       │                          │       │               │
       │                          │  ┌────┴────┐          │
       │                          │  │ LT1641-1│──GATE──┐ │
       │                          │  │  CS8    │        │ │
       │              panel ──────┼──┤ ON      │     ┌──┴─┴──┐
       │              toggle      │  │  TIMER  │     │ N-FET │  DPAK
       │                          │  └────┬────┘     │       │
       │                          │    [C_T]         └───┬───┘
       │                          │       │              │
       │                          └───────┴──────────────┼── PWR_GND
       │                                                 │
       │                                        UMBILICAL +12V ──► instrument
       │
  -12V ├───[D3 1N5817]──[FB3]──[C3 47µF]────────── MODULE ANALOG −12V
       │
   +5V ├───[FB4]──[C4 47µF]──────────────────────── 74AHCT125 only
       │
   GND └───────────────────────────────────────────── STAR POINT
```

## Three diodes, not two, and the branch is before them

**`D1` and `D2` are the whole point.** An earlier revision branched the two
+12 V paths *after* a single shared Schottky, and four reviewers found the
consequence by four different routes: the instrument's current then flows
through the same diode as the module's analog rail and modulates its forward
voltage by ~80 mV. That is about **20 cents of breath-correlated pitch bend**,
needing no ground path at all, visible by inspection of the diagram.

The second diode costs about twenty cents. There is no prior art for this
split because there is no prior art for the situation.

`D3` protects −12 V. The bus +5 V pin gets no diode: the only thing on it is a
$0.30 buffer, and a reversed ribbon that kills the buffer and nothing else is
an acceptable outcome (ADR 0004).

**Beads, not resistors, and the rating is the part that matters.** A ≥1 A bead
is specified because the common 0805 600 Ω part is ~300 mA and **a saturated
bead is a wire**. Package does not set the rating — the *series* does: within
one vendor's 0805 600 Ω line there are 600 mA and 2.3 A versions, and another
"600" part is 60 Ω at 3 A. Read the series, not the footprint.

## The load switch, sized from its own arithmetic

`R-ILIM` sets the limit against the LT1641's 50 mV sense threshold:

```
R_SENSE = 50 mV / 1.0 A = 50 mΩ
at 360 mA typical:  18 mV drop, 6 mW
```

**The instrument's bulk capacitance is ~2.2 mF** — two 100 µF at the buck
inputs plus up to 2 × 1000 µF at the WS2815 feed points. Everything else
follows from that number:

| | 50 ms ramp | 100 ms ramp |
|---|---|---|
| dV/dt | 240 V/s | 120 V/s |
| Charging current | 0.53 A | 0.26 A |
| Peak FET dissipation | 6.3 W | 3.2 W |
| Energy into the FET | 0.16 J | 0.16 J |

**A normal start never enters current limit** — 0.53 A against a 1.0 A limit —
which is the whole job of the programmed ramp. The energy is the same either
way, because it is `½CV²` regardless of how long you take; the ramp buys peak
power, not total.

**The fault case is what sizes the FET.** A hard short holds 12 V across it at
the 1.0 A limit — **12 W** — until the timer expires. The timer must be longer
than a *current-limited* start (1.0 A into 2.2 mF to 12 V is **26 ms**) or the
instrument will not boot on a cold day. So:

- **Timer ≈ 50 ms**, comfortably past 26 ms.
- **The FET must survive 12 W for 50 ms — 0.6 J — as a single pulse.**

**This is why the package changed.** An earlier BOM revision said SOT-23, and
at 0.6 J that is hundreds of degrees of junction rise. **DPAK or SO-8, chosen
against the part's single-pulse SOA curve**, not against its R_DS(on) — at
360 mA even 50 mΩ dissipates 6 mW, so conduction loss is irrelevant here and
SOA is the only specification that matters.

**Program the foldback.** The LT1641 family reduces its current limit while the
FET's drain voltage is high, which holds dissipation roughly flat through a
fault instead of letting it peak at the worst moment. ADI's own material says
that is what the feature is for. It was not mentioned anywhere in this project
until the prior-art review.

> **What this page cannot pin down:** the LT1641's exact pin names, the
> foldback network's topology, and whether `-1` needs a reset cycle on `ON`
> after a latch-off. `analog.com` and `ti.com` were unreachable from this
> sandbox throughout. **Take those off the datasheet before laying out.**

## `-1`, not `-2`

`-1` latches off; `-2` retries automatically. Auto-retry into a persistent
fault is the oscillating-protection behaviour this design exists to avoid — it
is the same shape as the polyfuse thermal runaway ADR 0014 describes.

The cost of latching is that a fault leaves the instrument dark until you
deliberately cycle the panel toggle, which is why the panel LED matters.

## The panel LED sits on the buffer's rail, not on +12 V

**Drawing this found a bug.** The LED and the level shifter's `OE` pins share
one node — the presence comparator's open collector — and the BOM had the LED
pulled up to **+12 V** while `OE` is an input on a **5 V** part. With the
comparator off, that node would have been dragged toward 12 V through the LED
resistor and into the 74AHCT125's input clamp.

Both loads now pull up to the **74AHCT125's own bus +5 V**:

```
  bus +5V ──┬──[R-OE-PU 10k]────────┬── OE ×4 (active low)
            │                       │
            └──[R-LED 820R]──▷|─────┘
                            LED      │
                                     └── LM311 collector (emitter at GND)
```

`(5.21 − 2.0) / 4 mA ≈ 800 Ω → 820 Ω`, and on the 5 V rail it is ~3.8 mA.

Pulling to the buffer's own rail is also the fail-safe arrangement: if bus
+5 V dies, the buffer is unpowered and its outputs are off anyway, and the LED
goes out — which is the correct indication. The **comparator and the watchdog
stay on the LM317's 5.21 V** so that a bus rail failure cannot take the
supervision with it.

**The LM311 itself runs on ±12 V**, not on 5.21 V — it has to resolve a signal
near 0 V, and a comparator on a single positive supply cannot, which is
precisely and only why the LM393 was rejected. Only its **pull-up** sits on a
5 V rail, via the separate emitter pin that is the LM311's whole reason for
being here.

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

- **Damping the input LC.** `L-BUCK-IN` (10–47 µH) in front of a constant-power
  switching load, with 2 m of cable and ~2 mF at the far end, is the textbook
  negative-resistance instability and no damping leg is specified. Put it on
  E11 with the real cable.
- **No fuse on the analog rails.** The load switch covers only the umbilical
  branch. Mutable, Telex and others fit PTCs on their entry rails; ADR 0005's
  deletion argument was about the *instrument-end* polyfuse and does not reach
  these. Deliberately left open rather than silently omitted.
- **Entry bulk is 4 × 47 µF**, which is 2–5× the surveyed norm of 10–22 µF.
  Harmless except for case-wide inrush at rack power-on, where it adds to
  everything else in the case.
