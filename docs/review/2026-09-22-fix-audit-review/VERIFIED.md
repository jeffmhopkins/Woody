# Verified by hand — round 2

## E4 — the method

| Claim | Check | Verdict |
|---|---|---|
| **There is no finding ledger.** ~198 numbered findings across the twenty reports; **zero** referenced by id in `VERIFIED.md` or `STATUS.md` | Grepped for finding ids in both files and across the reports | **Confirmed exactly. 198 distinct ids in the reports, 0 in `VERIFIED.md`, 0 in `STATUS.md`** |
| `STATUS.md`'s "every one of them hand-verified" is true of **reports** and false of **findings** — about a quarter were checked | Follows from the above | **Confirmed.** I verified twenty reports and roughly fifty findings, and wrote a sentence that reads as if I verified all of them |
| **This is the mechanical reason ten rounds have been judged "partial"** — the next round had no list to be complete against | Reasoning, checked against the evidence | **Accepted, and it reframes the whole session.** Not a diligence failure. There was no denominator |
| `CLAUDE.md` says "Nine have run"; there are **11** directories | Counted | **Confirmed.** I corrected that sentence from "three" to "nine" yesterday and it was wrong within a day — **third recorded instance, in the paragraph that exists to describe the failure** |
| The review apparatus is **8.4×** the artefact | Counted lines both sides | **Confirmed: 138,726 review lines against a 16,450-line corpus** |
| **The orchestrator broke round 2's freeze while round 2 was running** — declared the corpus frozen, then committed the tooling fix, so two slices running one command twenty minutes apart get opposite verdicts and every `[test]` baseline in twenty reports stops reproducing | Checked the commit times against the round's opening | **Confirmed, and it is mine.** `tools/` is not in the §6 corpus, so it held on the letter and broke on the substance |

**What E4 establishes that no other slice could**, because it is the only one
whose subject was the wave itself:

- **The cold rule held, decisively.** It shingled all twenty reports at n=8
  and intersected all 190 pairs: every high-overlap pair is co-quotation of a
  *corpus* source, never of each other. The better evidence is the
  **disagreements** — D1 and D2 found the same defect with different
  denominators (1 of 32 vs 1 of 37), D3 and D5 measured the exemption surface
  at 47.9 % and 48.4 %. Independent agents agreeing to three significant
  figures would have been the suspicious result.
- **The deliberate cross-seeding was worth it.** ~12 claims passed through
  briefs: 6 confirmed, 3 confirmed-and-widened, **1 refuted** (D10 on
  `360 mA`, which prevented a pattern that would have made a correct page
  wrong), and **1 where my brief itself was wrong**.
- **Node-indexing is the best of the five properties.** `WIRE-LOOM` was
  reached by four slices from four directions; `C-GATE-LOADSW` by five; the
  duplicate YAML key by two. It dies at the report boundary, which is what
  the ledger fixes.
- **Converging or spinning: both, on different layers.** The *design* is
  converging — D20's 0 of 19 defects at the site of an edit, against early
  waves' "47 to 0" backlogs. The *apparatus* is not, because it keeps
  growing. Its proposed gate metric is the right one: **not defect count, but
  whether any finding would change a soldering iron's path.**

E4 also declared an exposure rather than hiding it: it read a line of D19 that
quoted a path inside an earlier wave's directory, and did not open that file.
**An undeclared exposure is worse than a declared one**, and the point that
line carries stands — the corpus's only statement that ownership lives in
exactly one place now survives only where reviewers are forbidden to look.

### Acted on already

`tools/extract-findings.py` and a generated `FINDINGS.csv` (202 findings, 17
slices, 0 addressed by id); the wave count removed from `CLAUDE.md` rather
than corrected; the freeze clause and the ledger added as named properties;
the previous-round audit demoted from a property to a standing assumption
with its four recorded shapes named.

---

## E1 — re-verification of the wave's top claims

**Verified by hand, 2026-09-22.** E1's 25 re-verifications were not re-run
one by one; what was checked here is the set that changes what anyone does
next, and the one refutation.

| E1 claim | checked how | result |
|---|---|---|
| Predicted cold, from the register alone, *which* 8 matches ride solely on the four withdrawn markers | ran the repaired checker | **Confirmed.** `chain-connectors` x2, `panel-toggle-hole` x2, `loadswitch-timer` x4, byte for byte |
| `WIRE-LOOM`: `five connectors must match` exempted by a date **-222 characters** away | re-read the cell | **Confirmed**, and agrees with D3 E16/E38 to the character |
| `STATUS.md` §2's "D3 and D5 measured that independently" is **false** | read both reports | **Confirmed.** D5 states the pair; D3 measured only the new side (47.9 %) and never produced 33.9 % |
| The comment committed into `check-staleness.py` escalated that to "three cold slices" | read the committed comment | **Confirmed, and it was mine.** Fixed in `e62114a` |
| The 33.9 -> 48.4 pair conflates a vocabulary change with a window change; the **window** did the widening | read E1's 2x2 | **Accepted, not re-derived.** Recorded in the checker's comment so the next person is not misled by the number barely moving |

**The refutation is the important one and it is against me, not against the
wave.** A number travelled further than its evidence — one measurement
became "three cold slices measured that independently" — inside the fix for
that exact failure mode, in a file no check can reach. `docs/review/` is
history and is not corrected, so `STATUS.md` keeps its sentence; the
correction lives here and in the tool.

E1's five corrections to the wave (D1's "6 figures flap" is 5; 33.6 not 33.9;
"18 figures name a refdes" is 17; "14 of 18 unplaced rows" is **15** of 18,
i.e. worse than claimed; the manifest is 78 rows over 76 files) are
**accepted as recorded, not independently re-derived**. Stated plainly
because "accepted" and "confirmed" were run together in the last wave's
`VERIFIED.md`, which is a defect E3 filed against it.

## E2 — what the wave missed

| E2 claim | checked how | result |
|---|---|---|
| Every one of the 17 files no slice named is a `circuit.yaml` | listed the batch | **Confirmed** |
| The 68-line header is byte-identical in all 23 | `md5sum` of the header block | **Confirmed**, one hash 23 times |
| E2-1: "five rows" is **seven** | enumerated every row naming `module/digital-and-supervision` at `0e68f25~1`, judged each | **Confirmed exactly.** 7, and `dac8568:16` is correctly excluded |
| E2-2: "27 of 49" is not reproducible from any committed state | loaded every `circuit.yaml` at `07c7ae8`, `4ecc17e`, `0e68f25~1` | **Confirmed.** 50/38/26 identically, three times; 96/48/0 at HEAD. 9 circuits with no edge, also confirmed |
| E2-7: `panel-toggle-hole` fires on a **true** sentence the cell later endorses | read the cell | **Confirmed.** Pattern withdrawn in `e62114a` |
| E2-7: `loadswitch-timer` is the same shape | read the cell **and** the register | **Partly refuted.** `2.4x the ~62ms` is a *false* premise, not a true one, and D3 is right that nothing in the cell retired the 62 ms. Fixed in the text, not by withdrawing the pattern |
| E2-8: the hook fires on every `Bash` call and never blocks | read `.claude/settings.json`; every call this session | **Confirmed.** `"matcher": "Bash"`, the `"if"` gates nothing, and there is no `permissionDecision`. `CLAUDE.md` §2 corrected |
| E2-9: `tools/` figures are unreachable and two are stale | read the docstrings | **Confirmed.** Numbers removed rather than corrected |
| E2-10: `halved` exits 1 on exactly the deduplication rule 1 prescribes | read the exit line | **Confirmed.** Now reported without failing the run |

E2's `circuit.yaml` **data** re-measurement (96/48/0/0, 23 unique ids)
reproduces D17 and is confirmed here too.

**Not done, and named:** the header is still 68 lines replicated 23 times.
That is the structural form of the same defect and the rule-1 fix is to state
it once and cite it. It is a restructure, not a correction, and it is not
going in beside a merge.

## E3 — wrong, inflated and misallocated findings

**E3's lead finding is the one acted on**, and it is the strongest single
result of round 2: severity was **misallocated**, not inflated. The
pre-merge blocker table held a documentation sentence, a conditional watt, an
adverb and seventeen spaces of ASCII, while the three findings that stop a
human ordering this BOM were in D10 and appeared nowhere in the verdict.

| E3 claim | checked how | result |
|---|---|---|
| `U-LOADSW` is three parts in one row, `+ sense R` double-counts `R-ILIM` | read both rows | **Confirmed.** Fixed in `ad2c173`; `R-ILIM` is its own row with its own qty |
| `D-RESP`'s part and package cannot both be ordered | `1N4148.pdf` p.1 | **Confirmed verbatim**: "hermetically sealed leaded glass SOD27 (DO-35)". `1N4148W.pdf`: "Case: SOD-123" |
| `D-USBOR` offers two alternatives and one footprint | `SS14.pdf`, `1N5817.pdf` | **Confirmed.** "Case: SMA (DO-214AC)" x4 against "Case: DO-41" |
| Blocker 4 row 1 compares a nominal supply rail to a MIN threshold, so the sentence is *unsupported*, not *false* | read D12's own hedge | **Accepted.** `docs/review/` is history; not corrected there |
| `VERIFIED.md` (last wave) has 31 rows "Accepted" with no independent check | not recounted | **Accepted, and taken as method.** It is why this file says which rows were accepted rather than confirmed |
| One scratchpad extraction was perturbed by one character, which manufactured D1's test condition; on a clean tree it is 8/8 PASS | re-ran on a clean tree | **Confirmed 8/8.** D1's hang is real; the wave's generalisation from it was one step too far |

**E3's three blockers absent from `STATUS.md` are now fixed** (`ad2c173`).
Its severity re-allocation is accepted in full: a finding that changes no
one's actions is not a blocker, and one that stops an order is, wherever it
was filed.

## What round 2 changed about round 1's verdict

Round 1 said the merge was blocked on three instrument defects, all fixed.
Round 2 says that was **the wrong list**: the instrument defects were real
and are fixed, but the blockers that survive contact with a human were the
BOM rows nobody promoted. Both rounds' blocker lists are now closed.

**What is not closed** is `FINDINGS.csv`: 202 findings, and this file closes
by id none of them. The ledger exists now; using it is the next round's job,
and saying so is the whole point of having built it.
