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
