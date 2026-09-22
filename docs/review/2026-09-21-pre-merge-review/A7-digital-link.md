# A7 — the digital path, MCU to DAC output register

**Wave:** 2026-09-21 pre-merge review. **Slice:** SPI egress → 2 m Cat5 →
74AHCT125 → DAC8568C, plus `CLR`/`LDAC` power-on behaviour, the loop budget,
supervision, and SPI host allocation.

**Cold.** Nothing under `docs/review/**` was read. `docs/research/**` was
touched once (R10) and is flagged where used.

**Provenance.** `[repo] path:line` · `[datasheet] doc, section` · `[calc]`
with the arithmetic shown · `[from memory]`. Every claim below carries one.

**Banked datasheets read for this slice**, both by decompressing the PDF
content streams directly:

- `datasheets/logic/SN74AHCT125.pdf` — TI **SCLS264O**, Dec 1995 / rev Jul 2003.
- `datasheets/analog/DAC8568CIPW.pdf` — TI **SBAS430E**, Jan 2009 / rev Jan 2014.

**Findings are node-indexed and are claims, not fixes.** Nothing in the corpus
was edited.

---

## Severity summary

| # | Node / refdes | Finding | Sev |
|---|---|---|---|
| A7-1 | `SCLK`/`MOSI`/`CS`, `R-SPI-SER` | The 100 Ω table is computed under two mutually exclusive driver models; each half's conclusion needs the model the other half rejects | **high** |
| A7-2 | `CS` cable-side `R-SPI-PULL` | Cannot hold `CS` high in the state it exists for, and is specified to a rail the module does not have | **high** |
| A7-3 | `SYNC` | Consequence of A7-2: the DAC's `SYNC` is held **asserted** in the design's declared normal resting state | **high** |
| A7-4 | DAC `SCLK`/`DIN`/`SYNC` | ADR 0004's `V_IH` is the wrong datasheet row — 0.625 × AVDD, not 0.7 × AVDD | **high** |
| A7-5 | pitch jack at power-on | ADR 0006's power-on table contradicts itself 30 lines later; the corrected value lives only in `pitch-stage.md` | **high** |
| A7-6 | `loop-budget` | The tracked value is not reproducible from its own derivation, and 4 kHz does not close once the page's own firmware terms are added | **high** |
| A7-7 | SPI2 host | ADR 0007 puts the 64-pixel matrix on SPI2; nothing reconciles it | **high** |
| A7-8 | firmware obligations | Six hardware-derived firmware requirements, none in `firmware/README.md`; one is cited *as if* it were | **high** |
| A7-9 | ADR 0004 watchdog scope | "SPI stops, `CLR` fires" still asserted in the present tense; nothing asserts `CLR` | **med-high** |
| A7-10 | DAC-side `R-SPI-PULL` | Justified by a state (`OE` disabled) that the same page deletes; the real case is unstated | **med** |
| A7-11 | `CLR` / `LK-CLR` | `CLR` is falling-edge triggered; the hand-assert pad cannot hold a clear against the running loop | **med** |
| A7-12 | `SYNC` glitch model | The "every bit lands in the wrong field" mechanism is refuted by SBAS430E | **med** |
| A7-13 | bus +5 V | The module is silently inoperative in a case with no +5 V on the bus; the open item does not say so | **med** |
| A7-14 | `R-SPI-SER` | The "40 mA pad spec" has no source, no banked datasheet, and is firmware-settable | **med** |
| A7-15 | ADC read | `latency-budget.md`'s ADC row does not produce its own number, and disagrees with `spi-link.md` | **med** |
| A7-16 | IMU | The QMI8658C read is booked nowhere in the latency budget | **med** |
| A7-17 | `U-LVL-MOD`, `U-DAC` | Both active parts of this path sit in `unplaced.csv`, which is defined as parts no page draws | **med** |
| A7-18 | 74AHCT14 proposal | "One part, three jobs" does not close on gate count or polarity | **med** |
| A7-19 | `U-TVS-SPI` | The "~29 ns of edge" figure is not reproducible | **low-med** |
| A7-20 | buffer spare gate | The unused input's tie exists only in a BOM note | **low** |
| A7-21 | drawing net names | DAC-side pulls labelled with cable-side net names | **low** |
| A7-22 | *(outside slice)* | `ROADMAP.md` E12 still reasons at 8HP | **low** |

---

## 1. Signal integrity

### A7-1 — `SCLK` / `MOSI` / `CS`, `R-SPI-SER`: the decision table needs two contradictory driver models **[high]**

The 100 Ω choice is stated in four places with the same table
`[repo] hardware/interfaces/spi-link/spi-link.md:60-76`,
`[repo] docs/decisions/0004-cv-interface-module.md:79-88`,
`[repo] hardware/interfaces/spi-link/bom.csv:3`,
`[repo] config/figures.yaml` (`spi-series-r`).

**Threshold, verified.** `V_IH` min = **2 V** and `V_IL` max = **0.8 V**,
Recommended Operating Conditions, both SN54 and SN74 columns, at
V_CC = 4.5–5.5 V `[datasheet] SCLS264O, Recommended Operating Conditions`.
TTL levels, not ratioed to V_CC. **The corpus's 2.0 V is correct.**

**The far-end arithmetic.** For a step `V` into a line of impedance `Z0`
through a total source resistance `R_drv + R_s`, the launched step is
`V·Z0/(Z0+R_drv+R_s)`, and at a high-impedance CMOS far end the reflection
coefficient is ≈ +1, so the first step seen by the receiver is twice that.
With `V` = 3.3 V and `Z0` = 100 Ω `[calc]`:

| `R_s` | `R_drv` = 0 | `R_drv` = 35 Ω | `R_drv` = 40 Ω |
|---|---|---|---|
| 220 Ω | **2.06 V** | 1.86 V | 1.83 V |
| 100 Ω | 3.30 V | 2.81 V | **2.75 V** |
| 68 Ω | 3.30 V | **3.25 V** | 3.17 V |
| 60 Ω | 3.30 V | 3.35 V* | **3.30 V (exact match)** |

*(\*clipped at the rail; a slightly under-damped source.)*

The corpus's three published numbers are **1.83–1.86 V**, **2.75 V** and
**3.25 V** `[repo] spi-link.md:69-72`. Reading back: the 220 Ω row needs
`R_drv` ≈ 35–40 Ω, the 100 Ω row needs **exactly 40 Ω**, and the 68 Ω row
needs **exactly 35 Ω**. So:

1. **A driver output impedance of 35–40 Ω is load-bearing and is stated in no
   document in the corpus.** `[repo]` — grepped `hardware/**`,
   `docs/decisions/**`, `docs/reference/**`, `config/**`, `firmware/**`,
   `README.md`, `ROADMAP.md`; there is no output-impedance figure for the
   ESP32-S3 pad anywhere, and no ESP32-S3 datasheet is banked
   `[repo] datasheets/MANIFEST.csv`.
2. **With that number removed, the case against 220 Ω collapses.** At
   `R_drv` = 0 the 220 Ω first step is **2.06 V**, which is *above* the 2.0 V
   `V_IH`, not 170 mV below it `[calc]`. The whole 220 Ω → 100 Ω revision —
   which propagated into ADR 0004, `spi-link.md`, the BOM row and the figure
   register — rests on an unstated assumption.
3. **The three rows are not mutually consistent**: 40 Ω for one row and 35 Ω
   for another. Small, but it means no single stated model reproduces the
   table.

**The current rows use the opposite model, and that is the real defect.**
"48 mA fault current against a 40 mA pad spec" for 68 Ω, and "33 mA into a
clamp" for 100 Ω `[repo] spi-link.md:71-74`. These are
`[calc] 3.3/68 = 48.5 mA` and `[calc] 3.3/100 = 33.0 mA` — i.e. computed with
`R_drv = 0`, the very value the voltage rows need to be non-zero. Under the
table's own 35–40 Ω driver, `[calc] 3.3/(68+37.5) = 31.3 mA` and
`3.3/(100+37.5) = 24.0 mA`: **68 Ω does not exceed a 40 mA limit**, and the
only stated reason to reject it disappears.

**Where a consistent analysis lands.** Taking `R_drv` = 40 Ω throughout, a true
source match is `R_s` = `Z0` − `R_drv` = **60 Ω**, giving a single clean 3.30 V
step and no reflections at all `[calc]`. **68 Ω is the nearest E24 value to
that**, gives 3.17 V in one step, a source reflection coefficient of
`[calc] (108−100)/(108+100) = 0.038`, and 31 mA of short-circuit current.
100 Ω is not a source match — it is 140 Ω into a 100 Ω line, ρ = +0.167, which
settles in three transits (2.75 → 3.21 → 3.28 V `[calc]`) rather than one.
The page calls it "a source match into the cable's own impedance"
`[repo] docs/decisions/0004-cv-interface-module.md:84`; on the page's own
arithmetic it is not one.

**The conclusion may still be 100 Ω** — it is above threshold on the first step
under every model, it is a common value, and 68 Ω's advantage is small. But
the derivation as written cannot be audited, and per `CLAUDE.md` an unmarked
assumption of this weight is itself the defect. **What is needed: state the
assumed pad output impedance, with a source, and recompute both halves of the
table under it.**

### A7-14 — `R-SPI-SER`: the "40 mA pad spec" is unsourced and is a firmware setting **[med]**

The number appears exactly once in the corpus, unqualified
`[repo] hardware/interfaces/spi-link/spi-link.md:71`, and once more in the BOM
note `[repo] hardware/interfaces/spi-link/bom.csv:3`. No ESP32-S3 datasheet is
banked `[repo] datasheets/MANIFEST.csv` — the only S3 artefacts are the
Waveshare board schematic and pin dump. Per `CLAUDE.md` §3 this is exactly the
shape that has cost this project three figures in one afternoon.

Two things follow that the corpus does not say `[from memory]`: the ESP32-S3
pad's drive is **selectable** (nominal 5/10/20/40 mA settings), so both the
output impedance A7-1 needs and the current limit A7-1 tests against are set
by `gpio_set_drive_capability()` at runtime. **The termination value therefore
depends on a firmware setting that no document names** — see A7-8.

### Edge rate at the receiver — checked, and it passes

SCLS264O carries a spec the corpus never cites: **input transition rise/fall
rate `Δt/Δv` ≤ 20 ns/V, max**
`[datasheet] SCLS264O, Recommended Operating Conditions`. Checking it against
this slice `[calc]`:

- At 100 Ω the far end resolves in one 2–5 ns step, so crossing the 1.2 V band
  from `V_IL` to `V_IH` takes 2–5 ns → **~2–4 ns/V**. Comfortable.
- At 220 Ω the first step stalls at 1.83 V and the second arrives ~20 ns later,
  so the 0.8 → 2.0 V crossing takes ≈ 20 ns → **~17 ns/V**, inside the 20 ns/V
  limit but with 15 % margin.

So the rejected 220 Ω case was marginal against a *second*, independent spec
as well. Worth adding, because it is a stronger argument than the one made and
it comes off the banked document.

### A7-19 — `U-TVS-SPI`: the "~29 ns of edge" figure is not reproducible **[low-med]**

The BOM row states 30 pF per channel and concludes "against 2m of Cat5 and
R-SPI-SER this is ~29ns of edge on a 250ns half-period at 2MHz"
`[repo] hardware/interfaces/spi-link/bom.csv:4`. The array sits at the
**driving** end, where it is a lump in parallel with the line's 100 Ω and the
source. `[calc]` τ = 30 pF × (140 Ω ∥ 100 Ω) = 30 pF × 58.3 Ω = **1.75 ns**;
even taking the full source resistance alone, 30 pF × 220 Ω = 6.6 ns. Nothing
in the model produces 29 ns. This matters because the same decision rejects
220 Ω on a 20 ns dwell — a genuine 29 ns of edge degradation would be the
larger term, and 1.8 ns is not a term at all.

---

## 2. The pull network — six pulls, and the two that do not work

`R-SPI-PULL`, 10 k × 6, three on each side of the buffer, `CS` up, `SCLK` and
`MOSI` down `[repo] hardware/interfaces/spi-link/spi-link.md:118-125`,
`[repo] hardware/module/digital-and-supervision/digital-and-supervision.md:50-60`,
`[repo] hardware/interfaces/spi-link/bom.csv:2`.

**Polarity is consistent everywhere and is correct.** `CS` up holds `SYNC`
de-asserted; `SCLK`/`MOSI` down hold an idle bus. Checked across all four
places; no disagreement.

### A7-2 — cable-side `CS` pull-up: cannot do its job, and names a rail the module does not have **[high]**

The state it exists for is named explicitly: *"The panel switch cuts +12 V to
the umbilical while the module stays powered from the bus. So the ordinary
powered-down state is: module alive, DAC alive, and SCLK / MOSI / CS floating
at the level shifter's inputs. That is a designed-in operating mode, not a
fault case, and it is the state the instrument spends most of its life in."*
`[repo] docs/decisions/0004-cv-interface-module.md:377-383`

In that state the instrument is fully unpowered — it takes all of its power
down the umbilical `[repo] docs/decisions/0004-cv-interface-module.md:96`.

The correction currently on record is: *"the cable-side `CS` pulls to **3V3,
not +5 V**: pulled to 5 V it drives 430 µA continuously through the unpowered
ESP32's input clamp"* `[repo] docs/decisions/0004-cv-interface-module.md:399-403`,
repeated in the BOM row, which adds *"and the node sits at ~0.7V so 'CS idle
high' is not even achieved"* `[repo] hardware/interfaces/spi-link/bom.csv:2`.

**Three things are wrong with that.**

1. **There is no 3.3 V rail on the module.** The module's rails are +12 V,
   −12 V, bus +5 V (74AHCT125 only) and the LM317's 5.21 V AVDD
   `[repo] hardware/module/power-entry/power-entry.md:23-32,42,74`. A grep of
   `hardware/module/**` for `3V3` / `3.3 V` returns **zero hits** `[repo]`.
   The instruction is unbuildable where the part sits.
2. **Sourcing it from the instrument's 3V3 inverts the polarity.** If the
   pull-up is moved to the carrier, then in exactly the state it exists for
   the instrument's 3V3 is 0 V, and a 10 k resistor to 0 V is a pull-**down**
   on `CS` — worse than no pull at all.
3. **Changing the rail does not fix the stated symptom anyway.** The node sits
   at ~0.7 V because a 10 k resistor is fighting the ESP32 pad's ESD diode into
   a dead rail. `[calc]` from 3.3 V the same clamp gives (3.3−0.7)/10 k =
   **260 µA** and the node still sits at ~0.7 V. The 430 µA becomes 260 µA;
   "`CS` idle high" is still not achieved. The fix as written buys a 40 %
   current reduction and nothing else.

Note also that the pull-up rail is **not** a hazard at the buffer: SCLS264O
specifies `I_IK` for `V_I < 0` **only**, against `I_OK` specified for
`V_O < 0` *or* `V_O > V_CC`, and specifies input leakage at `V_I` = 5.5 V with
`V_CC` = 0 V `[datasheet] SCLS264O, Absolute Maximum Ratings and Electrical
Characteristics`. There is no clamp to V_CC. So a +5 V pull-up is safe at the
74AHCT125; **the entire problem is 2 m away at the ESP32**, and no choice of
rail at the module end escapes it.

### A7-3 — `SYNC`: the DAC's frame is held **asserted** in the design's normal resting state **[high]**

Following A7-2 through the buffer `[calc]`, with `OE` tied enabled and the
buffer powered from bus +5 V:

| State | `CS` at buffer in | Buffer | `SYNC` at DAC | `SCLK` at DAC |
|---|---|---|---|---|
| Both powered, loop running | driven | enabled | driven | driven |
| **Module on, instrument off, cable connected** *(the declared normal state)* | **~0.7 V — a valid AHCT LOW (`V_IL` max 0.8 V)** | enabled | **driven LOW — asserted** | 0 V |
| Cable unplugged | 10 k to +5 V → 5 V | enabled | driven HIGH ✓ | 0 V |
| Bus +5 V absent | ~0.7 V | unpowered, Hi-Z | 10 k to AVDD → 5.21 V ✓ | 0 V |

So the one case the network was bought for is the one it fails, and the two it
handles are a disconnected cable and an unpowered buffer.

`SYNC` low means the DAC's 32-bit shift register is **open**: SBAS430E, *"The
input shift register is 32-bits wide… Data from the D_IN line are clocked into
the 32-bit shift register on each falling edge of SCLK"*, gated by `SYNC` low
`[datasheet] SBAS430E, Serial Interface`. The only thing then standing between
the module and a latched garbage word is a 10 k pull-down holding a 2 m open,
unterminated, undriven twisted pair below the AHCT125's 2.0 V `V_IH` — the
`SCLK`/`MOSI` pair, which shares the cable with nothing else driving it.
ADR 0004 states the hazard in exactly these terms — *"a stray edge on CS
latches a garbage word into the pitch DAC"*
`[repo] docs/decisions/0004-cv-interface-module.md:385` — and the six pulls as
specified do not prevent it; they park the circuit one noise edge closer to it
than a floating `CS` would.

This is also the one failure the corpus already identifies as **sticky**: no
`MISO`, so firmware cannot discover it, and a mis-framed word can carry the
software-reset and reference-enable bits
`[repo] hardware/interfaces/spi-link/spi-link.md:99-107`.

**Candidate directions, none of them costed here:** hold `SYNC` at the DAC
rather than at the buffer input (which requires the buffer's output to be
undriven in that state — i.e. `OE` gating, the thing that was deleted, or
gating the buffer's V_CC); or block the cable with a series diode at the
cable-side pull-up; or accept `SYNC` low and make the `SCLK` hold far stiffer
than 10 k. This is a real open question, not a wording fix.

### A7-10 — DAC-side `R-SPI-PULL`: justified by a deleted state **[med]**

*"**with `OE` disabled the buffer's outputs are Hi-Z**, so the pins actually
floating in that state are the DAC's `SCLK`, `DIN` and `SYNC` — which is the
state the pulls were bought for"*
`[repo] hardware/interfaces/spi-link/spi-link.md:112-117`, and verbatim in the
BOM row `[repo] hardware/interfaces/spi-link/bom.csv:2`.

`OE` is tied to GND, permanently enabled, on the same page
`[repo] .../digital-and-supervision.md:58`, in the ADR
`[repo] docs/decisions/0004-cv-interface-module.md:441`, and in the BOM row for
the buffer `[repo] hardware/unplaced.csv:20`. **The stated justification is a
state that cannot occur.** This is the `mod-channels.md` failure class named in
`CLAUDE.md` §5, in a 2026-09-21 page.

The parts are probably still right, for a reason nobody has written down: the
buffer runs on **bus +5 V** while the DAC runs on the **LM317's AVDD off
+12 V** `[repo] hardware/module/power-entry/power-entry.md:42,74`. Those are
different rails with different sources, so the buffer can be unpowered while
the DAC is alive — at power-up sequencing, and permanently in a case with no
+5 V (A7-13). In that state the buffer's outputs are undriven and the DAC-side
pulls are the only thing holding `SYNC`. **That is the argument, and it should
replace the refuted one.**

### A7-13 — bus +5 V: the module does not work in a case that has no +5 V **[med]**

The "Still open — the bus +5 V rail" item gives three reasons to drop it:
reversed-ribbon danger, zero of eight surveyed designs taking a sub-12 V bus
rail, and no reverse protection
`[repo] hardware/module/digital-and-supervision/digital-and-supervision.md:88-97`.

It does not give the fourth and most concrete one. Many Eurorack cases and DIY
bus boards do not distribute +5 V at all `[from memory]`. In such a case the
74AHCT125 is unpowered, its outputs are undriven, the DAC-side pulls hold
`SYNC` high and `SCLK`/`DIN` low, and **the module accepts nothing and outputs
nothing** — silently, with the panel power LED lit from +12 V
`[repo] hardware/module/panel-led/panel-led.md`. Deriving the 5 V locally from
the protected +12 V, which the open item already proposes as "one TO-92 and two
capacitors", removes a whole class of "it doesn't work in my rack". Worth
adding to the item; it is the reason a user would hit, not just the reason a
reviewer would.

### A7-20 / A7-21 — two small ones **[low]**

- **The spare gate's input tie is only in a BOM note.** SCLS264O Note 4: *"All
  unused inputs of the device must be held at V_CC or GND to ensure proper
  device operation"* `[datasheet] SCLS264O, Recommended Operating Conditions,
  Note 4`. The BOM row carries it — *"tie every unused input to VCC or GND"*
  `[repo] hardware/unplaced.csv:20` — but the schematic drawing shows only
  `OE x4 → GND` `[repo] .../digital-and-supervision.md:56-58` and does not
  show the fourth gate's `A` input. A board laid out from the drawing floats
  it. Same applies to `U-LVLSHIFT`'s two spare gates on the carrier.
- **The DAC-side pulls are drawn with cable-side net names.** The drawing
  labels both triplets `SCLK↓ MOSI↓ CS↑`
  `[repo] .../digital-and-supervision.md:53,59-60`, while both Interfaces
  tables name the buffer's outputs `SCLK`, `DIN`, `SYNC`
  `[repo] .../digital-and-supervision.md:24`,
  `[repo] hardware/module/dac8568/dac8568.md:15`. Cosmetic, but it is the kind
  of slip that makes a netlist review miss a polarity.

---

## 3. `CLR`, `LDAC`, and what the jacks do at power-on

### Verified correct — the `LDAC` strap and the `CLR` pull-up

Both were corrected on 2026-09-21 and both corrections check out against the
banked datasheet.

- **`LDAC` = 0 Ω strap to GND.** SBAS430E: *"For such synchronous updates, the
  LDAC pin is not required and it must be connected to GND permanently."* And:
  *"If the LDAC register bit is set to '1', it overrides the LDAC pin (the
  LDAC pin is internally tied low for that particular DAC channel)"*, with the
  register defaulting to `0x00`
  `[datasheet] SBAS430E, LDAC Function / Synchronous vs Asynchronous Mode`.
  `[repo] hardware/module/dac8568/dac8568.md:37-39`,
  `[repo] hardware/module/dac8568/bom.csv:3`. **Correct, and the reasoning for
  why the old pull-up was fatal is correct.**
- **`CLR` pulled high, inactive, with `LK-CLR` to GND.** Active low, and on a
  C-grade part the default clear code is zero scale: *"When performing a
  software reset of the device, the clear code register is set back to its
  default mode (DB1 = DB0 = '0')"*, and DB1 = DB0 = '1' *"ignores any activity
  on the external CLR pin"*
  `[datasheet] SBAS430E, Clear Code Register and CLR Pin`. The BOM row's
  *"Leave the DAC's clear-code register at its default… Do NOT write
  ClearIgnore"* `[repo] hardware/module/dac8568/bom.csv:2` is exactly right.
- **C-grade POR is to zero scale**, verbatim: *"power on reset to zero scale
  for grades A and C; power on reset to midscale for grades B and D"*
  `[datasheet] SBAS430E, Power-On Reset`. **The corpus's grade lock is
  correct** `[repo] hardware/unplaced.csv:6`.

### A7-11 — `LK-CLR` cannot hold a clear against the running loop **[med]**

SBAS430E: *"The CLR pin is **falling-edge triggered**; therefore, the device
exits clear code mode on the **32nd falling edge of the next write
sequence**."* `[datasheet] SBAS430E, Clear Code Register and CLR Pin`

`LK-CLR` is described as the hand assert for E7–E10 bring-up
`[repo] hardware/module/dac8568/bom.csv:2`,
`[repo] hardware/module/link-supervision/link-supervision.md:24`,
`[repo] firmware/README.md:60-63`. With the 4 kHz loop running, shorting the
pad produces **one clear that is undone 250 µs later** by the next word — it
is a 250 µs blip on the jacks, not a held state `[calc]`. The affordance only
does what the corpus expects of it when firmware is stopped or is not writing
that channel. Nowhere is that said.

This also sharpens `firmware/README.md`'s statelessness argument in the right
direction: the *hardware does* require refresh-everything, because a `CLR` is
self-clearing and undetectable, so a firmware that refreshed only on change
would carry a zeroed channel 7 forward indefinitely
`[repo] firmware/README.md:47-80`. **The rule is correct and the hardware does
require it.** Verified.

### A7-12 — the `CS`-glitch mechanism is refuted by the banked datasheet **[med]**

The corpus states: *"A glitch restarts the bit count mid-message, so every bit
lands in the wrong field — including the software-reset and
internal-reference-enable bits"*
`[repo] hardware/interfaces/spi-link/spi-link.md:99-104`, and this is the
stated reason `CS` gets the ground partner on pins 7/8
`[repo] config/figures.yaml` (`umbilical-pinmap` derivation).

SBAS430E says the opposite of the first half: *"if SYNC is brought high before
the 31st falling edge, it acts as an **interrupt** to the write sequence; the
shift register resets and the write sequence is discarded. Neither an update
of the data buffer contents, DAC register contents, nor a change in the
operating mode occurs."* And, past the 32nd edge, *"the first 32 bits of data
are latched into the shift register and any further clocking of data is
ignored."* `[datasheet] SBAS430E, Serial Interface / SYNC Interrupt`

So a `SYNC` glitch **high** mid-frame is **benign** — it discards the word,
which self-heals on the next pass 250 µs later. The dangerous case is narrower:
a glitch that goes high *and back low* inside a frame, which restarts framing
and can execute one garbage word.

**The conclusion survives** — the pin map should still pair `CS` with
`DIG_GND` — but the mechanism as written is refuted by the part's own
datasheet, and per `CLAUDE.md` §3 the banked document wins. The narrower
mechanism is still enough to justify the pairing and should replace it.

### A7-4 — the DAC's `V_IH` is 0.625 × AVDD, not 0.7 × AVDD **[high]**

ADR 0004: *"Its job is to get 3.3 V logic over the DAC's 0.7 × AVDD input
threshold — **3.65 V at AVDD = 5.21 V**"*
`[repo] docs/decisions/0004-cv-interface-module.md:208-210`. This is the number
that justifies the level shifter's existence.

SBAS430E's Electrical Characteristics splits the parameter into **two rows**:

> `V_INH` Logic input HIGH voltage … **0.7 × AV_DD** V
> `V_INH` Logic input HIGH voltage, **4.5 V ≤ AV_DD ≤ 5.5 V** … **0.625 × AV_DD** V

`[datasheet] SBAS430E, Electrical Characteristics — Logic Inputs`. The revision
history confirms this was a deliberate split: *"Split Input HIGH Voltage
parameter test condition into two rows"*, and separately *"Changed Input HIGH
Voltage parameter minimum value from 1.8 to 0.7 × AV_DD"*
`[datasheet] SBAS430E, Revision History`.

At AVDD = 5.21 V the applicable row is the second: `[calc]` 0.625 × 5.21 =
**3.256 V**, not 3.65 V. **The corpus is quoting the wrong row, by ~0.4 V, on
the figure that motivates the part.**

Consequences:

- **The buffer is still needed** — AVDD may be selected up to 5.5 V at E7
  (`[calc]` 0.625 × 5.5 = 3.44 V > 3.3 V), and an ESP32 pad under load does
  not deliver a clean 3.3 V anyway. The decision survives; the number does not.
- But the margin story changes materially: the corpus believes it is 350 mV
  short of direct drive when it is 44 mV short at nominal. Anyone re-deriving
  from 3.65 V will reach wrong conclusions about rail sag and about whether a
  3.3 V DAC was ever viable.
- **Related, unstated:** the DAC's `SYNC`, `SCLK` and `D_IN` are
  **Schmitt-trigger inputs** `[datasheet] SBAS430E, Pin Functions`. The "no
  hysteresis" problem is entirely at the 74AHCT125's inputs, not at the DAC —
  relevant to A7-18.

### A7-5 — the pitch jack's power-on state: ADR 0006 contradicts itself and the fix landed elsewhere **[high]**

ADR 0006's power-on table, the corpus's answer to "what does every jack do at
power-on":

> | **Pitch** | Bottom of its range, below −2 V | Subsonic. A VCO there is inaudible |

`[repo] docs/decisions/0006-cv-channel-allocation.md:197-199`

Thirty lines below, the same ADR: *"the internal reference is disabled by
default and needs an explicit enable write at boot… It also means the outputs
sit at **0 V** from rack power-on until firmware enables the reference, **which
happens to reinforce the table above**."*
`[repo] docs/decisions/0006-cv-channel-allocation.md:226-230`

Those two statements are 2.5 V apart and the second claims to agree with the
first. `pitch-stage.md` derives it independently and says so plainly:
*"**Power-on is 0.000 V, not 'subsonic'.** … so both terms are zero and the
jack sits at 0 V, a VCO's base note, until that write. After it, `CLR` parks at
−2.500 V. ADR 0006's power-on table asserts 'below −2 V' for both; they are
different states, 2.5 V apart."*
`[repo] hardware/module/pitch-stage/pitch-stage.md:134-139`

**Datasheet check:** *"at power up the internal reference is powered down until
a valid write sequence is applied to power up the internal reference"*, and the
part is described on page 1 as having a *"2.5 V reference voltage (disabled by
default)"* `[datasheet] SBAS430E, Features / Internal Reference`. **The
correction is right and the ADR's table is wrong.**

The behavioural consequence is not cosmetic: the table's whole justification is
"subsonic, inaudible", and the true state is a **playable note at 0 V** on a
patched VCO from the moment the rack powers up until firmware's first write.
`ROADMAP.md` E7 and the first-power-on discussion rely on the table
`[repo] ROADMAP.md:48`. This is the named failure mode exactly: the fix landed
in the page being edited and not in the document the reader opens.

*(`breath-receive-stage.md` gets this right and cites the same mechanism when
rejecting `VREFOUT` as the breath offset reference
`[repo] hardware/module/breath-receive-stage/breath-receive-stage.md:231-235`.
So the corpus knows the fact in three places and the owner table still
contradicts it.)*

### A7-8 — firmware's obligations are not where firmware can see them **[high]**

The slice brief asks whether firmware's obligations are stated where firmware
can see them. **Six hardware-derived, load-bearing requirements were found.
`firmware/README.md` carries one of them.** Grepped `firmware/README.md` for
each `[repo]`:

| Obligation | Stated in | In `firmware/README.md`? |
|---|---|---|
| Refresh all six populated channels every pass | `firmware/README.md:47-80` | **yes** — and correct |
| **The reference-enable must be firmware's first DAC write**, before any channel data | `hardware/module/pitch-stage/pitch-stage.md:143-146` | **no** |
| Use SW-LDAC ("update all DAC registers") as the last word of each pass, so the six channels move together and the `CLR`-exit window goes to zero | `hardware/module/dac8568/bom.csv:3` (a **generated** file's note) | **no** |
| Leave the clear-code register at default; **do not write ClearIgnore** | `hardware/module/dac8568/bom.csv:2` (generated) | **no** |
| Set `clock_speed_hz` **per device** on the shared SPI2 host — 2 MHz DAC, 0.9 MHz ADC | `hardware/interfaces/spi-link/spi-link.md:108-111`, which itself says *"It is written nowhere."* | **no** |
| Use **polling** transactions on an acquired bus, not interrupt — *"not an optimisation here; they are what makes 4 kHz reachable at all"* | `docs/reference/latency-budget.md:155-158` | **no** |
| The DAC service routine belongs in **IRAM** (NVS/OTA writes disable the instruction cache) | `hardware/module/digital-and-supervision/digital-and-supervision.md:80-86` | **no** |

Two of these are worse than merely absent:

1. **`pitch-stage.md` cites `firmware/README.md` as carrying the first-write
   rule** — *"it is in the sticky-register set that gets periodically refreshed
   (`firmware/README.md`)"*
   `[repo] hardware/module/pitch-stage/pitch-stage.md:145-146`. The *periodic
   refresh* half is there; the ***first*** *write* half, which is the half that
   decides the power-on state of the pitch jack, is not. A reader following the
   citation finds a rule that does not say what they were told it says.
2. **Two of them live only in `hardware/bom.csv` notes**, which `CLAUDE.md` §
   *Hardware conventions* identifies as a generated file. They are safe in the
   fragment, but a firmware author will never open a BOM fragment.

This is the same defect the repository's own §1 is built to prevent, applied to
requirements rather than to numbers. **`firmware/README.md` is where the
reader looks.**

---

## 4. The timing budget — one pass, re-derived

`loop-budget` = "196-241 us of 250 us", owner `docs/reference/latency-budget.md`
`[repo] config/figures.yaml` (`loop-budget`);
`[repo] docs/reference/latency-budget.md:146-149`.

### The bus time reproduces

`[calc]`, at the stated clocks:

```
DAC   6 words x 32 bits / 2.0 MHz   = 192 bits / 2.0e6   =  96.00 us
ADC   18 clocks / 0.9 MHz           =                    =  20.00 us
 or   24 clocks / 0.9 MHz           =                    =  26.67 us
keys  32 bits / 1.0 MHz             =                    =  32.00 us
                                      bus total  = 148.00 - 154.67 us
```

This matches the derivation field's "Bus time 148-155 us" exactly, and it
identifies where the 7 µs spread comes from — **the 18-vs-24-clock
disagreement in A7-15**, which nothing states as the source of the range.

### A7-6 — the published value does not follow from the published derivation **[high]**

The derivation field gives only: *"Bus time 148-155 us PLUS ESP-IDF
per-transaction overhead (24 us interrupt / 9 us polling)"*
`[repo] config/figures.yaml` (`loop-budget`).

A pass has **eight** transactions: six DAC words (each needs its own `SYNC`
frame — SBAS430E requires `SYNC` low for exactly 32 falling edges per word
`[datasheet] SBAS430E, Serial Interface`), one ADC read, one key-chain read.
`[calc]`:

| Model | Overhead | Pass | Duty |
|---|---|---|---|
| All polling, 8 × 9 µs | 72 µs | **220.0 – 226.7 µs** | 88 – 91 % |
| All interrupt, 8 × 24 µs | 192 µs | 340.0 – 346.7 µs | 136 – 139 % |

**Neither bracket is 196–241 µs.** The published range is 45 µs wide, while
the only stated source of spread (the ADC clock count) is 6.7 µs wide, so the
range's *width* is unexplained as well as its endpoints. `[calc]`
196 − 148 = 48 µs and 241 − 155 = 86 µs; 48 is not an integer multiple of 9 or
24, and neither is 86.

**The "291 µs with driver defaults" figure is reproducible, but only by
dropping the key-chain read.** `[calc]` SPI2 bus alone (96 + 26.67 = 122.67 µs)
plus **seven** interrupt transactions (7 × 24 = 168 µs) = **290.67 µs**. That
is the only clean fit found. It excludes both the key chain's 32 µs of bus time
and its transaction overhead — while the same paragraph adds the key chain's
32 µs explicitly `[repo] docs/reference/latency-budget.md:146-148`. So the
figure's two published numbers are computed on two different inventories of the
pass.

This is the second time this figure has been found not to match its owner
`[repo] config/figures.yaml` (`loop-budget`, `escape_note`). The `escape_note`
records that the owner did not *state* the value. It is now also the case that
the value does not **follow** from the derivation — which the owner-check
cannot see either, because the check matches tokens, not arithmetic.

### Does 4 kHz close? On the corpus's own numbers, **no**

Take the most favourable reproducible model — all-polling, ADC at 18 clocks:
**220 µs of the 250 µs period, 30 µs left** `[calc]`.

`latency-budget.md` then books, in its own tables, two firmware terms that both
occur every pass:

- *"SPI to MCU + firmware | < 20 µs"* (breath digital path)
  `[repo] docs/reference/latency-budget.md:69`
- *"Firmware note resolution | < 20 µs"* (key path)
  `[repo] docs/reference/latency-budget.md:107`

`[calc]` 220 + 20 + 20 = **260 µs against a 250 µs period.** At the pessimistic
bus end, 227 + 40 = 267 µs. **The loop does not close**, before any of: 21-key
debounce state machines, the fingering lookup, four mod channels of
scale/offset/curve/slew, breath scaling, the UART frame to the display board,
USB MIDI when enabled, and the IMU (A7-16).

The page's own warning already says where this lands — *"if the measured round
trip comes back near 200 µs, **the answer is not a faster ADC — it is that
4 kHz does not close and the loop rate has to move**"*
`[repo] docs/reference/latency-budget.md:176-179`. **That conclusion is
already reachable from the figures on the page, without waiting for a
measurement.** The honest statement is not "196–241 µs, tight"; it is "220–227
µs of bus and driver time, leaving under 30 µs for all firmware, which the
page's own firmware rows already exceed."

**This is a gate on the architecture, and it should be stated as one before
E11**, not as a measurement to be taken later. Options visible from here:
drop to 2 kHz for the mod channels while keeping pitch at 4 kHz; batch the six
DAC words into one queued transaction sequence to amortise the per-transaction
overhead; move the key chain to DMA on SPI3 so its 32 µs genuinely overlaps.
None is costed anywhere.

### A7-15 — the ADC row does not produce its own number **[med]**

`latency-budget.md`: *"SAR ADC conversion | **~24 µs** | **18 clocks** at the
MCP3202's ~0.9 MHz ceiling on 3.3 V"*
`[repo] docs/reference/latency-budget.md:68`. `[calc]` 18 / 0.9 MHz = **20.0 µs**,
not 24 µs. The row's stated clock count and its stated time disagree by 20 %.

`spi-link.md` books the same read as *"24 clocks @ 0.9 MHz = 26.7 µs"*
`[repo] hardware/interfaces/spi-link/spi-link.md:126`. `[calc]` 24 / 0.9 =
26.67 µs ✓ — that one is self-consistent, and 24 clocks (three SPI bytes) is
the realistic figure for a byte-oriented host `[from memory]`.

Three numbers for one read: 20 µs (implied), 24 µs (stated), 26.7 µs (stated
elsewhere). The `loop-budget` register silently uses the outer two as a range
without saying so.

### A7-16 — the IMU is booked nowhere **[med]**

The QMI8658C is an **I²C** part on GPIO11/12
`[repo] docs/decisions/0007-imu-selection.md:166-168`,
`[repo] docs/decisions/0013-two-mcu-split.md:51`, and IMU tilt is a routing-matrix
modulation source `[repo] docs/decisions/0007-imu-selection.md:138`,
`[repo] firmware/README.md` (routing matrix), and a lighting source
`[repo] docs/decisions/0014-lighting.md:324`.

`latency-budget.md` has **no row for it**, in either path table or in rule 1
`[repo] docs/reference/latency-budget.md`. `[calc]` a 6-axis burst read is
~13 bytes × 9 bit-times: at 400 kHz fast-mode that is **293 µs**; at 100 kHz,
1.17 ms. **Either is longer than the entire 250 µs loop period.** The read must
therefore be decimated across passes or moved off the real-time core, and
nothing says which. At 1-in-10 decimation it is still ~29 µs per pass on
average — comparable to the entire remaining margin computed above.

---

## 5. Supervision — is what replaces the deleted parts adequate?

`hardware/module/link-supervision/link-supervision.md` is, on its own terms,
one of the better documents in this corpus. The **"NOT FITTED"** header, the
honest coverage table, and the 2026-09-21 blockquote correcting "for no new
parts" into "four parts, none of which has a BOM row today" are exactly the
discipline `CLAUDE.md` asks for `[repo] .../link-supervision.md:1-9,89-99`.
The costed restoration is credible and I found nothing wrong with its
arithmetic.

**Is the replacement adequate?** The page's own table answers it honestly:
four failure modes went from "caught" to "not caught", and the everyday one is
stated plainly — *"pull the umbilical mid-note and the rack holds that note
until you flip the module's toggle"*
`[repo] .../link-supervision.md:70-80`. I agree with the deletion of the
watchdog on the stated grounds (it counted `CS` edges and so could never catch
the hang it was named for, and its 99 ms timeout would have fought E7–E10). I
do **not** think the corpus has established that losing the *link* coverage is
acceptable; it has established that it is **known**, which is different and is
what the open item correctly says.

One thing the page does not weigh: with A7-3 unresolved, "module alive,
instrument off" is not a quiescent state but one with `SYNC` asserted. A
restored presence detect would fix A7-3 as a side effect, which strengthens
the restoration case materially. That connection is not drawn anywhere.

### A7-9 — ADR 0004 still reasons as though `CLR` fires **[med-high]**

The section *"#### The watchdog's scope is the DAC channels, and breath is
outside it"* `[repo] docs/decisions/0004-cv-interface-module.md:505-529` is
**not struck through** and is written throughout in the present tense. Its
central sentence:

> *"on a sagging cable the buck drops out at 8 V while the REF5050 and OPA2197
> hold regulation to ~7.2 V, so the MCU dies, SPI stops, **`CLR` fires**, and
> breath keeps working."* `[repo] docs/decisions/0004-cv-interface-module.md:521-523`

**`CLR` does not fire.** Nothing drives it: `R-CLR-PU` holds it inactive and
the only assertions are the DAC's own POR and the `LK-CLR` pad
`[repo] hardware/module/dac8568/dac8568.md:15`,
`[repo] hardware/module/link-supervision/link-supervision.md:56-58`,
`[repo] hardware/module/mod-channels/mod-channels.md:157-163`. On that fault
the pitch and four mod jacks **hold their last value indefinitely** — which is
the opposite of what this paragraph concludes, and the paragraph is offered as
the answer to "three reviewers read the omission as a hole".

The blockquote above it does say the paragraphs *"are kept because the problem
they describe is still real"*
`[repo] docs/decisions/0004-cv-interface-module.md:491-492` — but the problem
is not what is stale; the **mechanism** is, and it is stated as live fact. This
is precisely the `mod-channels.md` class from `CLAUDE.md` §5, still open in the
ADR that owns the decision. Note that `mod-channels.md`, `breath-receive-stage.md`,
`firmware/README.md` and `panel-led/notes.md` were *all* corrected for this on
2026-09-21 `[repo]`; ADR 0004 was not. Fourth consecutive wave in which the
last round's fixes were partial.

**Same sentence, second defect.** The blockquote points the reader at
*"`hardware/module/digital-and-supervision/digital-and-supervision.md`"* for
*"the **no-new-parts** way to get the link coverage back"*
`[repo] docs/decisions/0004-cv-interface-module.md:490-491`. Both halves are
wrong: the content moved to `link-supervision/link-supervision.md` on
2026-09-21, and that page's first act is to refute "no new parts" — it is
**four parts** `[repo] hardware/module/link-supervision/link-supervision.md:89-99`.
ADR 0004 is corpus, not a historical record, so `CLAUDE.md` §6's
"paths in records are not to be corrected" does **not** protect this one.

### A7-18 — the 74AHCT14 proposal does not close on gates or polarity **[med]**

*"One part, three jobs"* — inverting the presence comparator for `CLR`/`OE`,
plus *"edge cleanup on `SCLK`, `MOSI` and `CS` over 2 m of Cat5"*
`[repo] hardware/module/link-supervision/link-supervision.md:106-115`.

Three problems `[calc]` / `[from memory]`:

1. **Gate count.** A 74AHCT14 is a **hex** inverter. Putting three SPI signals
   through it while preserving polarity costs **two gates each = 6**, leaving
   **zero** for the inversion job that motivated the part. Taking one gate each
   (3 gates) leaves the three SPI signals **inverted** into the 74AHCT125.
2. **Polarity is not free to fix in firmware.** `CS` and `SCLK` polarity can be
   inverted in the ESP32's SPI peripheral / GPIO matrix; `MOSI` data polarity
   cannot be inverted meaningfully by the peripheral `[from memory]`. So the
   naive arrangement needs seven gates, or a stated inversion scheme. Neither
   is given.
3. **The third job is smaller than claimed.** The hysteresis problem is at the
   74AHCT125's inputs only — the DAC's `SYNC`, `SCLK` and `D_IN` are already
   **Schmitt-trigger inputs** `[datasheet] SBAS430E, Pin Functions`. An AHCT14
   placed after the buffer adds nothing; placed before it, it is the third
   receiver in a chain of two and brings its own 20 ns/V input-rate spec.

The proposal may still be right. **It needs a gate budget.**

---

## 6. Two SPI hosts — allocation

**Checked and correct.** SPI2 = GPIO35/36/37 (SCK/MOSI/MISO) with CS on 34
(DAC) and 39 (ADC); SPI3 = GPIO38/40 for the 74HC165 chain, latch on GPIO7
`[repo] docs/decisions/0007-imu-selection.md:186-192`,
`[repo] hardware/carrier/carrier.md:212-219`,
`[repo] docs/decisions/0013-two-mcu-split.md:43-46`. `MISO` on IO37 is the
MCP3202's `DOUT` and never leaves the carrier — nothing reads the DAC back
`[repo] hardware/interfaces/spi-link/spi-link.md:39`. The two clocks (2 MHz
DAC, 0.9 MHz ADC) are per-device on one host, which ESP-IDF supports
`[repo] hardware/interfaces/spi-link/spi-link.md:108-111`. Consistent
everywhere. **No pin is double-booked in the GPIO tables.**

**The octal-PSRAM question is correctly closed** — ESP32-S3FH4R2, `R2` = quad,
plus the vendor board definition exposing GPIO33–40
`[repo] docs/decisions/0007-imu-selection.md:228-240`. GPIO35/36/37 are
genuinely free. Verified reasoning; agreed.

### A7-7 — but the 64-pixel matrix claims SPI2 and nothing reconciles it **[high]**

ADR 0007, in the "what was verified, and how" section: *"**The matrix is 64
`WS2812B-0807` parts on GPIO14**, chained, **driven over SPI2** in Zephyr's
configuration."* `[repo] docs/decisions/0007-imu-selection.md:175-177`

ADR 0014 assigns **RMT** channels — but only to the two WS2815 **strips**:
*"Two data lines cost one extra GPIO… The ESP32-S3 drives both on separate RMT
channels without effort."* `[repo] docs/decisions/0014-lighting.md:54-56`. It
says nothing about the matrix. ADR 0014 then makes the matrix *"the
instrument's second display"*, a generic assignable surface
`[repo] docs/decisions/0007-imu-selection.md:204-210`,
`[repo] docs/decisions/0014-lighting.md:312,324`.

`spi-link.md`'s Interfaces table declares SPI2 as *"One host, two devices, two
clocks"* `[repo] hardware/interfaces/spi-link/spi-link.md:41` — the matrix is
not among them. **Nothing in the corpus resolves whether the matrix is on SPI2
or RMT.**

**If it is on SPI2, the output loop does not run.** `[calc]` a 64-pixel
WS2812 frame is 64 × 24 = 1536 bits at 800 kbit/s = **1.92 ms**, or about
**7.7 loop periods**; encoded 3-SPI-bits-per-WS2812-bit at 2.4 MHz it is 4608
bits = 1.92 ms of bus occupancy either way. The DAC cannot be refreshed while
that transfer holds the host, and the 250 µs period would be missed on every
matrix frame.

*(This was already raised, outside the corpus and not landed:
`docs/research/2026-09-21-eurorack-prior-art/R10-keyscan-and-adc.md:608,727`
carries "Confirm the 8×8 matrix is driven by RMT, not SPI. Both SPI hosts
are…" `[repo]`. Flagged because a research record is not the corpus and this
never reached a decision document.)*

**Also unbooked:** even on RMT, a 1.92 ms matrix frame plus two strip frames
are DMA/RMT transfers competing for memory bandwidth and interrupt latency
with an IRAM DAC routine. Nothing in `latency-budget.md` mentions the lights at
all `[repo]`.

**Minor, same area:** ADR 0014 says *"roughly 17 broken out and **12 needed**
on the real-time board (ADR 0007)"* `[repo] docs/decisions/0014-lighting.md:53-54`
while ADR 0007's own table says **14 of 17 used, three spare**
`[repo] docs/decisions/0007-imu-selection.md:196`. Stale derived count.

---

## 7. Repository-convention findings

### A7-17 — the two active parts of this path are filed as undrawn **[med]**

`CLAUDE.md`: *"`hardware/unplaced.csv` holds the rows no schematic page names —
a count of parts nobody has drawn."*

- **`U-LVL-MOD` (74AHCT125)** is in `hardware/unplaced.csv:20` `[repo]` — and
  is drawn, by name, with its rail and its `OE` tie, at
  `[repo] hardware/module/digital-and-supervision/digital-and-supervision.md:52-58`,
  and named throughout `[repo] hardware/interfaces/spi-link/spi-link.md`.
- **`U-DAC` (DAC8568CIPW)** is in `hardware/unplaced.csv:6` `[repo]` — and is
  the subject of its own circuit directory and drawing
  `[repo] hardware/module/dac8568/dac8568.md:29-45`.
- **`hardware/module/digital-and-supervision/` has no `bom.csv` fragment at
  all** `[repo]`, against `CLAUDE.md`'s "one circuit per directory: the page,
  its `bom.csv` fragment, its `circuit.yaml`, and `notes.md`".

Both rows carry the most carefully datasheet-verified notes in this slice, so
nothing is *lost* — but `unplaced.csv`'s count is supposed to mean something,
and two of the three parts in the digital path are inflating it. A row lives
with the circuit whose page derives its value; both pages exist.

`tools/merge-bom.py --check` passes (138 rows, 24 fragments, 0 problems)
`[repo]`, and `tools/check-staleness.py` reports PASS `[repo]` — so neither
tool sees any of this, which is the point of §5.

### A7-22 — outside this slice, noted in passing **[low]**

`ROADMAP.md` E12: *"etherCON braced to the PCB — good practice at **8HP**
rather than the structural necessity it was at 6HP"*
`[repo] ROADMAP.md:53`. ADR 0004 says *"At **10HP** this is good practice
rather than a structural necessity"*
`[repo] docs/decisions/0004-cv-interface-module.md:830`. The panel is 10HP
`[repo] config/figures.yaml:272`. The staleness checker misses it: the
`forbidden` list for that figure holds `"at 8HP this"`, `"inside 8HP"`,
`"The panel is 8HP"`, `"Comfortable at 8HP"` — and the live spelling is
`"good practice at 8HP"` `[repo] config/figures.yaml:276`. **Fifth recorded
instance of a forbidden pattern missing a different phrasing of the same
value.** Handing to whichever agent owns the mechanical slice.

---

## What I checked and found correct

Recording these because a finding filed as handled stops getting re-checked,
and so does a fact nobody re-verified.

- **74AHCT125 `V_IH` = 2.0 V, `V_IL` = 0.8 V**, TTL, not ratioed to V_CC
  `[datasheet] SCLS264O, Recommended Operating Conditions`. The corpus's
  threshold is right.
- **No input clamp to V_CC** on the AHCT125, three independent ways as the BOM
  row claims — `I_IK` specified for `V_I < 0` only, against `I_OK` for
  `V_O < 0` *or* `V_O > V_CC`; and input leakage specified at `V_I` = 5.5 V with
  `V_CC` = 0 V `[datasheet] SCLS264O, Absolute Maximum Ratings / Electrical
  Characteristics`. **Verified; the BOM row is accurate.**
- **AHCT `V_OH` ≥ V_CC − 0.1 V at 50 µA** (4.4 V min at V_CC = 4.5 V)
  `[datasheet] SCLS264O, Electrical Characteristics`. ADR 0004's "on a rail
  sagging to 4.75 V still drives 4.6 V" is right `[calc] 4.75 − 0.1 = 4.65 V`.
- **`OE` ×4 to GND** is the correct tie: the '125 has four independent
  active-low output enables `[datasheet] SCLS264O, Function Table`.
- **DAC8568 SCLK max 50 MHz** `[datasheet] SBAS430E, Timing Requirements` —
  2 MHz is nowhere near a limit.
- **C-grade POR and clear-code default are both zero scale**, and
  DB1 = DB0 = '1' would ignore the `CLR` pin
  `[datasheet] SBAS430E, Power-On Reset / Clear Code Register`. The BOM row's
  "do not write ClearIgnore" is correct and important.
- **`LDAC` = 0 Ω to GND** is required, verbatim, for synchronous updates
  `[datasheet] SBAS430E, LDAC Function`. The 2026-09-21 correction is right.
- **The statelessness rule is genuinely required by the hardware** — no
  `MISO`, a self-clearing `CLR`, and a POR that zeroes channel 7 along with
  everything else `[datasheet] SBAS430E, Power-On Reset`,
  `[repo] firmware/README.md:47-80`,
  `[repo] hardware/module/mod-channels/mod-channels.md:150-180`. Verified, not
  merely asserted.
- **SPI host and GPIO allocation has no double-booking in the pin tables**, and
  the quad-PSRAM conclusion is sound (A7-7 is about a peripheral claim, not a
  pin conflict).
- **`merge-bom.py --check`** passes and **`check-staleness.py`** reports PASS
  with 5 tracked unresolved `[repo]`.

---

## The three I would fix before merge

1. **A7-3 / A7-2** — the pull network leaves the DAC's `SYNC` asserted in the
   state the design says it spends most of its life in, and the recorded fix
   names a rail that does not exist. This is a hardware change, not wording.
2. **A7-6** — `loop-budget` does not follow from its own derivation, and on the
   page's own firmware rows 4 kHz does not close. This is upstream of E11 and
   of the DAC clock.
3. **A7-7** — decide, in a decision document, whether the matrix is on RMT.
   If it is on SPI2 the output loop cannot run at any rate.

**A7-4** (the wrong `V_IH` row) and **A7-5** (the pitch jack's power-on state)
are single-line corrections against banked documents and should go in the same
commit as whatever else touches those pages, per `CLAUDE.md` §3.
