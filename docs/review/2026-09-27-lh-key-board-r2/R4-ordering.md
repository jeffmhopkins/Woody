# R4 — Ordering and sourcing: can the left-hand key board be ordered and built today?

**Slice:** R4, wave `2026-09-27-lh-key-board-r2`. **Cold:** read only `CLAUDE.md`
and this wave's `README.md` under `docs/review/`.
**Revision measured:** `eebcdfb` (HEAD `36341bf` adds only the wave README)
`[run: git log --oneline -3]`. Nothing in the repository changed except this file.
Scratch work: `/tmp/claude-0/-home-user-Woody/e3911cc0-db94-59ad-9e1f-62b9c10df7ff/scratchpad/R4/`.
Web checks were made on **2026-09-27**. Where a page was read through WebFetch,
the figures are what its summariser reported and are marked so.

**Method.** I followed `hardware/boards/key-board-lh/README.md` "Ordering it"
and "Assembling the rest by hand" as a first-time orderer would. I then
checked each bought part three ways:
1. `fab/*-bom-jlc.csv`, `*-cpl-jlc.csv` and `*-hand-assembly.csv` against the
   sheets' `Manufacturer`/`MPN`/`LCSC`/`Assembly` fields. I dumped these with
   a parser, `scratchpad/R4/dump.py`.
2. The sheets against the BOM rows' requirements.
3. Each LCSC number against JLC's own component search API, and each part
   against a US distributor.

## Findings

### R4-1 [medium] `CBL-CHAIN`: the length code is emitted as `4.48`, but Samtec's code is `XX.XX` with two integer digits (`04.48`)

- **Node:** `CBL-CHAIN`, and `mechanical/drc.echo` "key-chain cable to order (FFSD length code)".
- **Evidence:**
  - `drc.echo` line 52 prints `4.48` and says `FFSD-06-D-<this>-01-N-RN2` `[repo mechanical/drc.echo:52]`. Followed literally, the part number is `FFSD-06-D-4.48-01-N-RN2`.
  - Samtec's own print and catalogue give the field as `XX.XX` / `"XX.XX"` `[datasheets/connectors/SAMTEC-FFSD-XX-X-XX.XX-01-PRINT.pdf sheet 1, part-number block; datasheets/connectors/SAMTEC-FFSD-1.27MM-IDC-CABLE.pdf p.1]`.
  - Every FFSD-06-D that Digi-Key lists is zero-padded: `02.00`, `02.50`, `03.00`, `04.00`, `05.00`, … `[web https://www.digikey.com/en/products/result?keywords=FFSD-06-D, 2026-09-27, via WebFetch summary]`.
  - Samtec resolves `samtec.com/products/ffsd-06-d-04.48-01-n-rn2` to an FFSD product page. `…/ffsd-06-d-4.48-01-n-rn2` gives only a search-results page with no part `[web, both URLs, 2026-09-27, via WebFetch]`.
  - The value itself is right `[calc]`. `mechanical/cad/woody_body.scad:929` is `ceil((104.37 + 2×3.05 + 3.175)/25.4 × 100)/100` = `ceil(447.42)/100` = 4.48 in. The overall length is well above the 1.00 in minimum (print note 11), and the series is "non-standard, non-returnable" (catalogue p.1). A malformed code on a non-returnable custom cable is the one place in this ordering path where a typo costs money.
- **Fix:** have `woody_body.scad` format the echo zero-padded, e.g. `str(chain_order_in < 10 ? "0" : "", …)` with two decimals. Or have the echo and the `CBL-CHAIN` row both write the full part number. The README step 3 and the `CBL-CHAIN` row should say "two integer digits, zero-padded (`04.48`)". Samtec's configurator should confirm the full part number before paying.

### R4-2 [medium] `MECH-KB-SCREW`: "M2 low-head cap screw (DIN 7984)" is not a standard part, and its head size is `[from memory]`

- **Node:** `MECH-KB-SCREW`, and `config/body.yaml` `hardware.kb_screw_head_d` / `kb_screw_head_h`.
- **Evidence:**
  - The row specifies DIN 7984 `[repo hardware/unplaced.csv:27]`.
  - DIN 7984's size range begins at M3 `[web https://www.fasteners.eu/standards/DIN/7984/, 2026-09-27]`. Accu and other US stockists list DIN 7984 from M3 `[web search "DIN 7984" "M2 x 4", 2026-09-27; https://accu-components.com/us/low-head-cap-screws/8736-SSCL-M4-4-A2]`, and no M2 × 4 DIN 7984 turned up.
  - The modelled head, 3.8 × 1.6, is `[from memory]` with `status: tbd` `[repo config/body.yaml:778-786]`. It matches no standard M2 head I can name `[from memory]`:
    - ISO 4762 / DIN 912: 3.8 × 2.0;
    - ISO 7380: 3.5 × 1.3;
    - ISO 7045 / DIN 7985: 4.0 × 1.6;
    - DIN 84: 3.8 × 1.3.
  - The head diameter sizes the copper keep-out and `kb_standoff_inset`: "leaves 1.1 mm of board outside it" `[repo config/body.yaml:791]`. So a buyer who substitutes a 4.0 mm pan head, or a 2.0 mm tall DIN 912 head, is outside what the board and the CAD were checked against.
  - The row has no US source, unlike its washer and standoff siblings `[repo hardware/unplaced.csv:25-27]`.
- **Fix:** name a real, stocked M2 × 4 (standard, material, and one US source). For example ISO 7380 button head, A2, from McMaster or Aspen `[from memory]`. Set `kb_screw_head_d/_h` from that standard's table, re-run `tools/cad.py build`, and confirm the keep-out and "key-board screw heads clear of the chain header" still pass. Drop "DIN 7984" from the row.

### R4-3 [medium] `SW1-n` (SW-LH1…5): the hand list and the sheet carry a description, not an order code, although the banked drawing names one

- **Node:** `SW1-n`, and `fab/key-board-lh-hand-assembly.csv` rows SW-LH1…SW-LH5.
- **Evidence:**
  - The MPN field reads `KS-33 Red (linear) - bought, BOM row SW1-n` `[repo hardware/cluster/key-switch-network/key-switch-network.kicad_sch MPN field; fab/key-board-lh-hand-assembly.csv]`. The row admits "ORDER CODE NOT RECORDED … until then that field is a description, not a part number" `[repo hardware/cluster/bom.csv SW1-n]`.
  - The banked vendor spec is for Gateron Item No. **KS-33H10B050NN-Y24**, "Keyboard Switch (Low Profile 2.0 Red)" `[datasheets/mechanical/GATERON-KS-33-VENDOR-SPEC-DRAWING.pdf p.1]`. The plate slot, the cutout and the depth geometry are all taken from that drawing (PLATE-TOP row).
  - The US listings a first-time buyer finds for "KS-33 Red" mix three products: Low Profile 2.0 Red, **Red Silent**, and **Low Profile 3.0** `[web search, 2026-09-27: https://www.walmart.com/ip/…/19931559478 (Red Silent 2.0); https://www.gateron.com/products/gateron-ks-33-low-profile-30-mechanical-switch; https://mechanicalkeyboards.com/products/gateron-ks-33-20-red-low-profile-45g-linear-switch]`.
- **Fix:** put `KS-33H10B050NN-Y24` (Low Profile 2.0 Red, black bottom housing) in the sheet's `MPN` field. The hand list then carries it. Add one US source to the row, e.g. mechanicalkeyboards.com "KS-33 2.0 Red", $0.38 each, US stock `[web above, via search summary]`. Add a line: "not Silent, not 3.0; check the code on the packaging against the drawing".

### R4-4 [medium] One instrument needs the right-hand board, and it cannot be ordered today; the README does not say so

- **Node:** `PCB-CLUSTER` (qty 2), `hardware/boards/key-board-rh`.
- **Evidence:**
  - `PCB-CLUSTER`: "Two - left hand (5) and right hand (6)" `[repo hardware/cluster/bom.csv]`.
  - `hardware/boards/key-board-rh/` holds only the schematic, its netlist and renders. There is no `.kicad_pcb`, no `layout.yaml`, no `fab/` and no README `[run: ls hardware/boards/key-board-rh/]`.
  - The LH README says only "The right-hand board is a different design and a separate order" `[repo hardware/boards/key-board-lh/README.md:137]`. A first-time orderer reads that as "orderable elsewhere".
  - The bought-separately quantities in the README are per LH board. The BOM rows are for both boards: `MECH-KB-*` 8, `CBL-CHAIN` 2, `J-CHAIN` = chain-connectors.
- **Fix:** one sentence in the quantity row: "The right-hand board has no layout yet (`key-board-rh` is schematic only); an instrument needs both." Optionally, a per-board versus per-instrument column for the hand-fitted hardware.

### R4-5 [low] `MECH-KB-WASHER`: the named US sources sell M2 ISO 7092 only by the 4,400, and the McMaster alternative's thickness range is wider than the window

- **Node:** `MECH-KB-WASHER`, and `hardware.kb_washer_t_range`.
- **Evidence:**
  - The row's source is Aspen Fasteners, with "McMaster-Carr and Amazon list the same part" `[repo hardware/unplaced.csv:26]`.
  - Aspen's M2 A2 ISO 7092 sells in boxes of 4,400 or 16,000, from $173.84 `[web https://www.aspenfasteners.com/m2-din-433-iso-7092-metric-flat-washers-small-outside-diameter-a2-stainless-steel/, 2026-09-27, via WebFetch]`. Amazon's listing is "(4400 pcs)" `[web https://www.amazon.com/Metric-Washers-Outside-Diameter-Stainless/dp/B082GJYXKR, search result title, 2026-09-27]`. That is about $174 for the eight washers the instrument needs.
  - McMaster's M2 18-8 ISO 7092 washer, 98689A110, comes in packs of 100 but is listed at **0.2–0.4 mm** thick `[web https://www.mcmaster.com/products/washers/specifications-met~iso-7092/, 2026-09-27, via WebFetch summary; not confirmed on the part page]`. That is outside `kb_washer_t_range` [0.25, 0.35] `[repo config/body.yaml:765]`, and the washer sets the board depth.
  - The README's "check a sample with calipers" catches a bad washer, but only after purchase.
- **Fix:** name a small-pack source whose listed thickness range is inside [0.25, 0.35], or state that the McMaster part must be sorted by calipers. Bank the washer's dimension sheet (Aspen publishes `https://www.aspenfasteners.com/content/pdf/Metric_DIN_433_spec.pdf` `[web search result]`) with a manifest row, since `kb_washer_t` and its range are `[web]` only.

### R4-6 [low] `J-CHAIN`: the README sends the buyer to Samtec (0 in stock), but Digi-Key lists the exact part in stock

- **Node:** `J-CHAIN`, SHF-106-01-L-D-RA.
- **Evidence:**
  - The README says: "Order the stand-in from samtec.com and check the lead time" `[repo README.md:174]`. The row says the same.
  - samtec.com shows 0 in stock for the tube part. Its -TR and -FR (reel, MOQ 300) variants "ship tomorrow", from $3.00 each, and samples are offered `[web https://www.samtec.com/products/shf-106-01-l-d-ra, 2026-09-27, via WebFetch]`.
  - Digi-Key lists SHF-106-01-L-D-RA, "CONN HEADER R/A 12POS 1.27MM", **in stock at $2.83** `[web https://www.digikey.com/en/products/result?keywords=SHF-106-01-L-D-RA, 2026-09-27, via WebFetch summary; quantity not reported]`.
  - JLC still shows C17202657 = SHF-106-01-L-D-RA, Extended, stock 0 `[run: JLC selectSmtComponentList API, keyword C17202657, 2026-09-27]`. That confirms the README.
- **Fix:** name Digi-Key as the US source in the `J-CHAIN` row and README, with Samtec direct as the fallback. Keep "check stock at order".

### R4-7 [low] `C-BULK-CHAIN-LH`: bring-up step 6 says "its row says which part", but the row is a spec with no part number

- **Node:** `C-BULK-CHAIN` (`C-BULK-CHAIN-LH`).
- **Evidence:**
  - The README says "fit `C-BULK-CHAIN-LH` (its row says which part)" `[repo README.md:219]`.
  - The row reads "Capacitor 10uF X5R or X7R, 10V or more", with no manufacturer or MPN `[repo hardware/interfaces/key-chain-loom/bom.csv]`. The sheet symbol has no `Manufacturer`/`MPN`/`LCSC` `[run: dump.py on key-board-lh.kicad_sch]`.
  - This is correct as DNP, but if the rail rings the builder has nothing to order. A stocked part that meets the row: Samsung CL21A106KAYNNNE, 10 µF 25 V X5R 0805, LCSC C15850, JLC **Basic**, stock 5.5 M `[run: JLC API, keyword C15850, 2026-09-27]`.
- **Fix:** put a bought part in the sheet's fields with `Assembly = none`, so it stays out of the order. Or change the README wording to "its row says what the part must be".

### R4-8 [advisory] UNI-ROYAL resistors (`R-KEY-SER`, `R-KEY-PU`, `R-KEY-PU-FREE`) have no US distributor

- **Evidence:**
  - Digi-Key returns no result for `0805W8F2201T5E` `[web https://www.digikey.com/en/products/result?keywords=0805W8F2201T5E, 2026-09-27]`.
  - They are JLC Basic parts with millions in stock: C17408 9.59 M, C17520 3.67 M `[run: JLC API]`, so the JLC path is unaffected.
  - The fallback the README offers for the register (buy in the US, hand-fit or consign) has no equivalent here, if a board ever has to be hand-built.
- **Fix (optional):** name a US-stocked equivalent in each row's notes. Examples: YAGEO RC0805FR-07100RL / RC0805FR-072K2L `[from memory]`. The capacitors are already covered: CL21B473KBCNNNC at Digi-Key, 166,265 in stock; CC0805KRX7R9BB104, 1.61 M in stock `[web https://www.digikey.com/en/products/result?keywords=CL21B473KBCNNNC and …=CC0805KRX7R9BB104, 2026-09-27]`.

### R4-9 [advisory] Datasheet bank: the washer and the screw have no banked document

- **Evidence:**
  - `python3 tools/verify-datasheets.py` → "96 verified, 24 recorded as blocked or not-fetched, 0 problems" `[run]`.
  - Every other bought part on this board has an OK manifest row: SN74HCS165, the three passives' documents, the SHF print and catalogue, the FFSD print and catalogue, the PEM MPF bulletin, and the KS-33 vendor spec `[repo datasheets/MANIFEST.csv rows 32-35, 55, 60, 61, 80, 86, 91]`.
  - `MECH-KB-WASHER` and `MECH-KB-SCREW` have none (`grep 7092\|433\|7984` finds no manifest row), and the board depth is computed from the washer.
- **Fix:** bank the washer sheet (R4-5), and the chosen screw's standard table once R4-2 picks one, each in a new fragment.

### R4-10 [advisory] `MECH-KB-STANDOFF`: US stock not independently confirmed; PEM names stainless sheet only

- **Evidence:**
  - Mouser has an MSO4-M2-3 product page, but it returned HTTP 503 twice. Bisco lists it (ref 450MSO4-M2-3) with price and stock behind a ZIP-code prompt `[web https://www.mouser.com/ProductDetail/PEM/MSO4-M2-3?qs=l4Gc20tDgJJGVYgEmlXxlA%3D%3D; https://www.biscoind.com/pem-mso4-m2-3/p, 2026-09-27]`.
  - PEM's catalogue page rates it for sheet hardness "HRB 88 / HB 176 or less" and mentions stainless sheet only `[web https://catalog.pemnet.com/item/…/mso4-m2-3, 2026-09-27]`. The bulletin also says "Can be installed into stainless steel sheets" `[datasheets/mechanical/PEM-MPF-MICROPEM-FASTENERS.pdf p.5]`.
  - This agrees with the row's "CONFIRM BEFORE ORDERING THE PLATE" and the README's Open table. It is not a new defect.
  - The README's assembly also needs `PLATE-TOP` with the standoffs pressed in, and that order is not in this README. That is correct scope, but the builder should know the LH board cannot be assembled as written until the plate exists.

## Checked and found correct

- **LCSC numbers point at the sheets' MPNs, with the README's library status** `[run: JLC selectSmtComponentList API, 2026-09-27]`:

  | LCSC | Part | Library | JLC stock |
  |---|---|---|---|
  | C17408 | 0805W8F1000T5E | Basic | 9,585,459 |
  | C17520 | 0805W8F2201T5E | Basic | 3,674,850 |
  | C49678 | CC0805KRX7R9BB104 (100 nF 50 V X7R) | Basic | 18,081,009 |
  | C53134 | CL21B473KBCNNNC (47 nF 50 V X7R) | Basic | 204,396 |
  | C2864745 | SN74HCS165DR | Extended, not Preferred | 112, as the README says |

- **Every MPN meets its row** `[repo row files]`:
  - `R-KEY-SER`: 100R 1% 0805;
  - `R-KEY-PU`: 2k2 1% 0805;
  - `C-KEY`: 47 nF X7R 0805;
  - `C-DECOUPLE-165`: 100 nF X7R 0805;
  - `U-KEYS`: SN74HCS165, SOIC-16, Schmitt-trigger inputs;
  - `J-CHAIN`: 2×6 1.27 mm shrouded right-angle through-hole. `-01-L-D-RA` is valid per the print: lead style 01, 10 µ" gold, double row, right angle `[datasheets/connectors/SAMTEC-SHF-1XX-01-X-D-XX-PRINT.pdf sheet 1]`. The -L plating matches FFSD's standard 10 µ" contact plating `[FFSD catalogue p.1]`.
- **US source for the register:** Digi-Key SN74HCS165DR, 5,845 in stock at $0.73, Active. This matches the README `[web https://www.digikey.com/en/products/detail/texas-instruments/SN74HCS165DR/13563029, 2026-09-27]`.
- **The fab files agree with each other and with the board:**
  - `bom-jlc` and `cpl-jlc` carry the same 18 designators. `pos.csv` adds only `J-CHAIN` `[run: python cross-check]`.
  - The PCB's footprints: 7 caps (5 C-KEY, 1 decoupler, 1 DNP bulk), 11 resistors, 1 SOIC-16, 5 switches, 1 J-CHAIN, 6 test pads, 4 M2 holes `[run: grep footprint key-board-lh.kicad_pcb]`.
  - `C-BULK-CHAIN-LH` and the test pads are excluded from the BOM and the position file.
  - The NPTH file has four 2.2 mm holes and four 5.25 mm holes. The CPL and the Gerbers share one origin: outline X 97–181, Y −100.5…−142.5 `[run]`.
- **JLC Economic settings in the README** `[datasheets/fab/JLCPCB-PCBA-CAPABILITIES.pdf, Economic table and "PCB Specs for Economic PCB Assembly"]`:
  - 1.2 mm is a standard FR-4 thickness `[datasheets/fab/JLCPCB-PCB-CAPABILITIES.pdf, Thickness row]`.
  - Economic assembly takes 1.2 mm, green or black, lead-free HASL, 2–30 boards.
  - Economic is single-sided placement, and every placed part is on the bottom.
  - The `.gbrjob` says 1.2 mm and "HAL lead-free".
  - The Extended-part fee is $3 per part `[datasheets/fab/JLCPCB-PCBA-FAQ.pdf, FAQ 6]`. Consigned parts are accepted (same FAQ).
  - The BOM and CPL column names match the banked guide's Method 1 `[datasheets/fab/JLCPCB-KICAD-BOM-CPL-GUIDE.pdf]`.
- **The FFSD part-number structure** `FFSD-06-D-XX.XX-01-N-RN2`, apart from R4-1's zero-padding:
  - lead style 01, standard plating blank, N notch, -RN2 on the second connector only;
  - -RN2 is allowed with -N and -D (not with -RW or -R);
  - the length is overall, 1.00 in minimum, and ±0.125 in below 12.5 in.

  `[FFSD print sheet 1 and sheet 2 fig 3]`. Digi-Key stocks only standard (no -RN2) FFSD-06-D lengths. The README's warning that a standard cable is wrong is therefore the right guard for anyone shopping there.
- **Other checks:**
  - The KS-33 has a US source (mechanicalkeyboards.com and others, above).
  - `python3 tools/merge-bom.py --check` → 158 rows, 0 problems `[run]`.
  - `verify-datasheets.py` passes `[run]`.
  - The staleness hook reported PASS on every call `[run: PreToolUse hook]`.
