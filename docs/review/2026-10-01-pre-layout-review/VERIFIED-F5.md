# VERIFIED — fixer F5 (A8, A9)

**Base:** `claude/car-instrument-cad-design-xvqwv2` at `9956171`, later merged
again after F3 landed. **`tools/` modified** in this branch (`check-staleness.py`,
`extract-findings.py`) — named in each row.
**Ids owned:** every `A8-*` except A8-1, A8-4 (F1) and A8-7, A8-8 (F2); every
`A9-*`. 28 ids, plus A4-11 received from F3.

**Counts:** 16 CONFIRMED, 2 PARTLY (A8-3, A8-9), 0 REFUTED, 10 DUPLICATE.
Fixed here in full: A8-5, A8-6, A8-10, A8-15, A9-11, A4-11. Fixed here in
part: A8-11 (register), A8-12, A8-14, A8-19. OWNER: A8-2, and A8-3's sensor.
HANDED: A8-11 (page), A8-12 (one comment), A8-13, A8-16, A8-18, A8-19 (three
parts), A9-5 (residue), A9-7, A9-12, A9-13.

**One correction to A8's method, which matters for every orderability claim
below:** A8 measured stock on **LCSC's storefront** (`wmsc.lcsc.com` product
API). Machine-placed parts are drawn from **JLC's own parts library**, a
separate stock. Re-measured on both on 2026-10-01 for every one of the 99
LCSC codes on the sheets `[web: LCSC product API; jlcpcb.com parts-search
API selectSmtComponentList]`: at JLC only **FB-IN** is short among machine
parts; C28260, C28323 and C51349 are stocked there by the thousand. Written
into `docs/reference/tooling.md` §4 *Ordering: JLC's stock, not LCSC's*.

| Id | Verdict | Action | Evidence |
|---|---|---|---|
| A8-2 | CONFIRMED | **OWNER** (options below). No part changed. Würth 74279221601 datasheet banked (fragment R43-F5) as the evidence for option 2 | `[web]` C2441375: LCSC stock 0, **JLC stock 0** (2026-10-01). Searched JLC for every in-stock 1206 600 Ω ≥1 A bead (Murata BLM31PG/KN, TDK, Sunlord PZ/UPZ, TAI-TECH HCB, Chilisin PBY, FH CBW, YJYCOIN, ZE, APV, Yanchuang, Würth WE-CBF and WE-MPSB) and read each LCSC datasheet: only Würth **WE-MPSB 74279221601** (C2661423, JLC 3,667) publishes impedance under DC bias, and only at **1, 2 and 2.5 A** `[ds WURTH-74279221601-WE-MPSB-ferrite-bead.pdf p.2]`: ~65 Ω at 1 A, ~590 Ω at 0 A (100 MHz, read off the charts). FB2/FB4 sit at ~0.22–0.37 A (`ferrite-bias-impedance`), between those traces, so the figure cannot be re-derived from it. The Laird part is plentiful at distributors: Newark 15,320, RS 42,570, Sager 96,000 `[web findchips.com 2026-10-01]` |
| A8-3 | PARTLY | No part changed; tooling §4 note (5390b79). **OWNER** for U-BREATH (below) | `C-FB-PITCH` C28260: LCSC 0 but **JLC 123,345, Basic** — REFUTED as an orderability gap for a machine part. (Also C28323, `C-INRUSH-GS`/`C-REG-OUT`: LCSC 0 since A8 ran, JLC 2,294,300 Basic.) `U-BUCK` C3033024 and `U-LOADSW` C664552: 0 at LCSC and JLC — CONFIRMED, but both are `hand` and their rows already say to buy from a distributor; Recom R-78E5.0-1.0 Newark 17,794; LT1641-1IS8#PBF Newark 51 (the row's "Newark 272" of 2026-09-30 has moved), brokers several thousand `[web findchips 2026-10-01]`. `U-BREATH` C5190605: LCSC/JLC 3 against qty 2; Newark 0, Avnet 0, brokers only (Chip Stock 2,053, MacroQuest 92) `[web findchips 2026-10-01]` — CONFIRMED and worse than A8 said |
| A8-5 | CONFIRMED | Fixed cb2a530: `pcb-pipeline.md` "2 layers or 4" (both four layers; cites `dig-gnd-topology`, no dead `proposed_if_four_layers`), and its "the board is hand-assembled" (the module sheets machine-place most parts; `Assembly` field, `pcb.py` assembly files). ADR 0018 point 5 re-worded and a dated amendment added. `dig-gnd-topology`'s stale `false_positive_note` sentence removed; 3 forbidden spellings added | `[repo]` `config/figures.yaml` `dig-gnd-topology` settled 2026-09-30; `spi-link.md:46,124` only cite it; grep found the stale spellings only at `pcb-pipeline.md:320-327` and `0018:57`. Sheet `Assembly` counts by circuit `[repo]` (e.g. module/mod-channels 45 machine, 4 hand) |
| A8-6 | CONFIRMED | Fixed 15b7cf2: §4 notes bullet now states rule 2b (no history in `.csv`, replace the sentence, `audit-notes.py --regrown`); the stale "two clusters" sentence replaced | `[repo]` `hardware/unplaced.csv` 44 rows: mechanical parts, cables, PCBs, not-fitted parts, `J-B2B-MOD`; jack protection is drawn on pitch-stage/mod-channels/breath-output-stage; `C-DECOUPLE` (module) is placed |
| A8-9 | PARTLY | No part changed; tooling §4 note | `[web]` LCSC product API `result: null` for C51349 — CONFIRMED on LCSC. JLC parts search: **C51349 SWPA6028S220MT, Sunlord, 4,931 in stock** (2026-10-01). Both 22 µH parts are `machine`, so JLC is the source that matters |
| A8-10 | CONFIRMED | Fixed 15b7cf2: spi-link row names `R-RX-MOD`/`C-RX-MOD` into `U-RX-MOD` (74AHCT14); `key-board-rh/sim` row added; the shaper row now says its `D-RESP` is behavioural, fitted to the 1N4448W window (A1-3 makes that the bought part) | `[repo]` `spi-link/sim/sims.yaml:1-5`; 20 `sim/` dirs; `sim_coverage.py` PASS after |
| A8-11 | CONFIRMED | Register fixed f5ea412: value and derivation re-derived. **HANDED** (module power page owner): `hardware/module/power-entry/power-entry.md:122-123` "(`r_d` is 69 mΩ at 392 mA)" → "(`r_d` ≈ 0.55 Ω in `D2` at `U-ISO`'s ~0.22 A input, ≈ 2.8 Ω in `D1` at the analog rails' ~37 mA; `diode-split-rationale`)"; then add forbidden `"69 mΩ at 392 mA"` to `diode-split-rationale` (not added here: it would fire on the page until the hand-off lands) | `[calc]` least-squares fit of V = a ln I + b + R_s I to the four points the register already digitised off `[ds 1N5817.pdf Fig. 2]` (0.245 A 0.24 V, 0.612 A 0.36 V, 1.0 A 0.454 V, 3.0 A 0.746 V; residuals < 5 mV): a = 0.100 V, R_s = 0.093 Ω; r_d = 0.100/0.22 + 0.093 = 0.55 Ω, 0.100/0.037 + 0.093 = 2.8 Ω. The old 69 mΩ was a/I with a = 27 mV and no bulk term, ~5× low even at 392 mA (0.35 Ω by this fit). Conclusion (HF isolation) strengthens |
| A8-12 | CONFIRMED | Fixed f5ea412: `opa2197-output-impedance.note` now points at `cref-out-node`/`riso-ref-topology`/`riso-ref-phase-margin`; `umbilical-current` derivation says 358.1 is carried as 359 because an upper bound rounds up; its `false_positive_note` no longer names the retired 392 mA; `check-staleness.py` prints `blocked_on` as the decider. **HANDED**: `config/key-layout.yaml:157-158` "the right thumb is only its three" → "its four" (RT1–RT4, `right_thumb: 4`). Not done here because any byte in that file re-fingerprints every body CAD output (`cad.py`), so it belongs with the next real key-layout change | `[repo]` figures.yaml:568-635 settled entries; `[calc]` 226 × 5/(0.9 × 11.4) + 248 = 358.14; `.staleness/report.txt` now prints the E6 decider |
| A8-13 | CONFIRMED | **HANDED** (key-chain-loom owner; F3's domain, F3 finished): `hardware/interfaces/key-chain-loom/key-chain-loom.md:19-21` to state "four `J-CHAIN` (main-board J4/J5, one per key board)" as the owner | `[repo]` the page only cites the figure (lines 21, 42, 43, 48, 532); BOM `J-CHAIN` qty 4 |
| A8-14 | CONFIRMED | Partly fixed 84d7c5f: `check_sheet_fields()` matches every forbidden pattern against each placed symbol's `Value`/`Manufacturer`/`MPN`/`LCSC`/`Note` (no refutation exemption — data). 0 hits on the corpus; an injected `REF5050AIDR` MPN fires `[ref5050-grade]`. Documented in `repo-maintenance.md` §2. **Still open:** nothing checks an MPN against its BOM row's part, or an LCSC code against its MPN — that needs the network (this round's by-hand check: all 99 codes resolve, 98 on LCSC and C51349 on JLC, each to the sheet's MPN) | `[repo]` `tools/check-staleness.py` corpus filter `.md/.csv/.yaml`; `netlist.yaml` exports carry no MPN/LCSC |
| A8-15 | CONFIRMED | The stale photo was re-rendered at `9956171` (before this base); `check-staleness.py` PASS, 0 cad. The miscount fixed fab1223 (see A9-11) | `[repo]` `git log` 9956171; checker output |
| A8-16 | CONFIRMED | **HANDED** (module power owner): `hardware/module/umbilical-load-switch/umbilical-load-switch.md:327-330` — the "0805 C0G package in `bom.csv` is wrong" sentence is fixed in the row ("THROUGH-HOLE radial or 1210 ceramic"; sheet GRM32DR71E106KA12L 1210 X7R) | `[repo]` BOM `C-TIMER-LOADSW`; `[web]` LCSC C77100 |
| A8-17 | DUPLICATE of A1-3 | None here. The owner decided (2026-10-01) to buy the 1N4448W the bound was fitted to; once A1-3's owner changes `D-RESP`, "1.51× at the worst corner" covers the bought part. tooling §5 row already re-worded | `[repo]` `breath-response-shaper/sim/sims.yaml:5-8` |
| A8-18 | CONFIRMED | **HANDED to the orchestrator**: after every fixer branch has merged, convert the six fragments to CRLF in one commit (`merge-bom.py --check` passes either way). Not done here: five of the six are other fixers' circuits, and a whole-file line-ending change now would conflict with each of their row edits | `[calc]` CRLF count 0 of 7/10/9/5/24/16 lines in `carrier/`, `carrier/breath-excitation-reference/`, `interfaces/spi-link/`, `module/digital-and-supervision/`, `module/power-entry/`, `module/umbilical-load-switch/` `bom.csv` |
| A8-19 | CONFIRMED | (1) `J-UMBILICAL-INST`: LCSC C368526 set on umb-adapter `J1` and spi-link `J-UMB-INST`, and on spi-link `J-UMB-MOD` (also empty) — d670bf2, **sheet fields only, in F3's spi-link and the umb-adapter board**; exports unchanged, renders re-ledgered. (2) `U-MCU-RT` empty identity fields: **HANDED** with A6-5 (same symbol, `carrier.kicad_sch`). (3) `J-B2B-MOD` in `unplaced.csv`: **HANDED** (module boards owner, A7) — it is on both module board sheets. (4) `C-BULK-RAIL` two parts in one row: **HANDED** (module power owner), recommend one row per part. (5) KS-33 drawing BLOCKED row: closed bc3083f by an OK row quoting its exact part string with SUPERSEDES; re-fetched byte-identical (sha256 4ec2109e…) | `[repo]` sheet fields; `[web]` LCSC C368526 NE8FAV in stock; `merge-manifests.py` now lists the row under "now banked elsewhere" |
| A9-1 | DUPLICATE of A7-1 | Already fixed at `9956171` (also A2-15, A8-15) | checker PASS, 0 cad |
| A9-2 | DUPLICATE of A3-6 | — | `[repo]` `power-entry.md:199` still "~45 mA and ~40 mA" at this base |
| A9-3 | DUPLICATE of A1-8 | — | `[repo]` `breath-output-stage.md:24` |
| A9-4 | DUPLICATE of A5-7 and A3-4 | A5-7 fixed by F3 (`R-CS-PULL-MOD` row) | `[repo]` VERIFIED-F3.md A5-7 |
| A9-5 | DUPLICATE of A5-9 | F3 fixed `spi-link.md` and handed `digital-and-supervision.md`, `link-supervision.md`. **Residue not in F3's hand-off, HANDED** (module digital owner): `hardware/nets.yaml:582,706` and the `U-LVL-MOD` row in `module/digital-and-supervision/bom.csv` ("R-SPI-PULL's six resistors") | `[repo]` grep after merging F3 |
| A9-6 | DUPLICATE of A5-6 | F3 handed it (3.26 V) | VERIFIED-F3.md A5-6 |
| A9-7 | CONFIRMED | Overlaps A5-12, which F3 fixed (40 mA is typical drive, not a limit). **Residue HANDED** (spi-link owner; F3's domain): the 68 Ω row still reads "48 mA fault current" = 3.3/68 with no pad resistance, while the 82 Ω row uses the pad's 17–35 Ω; on one convention 68 Ω gives 3.3/(68+17) = 38.8 mA. Recompute the table on one convention and give 68 Ω's actual reason, if any | `[repo]` `spi-link.md:217-222` after F3; `[calc]` as shown |
| A9-8 | DUPLICATE of A4-9 | F3 fixed ADR 0027, handed `power-entry.md:191,260` | VERIFIED-F3.md A4-9 |
| A9-9 | DUPLICATE of A8-11 | See A8-11 | — |
| A9-10 | DUPLICATE of A4-10 | F3 fixed ADR 0027 | VERIFIED-F3.md A4-10 |
| A9-11 | CONFIRMED | Fixed fab1223: `check_cad()` drops cad.py's `FAIL n CAD output problem(s)` summary line (kept only if it is the sole line); tested against a faked one-problem output → 1. Same commit: `extract-findings.py` reads each finding's `**Severity:**` line (147 of 148 rows had none; A9-6 was mis-filed "high" from "settled high"), reads `VERIFIED-*.md`/`STATUS-*.md` as verification, and counts introduced findings apart from ids only cited (137 + 11, not "148 from 10 slices") | `[repo]` `tools/check-staleness.py` check_cad; run on a copy of this wave |
| A9-12 | CONFIRMED | **HANDED** (module boards owner, A7): `hardware/boards/module-main/README.md:88-90` | `[repo]` allocation table: 9 `OFFSET_WIPER`, 10 `AGND_MOD`, 11 `BREATH_JACK`, 13 `AGND_MOD` |
| A9-13 | CONFIRMED | **HANDED** (shaper page owner, A1): `breath-response-shaper.md:171` "the table below" → "the table above (*Scaling*)" | `[repo]` the 15 kΩ table is at :114-120 |
| A4-11 | CONFIRMED (received from F3) | Fixed e56e3cf: `PWR_GND` is the isolated return on its own layer-4 copper (12 pads), reaching the star only through `DIG_GND`; the star relief re-priced at the analog return, ~0.005 cents at 37 mA. Two forbidden spellings added to `dig-gnd-topology` | `[repo]` `module-main/board-netlist.yaml` `PWR_GND`: 12 endpoints; `[calc]` 0.053 × 37/359 = 0.0055 cents |

## OWNER decisions

**A8-2 — FB-IN (4 × MI1206K601R-10, machine-placed on the module board), 0 at
LCSC and JLC.** No in-stock 1206 bead publishes a bias curve where FB2/FB4
operate.
1. **Keep the characterised Laird part; source it outside JLC's library**
   (recommended). Either JLC Global Sourcing / consignment of 4–10 pieces
   from Newark (15,320), RS (42,570) or Sager (96,000) `[web findchips
   2026-10-01]`, or set FB1–FB4 `Assembly = hand` (four 1206s) and add them
   to the hand list. `ferrite-bias-impedance` unchanged.
2. **Würth WE-MPSB 74279221601** (C2661423, JLC 3,667; 600 Ω ±25 %, 2.5 A,
   50 mΩ max, AEC-Q200). Publishes bias data only at 1/2/2.5 A (~65 Ω at 1 A
   at 100 MHz, ~590 Ω at 0 A). FB1/FB3 (≤ ~45 mA) are on the flat part either
   way; for FB2/FB4 the figure would become "between ~65 and ~590 Ω,
   undocumented at 0.22–0.37 A". Not recommended — it gives up the one
   criterion the part was chosen on.
3. **Murata BLM31PG601SN1L** (C16902, JLC 39,603): an electrical twin with no
   published bias curve at all (already recorded on the row). Same objection,
   stronger.

**A8-3 — U-BREATH (MPXV4006DP, qty 2).** LCSC/JLC hold 3; Newark and Avnet show
0; only brokers have stock `[web findchips 2026-10-01]`. Options: (a) order the
two from LCSC now while 3 remain (recommended — hand-placed, so LCSC
stock is the right source); (b) a broker, with the counterfeit risk that
carries for a sensor whose offset is trimmed in the field; (c) NXP direct /
DigiKey / Mouser, not checked here (their pages refused the session).

## Gates at the head of this branch

`check-netlist.py --strict`: 0 problems (153 rows placed to qty; shorts
`C-DECOUPLE-CARRIER` 5/8 = A8-1, F1's, and `U-BREATH` 1/2 by design).
`merge-bom.py --check`: 210 rows, 26 fragments, 0 problems.
`verify-datasheets.py`: 272 verified, 42 blocked, 0 problems.
`merge-manifests.py --check`: matches. `sim.py check`: PASS, 20 dirs.
`sim_coverage.py`: PASS, 28. `check-staleness.py`: PASS. `kicad.py check`:
PASS, 22 sheets, 6 boards, 129 renders.

**The ledger:** `FINDINGS.csv` is not regenerated here. Run
`python3 tools/extract-findings.py docs/review/2026-10-01-pre-layout-review`
once every `VERIFIED-F*.md` has merged; with this branch's change it reads
them, and fills the severity column.
