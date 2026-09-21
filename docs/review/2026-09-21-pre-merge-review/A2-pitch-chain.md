# A2 — the pitch chain, and whether it can be tuned

**Agent:** A2, cold. **Date:** 2026-09-21.
**Slice:** DAC ch1 → `R-OPAMP-IN` → the two-resistor non-inverting stage and its
LT5400 pair → `TRIM-GAIN` / `TRIM-OFFSET` → `R-OUT-PROT` → the `PITCH` jack,
with DC feedback tapped at the jack.
**Read:** `hardware/module/pitch-stage/**`, `docs/decisions/0006`, `0004`,
`0005`, `config/figures.yaml`, `ROADMAP.md`, `firmware/README.md`,
`docs/reference/pcb-pipeline.md`, `hardware/bom.csv`,
`hardware/module/dac8568/dac8568.md`, `datasheets/analog/DAC8568CIPW.pdf`.
**Not read:** anything under `docs/review/`, per the cold rule.

**Provenance marks:** `[repo]` path:line · `[calc]` arithmetic shown ·
`[datasheet]` document and page · `[from memory]`. Unmarked = defect in this
report.

**Constants used throughout** `[calc]`: 1 V/oct ⇒ 1 cent = 1/1200 V =
**0.83333 mV**; so 1 mV = 1.200 cents. Gain `A = 1 + k`, intercept `= −k·V_ref`,
`k = R2/R1`. `∂Vout/∂k = Vdac − V_ref` ⇒ ratio-drift lever
`max|Vdac − V_ref| = |4.75 − 2.5| = 2.25 V`. Reference-drift lever
`max|Vout| = 7 V`.

---

## Verdict in one line per question

| # | Question | Verdict |
|---|---|---|
| 1 | Transfer function and endpoints | **Correct.** All four table entries and both endpoints reproduce exactly. Minor: the drawing omits three fitted parts (P13) |
| 2 | Error budget in cents | **Ranking survives; three of its numbers do not.** One row does not reproduce (P7a), four ADR 0006 figures are still on the refuted 9 V lever (P7b), and the page endorses one of them 165 lines above its own table (P7c) |
| 3 | Can the trims reach? | **No, and the page states the direction backwards** (P9). `TRIM-GAIN`'s one-sidedness is correctly described but its consequence contradicts ROADMAP E8 and ADR 0006 (P11) |
| 4 | Jack-side tap | **Stability argument is sound and the numbers reproduce** — but the compensation pole/zero is still the 1 nF pair (P6), the clamp no longer protects the LT5400 (P3), and "the AC sweep is structurally blind" is wrong (P12) |
| 5 | Offset reference tracking | **Holds exactly**, and survives the E10 fix if the trim network stays ratiometric. ADR 0006's stated reason for the buffer is now false as drawn, harmlessly (P10) |
| 6 | Power-on / `CLR` | **Both the ADR and the page are wrong.** The banked datasheet says `VREFOUT` is 3-state before the enable write, so the power-on state is *undefined*, not 0 V and not −2.5 V (P1) |

Severity: **P1–P4 before copper. P5–P12 before merge. P13–P15 editorial.**

---

## P1 — [node `VREFOUT`] Power-on is not 0 V. It is undefined, and the banked datasheet says so

`[repo] hardware/module/pitch-stage/pitch-stage.md:134-138` —
*"`V_ref` is the DAC's internal reference, which is disabled until firmware
writes an enable — so both terms are zero and the jack sits at 0 V, a VCO's
base note."*

`[datasheet] SBAS430E, PDF p.31, "Internal Reference"` — verbatim:
*"During the time that the internal reference is disabled, the DAC functions
normally using an external reference. At this point, the internal reference is
**disconnected from the VREFIN/VREFOUT pin (3-state output)**."*

Only one of the two terms is zero:

- `Vdac` **is** 0 V `[calc]` — zero-scale code gives `code/65536 × 2 × V_ref = 0`
  for any reference, including none. C grade resets to zero scale
  `[repo] docs/decisions/0006-cv-channel-allocation.md:180-184`.
- `V_ref` is **not** 0 V. It is the output of a follower whose input reaches a
  3-stated pin through `TRIM-OFFSET` and nothing else. As drawn
  `[repo] pitch-stage.md:28-29` there is **no DC path from that node to AGND**,
  so the follower input floats on leakage and `V_ref` is undefined between 0 V
  and roughly AVDD.

`Vout = 2·0 − k·V_ref` ⇒ the `PITCH` jack sits **anywhere from 0 V to about
−5.2 V** at rack power-on, drifting, until firmware's enable write.

This lands on three documents at once:

- `[repo] pitch-stage.md:134-138` "0.000 V, a VCO's base note" — wrong.
- `[repo] docs/decisions/0006:197-199` "Pitch | Bottom of its range, below −2 V
  | Subsonic. A VCO there is inaudible" — wrong, and the page already says so
  for the wrong reason.
- `[repo] docs/decisions/0006:226-230` "the outputs sit at 0 V from rack
  power-on until firmware enables the reference, **which happens to reinforce
  the table above**" — this is internally contradictory within one ADR: 0 V does
  not reinforce "below −2 V". It reinforces the *mod* row and nothing else.

**Pitch is the only channel with this problem, and the reason is structural.**
The mod channels take their offset from DAC ch 7, a *channel*, which is 0 V at
zero scale regardless of the reference `[repo] docs/decisions/0006:160-166`.
Pitch is the one output whose offset comes from the analog `VREFOUT` pin — the
same property that buys it the tracking argument in item 5.

**Fix is one part and it is already half-specified.** `R-TRIM-RANGE`
`[repo] hardware/bom.csv:82` is `open` and must set `TRIM-OFFSET`'s span
anyway; if that network is a *divider* (bottom leg to AGND) rather than a series
rheostat, `V_ref` is defined at 0 V during the window and the page's claim
becomes true as written. Decide it at E10 with the span, not after.

## P2 — [node `VREFOUT`] The datasheet asks for a capacitor there and the BOM has none

`[datasheet] SBAS430E p.31`: *"A minimum 100nF capacitor is recommended between
the reference output and GND for noise filtering."*
`[datasheet] SBAS430E p.45/47`: *"for improved noise performance, an external
load capacitor of 150nF or larger connected to the VREFH/VREFOUT output is
recommended."*

`[repo] hardware/bom.csv` — every module capacitor row enumerated: `C-DECOUPLE`
(described as *"HF decoupling at every module IC supply pin"*, qty 19),
`C-OUT-BREATH`, `C-FB-PITCH`, `C-AA-PITCH`, `C-FILT-PITCH`, `C-FILT-MOD`,
`C-REG-ADJ`, `C-FILT-BREATH`, `C-BULK-RAIL`, `C-TIMER-LOADSW`,
`C-GATE-LOADSW`. **None is on `VREFOUT`**, and `VREFOUT` is not a supply pin, so
`C-DECOUPLE` does not cover it by its own description.
`[repo] hardware/module/dac8568/dac8568.md` names no decoupling at all.

This is the node the whole precision argument rests on: its noise appears at the
jack as `−k·V_ref` with `k = 1`, i.e. **1:1, and 1 mV there is 1.2 cents**
`[calc]` — the same sensitivity `pcb-pipeline.md:186-188` already flags for the
hand-routing list.

## P3 — [node `PITCH` / `R1,R2` LT5400 pins] The clamp no longer stands between the jack and the matched network

`[repo] hardware/bom.csv:89` `D-JACK-CLAMP` — *"MOVED to the op-amp side of the
1k"*, for two good reasons (back-powering current, and leakage being absorbed
inside the loop). `[repo] pitch-stage.md:45-49` draws it there.

But the same change that made that correct — tapping DC feedback at the jack —
connects the `PITCH` jack to the LT5400's `R2` pin through `R2 + TRIM-GAIN`
(10.2 kΩ) and **nothing else**. There is no clamp on that path.

`[repo] hardware/module/pitch-stage/notes.md:100-106`, reading the banked
LT5400: *"the LT5400 has no internal ESD diodes, only ±1 kV HBM (p.6), with
Figure 1's named remedy being a BAV99 — which `D-JACK-CLAMP` already is. Pitch
feedback is tapped at the jack, i.e. exactly the datasheet's 'external
connector' case, so **check the clamp actually stands between the jack and every
LT5400 pin** when this is laid out."*

**The check fails as drawn.** It is not a layout question — the clamp is on the
wrong side of `R-OUT-PROT` for this purpose, by deliberate decision, and no
layout can put it back without reopening that decision. Two sub-cases:

- **ESD.** A hand-carried 3.5 mm plug discharges into a 10.2 kΩ path to an
  unprotected ±1 kV HBM part and to the op-amp's (−) input.
- **Back-powering.** `[calc]` a neighbouring module driving 10 V into our jack
  through its own 220 Ω output pushes `10/10.2 k ≈ 0.98 mA` into the (−) node
  and the LT5400 — small, but it is the precision network, and the BOM's
  back-powering analysis only considered the `R-OUT-PROT` path.

**Options, none free:** a second BAV99 at the jack (reintroduces the leakage the
move deleted — though `[repo] hardware/bom.csv:89` notes leakage at the jack is
now absorbed by the loop *if* the diode is inside it, which a jack-side clamp
would be); or a series resistor split in `R2`; or accept and record it. What is
not acceptable is `notes.md` carrying it as a check that has not been done.

## P4 — [ref `R-OUT-PROT`] Three live power ratings, and the pitch page carries the lowest

| Source | Rating |
|---|---|
| `[repo] pitch-stage.md:129` | 1206 **≥250 mW** |
| `[repo] hardware/module/breath-output-stage/breath-output-stage.md:151` | 1206 **≥500 mW**, *"shared spec with the other five outputs"* |
| `[repo] hardware/bom.csv:87` part field | `1k 1%, >=500mW` |
| `[repo] hardware/bom.csv:87` notes, 2026-09-21 | *"RATING RAISED … Specify **0.66–1 W** 1206 (ERJ-P08 class)"* |

`[calc]` the pitch short case does pass at 250 mW: `11.45² / 1 kΩ = 131 mW`
(the BOM's 142 mW uses 11.9 V — see P15). It is the *other* case that does not:
the BOM's output-to-output worst case is **322 mW**, and thick-film derating at
a 50 °C rack interior leaves a 500 mW 1206 delivering 350–420 mW.

The pitch page owns this worst case — it created it by moving the tap to the
jack — and it is the one document that still states a number the BOM twice
raised. This is the named failure mode with the direction reversed: the fix
landed in the BOM, and the page a builder reads for *this* circuit kept the old
value.

## P5 — [nets `DAC ch1`, `VREFOUT`] Stale peer: the DAC moved out of `digital-and-supervision` and pitch did not follow

`[repo] hardware/module/dac8568/dac8568.md:1-6` — *"Split out of
`digital-and-supervision.md` on 2026-09-21."* Its interface table
`[repo] dac8568.md:20-21` correctly names `module/pitch-stage` as the peer for
both `VREFOUT` and `DAC ch1`.

`[repo] pitch-stage.md:19-20` still names **`module/digital-and-supervision`**
as the peer for both. `[repo] pitch-stage/circuit.yaml:62` declares
`circuit:module/digital-and-supervision` and **does not declare
`circuit:module/dac8568`** — the circuit that actually feeds this stage.

By `circuit.yaml`'s own header `[repo] pitch-stage/circuit.yaml:33-36`:
*"`depends_on` is the field that can lie. It fails SILENT — an undeclared edge
is an unchecked edge."* The edge from pitch to its DAC is exactly that.

Same defect, same day, adjacent slice, worth one grep to sweep:
`[repo] hardware/module/mod-channels/mod-channels.md:26-27` names
`module/digital-and-supervision` for `DAC ch7` and `ch2–ch5`.

## P6 — [ref `C-FB-PITCH`] The pole/zero pair is still the 1 nF pair

`[repo] pitch-stage.md:181-188`:

```
G(s) = 1 + (R2/R1)/(1 + sR2C) = (2 + sRC)/(1 + sRC)
Pole at 15.9 kHz, zero one octave above at 31.8 kHz, flattening at gain 1.
```

`[calc]` `1/(2π · 10 kΩ · C) = 15.92 kHz` ⇒ **C = 1.0 nF**. The live value is
**2.2 nF** `[repo] config/figures.yaml:262-268` (`pitch-compensation`, settled),
for which the same formula gives **pole 7.23 kHz, zero 14.47 kHz**.

The same sentence is in the BOM: `[repo] hardware/bom.csv:81` (`C-AA-PITCH`
notes) — *"a pole at 15.9kHz and a zero an octave above"*, describing the
feedback cap.

**Why it escaped every check**, and it is worth recording because it is a clean
specimen: 15.9 kHz is *also* the legitimate `C-AA-PITCH` corner
(`1/(2π · 1 kΩ · 10 nF) = 15.92 kHz` `[calc]`), stated correctly four lines
away `[repo] pitch-stage.md:131`. A reader checking "is 15.9 kHz right on this
page?" finds that it is. And `pitch-compensation`'s `forbidden` list
`[repo] config/figures.yaml:267` covers three spellings of the old *net and
value* — `"1 nF across the feedback resistor"`, `"1nF across the feedback"`,
`"C-FB-PITCH 1nF"` — but nothing forbids the old value's **derived
consequence**, which is the form it actually survives in.

Suggested `forbidden` additions when this is fixed, per CLAUDE.md §2 (grep
first — these are the spellings that exist today): `"Pole at 15.9 kHz"`,
`"zero one octave above at 31.8 kHz"`, `"a pole at 15.9kHz and a zero an octave
above"`. Note `"15.9 kHz"` bare **must not** go in the list: `C-AA-PITCH` uses
it correctly in the same two documents.

## P7 — [error budget] One row does not reproduce; four ADR figures are on the lever the page says it fixed

### (a) The `TRIM-GAIN` row is ~26 % high and contradicts its own BOM row

`[repo] pitch-stage.md:285` — `TRIM-GAIN` tempco **0.068 cents** / 10 °C.

`[calc]` from the page's and BOM's own inputs (200 Ω, ~100 ppm/°C, in series
with `R2`, `R1 = 10 k`, lever 2.25 V, 10 °C, full travel = worst case):

```
ΔR    = 200 Ω × 100 ppm/°C × 10 °C          = 0.200 Ω
Δk    = 0.200 / 10 000                      = 20.0 ppm
ΔVout = 20.0e-6 × 2.25 V                    = 45.0 µV
cents = 45.0 µV / 833.33 µV                 = 0.054 cents
```

Independent cross-check `[calc]`: `[repo] hardware/bom.csv:78` says the trimmer
contributes **~2 ppm/°C** against the LT5400's **1 ppm/°C max**
`[repo] pitch-stage/notes.md:79-81`. Two terms with the same lever and a 2:1
tempco ratio must land in a 2:1 cents ratio. `0.054 / 0.027 = 2.00` ✓.
`0.068 / 0.027 = 2.52` ✗.

To produce 0.068 you need 2.52 ppm/°C or a 2.83 V lever; neither is stated
anywhere. **The ranking is unaffected** — the term stays between the LT5400 and
the DAC reference — so the table's *conclusion* survives and only its number
does not.

### (b) ADR 0006 still carries four cents figures on the 9 V lever

`[repo] pitch-stage.md:275-279` says the pivot error is *"resolved, and both
published numbers were wrong … Three documents used 9 V, 7 V and 2.5 V for the
same term."* It is not resolved where the reader looks:

| `[repo]` | States | Lever used | Correct on the page's own pivots `[calc]` |
|---|---|---|---|
| `0006:359` | DAC reference 0.54 cents | 9 V | **0.42** (50 ppm × 7 V = 350 µV) |
| `0006:360` | Discretes 5.40 cents | 9 V | **1.35** linear / **0.95** RSS (500 ppm × 2.25 V = 1.125 mV) |
| `0006:450-452` | Trim cost 2.4 / 3.7 / 6.3 cents | 9 V | **0.59 / 0.91 / 1.55** (220 ppm × 2.25 V = 495 µV) |
| `0006:454` | Matched network 0.11 cents | 9 V | **0.027** (10 ppm × 2.25 V = 22.5 µV) |

These are not decorative. `0006:450-461` is the table that concludes *"Keep the
trim range small — 5 to 10 %"*, which the adopted 200 Ω part (2 %) already
contradicts `[repo] hardware/bom.csv:78`; and `0006:454`'s comparison
("worse than a matched network, comparable to discrete resistors") **inverts**
once the lever is right: at 2.25 V a 5 % trim costs 0.59 cents against
discretes' 0.95–1.35, i.e. *better* than discretes, not comparable to them.

### (c) The page endorses 0.54 cents 165 lines above its own 0.42

`[repo] pitch-stage.md:117-118` — *"(This is also why the ADR's 'the DAC's
internal reference is sufficient, at 0.54 cents over 10 °C' survives: that
figure is a gain term.)"* — against `[repo] pitch-stage.md:283`, **0.42 cents**.
The *argument* survives (it is a gain term ✓); the *number* was replaced by this
page's own table and the endorsement quotes the replaced one.

### (d) The table headed "in order" is not in order, and omits the largest term

`[repo] pitch-stage.md:273-285`: rows run 0.42, 0.027, 0.068. Second and third
are inverted against the heading *"What limits accuracy, in order"*.

And **"the largest term"** `[repo] pitch-stage.md:283` is only true of the three
rows present. `[repo] docs/decisions/0006:475-476` puts DAC INL at **0.66 cents
typical** (±4 LSB) and 2.0 cents at ±12 LSB, both larger. `[calc]` the ADR's own
0.66 is itself low: 4 LSB × (5.000 V / 65536) × gain 2 = 610 µV = **0.73
cents**; the ADR appears to have divided the *9 V output span* by 65536
(`9/65536 × 4 = 549 µV = 0.66`), which is not this DAC's LSB. INL is firmware's
job, not a trimmer's — but the table does not say that, and it is the term a
reader would expect to see excluded explicitly.

## P8 — [figure `pitch-cents-budget`] Keep it disputed. Its `decided_by` is stale

`[repo] config/figures.yaml:324-331`:
`decided_by: "pitch-stage.md has two contradictory budget tables back to back
and states no total. One coherent table, then cite it."`

- **"Two contradictory tables back to back" no longer describes the page.** The
  superseded one moved to `[repo] hardware/module/pitch-stage/notes.md:43-64`,
  correctly marked and refuted in place.
- **"States no total" is still true**, and is the whole substance of the
  dispute. Nothing in the corpus states a total pitch error, while
  `[repo] hardware/module/power-entry/power-entry.md:130-133` scales an
  independent ground-path finding against *"the entire pitch error budget at
  0.42 cents"* — a row treated as a total, which is exactly the misuse the
  register's own first candidate warns about.
- **The page has since added a fourth value** to the four candidates listed
  (P7c, the 0.54 endorsement).

So: **the disputed status is still justified** — do not close it. But rewrite
`decided_by`, because a reviewer who checks the stated condition will find half
of it gone and may close a dispute that is live. That is the failure mode
CLAUDE.md flags as the worse kind.

For whoever writes the total: `[calc]` an RSS of the live table with P7a applied
is `√(0.42² + 0.027² + 0.054²) = 0.425 cents` over 10 °C — i.e. **the budget is
the DAC reference and a rounding error**, which is also what makes the LT5400
"currently masked" argument `[repo] pitch-stage.md:287-296` correct. Note also
that every candidate but one is a 10 °C figure and one is 0–40 °C; a total needs
its temperature span stated or it is four numbers again.

## P9 — [ref `TRIM-OFFSET`] "Not buildable" is right; the stated direction is backwards

`[repo] pitch-stage.md:314-318`:
*"`V_ref` nominal is `VREFOUT`, and a divider can only go below it, so the
nominal sits at an end stop with **no downward authority**."*

The sentence contradicts its own premise. If a divider can only go *below*
`VREFOUT`, then from a nominal sitting *at* `VREFOUT` the available direction is
**down** and the missing one is **up**.

In output terms `[calc]`, with `k = 1`, `Vout = 2·Vdac − V_ref`:

- `V_ref` ↓ ⇒ `Vout` ↑ ⇒ **sharp**. Available.
- `V_ref` ↑ ⇒ `Vout` ↓ ⇒ **flat**. **Not available.**

So the trimmer can only ever push the instrument sharp. A board that comes out
sharp cannot be trimmed flat.

The corpus already states the correct form elsewhere, in a section nobody would
grep for it: `[repo] docs/decisions/0004-cv-interface-module.md:563-566` —
*"reaching **above** 2.500 V from a 2.500 V reference needs an op-amp half and
0.1 % resistors, because 1 % on the step is 12 cents."*

**The conclusion is right and should stand**: the network must put 2.500 V at
mid-travel, via divide-and-gain-back or a small bipolar injection, at E10 with
`R-TRIM-RANGE`. Two riders for whoever builds it:

1. **It must stay ratiometric to `VREFOUT`** or item 5's tracking argument dies
   (see P10 / item 5). Divide-and-gain-back is ratiometric; a bipolar injection
   from the LM317 rail is **not**, and would put the rail back in the pitch
   path — the thing `[repo] docs/decisions/0006:590-600` bought the whole
   topology to avoid.
2. **±50 mV (≈60 cents) is the right span only if the range resistors are
   ≤1 %.** `[calc]` a divide-and-gain-back from 1 % parts contributes up to
   1 % × 2.5 V = 25 mV = **30 cents** of intercept error of its own, which is
   what the span has to absorb; at 5 % it would need ±125 mV. The span figure
   in `[repo] hardware/bom.csv:79` is therefore a constraint on `R-TRIM-RANGE`'s
   tolerance, not just its value.

## P10 — [ref `TRIM-OFFSET` / node `VREFOUT`] ADR 0006's reason for the buffer is false as drawn — and the corpus should record *why that is harmless*

`[repo] docs/decisions/0006:606-609`:
*"Buffering it matters, and not only for drive. Hanging a **trimmer** directly
on `VREFOUT` would make the reference move as the trimmer is turned, coupling
the offset adjustment into the DAC's full-scale span. **A follower breaks
that.**"*

The trimmer is now **ahead** of the follower `[repo] pitch-stage.md:125,
:231-243` and `[repo] hardware/bom.csv:79` — i.e. hanging directly on
`VREFOUT`, which is the arrangement that bullet rules out. The follower is
downstream of the trimmer and cannot break a coupling that happens upstream of
it. Same ADR, two sections, mutually exclusive.

**The hardware is fine; only the argument is broken.** Settled here with the
banked datasheet so it does not get "fixed" by a future reviewer moving the
trimmer back:

`[datasheet] SBAS430E p.4, EC table` — *"Load regulation, sourcing, T_A = +25°C:
**30 µV/mA**"*.

`[calc]` a 10 kΩ trim network on 2.500 V draws 250 µA. Worst case the whole of
that load appears and disappears with the adjustment:

```
ΔV_REFOUT = 0.250 mA × 30 µV/mA = 7.5 µV  =  3.0 ppm
at the jack (gain term, 7 V lever): 3.0e-6 × 7 V = 21 µV = 0.025 cents
```

0.025 cents against a 0.42-cent budget. **Negligible, and it is negligible for a
reason the ADR could not have known without the datasheet.** Two further numbers
from the same table that support the topology and are not in the corpus:
**line regulation 10 µV/V** (so `[calc]` the 50 mV rail step ADR 0006 costs at
12.5 cents on the old rail-divider topology becomes 0.5 µV on `VREFOUT` =
**0.0006 cents**) and **initial accuracy 0.004 %**, i.e. ±100 µV, which is
common-mode and therefore a gain term the trim does not have to reach.

Action: correct the ADR bullet's reasoning, keep the buffer (it is still needed
for drive and for isolating the follower's input from `R1`), and put the
0.025-cent number somewhere a future reviewer will find it.

## P11 — [ROADMAP E8] "Trimmers go both ways" is false for both trimmers

`[repo] ROADMAP.md:49` — E8: *"Raw analog gain and offset trimmed to target,
linear across the span. The 5 %-over kludge is deleted — **trimmers go both
ways** (ADR 0006)."*
`[repo] docs/decisions/0006:485-487` — *"The 'design the gain 5 % high' kludge
is deleted. It existed only because firmware could scale in one direction. **A
trimmer goes both ways.**"*

Neither trimmer does:

- `TRIM-GAIN` is **0 → +2 %**, one-sided, and the page says so twice
  `[repo] pitch-stage.md:126, :324-327`.
- `TRIM-OFFSET` is one-sided too, per P9.

**The consequence is concrete at E8, which is the bench step that meets it.**
`TRIM-GAIN` in series with `R2` can only *raise* `k`. With the nominal ratio
sitting dead on 1:1 `[repo] pitch-stage.md:126`, the LT5400's ±0.01 % (grade A)
matching `[repo] pitch-stage/notes.md:78-79` is symmetric, so **on roughly half
of built boards the gain error points the way the trimmer cannot reach.**
`[calc]` the size of what is unreachable: Δk = 1e-4 ⇒ 1e-4 × 2.25 V = 225 µV =
**0.27 cents** — smaller than the DAC reference term, so firmware's affine
genuinely does cover it.

That is the honest resolution, and it is the opposite of what E8 says: the gain
trimmer has **no job left**, not "both directions". The page's own proposed fix
`[repo] pitch-stage.md:324-327` — *"fixed leg slightly under nominal, trimmer
bracketing it"* — **is the deleted 5 %-over kludge under another name**, applied
to the resistor instead of the DAC code. Either the trimmer goes (firmware
covers it), or the kludge comes back in resistor form. E8's row asserts a third
option that does not exist.

## P12 — [node `PITCH`] "The AC sweep is structurally blind to this" is wrong, and "Measured" has no source

`[repo] docs/reference/pcb-pipeline.md:128` — *"**Measured** 41.8 % overshoot at
82 nF, 65.4 % at 330 nF. **The AC sweep is structurally blind to this** on the
same circuit at the same loads."* Repeated as the gate justification in
`[repo] hardware/module/pitch-stage/sim/README.md:13-26`.

**The overshoot numbers are sound.** `[calc]` from the page's own formula
`[repo] pitch-stage.md:264` `Q = √(R_eff·C_load / R2·C_fb)`, with
`R_eff = R-OUT-PROT = 1 kΩ`, `R2 = 10 kΩ`, `C_fb = 2.2 nF`:

```
82 nF :  Q = √(1k·82n / 10k·2.2n)  = √3.727 = 1.931
         ζ = 1/2Q = 0.2589 ; OS = exp(−πζ/√(1−ζ²)) = 43.1 %   (page: 41.8 %)
330 nF:  Q = √(1k·330n / 10k·2.2n) = √15.00 = 3.873
         ζ = 0.1291        ; OS                        = 66.4 %   (page: 65.4 %)
```

Within 1.5 points of the stated values — good agreement, and it confirms the
hazard is real.

**But the blindness claim is false, by the same model.** `[calc]` a second-order
loop with `τ₁ = R_eff·C_load`, `τ₂ = R2·C_fb` has
`ω₀ = 1/√(τ₁τ₂)` and an AC magnitude peak of `Q/√(1 − 1/4Q²)`:

```
330 nF: ω₀ = 1/√(3.3e-4 · 2.2e-5) = 11 736 rad/s = 1.87 kHz
        peak = 3.873/√(1−0.01667) = 3.906  =  +11.8 dB
 82 nF: ω₀ = 3.72 kHz ;  peak = 1.998      =  +6.0 dB
```

An AC sweep over 10 Hz–1 MHz shows **+11.8 dB of peaking at 1.9 kHz**. That is
not blindness; it is the loudest feature on the plot. If the intended claim is
about *large-signal* behaviour (slew limiting on a note-change step) then the
sentence should say so — as written it tells the next person that the cheap
screen is useless, which will cost a run.

**And "Measured" is not supported anywhere.** E9 has not happened
`[repo] ROADMAP.md:198`; `[repo] sim/README.md:3-11` states *"Nothing here has
been run"* and that a plausible number written there would be indistinguishable
from a datasheet figure. My reproduction above is consistent with these being
**calculated**, not measured. Under `pcb-pipeline.md`'s own rule — *"Results
land in `config/figures.yaml` with their provenance marked"*
`[repo] sim/README.md:41-44` — neither these nor the phase-margin numbers
**18° / under 10°** (`[repo] pitch-stage.md:218`, `hardware/bom.csv:80`,
`docs/decisions/0006:707-709`) have a recorded derivation, a sim, a bench run or
a register entry, and the 18° figure is the sole quantitative support for a
warning that now appears in three documents.

The *topological* half of that warning is independently correct and does not
need the number — `[calc]`/`[from memory]` a cap across `R2` connects jack→(−),
the same two nodes `R2` spans, so `R-OUT-PROT` and the cable stay inside the
loop at every frequency, which is the capacitive-load-in-the-loop case; a cap
from the op-amp *output* to (−) gives `β(∞) = 1` and leaves `R-OUT-PROT`
isolating the jack above the handover. Keep the warning; mark the 18° as
unsourced or derive it.

## P13 — [drawing] The ASCII schematic is missing three fitted parts

`[repo] pitch-stage.md:27-51`. Present: `VREFOUT`, `TRIM-OFFSET`, the follower,
`R1`, `DAC ch1`, `R-OPAMP-IN`, the op-amp, `C-FB-PITCH`, `D-JACK-CLAMP`,
`R-OUT-PROT`, `R2`, `TRIM-GAIN`, the jack.

Absent, though all three are in the component table `[repo] :120-132` and in
`[repo] hardware/bom.csv`:

- **`C-AA-PITCH`** (10 nF, `R-OPAMP-IN` node → `AGND`) — the part the page calls
  *"THE ACTUAL PITCH FILTER"*.
- **`C-FILT-PITCH`** (10 nF, at the jack) — the part whose restoration is the
  longest argument on the page.
- **`R-BIAS-DAC`** (100 k, at the DAC pin) — arguably belongs on `dac8568.md`,
  but `[repo] pitch-stage.md:320-323` is where it is specified and it is a
  pitch-stage dependency in `circuit.yaml:57`.

The page's own warning box `[repo] :212-221` closes with *"The drawing above is
right. Three other places said 'across the feedback resistor' and were wrong,
and **prose is what a layout gets built from**."* On a convention where the
Markdown page *is* the schematic `[repo] CLAUDE.md` "Hardware conventions", the
drawing is what a layout gets built from — and a part that is not on it is a
part the netlist will not have. Both capacitors' *placement* is the single most
contested thing on this page; neither appears in the only picture of it.

## P14 — [firmware] The ordering rule exists in exactly one document, and it is not the firmware one

`[repo] pitch-stage.md:142-146` — *"it carries a firmware requirement: **the
reference-enable must be firmware's first DAC write**, before any channel data,
and it is in the sticky-register set that gets periodically refreshed
(`firmware/README.md`)."*

`[repo] firmware/README.md:70-77` carries the *refresh* half — *"the
internal-reference enable, and the clear-code register itself … refreshing the
reference-enable and clear-code registers periodically costs a word every few
thousand passes"* — and **never states the ordering**. `[repo]
docs/decisions/0006:224-230` says only *"enable the DAC's internal reference
explicitly at boot"*.

Grep confirms it: `"first DAC write"` occurs once in the corpus, on the hardware
page `[repo] pitch-stage.md:144`.

Per P1 the ordering matters more than the page argues: until that write
`VREFOUT` is 3-state, so *every* pass firmware makes before it produces an
undefined pitch output, not a 0 V one. The requirement belongs in
`firmware/README.md`'s "Architecture constraints" list, which is the document a
firmware author reads.

## P15 — Coherence and arithmetic nits, no action beyond a line each

- **Two nominal gains.** `[repo] :258` *"the exact DC solve gives gain
  **2.020000** for every load from open circuit to 2 kΩ"* against `[repo] :126`
  *"**Nominal is dead on 2.000**"*. The first is the trimmer at full travel, the
  second at zero; nothing says so, and 2.020000 reads as the design value.
  (The load-independence claim itself **checks out**: `[calc]` finite-gain
  residual `1/(A_OL·β)`; at `R_L = 2 kΩ`, `β ≈ [2k/3k] × [10k/20.2k] = 0.330`,
  `A_OL ≈ 3.16e6` (130 dB), giving **0.96 ppm** — the page's "about 1 ppm".)
- **The 2 kΩ bound is a headroom bound and the page does not say so.** `[calc]`
  at the top of the ±600-cent reserve (+7.5 V) into 2 kΩ the op-amp must reach
  `7.5 + 3.75 = 11.25 V`, against the page's own `~±11.45 V` limit
  `[repo] :148-151` — 0.2 V of margin. Into 1 kΩ it needs 15 V and clips. The
  headroom paragraph considers only the unloaded case.
- **"Lead at every load … dead short"** `[repo] :204-207` sits against
  `[repo] :269-271` *"with the jack shorted, DC feedback is exactly zero and the
  amp rails."* `[calc]` confirms the latter: with `V_jack` pinned at 0,
  `V(−) = V_ref·R2/(R1+R2) = 1.25 V` and the op-amp slams to a rail for any
  `Vdac ≠ 1.25 V`. The dead-short entry does not belong in a list of loads the
  network is a *lead* into.
- **`−3 dB at 12.2 kHz` counts only the output stage.** `[calc]` my ideal-op-amp
  solve of `R1 ‖ R2 ‖ C-FB` with `C-FILT-PITCH` at the jack gives −2.3 dB at
  12.2 kHz for that stage alone; cascading `C-AA-PITCH`'s own 15.9 kHz pole,
  which is in the same signal path, gives −2.6 dB at 10 kHz, −3.4 dB at 11 kHz
  and −4.3 dB at 12.2 kHz. The **channel's** −3 dB is ≈10.7 kHz — still inside
  ADR 0006's 10–20 kHz window `[repo] :209`, but at its bottom edge rather than
  comfortably within it.
- **Two op-amp swing figures.** `[repo] :150` *"~±11.45 V"* (after two Schottky
  drops) against `[repo] hardware/bom.csv:67` *"RRIO on ±12V reaches ~11.9V"* —
  and the `R-OUT-PROT` 142 mW short-circuit figure `[repo] hardware/bom.csv:87`
  is computed from 11.9 V. `[calc]` at 11.45 V it is 131 mW. Immaterial to the
  rating (P4), but it is one quantity with two values.
- **"Fifteen times worse than the LT5400"** `[repo] :288`: `[calc]`
  `0.38 / 0.027 = 14.1`. Fine as prose; noted only because the 0.38 itself
  reproduces exactly as an RSS of two 10 ppm/°C parts
  (`√2 × 10 ppm × 10 °C × 2.25 V = 318 µV = 0.38 cents`), which is worth
  recording since the page does not show it.
- **`R-OFFINJ` still appears in the staleness advisory** — *"drawn in a
  schematic, no BOM row"* `[repo] .staleness/report.txt` — from
  `[repo] pitch-stage.md:231-243`, where it is named only as a deleted part.
  Correct as a refutation; noted so the next reader does not re-file it.

---

## Verified correct — recorded so it stops being re-checked

`[calc]` unless marked. Each of these I re-derived independently and each holds.

| Claim | `[repo]` | Check |
|---|---|---|
| `Vout = 2·Vdac − 2.500` from the drawn network | `:67-73` | `Vout = Vdac(1+R2/R1) − V_ref(R2/R1)`; `R1=R2` ⇒ `2·Vdac − 2.500` ✓ |
| Slope 9/4.5 = 2.000, intercept `−2 − 2(0.25) = −2.500` | `:62-65` | ✓ both |
| Endpoints | `:62` | `2(0.25) − 2.5 = −2.000`; `2(4.75) − 2.5 = +7.000` ✓ exact |
| ±600 cents reserve from the 0.25/4.75 window | `:148-151` | 0.25 V DAC = 0.5 V out = 600 cents at 1 V/oct ✓ |
| `CLR` parks at −2.500 V (post-enable) | `:137` | zero-scale code, `V_ref = 2.5`, `k = 1` ✓ |
| Load independence of the jack-side tap | `:257-260` | Exact for an ideal op-amp; ~1 ppm residual ✓ (P15) |
| The reference-tracking argument | `:96-115` | `Vout = VREFOUT·[2(1+k)·code − k·α]` ⇒ a fractional drift δ scales the whole function. **Holds exactly, and survives the E10 trim-network fix provided the network stays ratiometric to `VREFOUT`** (P9 rider 1) |
| Offset vs gain error table | `:107-110` | 1 mV = 1.2 cents ✓; 100 ppm × 2 V = 0.24 ✓; × 7 V = 0.84 ✓ |
| LT5400 row, 0.027 cents | `:284` | 1 ppm/°C max × 10 °C × 2.25 V = 22.5 µV ✓ |
| Two discretes, 0.38 cents | `:288` | RSS of two 10 ppm/°C parts ✓ (P15) |
| The pivot analysis itself | `:275-279` | Ratio drift pivots at `Vdac = V_ref` (`Vout = +2.5 V`), max lever 2.25 V ✓; reference drift pivots at `Vout = 0`, max lever 7 V ✓. **The page's diagnosis is right; the ADR just never followed it** (P7b) |
| 6.02 dB shelf maximum, any value | `:185-187` | `(2+sRC)/(1+sRC)`: 2 at DC, 1 at ∞ ✓ topology, not value |
| Deleted 10 nF gave −16 dB / 100 kHz, −36 dB / 1 MHz | `:188` | 15.9 kHz RC ✓ both |
| "Deleting it cost 30 dB at 1 MHz" | bom.csv:83 | 36 − 6 ✓ |
| −11.9 and −23.5 cents/octave load divider | `:158` | `1 − 100/101 = 9.90 mV` = 11.88 ¢; `1 − 50/51 = 19.61 mV` = 23.5 ¢ ✓ |
| `R-OUT-PROT` short dissipation | bom.csv:87 | `11.45²/1k = 131 mW` (142 at 11.9 V) ✓ |
| Cable capacitance cannot destabilise the loop | `:207` | `[calc]` 200 pF ⇒ `Q = √(1k·200p / 10k·2.2n) = 0.095` — heavily damped ✓. The hazard is a *mult to another output's jack cap*, which the page states separately and correctly |
| `β(∞) = 1` with `C-FB` from the output | `:203-205` | Above `1/(2π·R1·C) = 7.2 kHz` the cap shorts output→(−) ✓ |
| `C-AA-PITCH` 15.9 kHz against `R-OPAMP-IN` | `:131` | `1/(2π·1k·10n)` ✓ — and see P6 for why this correct number hid a wrong one |
| `R-OPAMP-IN` costs no gain error | `:83-86` | Feeds a (+) input; no current ⇒ no error ✓ |
| Gain trim touches offset, offset trim does not touch gain | `:245-255` | `A = 1+k`, `offset = k·V_ref` ⇒ `∂A/∂V_ref = 0` ✓. The trim procedure (high note → gain, low note → offset) is right |
| C grade: zero-scale reset, 5.000 V FS, 5 ppm/°C max | `0006:176-190` | `[datasheet] SBAS430E p.31 + EC table p.4` — confirmed; C/D tempco **2 typ / 5 max ppm/°C**, so the budget's 5 ppm/°C is the max, i.e. conservative ✓ |
| `merge-bom.py --check` | — | `138 rows from 24 fragments, 0 problems` — the pitch fragment and the master agree ✓ |

---

## Adjacent, outside this slice, not pursued

`[repo] firmware/README.md:82-84` states *"the in-amp's `REF` pin is grounded
rather than driven by a firmware zero (ADR 0003)"*, against
`[repo] ROADMAP.md:51` E10 — *"`REF` **trimmed, not grounded** — grounding it
makes the panel knobs interact, and leaves `TRIM-BREATH-ZERO` nothing to
drive"*. One of the two is stale. Flagged for whoever has the breath slice.

---

## If only three things are fixed before copper

1. **P1** — `VREFOUT` is 3-state before the enable write, so the pitch jack has
   no defined power-on state. Give the node a DC path to `AGND` in
   `R-TRIM-RANGE`, add the datasheet's 100 nF (**P2**), and correct all three
   documents that state a power-on voltage.
2. **P3** — the jack-side tap put the LT5400 on the outside of the clamp.
   `notes.md` already asks for this check; it fails as drawn, and it cannot be
   fixed at layout time.
3. **P4** — `R-OUT-PROT` at ≥250 mW on the pitch page is two revisions behind
   the BOM, on the only part in the module at real risk from a jack fault.
