# E3 — which findings are wrong, overstated, or double-counted

**Slice:** the adversarial complement. The fix-audit wave was incentivised to
find things; nobody was incentivised to find that it found too much.

**Read:** `docs/review/2026-09-22-fix-audit/**` (the subject) and this round's
`README.md`. No sibling in `docs/review/2026-09-22-fix-audit-review/`, no
earlier wave.

**Provenance:** `[repo] path:line`, `[calc]`, `[test]` with the command and its
real output, `[datasheet]` with document and page. Everything marked `[test]`
was run in this session against a `git archive` of the frozen commit
`0576a95` under the scratchpad. Report only; nothing in the corpus was changed.

---

## 0. Two facts about the tree that change how every measurement below reads

**(a) The tools stopped being frozen during round 2.** When this slice started,
`git status` showed ` M tools/check-staleness.py` — 49 uncommitted insertions
implementing D1's `check_owners` repair and D3/D5/D7's refutation-vocabulary
repair. It has since landed as `566159e` *"Fix the instrument: the verdict is
reproducible again"* (tools only: `check-staleness.py`, `merge-bom.py`,
`rewrite-paths.py`; no corpus file touched `[test] git show --stat 566159e`).

The consequence is mechanical and affects every slice in this round:

```
[test] at HEAD (566159e):   FAIL ... + 8 stale + 0 bom
[test] at 0576a95 (frozen): PASS no live stale values | ... | 233 restated-not-cited
```

Every `[test] python3 tools/check-staleness.py → PASS` quoted in the fix-audit
wave — D1's baseline table, D12-7, D13, D14 §4.1, D15, D20's four-green header
— is **no longer reproducible at HEAD**. It reproduces exactly at `0576a95`.
Anyone in round 2 who re-runs the tool without pinning the commit will
contradict the wave for the wrong reason.

**(b) One measurement of mine was contaminated, and the contamination
accidentally reproduced D1's headline.** My first scratchpad extraction
differed from its source commit in exactly one character —
`umbilical-load-switch.md:176` read `5.10 kΩ` where `0576a95` has `5.11 kΩ`
`[test] diff`. I did not make that edit and cannot account for it. It meant my
tree carried a live rule-1 violation, which is precisely D1's test condition.
Result over thirty identical runs of the unmodified HEAD tool:

```
[test] PASS=12 FAIL=18 of 30
[test] seeds 0,1,5 -> FAIL 1 owners ; seeds 2,3,4,6,7 -> PASS
[test] the flapping figure: loadswitch-fb-divider, value "35.7 kohm / 5.11 kohm, both 1%"
       nums = ['35.7','5.11'], both length 4 -> tie -> sorted(set(...), key=len) picks by hash seed
```

D1 reported **6 PASS / 4 FAIL over ten runs**. I got 12/30. Same distribution,
found by accident, on a different figure. **D1-F2 is the best-evidenced finding
in the wave and I could not break it.**

On the genuinely clean tree the tool is stable: `[test]` eight hash seeds, eight
PASSes. So the precise statement is narrower than STATUS's *"no run of this tool
means anything precise"* — a PASS on a clean corpus is reproducible; what flaps
is a **FAIL**, which a re-run clears ~60 % of the time. That is still the
serious form of the defect, and D1 stated it that way. STATUS did not.

---

## 1. Asserted confidently, and false or unsupported

Ordered by how far the assertion travelled from the report that could still
defend it.

### E3-1 — STATUS blocker 4, row 1: *"3.3 V CMOS clears it by 44 mV"* is not a valid comparison

`[repo] STATUS.md` lists, under **The four that block a merge → 4. Some fixes
are wrong, not merely incomplete**:

> | ADR 0004's DAC threshold | The corrected number **refutes the conclusion
> stated beside it**. 0.625 × 5.21 = 3.2563 V; 3.3 V CMOS clears it by 44 mV |

The arithmetic is right and I reproduced the datasheet read end to end
`[datasheet] SBAS430E p.4` — `V_INH` really is split at 4.5 V, `0.625 × AVDD`
is really in the MIN column (`[test]` word coordinates: MIN 411.0–423.8,
`0.625` at 381.5–399.0, phrase right-aligned into MIN; `0.3` at 469.9–479.6
against MAX 489.0–504.5), and `[datasheet] p.53` carries both revision-history
lines verbatim. **§1 of D12 is sound and I confirmed every part of it.**

**What is not sound is the inference.** `3.300 V` is a *supply rail*, not a
guaranteed output high. The comparison that decides "can 3.3 V CMOS drive this
pin" is `V_OH(min)` against `V_INH(min)`, and D12 itself establishes that the
first number does not exist:

> `[test]` `grep -rn "V_OH\|VOH\|0.8 *[×x] *VDD"` over the corpus → no output

I re-ran that and confirm it, and I add the other half: **no ESP32-S3 datasheet
is banked at all** `[test] ls datasheets/*/ ; grep -i esp32 datasheets/MANIFEST.csv`
— the five ESP32-S3-Matrix rows are a schematic, a pinout PNG, a dimensions
JPG and a CircuitPython pin map. So the corpus cannot decide the question in
*either* direction, and a comparison of a nominal rail against a MIN threshold
decides it in neither.

D12 knows this. Its **Uncertainty, stated** section says:

> What is a judgement call is whether the ADR should say the buffer is *needed*
> … or that 3.3 V *cannot* drive the pin (it can, at nominal).

That is a hedge. STATUS deleted it and promoted the result to a merge blocker,
and `VERIFIED.md` certified it with **"Computed it | Confirmed. 0.625 × 5.21 =
3.2563 V, and 3.3 V exceeds it by 44 mV."** The check verifies the
multiplication. The finding asserts the ADR's conclusion is FALSE. **A
verification that confirms a weaker statement than the finding it certifies is
the shape `CLAUDE.md` warns about most, and this is the clearest instance in the
file.**

**Correct disposition.** The ADR sentence is *unsupported*, not *false*. The
defect is that a sentence about logic levels is written with no `V_OH` anywhere
in the corpus or the bank — which is D12's own better finding, buried in its
third bullet. Severity: medium, documentation. **Not a merge blocker.**

Not disputed, and worth keeping: D12-1's observation that a `0.625 × AVDD`
threshold on a bench-selected rail is a **band, 3.125–3.44 V**, is correct and
is the right shape for the register entry D12-7 proposes.

### E3-2 — STATUS blocker 4, row 3: the clamp inversion is stated without its condition

> | The ADR 0014 lighting annotation | … the correction **inverts the clamp** it
> was defending — realistic use is 3.60 W against a ~3 W clamp |

`[calc]` The arithmetic holds: `[repo] 0014:132` single-hue-40 % is `0.13 A`;
`0.13 × 12 = 1.56 W`, which reproduces `[repo] 0014:173`'s `~1.5 W` exactly, so
D13's identification of "realistic use" is certain; at 45 mA/LED the same cell
is `0.30 A = 3.60 W` against `[repo] 0014:193`'s `~3 W`.

**The condition STATUS drops is the one D13 spends a page establishing.** The
45 mA/LED substitution is not settled. D13 §1a records the tension itself:

> 20.2 mA/LED × 12 V × 60/m = 14.5 W/m, which is very close to the 14.4 W/m
> that WS2815 60/m *tape* is commonly marketed at, while the IC datasheet
> implies 32.4 W/m. So the 2.23× is plausibly the known gap between an IC's
> constant-current spec and a tape vendor's W/m rating, and **neither number is
> a measurement.**

and D13 §2 concludes **"Not rewriting was the right call."** The ADR itself
declines to settle it and says so `[repo] 0014:149-152`. So "the correction
inverts the clamp" is a conditional consequence of a figure the same report
argues must not be treated as settled. STATUS states it flat.

`VERIFIED.md` reproduces the same omission: **"Computed both | Confirmed.
3.60 W — so the ~3 W clamp is 0.83× realistic use, not twice it."** The check
performed is the multiplication. The condition is not recorded.

**Correct disposition.** Real and important as a *conditional*: if the strip
figure resolves near the datasheet's, the clamp is below realistic use.
D13-2's recommendation — a `blocked` register entry plus a ROADMAP measurement
row — is the right action and is what makes the condition decidable. **Not a
merge blocker; it is a blocked measurement.**

### E3-3 — STATUS blocker 4, row 3 again: *"arithmetic that was never done"* is right, and its own magnitude is wrong

`[repo] 0014:141-143` says the WS2815's 2.1 mA quiescent *"reproduces ADR
0005's 123 mA figure exactly"*. `[calc]` 2.1 × 50 = 105. The word "exactly" is
false and D13-9 is right to file it.

But D13's stated magnitude — **"15 % out"** — is computed against a number D13
itself decomposes differently three sections later. `[repo] 0005:162` gives the
latched row as `1023 mA` in the `12 V direct` column, and D13 §3d derives *"the
12 V-direct cell is the strip full-white 1010 mA plus ~13 mA"*. Applying the
same decomposition to the quiescent row, `[calc] 105 + 13 = 118 mA` against the
stated `123 mA` — **4 %, not 15 %**. Two sections of one report use two
decompositions of the same column.

The finding survives (the adverb is unsupported either way), but the
**conclusion the annotation draws from it does not collapse**: "the two numbers
came from different sources and only the quiescent one came from the datasheet"
is still supported by 105–118 mA against 123 mA, and refuted by nothing. Calling
this row a fix that is *"wrong, not merely incomplete"* overstates it: one
adverb in one supporting sentence is wrong. **Severity: low.**

### E3-4 — STATUS blocker 4 contains a finding whose own slice says it does not block

`[repo] STATUS.md` row 4 of the blockers table is the `D-CLAMP-BREATH` edit,
built from D9-1/D9-2 (wrong part labelled, wrong claim recorded in the BOM
note) and D19 §C (drawing corrupted).

Both halves are real and I verified both independently:

```
[test] rail columns, breath-receive-stage.md
  line 65: ┼ at 68, ┼ at 70
  line 67: ┼ at 85, ┤ at 87        <- the prefixed line
  lines 63,64,66,68: │ at 68,70
[repo] hardware/bom.csv D-CLAMP-BREATH: qty 2, "Clamp diodes on the BREATH and
       AGND legs at the in-amp inputs", "behind the 10k series resistors"
[repo] hardware/bom.csv D-JACK-CLAMP:   qty 6, "on the DRIVER side of R-OUT-PROT"
[repo] breath-receive-stage.md:108-112: [1k] ─ [D-CLAMP-BREATH BAV99] ─ BREATH jack
```

The drawing at `:110` puts the label on the driver side of a 1 kΩ at the jack —
`D-JACK-CLAMP`'s described position, not `D-CLAMP-BREATH`'s. **D9-1 is right.**

**But D19, the slice that found the corruption, states in its own report:**

> `[repo] D19-conservation.md:496` — **None of these is a blocker for the
> merge.** Item 1 is the one that will cost someone an afternoon if it survives
> another wave.

A slice's finding appears in the wave's blocker table over that slice's
explicit contrary judgement, with no note that the two disagree. Seventeen
spaces of ASCII and a mislabelled clamp are a real defect and a cheap fix; they
are not a reason to hold a merge.

### E3-5 — `VERIFIED.md` certifies a package spec the repository does not contain

`[repo] VERIFIED.md`, D14 block:

> | **The height rule's ~1.4 mm cutoff is below the SOT-23 maximum it explicitly
> permits** (1.45 mm) | **Checked the package spec** | **Confirmed.** |

`[test] grep -ril "sot-23\|sot23" datasheets/` returns four files: a LilyGO
schematic PDF and three manifest CSVs. **No SOT-23 outline drawing is banked.**
D14's own report is honest about this — `[repo] D14 §3.1` marks SOT-23 1.45 mm
`[from memory]`, and `[repo] D14 §8` says *"0805 MLCC and SOT-23 heights are
`[from memory]`. No banked datasheet covers either; nothing in `datasheets/` is
a passive or a SOT-23 part."*

So the verification claims a check that could not have been performed against
the bank. The *neighbouring* row is the model of how it should read: D14-7's
SOIC-16 figure **is** `[datasheet]`-solid and I reproduced it —
`[datasheet] datasheets/logic/74HC165-nexperia.pdf` **p.14**, `SOT109-1`,
`MS-012`, `1.75` `[test]`. The height rule fails on SOIC-16 whether or not the
SOT-23 number is right, so D14's conclusion stands. The **verification line
does not**, and `CLAUDE.md` §3's whole point is that a number off a banked
document beats one from a review.

### E3-6 — `VERIFIED.md` certifies a 29-row census on a 2-row spot check

> | The reconciliation promise is mostly unkept … **7 of 29 do** … | **Spot-checked
> the two named as outright wrong** | **Confirmed on both.** |

The verdict is scoped honestly to the two rows. The prose four lines below is
not:

> 22 of 29 do not, so the mitigation that justified the decision is largely
> absent.

That sentence treats the census as verified. It was not; two instances were. I
re-ran one of the two and it holds — `[test] grep -n AGND
hardware/module/pitch-stage/pitch-stage.md` → exactly two hits, `:26` (the
Interfaces row making the claim) and `:201` (prose), **neither in a drawing**,
so D16-2 is right. The 7-of-29 denominator remains unverified by anything but
D16.

### E3-7 — STATUS's own datasheet count is wrong, in the sentence certifying datasheet counting

> `[repo] STATUS.md`: **141 corpus datasheet citations, 0 dangling.** 76 manifest
> rows against 76 files, both ways.

`[test]`
```
total MANIFEST.csv rows          101
rows naming a file                78
distinct files named              76
files on disk under datasheets/   76
on disk and not in the manifest   []
```

There are not 76 manifest rows; there are 101, of which 78 name a file and 76
are distinct. **This is exactly D11-7's finding** — *"'78 verified' counts rows,
not documents"* — restated in the summary in the form the finding says is wrong.
D11-7 is itself slightly under-stated: it names the DAC PDF as the double, and
there are **two** doubles `[test] analog/DAC8568CIPW.pdf, led/WS2815.pdf`.

### E3-8 — this round's own README miscounts the wave by 2.5×

> `[repo] docs/review/2026-09-22-fix-audit-review/README.md`: *"twenty reports
> and roughly a hundred findings"*

`[test]` Counting each report's own enumerated identifiers (`D<n>-<m>`, D1's
`F<n>`, D4's `D4.<n>`, D5's `R<n>`, D19's `A/B/C/D<n>`, D20's `A/B/C/D<n>`):

```
D1 13   D2 12   D3 10   D4 24   D5  6   D6 16   D7 12   D8 10   D9 14   D10 ~14
D11 13  D12 10  D13 15  D14 10  D15 17  D16 16  D17 16  D18  6  D19 ~14  D20 19
                                                                   TOTAL ~247
```

"Roughly a hundred" is the shape `D20-B` files seven instances of — a count
restated in prose, in the document that opens the round whose subject is counts
restated in prose.

### E3-9 — two smaller numeric errors inside otherwise-correct findings

- **D1-F3: "the other 12 figures … name it in `quantity:` not `value:`"** and
  *"1 figure of 32"*, *"12 of 13"*. `[test]` Over all 37 figures, exactly **11**
  name a real BOM refdes in `quantity:` and 1 in `value:`. D2's parallel
  measurement — 1 in `value`, **18** anywhere — I reproduced **exactly**:

  ```
  [test] in value: 1 ['spi-series-r']
         anywhere: 18  (quantity 11, derivation/note/forbidden/escape_note/floor/dc_error the rest)
  ```
  D1 and D2 are measuring different denominators (settled-only vs all;
  quantity-only vs all fields), which is legitimate, but D1 is one high inside
  its own denominator and only D2's number reached `VERIFIED.md`.

- **D10: "the register's value has been `359 mA` in all 20 recorded versions of
  `figures.yaml`".** `[test] git log --format=%h -- config/figures.yaml | wc -l`
  → **31**, and all 31 carry `"359 mA"`. D10's conclusion is right and stronger
  than it claims; its denominator is not the one git reports.

- **D3 47.9 % vs D5 48.4 %** for the exempt region. `VERIFIED.md` calls these
  "consistent"; they are two different measurements of two different things
  (D3 measures characters within 300 of *some* marker; D5 measures the exempt
  surface including `REFUTATION_SHOUT`). Neither is wrong; presenting them as
  independent agreement on one number overstates the corroboration.

### E3-10 — STATUS's *"D10 reversed a sibling's claim"* is not what happened

STATUS closes on this as the method earning itself. What D2 actually filed
`[repo] D2-new-checks.md:295-303`:

> **Either that is an accepted rounding** — in which case rule 1 says cite the
> figure … — **or** the figure moved from 360 to 359 and six statements did not
> follow. **What would settle it:** git-blame on those six lines against the
> commit that set `359 mA`.

D2 filed a disjunction and named the deciding test. D10 ran it. That is the
method working *as designed*, not one agent reversing another — and the
distinction matters, because the prompt for this round holds up that reversal
as the template for how many more wrong findings there might be. **There are
fewer of that shape than STATUS implies, because the original was already
hedged.**

D10's substance is right and I confirmed it independently:
`[test]` `umbilical-current` is `"359 mA"` in **all 31 recorded versions** of
`config/figures.yaml`, back to the file's creation. It never moved. A
`forbidden` pattern on `360 mA` would be the `CLAUDE.md` §2 trap.

---

## 2. Findings that are true but are not defects, or not the defect claimed

### E3-11 — three of D20's nineteen are the observer effect

`D20-A5` (the path map has an orphan), `D20-A7` (README says nine waves,
directory holds ten), `D20-A8` (CLAUDE.md says nine) and `D20-B7` (the wave
README's own "85 corpus files") are **all caused by the act of opening the
audit**. `[repo] D18` says so explicitly and well:

> **The orphan is the commit that opened this wave.** The map was whole for
> exactly two commits and broke on the next one — which was me writing the
> README for the audit that then found it.

They are true, they are diagnostic — D18's point that a hand-maintained census
goes stale on the first commit after it is written is the most useful thing in
that slice — but counting them toward *"the tenth round is partial too:
nineteen defects"* conflates "the fix batch did not land" with "writing the
audit changed the tree". Round 2 has now added a twelfth directory and a
second orphan, and will add more. **Corrected: sixteen of D20's nineteen are
defects in the fix batch; three are defects in the reviewing.**

### E3-12 — `D4.21`/`D4.22` are real and do not touch the corpus

`[test]` I reproduced D4.21 exactly at `0576a95`:

```
$ python3 tools/rewrite-paths.py --invert --baseline 81c081d
invert: 55 file(s) byte-identical under inversion, 2 hand-edited/skipped, 112 MISMATCH
  ... "not present at baseline 81c081d"
```

The finding is correct and STATUS is right that the proof it cited no longer
proves. But the row is filed under **"Some fixes are wrong, not merely
incomplete"**, and what is wrong is a *tool's domain*, not a corpus statement.
D4 says so itself — *"Phase A's conservation is still supported — by the
per-file blob hashes checked by hand at the time, and by the cold conservation
re-run at HEAD — but not by this."* Nothing in the tree is wrong because of it.

### E3-13 — the plate standoff: right in direction, and the "right answer next door" is an inference, not a record

STATUS: *"ADR 0002 already held the right answer — 2.50 − 1.20 = **1.30 mm** —
in the same batch."*

`[repo] 0002:181` holds *"at 1.20 mm the plate consumes only 48 % of the
2.50 mm through-section"*. `[calc]` 1.20/2.50 = 48 % ✓. To get **the
plate-to-PCB standoff** out of that you need the premise that the PCB seats on
the switch housing bottom — and D14's own closing line is:

> **Nothing in the corpus records whether the cluster PCB seats against the
> switch housing bottom.** The entire standoff number, the height rule, and ADR
> 0002 requirement 2 all hang on that one line.

So ADR 0002 held one of the two inputs, not the answer. D14 is careful about
this (it labels its own 1.30 mm an inference from three pieces of evidence);
STATUS is not. The arithmetic D14 does verify is solid and I re-derived it:
`[calc] p = 5.10 − d − 1.6` gives +0.30 / 0.00 / **−0.10 mm** at d = 3.20 /
3.50 / 3.60, so the upper end of the published window is impossible. **The
finding is right; the "the corpus already had it" framing is not.**

### E3-14 — three deliberate `TBD`/blocked states filed as defects

`CLAUDE.md` is explicit that a blocked row naming its decider is *"correct, not
a defect"*. These are on the edge of that line:

- **D11-6** — `BLOCKED` written into the `sha256` column of the two new manifest
  rows. `[test]` 21 other no-file rows leave it empty, so the inconsistency is
  real, but the row is *more* informative than an empty cell, and nothing reads
  the column. Severity medium is high for a cosmetic schema deviation in a
  deliberately-blocked row.
- **D11-12** — the two BLOCKED rows record candidate URLs "with no attempt
  evidence". `CLAUDE.md` §3 asks for *"the exact URLs"*, which is what they
  carry.
- **D13-8** — `D-TVS-BREATH`'s three unsourced numbers. The gap **is** recorded,
  in the manifest, in full, and D13 says so. The finding is that it is not also
  in the BOM row. That is a real completeness point; it is not an unmarked gap.

---

## 3. Double-counting: what the wave actually found

The wave sliced by fact domain, which is the right method and which
*guarantees* that one defect reaches several slices from several sides. That is
evidence, not inflation — but the headline counts never subtract it.

Clusters I can evidence, with the filings that make them up:

| # | Defect | Filed as | Filings | Distinct |
|---|---|---|---|---|
| 1 | `ROADMAP.md:71` "neither is published" | D7-4, D8-1, D14-9, D15-11 | 4 | 1 |
| 2 | Refutation vocabulary widened by date/`->`/`→`/`NOT` | D1-F4, D3-*, D5-R1, D5-R2, D5-R3, D7-2 | 6 | 1 (D5 files one root cause as three) |
| 3 | Three patterns containing their own marker | D3, D7-3, + a third slice per `VERIFIED.md` | 3 | 1 |
| 4 | `](page.md#anchor)` links unchecked | D1-F5, D5-R5, D20-C5 | 3 | 1 (+1 for the anchor itself) |
| 5 | `check_owners` exclusive `or` | D1-F1, D5-R4 | 2 | 1 |
| 6 | `check_bom_figures` coverage | D2-1, D1-F3 | 2 | 1 |
| 7 | `U-BREATH` "CONFIRMED as 0.2 to 4.8V" | D8-6, D13-3 | 2 | 1 |
| 8 | stale `125 µs` (two sites) | D8-2, D15-1, D15-2 | 3 | 2 |
| 9 | duplicate `false_positive_note` key | D12-7, D20-C1 | 2 | 1 |
| 10 | `0004:842` bare `97 mm` | D20-A2, D12-10 | 2 | 1 (handed, not independent) |
| 11 | `0004:506` "same safe state" | D20-A1, D12-9 | 2 | 1 (handed, not independent) |
| 12 | `repo-maintenance.md:204` "50 rows of 138" | D19-B1, D20-B2 | 2 | 1 |
| 13 | unplaced/BOM counts across four documents | D19-B2, D20-A3, D20-B1, D20-B4, D10 §4 | 5 | 4 (four files) |
| 14 | Gateron char count (9,680 / 11 kB / 11,053) | D8-9, D14 §2, D20-E | 3 | 1 |
| 15 | `verify-datasheets` advisory discarded / `msgs[:40]` | D4.18, D11-9 | 2 | 1 |
| 16 | `dac-rail` restated in derived drawings | D7-11, D16-10 | 2 | 1 |
| 17 | `D-CLAMP-BREATH` edit | D9-1, D9-2, D19 §C, **D20-E (opposite verdict)** | 4 | 2 |

**49 filings → 22 distinct defects; 27 excess filings.**

Two of the seventeen deserve the label *independent corroboration* rather than
duplication, and should be kept as such: #9 (D12 and D20 found the same silent
YAML key with no contact) and #2 (D3, D5 and D7 reached the vocabulary defect
from three directions). The rest are the same defect reported from different
sides, which is the slicing working.

---

## 4. Findings that contradict each other

### E3-15 — D20 certifies as VERIFIED the two things D9/D19 and D12 file as defects

`VERIFIED.md` accepted both sides of each pair and reconciled neither.

**(a) The `D-CLAMP-BREATH` edit.**

> `[repo] D20-completeness.md:142` — | `04b5208`: `D-CLAMP-BREATH` *"the drawing
> names it now, and the row is placed"* | **VERIFIED** `[repo]
> breath-receive-stage.md:67` and `:110` both write the refdes |

against D9-1 (`:110` labels the wrong part) and D19 §C (`:67` corrupted the
drawing). **D20 is right that the refdes now appears twice and wrong that this
is what the commit claimed to achieve.** D20's test — "does the string appear" —
is strictly weaker than the claim it certifies. **D9 and D19 are right; D20's
E-table row should be withdrawn.**

**(b) The `V_INH` fix.**

> `[repo] D20-completeness.md:122` — | `b32c557`: ADR 0004's `V_INH` 3.65 V →
> **3.26 V**, *"the conclusion survives"* | **COMPLETE** `[calc]` `3.65` appears
> once in the corpus, in its own refutation |

against D12-1, filed HIGH, on the same sentence. D20 checked *reach* (is the old
number gone) and reported COMPLETE on a quoted phrase it did not evaluate. D12
evaluated the phrase and, per E3-1, overstated the result. **Neither verdict is
usable as written: the correct answer is that the sentence is unsupported by
anything in the corpus, which is what makes it a documentation defect rather
than either a completed fix or a false claim.**

### E3-16 — D19 against STATUS on whether any of D19's findings block

Stated at E3-4. D19 §"Findings a fixer could act on" ends *"None of these is a
blocker for the merge."* STATUS puts one of them in the blocker table.

---

## 5. Claims resting on the broken checker — sorted

The round-2 README warns that "the checker reports PASS on this" may be true,
false or unfalsifiable. Sorted, with the frozen commit pinned:

**Reproducible, and true at `0576a95`** `[test]`:

- *All 68 forbidden-pattern matches are exempted; the live list is empty*
  (D3, and STATUS blocker 2). Reproduced: the `STALE VALUES` block does not
  print. Removing **only** the four added markers gives
  `STALE VALUES STILL LIVE (6)` / `refuted in place (62)`; the repaired tool at
  HEAD gives 8 live across 3 figures and 4 distinct texts, which matches D3's
  *"8 records, 4 distinct pieces of text, each appearing once in
  `hardware/bom.csv` and once in the fragment it is generated from"* **exactly**.
- *`REFUTATION_SHOUT` is dead weight: deleting it changes nothing, 68 → 68*
  (D3). Reproduced by neutralising the regex: `PASS`, 68 refuted, unchanged.
- *`WIRE-LOOM` is still live* (D3, STATUS). Reproduced — under the repaired
  vocabulary `hardware/bom.csv:30` and `hardware/carrier/bom.csv:6` report
  `[chain-connectors] found 'five connectors must match'`, and the row is
  `WIRE-LOOM`.
- *The documented `C-GATE-LOADSW` change reproduces green* (D2-1, STATUS
  blocker 3). Reproduced end to end: fragment edited 82nF→100nF, `merge-bom.py`
  → *"wrote 139 rows from 26 fragments | 0 problems"*, register value updated,
  `check-staleness.py` → `PASS`.
- *`check_bom_figures` reaches 1 figure of 37; 18 name a refdes elsewhere*
  (D2-1). Reproduced exactly.
- *`--invert` gives 112 MISMATCH on a healthy tree* (D4.21). Reproduced exactly:
  `55 byte-identical, 2 skipped, 112 MISMATCH`.

**Unfalsifiable at HEAD, reproducible only at `0576a95`:** every bare
`[test] check-staleness.py → PASS` quoted as context by D12, D13, D14, D15 and
D20. None of them is *wrong*; all of them are now un-runnable as written,
because `566159e` changed the instrument. Any round-2 slice that re-runs at
HEAD and reports a contradiction is reporting §0(a), not a defect in the wave.

**Overstated:** STATUS's *"Every PASS quoted in the last two days was a sample
from a distribution nobody knew existed."* `[test]` On a clean corpus the tool
is deterministic across eight hash seeds. The flap requires a live violation.
D1 stated it correctly; the summary generalised it.

---

## 6. Claims resting on a datasheet read nobody re-did — spot-checked

Seven re-reads, with PyMuPDF 1.28.2 per the wave README's route.

| Claim | Slice | Verdict |
|---|---|---|
| SBAS430E p.4 splits `V_INH`; `0.625 × AVDD` is the MIN-column value for 4.5–5.5 V | D12 §1 | **Confirmed**, including by word coordinates |
| SBAS430E p.53 revision history splits the parameter deliberately | D12 §1 | **Confirmed**, both lines verbatim |
| SBAS430E p.2 abs max: digital input `–0.3 to +AVDD + 0.3` | D12-2 | **Confirmed**, three rows |
| "Package Option Addendum (p.54-57)" is really p.54–55 | D11-11 | **Confirmed** — pp. 54–55 are the addendum, pp. 56–57 are *Tape and Reel Information* |
| 74HC165 SOIC-16 `A` max 1.75 mm, SOT109-1 / MS-012 | D14-7 | **Confirmed**, p.14 |
| SOT-23 max 1.45 mm "checked against the package spec" | `VERIFIED.md` | **Not supportable** — see E3-5 |
| 78 manifest rows ↔ 76 files | D11-7 | **Confirmed**; two documents doubled, not one |

Datasheet work is the strongest part of the wave. The one failure is in the
verification file, not in a slice.

---

## 7. The `VERIFIED.md` audit

104 table rows. `[test]` **44** carry the word *Confirmed* with a check
described; **31** carry *Accepted* with no independent check described at all.

**Where "Accepted" lands matters.** The entire D9 block is four rows of
*Accepted* — including `D9-1`, the mislabelled clamp, which STATUS then promotes
into the merge-blocker table. A claim that reaches the blocker list on the
strength of "Accepted as high-confidence" has been through no second pair of
eyes. (It happens to be right; I checked it, §E3-4. That is luck, not process.)
The same applies to all four D8 rows, six of seven D7 rows, and D11's headline
`DAC8568ICPW` row, which is accepted on the grounds *"it matches my own earlier
extraction"* — verification against the verifier's own prior work.

**Three rows certify a stronger statement than their check supports:**

1. D12-1 — check is the multiplication, verdict is "the conclusion is FALSE"
   (E3-1).
2. D14-6 — check is "the package spec", which is not in the repository (E3-5).
3. D16-1 — check is two rows, verdict is used as a 29-row census (E3-6).

**Two rows are honest about a weaker scope and should be read that way:**
D19's *"Confirmed on the counts I checked"* under a claim beginning "Every count
written in the batch is already wrong", and D16's *"Spot-checked the two named
as outright wrong"*. Both verdicts are correctly hedged; both headline claims
are stated without the hedge in the prose beneath.

**What the file does exceptionally well**, and should not be lost: it records
where the fixer was wrong about their own work, by name, with the mechanism —
the `WIRE-LOOM` entry (*"I narrowed the vocabulary and added a looser marker in
one edit, named this exact row in the commit message, and the row survived"*)
is the single most useful paragraph produced by the wave, and I reproduced it.

**What it does not do at all:** reconcile the two places where slices
contradict each other (E3-15). Both sides are recorded as accepted. A reader of
`VERIFIED.md` cannot tell that D20 and D9 filed opposite verdicts on the same
eleven lines of one drawing.

---

## 8. Corrected tally

**Method, stated so it can be disputed:** "filed" counts each report's own
enumerated identifiers. "Distinct" subtracts the 27 excess filings in §3 and
the three observer-effect items in §E3-11 from the D20 count where they are
also filed elsewhere. "Real" means I could not break it, or I re-derived it;
"blocking" means a merge would ship something that is wrong or unbuildable.

| | Count | Basis |
|---|---|---|
| Filed findings across 20 reports | **~247** | §E3-8 (README says "roughly a hundred") |
| Excess filings from cross-slice duplication | **−27** | §3, 17 clusters evidenced |
| **Distinct defects** | **~220** | |
| Of the 35 I re-derived independently | | |
|  … held exactly | **29** | §5, §6, and D6-1, D6-4, D16-2, D19 §C, D9-1, D10/D9 BOM mechanics, D20-B2/B5/B6 |
|  … held, with a numeric or scope slip inside a correct finding | **4** | E3-2, E3-3, E3-9 (D1-F3's 12, D10's 20), E3-13 |
|  … not supportable as stated | **2** | E3-1 (D12-1 as STATUS states it), E3-5 (a `VERIFIED.md` row) |
| **Sampled correctness** | **83 % exact, 94 % directionally right** | 29/35 and 33/35 |
| True but not a defect, or not the defect claimed | **~6** | §2 |
| Observer-effect defects (created by reviewing) | **4** | D20-A5, A7, A8, B7 |
| **Genuinely blocking at `0576a95`** | **3** | STATUS blockers 1, 2, 3 — all instrument defects, all reproduced, all now fixed by `566159e` |
| Filed as blocking and not blocking | **5 of 5** | STATUS blocker 4's table: two overstated (E3-1, E3-2/3), one whose own slice says it is not (E3-4), one mis-framed (E3-13), one that touches no corpus content (E3-12) |
| Blocking and **not** in STATUS's blocker list | **3** | D10's hard ordering blockers: `U-LOADSW` (no FET part number), `D-RESP` (DO-35 part in a SOD-123 package), `D-USBOR` ("1N5817 or SS14" in DO-41, where SS14 is SMA) |

**The severity is not inflated so much as misallocated.** The three findings
that stop a human doing something — you cannot order this BOM — are in D10 and
appear nowhere in the verdict. The five in the blocker table are a
documentation sentence, a conditional watt, an adverb, seventeen spaces of
ASCII and a tool's domain.

---

## 9. Where the wave was right, stated plainly

A slice that only lists errors gives no way to tell a careful report from a
lucky one, so:

- **D1-F2** is the best finding in the wave and I reproduced its distribution by
  accident on a different figure (§0b). **D1-F1** is correct and I confirmed the
  regression mechanism in the code.
- **D3** is the most accurate report I read. Every measurement I re-ran came
  back identical, down to "8 records, 4 distinct pieces of text".
- **D2-1** reproduces exactly, both halves — the 1-of-37 coverage and the
  green `C-GATE-LOADSW` failure.
- **D4.21** reproduces to the digit.
- **D9**, **D10** and **D19** on the BOM's mechanics agree with each other and
  with me to the byte: 131,725 bytes, 139 rows, 140 CRLF / 0 bare LF, 11
  columns, no duplicate refdes, `merge-bom.py --check` 0 problems.
- **D12 §1** is the best-sourced datasheet work in the wave; its only defect is
  what it concluded *from* it.
- **D13** wrote its suggested patterns in the spelling of the files they must
  match and recorded sixteen legitimate hits with a warning not to add a bare
  pattern. That is `CLAUDE.md` §2 followed, not recited.
- **D14** flagged every weak input of its own in a section headed "What I could
  not settle", which is why E3-5 and E3-13 are findings against the *summary*
  and not against D14.
- **D20** is the most useful single report, and its one-line diagnosis — *a
  count restated in prose is a forbidden pattern nobody wrote* — is worth more
  than most of the findings it supports. I verified three of its seven counts
  (B2, B5, B6) and all three hold.

---

## 10. What would settle the ones I could not

- **E3-1.** Bank an ESP32-S3 datasheet and record `V_OH`. Until then neither
  "3.3 V CMOS cannot drive it" nor "it clears by 44 mV" is a claim the corpus
  can carry. One row in the register, `dac-vinh`, value stated as the band
  `3.125–3.44 V`, is the mechanical half — D12-7 already specifies it.
- **E3-2.** One current probe on one strip's +12 V feed at commanded full
  white, at M6. Every conditional in D13 collapses to a number.
- **E3-13.** One sentence: does the cluster PCB seat against the switch housing
  bottom? D14 names this as the single missing sentence in the corpus and it is.
- **E3-9 (D1-F3's 12 vs 11).** Re-run the field census with the denominator
  stated. My script counted refdes tokens matching `\b[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+\b`
  against the 139 BOM refdes, over every field of all 37 figures.
- **§3's cluster table.** It is built from the reports' own text. A slice with
  time should rebuild it from node indexes rather than from prose, which is
  what node-indexed findings exist for and what would have made the duplication
  visible to the wave itself.
