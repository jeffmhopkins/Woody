# D20 — Completeness audit of the fix batch `0e68f25..HEAD`

**Slice:** the mandatory one. Not "is the fix right?" but "did it land everywhere
the value it changed is read?"

**Subject:** the seven commits `df22096, b32c557, c65083d, 6645fb7, 79f5c4a,
04b5208, 092b364` and their messages. Every claim verified **at HEAD**, not at
the commit that made it.

**Method:** extract each checkable assertion from the seven messages; re-derive
it at HEAD from the repository (`[repo]`, `[calc]`, `[test]`, `[datasheet]`);
then, for each corrected quantity, grep the whole corpus
(`hardware/**`, `docs/decisions/**`, `docs/reference/**`, `config/**`,
`firmware/**`, `README.md`, `ROADMAP.md`) in every spelling — spaced, unspaced,
ASCII hyphen, en dash, inside CSV cells, inside ASCII drawings.

**Read:** this wave's `README.md` only, then git log/diff and the tree. Nothing
else under `docs/review/**`.

**Tools at HEAD** `[test]`:

```
python3 tools/check-staleness.py   PASS  corpus 123 files, 23 circuits, 37 figures / 218 patterns
python3 tools/merge-bom.py --check checked 139 rows from 26 fragments | 0 problems
python3 tools/verify-datasheets.py 78 verified, 23 blocked/not-fetched, 0 problems
python3 tools/merge-manifests.py   MANIFEST.csv regenerates byte-identical
```

All four green. **The defects below are all invisible to all four**, which is
the point: they are semantic, or they are counts, or they are the one spelling
nobody put in the list.

---

## Headline

The tenth round is partial, like the nine before it. **Nineteen defects**, in
four shapes this repository has produced before:

1. **A fix that landed on the owner and not on the page that cites the owner** —
   ADR 0004 still says the CLR reset state is "the same safe state as rack
   power-on"; ADR 0006 reversed exactly that on 2026-09-21. ADR 0004 cites
   ADR 0006 in the same sentence.
2. **A retired value, live, in the document that OWNS the figure** —
   `0004:842` says "The 97 mm above", 52 lines under a table that now totals
   110 mm. `97 mm` is a retired `panel-height-budget` candidate. The pattern
   list holds `"97mm"` and `"97 mm against ~110 mm"` and not a bare `97 mm`.
3. **Counts that went stale inside this batch, and one inside its own commit.**
   Seven of them, including three in the meta-documents this slice was told to
   check and one in the sentence that tells the reader how to check the map.
4. **Notes that record a defect in the wrong tense** — two pages still say a
   sister page "still carries" a defect that the last commit of this batch
   fixed; one says the CV jacks "are not" placed, and they are.

Plus one **duplicate YAML key** in `config/figures.yaml` that silently discards a
`false_positive_note` — the same class as the YAML break the fixer already
caught, undetected.

---

## A. Asserted as done, and not done at HEAD

| # | Claim (source) | Verdict | Evidence |
|---|---|---|---|
| **A1** | `b32c557`: *"ADR 0006's pitch power-on row said 'below −2 V, subsonic' … Both terms are zero, so the jack sits at 0.000 V"* — **fixed in ADR 0006 only** | **INCOMPLETE — the refuted claim is live in ADR 0004, which cites ADR 0006 for it** | `[repo] docs/decisions/0004-cv-interface-module.md:506-510`: *"an A/C grade part clears to zero scale, which parks pitch subsonic and the mod channels at 0 V (ADR 0006), **the same safe state as rack power-on**."* `[repo] 0006:203` now reads *"**Exactly 0 V** — an ordinary, audible note \| **Not subsonic**"*, and `[repo] hardware/module/pitch-stage/pitch-stage.md:137-141` derives it: *"Power-on is 0.000 V … After it, `CLR` parks at −2.500 V. … they are different states, 2.5 V apart."* **The nuance matters and cuts one way only:** in the watchdog context 0004 describes, the reference *is* enabled, so "parks pitch subsonic" is defensible; **"the same safe state as rack power-on" is precisely the equivalence the fix destroyed.** The passage is live reasoning (the struck-through heading above it says *"The paragraphs below are kept because the problem they describe is still real"*), not history |
| **A2** | `df22096`: *"panel-height-budget — four retired values in the PANEL row, four misses, each by one removed space"* — fixed in `bom.csv` + fragment | **INCOMPLETE — a fifth instance is live in the OWNER document** | `[repo] docs/decisions/0004-cv-interface-module.md:842`: *"**The 97 mm above** is built from `[from memory]` component envelopes"*. The table it points at `[repo] 0004:790` now reads **"110 mm against 115.5 mm"**. `97 mm` is a retired candidate — `[repo] config/figures.yaml:407` forbids `"97 mm against ~110 mm"`, `"97 mm against ~110"`, `"= 97mm"`. **None of the three matches a bare `97 mm`**, so the checker reports PASS. `[calc]` the line predates the batch (`git log -L 838,848` → `7a5236c`) and survived the wave that rewrote the budget four rows away from it |
| **A3** | `79f5c4a`: *"pcb-pipeline.md re-measured its own BOM gap against the current tree rather than repeating the review's number: ~50 rows/105 units is now 34/75 … **The CV jacks are not** [placed]"* | **SUPERSEDED BY A LATER COMMIT IN THE SAME BATCH, and not followed** | `[repo] docs/reference/pcb-pipeline.md:155` still reads **34 \| 75**. `[calc]` at HEAD `hardware/unplaced.csv` is **32 rows / 67 units**. `[repo] 04b5208` moved `J-CV` (×6) to `hardware/module/bom.csv` and `D-CLAMP-BREATH` (×2) to `breath-receive-stage/bom.csv`. So also: `:157-160` *"Of those 34, **five** are module-board netlist parts … `J-CV` ×6 … `D-CLAMP-BREATH` ×2 … **Thirteen units**"* → **three rows, five units** at HEAD (`U-TVS-MODULE`, `R-BREATH-SUM` ×2, `R-BREATH-OFF` ×2); and `:176` ***"The CV jacks are not"*** [placed] is **false** — the same session placed them 7 minutes later |
| **A4** | `79f5c4a`: *"`ks33-geometry.md`'s plate-to-PCB conclusion … It is now a height rule"* + `04b5208`: *"cluster-boards.md … The fix landed on the page that owns the figure; this is the page that built on it"* | **FIX CORRECT; the owner page's note was not retensed** | `[repo] docs/reference/ks33-geometry.md:138-143`: *"**`hardware/cluster/cluster-boards.md` §'Three layout rules that are not obvious' **still carries** the reversed conclusion** … **That page has to follow this one**; it is outside this file to change."* `[repo] hardware/cluster/cluster-boards.md:153-173` carries the corrected **height** rule and a dated supersession note. The corpus now asserts a live defect that does not exist, at the exact page a reader would check |
| **A5** | `c65083d` / `79f5c4a`: *"repo-maintenance.md section 7 claimed 'every tracked file has a row'. That was the claim CLAUDE.md section 6 sends readers there to rely on"* — asserted fixed, with the check written into the page | **FALSE AGAIN AT HEAD, broken by the last commit of this batch** | `[test]` running §7's own four-line assertion at HEAD: `tracked 407, placed 406` → **`docs/review/2026-09-22-fix-audit/README.md` has no row.** `[repo] repo-maintenance.md:295` still asserts *"every tracked file has a row"*, and `:318` says *"run it whenever files are added, **because a new file is an orphan the moment it is committed**"*. `092b364` added a file and did not run it. `[calc]` the second assertion (`placed - tracked`) still holds |
| **A6** | `79f5c4a`: *"410 rows: 405 tracked files, plus 4 `deleted` and 1 duplicate destination"* | **ARITHMETIC WRONG, AND IT WAS WRONG WHEN WRITTEN** | `[calc]` at HEAD: 410 rows = 406 non-deleted + 4 deleted; distinct `new` values = **406**; **duplicate destinations = 0**. `[calc]` at `79f5c4a` itself: 410 rows, 406 non-deleted, 406 distinct, `git ls-tree -r 79f5c4a` = 406 tracked, zero missing, zero extra. So there were never 405 and never a duplicate destination. This is the sentence that tells the next restructure how to audit its own map |
| **A7** | `b32c557`: *"README carried '77 banked documents' and 'seven waves', both true when written and wrong within the week — which is the reason this repository cites rather than restates"* | **THE CORRECTION RESTATES A COUNT, AND IT WENT STALE IN THIS BATCH** | `[repo] README.md:117`: *"`docs/review/` holds **nine** waves."* `[calc]` `ls -d docs/review/*/` = **10** at HEAD; 9 at `b32c557`; `092b364` created the tenth. The explanatory sentence immediately below (`:118-121`) names restating-instead-of-citing as the failure and then does it |
| **A8** | `b32c557`: *"CLAUDE.md said three review waves had run; there are nine"* | **STALE AT HEAD, same cause** | `[repo] CLAUDE.md:114-115`: *"**Nine have run.** `docs/review/` is the index; this list is not kept in sync by anything and said 'three' for months while **the directory held nine**."* `[calc]` the directory holds **ten** as of `092b364`. The self-aware sentence is itself the defect it describes |

---

## B. Counts stated in a document, wrong at HEAD

Every one is in a file this batch edited. None is reachable by any check.

| # | Statement | At HEAD | Note |
|---|---|---|---|
| **B1** | `[repo] hardware/README.md:72` *"It was 50 rows and is now **34**. **Sixteen** of them were drawn all along"* | **32 rows**, **eighteen** moved | `[calc]` `unplaced.csv` 50 → 34 (`0e68f25`) → **32** (`04b5208`). This batch's own last content commit |
| **B2** | `[repo] docs/reference/repo-maintenance.md:204` *"`hardware/unplaced.csv` holds the **50 rows of 138** that no schematic page names"* | **32 rows of 139** | Both halves wrong. The `50` is the *pre-fix* number — this sentence was never updated at all, in the commit titled *"docs/reference/ catches up with the restructure"* |
| **B3** | `[repo] repo-maintenance.md:191` *"`merge-bom.py` rebuilds it from **24 per-circuit** `bom.csv` fragments"* | **26** fragments in `ORDER`, of which **22** are per-circuit, 3 board-level, 1 `unplaced.csv` | `[test]` `merge-bom.py --check` prints *"139 rows from 26 fragments"* |
| **B4** | `[repo] docs/reference/pcb-pipeline.md:153-154` *"master \| **138** \| **388**"*, *"In the **23** per-circuit fragments \| **104** \| **313**"* | master **139 / 390**; **22** per-circuit fragments holding **94 / 261** (107 / 323 with the 3 board-level) | `[calc]` the master went 138→139 in **the same commit `79f5c4a`** that wrote this table (`R-LED-PD` was added to `led-strip-drive/bom.csv`). Stale before the commit finished |
| **B5** | `[repo] hardware/README.md:43-45` *"**The two** board-crossing tables (`interfaces/breath-sense-link`, `interfaces/spi-link`) carry an extra **End** column"* | **Three.** `[repo] hardware/interfaces/key-chain-loom/key-chain-loom.md` header is `\| Node \| End \| Dir \| Peer \| Figure \| Note \|` | The same file at `:22` calls `interfaces/` *"The **3** circuits that cross a board boundary"*. Self-contradictory in 22 lines |
| **B6** | `[repo] tools/merge-bom.py:9-10` *"`bom.csv` is the most-cited file in the repository - **37** backtick references"* | **66** in the corpus (50 `` `bom.csv` `` + 16 `` `hardware/bom.csv` ``) | `[calc]` `grep -ro` over the corpus paths. Low consequence, same class |
| **B7** | `[repo] docs/review/2026-09-22-fix-audit/README.md` *"**85 corpus files** changed, +2,684 / −1,228 lines"* | **79** corpus files; 86 files total | `[calc]` `git diff --numstat 0e68f25~1..092b364~1` restricted to the `CLAUDE.md` §6 corpus = 79 files / +2064 / −1162. The `85` is *all files minus `docs/review/`* and the line counts are the all-files numbers — so the label "corpus" is wrong and the three numbers come from two different sets |

---

## C. Structural defects the batch created or walked past

| # | Defect | Evidence |
|---|---|---|
| **C1** | **Duplicate YAML key silently discards a `false_positive_note`.** `panel-height-budget` declares `false_positive_note` **twice** — `[repo] config/figures.yaml:408` and `:423`. `yaml.safe_load` keeps the **last**, so the first note — the one recording that `panel.md:20` and `0004:736` legitimately *narrate* the superseded numbers — **is not loaded and cannot protect anything.** `[test] python3 -c "…"` returns only the `:423` string. It is the sole duplicate key in the file `[calc]`, and it is the same class as the `derivation` string that broke the YAML earlier in the session — except this one does not raise |
| **C2** | **A consequence sentence orphaned onto the wrong subject.** `[repo] docs/reference/pcb-pipeline.md:78-83`: the new `SCLK` paragraph ends *"Merging them shorts a buffer across itself"*, and is immediately followed by *"A transcription taking names off the drawings shorts **the breath in-amp input to the breath output jack**"* — which is the `BREATH` collision's consequence, not `SCLK`'s. `[calc] git log -L 78,88` shows the sentence belonged to the `BREATH` bullet, was orphaned by `c65083d`, and had the `SCLK` paragraph inserted above it by `04b5208`. It now reads as the consequence of a claim it does not follow from |
| **C3** | **Three dangling *Still open* cross-references.** `[repo] hardware/interfaces/key-chain-loom/key-chain-loom.md:134` and `:143` both say *"see *Still open*"*; the page has **no such heading** (`:1,19,44,111,151,172,200,254`) and neither does its `notes.md`. `[repo] hardware/carrier/display-and-service-uart/display-and-service-uart.md:58` — *"5 V (or +12 V — see Still open)"*, inside the drawing — same. `[calc]` every other page that uses the phrase has the section. `git log -S"## Still open"` on `key-chain-loom.md` returns nothing, so the section never existed there: the text was moved in during the restructure and its pointers were never retargeted. `6645fb7` edited both pages and did not catch it |
| **C4** | **A settled figure's question is posed as open on a circuit page.** `[repo] key-chain-loom.md:141-143`: *"**Six conductors is the signal count, not the conductor count.** Whether this connector is **6-way or 10-way** is a decision this page cannot take alone."* `[repo] config/figures.yaml` `chain-conductors` = **12**, `status: settled`, owner ADR 0001; `[repo] docs/decisions/0001:81` *"12 conductors per hop (2x6 IDC)"*; `[repo] config/key-layout.yaml:108` *"TWELVE conductors leave each board on a 2x6 IDC"*. The page offers two widths, neither of which is the settled one, and routes the reader to a section that does not exist (C3). **This is plausibly the "fifth item, deliberately not done" of `04b5208`; if so, nothing in the corpus tells a reader that.** What would settle it: the commit's own words are *"two live topologies where one is a settled tracked figure"* — if this is the pair, the deliberate non-fix is recorded only in `docs/review/**`, which is outside the corpus by design |
| **C5** | **Probable broken anchor, replicated 23 times.** `[repo]` all 23 circuit pages link `](../../README.md#the-interfaces-table)`; the target heading `[repo] hardware/README.md:24` is ``## The `## Interfaces` table``. Under GitHub's slugger (strip backticks and `#`, lowercase, spaces→hyphens) that heading yields **`#the--interfaces-table`** — two hyphens, because the removed `##` leaves a double space. `[repo] tools/check-staleness.py:903` splits the fragment off before resolving (`tgt = m.group(1).split("#")[0]`), so anchors are never checked. **Settled by:** rendering `hardware/README.md` on GitHub and clicking one link, or renaming the heading to `## The Interfaces table` |
| **C6** | **A `false_positive_note` cites a line that has moved.** `[repo] config/figures.yaml:277` — *"`key-chain-loom.md:138` says 'Six conductors is the SIGNAL count…'"*. At HEAD that sentence is at **`:141`** `[calc]`. Harmless today; it is the citation-drift shape the register exists to prevent |

---

## D. Corrections that landed on the value and not on everything derived from it

| # | Item | Verdict |
|---|---|---|
| **D1** | `b32c557`: *"ADR 0014's strip table is computed at ~20.2 mA per LED … Both strips full white becomes roughly 27 W and ~81 K rather than 12.1 W and ~36 K. The table is annotated rather than rewritten"* | **ANNOTATION INCOMPLETE — it corrects one of the three places the retired figure is used.** `[repo] 0014:134-152` annotates the density table and names the *"Both strips full white"* row. Un-annotated, all derived from 20.2 mA/LED: `[repo] :175` *"Matrix full white as well \| ~17.7 W \| **~53 K**"* (contains the same strip term); `:198` *"3 W is … **about a sixth of the pathological case**"* (`[calc]` 3/17.7 ≈ 1/6; at the corrected strip figure the pathological case is ≈32 W and the ratio is nearer a tenth); `:257` *"around **0.13 A** there, which is unremarkable against a 3 W budget"*. The annotation is ~40 lines above the table row it corrects, and `12.1 W`/`~36 K` remain the printed numbers |
| **D2** | `b32c557`: *"CABLE-UMB specifies no conductor gauge while three derivations compute from 24 AWG … Recorded with what decides it"* | **RECORDED ON THE BOM ROW ONLY.** `[repo] hardware/bom.csv` `CABLE-UMB` notes carry the gap, the 1.6×–2.6× consequence and the E6 decider — correct and complete on that row. **None of the three derivations carries a marker**: `[repo] docs/decisions/0005:92` *"Over 2 m of **24 AWG**, round trip ~0.34 Ω"*; `[repo] hardware/interfaces/breath-sense-link/breath-sense-link.md:112` *"(0.168 Ω for 2 m of **24 AWG**…)"*; `[repo] docs/decisions/0003:315` *"Drop across 2 m of **24 AWG**"*. A reader arriving at any of the three is told nothing. The row names them by file and line; the pointer runs one way only |
| **D3** | `04b5208`: *"`ks33-contact-bounce` is now tracked, owned by `ks33-geometry.md`"* | **TRACKED, BUT CITED ONCE AND RESTATED THREE TIMES.** `[calc]` `grep -rn ks33-contact-bounce` over the corpus → **one** citation, `[repo] docs/decisions/0002:218`. Restating the number instead: `[repo] docs/reference/latency-budget.md:126` *"Gateron publishes **5 ms max bounce at 16 in/sec**"*; `[repo] ROADMAP.md:121` *"— **5 ms max at 16 in/sec** —"*; `[repo] docs/reference/repo-maintenance.md:133`. Rule 1 says state once, cite everywhere. The figure was created **after** `latency-budget.md` was rewritten in `79f5c4a`, so the citations were never propagated — the fix landed where the editing was happening, in the paragraph (`latency-budget.md:117-120`) that names that failure mode |
| **D4** | `df22096`: `inamp-full-scale` −9.6/−10.05 → **−9.94 V**, *"in two files at once because the master is generated from the fragment"* | **VALUES ALL CORRECT AT HEAD; the citation discipline was not applied.** `[calc]` no live `−9.6`/`−10.05` outside refutation text or the `mod-channels` false-positive set (four `±10.05 V` lines about the MOD range, correctly excluded). But **four non-owner files restate the number**: `[repo] breath-receive-stage.md:133`, `breath-output-stage.md:42,53,54`, `breath-response-shaper.md:54,107`. The owner is `breath-sense-link.md`. The next move of this figure is a four-file edit again |
| **D5** | `df22096`: `key-press-time` / `key-release-time` *"the patterns were written in markdown spelling and the BOM is CSV"* | **CSV instances fixed; the ADR restates all three key figures in a live table.** `[repo] docs/decisions/0001:227-229` prints **119.9 µs**, **5.92 µs**, **1.43 mA / 25.8 mA** — three tracked figures (`key-release-time`, `key-press-time`, `key-scan-current`, all owned by `key-switch-network.md`) with no citation by name. `check_restated` cannot see it: it fires at ≥3 files and only for values with no register entry |

---

## E. Verified complete — the claims that hold

| Claim | Verdict | Evidence |
|---|---|---|
| `b32c557`: `DAC8568CIPW` → `DAC8568ICPW`, *"reached the BOM, ADR 0006, MANIFEST.csv and the banked file's own NAME"*; file keeps its name | **COMPLETE** `[calc]` every remaining corpus occurrence of `DAC8568CIPW` is a **file path** (`figures.yaml:352`, `ROADMAP.md:48`, `0006:183`) or narrated supersession (`bom.csv`, `0006:176`). Residual, by design and stated: `MANIFEST.csv` carries both rows, the wrong code first, because R2's fragment may not be edited |
| `b32c557`: ADR 0004's `V_INH` 3.65 V → **3.26 V**, *"the conclusion survives"* | **COMPLETE** `[calc]` `3.65` appears once in the corpus, in its own refutation (`0004:213`). `[repo] 0004:209` reads `0.625 × AVDD = 3.26 V`; no other page states the threshold `[calc]` |
| `df22096`: `sensor-full-scale` nine spellings, `0005:74`, `0003:565`, three BOM rows, `D-TVS-BREATH` 300 mV → **140 mV** | **COMPLETE** `[calc]` the four decoys survive untouched and correctly (`0005:97,100,103` — the 5 V rail arriving at ~4.7 V; `breath-receive-stage.md:133,201` and `breath-output-stage.md:45,61` — the in-amp's −4.7 V). `140mV` present in fragment **and** master `[repo]` |
| `df22096`: `chain-conductors` `ROADMAP:203`, `panel-width` `ROADMAP:53` | **COMPLETE, and converted to citations** `[repo] ROADMAP.md:203` now reads `` `chain-conductors` per hop ``; `:53` reads `` good practice at `panel-width` ``. `[calc]` zero `HP` tokens left in `ROADMAP.md` |
| `6645fb7`: *"exactly one page sources the DAC's SPI nets"* | **VERIFIED** `[calc]` one `Sourced here` (`digital-and-supervision.md:30`), one `Not sourced here` (`spi-link.md:45`) |
| `6645fb7`: *"bus +5V … Resolved to power-entry, confirmed against FB-IN qty 4"* | **VERIFIED** `[repo] power-entry.md:30` `out`, `digital-and-supervision.md:31` `in`; `[calc]` `FB-IN` qty = **4** |
| `6645fb7`: *"96 directed, ZERO one-sided, ZERO isolated, zero naming a circuit that does not exist"* | **VERIFIED EXACTLY** `[test]` 23 circuits, 48 undirected = **96 directed**, one-sided **0**, isolated **0**, unknown targets **0**. Also `[test]` every `fig:`/`refdes:`/`adr:` edge resolves — **0** unresolved |
| `6645fb7`: *"Every circuit.yaml header now says plainly that circuit: edges are verified and adr:/fig:/refdes: edges are still seeded"* | **VERIFIED** `[calc]` all 23 files contain both statements |
| `6645fb7`: *"Dir settled at five values"* | **VERIFIED** `[calc]` exactly `in` (49), `—` (43), `out` (41), `ref` (27), `in/out` (4) across all 23 tables |
| `6645fb7`: five rows named the pre-split page; *"breath-receive-stage and breath-sense-link carried the same defect on CLR"* | **VERIFIED** `[repo]` both `CLR` rows now read *"Reaches no part of this circuit"* with Peer `—`; `VREFOUT` peers `module/dac8568` |
| `6645fb7`: *"panel.md stops calling itself 'not a circuit'"* | **VERIFIED** `[repo] panel.md:10` narrates it in past tense; `[calc]` no live instance |
| `79f5c4a`: Dir/Peer legend *"duplicated in all 23 circuit pages and is now defined once in hardware/README.md and cited"* | **VERIFIED** `[calc]` 23/23 pages carry the citation, 0/23 inline the legend. (Anchor target is suspect — see **C5**) |
| `79f5c4a`: *"the digital-and-supervision drawing labelled the buffer's OUTPUTS with the same three net names as its inputs"* | **FIXED** `[repo] digital-and-supervision.md:58-61` — outputs now `SCLK_DAC↓ DIN↓ SYNC↑` with *"◄ buffer OUTPUTS, not the same nets as the three above"* |
| `79f5c4a`: *"breath-output-stage's drawing had a tracked value inside a net label"* | **FIXED** `[repo] breath-output-stage.md:73-74` — `` DAC AVDD … (`dac-rail`) `` |
| `79f5c4a`: *"R-LED-PD … in no BOM fragment at all"* | **FIXED** `[repo] hardware/carrier/led-strip-drive/bom.csv:5`, and out of the checker's *drawn-not-bommed* list `[test]` |
| `79f5c4a`: *"the Gateron drawing … yields 9,680 characters"*; *"survey of all 60 banked PDFs"*; TE catalogue and NKK toggle extractable | **SUBSTANCE VERIFIED, ONE NUMBER OFF** `[datasheet] pymupdf on datasheets/mechanical/GATERON-KS-33-VENDOR-SPEC-DRAWING.pdf`: 6 pages, **11,053 characters**, contains *"Bounce Time: 5msec Max.(at 16 in/sec. actuation speed)."*, contains neither `1.20` nor `14.0`. `[calc]` 60 PDFs banked. `[repo] repo-maintenance.md:127-129` says *"11 kB"* — the **document is right and the commit message's 9,680 is wrong** |
| `b32c557`: two BLOCKED manifest rows (`D-TVS-BREATH`, `U-ESD-USB`); new R9 fragment for the DAC | **VERIFIED** `[repo] datasheets/.manifest-R9.csv:2-4`; `[test]` `MANIFEST.csv` regenerates byte-identical from the fragments |
| `b32c557`: `plate_thickness: null` closed in `key-layout.yaml`; `cluster-boards.md` citation closed; *"what actually gates M4/M5 is named: stiffening"* | **VERIFIED** `[repo] config/key-layout.yaml:41` = `1.20` with the reasoning above it; `[repo] cluster-boards.md:175-187` |
| `b32c557`: README links `hardware/README.md` from the front door | **VERIFIED** `[repo] README.md:126-129` |
| `b32c557`: CLAUDE.md gains the three step-2 traps and the *"most hits will be legitimate"* counterpart | **VERIFIED** `[repo] CLAUDE.md`, and the counterpart is used in practice — `panel-width`'s `false_positive_note` records *"Nine of the eleven live 8HP/6HP hits on 2026-09-21 were legitimate"* |
| `04b5208`: `J-CV` out of `unplaced.csv`, filed at board level | **VERIFIED** `[repo] hardware/module/bom.csv:5`, qty 6 (but see **A3**) |
| `04b5208`: `D-CLAMP-BREATH` *"the drawing names it now, and the row is placed"* | **VERIFIED** `[repo] breath-receive-stage.md:67` and `:110` both write the refdes; row in `breath-receive-stage/bom.csv:7` |
| `04b5208`: *"pcb-pipeline.md's collision list is five, not four, and AGND denotes three nets"* | **VERIFIED** `[repo] pcb-pipeline.md:61-73` — five rows, `AGND` three nets with `R1b` named (but see **C2**) |
| `c65083d`: §3's `pypdf` note replaced with the stub / pymupdf routes | **VERIFIED AND IT WORKS** `[test]` pymupdf 1.28.2 read the Gateron PDF on the first attempt using §3's route |
| `c65083d` / `79f5c4a`: path map 287 → 409 → **410**, *"every datasheet path now resolves"*, `.moves.csv` used rather than directory names | **VERIFIED** `[calc]` 410 rows, `old` side exactly 287 distinct paths, `placed - tracked` = **0**, both 74HC165 filename renames present. (The *"every tracked file"* half is broken again — **A5**; the decomposition sentence is wrong — **A6**) |
| `04b5208`: two patterns withdrawn for firing on true sentences, recorded in `false_positive_note` | **VERIFIED** `[repo] config/figures.yaml:642-655` |
| CLAUDE.md's own procedural claims: hook, corpus set, CRLF, 11 columns | **VERIFIED** `[repo] .claude/settings.json` runs `check-staleness.py` on `Bash(git commit *)`; `[repo] tools/check-staleness.py:30-32` `CORPUS_DIRS`/`CORPUS_FILES` match CLAUDE.md §6 exactly; `[calc]` `hardware/bom.csv` 140/140 lines CRLF, 11 columns, every fragment CRLF |

---

## F. The four self-recorded errors, treated as samples of a class

The wave README names four. Taking each as a *class* rather than a closed item:

| Class | Further instances found |
|---|---|
| **A `forbidden` pattern that fires on a true sentence** (3 recorded) | **None new.** `[test]` the checker passes and the 68 *"old values present but refuted in place"* entries all carry refutation wording. The four `sensor-full-scale` decoys, the four `mod-channels` `±10.05 V` lines and the nine legitimate `8HP`/`6HP` hits are all correctly excluded. **This class appears genuinely closed.** The *inverse* is not: **A2** is a retired value with no pattern that can reach it |
| **`git add -A` sweeping in another agent's work** (2 recorded) | **None at HEAD.** `[calc]` `git status` is clean of corpus changes; the only untracked files are other D-slice reports being written now. `[calc]` no half-finished edit is present in the seven commits' trees |
| **A citation to a figure id that did not exist** (1 recorded) | **None in the Interfaces tables** — `[test]` all `Figure`-column citations resolve; all `fig:` edges resolve. But the class generalises to **citations to things that are not figures**, and there it is alive: **C3** (three pointers to a section that does not exist), **C5** (23 pointers to an anchor that probably does not exist), **C6** (a line-number citation that has drifted), **A4** (a note pointing at a page that no longer carries the defect) |
| **A YAML break from text appended after the closing quote** (1 recorded) | **One new instance of the silent variant: C1**, a duplicate `false_positive_note` key in `panel-height-budget`. It does not raise — `yaml.safe_load` keeps the last and discards the first. `[calc]` it is the only duplicate key in the file, and nothing in the toolchain would ever report it |

---

## G. What I could not check

- **`docs/review/<wave>/STATUS.md` claims** (`04b5208`: *"STATUS.md records the outcome above the recommendation rather than instead of it"*; *"Four of the five pre-merge items are done and proved by reproducing the attack"*). The cold rule forbids reading `docs/review/**`. **Not checked, not disputed.** The half that is checkable from the corpus — whether the fifth, deliberately-unfixed item is visible to a corpus reader — is **C4**, and it is not.
- **Agent counts** in `CLAUDE.md` (*"20 agents"*, *"12 agents"*, *"22 agents"*) — same reason.
- **`CLAUDE.md` / `repo-maintenance.md`: *"Two BOM rows are deliberately blocked on a datasheet and say so."*** `[calc]` no row contains the phrase *"blocked on a datasheet"*; 16 rows mention blocking, 12 carry `TBD`. The two are most likely `D-TVS-BREATH` and `U-ESD-USB`, matching the two new BLOCKED manifest rows. **Settled by:** the author naming the two refs, or the rows adopting a literal marker so the claim becomes greppable.

---

## H. The pattern, stated once

Of the nineteen defects, **fifteen are on a page that cites the page that was
fixed.** Not one is a wrong value in the place the fix was made. The fixes in
this batch are, as far as this slice can tell, *correct* — the arithmetic
re-derives, the graph measures what the message says, the datasheet re-reads
confirm. What they are not is *arrived*.

Three of them went stale **inside this batch**: `pcb-pipeline.md`'s BOM table
(**B4**, stale in its own commit), the `unplaced.csv` counts (**A3**, **B1**,
stale seven minutes later), and the path-map assertion (**A5**, broken by the
commit that opened the wave to audit it).

The mechanical reading: **a count restated in prose is a forbidden pattern
nobody wrote.** The register protects values. It does not protect *"50 rows"*,
*"nine waves"*, *"the two board-crossing tables"*, *"405 tracked files"*, or
*"34 \| 75"*, and every one of those is now wrong. Seven of the nineteen would
be caught by a check that re-derives a stated count from the tree — which is
what `check-staleness.py` already prints for the corpus file count, and what
repo-maintenance §7 already writes out in four lines for the path map and then
does not run.

**Nine for nine becomes ten for ten.**
