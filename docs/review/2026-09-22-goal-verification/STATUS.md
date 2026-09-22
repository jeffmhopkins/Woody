# What landed

Twelve slices, ~365 findings. `VERIFIED.md` records what was checked and by
whom. This file records **what actually changed in the corpus**, by id, and
what did not.

The convention exists because a wave with twelve reports and four landed
slices looks finished from the outside and is not.

## The verdict on the goal

The session this wave audits was asked to make the repository *better
organised, with notes and cross-references updated and staleness removed*.

**Organisation: achieved.** Verified independently: the 23-circuit scheme is
exact, naming is consistent 23-for-23 across directory, page, `circuit.yaml`
`id:` and edges, every `circuit:` edge resolves and is mutual in both
directions, every Markdown link and anchor resolves, zero orphan files, the
BOM generates clean, and eleven package claims check out against banked PDFs.

**Staleness: not achieved — it moved.** Every slice independently reached the
same place: **the data files are clean and the defects are in the prose.**
G2 named the mechanism, and it is the finding the next round should start
from:

> Ten of fourteen defects are **correct information already written down
> elsewhere in the corpus**, contradicted by a live citation that was never
> edited. In every case **the correction was added beside the false statement
> rather than replacing it.**

G3 named the other half: **nine of thirteen live contradictions are
second-order numbers** — computed from a tracked figure and then written
down. `forbidden` lists protect the input; nothing protects the output.

## Closed, by id

| id(s) | what it was | where it landed |
|---|---|---|
| **G11-1, G11-49, G11-17** | ADR 0005 specified a ramp the part cannot deliver, three lines of the same passage still called two other controllers "equally valid", and the sizing was cited to the wrong page | `3fe7080` — one edit, because fixing the ramp alone invites the next reader to reach for a part the ADR blesses, discarding five LT1641-only constants |
| **G11-29, G8-1** | ADR 0004 asserted a retired 97 mm as a bare back-reference — a new escape *shape*, not a fifth spelling | `3fe7080` — now cites `panel-height-budget`. **No pattern added**: a guard for a value that now occurs zero times is the dead weight G8 measured |
| **G3-1** | ADR 0004's table headed "Drop at 359 mA" with both cells computed at 290 | `3fe7080` — column names the figure, cells recomputed |
| **G9-2** | `POT-OFFSET` asserted centre = +0.07 V, no buffering needed, true zero +0.605 V, and pointed at the row that buffers it | `3fe7080` — resolved in favour of +0.605 V, with the detent consequence stated |
| **G12-1, G12-2, G7-1** | "the body is bonded" live as an argument in **21 places** after ADR 0009 retired it | `f6a4ee8` — 13 files. Correct narration deliberately untouched |
| **G10-22, G10-23** | `audit-notes.py` could not see its own documented example | `8d57254` — case-insensitive, dated pattern re-anchored. `--regrown` 0 → 3 → **0**, and this time it means something |
| **G10-30** | `extract-findings.py` closed findings by prefix substring | `8d57254` — exact id matching; ids ≥ 100 no longer dropped |
| **(ledger, found here)** | heading-introduced findings were never "introduced" | `b47763f` — ghosts 168 → 12, and all 12 explained |
| **G4-11** | `REFUTATION_WINDOW` 3× wider than the corpus uses | `e9bdc11` — 300 → 120 on a measured sweep; max live distance is 93 characters |
| **G4-3, G4-4** | the window reached across table rows and drawing columns | `e9bdc11` — same-line scoping in tables and fences, proven by injection |
| **G4-12** | `CLAUDE.md` §2b's "48 % unfalsifiable" described a configuration that no longer existed | `e9bdc11` — corrected to the measured 7.2 points, 26.6 % → 19.4 % |
| **G8 / G11-48** | duplicate `false_positive_note` key silently discarded by every loader | `4641a25` — recovered; zero duplicate keys at any depth, proven by node walk |
| **G5-25** | the KS-33 footprint table duplicated and **already diverged on drill diameter** | `4641a25` — de-duplicated; the page a board is laid out from was the stale one |
| **G5-1, G5-10** | `README.md` never mentioned `config/figures.yaml` or `CLAUDE.md` | `4641a25` — both named in the tree |
| **G5-2, G5-3, G7-21, G7-22, G7-23, G7-24, G12-5** | four stale counts in the files that exist to explain the repo | `4641a25` — replaced with the command that produces them, not with new numbers |

## Open, and named rather than quietly dropped

**Ordering blockers (G6).** `J-DISP`, `J-LED-L`, `J-LED-R` and `C-ADC-BULK`
are drawn and have **no BOM row at all**; `J-UMBILICAL` is a product family
with `status: candidate`; `R-PRECISION` is `selected` with two unchosen
order-code letters; and the 82 nF C0G package is contradicted between two
rows. These stop an order today and should lead the next batch.

**Page-vs-BOM disagreements (G9).** Sixteen of them — `R-FB` 40 k drawn
against 40.2 k tabled, `C-BULK-RAIL`, `R-LED-SER`, `R-OUT-PROT`, four refdes
in drawings that exist nowhere in the BOM, and five drawings with column
drift. The BOM was trimmed this session and the pages were not.

**Register facts (G8-3, G3-2, G2-5).** `diode-split-rationale`'s `value`
(69 mΩ) is incompatible with its own derivation and with the banked
datasheet; the module +12 V total is 404 mA in one ADR and 392 mA in four
other places; and all three citations in one register entry point at wrong
lines, one into a file 300 lines shorter than the reference.

**Tooling (G10-17, G10-41, G4-6, G10-25).** `verify-datasheets.py`'s corpus
half has no shape assertion — the identical blind spot `check-staleness.py`
documents as found-and-fixed, never crossed to the sibling. Only
`check-staleness.py` is wired to anything. Eight file extensions inside
`CORPUS_DIRS` are scanned by nothing (latent; `.MD` is the sharp one). And
`check_links([])` still yields `PASS` — `instrument()` proves a check was
*called*, never that its result reaches the verdict. G10's `--selftest`
proposal is the fix and is not built.

**The structural question, and it is the user's call.** Rule 2b's cut line
took history out of the data files. It has **no prose counterpart**, and
every slice found the prose is now where the defects are. G2's corollary is
the uncomfortable one: a grep check over a corpus that keeps history inline
is *weakest exactly where it is most needed*, because a refutation is the
best possible evidence that the retired value is present.

**The standing assumption is worth re-testing (G7-10).** `CLAUDE.md` records
that ten consecutive rounds found the previous round's fixes partial. G7
found a *stale ledger* making a complete fix read as partial. Some of that
ten-for-ten may be ledger staleness rather than partial work, and nobody has
ever checked which.

## The wave's own defect

The freeze bound the orchestrator and **not the reviewers**: two slices were
told to inject defects and revert in the tree ten cold reviewers were
reading. Cost, measured: **one finding**, withdrawn in the open — and it cost
only one because that finding cited a *generated, untracked artefact* rather
than a tracked file. Mitigations, both one line: injection slices get their
own clone **at a unique path** (one clone was deleted under its slice), and
every slice records `git status --short` beside each `[test]`.
