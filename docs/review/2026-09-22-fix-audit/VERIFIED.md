# Verified by hand — fix-audit wave

A finding is a claim. This file records what was checked against the corpus
and where an agent was right or wrong. Checked as reports land.

## D16 — the net renames

| Claim | Check | Verdict |
|---|---|---|
| The reconciliation promise is mostly unkept: `hardware/README.md`, `pcb-pipeline.md` and `breath-sense-link.md` all state that **every** qualified row names the drawing's own spelling; **7 of 29 do**, and 3 of those 7 are cleanly correct | Spot-checked the two named as outright wrong | **Confirmed on both.** |
| `pitch-stage.md:26` says `AGND_MOD` is "drawn `AGND`", and that page's drawing contains no `AGND` | `grep -c AGND` on the file | **Confirmed. Two hits, and neither is in a drawing** — one is that row itself, one is prose at `:201`. The reconciliation instruction points at a spelling that is not there |
| `breath-output-stage.md:23` still instructs the reader that the drawing "restates the figure's value in the label" — **after** `79f5c4a` removed that label | Read the row and grepped the page for `5.21` | **Confirmed.** The label is gone; the row still describes it. `5.21 V` does survive at `:126` and `:129`, but in a table and in prose, not the label the row names |

The third one is the finding. **It is this project's named failure mode,
occurring inside the commit that was fixing that failure mode, in the one row
whose entire content is a reconciliation instruction.** I removed a drawing
label and did not update the row that exists to describe it.

And the first one indicts the decision, not just the execution. Leaving the
drawings alone was defensible *only because* every qualified row was supposed
to name the drawing's spelling. 22 of 29 do not, so the mitigation that
justified the decision is largely absent. D16's recommendation — relabel the
drawings, ~25–30 genuine net tokens across 9 files, verifiable in one grep —
is the right call, and `79f5c4a` already did exactly that for
`digital-and-supervision.md` and left three identical cases.

## D18 — the path map

| Claim | Check | Verdict |
|---|---|---|
| **The map's content is sound** — old side an exact bijection onto `81c081d`, all 22 datasheet corrections right, WS2815 SHAs confirmed | Re-measured the shape | **Confirmed.** 410 rows, and the corrections hold |
| `repo-maintenance.md` §7's unhedged "every tracked file has a row" is **already false at HEAD** | `git ls-files` against the map | **Confirmed. Exactly one orphan: `docs/review/2026-09-22-fix-audit/README.md`** |
| §7's "410 rows: 405 tracked files, plus 4 `deleted` and 1 duplicate destination" | Counted | **Confirmed wrong, in both parts.** 406 non-deleted rows, **406 distinct destinations, zero duplicates**, 4 deleted. 405+4+1 sums to 410, which is why it reads correct |
| Nothing runs the four-line check §7 tells a maintainer to run | Grepped the tools and the hook | **Confirmed.** The one artefact with a written, tested invariant is the only one not wired to the commit hook |

**The orphan is the commit that opened this wave.** The map was whole for
exactly two commits and broke on the next one — which was me writing the
README for the audit that then found it. A census that must be hand-maintained
goes stale on the first commit after it is written, and this is the proof.

D18's structural point is the one worth keeping: the map does **two** jobs.
Resolving a path quoted in a dated record needs only the 287 old-side rows
plus the moves and deletes, its domain is an immutable tree, and it *cannot*
go stale. The 123 `created`/`created-history` rows — 30 % of the file — exist
only to satisfy a census, answer no question a reader of a pre-restructure
record can ask, and are the half that breaks on every commit.

Its measurement is the thing nobody had done: **429 distinct path tokens in
the review and log records, 6,027 occurrences, 91.4 % resolving with no
effort and 96.1 % resolving at all.** That is the only number that says
whether the mechanism works.

## D3 — the refutation exemptions, and the worst finding of the wave so far

| Claim | Check | Verdict |
|---|---|---|
| **All 68 forbidden-pattern matches are exempted; the live list is empty** | Ran the checker verbose | **Confirmed.** The `STALE VALUES` section does not print at all. `PASS no live stale values` currently means *nothing fired*, not *nothing matched* |
| `WIRE-LOOM` still says "five connectors must match" against `chain-connectors` = **8**, and `0e68f25`'s own commit message names that row as one of the two escapes it was closing | Read the row; measured the marker distance | **Confirmed, and it is mine.** The pattern `"five connectors must match"` is in the register and it *matches*. The old exemption was an unrelated `rather than` at 24 characters, which that commit dropped — and the new exemption is the dated marker `DECIDED 2026-09-21:` at **222 characters**, a clause I added in the same commit. `J-CHAIN`, two rows away in the same generated file, says "EIGHT of them, not five" |

**I narrowed the vocabulary and added a looser marker in one edit, named this
exact row in the commit message, and the row survived.** Net effect on the
case I claimed to close: zero. The other named case, `FB-IN`, *is* closed —
because it was fixed by editing the text rather than the regex. That contrast
is the lesson.

D3's measurements, which nobody had:

- **47.9 % of the corpus lies within 300 characters of some marker** — that
  much of it is a place where no pattern can ever fire. Concentrated exactly
  where stale values live: every `notes.md` is 85–100 %, BOM fragments 85–93 %.
- **`REFUTATION_SHOUT` is dead weight.** Deleting it changes nothing: 68 → 68.
  It appears in 12 windows and **only 2 are corrections**; the rest are design
  rules like "must NOT share a diode". `DO NOT CUT THE PANEL HOLE` sits 57
  characters from a match in `bom.csv`.
- **The window does not bite at all.** Exempt at w=300 and exempt at
  whole-file are both 68. The data supports **[166, 221]**: the largest
  legitimate distance is 165, the smallest bad one is 222.
- **Three patterns self-exempt and can never fire anywhere**, because they
  contain a marker themselves — `VALUES NOT SET`, `0.2 → 4.8 V`,
  `75 mV → LM317`. One belongs to `sensor-full-scale`. `check_patterns()`
  looks only for newlines and passes all three.
- **Something was lost after all.** The corpus's house style for an ADR
  refutation is "**An earlier revision** …", and `earlier` was dropped: 60
  such openers, **41 with no surviving marker within 300 characters**.

## D17 — the dependency graph

| Claim | Check | Verdict |
|---|---|---|
| The rebuild's numbers are exactly as claimed, and the stated rule is followed without exception | Re-measured | **Confirmed.** 96/48/0/0, 23 ids all matching their directories |
| **Five of 48 edges point at `module/link-supervision`, which is NOT FITTED** | Counted the declaring circuits; read the page | **Confirmed.** Five circuits declare it; the page opens "**NOT FITTED. Nothing in this directory is on the board**", all five of its Interfaces rows begin "Not fitted", and it is the only circuit directory with no `bom.csv`. Its degree is higher than `pitch-stage` or `mod-channels`, which exist |
| The one-source rule is violated by `in-amp output`, and commit `6645fb7` verified that invariant on the DAC's SPI nets only | Grepped both tables | **Confirmed.** `breath-sense-link.md:59` and `breath-receive-stage.md:45` both declare it `out`. I checked the rule where the defect had been reported and did not re-run it generally |

**"Matches the tables" is not "verified", and the header says verified.** The
commit message for `6645fb7` says plainly *"it was seeded from them"*;
`hardware/README.md:12` still says `SEEDED, NOT VERIFIED`. Three wordings,
one graph.

D17 also finds the reciprocity model wrong on its own terms: `Dir` was
present in every row and was discarded when the edges were rebuilt from
`Peer` alone, so every edge is now a 2-cycle and **no topological order
exists** — a bring-up order gets nothing rather than an imperfect answer. And
the three known-false `refdes:` edges are **at least eleven**, two of them
carrying the literal sentence "the part is not here".

Its methodological note is worth keeping: the three `interfaces/**` tables
carry a sixth `End` column, so a fixed column index gives three false
mismatches; and `module/panel` is a substring of `module/panel-led`, so naive
matching invents four edges. Both are traps for the next person who measures
this.

## D19 — conservation. MANDATORY SLICE, and the batch passes it

| Claim | Check | Verdict |
|---|---|---|
| **Nothing was lost.** Zero distinct numeric tokens left the corpus (998 → 1,041; the *gone* set is empty). All 18 rows that left `unplaced.csv` landed. No `figures.yaml` entry or field removed. No file deleted or renamed. The history rule held — the only `docs/review/**` change is a pure `+27/−0` append | Re-measured the counts | **Confirmed.** This is the one thing the batch did cleanly, and it is the thing that most needed to be clean |

**But six findings, and two are mine and concrete.**

| Claim | Check | Verdict |
|---|---|---|
| **An ASCII drawing was corrupted by my own fix.** `breath-receive-stage.md:67` — prefixing `[D-CLAMP-BREATH] ` pushed that line's rails from columns 68/70 to **85/87** while every neighbouring line stayed at 68/70 | Measured the rail column on lines 63–71 | **Confirmed exactly.** Lines 63, 64, 65, 66, 68 all have rails at 68/70; line 67 has them at 85/87. **The clamp now connects to nothing and the sense pair has a one-row break.** I lengthened a line inside a picture and did not re-check the picture |
| `repo-maintenance.md:204` still says `unplaced.csv` "holds the **50 rows of 138**" | Read the line; counted the files | **Confirmed. It is 32 of 139.** `hardware/README.md`'s duplicate of that same paragraph *was* rewritten in this batch; this one was not — in the document that owns `bom.csv`, four lines from a note about exactly this failure |
| **Every count written in the batch is already wrong**: 34 vs **32** rows, 75 vs **67** units, master 138/388 vs **139/390**, "Sixteen" moved vs **18**. And `pcb-pipeline.md` still names `J-CV ×6` and `D-CLAMP-BREATH ×2` as unplaced — *this same batch placed both* | Spot-checked the row counts | **Confirmed on the counts I checked.** The numbers were written mid-batch and the batch kept moving under them |

Two more worth keeping:

- **The only genuinely lost content in the whole batch**: the `circuit.yaml`
  header rationale, deleted identically from all 23 files and relocated
  nowhere — why there is deliberately no `revision` key, why no
  `figures_owned` ("that would put ownership in two files, which is rule 1
  broken in the project's own metadata"), and why `depends_on` is seeded
  rather than empty ("it fails SILENT"). It survives only in a review
  directory, which cold reviewers may not read. **A future editor adding
  `figures_owned:` will find no objection anywhere in the corpus.**
- **`hardware/README.md:47` narrates a deduplication that did not happen.**
  No circuit page ever *defined* `Dir`/`Peer`; the columns were used and
  undefined. The new section is a real improvement — only its history is
  invented. That matters because this corpus uses those parentheticals as its
  record of what was wrong before.

D19's method caveat is worth passing on: it treated `check-conservation.py` as
evidence rather than proof, because that tool was itself changed in the batch.
Across 39 changed files it reported ~180 gap/head/tail/thinned hits and **not
one survived inspection**. All four of D19's positive findings came from hand
comparison and census scripts. The new head/tail and multiplicity checks fire
correctly; they just found nothing here.

## D2 — the two new checks, and the flagship fix reaches one figure of thirty-seven

I called `check_bom_figures()` "the one that matters" in its own commit
message. It is correct, it has no false positives, and it is very nearly
inert.

| Claim | Check | Verdict |
|---|---|---|
| **Coverage is 1 of 37 figures.** `REFDES_IN_VALUE` reads `fig["value"]` only; just `spi-series-r` names a BOM refdes there. **18 figures name a real BOM refdes somewhere in their entry** — in `derivation`, `note` or `owner`, fields the check never opens | Enumerated every figure's fields against the BOM's refdes set | **Confirmed exactly. 1 in `value`, 18 anywhere.** The check reaches one of the eighteen figures it is about |
| **The documented failure reproduces green on a different part.** `C-GATE-LOADSW` 82 nF → 100 nF by the documented procedure | Ran the three steps in a `git archive HEAD` copy | **Confirmed. `merge-bom.py`: "0 problems". `check-staleness.py`: `PASS`, byte-identical to baseline** — while the register and the owner page still derive 49/98/197 ms from 82 nF |

**So the exact failure I built that check to prevent still reproduces on the
next part anyone tries.** I proved the fix against the one case that motivated
it and never measured its reach.

D2 names the seventh fail-open, and it is this: **coverage is unreported.**
Every other check in that file carries a coverage number on purpose — the
commit message says "a run with no coverage used to print the same PASS line
as a healthy one" — and this one carries none. Rewording `spi-series-r`'s
value from `"100 ohm, R-SPI-SER, qty 3"` to `"100 ohm on SCLK, MOSI and CS,
qty 3"`, no change of meaning, takes coverage 1 → 0 **silently**.

And the obvious repair does not work. D2 moved the refdes into `value` for
the 7 settled figures that name one, leaving the BOM correct: **5 of 7
false-fail.** `primary = max(nums, key=len)` picks `197` out of
`"82 nF, ramp 49-197 ms (98 ms typ)"`; one `primary` is compared against
*every* refdes, so a multi-part figure can never pass; and a count (`24`) is
not a part value (`2k2 1%`). Each one's cheapest fix is to damage a correct
sentence — the anti-pattern `CLAUDE.md` names.

It also recommits trap 1 from `CLAUDE.md` §2 **inside the new check**:
register `2.2 kohm` against BOM `2k2 1%` false-fails, and `37.4 ohm` versus
`37.4R` passes only because the digits coincide.

### `check_restated()` — ~50 % signal, and the holes are not where I looked

| Finding | Verdict |
|---|---|
| Sample of 40, classified against real occurrences: **53 % real**, the rest collisions, datasheet quotes, one footprint (`1.25 mm`, rank 2, 17 files), one mathematical invariant | Plausible and carefully done |
| **Raising the threshold does not help**: 3→233, 4→128, 5→73, 6→39, 10→10, and the ≥6 band is still ~50 % real. The noise is at the **head**, not the tail | The measurement I should have made before shipping it |
| **The biggest hole is silent**: `if n in known` matches bare digits, not number+unit, so **93 of 146 suppressions are spurious** — `5 V` hidden in **38 files** because the digit `5` appears in the umbilical pinmap; `250 µs` hidden by a `us`/`µs` spelling mismatch | This makes the advisory itself wrong, not merely noisy |
| **`NUM_UNIT` cannot see R-notation at all** — `10k` in 29 files, 30 distinct such tokens. Resistors are the most-changed part class here and the check's own worked example | Trap 1 for the third time in one day |
| Parse bug: the trailing guard permits `/`, so `0.7665 V/kPa` is filed as `0.7665 V` and `3 ppm/°C` as `3 ppm`. **A rate recorded as a level** | Real |

D2's verdict — keep it advisory — is right, and its reasoning is better than
mine was: ~50 % precision with no knob that improves it means ~117 hand-written
exemptions before the first green build, and that list is itself a derived
document that fails **open** when a number moves.

### Three claims handed to other slices

- **`360 mA` in 6 corpus files against a register that says `359 mA`**
  (`umbilical-current`, derivation 358.1 mA).
- **`0.265 V` in 6 files** — the sensor pedestal, tracked only inside another
  figure's free-text `derivation`, while its predecessor `0.200 V` has eleven
  forbidden patterns against it.
- **`120 mV`** — one of the three figures `CLAUDE.md` §3 names as corrected off
  a banked datasheet, restated in 3 files, still not in the register.

## D20 — completeness. MANDATORY SLICE. Ten for ten.

Nine waves had found the previous round's fixes partial. **The tenth is
partial too: nineteen defects.**

The shape is the finding. All four tools are green at HEAD, and **every one of
the nineteen is invisible to all four**. Not one is a wrong value at the site
of an edit — **fifteen of nineteen are on a page that cites the page that was
fixed.** The fixes are *correct* and they have not *arrived*.

| Claim | Check | Verdict |
|---|---|---|
| **A refuted claim is live in the ADR that cites the ADR which refuted it.** `0004:506-510` says an A/C grade part "parks pitch subsonic and the mod channels at 0 V (ADR 0006), **the same safe state as rack power-on**" | Read the lines | **Confirmed.** Yesterday I established in ADR 0006 that power-on is **0.000 V** and the CLR park is **−2.500 V** — *"different states, 2.5 V apart."* This ADR now asserts the exact equivalence that fix destroyed, and cites the document I fixed as its authority. Qualified fairly by D20: "parks pitch subsonic" is defensible in the watchdog context; the equivalence is not |
| **`0004:842` carries a retired `97 mm`**, 52 lines under a table that now totals 110 mm, and **no pattern matches a bare `97 mm`** | Read the line; tested all twelve patterns against it | **Confirmed. Zero matches.** The list holds `= 97mm` and `97 mm against ~110 mm`; the live spelling is neither. Tenth spelling of that figure's family |
| **`config/figures.yaml` has a duplicate `false_positive_note` key** on `panel-height-budget`, and `yaml.safe_load` silently keeps the last | Counted the keys; loaded the file | **Confirmed. Two keys, at :408 and :423.** `safe_load` keeps :423. **The note I wrote yesterday is silently discarded** — the one recording that `panel.md:20` and `0004:736` legitimately narrate the review. Sole instance in the file, and a new member of the YAML class I had recorded as caught |

**Seven meta-document counts are wrong at HEAD**, every one of them a number
restated in prose rather than cited — which is to say a forbidden pattern
nobody wrote. Among them: `repo-maintenance.md:204`'s "50 rows of 138" (never
updated at all), `pcb-pipeline.md`'s BOM table whose master count went 138→139
**inside the commit that wrote the table**, and `hardware/README.md:43`'s "the
two board-crossing tables" contradicting line 22 of the same file.

**And three assertions that a defect is still live, where it has been fixed:**
`pcb-pipeline.md:176` says the CV jacks are unplaced (placed seven minutes
later, same session); `ks33-geometry.md:139` says `cluster-boards.md` "still
carries the reversed conclusion" (fixed in the next commit). The corpus now
reports defects that do not exist, which costs a reader exactly as much as one
that does.

**Even this wave's own README is wrong**: it says "85 corpus files changed"
where the corpus figure is **79** — 85 counts everything outside
`docs/review/`, and the line counts beside it are the all-files numbers.

### On my four self-recorded errors, taken as classes rather than items

- **Pattern-fires-on-a-true-sentence** — genuinely closed. No new instances;
  every decoy set correctly excluded.
- **`git add -A`** — clean at HEAD.
- **Citation to something that does not exist** — **not closed.** It
  generalises past figure ids to sections, anchors and line numbers: three
  dangling `*Still open*` references to a section that `git log -S` shows
  never existed on that page, and a probable broken anchor replicated 23×
  (`#the-interfaces-table` against a heading that slugs to
  `#the--interfaces-table`, which `check_links` never resolves because it
  splits the fragment off first).
- **YAML** — **one new silent instance**, above.

### D20's mechanical reading, which is the useful part

**A count restated in prose is a forbidden pattern nobody wrote.** Seven of
the nineteen would fall to a check that re-derives a stated count from the
tree — something `check-staleness.py` already does for the corpus file count,
and which `repo-maintenance.md` §7 already writes out in four lines for the
path map and then does not run.

## D1 — the checker, attacked again. Two findings make every run of it suspect.

| Claim | Check | Verdict |
|---|---|---|
| **`check_owners` stopped checking values.** `toks = sorted(set(idents))[:2] or sorted(set(nums))[:1]` — the `or` is **exclusive**, so for any figure whose value contains a hyphenated identifier the numbers are never looked at | Read line 864; enumerated what token each settled figure is actually tested on | **Confirmed. `spi-series-r` is tested on `['R-SPI-SER']` and its value `100` is NEVER CHECKED.** The docstring two lines above says "take EVERY distinctive token, numeric and symbolic" — and the same docstring condemns precisely what the code now does: "asking whether the owner page mentions a part … proves nothing" |
| **`check_owners` is nondeterministic.** `sorted(set(...), key=len)` breaks ties on set iteration order, i.e. `PYTHONHASHSEED` | Ran `loop-budget`'s token selection across eight seeds | **Confirmed: `196 241 196 241 250 241 250 196`.** D1 took it end to end with a real rule-1 violation live and got **6 PASS / 4 FAIL over ten identical runs** |

**F2 is the worst thing this wave found, and it is not a missed defect — it is
a defect in the instrument.** A check whose verdict flaps on the same tree
means no run of it means anything precise, and the failure mode is new for
this repo: not always-green, but green *often enough that a re-run clears a
surprising FAIL.* Every PASS I have quoted in the last two days was a sample
from a distribution I did not know existed.

F1 is mine and it is a **regression**: the pre-`0e68f25` version would have
caught the case I built the new one to catch. I widened the token set to
include identifiers and wrote `or` where I meant "and also".

Eleven more findings, the ones I would act on first:

- **Any inline link with a `#fragment` is completely unchecked.** `[^)#\s]+`
  refuses to cross the `#`, so the regex fails outright and the `split("#")`
  in the body is unreachable. **23 of 166 inline links (14 %)** — twelve of
  them the `](../../README.md#the-interfaces-table)` I added to every circuit
  page, which is also the broken anchor D20 found.
- **`check_sections` is defeated by the corpus's own hard wrap.** Its gap
  pattern forbids a newline, and `check_figures` was rebuilt *in this same
  commit* to search a line-joined stream for exactly that reason.
  `check_sections` was not. **8 of 68 real cross-file references invisible.**
- **`followlinks=True` plus a symlink loop hangs indefinitely** — 60 s, zero
  output, against a 60 s hook budget, so the commit is simply not gated. And
  the symlink fix went into one of the *two* `os.walk`s: `load_circuits()`
  never got it, so a symlinked circuit joins the corpus while the circuit
  count stays 23.
- **The wiring assertion records the call, not the consequence.** Five tokens
  of edit give `UNWIRED CHECKS = 0`, PASS, exit 0, with a broken link and a
  registered stale value live — and the coverage line is byte-identical to a
  healthy run, because it counts **inputs**, never findings.
- **The tool tells you to read a report it did not write.** `.staleness/report.txt`
  is written at the end of `main()`, after the early return and after any
  traceback, so on those paths it holds the *previous* run's content — while
  the hook says "read it when fixing, do not re-run for detail."

D1's honest counterpoint, recorded because it matters: the 300-char widening
causes only 4 exemptions today and all 4 are legitimate. **The commit's thesis
— vocabulary, not distance — was right. It just swapped `was` for a date.**

## D6 — the repointed owners. Two of nine landed on a page that never states the figure.

| Claim | Check | Verdict |
|---|---|---|
| `key-pullup-qty`'s new owner never states 24 | `grep -c 24` on the page | **Confirmed. Zero occurrences.** It says "21 of these" and its Interfaces row *cites* the figure. The page that derives it is `key-marker-and-bits.md:107` — "**qty 24**. Found in review." — which is the register's derivation verbatim. It passed only because `"24"` is reported UNCHECKED |
| `inamp-full-scale` has **two** owners | Grepped both | **Confirmed.** `breath-receive-stage.md:45` says "Owned here."; the register names `breath-sense-link.md`. "Owned here" was written at 19:46 and the owner moved away at 20:15, never reconciled. Both files contain an unglued `9.94`, so the check is blind either way |
| `chain-conductors`' owner states a breakdown that sums to **13** | Read `0001:135` | **Confirmed. "12 per hop — 6 signals-and-supply, 5 grounds, 2 spare."** Its own pin list gives 5+5+2. No grep reaches an arithmetic error |

`ref5050-grade`'s repoint was verified by nothing — it is `disputed`, so
`check_owners` skips it, and the new owner mentions only a part number while
the dispute is derived in ADR 0003.

**The ferrite numbers I added are right** — D6 extracted the curve geometry
and got 610–620 / 426–439 / 155–161 / 71–75 / 50–54 Ω against my
614/431/157/72/51. But the addition is **assertion, not derivation**: no bias
currents, no interpolation, and the real derivation is still in the `FB-IN`
BOM row. Same for the toggle paragraph — numbers correct against the NKK PDF,
but inserted **inside a block that declares itself "moved verbatim"**, with a
reason that is a non-sequitur, and it contains the word "superseded", which
pre-exempts the whole paragraph inside the checker's own refutation window.

## D9 — the eighteen moved rows. Eleven clean, seven with findings, and the worst is the one I did last.

| Claim | Verdict |
|---|---|
| **The `D-CLAMP-BREATH` drawing edit labelled the wrong part.** Line 110 is at the BREATH output **jack**, where every other jack on the module labels that identical structure `D-JACK-CLAMP`. `D-CLAMP-BREATH` is qty 2 and describes itself as "at the in-amp inputs" — both accounted for by line 67 | **Accepted as high-confidence.** So the breath jack now has no `D-JACK-CLAMP` drawn, the part appears three times for a qty of two, **and the wrong claim ("drawn … TWICE") is now recorded in `hardware/bom.csv`'s own note** |
| `J-UMBILICAL` → `power-entry/` derives nothing about it; the page never names the part and draws no etherCON. qty 2 spans two boards | Accepted; my stated reason was wrong |
| `C-BULK-RAIL`'s new owner **refutes** it — the row says 100 µF and "NOT 47uF on every rail"; the page draws C1–C4 all at 47 µF | Accepted. Not caused by the move, but the move made the refuting page the owning page |
| Two of the 32 remaining rows are drawn **and** derived — `R-BREATH-SUM` and `R-BREATH-OFF`, both in `breath-output-stage.md`'s Values table. They sit in the same `pcb-pipeline.md` sentence as `J-CV` and `D-CLAMP-BREATH`, which I fixed | Accepted, and the spelling trap is the lesson: the row says `40.2k`, the page says `40.2 kΩ` |

**D9 proved the BOM's mechanical consistency independently** rather than
trusting `merge-bom.py --check`: multiset union exact, no orphans either way,
rebuild byte-identical at 131,725 bytes, all 27 files 11-column CRLF. That
part holds.

## D8 — the two new figures. Both values right; the completeness is not.

| Claim | Verdict |
|---|---|
| **Both values verified against the banked documents** — MPXV4006DP p.5 gives the transfer function character for character; the Gateron drawing sheet 6 item 5 gives the bounce line, confirmed by extraction *and* a 150 dpi render | **Accepted.** The two figures themselves are sound |
| **`ROADMAP.md:71`, the M1 row, still says bounce is "neither is published"** — and all five of the new entry's patterns match **zero** places in the corpus | **Accepted, and it is the grep-first failure one commit after a commit titled "fixed by grepping first."** The patterns were written from the three documents I edited and missed the fourth spelling |
| `key-release-time` is restated as a stale **125 µs** in two live places, one of them written **inside this fix batch** (`latency-budget.md:133`) and the other on that figure's own owner page | **Accepted.** And D8's warning is the useful part: `"125 µs"` must **not** become a pattern — it is also the true mean sampling latency in two places |
| All three `breath-sensor-slope` patterns **never existed in the corpus** — invented rather than grepped, guarding nothing while counting toward "218 patterns" | **Accepted.** I wrote that entry's patterns from the document in front of me, which is the exact practice `CLAUDE.md` §2 exists to forbid |

D8's structural finding is the one to keep: **`NUM_UNIT` has no `kPa`, `gf` or
`in/sec`, so `check_restated` could never have nominated either of the two
figures this slice reviews.** And its `known` set is polluted by single digits
from `umbilical-pinmap`'s pin list, which silently suppresses **`4 kHz` (15
files)**, **`5 ms` (10 files)** and **`250 µs` (9 files)** from the advisory
entirely.

## D4 — the other five tools. Two findings undercut things I cited as proof.

| Claim | Check | Verdict |
|---|---|---|
| **`rewrite-paths.py --invert` is no longer a valid proof.** 112 MISMATCH on a healthy tree, because 92 of them are files the map explicitly marks `created` and `invert_targets()` never reads the `kind` column | Ran it against the recorded baseline | **Confirmed: `55 byte-identical, 2 skipped, 112 MISMATCH`**, with messages of the form "not present at baseline 81c081d" |
| **`merge-bom.py` writes the truncated master to disk before reporting problems** — the exact bug `e30d3d8` fixed in `merge-manifests.py`, whose own comment says "by which time the damage was on the filesystem", left unfixed on "the most-cited file in this repository" | Read `main()` | **Confirmed.** In the non-`--check` branch the write happens, *then* `for p in problems: print(...)`. A fragment with a corrupt header yields a short master on disk before anyone sees the error |
| **`--check` is byte-exact and cannot see the assignment rule.** Moving `D-CLAMP-BREATH` between two ORDER-adjacent fragments leaves the concatenation byte-identical → `0 problems`, rc=0, hook green | Accepted; the mechanism is obvious from the code | The rule `CLAUDE.md` states — a row lives with the circuit whose page derives it — has no mechanical check at all |

**The `--invert` one matters beyond the tool.** I cited it in the pre-merge
`STATUS.md` as "the strong check … what makes *Phase A changed no content*
decidable", and a cold tooling slice reported it as the one thing it could not
fool. **It is broken now, and I broke it** — by growing the path map with
`created` rows whose `old` column is empty. Worse, D4 shows the proof is not
even reproducible against itself: the same tree gives 0 MISMATCH with the
old map and 21 with today's.

So the strongest evidence in the merge recommendation no longer stands as
written. Phase A's conservation is still supported — by the per-file blob
hashes checked by hand at the time, and by the cold conservation re-run at
HEAD — but not by this.

**D4's candidate seventh fail-open is in my wiring, not in the tool:**
`check_datasheets()` truncates with `msgs[:40]`, and `verify-datasheets.py`
prints its "not a failure" coverage advisory *before* the real `bad` list. At
37+ uncovered parts a genuine SHA mismatch falls off the end entirely —
reproduced with a flipped byte in a banked PDF. Today `uncovered` is 0, so it
is latent. And the wiring discards the whole advisory on success, so the one
output whose stated justification is "nothing else will ever mention them"
now reaches nobody.

Two more worth acting on:

- **`check-conservation.py`'s head check is switched back off by this repo's
  own `notes.md` convention.** Delete a page's H1 and add a line of the form
  "Moved verbatim from …" quoting it — which `mod-channels/notes.md` literally
  carries — and rc=0 with a seam count identical to a clean split.
- **The `Counter` check exits 1 on a formatting-only edit.** A markdown
  table-alignment change reports `REPEATED PASSAGES THINNED (3): 4x -> 1x:
  --- --- --- ---`. 24 corpus files carry repeated 8-grams of pure table and
  drawing furniture, and the cheapest fix is to undo a correct change.

**What D4 proved sound, by construction rather than by sampling:** the
head/tail comparison *is* symmetric — it derived the condition under which a
k-word deletion at position p hides from the shingle walk, and a 30-case
sweep caught 30/30. Both real Phase B splits in history still pass clean.
`--apply` is safe with the map's 123 empty-`old` rows. CRLF handling is exact,
`ORDER` is complete and correctly ordered, and master hand-edits are caught.

## D11 — the datasheets. The order code is right; the reason I gave for not renaming the file is false.

| Claim | Check | Verdict |
|---|---|---|
| **`DAC8568ICPW` is correct** and the whole C-grade argument holds for it — 5 V full scale, clear-to-zero, the 2/5 ppm tempco, `VREFIN ≤ AVDD/2`, all verified page by page against SBAS430E. `DAC8568CIPW` occurs **0 times** in the document, `DAC8568ICPW` 12 times | Accepted; it matches my own earlier extraction | **Sound.** The fix itself is right |
| **The recorded reason for not renaming the banked file is false.** It is stated as "renaming would mean editing another wave's fragment, which CLAUDE.md §4 forbids" | Read `merge-manifests.py`'s own header and `.moves.csv` | **Confirmed, and it is worse than a wrong reason.** `merge-manifests.py:12-13` says `.moves.csv` is "an established, documented, **sanctioned** transformation that **does not count as editing a fragment**" — and `.moves.csv:2` **already rewrites this exact file's path**. The mechanism was sanctioned, documented, and in use on that very file |
| The false reason is in three places including the BOM | Grepped all three | **Confirmed.** `hardware/bom.csv` says "editing another wave's **manifest** fragment" — different wording, which is why my first grep missed it and D11's did not |
| **`MANIFEST.csv:2` still asserts `DAC8568CIPW` as a live `OK` part, sorted above its own correction** | Read the first three lines | **Confirmed.** Two `OK` rows for one document disagreeing about the part name. And R9's `SUPERSEDES` keyword is invisible **by construction**: the declared-supersession rule skips any row that names a file, so an `OK` row can never be reported as superseded |

**Teaching a false constraint is worse than leaving a stale value**, because a
stale value is one defect and a false rule generates them. I wrote that
`CLAUDE.md` §4 forbade a thing the tooling explicitly sanctions, put it in the
generated BOM and in the manifest, and a future maintainer reading either will
believe the bank cannot be re-filed.

Ten more findings. The ones I would act on:

- **`D-TVS-BREATH`'s three unsourced numbers are still unmarked** in
  `hardware/bom.csv`. The caveat exists only in the `notes` column of a 127 kB
  generated CSV — while `U-TVS-SPI`, **two rows away in the same file**,
  carries its unsourced-number caveat inline correctly. Same commit, same
  file, opposite treatment.
- **The BLOCKED row misattributes its own case.** Of the "three numeric claims
  about this part", the 5 V `V_RWM` is a property of the *rejected* part and
  the 140 mV is `[calc] 5.00 − 4.86` off a tracked figure. The Nexperia
  datasheet can settle neither. What it *would* settle — the leakage, the
  package, and whether the part is 12 V-standoff at all — is what `blocked_on`
  should name.
- **"78 verified" counts rows, not documents** — 76 distinct files, and the DAC
  PDF is now hashed and counted twice. R9 raised the headline by one while
  banking nothing.
- **The coverage claim tests 26 of 139 BOM rows.** `ESP32-S3-Matrix` — one of
  the three parts the tool's own comment says were hiding in that blind spot —
  is still skipped by the ≥6-character token filter, along with `SS34`,
  `R-78E5.0-1.0` and `KS-33`. Zero uncovered is true today, not by
  construction.
- **Wiring `verify-datasheets.py` in captured the exit code and discarded the
  report.** `check_datasheets()` returns `[]` on exit 0, and that tool exits 0
  on a clean-but-incomplete tree by design, so its whole advisory half never
  reaches the hook. The enforcement gain is real; the reporting gain is zero.
- **`check_verified_against()` has zero inputs.** The union of keys across all
  23 `circuit.yaml` is `[depends_on, id, last_reviewed, title]`. This batch
  rewrote all 23 and added none. **The SHA-256 bank has no machine link to any
  figure**, and `figures.yaml` has no provenance field on any of its 37.

**And the provenance spot-check is the good news**: 11 figures checked against
their cited documents, **10 fully confirmed** — including `loadswitch-timer`
with 51 `LT1641` hits and **0** `LT4256`, which clears the mislabelled-mirror
trap `repo-maintenance.md` warns about. `dac-rail`'s 5.00 V floor is right but
one clause of its provenance overstates: only two rows carry the C/D 5 V
condition, not the whole EC table.

Also: **141 corpus citations of a `datasheets/` path, 0 dangling**, and 76
manifest rows against 76 files on disk both ways. That half is genuinely
honest — D11 had to instrument the tool's own walk to get the denominator it
hides on success.

## D5 — the regression audit. My "narrowing" of the refutation vocabulary was a net WIDENING.

D5 built the control this needed: three trees — `old` (`0e68f25~1`), `new`
(HEAD), and **`mixed`** (HEAD corpus with the old tools). Every regression
reproduces on `mixed`, so it is attributable to the tool change and not to the
85-file corpus diff.

| Claim | Check | Verdict |
|---|---|---|
| **A bare ISO date exempts a live stale value.** The new vocabulary added `\d{4}-\d{2}-\d{2}`, a bare `->`, a bare `→` and a case-sensitive `NOT` — all of which are ordinary prose | Injected `"The panel is 8HP this"` (a live forbidden pattern) into ADR 0004, preceded on a different line by ordinary prose, and toggled one thing | **Confirmed, decisively.** With `"Bench session 2026-08-14 covered the jack layout"` → **PASS**. Delete just the date, everything else byte-identical → **FAIL**. Same for a bare `->` and a bare capital `NOT` |
| **The exempt region grew from 33.9 % to 48.4 % of corpus characters** | Accepted; consistent with D3's independent 47.9 % | **Nearly half the corpus is now ground where no pattern can fire** |

**I removed ten weak words and added four that are more common than the ones I
removed.** The commit message says "Dropped the past-tense words, kept the
ones that mean a correction was made" — and a date means nothing of the kind.
D3, D5 and D7 reached this from three directions without seeing each other.

**Six regressions total**, four in `check_figures` and two in `check_links`.
The link ones: `](page.md#anchor)` never matches because the character class
excludes `#`, so **23 links dropped out of coverage** — all 23 circuit pages'
`](../../README.md#the-interfaces-table)`, the anchor I added, which is
exactly what a restructure moves. And `](path 'Title')` is unmatched too.

**Runtime, measured, which I had not done:** 8.64 s → 11.12 s against the
hook's 60 s. Of the +2.48 s, **+1.96 s is corpus and register growth** and only
+0.5 s is the rebuild; all three subprocesses together are **0.31 s of 11.1 s**.
`check_figures` is 10.51 s, re-reading every file once per pattern, exactly
linear at **0.049 s/pattern** — so the timeout arrives at **~1,220 patterns**.
The register went 184 → 218 in one commit and rule 2 mandates adding more.
Inverting the loops is a ~40× I/O reduction.

**23 defect classes still caught in both trees, and 9 newly caught** — the
rebuild is not a net loss, and D5 says so explicitly. Latin-1 under
`hardware/**` used to **traceback** and now reports; reference-style links, a
SHA belonging to another part, a tampered PDF, a deleted PDF, a commented-out
check and a typo'd `depends_on` prefix are all new wins.

## D7 — the register side of the same root cause

| Claim | Verdict |
|---|---|
| **The commit named "the eight forbidden-list escapes, fixed by grepping first" does not close those escapes in the checker.** Of its 31 added patterns: 14 produce a live hit, **13 match the stale text but every match is exempted**, 4 match nothing at any commit | **Accepted, and the test is the right one** — D7 put the HEAD register in front of the pre-fix tree and ran the HEAD checker: **19 live hits from only 14 patterns** |
| Three of the silent ones are the very escapes the register was edited to close — `U-DIFFRX` (whose `escape_note` says "THE MISS WAS ONE SPACE", and whose space-less spellings are now exempted by `until 2026-09-21` 180 chars away, about a *different* prior value), `C-KEY`, and `D-TVS-BREATH` | **Accepted.** The patterns are right; the exemption swallows them |
| **The ±300-char window crosses CSV record boundaries** — an identical injected row goes from 1 stale to 0 once an unrelated neighbouring row containing "deleted" is added | **Accepted, and it explains a thing I had noted and not understood**: why `13mm spare` and `= 97mm` were exempt in `hardware/bom.csv` and live in its own fragment |
| **Three patterns can never fire anywhere** because they contain a marker themselves — `"0.2 → 4.8 V"`, `"75 mV → LM317"`, `"VALUES NOT SET"`. Injected verbatim with nothing correcting them: PASS, exit 0 | **Accepted; third slice to find this independently** |
| `"0.5059 V/kPa"` forbids an **arithmetically correct** number — the true slope at 3V3 — and the same entry's note gives the reason someone will write that sentence | **Accepted.** A trap one sentence early, in a pattern I wrote |
| 9 added patterns match nothing at any commit; 8 never existed in corpus history — including **all three** of `breath-sensor-slope`'s | **Accepted.** Invented rather than grepped |

D7's coverage measurement is the one to carry forward: **`dac-rail` is past
the nine-spelling benchmark already — 36 restatements across 17 files, in both
`5.21 V` and `5.21V`, two of them inside ASCII drawing gutters.** Then
`cref-out-node` 35/15, `panel-toggle-hole` 30/7, `loadswitch-gate-cap` 30/11.

And the structural observation: **pattern count is inversely correlated with
restatement count.** The best-patterned figures (`key-press-time`,
`key-release-time`, twelve patterns each) are restated three times.
`ferrite-bias-impedance` has one 78-character pattern for a value restated 17
times across 8 files.

## D10 — the BOM. Mechanics clean; the rule I applied to one row I did not apply to the rest.

| Claim | Check | Verdict |
|---|---|---|
| **The mechanics pass**, verified with D10's own concatenator and byte comparator rather than `merge-bom.py --check`: 131,725 bytes, 139 rows, 140 CRLF / 0 bare LF, 11 columns everywhere, exact header in all 25 fragments, no duplicate refdes, nothing on disk outside `ORDER` | Accepted; matches D9's independent rebuild to the byte | **Sound** |
| `U-DAC`'s order code change is **correct and complete** — no corpus file spells the old code as an order code any more | Accepted | **Sound** |
| Every multi-quantity row re-derived correctly; the `C-KEY`/`R-KEY-SER` rewrite left no number behind | Accepted | **Sound** |
| **"The batch answered *placed* and not *named*."** Of the rows moved out of `unplaced.csv`, almost none is named by any hardware page | Counted, per refdes, across every `hardware/**/*.md` | **Confirmed, and worse than stated: 14 of 18 are named by ZERO pages.** Only `R-SER-BREATH` (3), `U-LVL-MOD` (2) and `D-CLAMP-BREATH` (1) — and the last only because I edited that drawing, which D9 shows I did wrongly |

**This is the wave's pattern in one finding.** `unplaced.csv` is "the rows no
schematic page names". I emptied 16 of them on the grounds that the parts were
*drawn*, and left 14 with no page naming them — so the join between the
picture and the BOM row still does not exist. `pcb-pipeline.md:167` states the
three tests, **drawn, named and placed**, and I applied all three to exactly
one row.

| Claim | Verdict |
|---|---|
| **`pcb-pipeline.md:150-176` is stale on six numbers, and went stale inside the commit that placed the parts** — which edited that same file twenty lines above, in the collision table, without touching the block | **Accepted. Four documents state this BOM's size and all four are wrong, three different ways** — `pcb-pipeline.md`, `hardware/README.md:72`, `repo-maintenance.md:204`, and the batch's own commit messages. All three files were edited in this batch |
| **`C-BULK-RAIL`'s new owner contradicts it twice** — the row says 100 µF on +12 V, the page draws C1/C2 at 47 µF and states "Entry bulk is 4 × 47 µF". Its 22 mA justification also counts the **deleted** LM311 | Accepted; D9 found the same from the other side |
| Three hard ordering blockers — `U-LOADSW` (no FET part number, sense resistor double-counted), `D-RESP` (a DO-35 axial part in a SOD-123 package), `D-USBOR` ("1N5817 **or SS14**" in DO-41, where SS14 is SMA) | **Accepted, and the third one stings**: that is the exact fact the same batch used to fix `D-REVSHUNT`, three rows below it in the same file |
| One order code correctable from a banked document today: `SP0504BAHT` is listed only as `SP0504BAHT**G**` | Accepted |
| **17 of 34 `open` rows name nothing that decides them.** `R-LED-PD` — added in this batch — does, and is the best-formed row in it; four of the five rows added beside it name no decider | Accepted |
| `merge-bom.py:20` gives `R-BIAS-INAMP` as its **worked example** of why "where it is mentioned" fails — and that row is filed in `pitch-stage/bom.csv` | **Accepted.** Two fragment assignments are wrong by the tool's own documentation, by name |

### D10's handling of a sibling claim is the model, and it reversed it

A sibling slice reported **`360 mA` in 6 files against a register that says
`359 mA`**. D10 confirmed the occurrences and **refuted the staleness**: the
register's value has been `"359 mA"` in **all 20 recorded versions** of
`figures.yaml`, so it never moved — this is a rounding, not a stale value. It
is also used in correct arithmetic (940−360=580 mA, 47.5 ms total; at 359 mA
the answer is 47.4 ms and the conclusion is unchanged).

**A `forbidden` pattern there would be exactly the `CLAUDE.md` §2 trap** — its
cheapest fix would make a correct sentence wrong. The right action is a
rounding note on `umbilical-current`. D10 also found a **third** spelling
(`~350 mA`, three files) that the original claim missed, and noted the CSV
forms are `360mA`/`350mA` with no space.

It also recorded a near-miss rather than filing it: `U-BREATH` qty 2 against
one drawn sensor looks wrong until you find the rationale on the **neighbouring
row** — "ADR 0003 calls the sensor a wear part and buys two". Correct, not a
defect, written down so the next reviewer does not file it.

## D15 — the latency budget. Correct where it is arithmetic, wrong where it is argument.

| Claim | Check | Verdict |
|---|---|---|
| **`latency-budget.md:133` carries a stale `125 µs` against a tracked 119.9 µs, and the sentence was added in THIS batch** | `git log -S` on both | **Confirmed. Added by `c65083d`** — "docs/reference/ catches up with the restructure", my own commit — while `119.9 us` has been tracked since `cfcdc6e`, Wave R7, long before. **I wrote a stale value into the file I was fixing**, in the paragraph carrying the bounce consequence |
| The same stale value sits on `key-switch-network.md:112`, **that figure's own owner page**, and survived a batch that rewrote its consumer | Accepted | And it mislabels the RC as "the release filter", which the same page says is firmware's job |
| The caution was right and is the useful part: six `125 µs` occurrences, **four legitimate**. Two safe RC-specific patterns each hit exactly one stale line and nothing else | Accepted | This is how a pattern should be proposed |
| **The `~1 ms` transducer response is called "a datasheet figure" and the banked datasheet has no such row** | Extracted all 22 pages myself | **Confirmed. 19,412 characters, and `response`, `rise time`, `10% to 90` each occur ZERO times.** The second-largest breath term, unsourced, on a document that is already banked and already readable — a `CLAUDE.md` §3 case |

**And the finding the slice was not handed, which is the important one:**

> **The key path that does not close was left unbooked.** The table says
> release debounce is "off the attack path by construction"; `ROADMAP.md:127`
> refutes exactly that — "lifting a finger is how you start the next note".
> A release-initiated note change is W + 0.418 ms, and at the **published
> 5 ms** bounce maximum that is **5.67 ms against a 5 ms target. It fails.**

And the page's own summary reads *"The key path is not the one at risk."* This
is the same defect shape I repaired — largest term omitted, no total — left
sitting on the sibling path.

Three more that matter:

- **ADR 0003 still carries a complete stale copy of this budget**, untouched
  by the batch, with **three mutually inconsistent breath totals in one file**
  (`<1.5 ms`, `~2.6 ms`, `~3.1 ms`). Its `50–200 µs` **is** a `loop-budget`
  forbidden pattern and cannot match, because the value sits in a **table cell
  with pipes** while the pattern was written in prose spelling — §2's trap in
  markdown-table form. The same list proves the author knew: a neighbouring
  pattern carries the pipe.
- **The release filter is 41.7× too small** for the job the page assigns it,
  and D15 supplies the three-line proof the page is missing: to span 5 ms the
  RC needs C ≈ 1.96 µF, which pushes the **press** to 246 µs — the whole scan
  period — destroying the asymmetry the design depends on. The page's
  conclusion is right; it never showed why.
- **`loop-budget`'s 196–241 µs is not reproducible from its own derivation.**
  The 291 µs default pins about six transactions (148 + 6×24 = 292), and six
  polling transactions give 202–209.

**`ks33-contact-bounce` completeness: 1 of 6 followed.** ADR 0002 cites it
correctly. Not followed: `latency-budget.md` (restates it twice),
`firmware/README.md` (carries neither half of the relationship the register's
own `companion` field claims it carries), ADR 0001 (never mentions it, still
argues from 20 ms), `key-switch-network/` (calls the 47 nF "a bounce filter"
unqualified), `ROADMAP.md:71` (flatly contradicts it).

**D15's cross-cutting note is the sharpest diagnosis in the wave.** Of every
quantity this page books, exactly **one** is tracked with this page as owner.
**Every divergence in its report is in an untracked quantity** — the DAC
burst, the tube delay, the filter corners, the transducer response, the
umbilical rate, the 5 ms target itself, and all four path totals.

> The fix was correct arithmetic in one file, and the register was not extended
> to hold any of it in place.
