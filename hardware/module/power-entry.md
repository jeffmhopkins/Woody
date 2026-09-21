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
       │   │                                  │   OPA2197 ×6, INA828
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
       │                          │  │ LT1641-1│──GATE──┬─┐
       │                          │  │  CS8    │      [C_GATE]
       │              panel ──────┼──┤ ON      │        │ │   ** WAS MISSING **
       │              toggle      │  │  TIMER  │     ┌──┴─┴──┐
       │                          │  └────┬────┘     │ N-FET │  DPAK
       │                          │  [C-TIMER]       │       │
       │                          │       │          └───┬───┘
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

**`D1` and `D2` are right, and the reason given for them was wrong.** An
earlier revision branched the two +12 V paths *after* a single shared
Schottky, so the instrument's current flowed through the same diode as the
module's analog rail and modulated its forward voltage by **~80 mV** (A7
independently gets 75 mV: 0.305 V at 245 mA → 0.380 V at 612 mA, so the
figure itself is sound).

**The figure that followed it does not survive.** This page used to say the
modulation was worth "about 20 cents of breath-correlated pitch bend".
It implies ~21 % pitch sensitivity to the +12 V rail. Pitch full scale is
set by the DAC's *internal* reference, and AVDD comes from the LM317, so
the real path is 75 mV → LM317 line regulation (0.52 mV/V) → 39 µV on AVDD
→ OPA2197 PSRR (114 dB) → **0.15 µV = 0.00018 cents** `[calc, A7]`. The
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

## The load switch — rebuilt 2026-09-21, because it never started

**Three reviewers independently concluded that this circuit as specified
latches off at the end of every start attempt.** They reached it from the
BOM arithmetic, from a sequencing walk-through, and from the datasheet
equation read against fourteen published module schematics. None of them
could see the others' work. What follows replaces the previous section.

### Four things the old section had wrong

**1. The limit is 0.940 A, not 1.0 A.** The LT1641's sense threshold is
**47 mV**, not 50 `[web, two reviewers]`. `R-ILIM` at 50 mΩ gives
`47 mV / 50 mΩ = 0.940 A` `[calc]`.

**2. Foldback was described backwards, and it fights the start.** The old
text said foldback acts "while the FET's drain voltage is high". In a
high-side N-FET the drain is *always* at 12 V — it is the **output** that
is low, and foldback acts during **the entire start ramp**. It regulates
the sense drop to about **12 mV at V_out = 0**, i.e. **240 mA** `[calc]` —
*below* the programmed charging current. **Every start therefore begins in
current limit.** The old page programmed foldback in one paragraph and
asserted "a normal start never enters current limit" in the next.

**3. The start table had a charging row and no load row.** The instrument
draws ~360 mA while it is starting; the table only counted the current
going into the capacitors.

```
100 ms ramp:  charging 2.2 mF x 120 V/s = 264 mA
              plus instrument load        360 mA
                                        = 624 mA   against a 940 mA limit
```

That is 1.5x on the *unfolded* limit — and still above the 240 mA that
foldback allows at V_out = 0, so the start is current-limited regardless.

**4. There was no gate capacitor anywhere.** Not in the drawing, not in
`bom.csv`. The FET sizing, the boot analysis and ADR 0005's 50–100 ms
specification all rest on a "programmed ramp" that **did not exist**. With
the FET's bare C_iss (~1 nF) and ~10 uA of gate current the ramp is
10 kV/s, which demands `2.2 mF x 10 kV/s = 22 A` `[calc]` — twenty-odd
times the limit.

### What the start actually takes

Integrating the foldback law from V_out = 0 to 12 V, with
`k = 240 mA / 940 mA = 0.255`:

```
t = C.V / (I.(1-k)) . ln(1/k)
  = 2.2 mF x 12 V / (0.940 A x 0.745) x ln(3.92)
  = 51.5 ms                bare
  ~ 62 ms                  with the strip quiescent and both bucks loading
```

**The timer must exceed that, not the 26 ms the old page compared against.**
And the sizing case is not the cold start at all — it is the **hot-plug**,
because etherCON invites live insertion: 2.2 mF at 0.940 A is 28 ms
*before* foldback, and the FET is fully enhanced before the plug is even
inserted, so the ramp cannot help.

### The two capacitors, and why this page will not name their values

```
C-TIMER  =  I_TIMER x t / 1.233 V          fault timer
C-GATE   =  I_GATE / (dV/dt)               programmed ramp
```

**Target: a 150 ms timer** (2.4x the 62 ms loaded start) **and a 100 ms
ramp** (120 V/s, 264 mA of charging).

| If `I_TIMER` is | `C-TIMER` for 150 ms |
|---|---|
| 3 uA | **365 nF** |
| 76 uA | **9.25 uF** |

The two reviewers who worked from datasheet text disagree about which
current applies, and a third bracketed real parts at 2–100 uA. **That
spread is the finding.** The specified **10 nF is wrong under every
reading** — 37x to 925x too small, giving a 0.16–4 ms timer — but the
replacement value cannot be taken from a review. `C-GATE` is likewise
`I_GATE / 120 V/s`, which is ~83 nF at 10 uA.

> **Gate on the datasheet.** `analog.com` and `ti.com` were unreachable
> from this sandbox throughout three review waves. **Read `I_TIMER`,
> `I_GATE` and the sense threshold off the LT1641 datasheet and set both
> capacitors before ordering.** The 0805 C0G package in `bom.csv` is wrong
> for any value in the table above.

### What sizes the FET

With foldback working, peak fault dissipation is **~4 W at V_out ~ 4 V**,
not the 12 W the old page assumed — the feature holds dissipation roughly
flat instead of letting it peak. Ramp energy is `1/2 CV^2` = **0.158 J**
regardless of ramp time; the ramp buys peak power, not total.

**DPAK or SO-8, chosen against the single-pulse SOA curve** — not against
R_DS(on), which is irrelevant at 360 mA. And the criterion is not thermal:
a DPAK is 0.6 C/W at 50 ms, so 12 W is a 7 C rise. **The killer is
Spirito / linear-mode derating at V_DS = 12 V**, which can put a trench
part at 2–3 W. The SOA chart must cover 12 V at 10 and 100 ms.

### Still not designed: the `ON` pin

The panel toggle drives it, and the `ON` pin is the LT1641's **UVLO**
input. There is no divider, no logic level, no supply, no pull-down, no
debounce and no UVLO threshold specified anywhere — four missing passives
on the node that decides whether the instrument powers up at all. Route
the toggle as the bottom leg of an undervoltage divider.

## `-1`, not `-2`

`-1` latches off; `-2` retries automatically. Auto-retry into a persistent
fault is the oscillating-protection behaviour this design exists to avoid — it
is the same shape as the polyfuse thermal runaway ADR 0014 describes.

The cost of latching is that a fault leaves the instrument dark until you
deliberately cycle the panel toggle, which is why the panel LED matters.

## The panel LED — superseded, and its job has changed

**This whole section described a circuit that no longer exists.** It put
the LED and the level shifter's `OE` pins on one node — the presence
comparator's open collector — with `R-OE-PU` 10 kOhm and `R-LED` 820 Ohm
pulled to bus +5 V. The comparator is deleted, `OE` is tied low and
permanently enabled, and neither `R-OE-PU` nor `R-LED` ever had a BOM row.
`bom.csv` carries `R-LED-PANEL` at **2.2 kOhm from +12 V analog** instead,
and that is the circuit.

The bug the old section found was real — pulling a 5 V part's input toward
12 V through an LED resistor — and it is moot now that nothing shares that
node.

### But the LED has lost the job it was kept for

`bom.csv` justifies it: *"with LT1641-1 latching off on a fault, this still
says why the instrument went dark."* **On +12 V analog it cannot.** That
rail is live whenever the rack is, so the LED is lit in every one of the
latching faults above — hot-plug, LED-boot overcurrent, a current-limited
start, a soft short. The one indication the design has for "the load switch
has latched" indicates nothing.

**Cheapest high-value fix in the review**: drive it from the LT1641's
`TIMER` node, or from the gate, so that **lit = running and dark =
latched.** One resistor's worth of rework on a part that is already fitted.

Not applied here: it needs the same datasheet read as `C-TIMER`, because it
depends on what the `TIMER` pin does after a latch.

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
