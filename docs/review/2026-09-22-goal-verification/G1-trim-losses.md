# G1 — What the BOM notes trim lost

Slice G1 of the 2026-09-22 goal-verification wave.
**Measured against `a4b80b1`** (working tree at `25cc740`, which adds only this
wave's README — verified: `git diff --stat a4b80b1 HEAD` reports one file,
`docs/review/2026-09-22-goal-verification/README.md`, 81 insertions `[test]`).
Pre-trim baseline is `d69f7fa`. **`tools/` is NOT pinned** — it changed inside
the measured range (`92afc0b` touches `tools/check-staleness.py`, `ad3a15c`
and `192d03e` add `tools/audit-notes.py` `[repo: git diff --stat d69f7fa a4b80b1]`),
so every `[test]` below is a run of the tools **at `25cc740`**, and none of them
reproduces against `d69f7fa`'s tools.

## Method

1. `git show d69f7fa:hardware/bom.csv` against the working tree, parsed with
   `csv.DictReader`, keyed by `ref`. **140 rows both sides, no row added or
   removed, no ref renamed** `[test: python3 cmp.py in scratchpad]`.
2. **Only the `notes` column changed.** All ten other columns are byte-identical
   on all 140 rows `[test: column-by-column compare, 0 differences]`. So no
   package, qty, status, part or adr field was altered under cover of the trim.
3. 40 rows changed notes; **every one shrank** (no row grew). Total notes
   118,198 → 82,129 characters, −30.5 % `[test]`.
4. For each changed row I read the old and new cells side by side in full, and
   separately ran a mechanical pass that extracts every old sentence containing
   NEVER / DO NOT / MUST / CHECK / VERIFY / DECIDE / SPECIFY / BEFORE / OPEN /
   BLOCK and reports the ones whose wording does not survive into the new cell
   (shingle match, 50 % threshold) `[test: imper.py]`. That produced 46
   candidates; I read all 46 and most were paraphrase-retained.
5. For each surviving candidate I then asked where it went: the same row, the
   circuit's `.md`, `config/figures.yaml`, `hardware/**/notes.md`, an ADR, or
   `datasheets/MANIFEST.csv`.
6. Inverse direction: every numeric token present in a new cell and absent from
   the old cell for the same row `[test: newnums.py]` — six rows, all traced
   below.
7. CRLF and generation integrity: `hardware/bom.csv` is 141 CRLF terminators
   and 0 bare LF, same as `d69f7fa` `[test]`; `python3 tools/merge-bom.py
   --check` → `140 rows from 26 fragments | 0 problems` `[test]`;
   `python3 tools/verify-datasheets.py` → `78 verified, 23 blocked/not-fetched,
   0 problems` `[test]`; `python3 tools/audit-notes.py --regrown` →
   `0 row(s) still narrating rather than specifying` `[test]`.

## What I could not check

- **I could not re-run the pre-trim corpus through the pre-trim checker.** That
  needs a worktree, which writes into `.git`; the brief says touch nothing else.
  So I cannot give you a before/after on the `restated-not-cited` advisory count
  (211 today `[test: hook output]`).
- **I did not verify any datasheet figure against a banked PDF.** Every
  `[datasheet]`-shaped statement below is quoted from the repo, not re-read from
  the document. G1 is a diff audit, not a datasheet audit.
- **I could not tell, for two of the losses below, whether the deletion was
  intentional.** Commit messages in the range describe the rule, not the
  per-sentence calls.
- **Coldness, disclosed:** I read no file under `docs/review/`. I did read
  `git log --oneline` and the full commit message of `d69f7fa`, whose subject is
  "Round 2 STATUS" and whose body summarises a previous wave's open findings.
  That is git, not `docs/review/`, but it is prior-review content and you should
  discount any agreement between me and Round 2 accordingly. I listed
  `docs/review/` directory names once (to confirm my output directory exists)
  and opened nothing, including this wave's README.

## Verdict

**The trim was sound on 37 of 40 rows, and I would not put any of it back.**
Every deletion I traced was either (a) narrative about what a previous reviewer
believed, (b) a value that is now a tracked figure and is correctly cited by
name, or (c) a verbatim triplication. The delegations are real, not promises: I
checked each one at the destination and they had all landed (see "Verified
landed" below). No warning of the NEVER/MUST class was lost. No numeric bound
was lost without its owner carrying it.

**Three genuine losses, one introduced restatement, one introduced unsourced
claim, and one typo.** The first finding is the only one I would fix today.

---

## Findings

**G1-1 — `U-LOADSW`: the retirement of two alternative controllers was deleted,
and ADR 0005 still offers them. THE MOST EXPENSIVE LOSS IN THE TRIM.**

Removed from `U-LOADSW` `[repo: hardware/bom.csv:64, hardware/module/umbilical-load-switch/bom.csv:3]`:

> (c) 'LM5069MM or LTC4210 equally valid' is RETIRED: the LT1641 datasheet is
> banked, every claim in this row bar the VCC UVLO was confirmed against it, and
> the whole page is derived from it — those two were alternatives from before
> the part was chosen.

It now lives **nowhere in the corpus** `[test: grep -rn "LM5069\|LTC4210" over
hardware, docs/decisions, docs/reference, config, firmware, README.md, ROADMAP.md
→ one hit, and it is the live claim, not the retirement]`. That hit is
`docs/decisions/0005-power-architecture.md:339`:

> **LM5069MM (MSOP-10) and LTC4210 (MSOP-8) are equally valid.**

So the corpus now asserts, in an ADR, that two un-banked parts are equally valid
substitutes for a controller whose every page-level number was derived from one
specific banked datasheet (`164112fc` / `datasheets/discrete-and-power/LT1641.pdf`)
— foldback law, `I_GATE` bounds, `I_TIMER` bounds, UVLO, package theta-JA
`[repo: hardware/module/umbilical-load-switch/umbilical-load-switch.md:123-145]`.
**The only statement that this was no longer true went to git.** This is exactly
the recorded shape "a fix that did not reach the pages citing it", except the fix
was deleted rather than merely not propagated.

Cost if unfixed: someone orders an LM5069MM on the ADR's authority and inherits a
page of numbers that do not describe it.

**G1-2 — `FB-IN`: the retired `>=1 A` rationale was moved into `forbidden` in ONE
spelling, and the corpus carries it in a second spelling that the pattern cannot
match.**

The trim removed from `FB-IN` `[repo: hardware/bom.csv:61]`:

> Rated >=1A — the common 0805 600R part is ~300mA and a saturated bead is a wire

That exact string is a forbidden pattern `[repo: config/figures.yaml:726, figure
`ferrite-bias-impedance`]`, and the figure's own note says why it is retired:
"A bead's current rating is THERMAL, not magnetic, so it says nothing about
saturation" `[repo: config/figures.yaml:727]`. **Removing the sentence was
correct.** The defect is that the same retired claim is live, in prose spelling,
at `docs/decisions/0006-cv-channel-allocation.md:824-826`:

> **Ferrite beads rated ≥1 A, in 1206 or 1210.** The common 0805 600 Ω part is
> rated around 300 mA and both +12 V branches now exceed that. A saturated bead
> does not degrade gracefully — it loses its impedance entirely and becomes a wire.

`600 Ω` not `600R`, `≥1 A` not `>=1A`, "rated around 300 mA" not "~300mA" — a
case-sensitive literal misses all three. The checker reports `0 stale` for this
figure `[test: .staleness/report.txt, STALE VALUES STILL LIVE (1), and the one
is `umbilical-current`, not this]`. This is CLAUDE.md §2's named trap ("write the
pattern in the spelling of the file it must match") with the BOM and a prose ADR
as the two spellings.

Two caveats, both in the trim's favour: the pattern predates the trim
`[test: git log -S over config/figures.yaml → cfcdc6e, an earlier wave]`, and the
useful half of the ADR sentence (do not substitute an 0805 600R part) is still
true — it is only the *reason* that is refuted. But the trim removed the last
corpus instance the pattern could ever match, so that guard is now a no-op, and
`check_patterns` in `tools/check-staleness.py` only flags newline patterns and
self-refuting patterns — **it does not flag a pattern that matches nothing**
`[repo: tools/check-staleness.py, def check_patterns]`.

**G1-3 — `J-UMBILICAL-CABLE`: the cable-OD window lost its upper bound while the
instruction to check against it survived.**

Old `[repo: git show d69f7fa:hardware/bom.csv, J-UMBILICAL-CABLE]`: "NE8MC … cable
OD 5.0-8.0mm … while another source names NE8MX for that role with OD 4.5-8mm".
New `[repo: hardware/bom.csv:115, hardware/unplaced.csv:7]` keeps only the lower
bound: "IT ADDS A 4.5mm LOWER BOUND ON CABLE OD … check the chosen Cat5's jacket
against it".

So the row tells a buyer to check the jacket against a spec it states one half
of. The full range survives in the bank —
"Cable O.D. 4.5 mm - 8 mm" `[repo: datasheets/MANIFEST.csv:21, NE8MX row]` — so
this is recoverable in one lookup, which is why it is ranked third. It matters
because the sibling row `CABLE-UMB` is open on gauge and explicitly contemplates
a thicker or thinner lead `[repo: hardware/bom.csv:125]`, and a booted patch lead
is the case that busts an upper bound.

**G1-4 — `U-LOADSW`: the trim INTRODUCED a three-value restatement of a
page-owned figure that has already gone stale once.**

New text `[repo: hardware/bom.csv:64]`: "VCC UVLO 7.5 / 8.3 / 8.8 V, which holds
GATE low regardless of ON". Neither `7.5` nor `8.3` appears anywhere in the old
cell `[test: newnums.py — U-LOADSW is one of six rows with new numerals, and
these are its only two]`. The values are correct and sourced — the page carries
`V_LKO = 7.5 min / 8.3 typ / 8.8 max V [p.2]`
`[repo: hardware/module/umbilical-load-switch/umbilical-load-switch.md:140]` —
but they are **not a tracked figure** (37 figures; `VCC` UVLO is not among them
`[test: grep "  - id:" config/figures.yaml]`), and this quantity has already gone
stale once in this repo: the same page records it was "9.8 V max" and was
REFUTED, with the story in
`hardware/module/umbilical-load-switch/notes.md:15-25` `[repo]`.

So a trim justified by rule 1 created a fresh uncited restatement of a value with
a staleness history. Low cost today, exactly the right shape to become tomorrow's
defect. Either register it or cite the page.

**G1-5 — `C-GATE-LOADSW`: an unsourced claim was introduced.**

New tail `[repo: hardware/bom.csv:73]`: "C0G/NP0 or film, 50V — the dielectric
matters, because **a Y5V here re-programs the ramp with temperature**". The old
cell contains no Y5V sentence and no dielectric argument `[repo: git show
d69f7fa]`; the `package` column already said "THROUGH-HOLE radial or 1210
ceramic" and carries no dielectric either. The statement is true as general
engineering `[from memory]`, but it entered the corpus in a rewrite, with no
`[datasheet]` or `[calc]` behind it. Flagged because the brief asks whether the
rewrite invented, and this is the one place it did. I would keep it and mark it,
not delete it.

**G1-6 — `D-USBOR`: unbalanced bracket introduced.**

`[repo: hardware/bom.csv:7]`: `['Case: SMA (DO-214AC)', stated four times)` —
opens with `[`, closes with `)`. Cosmetic, one character, but it is inside a
quoted datasheet citation where the brackets carry meaning.

**G1-7 — `J-CHAIN`: three secondary mechanical numbers went and are not anywhere.**

Gone `[repo: git show d69f7fa:hardware/bom.csv, J-CHAIN]`: the socket **body
width 6.10 (.240) MAX**; the header length formula **L = pin-to-pin + 10.20**;
and the stated assumption behind the stack arithmetic — `H_mated = H_header +
H_socket − D_cavity`, "which assumes the socket bottoms on the cavity floor",
with the Wurth header's **6.50 mm cavity**. Not in `key-chain-loom.md`
`[test: grep "6.10" hardware/interfaces/key-chain-loom/*.md → no hits]`.

The conclusions survive intact and correctly (13.1–14.9 mm into a 20 mm cavity,
13.10 mm a hard lower bound, DO NOT FIT A STRAIN-RELIEF CLIP) `[repo:
hardware/bom.csv:49]`, and 8 connectors with their rationale is now the tracked
figure `chain-connectors` `[repo: config/figures.yaml:291-297]`. The body width is
the only one a layout engineer might actually want — it is what sets how close
two of these can sit — so this is a real but small loss.

---

## Checked and NOT a loss

These looked like losses in the mechanical pass and are not. Recording them so the
next round does not re-file them.

**G1-8 — `SW-POWER`'s S4 keyway dimensions survive.** The deleted "5.6mm flat
(S4 keyway) … or a separate 2.2mm dia anti-rotation hole at 6.5mm centres" is
verbatim in the tracked figure's derivation `[repo: config/figures.yaml:442-464,
`panel-toggle-hole`]`, along with the banked drawing path
`datasheets/connectors/NKK-SERIES-M-TOGGLE.pdf`, the 2.6 mm max panel thickness,
and the reason the 6.00 mm alternative was rejected. The register carries more of
this row's history than the row does, deliberately, and is right to.

**G1-9 — `U-LOADSW`'s TPS2553 rejection survives.** "Would not survive first
power-on at 12 V" is alive and argued at
`docs/decisions/0005-power-architecture.md:325-329` `[repo]`.

**G1-10 — `U-DIFFRX`'s deleted E10 warning is obsolete, not lost.** The removed
text warned against trimming to the un-nulled "−0.44 V at rest to −10 V at full".
`ROADMAP.md:51` now instructs "Set `TRIM-BREATH-ZERO` first, until the in-amp
output reads 0 V" `[repo]`, so the thing the warning warned against is no longer
written anywhere.

**G1-11 — `F-CHAIN`'s tooling lesson survives, in the tool.** The deleted
"verify-datasheets.py checks the manifest against the disk, never the corpus
against the manifest" is now a 12-line comment **and an implemented check** at
`tools/verify-datasheets.py:156-175`, which names the `MF-PSMF010X.pdf` incident
that caused it `[repo]`. I tested the corpus for dangling `datasheets/` paths
independently: 114 referenced, 26 non-existent, and **all 26 are inside
`docs/reference/path-map-2026-09-21.csv` or `datasheets/.manifest-R*.csv`**
`[test: python3 path-existence scan]` — i.e. the historical map and the
untouchable fragments, exactly where CLAUDE.md §4 and §6 say not to correct them.
Zero dangling paths in live prose.

**G1-12 — `R-KEY-SER` / `C-KEY` / `R-SPI-SER` lost only superseded arithmetic.**
The `~5.7us` / `44x` / `~1.4us` / `176x` values are all registered as forbidden
patterns `[repo: config/figures.yaml:247-250]` and the removals are the register
working as designed. `R-SPI-SER`'s deleted note about the old
`R-SCLK-SER`/`R-MOSI-SER`/`R-CS-SER` refdes survives in prose at
`hardware/interfaces/spi-link/spi-link.md:59-62` and
`docs/decisions/0004-cv-interface-module.md:558` `[repo]`.

**G1-13 — the three consolidations all landed.** (a) The 1,100-character OPA2197
device block was in `U-BUF`, `U-RESP` and `U-OPA-PITCH` verbatim; it is now on
`U-OPA-PITCH` only, and the 375 Ω Zo, the 1 nF limit with its ringing caveat, the
Table 3 `R_ISO` pointer, GBW/SR/Isc/IQ, the dual-vs-single theta-JA trap and the
"114 dB PSRR is not in the document" correction are all present there `[repo:
hardware/bom.csv, U-OPA-PITCH]`. (b) The four RV09 order-code traps were in
`POT-GAIN`, `POT-OFFSET` and `POT-RESP`; they are on `POT-GAIN` now, complete,
including the A/B-is-angle-not-taper trap and the Song Huei R0904N alternative
`[repo]`. (c) `U-REF-BREATH`'s grade numbers moved to the tracked figure
`ref5050-grade`, which carries both grades, the decider, the four forbidden
spellings, **and the provenance caveat that Table 4-2 is new in rev O** — the one
I expected to have been dropped `[repo: config/figures.yaml:729-746]`.

**G1-14 — the figure delegations are real.** I checked every "do not restate it,
see X" pointer the new cells make. `chain-connectors` (291), `panel-toggle-hole`
(442), `loadswitch-timer` (483), `loadswitch-gate-cap` (499),
`loadswitch-fb-divider` (508), `ks33-contact-bounce` (648), `ref5050-grade` (729),
`breath-zero-ref` (159), `diode-split-rationale` (621) all exist and all carry the
number **and** the derivation the cell stopped stating — including
`loadswitch-fb-divider`'s full 35.7k/5.11k sizing with the 10.05–10.93 V PWRGD
window `[repo: config/figures.yaml:508-517]`. Not one delegation points at
nothing.

---

## One live cross-row defect this audit surfaced (pre-existing, not the trim's)

**G1-15 — `U-TVS-CHAIN` is a 4-channel array specified in SOT-23-6, which is the
package error `U-TVS-SPI` was just corrected for.**

`U-TVS-SPI` moved to SOT-23-5 because "SP0504BAHTG | 4 CH | SOT23-5, and
SP0505BAHTG | 5 CH | SOT23-6" `[repo: hardware/bom.csv:48]`. Its sibling
`U-TVS-CHAIN` is `4-channel TVS array | SOT-23-6 | open`, and its own note says
"U-TVS-SPI does exactly this job for the umbilical's three"
`[repo: hardware/interfaces/key-chain-loom/bom.csv:4]`. Either it is a different
part (then say which) or it has the same wrong package.

The trim did not cause this — `U-TVS-CHAIN`'s notes are byte-identical across the
range `[test: cmp.py, it is not among the 40 changed rows]`. But the sentence the
trim removed from `U-TVS-SPI` was the one that said out loud "this row asserted
SOT-23-6, which is exactly the unchecked-package error it exists to replace
U-TVS-UMB for", and the old `D-USBOR` cell recorded the identical shape one wave
earlier: "the fix landed on the row being edited and not on the row two lines away
that shares the fact". Both of those sentences are gone and the defect they
describe is still here.

---

## Repo state at the time of this report — NOT MINE

`git status --short` was clean when I started `[test]` and **something else is
writing to this working tree while the wave runs.** I observed two different
edits appear and one of them disappear again, in the space of one report:

```
 M docs/reference/path-map-2026-09-21.csv     (mid-session; reverted by the end)
   + x/y,x/y,unmoved,This row previously said ~275 instrument mA and that is superseded and no longer true

 M hardware/module/power-entry/power-entry.md (present as I finished)
   + This page previously said ~275 instrument mA down the umbilical. That is
   + superseded; the corrected figure is: Drop at 290 mA.
```

Both concern the same quantity (`umbilical-current`) and both are shaped as
refutations — one in a `.csv`, where rule 2b gives no exemption, and one in an
`.md`, where it does. That is a probe of the prose-only exemption, run against
the live tree rather than a copy.

**I wrote neither of them**, and nothing I ran can write them — the `PreToolUse` hook
runs only `tools/check-staleness.py`, which writes `.staleness/report.txt` and
`.staleness-report.txt` `[repo: .claude/settings.json]`, and `merge-bom.py
--check`, `verify-datasheets.py` and `audit-notes.py` are all read-only in the
modes I used `[test: all three run, `git status` clean immediately after]`. It
appeared between two of my tool calls, so another slice or the orchestrator is
writing in this working tree.

It matters to whoever reads the checker next: **the staleness hook flipped from
`PASS` to `FAIL` mid-session because of the `.csv` row**, and the failure was
`[umbilical-current] found '~275 instrument' at
docs/reference/path-map-2026-09-21.csv:412` `[test: .staleness/report.txt lines
79-83]`. A `PASS` or a `FAIL` from this hook during this wave may be measuring
somebody else's probe, not the corpus. I left both edits alone, per "touch
nothing else" — but **no `[test]` baseline taken in this wave reproduces**, which
is the freeze problem CLAUDE.md records from the last wave, one layer down: the
corpus itself is moving now, not just `tools/`.

It also shows something worth a line: `docs/reference/path-map-2026-09-21.csv` is
**inside the checked corpus** although it is a historical map of pre-2026-09-21
paths, which CLAUDE.md §6 says is not to be corrected. A future honest history
row in that file will fail the checker.
