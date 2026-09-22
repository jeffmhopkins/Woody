# What I checked by hand, and where a reviewer was wrong

Twelve slices, ~365 findings. This file records what the orchestrator
verified **personally**, with the command or the reading, and — as importantly
— what was **accepted as recorded rather than re-derived**. The last wave ran
those two together and E3 filed it as a defect: 31 of 104 rows read
"Accepted" with no check described, and `STATUS.md` promoted a finding into
its blocker table out of that block.

**Confirmed** means I reproduced it myself. **Accepted** means I did not.

## The fix-order head: ADR 0005

| claim | how checked | result |
|---|---|---|
| **G11-1** ADR 0005 specifies a ramp the part cannot deliver | read `0005:263` | **Confirmed verbatim**: "**1.0 A, latch-off, with a programmed 50–100 ms ramp.**" against `loadswitch-gate-cap`'s settled 49–197 ms envelope |
| **G11-49** the ADR still calls two other controllers equally valid | read `0005:339`; `grep -rn "LM5069\|LTC4210"` across the whole corpus | **Confirmed, and the grep sharpens it**: "LM5069MM (MSOP-10) and LTC4210 (MSOP-8) are equally valid" is the **only** occurrence of either part anywhere in the corpus. Neither has a `MANIFEST.csv` row |
| **G11-49** the two sit "three lines" apart | counted | **Corrected — 76 lines apart** (263 and 339). I repeated the three-line figure to the user before checking it. The *substance* is untouched: they are one edit, because fixing the ramp alone leaves the next reader free to reach for a part the ADR blesses, discarding the 82 nF, 10 µF, 35.7k/5.11k and 50 mΩ that are all LT1641-only constants |

## Live stale values, confirmed by reading

| claim | how checked | result |
|---|---|---|
| **G11-29 / G8-1** ADR 0004 asserts a retired 97 mm | read `0004:842`; grepped the corpus for both spellings | **Confirmed**, and G8's framing is right. The live text is "> The 97 mm above is built from `[from memory]` component envelopes". `97 mm`/`97mm` occurs **once** in the corpus outside the register. The `forbidden` list holds `"97 mm against ~110 mm"` and `"= 97mm"` — a **bare back-reference is a new escape shape, not a fifth spelling**, which is why four rounds of fixing the spacing never reached it |
| **G3-1** ADR 0004's table is headed 359 mA and computed at 290 | read `0004:280-287` | **Confirmed verbatim.** Header "\| Series R \| Drop at 359 mA \|"; cells 0.64 V and 2.90 V, which are 2.2 × 0.290 and 10 × 0.290 `[calc]`. At 359 mA they would be 0.79 and 3.59 |
| **G9-2** `POT-OFFSET` contradicts itself | read the cell | **Confirmed, and it is my own text from this morning.** One cell asserts centre = +0.07 V, that the wiper needs no buffering, that its true zero is +0.605 V ~20° past centre, and points at the row that buffers it |

## The two tools whose output I had been quoting

| claim | how checked | result |
|---|---|---|
| **G10-22/23** `audit-notes.py` cannot see its own example | ran it on `D-REVSHUNT`; then proved both mechanisms in isolation | **Confirmed twice.** The row contains "This row said DO-214AC, which is the SS14's package" — verbatim `CLAUDE.md` §2b's example of what must be cut — and every segment classified `PLAIN`. Mechanism 1: `classify()` returned `('PLAIN', [])` because the marker is lowercase and `segments()` guarantees a capitalised first word. Mechanism 2: the dated pattern requires a `\|` that `segments()` consumes, so it fires on nothing — 12 markers present, 0 classified |
| **G10-30** `extract-findings.py` closes findings by substring | built a synthetic wave | **Confirmed.** `X1-1` read `recorded` on the strength of a mention of `X1-11`; after the fix it reads `NOT ADDRESSED`, `X1-100` survives, `X1-11` still closes |
| **G10-31-ish** heading-introduced findings are never "introduced" | generated this wave's ledger | **Confirmed and worse than stated**: 168 of 377 rows — 45 % — were ghosts, every one a real finding under a real `###` heading |

## Where a reviewer was wrong, or I was

| | |
|---|---|
| **G4-6, extension blindness** | **Partly confirmed, and I overstated it first.** My initial test matched a relative prefix against absolute paths and concluded `firmware/` contributed *zero* files. It does not: `firmware/README.md` **is** scanned. G4's own statement was accurate — the directory holds exactly one `.md`, that file is checked, and the other extensions would be invisible *if they existed*. It is a latent trap (sharply so for `.MD`, a case-variant), not a live hole |
| **G8-5/6/7, 57 dead patterns** | **Accepted, not re-derived.** The claim is historical — never matched at *any* of 592 revisions — and I did not walk the history. My own current-corpus measurement (198 of 217 match nothing today) does **not** test it: a guard matching nothing *now* is the healthy state, because it means the retired value is gone |
| **G12-1 / G7-1, the bonded body** | **Core confirmed, my own count rejected.** `firmware/README.md:94` reads "The body is bonded." verbatim, and `ROADMAP.md:78` records the retirement explicitly. But my crude `grep -l` returned 21 files and is **not** evidence: `ROADMAP.md:75`'s "bonded to `PWR_GND`" is electrical bonding to ground, an unrelated sense. G7 and G12 both triaged live arguments from mentions by hand and landed on ~20–25; that triage is what the number rests on, not my grep |
| **G6's broken-link finding** | **Withdrawn by G6 itself**, correctly and in the open. It cited `README.md` linking to `g10-does-not-exist.md`, which never existed here — it was G10's probe, live in the uncommitted layer during the read. G6 rewrote the finding on a sweep of its own over a pinned clone, and left the retraction visible |
| **G10's own contamination** | **Disambiguated by G10, unprompted.** Any fail-open finding in this wave about `check_links` passing over a broken `README.md` link is its artefact. `G10-1`/`G10-2` are not, and reproduce in a clean clone |

## The freeze

Breached by me, and the breach is the wave's own finding (`G4-15/16`, `G10-42`,
`G5-0`, and reported independently by `G1`, `G6`, `G7`, `G9`, `G12`). My briefs
told two slices to inject defects and revert **in the tree ten cold reviewers
were reading**. The clause I wrote that morning bound the orchestrator and
said nothing about reviewers' working-tree writes.

What it cost, measured rather than guessed: **one finding**, withdrawn in the
open. The reason it cost only one is worth keeping —

> the disturbance reached exactly one finding, and only because that finding
> cited a **generated, untracked artefact** (`.staleness/report.txt`) rather
> than a tracked file.

Three slices independently re-verified live-versus-pinned with `cmp` and
`diff -rq` across the corpus **and** `tools/` and found no differences. The
commit-level freeze held throughout and stayed checkable:

    git diff a4b80b1 HEAD --stat -- . ':(exclude)docs/review/'   → EMPTY

Two mitigations the wave produced, both cheap: slices that mutate files get
their **own clone at a unique path** (G8's first clone was deleted under it —
the scratchpad is shared), and every slice records `git status --short`
beside each `[test]`.

## Method notes worth carrying, from the reviewers rather than from me

- **G8 wrote down the shape of its own blind spot** — its sweep filtered on
  comparison-shaped lines and passed over the bare back-reference another
  slice found. A reviewer recording what it *cannot* see is worth more to the
  next round than another finding.
- **G11 hit `CLAUDE.md` §2's hard-wrap trap while *verifying*** — three of its
  own quotes read ABSENT until it line-joined. That trap catches a reviewer
  checking a finding exactly as readily as an author writing a pattern, which
  §2 does not currently say.
- **G2 recorded a negative**: it built a value-presence sweep, ran it, hand-
  checked 71 flagged lines, found every one a false positive, and wrote that
  down so the next wave does not rebuild it.
- **G11 re-grounded two findings onto a comparison that runs no tool at all**
  when the instrument became untrustworthy. That is the right reflex and it
  should be the default for any finding about the checker.
