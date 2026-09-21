# A7 — Module power entry: cold hardware review

**Reviewer:** A7, cold. **Date:** 2026-09-21.
**Scope reviewed:** `hardware/module/power-entry.md`, `hardware/bom.csv`,
`docs/decisions/0005-power-architecture.md`, `docs/decisions/0004-cv-interface-module.md`,
`hardware/controller/carrier.md` §1, and the four other `hardware/module/*.md` pages for
rail loading.

**Cold-review discipline:** I did not open `docs/review/**` or `docs/research/**`.
Everything below was re-derived from the schematic pages, the BOM and arithmetic.

**Evidence marking**
- `[repo] <file>` — read in this repository.
- `[calc]` — my arithmetic, shown inline.
- `[web] <url>` — fetched or searched this session.
- `[prior-art] <path>` — an upstream open-source design already present in the
  session scratchpad (`/tmp/claude-0/.../scratchpad/repos/...`), inspected directly.
- `[from memory]` — I could not reach the datasheet. **Check before ordering.**

**Network:** `doepfer.de`, `analog.com`, `ti.com`, `mouser.com`, `digikey.com` and
`en.wikipedia.org` were all blocked by the egress proxy this session (403 CONNECT
tunnel / `EGRESS_BLOCKED`). One web *search* returned usable LT1641 text; the PDF
itself could not be opened. Pinout was instead confirmed against a real open-source
Eurorack netlist (below), which is better evidence than a forum post.

---

## Summary of findings, ranked

| # | Node / ref | Finding | Rank | Confidence |
|---|---|---|---|---|
| 1 | `C-TIMER-LOADSW` | 10 nF gives a **~1 ms** fault timer, not 50 ms — wrong by 40–400× | **Showstopper** | High |
| 2 | `U-LOADSW` gate | **No gate capacitor exists** in the BOM or the schematic. Without it there is no programmed ramp at all | **Showstopper** | High |
| 3 | `U-LOADSW` / `R-ILIM` | Start current is **0.89 A against a 0.9 A worst-case limit** once load current is counted — 1 % margin | **Showstopper** | High |
| 4 | `U-LOADSW` FB pin | Foldback, as instructed, stretches a current-limited start from 26 ms to **~49 ms** against a 50 ms timer | **Showstopper** | Medium |
| 5 | `PWR_GND` / `J-PWR-EURO` ground pins | The 367 mA umbilical-current *swing* returns through the ribbon's ground conductors and lands on the CV jacks as **~6 mV ≈ 7 cents** of breath-correlated pitch bend. ~50 000× larger than the effect `D2` was added to fix | **Showstopper** | Medium-High |
| 6 | `U-LOADSW` `ON` pin | The `ON` node is unbuildable as drawn: no divider, no logic levels, no supply, no debounce, no UVLO | **High** | High |
| 7 | `J-PWR-EURO` | A reversed **16-pin** ribbon shorts rack **+12 V to +5 V to bus CV** through the module's ground pour. The page's "kills the buffer and nothing else" is wrong for 16-pin geometry | **High** | Medium-High |
| 8 | `J-UMBILICAL` | Hot-plugging the umbilical with the switch already on consumes **~25 ms of the 50 ms timer** and puts full fault dissipation on the FET during a normal user action. No operating procedure is written down | **High** | High |
| 9 | FET (`U-LOADSW`) | SOA is sized on the constant-power hyperbola only. Modern trench FETs are **derated far below it** at 12 V in linear mode (Spirito). The page's selection criterion is insufficient | **High** | High |
| 10 | `R-ILIM` | 50 mΩ 2-terminal in 0805 — pad/trace parasitics are **~10 % of the value**, equal to the LT1641's own threshold tolerance. Needs Kelvin | **High** | High |
| 11 | Umbilical cable | A **soft** fault (5–30 Ω) draws under the 1.0 A limit forever and dissipates up to **12 W inside a bonded oak body**. The limiter cannot see it | **High** | High |
| 12 | `D1`/`D2` | The **~80 mV** Vf-modulation figure is right; the **"20 cents"** consequence is wrong by ~5 orders of magnitude for the circuit as now drawn | **High** | High |
| 13 | `C-BULK-RAIL` / `C1`–`C4` | Page says **4 × 47 µF**; BOM says **100 µF on +12 V**, with the arithmetic. Page is stale, and 47 µF is the wrong answer | **Medium-High** | High |
| 14 | `J-PWR-EURO` | Module draw is **declared nowhere**. It is ~390 mA typ / ~610 mA worst on +12 V — about **10× a normal 8HP module** | **Medium-High** | High |
| 15 | `LED-PANEL` / `R-LED-PANEL` / `U-LVL-MOD` | The whole "panel LED on the buffer's rail" section is **superseded**. The comparator, the gated `OE` and the watchdog are deleted; the LED is 2k2 from +12 V analog | **Medium** | High |
| 16 | `FB-IN` (FB2) | One rating (≥1 A) applied to four branches carrying 0.61 A, 0.03 A, 0.015 A and 0.01 A. FB2 is the only one that matters and wants **≥2 A** | **Medium** | High |
| 17 | `U-REG-DAC` | Dissipation, dropout, min load all comfortable — **all three concerns in the brief are non-issues**, quantified below. Noise claim is ~3× optimistic but irrelevant | **Low / Note** | Medium |
| 18 | `U-REG-DAC` | Nominal 5.208 V puts the **worst-case low end exactly at the 5.000 V failure point**. Bench selection must go up, not centre | **Medium** | High |
| 19 | Fusing | Absence on the analog rails is **not** defensible as written: `D1` is the de facto fuse and DO-41 Schottkys fail short | **Medium** | Medium-High |
| 20 | Drawing | Shunt caps drawn in series; FET source shorted to `PWR_GND` in the ASCII | **Low** | High |
| 21 | `C-BULK-RAIL` | "4 × 47 µF is 2–5× the surveyed norm of 10–22 µF" — prior art contradicts it | **Note** | High |
| 22 | `J-UMBILICAL` | Live-unplug arc energy is **0.13 µJ** — a non-problem. Mating-cycle life is the real wear item | **Note** | High |
| 23 | `D-JACK-CLAMP` back-feed | The diodes trap back-fed jack current on the module's own rail instead of the rack. Settles at ≤ the driver's 10 V — harmless, but the LED glows with the rack off | **Note** | Medium |

---

## 1. `J-PWR-EURO` — Eurorack conformance of the entry itself

### 1.1 The connector

`[repo] hardware/bom.csv` — `J-PWR-EURO`: "16-pin shrouded keyed IDC header … Shrouded
and keyed — reversed ribbon is the classic eurorack failure. Carries the +5V rail the
module REQUIRES."

Shrouded + keyed 2×8 on 2.54 mm pitch is the Doepfer convention `[from memory]`. That
part of the specification is correct and unremarkable.

### 1.2 The pinout is stated nowhere in the repository

`[repo]` — I grepped `hardware/`, `docs/decisions/` and `README.md`. **No pin numbers
appear for `J-PWR-EURO` anywhere.** `hardware/module/power-entry.md`'s diagram lists the
rails in the order `+12V, −12V, +5V, GND`, which is not the physical order and is not
labelled as a schematic-only ordering.

The physical order I could establish:

`[prior-art] scratchpad/repos/performer-hardware/sequencer.net` + `power.sch` — the
Westlicht Performer's 2×5 Eurorack header `JP5`:

```
JP5 pins 1,2  → D4 → −12V rail
JP5 pins 3,4,5,6,7,8 → GND
JP5 pins 9,10 → D3 → +12V rail
```

So, by row (two pins per row, red stripe at row 1):

| Row | 10-pin | 16-pin |
|---|---|---|
| 1 | **−12 V** | **−12 V** |
| 2 | GND | GND |
| 3 | GND | GND |
| 4 | GND | GND |
| 5 | **+12 V** | **+12 V** |
| 6 | — | **+5 V** |
| 7 | — | **CV** |
| 8 | — | **Gate** |

`[web] https://doepfer.de/faq/a100_faq.htm` (search snippet only; the site itself is
egress-blocked): "Both the 10 pin and the 16 pin version … have available the standard
power supply (−12V, GND, +12V). In addition the 16 pin version … has the three signals
+5V, CV and Gate," and "the colored wire indicates −12V." A forum-derived row list in the
same result ("1 = −12 V, 5 = +12 V, 6 = +5 V, remainder ground") matches the netlist
above.

**Action:** put this table on `power-entry.md`. A power-entry page with no pin numbers is
the one page in the repository that cannot afford to have none.

**Residual uncertainty:** whether CV is row 7 and Gate row 8, or the reverse. It does not
matter electrically here (both are left unconnected), but check Doepfer before silkscreen.

### 1.3 Reverse-insertion behaviour — the page's claim is wrong for 16 pins

`[repo] power-entry.md`: "The bus +5 V pin gets no diode: the only thing on it is a $0.30
buffer, and a reversed ribbon that kills the buffer and nothing else is an acceptable
outcome (ADR 0004)."

**On a 10-pin cable that reasoning is fine.** Reversing a 10-pin ribbon maps row *n* to
row *6−n*: rows 2,3,4 are all GND and map onto each other, and the only change is that
+12 V and −12 V swap. `D1`/`D2`/`D3` block, reverse voltage is 12 V against the 1N5817's
20 V V_RRM, nothing is damaged. `[calc]`

**On a 16-pin cable it is not.** With eight rows, reversal maps row *n* → row *9−n*:

| Module row | Sees (bus row) |
|---|---|
| 1 (−12 V) | 8 — Gate |
| 2 (GND) | 7 — CV |
| **3 (GND)** | **6 — +5 V** |
| **4 (GND)** | **5 — +12 V** |
| 5 (+12 V) | 4 — GND |
| 6 (+5 V) | 3 — GND |
| 7 (CV) | 2 — GND |
| 8 (Gate) | 1 — −12 V |

Module rows 2, 3 and 4 are **one net** — the ground pour. So a reversed 16-pin ribbon
**shorts the rack's +12 V rail to its +5 V rail and to the bus CV line, through the
module's ground plane**, and simultaneously lifts the module's ground (and every CV jack
sleeve, and therefore every patch cable connected to it) to +12 V. `[calc]` from the row
table above. No entry diode can prevent this; only the shroud and key can.

Two consequences:

- The debate about whether the +5 V pin needs a diode is a **red herring**. In the
  failure that actually matters the +5 V pin sees 0 V; the buffer dies because its ground
  is at +12 V, and a diode in the +5 V leg changes nothing.
- The **shroud on the bus-board end** is load-bearing and is outside this project's
  control. Doepfer's current bus boards use boxed headers `[web] modularsynthesizers.nl
  product listing: "22 boxed pin headers"`, but plenty of DIY bus boards and flying-bus
  cables do not. **Rewrite the paragraph**: the reason the 16-pin header is acceptable is
  the key, not the diodes, and the cost of defeating the key is a rail-to-rail short, not
  a dead buffer.

**Rank: High. Confidence: Medium-High** (the row table depends on the CV/Gate assignment
I could not confirm from Doepfer directly; the conclusion holds for *any* non-palindromic
row order, which this is regardless of which of rows 7/8 is CV).

### 1.4 The 10-pin-cable case, which nobody has written down

A 10-pin cable in a 16-pin shrouded module header seats at one end of the shroud. Aligned
to the −12 V end (the convention), the module gets −12 V, GND and +12 V correctly and
**+5 V, CV and Gate are open**. The module then:

- has no bus +5 V, so `U-LVL-MOD` (74AHCT125) is unpowered and passes no SPI `[repo] bom.csv U-LVL-MOD`;
- **still lights `LED-PANEL`**, because the BOM moved it to the +12 V analog rail
  (`[repo] bom.csv R-LED-PANEL`: "~4mA from the module's +12V analog rail");
- still powers the umbilical, so the instrument boots and looks healthy.

Result: a lit module, a lit instrument, and no CV. `[repo] ADR 0005`: "The target rack
supplies +5 V, so the level shifter's rail is a **requirement, not an option**. No jumper,
no unpopulated fallback footprint."

That decision is defensible, but the *diagnostic* is missing. **Suggestion:** one more
LED, or better, move `LED-PANEL` to the **bus +5 V** rail so that a missing +5 V is
visible by the one indicator the module has. That is the fail-safe arrangement
`power-entry.md` already argues for — it just argues it for a circuit that no longer
exists (finding 15). Cost: zero. **Rank: Medium.**

### 1.5 Declared current draw — there is none

`[repo]` — grepped the whole repository. The module's +12 V / −12 V / +5 V draw is
**declared nowhere**, in any form, in any document. Eurorack convention is that a module
publishes all three.

Built from the BOM and the module pages:

**+12 V**

| Item | mA | Source |
|---|---|---|
| Umbilical, typical play | 359 | `[repo] ADR 0005` load table |
| 6 × OPA2197, 12 channels @ ~1 mA | 12 | `[repo] bom.csv U-OPA-PITCH`; I_Q `[from memory]` 1 mA/ch max |
| INA828 | 1.0 | `[from memory]` 0.9 mA max |
| LM317 branch (divider 8.3 mA + DAC + pots) | 13 | `[repo] bom.csv U-REG-DAC` "~13mA load incl. the divider" |
| `LED-PANEL` via `R-LED-PANEL` 2k2: (12−2.0)/2200 | 4.5 | `[calc]` |
| LT1641 V_CC | ~1.5 | `[from memory]` |
| Six CV outputs into 100 kΩ Eurorack inputs | ~0.6 | `[calc]` 6 × 10 V/100 kΩ |
| **Module-local subtotal** | **~33** | `[calc]` |
| **+12 V total, typical play** | **~392** | `[calc]` 33 + 359 |
| **+12 V total, clamp-legal worst** | **~612** | `[calc]` 33 + 579 |
| +12 V during an umbilical fault (≤50 ms) | ~1033 | `[calc]` 33 + 1000 |

**−12 V:** 12 op-amp channels 12 mA + INA828 0.9 mA + `R-OFFNEG` 12/95.3k = 0.13 mA
→ **~13 mA**. `[calc]`, parts from `[repo] bom.csv`, `hardware/module/breath-output-stage.md`.

**+5 V (bus):** 74AHCT125 static is µA; dynamic on three lines at 2 MHz into ~20 pF is
I = C·V·f = 20 pF × 5 V × 2 MHz = 0.2 mA/line → **~0.6 mA**, call it **≤10 mA** with
margin. `[calc]`; `[repo] ADR 0005` says "around 10 mA" — consistent.

**Declare: +12 V 612 mA, −12 V 13 mA, +5 V 10 mA**, with a footnote that +12 V reaches
1.03 A for up to 50 ms during a limiter event.

**Is that reasonable for 8HP?** No, it is about **10× a normal 8HP module** — a Mutable-
class 8HP digital module is 30–60 mA on +12 V `[from memory]`. `[repo] README.md` is
entitled to say "Rack current budget is therefore **not** a design constraint here", and
that is fine for *this* rack. It is not a reason to skip the declaration: the number is
what tells the next person that this module alone is half of a 1.2 A small-case supply.

**The conductors are fine, and nobody has checked that either.** 28 AWG ribbon,
0.232 Ω/m stranded `[from memory]`, 300 mm cable:
- +12 V on 2 conductors: 0.232 × 0.3 / 2 = **34.8 mΩ**, + ~15 mΩ of IDC contacts = ~50 mΩ.
  At 612 mA → **31 mV** drop, 19 mW. At the 1.03 A fault → 52 mV. `[calc]`
- Per-conductor current at worst legal: 612/2 = **306 mA**. 28 AWG ribbon is ~1 A per
  conductor free-air, derated to ~0.5–0.7 A in a fully loaded 16-way bundle `[from memory]`.
  306 mA is comfortable.
- IDC contacts are ~1 A each, two in parallel `[from memory]`. Comfortable.

So: electrically conformant, undeclared. **Rank: Medium-High (documentation), Confidence: High.**

---

## 2. `D1`, `D2`, `D3` — the three 1N5817s

### 2.1 Forward drop and dissipation at the real currents

1N5817, 1 A / 20 V DO-41. V_F max 0.45 V at 1.0 A; typical curve ~0.20 V at 20 mA,
~0.30 V at 250 mA, ~0.33 V at 360 mA, ~0.38 V at 600 mA `[from memory — 1N5817 datasheet
was not reachable; these are curve readings and must be confirmed]`.

| Diode | Branch | Current | V_F | P = V_F·I | ΔT at R_θJA ≈ 100 °C/W |
|---|---|---|---|---|---|
| `D1` | module analog +12 V | 33 mA | ~0.22 V | **7.3 mW** | 0.7 °C |
| `D2` | umbilical, typical | 359 mA | ~0.33 V | **118 mW** | 12 °C |
| `D2` | umbilical, clamp-legal worst | 579 mA | ~0.38 V | **220 mW** | 22 °C |
| `D2` | at the 1.0 A limit (≤50 ms) | 1000 mA | 0.45 V | **450 mW** | transient |
| `D3` | −12 V | 13 mA | ~0.20 V | **2.6 mW** | 0.3 °C |

`[calc]` throughout, from `[repo] ADR 0005` load table.

`D2` runs at **100 % of its 1 A continuous rating** during a limiter event, for 50 ms. The
1N5817's I_FSM is 25 A for 8.3 ms `[from memory]`, so this is not close to a problem. But
`D2` at 22 °C rise in a rack is a warm axial part and should not be tucked under the
etherCON. Layout note, not a finding.

### 2.2 Why the +12 V leg is split — the arithmetic *is* right

`[repo] power-entry.md`: a shared diode would let instrument current modulate V_F "by
~80 mV". Recomputed:

| State | Shared-diode current (33 mA + umbilical) | V_F |
|---|---|---|
| Quiescent | 33 + 212 = 245 mA | ~0.305 V |
| Typical play | 33 + 359 = 392 mA | ~0.340 V |
| Clamp-legal worst | 33 + 579 = 612 mA | ~0.380 V |

Swing = 0.380 − 0.305 = **75 mV**. `[calc]` The page's ~80 mV is confirmed.

### 2.3 …and the *consequence* is wrong by five orders of magnitude

`[repo] power-entry.md` calls the 75 mV "**about 20 cents of breath-correlated pitch
bend**, needing no ground path at all, visible by inspection of the diagram." That is the
sole stated justification for `D2`.

Trace the 75 mV forward through the circuit **as it is now drawn**:

1. **→ `U-REG-DAC` → DAC AVDD.** LM317 line regulation 0.01 %/V typ `[from memory]`
   = 0.01 % × 5.21 V = 0.52 mV per volt of input change. 0.075 V × 0.52 mV/V = **39 µV**
   on AVDD. `[calc]`
2. **→ pitch.** Pitch's reference is *not* this rail.
   `[repo] hardware/module/pitch-stage.md` line 14: `VREFOUT ──[TRIM-OFFSET 10k]──┬── ½ OPA2197 ──┬── V_ref ≈ 2.500 V`,
   and line 99: "The DAC's full scale is `2 × VREFOUT`". The DAC uses its **internal
   2.5 V reference** `[repo] ADR 0005`. AVDD sets only whether the buffer can *reach*
   5.000 V. So 39 µV of AVDD movement is not a pitch error at all.
3. **→ op-amps.** OPA2197 PSRR ≥ 114 dB `[from memory]`. 75 mV / 10^(114/20) =
   75 mV / 501 187 = **0.15 µV** referred to input. `[calc]`

0.15 µV at 1 V/oct is **0.00018 cents**. The claimed figure is 20 cents. The ratio is
~10⁵.

The "20 cents" number is almost certainly a survival from a superseded topology — one
where the pitch offset came from a rail divider, which `[repo] hardware/module/pitch-stage.md`
line 94 records as already deleted: "ADR 0006 moved the offset reference off the ±12 V
rail because a bare divider…".

**I am not recommending deleting `D2`.** Twenty cents of hardware is worth it. I am saying
the page's headline argument does not survive contact with the circuit it sits on, and a
justification that is wrong by 10⁵ will get the part deleted by the next reviewer who
checks it. Replace it with the reasons that hold:

- **Fault isolation.** With a shared diode, a 1.0 A limiter event runs the module's own
  analog rail through a diode at 0.45 V instead of 0.22 V — a 230 mV step on the analog
  rail at the exact moment the instrument faults.
- **HF, not DC.** The Schottky's dynamic resistance at 392 mA is
  r_d = n·V_T/I = 1.05 × 25.9 mV / 0.392 A = **69 mΩ** `[calc]`. The instrument's two
  R-78E5.0 bucks put chopped current through this node; OPA2197 PSRR falls to ~45 dB at
  100 kHz `[from memory]`, so 10 mA of HF ripple in a shared diode → 0.7 mV → ~4 µV RTI.
  Still small, but 25× the DC case, and it is the term that actually justifies a split.
- **It costs twenty cents.** Which is the page's own last line and the best argument on
  the page.

**Rank: High (the number, not the part). Confidence: High.**

### 2.4 What the split does *not* fix — and this is the real problem

See §5. `D1` and `D2` isolate the **diode**. They do nothing about the shared **ribbon,
IDC contacts and bus-board copper**, which the page dismisses in the same sentence
("needing no ground path at all"). That dismissal is the error: the ground path is where
the pitch bend actually lives, and it is roughly **50 000× larger** than the effect the
second diode removes.

### 2.5 Effect on downstream rail budgets — `U-REG-DAC` dropout is not in danger

The brief asks specifically about the LM317 dropout. Worked:

```
Rack +12 V at −5 %                       11.40 V
− D1 forward drop at 33 mA               − 0.22 V
− FB1 DCR ~50 mΩ at 33 mA                − 0.0017 V
= LM317 input, worst case                 11.18 V        [calc]

LM317L dropout at 13 mA, worst case      ~ 2.5 V         [from memory]
Required input = 5.21 + 2.5              = 7.71 V
Margin                                    11.18 − 7.71 = 3.47 V     [calc]
```

**Margin is 3.47 V.** You could put *fifteen* more 1N5817s in series before the LM317
dropped out. The Schottky drop is a complete non-issue for this regulator, and the page
should say so rather than leaving it as an open worry.

The only rail where the drop is arithmetically interesting is the umbilical, and
`[repo] ADR 0005` has already done it: "122 mV cable + 400 mV Schottky + 60 mV → ~11.4 V,
5 %". Recomputed with my V_F: 12.00 − 0.33 (D2) − 0.03 (FB2 at 50 mΩ) − 0.122 (cable) =
**11.52 V** at typical play. `[calc]` ADR 0005's 11.4 V used a pessimistic 0.40 V diode;
either number is inside the instrument's tolerance.

---

## 3. `U-LOADSW` — the LT1641-1 circuit

### 3.1 Part facts I could establish

`[web] https://www.analog.com/media/en/technical-documentation/data-sheets/164112fc.pdf`
— **blocked** (`EGRESS_BLOCKED`). Mirrors at mouser, digikey and rocelec all returned
403 through the proxy. What a web *search* returned verbatim
`[web] search result summarising analog.com/en/products/lt1641-1.html`:

- "8-pin Hot Swap controllers that allow a board to be safely inserted and removed from a
  live backplane."
- "**The current limit is set by placing a sense resistor between VCC (Pin 8) and SENSE
  (Pin 7).**"
- "programmable **analog foldback** current limit circuit."
- "If the chips remain in current limit for more than a programmable time, the N-channel
  pass transistor is either **latched off (LT1641-1)** or is set to **automatically
  restart after a time-out delay (LT1641-2)**."
- "After the **TIMER pin is pulled higher than 1.233 V**, the fault latch is set and the
  GATE pin is pulled to GND immediately."

Everything else below is `[from memory]` and **must be checked**: sense threshold 50 mV,
GATE pull-up current ~10 µA, TIMER charge current, ON pin threshold ~1.316 V, FB pin (pin
5) sets foldback from a divider off the **output**.

`[repo] power-entry.md` already flags that it could not pin down pin names, foldback
topology, or the `-1` reset behaviour. Good. The problem is that it then does arithmetic
that depends on all three.

### 3.2 `R-ILIM` at 50 mΩ

```
I_LIM = 50 mV / 50 mΩ = 1.00 A                                  [calc]
Drop at 359 mA typical: 0.359 × 0.05 = 18.0 mV, P = 6.4 mW      [calc]  ✓ page
Drop at 1.0 A:          50 mV, P = 50 mW                        [calc]
```

Page's arithmetic is right. A 0805 at 50 mW is inside a 125 mW part.

**But the tolerance stack is dominated by something nobody has counted.** `[repo]
bom.csv R-ILIM` correctly notes that a ±11 % target window is narrower than the LT1641's
own sense-threshold tolerance. It does not note that **a 50 mΩ 2-terminal chip resistor's
own termination and pad resistance is 2–5 mΩ** `[from memory]`, plus trace. 5 mΩ on 50 mΩ
is **10 %** — the same size as the IC's threshold tolerance, and it adds on top.

**Action:** specify a **4-terminal (Kelvin) sense resistor** — 1206 or 2010 metal-strip —
and Kelvin-route V_CC and SENSE to its sense pads, not to its power pads. This is a
layout constraint that must be on the page, because it cannot be fixed later. It also
makes the E6 bench selection meaningful; with 2-terminal connection you would be
selecting against your own solder joint.

**Rank: High. Confidence: High.**

### 3.3 The timer — `C-TIMER-LOADSW` at 10 nF is wrong by 40–400×

`[repo] bom.csv C-TIMER-LOADSW`: "10nF C0G … Sets the ~50ms fault timeout … Exact value
from the datasheet equation; analog.com was unreachable."

```
t_FAULT = 1.233 V × C_T / I_TIMER                                [web] 1.233 V threshold
```

Solve for the I_TIMER that would make 10 nF give 50 ms:

```
I_TIMER = 1.233 × 10 nF / 50 ms = 0.247 µA                       [calc]
```

**No hot-swap controller uses a 250 nA timer current.** Plausible values are 2–100 µA,
which give:

| I_TIMER | C_T for 50 ms | What 10 nF actually gives |
|---|---|---|
| 2 µA | 81 nF | 6.2 ms |
| 10 µA | 405 nF | **1.23 ms** |
| 100 µA | 4.06 µF | 123 µs |

`[calc]` all rows.

So the required part is **somewhere between 81 nF and 4.1 µF** — and in no case is it
10 nF, and in no case is it a **0805 C0G** part, which is also what the BOM row specifies.
81 nF C0G is already a 1206; 4 µF is an X7R or a film cap.

As drawn and as BOMed, the module **latches off about 1 ms into every start**, forever,
and the failure would look exactly like a bad FET or a bad cable.

**Action:** this row cannot ship as a placeholder. Pull the LT1641 timer equation from the
datasheet, compute, and put the package on the row. Until then mark the row `blocking`,
not `open`.

**Rank: Showstopper. Confidence: High** — the conclusion is independent of which I_TIMER
value is correct.

### 3.4 The gate ramp — **there is no gate capacitor anywhere**

The entire design rests on a programmed ramp: `[repo] power-entry.md` "**A normal start
never enters current limit** — 0.53 A against a 1.0 A limit — which is the whole job of
the programmed ramp," and `[repo] ADR 0005` "1.0 A, latch-off, with a programmed
50–100 ms ramp."

The ramp is set by a capacitor from GATE to ground (or GATE to source), charged by the
LT1641's internal charge-pump pull-up:

```
dV_OUT/dt = I_GATE / C_GATE
For 240 V/s at I_GATE = 10 µA:  C_GATE = 10 µA / 240 V/s = 41.7 nF     [calc]
For 240 V/s at I_GATE = 20 µA:  C_GATE = 83 nF                          [calc]
```

`[repo] hardware/bom.csv` — grepped. **There is no `C-GATE-LOADSW` row.** `[repo]
power-entry.md` — the ASCII shows `GATE` going straight to the FET gate with nothing on
it. `C-TIMER-LOADSW` exists (for the TIMER pin); the gate capacitor does not.

Without it, the ramp is set by the FET's own C_iss (~1 nF for a DPAK part `[from memory]`):

```
dV/dt = 10 µA / 1 nF = 10 000 V/s
I = C_LOAD · dV/dt = 2.1 mF × 10 000 V/s = 21 A demanded          [calc]
```

which is 21× the limit. Every start becomes a hard current-limited start, the timer runs
from t = 0, and (per §3.3) the module latches. **The "programmed ramp" that the FET
sizing, the boot analysis, the SOA argument and the ADR's 50–100 ms specification all
depend on does not exist in the BOM.**

**Rank: Showstopper. Confidence: High.**

### 3.5 The start current is not 0.53 A — the load is not counted

`[repo] power-entry.md`: "**A normal start never enters current limit** — 0.53 A against
a 1.0 A limit."

That is the *capacitor charging current only*. During the ramp the instrument also turns
on. From `[repo] hardware/controller/carrier.md` §1, the WS2815 strips tap raw +12 V
directly and the two R-78E5.0 bucks sit behind `L-BUCK-IN`; the bucks start around
6.5–7 V input `[from memory — Recom R-78E5.0 input range 6.5–32 V]`.

```
Charging current (2.1 mF at 240 V/s):                    0.50 A       [calc]
+ load current at the top of the ramp (typical play):    0.36 A       [repo] ADR 0005
= peak demand near V_OUT = 12 V                          0.86–0.89 A  [calc]

Limit, nominal (50 mV / 50 mΩ):                          1.00 A
Limit, −10 % sense threshold (45 mV / 50 mΩ):            0.90 A       [calc]
Limit, −10 % threshold AND +10 % R_ILIM (45 mV/55 mΩ):   0.82 A       [calc]

Margin at the nominal corner:   1.00 − 0.89 = 0.11 A  (11 %)
Margin at the −10 % corner:     0.90 − 0.89 = 0.01 A  (1 %)           [calc]
Margin at the worst corner:     0.82 − 0.89 = −0.07 A (fails)         [calc]
```

Every normal start lands on the edge of current limit at the *end* of the ramp, and at the
tolerance corner it enters current limit — which starts the timer, which (once §3.3 is
fixed to ~50 ms) it will probably survive, and which (as BOMed) it will not.

Worse at the clamp-legal worst case: 0.50 + 0.58 = **1.08 A demand against a 1.00 A
nominal limit**. `[calc]` The module cannot start into a full-lighting instrument.

**Actions, pick one or more:**
- Lengthen the ramp to 100 ms (halves the charging term to 0.25 A → 0.61/0.83 A demand).
  The page's own table already offers this column; nothing on the page chooses it. **Choose it.**
- Raise the limit. But `[repo] ADR 0005` bounds it from above at the etherCON's 1.5 A
  contact rating, and from below by 0.63 A + ramp. The window is 0.9–1.4 A and 1.0 A is
  at the bottom of it. **1.2 A with a 42 mΩ sense resistor is the better centre.** `[calc]`
  50 mV / 1.2 A = 41.7 mΩ.
- Both. A 100 ms ramp at a 1.2 A limit gives 0.25 + 0.58 = 0.83 A against a worst-corner
  0.98 A — 15 % margin at the worst case rather than −8 %. `[calc]`

**Rank: Showstopper. Confidence: High.**

### 3.6 Foldback — stated backwards, and it breaks the boot

`[repo] power-entry.md`: "**Program the foldback.** The LT1641 family reduces its current
limit while the FET's drain voltage is high."

In a high-side N-FET switch the drain is on the **input** side, permanently at +12 V. The
drain voltage is *always* high. What the sentence means is that the limit folds back when
**V_DS** is high, i.e. when the **output** is low — the FB pin is driven by a divider from
the output `[from memory]`. As literally written the sentence is not implementable.

That matters, because the foldback the page recommends **acts during the ramp**, when
V_OUT starts at zero.

Let *k* be the folded-back limit at V_OUT = 0 as a fraction of the full limit, with a
linear law I(V) = I_max·(k + (1−k)·V/12). A current-limited start then takes:

```
t = C · ∫₀¹² dV / I(V) = C · V_in / (I_max·(1−k)) · ln(1/k)          [calc]
```

| Foldback *k* | Start current at V=0 | Current-limited start time (2.2 mF, 12 V, 1.0 A) |
|---|---|---|
| 1.0 (none) | 1.00 A | **26.4 ms** ← the page's number |
| 0.50 | 0.50 A | **36.6 ms** |
| 0.25 (typical) | 0.25 A | **48.8 ms** |
| 0.20 | 0.20 A | **53.1 ms** |

`[calc]` each row from the expression above; k=1 reproduces the page's 26 ms exactly,
which validates the form.

**The page's own timer is 50 ms, "comfortably past 26 ms".** With the foldback it also
instructs, a current-limited start takes 49–53 ms and the module latches off on its own
cold start, intermittently, in a way that will look like a marginal cable.

The page adds foldback in one section and does the boot arithmetic in another and never
connects them.

**And the SOA number is then double-counted the other way.** With foldback, a hard short
does not dissipate 12 W. Peak FET dissipation is at
V = 12·(1−2k)/(2(1−k)) `[calc]`, giving:

| *k* | V at peak | Peak FET dissipation | Energy over 50 ms |
|---|---|---|---|
| 1.0 (none) | 0 V | **12.0 W** | 0.60 J |
| 0.50 | 0 V | **6.0 W** | 0.30 J |
| 0.25 | 4.0 V | **4.0 W** | 0.20 J |

`[calc]` So the page sizes the FET at 12 W/0.6 J (no foldback) *and* tells you to program
foldback (4 W/0.2 J). Conservative by 3×, which is fine — but it means the SOA number and
the boot number are computed from **different circuits**.

**Action:** decide whether foldback is in or out, and recompute both. My recommendation:
**leave foldback out**, take the 12 W / 0.6 J FET (which §3.8 shows is easy), and keep the
26 ms start. Foldback buys FET margin you do not need and costs boot margin you cannot
spare. If it goes in, the timer must go to ~100 ms and §3.3's capacitor grows with it.

**Rank: Showstopper (the boot interaction). Confidence: Medium** — the exact foldback law
is `[from memory]`; the *shape* of the problem (foldback slows a current-limited start
toward the timer) is certain.

### 3.7 The `ON` pin is not buildable as drawn

`[repo] power-entry.md` shows `panel toggle ──── ON` and nothing else. There is no
resistor, no divider, no stated logic level, no supply for the toggle, no pull-down, and
no debounce. `[repo] bom.csv SW-POWER`: "SPST sub-miniature toggle … drives the load
switch enable, carries no load current". `[repo] bom.csv` — grepped: **no resistor row
exists for this node.**

What is missing, and why each matters:

1. **A divider from V_CC to ON.** The ON pin threshold is ~1.316 V `[from memory]`; the
   pin is not rated to sit at 12 V. The divider is also the standard way to set **UVLO** —
   which this design wants, because the toggle will be left ON and the module must not
   start ramping into 2.1 mF while the rack's +12 V is still rising. Two resistors.
2. **A pull-down**, so an SPST toggle with one end open reads OFF rather than floating.
3. **Debounce.** A mechanical toggle bounces 1–10 ms `[from memory]`. Each bounce drops
   GATE to ground and restarts the ramp from zero with the output already partly charged.
   Not destructive, but it re-runs the inrush several times per flip and can chain into a
   fault. 10 kΩ + 100 nF = 1 ms `[calc]` fixes it, and shares parts with (1).
4. **Panel wiring.** The toggle is on the panel, the LT1641 is on the PCB; the ON node is
   a high-impedance CMOS input on a wire next to six CV outputs. The RC in (3) also
   handles that.

**Rank: High. Confidence: High.** This is four passives that do not exist, on the one node
that decides whether the instrument powers up.

### 3.8 The FET — the SOA criterion on the page is the wrong one

`[repo] power-entry.md`: "**DPAK or SO-8, chosen against the part's single-pulse SOA
curve**, not against its R_DS(on)."

The *direction* is right and the earlier SOT-23 was indeed an error. Numbers:

| Package | Z_θJ at 50 ms single pulse | ΔT_J at 12 W | ΔT_J at 4 W |
|---|---|---|---|
| SOT-23 | ~25–40 °C/W (to ambient) | **300–480 °C** | 100–160 °C |
| SO-8 | ~3–6 °C/W | 36–72 °C | 12–24 °C |
| DPAK | ~0.6 °C/W (junction-to-case) | **7.2 °C** | 2.4 °C |

`[from memory]`, `[calc]` for the products. The page's "hundreds of degrees" for SOT-23 is
right; DPAK and SO-8 are both comfortable on a *thermal* basis.

**But thermal transient impedance is not what kills hot-swap FETs.** Modern low-R_DS(on)
trench MOSFETs suffer **thermal instability in linear mode (the Spirito effect)**: at the
low V_GS the LT1641 holds during current limit, the threshold's negative tempco causes
current to crowd into the hottest cells, and the published SOA at high V_DS falls **far
below** the constant-power hyperbola. A 30 V trench DPAK may be rated only ~2–3 W at
V_DS = 12 V for 10 ms, despite a 50 W DC rating at low V_DS. `[from memory]` This is the
single most common hot-swap FET selection failure.

**Action — make the criterion specific:**
- Choose a FET whose datasheet publishes a **single-pulse SOA chart with a 10 ms and a
  100 ms curve**, and read the current allowed at **V_DS = 12 V** off that chart. Many
  parts only publish 10 µs / 1 ms / DC; those are not selectable for this job.
- Prefer a part explicitly characterised for **linear-mode / hot-swap** operation, or an
  older planar device, over the lowest-R_DS(on) trench part on the shelf.
- Required point: **1.0 A at V_DS = 12 V for 50 ms**, single pulse, at T_C = 70 °C.
  (Or 0.25 A at 12 V if foldback stays — but see §3.6.)
- R_DS(on) is genuinely irrelevant: at 359 mA, even 50 mΩ gives 0.359² × 0.05 = **6.4 mW**
  `[calc]`. The page says this and is right.

**The `-1` suffix is an SOA argument nobody has made.** Repeated SOA pulses are what
destroys hot-swap FETs; `-2`'s auto-retry is what delivers them, at whatever its retry
duty cycle is. `LT1641-1` latching means the FET sees **one** 0.6 J pulse per human
intervention, at a cadence of seconds. That is a much stronger argument for `-1` than the
one on the page (§3.9) and it should be written down.

**Rank: High. Confidence: High.**

### 3.9 `-1` vs `-2` for an instrument that gets unplugged mid-performance

`[repo] power-entry.md`: "`-1` latches off; `-2` retries automatically. Auto-retry into a
persistent fault is the oscillating-protection behaviour this design exists to avoid."
`[repo] ADR 0005` agrees.

**I concur with `-1`, and the brief's framing deserves a direct answer.**

*Unplugging mid-performance is not a fault.* Pulling the etherCON removes the load; the
output rises to 12 V, no current flows, the LT1641 does not trip, nothing latches. The
instrument goes dark and the module stays on. Correct.

*Re-plugging mid-performance is the problem*, and it is `-1`-specific — see §4.3.

Where `-1` costs you:
- `[repo] power-entry.md`: "a fault leaves the instrument dark until you deliberately
  cycle the panel toggle, which is why the panel LED matters." **The panel LED as BOMed no
  longer reports this** — `[repo] bom.csv R-LED-PANEL` puts it on the module's +12 V analog
  rail, which is alive whether the load switch has latched or not. The LED will be lit
  after a latch. So the stated mitigation for choosing `-1` does not exist. (§6.)
- Nowhere in the repository does it say **how to reset the latch.** `[repo] power-entry.md`
  itself flags this as unknown: "whether `-1` needs a reset cycle on `ON` after a
  latch-off." It does — toggling ON low then high resets the fault latch on LT1641-1
  `[from memory]`. Confirm on the datasheet, then **put it on the panel or in the manual**,
  because "the instrument is dark, flip the switch off and on again" is otherwise
  unguessable.

**Rank of the LED gap: Medium. Confidence: High.**

### 3.10 A downstream short 2 m away

**Hard short at the far end.** The cable's own 0.34 Ω round trip `[repo] ADR 0005` takes
0.34 V at 1.0 A, so the FET sees 11.66 V not 12 V → 11.7 W. `[calc]` A 2.5 % correction;
ignore it. The FET dissipates essentially all of it. Timer runs, latch sets, done.

**The soft short is the one nobody has written down, and it is worse.** The limiter is set
at 1.0 A; typical play is 0.36 A; clamp-legal worst is 0.58 A. **Any fault drawing between
~0.6 A and 1.0 A is electrically indistinguishable from legal operation and will run
indefinitely.**

```
20 Ω fault (a crushed Cat5 pair, a wetted connector, a pinched strip lead):
  I = 12 / 20 = 0.6 A        under the 1.0 A limit, never trips        [calc]
  P = 0.6² × 20 = 7.2 W      dissipated in the fault                   [calc]

12 Ω fault:
  I = 1.0 A — right at the limit, may or may not trip on tolerance
  P up to 12 W in the fault                                            [calc]
```

`[repo] ADR 0005`'s own "Body heat" column gives the instrument's normal internal
dissipation as 4.1 W typical, 6.5 W at the clamp-legal worst. So **a legal-looking fault
can more than double the thermal load inside a sealed, bonded, insulating oak body**, with
no indication anywhere and no mechanism to stop it.

`[repo] README.md` names heat as one of the three constraints that survive the "generous
supply" relief: "The body is oak and acrylic — insulators — and sealed."

**Action:** state this explicitly on the page as the limiter's blind spot, and decide
what, if anything, covers it. Candidates, cheapest first:
- **Nothing**, accepted and written down. Defensible, but it must be a decision.
- A thermal cutout on the instrument's interior — `[repo] ADR 0014` already cares about
  interior rise for the lighting clamp, so there may already be a sensor to reuse.
- Firmware: the real-time board knows its own 5 V load; it cannot see a fault upstream of
  the buck, so this covers little.

**Rank: High. Confidence: High.**

---

## 4. Inrush, and the three umbilical connection cases

### 4.1 How much capacitance is actually at the far end

`[repo] power-entry.md`: "**The instrument's bulk capacitance is ~2.2 mF** — two 100 µF at
the buck inputs plus up to 2 × 1000 µF at the WS2815 feed points."

`[repo] hardware/controller/carrier.md` §1 draws **one** `C-BUCK-IN 100 µF 25V`, behind a
single `L-BUCK-IN`, feeding *both* R-78E5.0 modules. And `C-STRIP-BULK` is specified as a
range, 470–1000 µF each.

```
Maximum: 100 µF + 2 × 1000 µF = 2.10 mF        [calc]
Minimum: 100 µF + 2 ×  470 µF = 1.04 mF        [calc]
```

So 2.2 mF is the right *worst case* to design to, but the page states it as a single
number, and 2.1 mF is the correct one. More importantly the **factor-of-two range** is
never acknowledged, and it flows into the charging current (§4.2), the start time and the
timer margin. **Fix the number, and state it as a range.** `Rank: Low, but it propagates.`

### 4.2 Does the ramp work, and is the energy right?

Page's table, re-derived:

```
dV/dt over 50 ms to 12 V:     12 / 0.050 = 240 V/s                     [calc] ✓
Charging current at 2.1 mF:   2.1e-3 × 240 = 0.504 A                   [calc] (page: 0.53 A at 2.2 mF ✓)
Peak FET dissipation at t=0:  12 V × 0.504 A = 6.05 W                  [calc] (page: 6.3 W ✓)
Energy into the FET:          ∫(V_in − V)·C·dV/dt dt = ½·C·V_in²
                              = ½ × 2.1e-3 × 144 = 0.151 J             [calc] (page: 0.16 J ✓)
```

All of the page's inrush arithmetic checks out, **including** its observation that the
energy is ½CV² regardless of ramp length and that the ramp buys peak power, not energy.
That section is correct and well reasoned.

**Does the timer allow it?** In a *ramped* start the part is not in current limit at all,
so the timer never starts — provided §3.5's margin holds, which it does not at the
tolerance corner. So: **yes in principle, marginal in practice, and impossible as BOMed
(§3.3, §3.4).**

**Does the SOA hold?** For the ramp, trivially: 6.05 W peak falling linearly to zero,
0.151 J, well inside any DPAK or SO-8. For the fault, see §3.8 — thermally yes, in linear
mode only if you select the FET against a chart that covers V_DS = 12 V.

### 4.3 Plugging the umbilical in with the module already powered — **unanalysed, and the worst case**

Nothing in `power-entry.md`, `ADR 0005` or `ADR 0004` covers this, and it is the thing a
player will do most often.

State before: toggle ON, no instrument attached, no load, no fault, LT1641 fully enhanced,
output sitting at ~12 V. Then the etherCON is inserted.

The instrument's 1.04–2.10 mF of **discharged** capacitance is connected to a fully-on
FET. There is no ramp — the gate is already up. The LT1641's current-limit amplifier must
pull the gate back down and regulate:

```
V_OUT rises at I_LIM / C = 1.0 A / 2.1 mF = 476 V/s                    [calc]
Time to 12 V:                12 / 476 = 25.2 ms                        [calc]
ALL of it in current limit → the timer runs for the whole 25.2 ms.

Against a 50 ms timer:       25.2 / 50 = 50 % of the fault budget consumed
                             by a normal user action.                  [calc]
FET dissipation, peak:       12 V × 1.0 A = 12 W — the full fault number
Energy:                      ½ × 2.1e-3 × 144 = 0.151 J in the FET     [calc]
```

And with the foldback of §3.6 at k = 0.25, the same insertion takes **48.8 ms** against a
50 ms timer — **it latches**, every time, on a normal plug-in.

Layer on top: an RJ45's eight contacts make in an uncontrolled order over a few
milliseconds of insertion, with bounce. Each make/break re-runs a piece of this.

**Actions:**
1. **Write the operating procedure down and put it on the panel:** *plug the umbilical
   first, then switch on.* This is the single cheapest fix and it costs a silkscreen line.
2. **Size the timer for the hot-plug case, not the cold-start case.** The binding number
   is 25 ms (no foldback) or 49 ms (k = 0.25), not the page's 26 ms. A 100 ms timer clears
   both with margin and costs nothing but a larger `C-TIMER-LOADSW` (which per §3.3 has to
   be resized anyway).
3. Consider whether the FET's SOA point should be specified at **12 W for 100 ms = 1.2 J**
   rather than 0.6 J. For a DPAK that is still ~14 °C of junction rise `[calc]`, so it is
   nearly free.

**Rank: High. Confidence: High.**

### 4.4 Unplugging the umbilical live

**Arc energy — a non-problem, quantified so it stops being a worry.** The umbilical is
2 m of Cat5 at roughly 1 µH/m `[from memory]`:

```
E = ½ L I² = ½ × 2 µH × (0.36 A)² = 0.13 µJ                            [calc]
```

At 12 V and 0.36 A that is far below any arcing threshold. Contact erosion is not a
consideration.

**Break order.** `[repo] carrier.md` §1 gives the umbilical map: pin 3 = +12 V, pin 6 =
PWR_GND, pin 8 = DIG_GND. Both 6 and 8 land on module ground `[repo] power-entry.md`
grounding section. If pin 6 breaks before pin 3 and pin 8, the 360 mA return transfers to
DIG_GND — one 24 AWG conductor, 0.084 Ω/m × 2 m = 0.17 Ω `[calc]` → 61 mV of transient
SPI ground offset for a few milliseconds during a disconnection that is already ending the
link. Harmless. 24 AWG carries 360 mA trivially.

**Mating-cycle life is the real wear item.** Neutrik etherCON / RJ45 is rated ~750 mating
cycles `[from memory]`. One session = one cycle; ~750 sessions is a few years of regular
playing, on a connector that is **on the module panel** (replaceable, four screws) and on
the **instrument tail** (bonded shut, per `[repo] bom.csv J-UMBILICAL`). That asymmetry is
worth a line in ADR 0004. **Rank: Note.**

**Breath output when the instrument goes:** `[repo] ADR 0005` already specifies "Pull down
the module's breath receive input", and `[repo] hardware/module/breath-receive-stage.md`
uses `R-BIAS-INAMP` for it. Covered.

---

## 5. `PWR_GND` and the IDC ground pins — the finding that outranks the diodes

`[repo] power-entry.md`, Grounding: "One origin, at the IDC's ground pin. `PWR_GND` — the
~360 mA umbilical return — runs to it on its own copper and touches nothing else on the
way."

That is correct **on the PCB**. It stops at the connector. Past the connector, the 360 mA
return shares the ribbon's ground conductors, the IDC contacts, and the bus board with
everything else — including the module's own analog return and every other module's
ground reference.

```
Ribbon, 28 AWG stranded 0.232 Ω/m, 300 mm, 6 ground conductors in parallel:
  0.232 × 0.3 / 6                                  = 11.6 mΩ          [calc]
+ IDC contacts, ~15 mΩ each, 6 in parallel, both ends:
  2 × (15/6)                                       =  5.0 mΩ          [calc]
= ground impedance in series with the module's reference   ≈ 17 mΩ

Umbilical current SWING, quiescent → clamp-legal worst:
  579 − 212                                        = 367 mA           [repo] ADR 0005 load table

Module ground moves relative to the rest of the case:
  0.367 A × 17 mΩ                                  = 6.2 mV           [calc]
```

**Every CV output on this module is referenced to that ground.** The destination VCO is
referenced to its own ground pin on the bus. Our ribbon's drop is entirely in series with
our reference and is *not* shared with the destination, so it appears as a differential
error at the destination's input:

```
6.2 mV at 1 V/oct × 1200 cents/V = 7.4 cents                          [calc]
```

Compare with the numbers this project already works to. `[repo] hardware/module/pitch-stage.md`
line 287 puts the **whole pitch error budget** at "0.42 cents … the largest term, and
untrimmable" (the DAC's internal reference), with the LT5400 below it. **A 7-cent
ground-coupled term is roughly 15× the entire budget**, and it is breath- and
lighting-correlated because the instrument's lighting tracks play (`[repo] ADR 0014`).

And compare with what `D2` buys: §2.3 puts that at **0.00018 cents**. The ground term is
about **40 000× larger**, and `power-entry.md` explicitly dismisses the ground mechanism
in the same sentence that introduces the diode one — "needing no ground path at all."

**How bad it actually is depends on case wiring, which is outside the module:**

| Bus topology | Ground path, our module → destination | Pitch error at 367 mA swing |
|---|---|---|
| Short ribbon, rigid bus board with a pour | ~10 mΩ | **4.4 cents** `[calc]` |
| 300 mm ribbon + typical bus board | ~17–25 mΩ | **7.4–11 cents** `[calc]` |
| Flying-bus cable, modules 1 m apart (0.232 Ω/m / 6 = 38.7 mΩ/m) | ~55 mΩ | **24 cents** `[calc]` |

**Actions, in order:**
1. **Measure it at E6, before anything else.** Scope across (our module's jack sleeve) −
   (a neighbouring module's jack sleeve) while the instrument cycles its lighting from
   blanked to clamp-legal worst. Five minutes. It settles whether this is 2 cents or 20.
2. **Shortest possible ribbon**, and specify it: this is the one module in the case where
   ribbon length is an electrical parameter, not a convenience.
3. **Two ribbons.** The module has one 16-pin header; a second header wired ground-only,
   on a separate short ribbon to a different bus position, halves the ground impedance for
   ~£1. Non-standard, but so is the module.
4. **Reduce the swing, not just the peak.** `[repo] ADR 0014`'s lighting clamp bounds the
   *maximum*; what hurts here is the *modulation*. A clamp that holds total LED current
   roughly constant (dumping the difference) converts a 367 mA swing into a near-DC load
   and deletes the term. That is a real cost and a real decision — but it is the only fix
   that is entirely inside the project.
5. If it measures small, **say so on the page with the measurement**, so the "needs no
   ground path at all" sentence stops being an unexamined assertion.

**Rank: Showstopper. Confidence: Medium-High** — the mechanism and the arithmetic are
certain; the ribbon and bus-board impedances are `[from memory]` estimates and the answer
scales linearly with them, which is exactly why it must be measured rather than argued.

**The +12 V side of the same shared path is *not* a problem**, and it is worth saying so:

```
+12 V ribbon impedance:  0.232 × 0.3 / 2 + 15 mΩ  ≈ 50 mΩ             [calc]
Node movement at 367 mA swing:  18.4 mV                                [calc]
→ LM317 (0.52 mV/V line reg):   9.6 µV on AVDD                        [calc]
→ OPA2197 (PSRR 114 dB):        0.037 µV RTI                          [calc]
```

Negligible. The asymmetry is the whole point: **rail movement is rejected by PSRR; ground
movement is not rejected by anything.**

---

## 6. `LED-PANEL`, `R-LED-PANEL`, `U-LVL-MOD` — the page's LED section is superseded

`[repo] power-entry.md` devotes a section to "The panel LED sits on the buffer's rail, not
on +12 V", drawing the LED and the 74AHCT125's `OE` pins sharing the LM311's open
collector, with `R-OE-PU 10k` and `R-LED 820R` on bus +5 V, and states: "The **comparator
and the watchdog stay on the LM317's 5.21 V**."

**All three circuits are deleted.**

- `[repo] bom.csv U-LVL-MOD`: "**OE IS TIED ENABLED.** The presence-gated OE is deleted
  along with its comparator."
- `[repo] bom.csv LED-PANEL`: "**A PLAIN POWER LED off the module's own rail** … that
  comparator is **DELETED**."
- `[repo] bom.csv R-LED-PANEL`: "**2k2 1%** … ~4mA from the module's +12V analog rail.
  **Was 820R from bus +5V** when it shared a node with the level shifter's OE pins; **that
  node is gone** with the comparator."
- `[repo] bom.csv R-CLR-PU`: "**THE WATCHDOG IS DELETED** (U-WATCHDOG, R-WDT, C-WDT all gone)."
- `[repo] hardware/module/digital-and-supervision.md` §"There is no presence detect
  either" and §"There is no frame watchdog" confirm both deletions in prose.

So `power-entry.md`'s LED section, its `(5.21 − 2.0)/4 mA ≈ 800 Ω → 820 Ω` arithmetic, its
fail-safe argument, its LM311-on-±12 V paragraph, and the "OPA2197 ×6, INA828, LM311" load
list in its top diagram are **all stale**. The correct state:

```
+12 V analog ──[R-LED-PANEL 2k2]──▷|── PWR_GND
I = (12 − 2.0) / 2200 = 4.55 mA                                        [calc]
```

Three knock-ons:

1. **The load list in the diagram is wrong.** Remove LM311; it changes the +12 V analog
   tally (I used the corrected figure of ~33 mA throughout, not the BOM's stale "~22 mA").
2. **The `-1` latch has lost its indicator** (§3.9). On +12 V analog, the LED is lit
   whether or not the load switch has latched. If the LED's job is "this still says why
   the instrument went dark" `[repo] bom.csv LED-PANEL`, it must be driven from the
   **load switch output**, not from the module's own rail. One resistor, moved.
3. **`C-DECOUPLE` still counts the LM311.** `[repo] bom.csv C-DECOUPLE`: "6 x OPA2197 on
   +/-12V = 12, INA828 = 2, **LM311 on +/-12V = 2**, DAC8568 AVDD+DVDD = 2, 74AHCT125,
   LT1641 VCC, LM317 in" = 21, matching the row's qty 21. With the LM311 gone the count is
   **19**. Out of my scope to fix, but it is in my scope to notice that the deletion was
   not propagated into the BOM's own arithmetic.

**Rank: Medium (the LED indicator is the substantive part). Confidence: High.**

---

## 7. `C-BULK-RAIL` / `C1`–`C4` — the page contradicts the BOM, and the BOM is right

`[repo] power-entry.md` draws `C1 47µF`, `C2 47µF`, `C3 47µF`, `C4 47µF` and states under
*Still open*: "**Entry bulk is 4 × 47 µF**".

`[repo] bom.csv C-BULK-RAIL`: "**100uF (+12V) / 47uF (−12V, +5V)** 25V electrolytic …
**NOT 47uF on every rail.** The +12V branch carries the LM317's divider, the DAC and the
comparator, about 22mA against −12V's 10mA — so at 47uF each it collapses 2.2x faster and
every rack power-down leaves the op-amps with V+ near 0 and V− at −6 to −8V for ~30ms,
pulling all six jacks toward the surviving negative rail. 100uF on +12V balances the decay."

The BOM's reasoning is sound and I reproduce it with my corrected load figures:

```
+12 V analog load (§1.5, LM311 removed, LED at 4.55 mA):  30.4 mA
−12 V load:                                               13.0 mA
Ratio:                                                     2.34                    [calc]

Decay rate dV/dt = I/C.  For the two rails to collapse together:
  C(+12) / C(−12) = 2.34  →  with 47 µF on −12 V, +12 V wants 110 µF               [calc]

BOM's 100 µF gives a ratio of 100/47 = 2.13 against a required 2.34 — within 10 %.  ✓
The page's 47 µF gives a ratio of 1.00 against a required 2.34:
  +12 V decays at 30.4 mA / 47 µF = 647 V/s
  −12 V decays at 13.0 mA / 47 µF = 277 V/s
  +12 V reaches 0 in 18.5 ms; −12 V is still at −6.9 V                             [calc]
```

Eighteen milliseconds of six CV jacks being dragged toward −7 V on **every rack
power-down** is exactly the failure the BOM row describes, and the page's number produces
it.

**Fix the page.** And note that the BOM's own input figure ("about 22mA") is now low —
with the LM311 gone but the LED moved onto this rail, the true number is 30.4 mA, and the
ideal capacitor is ~110 µF. 100 µF is close enough; 47 µF is not.

**Rank: Medium-High. Confidence: High.**

### The "2–5× the surveyed norm" claim does not survive prior art

`[repo] power-entry.md`, *Still open*: "**Entry bulk is 4 × 47 µF**, which is 2–5× the
surveyed norm of 10–22 µF."

`[prior-art] scratchpad/repos/performer-hardware/power.sch` — the Westlicht Performer, a
shipping open-source Eurorack module, fits **47 µF** electrolytics (`C13`) directly on its
±12 V entry behind 1N5819 Schottkys, with a further 22 µF behind the bead for its
regulator. So 47 µF per rail is *the* norm in at least one surveyed design, not 2–5× it.

The underlying concern — case-wide inrush at rack power-on — is real. Quantified:

```
Per +12 V branch: 100 µF, charged through ~90 mΩ of bead+ribbon plus the cap's own
ESR (~0.5 Ω for a 25 V radial electrolytic, [from memory]):
  I_peak ≈ 12 / 0.59  = 20 A
  τ      = 0.59 × 100 µF = 59 µs
  Q      = 100 µF × 12 = 1.2 mC                                                    [calc]
1N5817 I_FSM is 25 A for 8.3 ms [from memory] — a 20 A / 60 µs pulse is inside it.
```

That is what every Eurorack module does. And **the module's largest capacitance — the
instrument's 2.1 mF — contributes nothing to rack power-on inrush**, because the load
switch ramps it. The load switch is the module's single biggest inrush *mitigation*, and
the page's Still-open note does not credit it.

**Rank: Note. Confidence: High.**

---

## 8. `FB-IN` — one rating for four very different branches

`[repo] bom.csv FB-IN`: "Ferrite bead ≥1A 600R@100MHz … One per branch: +12V analog, +12V
umbilical, −12V, +5V. **Rated ≥1A** — the common 0805 600R part is ~300mA and a saturated
bead is a wire."

The *principle* is right and `power-entry.md` states it well ("Read the series, not the
footprint"). The *application* is uniform where the branches are not:

| Bead | Branch | Continuous current | Fraction of a 1 A rating |
|---|---|---|---|
| FB1 | +12 V analog | 30 mA | 3 % |
| **FB2** | **+12 V umbilical** | **359–579 mA, 1.0 A in a fault** | **36–58 %, 100 % in a fault** |
| FB3 | −12 V | 13 mA | 1 % |
| FB4 | bus +5 V | ≤10 mA | 1 % |

`[calc]` from §1.5.

A ferrite bead's impedance falls with DC bias long before it "saturates" — a 1 A-rated
part is typically down 30–50 % of its rated impedance at 60 % of rated current
`[from memory]`. FB2 at 579 mA is doing perhaps 300 Ω of the specified 600 Ω, and at the
1.0 A limiter trip it is close to a wire — exactly the condition the row warns about.

**FB2 is also the only one whose job matters**: it is what keeps the instrument's two
buck converters' switching current out of the rack's +12 V rail and off `D1`'s shared node
(§2.3). The other three filter loads of 10–30 mA.

**Action:** split the row. FB2 = **≥2 A, 600 Ω @ 100 MHz, 1210**, selected against its
published **impedance-vs-DC-bias curve at 600 mA**, not against its rated current. FB1/3/4
can be any ≥300 mA 0805.

DCR check: a 2 A 1210 bead is ~25–50 mΩ `[from memory]`. At 579 mA → 14–29 mV, 8–17 mW.
`[calc]` Negligible, and it does not threaten the umbilical budget (§2.5).

**Rank: Medium. Confidence: High.**

---

## 9. `U-REG-DAC` (LM317LZ) and `R-REG-SET` (150 R / 475 R, 0.1 %)

### 9.1 Output voltage

```
V_out = 1.25 × (1 + 475/150) + I_ADJ × 475
      = 1.25 × 4.1667                      = 5.2083 V
I_ADJ (LM317L) 50 µA typ, 100 µA max:      + 24 to 48 mV
→ 5.232 V typical, 5.256 V worst high                                  [calc]
```

`[repo] bom.csv R-REG-SET` gives 5.21 V (the ratio term only). `[repo] bom.csv U-REG-DAC`'s
*description* field says "**set to 5.25 V**". Both are inside the band but the two rows
disagree with each other, and every module page quotes 5.21 V. Pick one. **Rank: Low.**

### 9.2 The nominal is on the wrong side of the window

The reference is the dominant term, as the BOM row correctly says. Worked:

```
LM317 V_REF spread, 1.20–1.30 V [from memory]:
  low:  1.20 × 4.1667                     = 5.000 V
  high: 1.30 × 4.1667 + 0.048 (I_ADJ)     = 5.465 V
Span: 465 mV                                                           [calc]
```

(`[repo] bom.csv U-REG-DAC` says "worst case spans 0.66 V"; mine is 465 mV using the
25 °C reference band. Same conclusion either way.)

**The window the rail must land in:**

```
Floor:  DAC full scale 5.000 V + output-buffer headroom (~50 mV)  = 5.05 V
        [repo] ADR 0005: "What AVDD does decide is whether the output buffer can
        *reach* 5.000 V."
Ceiling: DAC8568 AVDD absolute maximum                             = 5.50 V
Window: 5.05–5.50 V, i.e. 5.275 V ±4.3 %                                          [calc]
```

The reference tolerance alone is ±4.0 %. **The window and the tolerance are the same size**
— so no fixed divider fits on paper, and `[repo] bom.csv U-REG-DAC`'s "TOLERANCE IS A
BENCH TASK, NOT A SPEC TASK" is the right call.

**But the 150/475 nominal is placed badly.** At 5.208 V nominal, the worst-case *low*
outcome is 5.000 V — **exactly the failure point**, where the top of the pitch range
silently compresses. The worst-case *high* outcome is 5.465 V, still 35 mV under abs max.
The starting point is biased toward the failure, not away from it.

**Action:** E7 should select **upward**. A first-fit alternative: 150 R / 499 R gives
1.25 × 4.327 = 5.408 V nominal, worst-case low 5.192 V (clears the 5.05 V floor by
142 mV), worst-case high 5.673 V — **which violates the 5.5 V abs max**. `[calc]` So 499 R
is too far. The usable nominal band is roughly **5.25–5.30 V**; 475 R (5.21 V) is at its
bottom edge and 487 R (1.25 × 4.247 = 5.309 V) is close to its centre. **Buy 475 R, 487 R
and 499 R** — `[repo] bom.csv R-REG-SET` already says "Buy a handful of neighbouring E96
values", which is right; this just says which way to reach.

**Rank: Medium. Confidence: High.**

### 9.3 The 0.1 % resistors are justified — but not for the reason given

`[repo] bom.csv R-REG-SET`: "Smaller R2 halves the I_ADJ term to 24–48mV; 0.1 % parts cost
pennies in the same order. The LM317's own 1.20–1.30 V reference is the dominant term and
no divider fixes it."

```
1 % parts:  ratio term error ≈ 1.4 % of (R2/R1) → 1.4 % × 3.167/4.167 = 1.06 % of V_out
            = 55 mV                                                    [calc]
0.1 % parts: 5.5 mV                                                    [calc]
Reference term: ±208 mV                                                [calc]

Total, 1 %:   √(208² + 55²) = 215 mV
Total, 0.1 %: √(208² +  5.5²) = 208 mV
Improvement: 3 %                                                       [calc]
```

So as a *tolerance stack* argument the 0.1 % parts buy 3 % and the row is right that they
do not fix the problem. **The real justification is the bench-selection procedure**: E7
measures one unit and picks R2 from the result. That only works if the part you then fit
is *the value you measured with*, to better than the increment you are selecting in. The
E96 step here is ~2 %, which at 1 % tolerance overlaps. **0.1 % is what makes bench
selection repeatable**, which is a different and better argument than the one written down.

**Rank: Note. Confidence: High.**

### 9.4 Dissipation — comfortable

```
V_in (nominal rack): 12.00 − 0.22 (D1) − 0.002 (FB1) = 11.78 V
V_in (rack +5 %):    12.60 − 0.22 − 0.002            = 12.38 V
ΔV at the high corner: 12.38 − 5.21                  = 7.17 V
I_out (incl. divider 8.33 mA): ~13 mA                  [repo] bom.csv U-REG-DAC
P = 7.17 × 0.013                                     = 93 mW          [calc]
TO-92 R_θJA ≈ 180 °C/W [from memory] → ΔT_J          = 17 °C          [calc]
LM317LZ package limit ≈ 0.6 W; output limit 100 mA
```

93 mW is **15 % of the package's capability** and 13 % of the part's current rating. Not a
concern, and the page should say so instead of leaving it implicit. `[repo] bom.csv`'s
"~90mW" is confirmed.

### 9.5 Minimum load — met, with a substitution trap

The LM317 is a floating regulator and needs a minimum load to maintain regulation.

```
Divider bleed: I = V_REF / R1 = 1.25 / 150 = 8.33 mA                   [calc]

LM317L (TO-92) minimum load: 2.5 mA typ, 5 mA max  [from memory]
  → 8.33 mA clears the worst case by 1.67×.  ✓

LM317 / LM317T (TO-220) minimum load: 3.5 mA typ, 10 mA max [from memory]
  → 8.33 mA is BELOW the worst-case 10 mA.  ✗
```

So the 150 R bottom leg is correct **for the LM317LZ that is specified**, and this is
actually the strongest argument for choosing 150 R over the previous 240 R (240 R would
give 5.2 mA `[calc]` — marginal even for the L). `[repo] bom.csv U-REG-DAC` lists the
manufacturer as "multiple", which invites an availability substitution; **if anyone fits
an LM317T, the rail drifts high at light load.** Put "LM317**L** only — the divider current
is sized to its minimum load" on the row.

**Rank: Note, but a cheap one to close. Confidence: Medium-High.**

### 9.6 Dropout — 3.47 V of margin

Done in §2.5. **Not a concern, by a factor of 4.5 on the available headroom.** The entry
Schottky is irrelevant to it.

### 9.7 Noise and PSRR into the trim networks — a non-issue, and worth saying so

`[repo] bom.csv C-REG-ADJ`: "ADJ bypass drops output noise to **~50 µV RMS**."

```
LM317 output noise spec: 0.003 % of V_OUT, 10 Hz–10 kHz [from memory]
  0.00003 × 5.21 V = 156 µV RMS                                        [calc]
```

The BOM's 50 µV corresponds to 0.001 %, which is better than the datasheet typical. I
could not reach ti.com to check whether the 0.003 % figure is specified with or without
C_ADJ. **Treat 156 µV as the design number until someone reads the datasheet.**

**Then ask whether it matters, and the answer is emphatically no:**

1. **→ DAC AVDD.** Full scale is set by the internal 2.5 V reference × 2, not by AVDD
   `[repo] ADR 0005`, `[repo] hardware/module/pitch-stage.md` line 99. AVDD noise enters
   only through the output buffer's PSRR. Small.
2. **→ pitch.** Pitch's V_ref is **VREFOUT**, not this rail `[repo] pitch-stage.md` line 14.
   `TRIM-OFFSET` sits on VREFOUT. Even if E10 builds the "small bipolar correction"
   `[repo] pitch-stage.md` line 319 from the 5.21 V rail, the injection is ±50 mV out of
   5.21 V — an attenuation of ≥100:1 `[calc]` — giving **≤1.6 µV** at V_ref, i.e.
   **0.0016 cents**. `[calc]`
3. **→ `TRIM-BREATH-ZERO` → INA828 REF.** Range is 0 → +1.0 V from 5.21 V
   `[repo] hardware/module/breath-receive-stage.md` line 163, so attenuation ≤ 1.0/5.21 =
   0.192. Noise at REF = 156 µV × 0.192 = **30 µV**, ×1 to the in-amp output, then ×4 at
   maximum panel gain → **120 µV at the breath jack** = **12 ppm** of the 10 V span. `[calc]`
4. **→ `POT-OFFSET` → the breath summer.** `[repo] hardware/module/breath-output-stage.md`:
   `R-OFF` 21.0 kΩ into `R-FB` 40.2 kΩ, gain 40.2/21.0 = 1.914. 156 µV × 1.914 =
   **299 µV at the jack** = **30 ppm** of span. `[calc]`

**PSRR at line frequency:** LM317 ripple rejection 65 dB min / 80 dB typ with a 10 µF ADJ
bypass `[from memory]`. A Eurorack linear PSU puts perhaps 10–50 mV pk-pk of 100/120 Hz on
+12 V `[from memory]`:

```
50 mV × 10^(−65/20) = 28 µV on the 5.21 V rail                         [calc]
```

Below the regulator's own noise.

**Conclusion: the LM317 is more than good enough here and the 10 µF ADJ bypass is
sufficient. Do not spend money on a low-noise LDO or an RC post-filter.** Say this on the
page so the question stops being re-opened.

**Protection diodes:** the classic LM317 ADJ-to-OUT and OUT-to-IN protection diodes are
needed above roughly 25 V output or with large output capacitance `[from memory]`. At
5.21 V with 10 µF on ADJ and 1 µF out, they are **not required**. Worth one line so nobody
adds them.

**Rank: Low / Note. Confidence: Medium** (the 156 µV vs 50 µV question is unresolved; the
*conclusion* holds at either value, since even 156 µV is 12–30 ppm of span).

---

## 10. Rail sequencing and the −12 V rail

**Power-up.** All three rails rise together from the rack. `D1`/`D2`/`D3` add ~0.2 V and no
sequencing. The LM317 starts once its input clears ~7.7 V, so **AVDD rises after +12 V** —
covered by `[repo] bom.csv R-BIAS-DAC` ("Without it the op-amp (+) inputs have no DC path
to ground … outputs can sit at either rail during that window") and
`[repo] hardware/module/pitch-stage.md` line 89. Not my finding; already handled.

**The one sequencing hazard in my scope is the load switch.** The toggle will be left ON.
At rack power-on, the LT1641 sees ON already high and begins ramping into 2.1 mF while the
rack's own rails are still coming up and every other module in the case is drawing its own
inrush. The standard mitigation is a **UVLO divider on the ON pin**, which §3.7 shows does
not exist. With it, the ramp is held off until +12 V is genuinely up; without it, the
module's ramp competes with the case's inrush and the LT1641's behaviour at a sagging V_CC
is undefined from this page. **This is the second reason the ON node needs its divider.**

**Power-down** is handled by `C-BULK-RAIL` and the analysis is in §7. `[repo] power-entry.md`'s
4 × 47 µF breaks it; the BOM's 100 µF/47 µF fixes it.

**The −12 V rail's role.** Loads: 12 OPA2197 channels, the INA828, and
`R-OFFNEG` 95.3 kΩ `[repo] hardware/module/breath-output-stage.md` — total ~13 mA (§1.5).
Its functional jobs:

1. **Pitch reaches −2.000 V** `[repo] hardware/module/pitch-stage.md` — impossible on a
   single positive supply. This is the rail's reason for existing.
2. **Mod channels reach −10.000 V** `[repo] bom.csv R-MODGAIN`.
3. **The breath offset's negative leg.** `R-OFFNEG` pulls a fixed current from −12 V into
   the summer so the offset knob crosses zero at mid-rotation, "which is what makes ±5 V
   cost two resistors instead of a part" `[repo] breath-output-stage.md`. That page also
   makes the right stability argument: 50 mV of −12 V movement gives 40.2/95.3 × 50 mV =
   **21 mV at the jack, 0.21 % of span** `[calc]` — and notes "the −12 V rail carries no
   LED current, because the strips run from +12 V." **That is correct and it is the one
   place in this design where a rail is used as a reference and it is defensible.**
4. **Not used by the LM311 comparator's threshold any more** — the comparator is deleted
   (§6), so `power-entry.md`'s and `digital-and-supervision.md`'s "threshold −200 mV (from
   −12 V)" is stale.

**Nothing on the umbilical is bipolar** `[repo] ADR 0004`: "No −12V goes up the cable." So
−12 V has no role in any umbilical fault case. Correct and worth one line, because the
question will be asked.

`D3` sizing, thermal and reverse behaviour: §2.1 and §1.3. Nothing further.

---

## 11. Fusing

### 11.1 Where there is protection

- **Umbilical branch:** the LT1641 load switch, 1.0 A, latching. This is the right device
  in the right place, and `[repo] ADR 0005`'s argument for deleting the instrument-end
  polyfuse is sound: "It sits **downstream of the module's limiter**, so it can never
  reach its trip current and protects nothing." I agree, with no reservations. The
  polyfuse deletion is correct.
- **Nothing else.** `[repo] power-entry.md`, *Still open*: "**No fuse on the analog rails.**
  The load switch covers only the umbilical branch … Deliberately left open rather than
  silently omitted."

### 11.2 The absence on the analog rails is **not** defensible as written

The honest question is: *what is the fusing element today?* Answer: **`D1` and `D3`.**

A short on the module's +12 V analog rail — a shorted 47 µF/100 µF electrolytic, a solder
bridge under the DAC's 0.65 mm pitch, an op-amp failure — is fed by:

```
Rack PSU on +12 V:                 typically 1.5–4 A available [from memory]
Path impedance: ribbon 50 mΩ + D1's dynamic resistance
At 3 A, D1's V_F ≈ 0.6 V and it is a 1 A DO-41 part carrying 3× rating.
```

The 1N5817 will fail. **Schottky diodes predominantly fail short**, not open
`[from memory]`. A shorted `D1` leaves the fault connected to the rack, and the next
element in line is the two 28 AWG ribbon conductors, which fuse in the multi-amp range
over seconds. Meanwhile every other module in the case is browning out.

So the module *does* eventually contain its own fault, by destroying a diode, possibly a
ribbon, and possibly the rack's supply's foldback behaviour along the way. That is a
failure *mode*, not a protection *strategy*, and the page should not describe it as
"deliberately left open" without saying what happens.

### 11.3 The fix is cheap and the page's own objection does not apply

`[repo] ADR 0005`'s objection to polyfuses is: "Its hold current derates to ~350–375 mA at
the documented interior rise — *below typical play*" and "A polyfuse above hold does not
trip cleanly; it creeps into current-limiting."

**Both objections are about a part running near its hold current.** On the analog rails
that is not the situation:

| Rail | Load | Suggested PTC | Margin |
|---|---|---|---|
| +12 V analog | **30 mA** | 100 mA hold / 200 mA trip | **3.3×** |
| −12 V | **13 mA** | 100 mA hold / 200 mA trip | **7.7×** |

`[calc]` A PTC at 30 % of its hold current has no meaningful derating problem, does not
creep, and clears a hard short (3 A available against a 200 mA trip = 15× overload) in
well under a second `[from memory]`. Cost: two parts, ~£0.20, ~25 mΩ each → 0.75 mV drop
`[calc]`.

**And keep them off the umbilical branch.** A PTC there would re-create exactly the
thermal-runaway loop `[repo] ADR 0014` and `[repo] ADR 0005` deleted. The load switch owns
that branch; do not double up. This is the distinction the ADR's argument actually
supports, and stating it that way makes both decisions coherent rather than contradictory.

**On the bus +5 V branch:** 10 mA of load, no diode, and the only consequence of a fault is
a dead 74AHCT125. A PTC here is optional; a 100 mA one costs nothing and stops a shorted
buffer pulling on a rack rail that other modules share.

### 11.4 Prior art

`[repo] power-entry.md` asserts "Mutable, Telex and others fit PTCs on their entry rails."
I attempted to verify this against Mutable's published board files
(`[prior-art] scratchpad/repos/mi/*/hardware_design/pcb/*.brd`) and **could not confirm
it** — my parse of the Eagle `.brd` format did not return a component list, so this is
"unverified", not "false". `[prior-art] scratchpad/repos/performer-hardware/power.sch`
(Westlicht Performer) has **no fuse or PTC** on its ±12 V entry — only 1N5819 Schottkys,
47 µF and beads. So the prior art is at best mixed, and the claim should be softened or
sourced.

**Rank: Medium. Confidence: Medium-High.**

---

## 12. Drawing defects in `power-entry.md`

These are ASCII-art artifacts, but this page is the reference a layout will be built from.

1. **Shunt capacitors drawn in series.**
   `+12V ├───┬──[D1 1N5817]──[FB1]──[C1 47µF]──┬── MODULE ANALOG +12V` puts `C1` in the
   series path. Same for `C2`, `C3`, `C4`. They are shunt to `PWR_GND`. `[repo] power-entry.md`
2. **The FET's source is shorted to `PWR_GND`.** Lines 33–37 show the FET's lower terminal
   connecting to both `PWR_GND` and `UMBILICAL +12V`. `[repo] power-entry.md`
3. **`R-ILIM`'s connection is ambiguous.** It must sit between V_CC (pin 8) and SENSE
   (pin 7) `[web]`, i.e. in the +12 V path upstream of the FET drain, with Kelvin sensing
   (§3.2). The drawing does not show which node is which.
4. **No pin numbers on `J-PWR-EURO`** (§1.2).
5. **No `ON`-pin network, no gate capacitor, no timer capacitor shown with a value**
   (§3.4, §3.7).
6. **Stale load list:** "OPA2197 ×6, INA828, LM311" — the LM311 is deleted (§6).

**Rank: Low individually; collectively the page is not yet a schematic.**

---

## 13. Things I checked that are fine

Recorded so they are not re-reviewed.

- **LM317 dropout vs the Schottky drop** — 3.47 V of margin (§2.5, §9.6).
- **LM317 dissipation** — 93 mW in a ~600 mW package (§9.4).
- **LM317 minimum load** — 8.33 mA against a 5 mA worst case, *for the L version* (§9.5).
- **LM317 noise into the trim networks** — 12–30 ppm of span, worst case (§9.7).
- **LM317 protection diodes** — not required at 5.21 V (§9.7).
- **Pitch is not on the LM317 rail** — it references VREFOUT (§9.7, `[repo] pitch-stage.md`).
- **Ribbon current capacity** — 306 mA per conductor at worst legal, against ~0.5–0.7 A
  derated (§1.5).
- **IDC contact current** — two contacts per rail at ~1 A each (§1.5).
- **Diode thermal** — 22 °C rise on `D2` at worst legal, 45 °C transiently at the limit (§2.1).
- **Diode surge** — 20 A/60 µs entry inrush against 25 A/8.3 ms I_FSM (§7).
- **Inrush energy and peak power arithmetic on the page** — all three numbers correct (§4.2).
- **Live-unplug arc energy** — 0.13 µJ (§4.4).
- **−12 V used as a reference in the breath offset** — 0.21 % of span, defensible (§10).
- **Back-powering through the CV jacks with the rack off** — `[repo] bom.csv D-JACK-CLAMP`
  gives 254 mA across six jacks. The entry diodes block it from reaching the rack, so it
  is trapped on the module's +12 V analog rail — but it cannot exceed the driving module's
  ~10 V output, so every part stays inside its rating. Consequence: **with the rack off,
  a neighbour driving our jacks partially powers our analog section and lights the panel
  LED.** Cosmetic; worth one line so it is not mistaken for a fault. `[calc]`

---

## 14. What I could not check

- **The LT1641 datasheet.** analog.com, mouser, digikey, rocelec all egress-blocked. The
  sense threshold (50 mV), GATE pull-up current, TIMER charge current, ON pin threshold,
  FB pin foldback law, UVLO behaviour and latch-reset procedure are all `[from memory]`.
  §3.3's conclusion (10 nF is wrong) and §3.6's conclusion (foldback slows the start) are
  robust across the whole plausible parameter range; the exact component values are not.
- **The 1N5817 curve.** V_F values in §2.1 are read from memory of the datasheet curve and
  set the 75 mV figure in §2.2. The *conclusion* in §2.3 does not depend on them.
- **The Doepfer A-100 technical specification.** doepfer.de blocked. §1.2's row table comes
  from a real open-source netlist for the 10-pin subset plus a search snippet for the
  16-pin extension, and the CV/Gate row assignment is unconfirmed.
- **DAC8568 AVDD PSRR and output-buffer headroom to AVDD.** ti.com blocked. §9.2's 50 mV
  headroom allowance is an estimate; if the real number is 200 mV the window in §9.2
  narrows to 5.20–5.50 V and the case for selecting upward gets stronger, not weaker.
- **OPA2197 / INA828 quiescent currents.** `[from memory]`; the §1.5 declaration is ±20 %
  on the module-local ~33 mA, which is ~5 % of the total.
- **Whether Mutable and Telex actually fit PTCs** (§11.4).

---

## 15. The shortest useful action list

1. **`C-TIMER-LOADSW`:** get the LT1641 timer equation. 10 nF is wrong by 40–400×. (§3.3)
2. **Add `C-GATE-LOADSW`.** It does not exist and the entire design depends on it. (§3.4)
3. **Recompute the start margin with load current included**, and choose the 100 ms ramp
   column the page already drew. (§3.5)
4. **Decide foldback in or out**, and recompute the timer and the SOA from that one
   decision rather than from two. My recommendation: out. (§3.6)
5. **Draw the `ON` node**: divider (doubling as UVLO), pull-down, RC debounce. (§3.7)
6. **Measure the ground-coupled pitch error at E6** before arguing about diodes. (§5)
7. **Fix `C1` to 100 µF** on the page, to match the BOM and its arithmetic. (§7)
8. **Specify the FET against a published SOA curve at V_DS = 12 V**, not against the
   constant-power hyperbola. (§3.8)
9. **Kelvin-connect `R-ILIM`.** (§3.2)
10. **Put the pinout table on the page**, and rewrite the reverse-insertion paragraph. (§1.2, §1.3)
11. **Move `LED-PANEL` to the load-switch output** so it reports the latch it was kept for. (§6)
12. **Delete the LM311/watchdog/820R section** from the page. (§6)
13. **Rewrite the `D2` justification** with a number that survives the circuit. (§2.3)
14. **Two 100 mA PTCs on the analog rails**, and none on the umbilical branch. (§11.3)
15. **Write down "plug first, then switch on."** (§4.3)
