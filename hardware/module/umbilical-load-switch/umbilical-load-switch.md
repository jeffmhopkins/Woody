# Umbilical load switch — schematic

**Status:** Split out of [`power-entry.md`](../power-entry/power-entry.md)
2026-09-21. It is drawn there, inside the module entry drawing, because that is
one drawing; every word below moved across unchanged.

## Interfaces

Every net that crosses this circuit's boundary. Quantities appear **only** as a
citation into `config/figures.yaml` — this table names nodes, it does not
restate values.

The `Dir` and `Peer` columns are defined once in
[`hardware/README.md`](../../README.md#the-interfaces-table).

| Node | Dir | Peer | Figure | Note |
|---|---|---|---|---|
| `+12V` ahead of `D1`/`D2` | in | `module/power-entry` | — | `U-LOADSW`'s `VCC` and the top of `R-ILIM`. Taken before the entry diodes, which is the point of the split |
| `ON` | in | `module/panel` | — | The panel toggle `SW-POWER`. The LT1641's undervoltage-lockout input; the divider around it is **still not designed** — see below |
| `UMBILICAL +12V` | out | `carrier/power-entry-instrument`, `module/link-supervision` | `umbilical-current` | The FET's source, down the Cat5 umbilical. What the far end needs is what sizes the `FB` divider. `module/link-supervision`'s deleted presence detect gated `OE_MOD` from this node |
| `PWR_GND` | ref | `module/power-entry` | — | `C-TIMER`, `C-GATE`, `R-FB-LO` and the FET source return here, to the star at the IDC |
| `TIMER` / `GATE` | — | `module/panel-led` | `loadswitch-timer` | **Proposed only, nothing is drawn on it.** The indicator's missing "latched" signal would come from here — see [`panel-led.md`](../panel-led/panel-led.md) |

## The load switch — rebuilt 2026-09-21, because it never started

**Three reviewers independently concluded that this circuit as specified
latches off at the end of every start attempt.** They reached it from the
BOM arithmetic, from a sequencing walk-through, and from the datasheet
equation read against fourteen published module schematics. None of them
could see the others' work. What follows replaces the previous section.

### Four things the old section had wrong

**1. The limit is 0.940 A, not 1.0 A.** The LT1641's sense threshold is
**47 mV**, not 50 — **CONFIRMED** `[164112fc p.5]`, was `[web, two reviewers]`.
`R-ILIM` at 50 mΩ gives `47 mV / 50 mΩ = 0.940 A` `[calc]`. The document also
gives the *spread*, which no reviewer had: `V_SENSETRIP` is **39 / 47 / 55 mV**
`[p.2]`, so the limit is really **0.78–1.10 A**. See `R-ILIM` in `bom.csv`.

**2. Foldback was described backwards, and it fights the start.** The old
text said foldback acts "while the FET's drain voltage is high". In a
high-side N-FET the drain is *always* at 12 V — it is the **output** that
is low, and foldback acts during **the entire start ramp**. It regulates
the sense drop to about **12 mV at V_out = 0**, i.e. **240 mA** `[calc]` —
*below* the programmed charging current. **Every start therefore begins in
current limit.** The old page programmed foldback in one paragraph and
asserted "a normal start never enters current limit" in the next.

> **Corrected 2026-09-21, one step further on.** "Foldback acts during the
> entire start ramp" was itself written while `FB` was unconnected, which is the
> only condition under which it is true. With the divider of §5 fitted, foldback
> releases at `V_out` = 3.99 V and the cold start is in current limit for about
> **1 ms**, not for the ramp. The 240 mA floor is still right, and it is still
> what the start has to climb out of. See *What the start actually takes* below.

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
**Both halves of that sentence survive; the conclusion drawn from them does
not** — the start climbs out of the foldback floor in about a millisecond once
`FB` is driven. The 624 mA figure is still the number the 940 mA limit has to
cover, and it does, with the instrument's load arriving above ~7 V where the
limit is already flat.

**4. There was no gate capacitor anywhere.** Not in the drawing, not in
`bom.csv`. The FET sizing, the boot analysis and ADR 0005's 50–100 ms
specification all rest on a "programmed ramp" that **did not exist**. With
the FET's bare C_iss (~1 nF) and ~10 uA of gate current the ramp is
10 kV/s, which demands `2.2 mF x 10 kV/s = 22 A` `[calc]` — twenty-odd
times the limit. **`C-GATE` now exists and is 82 nF** — see below.

### 5. `FB` was not connected, and that is what stops it starting

**Found 2026-09-21. CONFIRMED against the datasheet 2026-09-21** — see the
provenance note below. The four items above were written on the assumption that
foldback tracks the switch *output*. It does not. **It tracks the `FB` pin
(pin 2)** — a dedicated input, which this page did not draw and `bom.csv` had
no resistors for.

The consequence is not subtle. With `FB` tied to nothing, the part holds the
sense-resistor drop at its foldback floor of **12 mV forever**:

```
V_FB = 0 V  →  limit = 12 mV / 50 mΩ = 240 mA,  permanently
```

The output never charges, so the current-limit amplifier never releases, so
the `TIMER` ramp runs continuously — and the **`-1` suffix latches off**. The
instrument never starts, and **no value of `C-TIMER` fixes it**; a bigger timer
capacitor only makes the latch take longer. Three reviewers reached "the
instrument never starts" by three routes and none of them found the mechanism.
This is it.

**ADI describes this exact failure itself**, as the caption story for Figure 9:

> *"The waveform in Figure 9 shows how the output latches off following a
> short-circuit. The drop across the sense resistor is held at 12mV as the
> timer ramps up. Since the output did not rise bringing FB above 0.5V, the
> circuit latches off."*
> `[datasheet 164112fc p.9]`

An unconnected `FB` is indistinguishable, to this part, from a permanently
shorted output.

> **✅ Provenance — resolved 2026-09-21. The PDF is banked.**
> `164112fc.pdf` is at `datasheets/discrete-and-power/LT1641.pdf`
> (12 pages, Linear Technology, `164112fc` footer), recovered from the Internet
> Archive's 2019-02-02 capture of `analog.com` — `analog.com` itself is still
> unreachable, but `web.archive.org` is reachable from this sandbox and was not
> in earlier waves. The demo-board quick-start guide is banked beside it as
> `LT1641-DC1354A-demo-manual.pdf` and independently repeats the DC table.
>
> Every number in this section was `[web, search-index]` until now. **Eight of
> the nine claims are CONFIRMED verbatim; one is REFUTED** (the `VCC` UVLO
> maximum) and one open question is **answered** (`I_GATE` does have min/max).

### The electrical picture, now read off the document

| Parameter | Datasheet | Verdict vs. what this page said |
|---|---|---|
| Pinout | `1 ON  2 FB  3 PWRGD  4 GND  5 TIMER  6 GATE  7 SENSE  8 VCC` `[164112fc p.2, TOP VIEW]` | **CONFIRMED** — matches the KiCad-derived map exactly |
| Foldback input | *"the current folds back as a function of the output voltage, **which is sensed at the FB pin** (Figure 7)"* `[p.8]` | **CONFIRMED** — the whole of §5 above stands |
| Foldback law | 12 mV at `V_FB` = 0, **linear to 47 mV at `V_FB` = 0.5 V, flat above** `[p.5 SENSE pin; p.8; Figure 7 p.9]` | **CONFIRMED** exactly, including the 0.5 V knee |
| Sense threshold | **47 mV**, *"when `V_FB` is 0.5V or higher"* `[p.5]`. Tabulated 39 / **47** / 55 mV at `V_FB` = 1 V; 8 / **12** / 17 mV at `V_FB` = 0 V `[p.2]` | **CONFIRMED**, and the ±17 % spread is new — see `R-ILIM` |
| `I_TIMER` | *"When the current limit circuitry is not active, the TIMER pin is pulled to GND by a **3µA** current source. After the current limit circuit becomes active, an **80µA** pull-up current source is connected … the voltage will rise with a slope equal to **77µA/C_TIMER**"* `[p.8]` | **CONFIRMED verbatim**, mechanism and all. The two-reviewer dispute is settled by the document, not by inference |
| `I_TIMER` bounds | Pull-up `I_TIMERUP` = **–24 / –80 / –132 µA**; pull-down `I_TIMERON` = **1.5 / 3 / 5 µA** `[p.2]` | **NEW.** The ramp current was a typical with no bounds. It is ±60 % |
| `I_GATE` | `I_GATEUP` = **–5 / –10 / –20 µA** `[p.2]`, corroborated `[DC1354A p.1]` | **ANSWERED** — the open question "is there a min/max?" is **yes**, and it is 4:1 |
| Fault threshold | `TIMER` reaches **1.233 V** → `GATE` to ground, `TIMER` discharged at 3 µA `[p.5, p.8]` | **CONFIRMED** |
| `-1` vs `-2` | *"Operation is restored either by **interrupting power** or by **pulsing ON low**"* `[p.9]`; *"If the ON pin is not cycled low, the GATE pin remains latched off"* `[p.5]` | **CONFIRMED verbatim** |
| `ON` pin | Falling `V_ONL` **1.233 V** typ (1.221–1.245), rising `V_ONH` **1.313 V** typ, hysteresis **80 mV** `[p.2]` | **CONFIRMED** |
| `VCC` UVLO | `V_LKO` = 7.5 min / 8.3 typ / **8.8 max** V `[p.2]`, corroborated `[DC1354A p.1]` | **REFUTED.** This page said **9.8 V max**. It is **8.8 V** |
| Minimum `C-TIMER` | *"Use no less than **1.5nF** for the timing capacitor"* `[p.5]` | **NEW** constraint. Not binding here |
| Package | S8, 8-lead plastic SO, θ_JA **110 °C/W**. Order codes `LT1641-1CS8` (0–70 °C) / `LT1641-1IS8` (–40–85 °C), `#PBF` for lead-free `[p.2]` | **CONFIRMED** — `bom.csv`'s `LT1641-1CS8` is a real code. The **I grade exists** and costs nothing to prefer |

*(The one refutation that closed with nothing downstream of it — the `VCC`
UVLO maximum — is recorded in [`notes.md`](notes.md).)*

### Sizing the `FB` divider — `R-FB-HI` and `R-FB-LO`

**The two thresholds on this pin cannot be placed independently.** `V_FB` = 0.5 V
(where the limit reaches the full 47 mV) and `V_FB` = 1.313 V (where `PWRGD`
releases) are set by the *same* divider, so their ratio is fixed by the part:

```
V_OUT(full 47 mV limit)  =  (0.5 / 1.313) x V_OUT(PWRGD)  =  0.381 x V_OUT(PWRGD)
```

"Size it so `V_FB` crosses 0.5 V early in the ramp" and "`PWRGD` should mean the
output is good" are therefore **one decision, not two**. Pulling the foldback
knee earlier pulls `PWRGD` earlier by the same factor. The divider is chosen at
the `PWRGD` end, because that is the end with a hard requirement.

**`PWRGD` must release below the worst-case delivered output.** Eurorack +12 V
at −5 % is 11.4 V; `R-ILIM` at 50 mΩ drops exactly 20 mV at 0.4 A, and the FET
drops about the same *if* its `R_DS(on)` is also ~50 mΩ — **an assumption, since
the FET is still TBD** — so the worst-case output is ~11.36 V `[calc]`. A worse
FET moves this, and the 0.4 V worst-case `PWRGD` margin below is what absorbs
it: at 200 mΩ the output is 11.30 V and the margin is still 0.37 V. Placing the nominal `PWRGD` point at
**10.5 V** leaves ~0.9 V nominal and ~0.4 V worst-case margin, and sits 2.5 V
above the instrument buck's **8 V** input minimum
`[repo, datasheets/discrete-and-power/R-78E5.0-1.0.pdf: R-78E5.0-1.0 is 8–28 V]`.

```
k = V_FB / V_OUT = 1.313 V / 10.5 V = 0.1250   →   R-FB-HI / R-FB-LO = 7.00
```

**Chosen, E96 1 %:  `R-FB-HI` = 35.7 kΩ,  `R-FB-LO` = 5.11 kΩ**  (ratio 6.986)

| | `V_OUT` at which it happens |
|---|---|
| `V_FB` = 0.5 V — full 47 mV limit available | **3.99 V** (3.92–4.06 V worst case) |
| `PWRGD` releases, `V_FB` = 1.313 V rising | **10.49 V** (10.05–10.93 V worst case) |
| `PWRGD` re-asserts, `V_FB` = 1.233 V falling | **9.85 V** |
| `V_FB` at the settled 12.0 V output | **1.503 V** (abs max on `FB` is 60 V) |

Worst case spans 1 % resistors and the datasheet's 1.280–1.345 V `V_FBH` window
`[calc]`. Divider current is **294 µA** at 12 V — 294x the 1 µA max `FB` input
current `[p.2]`, so leakage contributes ≤0.34 % of the ratio, and 3.5 mW is not
worth trimming. The `47 kΩ`-scale alternative would have been 30x the leakage
for 3 mW; this is the cheaper mistake to avoid.

### What the start actually takes — **rewritten, because §5 changed it**

The 62 ms figure this section used to carry was computed by integrating the
foldback law across the *whole* ramp, which was correct **only while `FB` was
unconnected**. With the divider fitted, the limit rises with the output:

```
V_OUT      V_FB       limit
  0 V      0.000 V    240 mA
  1 V      0.125 V    415 mA
  2 V      0.250 V    591 mA
  3 V      0.376 V    766 mA
  3.99 V   0.500 V    940 mA   ← and flat above here
```

**Cold start (the FET ramps).** `C-GATE` programs 122 V/s, so the charging
demand is `2.2 mF x 122 V/s` = 268 mA `[calc]` — just above the 240 mA the
foldback allows at `V_OUT` = 0. The part therefore *does* enter current limit,
and escapes it at `12 mV + 8.77 mV/V x V_OUT = 268 mA x 50 mΩ` → **`V_OUT` =
0.16 V**, about 1.3 ms in `[calc]`. The `TIMER` rises **10 mV** in that time
(17 mV on worst-case silicon) out of 1.233 V, and is then discharged at 3 µA. **The old claim "every start begins in current limit"
survives, but it is now a millisecond, not the whole ramp, and it is harmless.**

**Hot-plug is the sizing case**, and it always was — etherCON invites live
insertion, and on insertion the FET is already fully enhanced, so there is no
ramp and the entire start runs at the foldback limit:

```
phase 1  0 → 3.99 V through the foldback ramp    t = (C/m).ln(I2/I1)
                                                   = (2.2mF/0.1753 A/V).ln(940/240)
                                                   = 17.1 ms
phase 2  3.99 → 12 V at 940 mA less 360 mA load  = 2.2mF x 8.01 V / 580 mA
         (the load cannot start below the buck's 8 V minimum, so charging
          the 3.99–8 V leg is faster than this; 47.5 ms is the safe side)
                                                   = 30.4 ms
                                          total  ≈ 47.5 ms, all of it in current limit
```

**The `TIMER` must exceed 47.5 ms on worst-case silicon.** That is the
requirement; 62 ms was an artefact of the unconnected `FB`.

### The two capacitors — **values set 2026-09-21, no longer blocked**

```
C-TIMER  =  I_TIMER x t / 1.233 V          fault timer
C-GATE   =  I_GATE / (dV/dt)               programmed ramp
```

ADI gives the first as a shorthand: **`C(nF) = 62 . t(ms)`** `[p.8]`, which for
150 ms is 9.30 µF against the 9.37 µF the exact form gives — the same number.
**`C-TIMER` is set to 10 µF**, the nearest stock value above it, because 9.4 µF
is not orderable and the extra 6 % buys the worst-case margin below.

| `TIMER` pull-up | net ramp (less the 3 µA pull-down) | fault time at 10 µF |
|---|---|---|
| –24 µA (min) | 21 µA | **587 ms** |
| –80 µA (typ) | 77 µA | **160 ms** |
| –132 µA (max) | 129 µA | **95.6 ms** |

**95.6 ms against a 47.5 ms hot-plug start is 2.01x** `[calc]`. That is the
margin that matters, and it is the reason for 10 µF rather than 9.4 µF, which
gives 1.89x. The 150 ms "target" was never the spec; **exceeding the start on
worst-case silicon is the spec**, and it is now met with the bound read off the
document rather than assumed away.

**`C-GATE` is set to 82 nF** (E24; 83 nF is not a stock value):

| `I_GATE` | `dV/dt` | ramp to 12 V | charging current into 2.2 mF |
|---|---|---|---|
| –5 µA (min) | 61 V/s | **197 ms** | 134 mA |
| –10 µA (typ) | 122 V/s | **98 ms** | 268 mA |
| –20 µA (max) | 244 V/s | **49 ms** | 537 mA |

> **⚠ ADR 0005's "50–100 ms ramp" is not achievable with this part, and that is
> a spec defect, not a component choice.** `I_GATE` is specified 5–20 µA — a
> **4:1** window — so no single `C-GATE` can hold the ramp inside a 2:1 one. 82 nF
> centres the *typical* at 98 ms, inside ADR 0005; the guaranteed envelope is
> **49–197 ms**. Either ADR 0005 widens its ramp specification to 50–200 ms, or
> the ramp must be programmed by something other than the internal pull-up.
> **Raised against ADR 0005 2026-09-21; not decided here.**

**Both ends of that envelope are safe, and the fast one is worth doing properly.**
At 537 mA the fast corner climbs out of foldback at `V_OUT` = **1.69 V**, not
the 0.16 V of the typical corner — so it spends **10.1 ms** in current limit
rather than 1.3 ms `[calc, t = (C/m)·ln(I₂/I₁) = (2.2mF/0.1753)·ln(536/240)]`,
and on worst-case timer silicon the `TIMER` rises **130 mV** of its 1.233 V.
That is 10.5 % of the fault timer, and it is the largest bite the cold start
takes out of it — worth knowing, and nowhere near a latch. It never approaches the 940 mA limit thereafter:
the instrument's own load cannot appear below **8 V**, which is the
R-78E5.0's input minimum `[repo]`, and by then `V_FB` is 1.00 V and the limit
has been flat at 940 mA for 4 V of output. At 134 mA the slow corner **never
enters current limit at all** — 134 mA is below the 240 mA foldback floor.

And the two consequences that were flagged as conditional now both land: the
**0805 C0G package in `bom.csv` is wrong for 10 µF by three orders of
magnitude**, and at 10 µF this is an electrolytic or a large ceramic where
**leakage is a meaningful fraction of the 3 µA pull-down** — specify a
low-leakage part, or the timer never resets.

### Three parts the datasheet's own application has and this page did not

`[164112fc Figure 5, p.8]` — the typical application carries a gate network this
page drew as a bare capacitor:

```
GATE ──┬──[R-GATE-SER 10Ω]── FET gate
       │
    [R-GATE-COMP 1k]
       │
    [C-GATE 82nF]
       │
     PWR_GND
```

ADI's own words: *"Resistor R6 provides current control loop compensation while
R5 prevents high frequency oscillations in Q1"* `[p.7]`. `R6` is **in series
with the gate capacitor**, not in parallel with anything — this page had `C-GATE`
going straight to ground, which removes the compensation zero from the
current-limit loop. The third is a **0.1 µF bypass between `VCC` and `GND`**
`[p.9, Supply Transient Protection]`, which `C-DECOUPLE` already provides.

**Added to `bom.csv` as `R-GATE-SER` and `R-GATE-COMP`.** Neither is a
judgement call; both are read straight off the manufacturer's reference circuit,
and the loop they compensate is the one that has to hold 940 mA steady for 47 ms
on every hot-plug.

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

**What the datasheet now supplies for it** `[164112fc p.2, p.5]`: the `ON`
comparator trips at **1.233 V** falling / **1.313 V** rising, 80 mV of
hysteresis, input current **−1 µA max**, and the part has a *separate* `VCC`
undervoltage lockout at **7.5 / 8.3 / 8.8 V** that holds `GATE` low regardless
of `ON`. So the divider only has to place the *intended* UV trip somewhere above
8.8 V; below that the chip is off anyway. ADI's own 24 V example uses 49.9 k /
3.4 k for a ~19.6 V trip `[Figure 5, p.8]` — the same two-resistor form, and the
one to copy. **Still not designed**, because the trip point is an ADR 0005
decision, not a datasheet reading: pick it, then the divider is arithmetic.

## `-1`, not `-2`

`-1` latches off; `-2` retries automatically. Auto-retry into a persistent
fault is the oscillating-protection behaviour this design exists to avoid — it
is the same shape as the polyfuse thermal runaway ADR 0014 describes.

The cost of latching is that a fault leaves the instrument dark until you
deliberately cycle the panel toggle, which is why the panel LED matters.

## Still open

- **Damping the input LC.** `L-BUCK-IN` (10–47 µH) in front of a constant-power
  switching load, with 2 m of cable and ~2 mF at the far end, is the textbook
  negative-resistance instability and no damping leg is specified. Put it on
  E11 with the real cable.
