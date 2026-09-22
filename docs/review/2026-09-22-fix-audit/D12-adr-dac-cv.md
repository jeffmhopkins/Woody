# D12 — the two ADR changes about the DAC and the CV outputs

**Slice:** ADR 0004's level-shifter threshold (`0.7 × AVDD` → `0.625 × AVDD`)
and ADR 0006's power-on table (pitch row `below −2 V` → `Exactly 0 V`).
**Cold:** nothing under `docs/review/**` was read except this wave's
`README.md`. Git log and diffs were read; they are the subject.

**PDF route:** `pip install pymupdf` was not needed — PyMuPDF 1.28.2 is already
importable in this container (`python3 -c "import pymupdf"` → 1.28.2)
`[test]`. All `[datasheet]` quotes below come from
`datasheets/analog/DAC8568CIPW.pdf` read with it. Printed page numbers equal
PDF index + 1 (verified on pages 2, 3, 4, 53) `[test]`.

---

## Verdict in one page

| | |
|---|---|
| **ADR 0004 — the datasheet claim** | **Correct, verbatim.** The supply-band split is real, `dac-rail` is in the band claimed, the arithmetic and the "0.39 V wrong" are right, and the p.53 revision-history citation checks out. |
| **ADR 0004 — the conclusion** | **The part survives; the stated reason does not.** With the *lower* threshold the buffer's output margin grows (1.34 V, was 0.95 V) — but the ADR's parenthetical "3.3 V CMOS still cannot drive it" **becomes false at nominal**. `V_INH` min is 3.26 V against a 3.3 V logic high: 3.3 V CMOS now *exceeds* it by 40 mV. **D12-1, and the most important thing in this report.** |
| **ADR 0006 — the reasoning** | **0.000 V follows, and by a stronger route than the ADR gives.** The mod rows are right. |
| **Completeness** | **One miss, and it is the document the fix cites as its independent derivation:** `pitch-stage.md:140-141` still tells the reader ADR 0006's table asserts "below −2 V". **D12-4.** |
| **Acted on?** | **No.** Recorded and left: no milestone observes it, no firmware requirement, no `Consequences` entry. **D12-6.** |
| **Sibling claims** | **Both confirmed.** `0004:506-510` and `0004:842`. |
| **New, from reading the edited paragraph cold** | **D12-2** (abs-max on the DAC's digital inputs vs the buffer's bus rail — the corpus already makes this exact argument one component over), **D12-3** (the markdown blockquote swallowed a live design sentence), **D12-5** (the C-grade reset argument is now the wrong argument for the *power-on* row), **D12-8** ("full scale *equals* AVDD" contradicts `ROADMAP.md:196`). |

Findings are indexed by node / figure id, per `CLAUDE.md`. Severity is my own.

---

## 1. The datasheet claim — verified

`[datasheet]` SBAS430E, **p.4**, `ELECTRICAL CHARACTERISTICS (continued)`,
`LOGIC INPUTS` block, transcribed row by row from the text layer:

```
VINL  Logic input LOW voltage    2.7V ≤AVDD ≤5.5V     0.3 × AVDD    V
                                 2.7V ≤AVDD < 4.5V    0.7 × AVDD    V
VINH  Logic input HIGH voltage   4.5V ≤AVDD ≤5.5V     0.625 × AVDD  V
```

**The split is real and it is `V_INH` specifically** — `V_INL` is one row
across the whole supply range, `V_INH` is two. ADR 0004's quotation of the
band edges (`2.7 V ≤ AVDD < 4.5 V` and `4.5 V ≤ AVDD ≤ 5.5 V`) is
character-for-character the datasheet's, including the asymmetric `<` on the
first band.

**Both values are in the MIN column, which is what makes them a threshold to
clear.** Checked by word coordinates rather than by reading order, because the
extracted text does not preserve columns `[test]`: the page's column headers
sit at MIN `x` 411.0–423.8 and MAX `x` 489.0–504.5; `0.625 × AVDD` spans
`x` 381.5–423.8 (right-aligned into MIN) and `0.3 × AVDD` spans 469.9–504.5
(MAX). So `V_INH ≥ 0.625 × AVDD` and `V_INL ≤ 0.3 × AVDD`.

**`dac-rail` is in the band claimed.** `[repo] config/figures.yaml:344-352` —
`dac-rail`, value `5.21 V`, `derivation: "1.25 x (1 + 475/150) = 5.208 V"`,
`floor: "5.00 V, HARD"`. 5.21 V ∈ [4.5, 5.5] → the `0.625` row. ✓

**The revision-history citation is right too.** `[datasheet]` SBAS430E **p.53**,
`REVISION HISTORY`, under *Changes from Revision C (February 2011) to Revision
D*: *"Changed Logic Input HIGH Voltage parameter test condition into two rows
…… 4"*. And the row's own origin, under *Changes from Revision A to Revision
B*: *"Changed Logic Input HIGH Voltage parameter minimum value from 1.8 to
0.7 × AVDD"*. So TI first made it ratioed and then split it by supply band,
deliberately, and the ADR's sentence about p.53 is accurate.

**Arithmetic** `[calc]`:

```
0.625 × 5.21 = 3.25625  → 3.26 V   ✓ as stated
0.700 × 5.21 = 3.6470   → 3.65 V   ✓ the old number
difference    = 0.39075 → 0.39 V   ✓ "0.39 V wrong"
```

Nothing in §1 is wrong. This is the best-sourced fix in my slice.

---

## D12-1 — the conclusion the fix declares survived is now false at nominal

**Nodes:** `SCLK_DAC`, `DIN`, `SYNC`. **Figure:** `dac-rail`.
**Severity: HIGH.** This is the "a fix that quietly weakens a conclusion
without saying so" case, and here the fix *states* that the conclusion
survives.

`[repo] docs/decisions/0004-cv-interface-module.md:218-219`:

> the **conclusion survives — 3.3 V CMOS still cannot drive it —** but the
> number carrying the argument was 0.39 V wrong

**Two conclusions are being conflated, and they move in opposite directions.**

**(a) "the 74AHCT125 clears the threshold" — strengthened.** `[calc]`

| | old row | corrected row |
|---|---|---|
| `V_INH` at AVDD = 5.21 V | 3.65 V | **3.26 V** |
| buffer `V_OH` on a 4.75 V rail (ADR's figure) | 4.6 V | 4.6 V |
| margin | 0.95 V — "a volt of margin" | **1.34 V — "well over a volt"** |

The ADR's edit from "a volt" to "well over a volt" is arithmetically right,
and the 4.6 V is defensible against the banked part:
`[datasheet] datasheets/logic/SN74AHCT125.pdf` p.4 gives `V_OH` min **4.4 V**
at `V_CC` = 4.5 V, `I_OH` = −50 µA (and 3.8 V min at −8 mA). The DAC's digital
inputs draw `±1 µA` max `[datasheet]` SBAS430E p.4, `LOGIC INPUTS`, *"Input
current ±1 µA"*, so the −50 µA column is the applicable one and
`V_OH ≈ V_CC − 0.1`. **Even at the worst corner the conclusion holds**: 4.4 V
guaranteed against `0.625 × 5.5` = 3.44 V is 0.96 V `[calc]`.

**(b) "3.3 V CMOS cannot drive it" — broken.** `[calc]`

```
a 3.3 V logic high        3.300 V
V_INH min at AVDD 5.21 V  3.256 V   →  the 3.3 V high CLEARS it by 44 mV
V_INH min at AVDD 5.00 V  3.125 V   →  clears it by 175 mV   (the HARD floor)
V_INH min at AVDD 5.50 V  3.438 V   →  fails by 138 mV
break-even: AVDD = 3.3 / 0.625 =  5.28 V
```

So the sentence is true only for **AVDD above 5.28 V**, and `dac-rail` is
5.21 V nominal with a bench-selected window whose *hard floor* is 5.00 V
`[repo] config/figures.yaml:352`. Across most of the window the part's own
`V_INH` min is *below* a nominal 3.3 V high. With the old row the claim was
clean (3.3 V against 3.65 V); the corrected row is the row that dissolves it.

**Related: the fix states a single-point threshold for a rail the same ADR
says is selected on a bench.** `[repo] 0004:196-200` — *"Select R2 on the
bench at E7, against the real DAC"* — and `[repo] 0006:190-194` — *"E7 selects
the divider on the bench across a 0.66 V worst-case spread"*. A threshold that
is `0.625 × AVDD` on a bench-selected AVDD is a **band, 3.125–3.44 V**, not
3.26 V. Writing one nominal number for it is the same shape of error the fix
was correcting.

**The buffer is still the right part — for reasons the ADR does not give.**
All three are in the repo already:

- `[repo] hardware/interfaces/spi-link/spi-link.md:71-75` — at the chosen
  100 Ω the **first step at the far end is 2.75 V**, resolving over the ~20 ns
  round trip of 2 m of Cat5. A DAC wired straight to the umbilical would be
  given 2.75 V for the first transit of every edge, under *every* value of
  `V_INH` in the band, on a pin with no hysteresis.
- `V_INH` is a MIN over −40 … +125 °C with no typical `[datasheet]` p.4 — 44 mV
  is not a design margin.
- **The corpus has no `V_OH` figure for the ESP32-S3 anywhere.** `[test]`
  `grep -rn "V_OH\|VOH\|0.8 *[×x] *VDD" hardware/ docs/decisions docs/reference
  firmware config README.md ROADMAP.md` → no output. So "3.3 V logic" in this
  ADR means the rail, not a specified output high, and the one number the
  argument needs has never been banked.

**What would settle it:** rewrite 0004:208-219 so the surviving claim is the
one that is true — the buffer exists because the umbilical's far-end step and
an unspecified MCU `V_OH` cannot be trusted against a 3.125–3.44 V band — and
delete "3.3 V CMOS still cannot drive it", or qualify it to AVDD > 5.28 V.
A `dac-vinh` register entry (see D12-7) is the mechanical half.

---

## D12-2 — the edited paragraph's other claim: abs max on the DAC's digital inputs

**Nodes:** `SCLK_DAC`, `DIN`, `SYNC`, bus `+5V` after `FB4`/`C4`.
**Severity: HIGH** (a part, and an unretrofittable one).

`[repo] 0004:208-223`, the paragraph the fix rewrote, concludes:

> Leaving it there keeps its switching current off the DAC's supply, and it
> means **the only thing hanging on the unprotected bus +5 V pin is a $0.30
> buffer. A reversed or row-offset ribbon that puts +12 V onto that pin kills
> the buffer and nothing else**, which is why the +5 V entry gets no
> protection network of its own.

The fix read p.4's `LOGIC INPUTS` rows. **Two pages earlier, on the same
part:** `[datasheet]` SBAS430E **p.2**, `ABSOLUTE MAXIMUM RATINGS`:

```
Digital input voltage to GND     –0.3 to +AVDD + 0.3    V
```

The buffer's rail is the rack bus, which this ADR itself calls *"the
least-regulated rail in Eurorack — ±5 % is normal"* `[repo] 0004:163`. The
DAC's rail is the LM317. **They are different rails, and the abs-max ceiling
on three DAC pins is set by the second one while the drive comes from the
first.** `[calc]`

| Condition | Buffer `V_OH` | Ceiling `AVDD + 0.3` | |
|---|---|---|---|
| bus 5.00 V, AVDD 5.21 V | ~4.90 V | 5.51 V | fine |
| bus 5.25 V (+5 %), AVDD 5.21 V | ~5.15 V | 5.51 V | 0.36 V |
| bus 5.25 V, AVDD **5.00 V** (the hard floor E7 may select to) | ~5.15 V | **5.30 V** | **0.15 V** |
| bus 5.5 V (a lightly-loaded bus board), AVDD 5.00 V | ~5.40 V | 5.30 V | **exceeded** |
| **reversed ribbon, +12 V on the buffer's V_CC** | toward 12 V | 5.51 V | **exceeded by ~6.5 V** |

There is **no series element between the buffer's outputs and the DAC's
inputs** `[repo] hardware/module/digital-and-supervision/digital-and-supervision.md:45-66`
— the drawing shows the three DAC-side `R-SPI-PULL` as pulls to a rail and to
ground, not as series resistors, and `R-SPI-SER` is three parts at the
*controller's* driving end `[repo] hardware/interfaces/spi-link/bom.csv:3`. The
buffer drives ±8 mA `[repo] bom.csv U-LVL-MOD note`.

**And the corpus already makes exactly this argument, one component over.**
`[repo] hardware/interfaces/spi-link/bom.csv`, the `R-SPI-PULL` note:

> DAC-SIDE CS PULLS TO AVDD (the LM317's 5.21V) not bus +5V — a pull-up
> belongs on its consumer's rail, and **on the bus rail a reversed ribbon
> reaches the DAC's SYNC pin and turns a $0.30 buffer failure into a DAC
> failure**

That reasoning was applied to a 10 kΩ pull-up — which would have been
current-limited to well under a milliamp — and not to the three ±8 mA push-pull
drivers that reach the same three pins. `hardware/module/pitch-stage/pitch-stage.md:86-89`
shows the same class of hazard being paid for on the analog side: *"`R-OPAMP-IN`
… is pure clamp-current protection for the power-up window where the DAC is on
5.21 V and the op-amp is on ±12 V"*.

**Severity is not the nominal case — it is that "kills the buffer and nothing
else" is asserted, not derived.** It needs the AHCT part to fail before the
DAC's input clamp is stressed, on a $30 TSSOP-16 that is the module's only
non-substitutable IC. **What would settle it:** either a derivation showing the
buffer's failure mode is open-circuit and fast, or three series resistors
(the same answer `R-OPAMP-IN` is), or the rail change
`digital-and-supervision.md:93-101` already records three reviewers asking for.
I am not proposing the fix; I am reporting that the sentence is unsupported and
that the corpus contradicts it under `R-SPI-PULL`.

---

## D12-3 — the fix's own blockquote swallowed a live design sentence

**Severity: MEDIUM** — cosmetic in the file, not in the rendered page, and it
lands on the sentence that carries the rail decision.

`[repo] 0004:213-223`, and `[test]` `cat -A` confirms there is no blank line
and no `>` prefix on 220:

```
219:  > carrying the argument was 0.39 V wrong, in the ADR that owns the link.* Leaving it
220:  there keeps its switching current off the DAC's supply, and it means the only
221:  thing hanging on the unprotected bus +5 V pin is a $0.30 buffer. …
```

Lines 220-223 are **lazy continuation lines of the blockquote's last
paragraph** in CommonMark and GFM — no blank line separates them, so they do
not start a new block. Rendered, the reader gets the live rail justification
("Leaving it there keeps its switching current off the DAC's supply…") printed
*inside* the italicised 2026-09-21 historical correction, i.e. presented as
history. Its subject, "Leaving it there", also no longer has an antecedent: the
sentence it continued is now six lines and a quote block away
(`git show b32c557 -- docs/decisions/0004-cv-interface-module.md` shows the
quote inserted mid-sentence) `[repo]`.

This is `CLAUDE.md`'s "a refutation split across an ASCII drawing's gutter does
not count" trap in a new location: a *correction* block that captured the text
it was meant to sit beside. The fix is one blank line after `link.*`.

---

## 2. Re-deriving the power-on output — ADR 0006

**The transfer function, from its owner** `[repo]
hardware/module/pitch-stage/pitch-stage.md:70-76`:

```
Vout = Vdac·(1 + R2/R1) − V_ref·(R2/R1)
     = 2·Vdac − 2.500          when R1 = R2 and V_ref = 2.500 V
```

`V_ref` is *not* a rail-derived divider: `[repo] pitch-stage.md:22, 31-32,
128` — `VREFOUT ──[TRIM-OFFSET 10k]──┬── ½ OPA2197 ──┬── V_ref ≈ 2.500 V`,
`"2.500 V, trimmed then buffered from VREFOUT"`.

**The reference really is off, and the datasheet says what that does to the
pin** `[datasheet]` SBAS430E **p.31**, `INTERNAL REFERENCE`:

> The internal reference in the DAC7568, DAC8168, and DAC8568 is **disabled by
> default** for debugging, evaluation purposes, or when using an external
> reference. … **During the time that the internal reference is disabled, the
> DAC functions normally using an external reference.** … In the default mode,
> the internal reference is powered down until a valid write sequence is
> applied to power up the internal reference.

and p.1 Features: *"internal reference (disabled by default)"*.

**So with the reference off the `VREFIN/VREFOUT` pin is an input, and nothing
drives it.** Its only load is the pitch stage's own `TRIM-OFFSET` 10 kΩ network
to `AGND` `[repo] pitch-stage.md:31` plus the part's internal 8 kΩ
(`[datasheet]` p.4, *"Reference input impedance 8 kΩ"*). The node sits at
≈ 0 V. Therefore `[calc]`:

```
V_REF at the pin        = 0 V                (nothing sources it)
any DAC channel output  = code/65536 × 2 × V_REF = 0 V   for ANY code
pitch V_ref (buffered)  = 0 V                (follower of a 0 V divider)
Vout(pitch) = 2 × 0 − 1 × 0 = 0.000 V
```

**0.000 V follows — and by a stronger route than either document gives.** Both
ADR 0006:212 and pitch-stage.md:138 argue "both terms are zero" *because the
codes reset to zero scale*. The reference being at 0 V makes the output 0 V
**independently of the code and therefore independently of the grade**. That
matters — see D12-5.

**The op-amp can actually deliver it:** OPA2197 is RRIO on ±12 V
`[repo] 0004:229-231`, so 0 V is mid-supply, not a rail. "Exactly 0 V" is
right to within the stage's input offset.

**Do the mod rows stay at 0 V? Yes, and more robustly than the table claims.**
`[repo] 0006:156` and `hardware/module/mod-channels/mod-channels.md:111,
165-172`: `Vout = 4 × Vdac − 3 × V_ref`, `V_ref` = DAC ch7 = `mod-reference`
3.3333 V. `[calc]` span check: `4×5 − 3×3.3333 = +10.000`,
`4×0 − 3×3.3333 = −10.000` ✓. At power-on with `V_REF` at the pin = 0 V, ch7 = 0
and every signal channel = 0, so `4×0 − 3×0 = 0 V` on all four jacks — and, per
above, this holds for **any** code and **any** grade. The table's cell "Both
terms of the difference are zero" is correct. ✓

**One state the corpus does not describe: the step at the enable write.**
`[calc]` Firmware's first DAC write is the reference enable
(`pitch-stage.md:146-149`, *"the reference-enable must be firmware's first DAC
write, before any channel data"*). The instant it lands, `V_ref` becomes
2.500 V (analog, immediate) while the pitch code is still zero, so pitch steps
**0.000 V → −2.500 V**, and only then to whatever firmware writes. The mod
jacks do *not* move (ch7's code is still zero). So the real boot sequence on
the pitch jack is `0 V → −2.500 V → commanded`, and only the first of those
three is in the corpus. It is brief, but it is the state the *old* table
described, arriving at the moment the *new* table stops covering.

---

## D12-4 — the completeness miss: `pitch-stage.md` still quotes the old table

**Node:** pitch stage output / `PITCH` jack. **Severity: HIGH** — it is the one
document ADR 0006 names as its independent derivation.

`[repo] hardware/module/pitch-stage/pitch-stage.md:137-141`:

> **Power-on is 0.000 V, not "subsonic".** `V_ref` is the DAC's internal
> reference, which is **disabled until firmware writes an enable** — so *both*
> terms are zero and the jack sits at **0 V, a VCO's base note**, until that
> write. After it, `CLR` parks at −2.500 V. **ADR 0006's power-on table asserts
> "below −2 V" for both; they are different states, 2.5 V apart.**

ADR 0006's table has said `Exactly 0 V` since `b32c557` `[repo] 0006:203`. The
circuit page still tells its reader the ADR asserts the opposite, and offers
that disagreement as the reason to trust the page. Meanwhile ADR 0006:213 says
*"which `pitch-stage.md` derives independently"* — **the two documents now cite
each other in opposite directions across the same fix.** A reader arriving at
either one is told the other is wrong.

Only the last sentence is stale; 137-140 is correct and is the derivation. The
fix was one file short.

**Nothing else in the corpus is stale on this value.** `[test]`
`grep -rn "below −2 V\|below -2 V\|subsonic\|bottom of its range\|parks pitch"`
over `hardware/ docs/decisions docs/reference firmware config README.md
ROADMAP.md` returns exactly three live hits: `pitch-stage.md:140-141` (this
finding), `0004:506-507` (D12-9) and `0006:207` (the refutation itself,
correctly framed as history). `hardware/module/pitch-stage/notes.md:34` and
`mod-channels.md:174` both say `0 V` and both are about the **mod** channels,
where it is true.

---

## D12-5 — the C-grade argument is now the wrong argument for the power-on row

**Figure:** `mod-reference`; **part:** `U-DAC`. **Severity: MEDIUM.** This is
the `CLAUDE.md` §5 shape — an argument surviving its own refutation, in the
same ADR, 40 lines above the fix, under a heading that names the case.

`[repo] 0006:143-169`, heading **"Resolved: what the outputs do at power-on"**:

> So specify a **C grade** part — zero-scale reset — and **the power-on state
> is the best available on every channel at once** … a B or D part would put
> **+2.5 V on all four mod jacks** where the old topology gave 0 V regardless

`[calc]` With the reference off at rack power-on, `V_REF` at the pin = 0 V, so
every channel's output is `code/65536 × 2 × 0 = 0 V` **whatever the reset code
is**. A B or D part, reset to midscale, also puts 0 V on all four mod jacks and
0 V on pitch. **The reset state is invisible at power-on.** What the C grade
actually buys is the state from the **reference-enable write** until firmware's
first data write, and the state after a **runtime `CLR`** — on a B/D part the
midscale codes then give `4(2.5) − 3(2.5) = +2.5 V` on the mods `[calc]` and
`2(2.5) − 2.500 = +2.5 V` on pitch, which is the real hazard and is correctly
described everywhere else.

This is not a reason to unlock the grade: the *other* reason is untouched and
binding — `[repo] 0006:171-178`, C/D are reference gain 2, and
`[datasheet]` p.2 Table 1 confirms it (`DAC8568C … MAXIMUM REFERENCE
FULL-SCALE 5V, RESET TO Zero`; `DAC8568A … 2.5V, Zero`;
`DAC8568B/D … Midscale`). The defect is that the fix corrected the table's
pitch row and left the paragraph above it deriving "the power-on state is the
best available" from a property that power-on cannot see.

**Same correction due in two derived documents**, which state the trigger the
same way `[repo]`:

- `hardware/module/mod-channels/mod-channels.md:160-163` — *"the DAC's own
  **power-on reset**, which happens on every rack power-up"*
- `firmware/README.md:60-62` — *"The DAC's own **power-on reset**, which fires
  on every rack power-up — so this is not a fault case, it is the boot path"*

Both are still right about the *failure* they describe (firmware refreshing
five channels and not ch7 → `4 × Vdac` ≈ +11.45 V), because that happens after
the enable write. Only the claim that the grade's reset state is what makes
rack power-on safe needs the qualifier.

---

## D12-6 — an audible note at every rack power-on, recorded and left

**Severity: MEDIUM** (a design property, not an error). Asked for by the slice,
and the answer is: **nothing in the corpus acts on it.**

`[test]` `grep -rn "audible"` over the corpus: the only hits about this state
are `0006:203` (the table cell) and `0006:208` (the refutation). `[test]`
`grep -rn "power-on\|power up\|power-up" ROADMAP.md` → one hit, `ROADMAP.md:142`,
about breath ambient zeroing. Specifically:

- **No milestone observes it.** `ROADMAP.md`'s E7–E11 rows and its
  measurements table (`ROADMAP.md:190-204`) contain nothing about the pitch
  jack at power-on. E7 is *"Commanded codes produce expected voltages"*; the
  DAC row at `ROADMAP.md:196` is about saturation vs AVDD.
- **The ADR treats the two new findings unequally.** Its breath row's
  consequence is scheduled — `[repo] 0006:236-237`: *"a patch left connected
  can wake with up to 5 V of standing breath CV. **E10** is where that gets
  observed rather than discovered (`ROADMAP.md`)"*. The pitch row's
  consequence names no milestone, no firmware requirement and no
  `Consequences` entry. Both were written in the same commit.
- **No firmware requirement.** `firmware/README.md` carries the reference-enable
  ordering rule and the statelessness rule, and nothing about the pitch jack
  before the first write. The available mitigations are firmware-only and free:
  write the pitch code **in the same pass as** the reference enable, or write a
  subsonic code first, which would restore the property the old table wrongly
  claimed.
- **`ROADMAP.md`'s "Failures that are silent, and what makes them loud" table**
  is the obvious home for the *inverse* — a failure that is loud by
  construction — and it is not mentioned there either.

**One unsourced number inside the fix.** `[repo] 0006:214-215` — *"held for
**about a second** at every rack power-on"*. `[test]` `grep -rn "about a
second\|boot time\|boot-time\|~1 s\|1 second\|startup time"` over the corpus
returns that line and nothing else. The duration of the artefact is the whole
question of whether it matters, it is stated to one significant figure, and it
carries no provenance tag in a corpus whose review rule is that an unmarked
claim is a defect. It reads as `[from memory]`.

---

## D12-7 — neither number is in the register, and both are read in more than one place

**Severity: MEDIUM**, mechanical. `CLAUDE.md` §1: *"If a quantity is in that
register, the owning document states it and every other document cites it by
name."* Neither of my two quantities is in it `[test]`
(`grep -n "3.65\|0.625\|3.26\|V_INH" config/figures.yaml` → no threshold entry;
no power-on-state entry either).

Consequence, measured: `[test]` `python3 tools/check-staleness.py` →
`PASS no live stale values | corpus 123 files, 23 circuits, 37 figures / 218
patterns | 5 unresolved (tracked) | 233 restated-not-cited (advisory)`. **The
checker passes with D12-4, D12-9 and D12-10 live in the corpus**, because
nothing tracks these values. `--detail`'s restated-not-cited list does not
reach 3.26 V either (it fires at three or more files).

- **`dac-vinh`** would own the threshold. Its `value` is not a number but a
  **band**, `3.125–3.44 V over the bench-selectable AVDD window`, which is the
  honest form (D12-1). Two documents read it: `0004:209` and, in its retired
  spelling, `0004:147` (D12-8). `forbidden` should carry `0.7 × AVDD`
  spellings — and, per `CLAUDE.md` §2's third trap, the `false_positive_note`
  must protect `0004:213-215`, which quotes *both* rows correctly as the
  datasheet's own text, and `0014:96`, where *"a logic high near 0.7 × their
  supply"* is about the WS2815 and is a different part entirely.
- **`pitch-power-on`** would own `0.000 V`, read in `0006:203`,
  `pitch-stage.md:137-139` and (stale) `0004:507`. Its `forbidden` would have
  caught D12-4 and D12-9 — spelled, per the same trap, in **both** the en-dash
  and hyphen-minus forms, since `0006:207` uses `−2 V` (U+2212) and a BOM row
  or a plain-ASCII edit would use `-2 V`.

**And one register defect I hit while checking the sibling claim about
`97 mm`:** `[repo] config/figures.yaml`, figure `panel-height-budget`, has
**two `false_positive_note` keys**, at lines 408 and 423. `[test]` a duplicate-
key scan reports it, and `yaml.safe_load` keeps only the **second** — the
figure's parsed keys are `[id, quantity, value, status, owner, derivation,
toggle_row, forbidden, false_positive_note, escape_note, note]` with
`false_positive_note` = the `"candidates 107 / 97 / 112 / 124"` text. **The
note at 408 is silently discarded**, including its record that `panel.md:20`
and `0004:736` legitimately narrate the review. It is the only duplicate key in
the file. (Register slice's turf, reported here because it is load-bearing for
D12-10.)

---

## D12-8 — `0004:147`, and `0004:168-169` against `ROADMAP.md:196`

**Severity: LOW/MEDIUM.** Both are in the same section as the fix.

**(a) The same fact, stated off the old row, 62 lines above the correction.**
`[repo] 0004:147-148`:

> The cost is that a 5 V DAC wants **roughly 3.5 V for a logic high** while the
> instrument sends 3.3 V, so SPI needs shifting.

3.5 V is `0.7 × 5` `[calc]` — the retired row, at a 5 V rail. On the corrected
row a 5 V DAC wants `0.625 × 5` = **3.125 V**, and at this module's rail
3.26 V. The hedge "roughly" keeps it from being flatly false, but it is the
number the fix disproved, in the sentence that introduces the level shifter,
and it is what a reader skimming the section for "why a shifter" will find
first. It also silently supplies the missing premise for D12-1: 3.5 V > 3.3 V
is what makes "3.3 V CMOS cannot drive it" read as obvious.

**(b) "full scale *equals* AVDD" is wrong, and `ROADMAP.md` already says so.**
`[repo] 0004:168-171`:

> **The DAC's full-scale output is its supply.** DAC8568 at internal reference
> × 2 spans 0–5 V, **so full scale *equals* AVDD.** TI does not specify the
> headroom needed to actually reach it, and wants AVDD ≈ 5.5 V for a true 5 V
> full scale.

against `[repo] ROADMAP.md:196`:

> Full scale is **5.000 V from the internal reference at gain 2, *independent*
> of AVDD** — what AVDD decides is whether the output buffer can reach it.

`ROADMAP.md` is right. `[datasheet]` SBAS430E p.3 has these as two separate
things: `Output voltage range | 0 | AVDD | V`, whose test conditions are
*"AVDD ≥2.7V; grades A and B: maximum output voltage"* and *"AVDD ≥5V; grades C
and D: maximum output voltage"* — i.e. the **swing capability** is 0…AVDD,
while full scale is `2 × VREFOUT` = 5.000 V and does not move with AVDD.
The ADR's *conclusion* (do not run AVDD off a sagging bus rail, because the top
codes compress and corrupt the fit) is correct and is exactly what that p.3
condition encodes — but the sentence carrying it says something false, and
the corpus's correction of it lives in `ROADMAP.md` and never came back.
`0004:169`'s "TI does not specify the headroom" is fair: p.3 claims 0…AVDD with
no headroom spec.

---

## Sibling claims

### D12-9 — `0004:506-510`: **CONFIRMED.** The equivalence ADR 0006 destroyed

`[repo] docs/decisions/0004-cv-interface-module.md:504-509`:

> ~~**Assert `CLR` at the module when no valid frame has arrived for N
> milliseconds.**~~ … The DAC's own `CLR` pin already does exactly what is
> wanted — an A/C grade part clears to zero scale, which **parks pitch subsonic
> and the mod channels at 0 V (ADR 0006), the same safe state as rack
> power-on.**

Two claims, and they are not both wrong — which matters, because the cheapest
fix here would break the good one `[calc]`:

- **"parks pitch subsonic" is correct** for the state it is about. A runtime
  `CLR` happens with the reference *enabled*, so zero-scale codes give
  `2 × 0 − 2.500` = **−2.500 V**, which is below −2 V. `pitch-stage.md:140`
  says the same: *"After it, `CLR` parks at −2.500 V."*
- **"the same safe state as rack power-on" is now false.** Rack power-on is
  0.000 V (reference off); `CLR` is −2.500 V (reference on). **2.5 V apart** —
  and `pitch-stage.md:141` says precisely that: *"they are different states,
  2.5 V apart."* The sentence asserts an equivalence that the ADR 0006 fix
  dissolved, and the document that states the refutation is the one the fix
  cites.

The claim's framing — *"may still say … the same safe state as rack power-on"*
— is exactly right, and the sibling was right to file it. Mitigating: the
paragraph sits under a struck-through proposal (`~~**Assert `CLR` …**~~`) for a
watchdog that is deleted. Not exculpating: `[repo] 0004:500-501` says *"The
paragraphs below are **kept** because the problem they describe is still
real"*, so this is live prose, and "the same safe state as rack power-on" is
the sentence a reader would use to justify a future `CLR`-on-timeout scheme.

Also, in passing: **"an A/C grade part"** at 0004:506 is factually fine (A and
C both reset to zero scale, `[datasheet]` p.2 Table 1) but reads against ADR
0006:171-178's *"Not 'A or C', which this line used to say … Only C satisfies
both requirements."* An A-grade part is excluded for its reference gain, not
its reset state, so the sentence is not stale — but it is the last "A/C" left
in the corpus `[test]`, and it is one grep away from looking like one.

### D12-10 — `0004:842`: **CONFIRMED.** A retired `97 mm`, and the checker cannot see it

`[repo] docs/decisions/0004-cv-interface-module.md:841-845`:

> > **Still a 1:1 paper check at M4, and now it has numbers to check against.**
> > **The 97 mm above** is built from `[from memory]` component envelopes …

The table it points at is at `[repo] 0004:783-790` and totals
**`110 mm against 115.5 mm — 5.5 mm spare`** — 52 lines above, exactly as the
claim says. 97 mm is one of the four retired candidates the register names
`[repo] config/figures.yaml:401-424`, figure `panel-height-budget`, value
`"110 mm of content against 115.5 mm of clear panel"`. There is no 97 mm
anywhere in that table or its derivation `[test]`; `grep -rn "97 mm\|97mm"`
over the corpus returns only this line, the register's own `forbidden`/
`escape_note` strings, and `CLAUDE.md`'s account of the trap.

**Why it is live**, and it is the canonical `CLAUDE.md` §2 failure `[test]`:
every pattern in that figure's `forbidden` list carries context —
`"97 mm against ~110 mm"`, `"97 mm against ~110"`, `"= 97mm"` — and the surviving
text is `"The 97 mm above"`. No pattern is a substring of it, so
`check-staleness.py` reports `PASS`. The `escape_note` in that same entry
records four misses "each by one removed space"; this is a fifth, by three
different words. And per D12-7 the entry's first `false_positive_note` — the
one that licenses the legitimate narrations — is being discarded by a duplicate
YAML key, so anyone adding a pattern here is working from half the guidance.

Note also that this sentence is the *provenance* note for the layout: it says
the figure it names is `[from memory]` and unverified. Pointing that warning at
a number the table no longer contains detaches the warning from the layout it
was written to qualify. (Panel/mechanical slice's value; reported because the
claim was routed to me and it verifies.)

---

## What I checked and found clean

Recorded so the next reviewer does not redo it.

- **The datasheet claim, end to end** — rows, columns, band edges, the MIN/MAX
  placement, the p.53 history, `dac-rail`'s membership in the band, and the
  three arithmetic results. §1. No defect.
- **`hardware/module/dac8568/`** — `dac8568.md` states no threshold and no
  power-on state; it cites `dac-rail` by name in its Interfaces table, which is
  §1-compliant. Nothing to follow. `bom.csv`'s `U-DAC` row carries the
  `DAC8568ICPW` correction and the grade lock.
- **`hardware/module/digital-and-supervision/`** — the `U-LVL-MOD` BOM row's
  threshold numbers are the **buffer's own** TTL levels (`V_IH` 2.0 V,
  `V_IL` 0.8 V, confirmed there against SCLS264O), not the DAC's `V_INH`. Not a
  stale copy. `digital-and-supervision.md` states no threshold.
- **`hardware/interfaces/spi-link/`** — `spi-link.md:71-75`'s threshold table
  is against the buffer's 2.0 V `V_IH`, consistent with `0004:85`. Not a copy of
  the corrected figure; it is the argument D12-1 says should be carrying the
  conclusion.
- **`hardware/module/mod-channels/`** — `mod-channels.md:102, 111, 155-174` and
  `notes.md:34, 97, 106` are all correct about the mods at 0 V, for the reason
  given. `mod-channels.md:174`'s *"the same state as rack power-on"* is true
  for the mod channels (unlike `0004:507` for pitch).
- **`firmware/README.md`** — the `V_ref` = 3.3333 V, the `4·Vdac − 3·V_ref`
  form, the +11.45 V failure and the statelessness rule all check out, and the
  reference-enable is named in the sticky set. Subject to D12-5's qualifier
  only.
- **`ROADMAP.md`, `config/figures.yaml`** — no stale copy of either value,
  because neither value is in them at all (D12-7).
- **`0006:179-194`** — the SBAS430E quotation (*"For device grades A and C on
  power-up, all DAC registers are filled with zeros…"*), the A/B-2.5 V /
  C/D-5 V gains and the *"C grade is specified only for AVDD = 5.0 V to
  5.5 V"* rider are all confirmed against `[datasheet]` p.2 Table 1 and p.3's
  `Output voltage range` test conditions. The `VREFIN < AVDD/2` rider is
  confirmed at p.4 (`Grades C/D, AVDD = 5.0V to 5.5V | 0 | AVDD/2 | V`).
- **The `DAC8568CIPW.pdf` filename** in `0006:180` and `ROADMAP.md:48` is
  correct as written — the file keeps the transposed name deliberately
  (`datasheets/MANIFEST.csv` row 3 `SUPERSEDES`), so these are not stale.
- `python3 tools/verify-datasheets.py` and `merge-bom.py --check` were not run;
  I touched nothing they own.

## Uncertainty, stated

- **D12-2's severity is the part I am least sure of.** The nominal case is
  inside abs max; what I am reporting as a defect is that "kills the buffer and
  nothing else" is asserted rather than derived, on a coupling the corpus
  already rejected for the pull-up. A measurement of the target rack's +5 V at
  E6 plus the AVDD selected at E7 would bound it; the reversed-ribbon case
  needs a failure-mode argument about the AHCT part, not a measurement.
- **D12-1 is arithmetic and I am confident in it.** What is a judgement call is
  whether the ADR should say the buffer is *needed* (it is, for the umbilical
  and temperature reasons) or that 3.3 V *cannot* drive the pin (it can, at
  nominal). If a future reader concludes from 3.3 V > 3.26 V that the buffer
  can be deleted, the ADR as written gives them no reason not to.
- **D12-5 does not unlock the grade** and should not be read as proposing that.
  Reason two (reference gain 2) is independent, banked and binding.
