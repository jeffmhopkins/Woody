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
