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

The one refutation is small but it is the kind this project exists to catch:
**9.8 V was never in the document.** Nothing was derived from it, so nothing
downstream moves — but it had been sitting in a table headed "the rest of the
electrical picture" for a day, and a reader sizing the `ON` divider against a
9.8 V worst-case UVLO would have given away a volt of nothing.

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
