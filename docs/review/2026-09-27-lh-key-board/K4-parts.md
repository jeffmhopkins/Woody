# K4 — Parts and assembly of the left-hand key board

**Slice:** K4, cold. **Revision:** `d46a3b0`. `tools/` run, not changed. Read
nothing under `docs/review/` except the wave README.
**Web checks:** 2026-09-27, JLCPCB part pages and JLCPCB's component-search API
(`POST https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList`,
keyword = LCSC number), PEM's SO bulletin.

## Summary

The board can be ordered. Every LCSC number on the sheets is the part its MPN
field names, and each one meets its BOM row. That covers value, tolerance,
dielectric, voltage, package and footprint. All five numbers were in stock
today, and the Basic/Extended/Preferred claims in the README hold. The
Nexperia 74HC165 runs at 3.3 V, and it is the best-documented of the four
banked vendors at that voltage (JESD8C). The JLC BOM and CPL are complete and
consistent: 18 machine parts, each once, all on the bottom, and nothing hand-fitted
or copper-only in either file. Row quantities match what the circuits place.

What is wrong is smaller, and it sits in the explanations and the sourcing
edges. The one medium finding is that the README (and `tools/pcb.py`'s docstring) cites
JLC's banked KiCad guide for something the guide does not say: that JLC
corrects KiCad's rotations itself. The guide attributes those corrections to
the Fabrication Toolkit plugin, which this flow does not use. Because every
machine part is on the bottom side, that matters. The low findings:

- the standoff row names a PEM class that has no M2 member;
- three of the five bought parts have no banked datasheet;
- the README restates sheet part numbers, in a different spelling;
- the switch "MPN" is prose;
- the ordering section leaves out order quantity and the J-CHAIN source.

## Findings

### K4-1 [medium] The README says JLC applies its own rotation corrections, citing a guide that attributes them to a plugin this flow does not use

**Node:** `fab/key-board-lh-cpl-jlc.csv`, all 18 rows (every one `Bottom`);
README "Ordering it", "Check every part's orientation…"; `tools/pcb.py`
`assembly_files` docstring.

- The README says: "JLC applies its tape-orientation corrections itself
  (`datasheets/fab/JLCPCB-KICAD-BOM-CPL-GUIDE.pdf`). We do not guess them."
  `[repo hardware/boards/key-board-lh/README.md]`
- The banked guide describes two methods `[datasheets/fab/JLCPCB-KICAD-BOM-CPL-GUIDE.pdf, Method 1 step 5; Method 2 step 5]`:
  - **Method 1** is KiCad's `.pos` with its headers renamed. That is exactly
    what `tools/pcb.py` writes `[repo tools/pcb.py assembly_files]`. The guide
    describes no rotation correction for it.
  - **Method 2** is the Fabrication Toolkit. For it the guide says: "Keep *Apply
    automatic component translations* ticked (this fixes part rotations/positions
    for JLCPCB)". The correction is the plugin's, not JLC's.
- So the stated provenance does not support the claim. On this board, every
  placed part is on the bottom:
  - `U-KEYS-LH` at 90°, `C-DECOUPLE-165-LH` at 90°, `R-KEY-PU-FREE3` at 90°,
    and the rest at 0° `[repo fab/key-board-lh-cpl-jlc.csv]`.
  - Bottom-side KiCad rotations are the case most often shown wrong in JLC's
    preview `[from memory]`.
- The README's instruction to check the preview before paying is right and
  sufficient as a procedure. Only the reason it gives is wrong.

**Fix:** In the README, replace the sentence with: "JLC does not correct raw
KiCad rotations. Its preview is the only check. Record any correction the first
order needs (e.g. a per-footprint rotation offset in `layout.yaml`) so the
next order does not rediscover it." After the freeze, correct the
`tools/pcb.py` docstring the same way.

### K4-2 [low] `MECH-KB-STANDOFF` names a PEM class with no M2 member

**Node:** `MECH-KB-STANDOFF` (`hardware/unplaced.csv`); drc.echo
"key-board standoff length (derived)".

- The row asks for an "M2 self-clinching threaded standoff … (PEM SO/BSO class)",
  and for "buy that length, not a round number". The length is 2.2 mm
  `[repo hardware/unplaced.csv]` `[repo mechanical/drc.echo:54]`.
- PEM's SO/BSO/TSO bulletin has no M2 `[web https://www.pemnet.com/wp-content/uploads/sites/9/2022/06/sodata.pdf]`:
  - Its metric SO/BSO tables start at M3.
  - Its thin-sheet TSO starts at M2.5. TSO lengths can be specified in 0.02 mm
    steps from 2.00 mm, so a 2.2 mm TSO-M2.5 does exist as a class.
- M2 is sold only as microPEM, e.g. `MSO4-M2-3` (3 mm long). That part is
  400-series stainless, for stainless sheets
  `[web https://appianfasteners.com/pem-mso4-m2-3-m2-x-3-micropem-standoff-bag-of-100.html]`.
- `config/body.yaml` `hardware.kb_standoff_od` / `kb_standoff_hole` (4.0 / 3.2)
  are `tbd` and `[from memory]` `[repo config/body.yaml:718-726]`. The
  microPEM page gives a 3.18 mm sheet hole `[web ibid.]`.
- The README's Open table already hands the length and the alloy to the plate
  vendor. The row, though, points a buyer at a catalogue that cannot supply it.

**Fix:** In the row, name the realistic classes: microPEM MSO/MSO4 (M2, which
constrains the plate alloy), or PEM TSO at M2.5 (which changes
`kb_screw_hole` / `kb_screw_head_*` and `MECH-KB-SCREW`). Also state that the
length is bought at the nearest catalogue length and `switch.pcb_below_seat`
is re-checked, not "that length".

### K4-3 [low] Three of the five bought part numbers have no banked datasheet, and the 74HC165's pin source cites a vendor the board does not buy

**Node:**

| Ref | MPN | LCSC |
|---|---|---|
| `R-KEY-SER` | UNI-ROYAL 0805W8F1000T5E | C17408 |
| `R-KEY-PU` | UNI-ROYAL 0805W8F2201T5E | C17520 |
| `C-KEY` | Samsung CL21B473KBCNNNC | C53134 |
| `C-DECOUPLE-165` | YAGEO CC0805KRX7R9BB104 | C49678 |
| `U-KEYS` (`Pins_source`) | — | — |

- `datasheets/MANIFEST.csv` has no row for UNI-ROYAL, YAGEO or Samsung
  `[run: grep -i 'CL21B\|CC0805\|0805W8F\|uniroyal\|yageo\|samsung' datasheets/MANIFEST.csv → no hits]`.
  CLAUDE.md §3 wants banked documents.
- The 74HC165 bought is Nexperia `74HC165D,653` (C5613). Its datasheet is
  banked (`datasheets/logic/74HC165-nexperia.pdf`, status OK). The sheet's
  `Pins_source` still cites TI's `74HC165-ti-scls116e.pdf p.1`
  `[repo hardware/cluster/key-register/key-register.kicad_sch:400]`.
- The pin-out is identical (TI A..H = Nexperia D0..D7 on pins 11–14, 3–6)
  `[datasheets/logic/74HC165-nexperia.pdf p.3]`
  `[datasheets/logic/74HC165-ti-scls116e.pdf p.1]`. The field names are already
  Nexperia's (`PL`, `CP`, `CE`, `DS`, `Q7`, `D0..D7`).

**Fix:** Bank the three passive datasheets in a new `.manifest-R*.csv`
fragment (JLC part pages link LCSC PDFs), and set `Pins_source` to
`74HC165-nexperia.pdf p.3`.

### K4-4 [low] The README restates the sheets' part numbers, and already spells one differently

**Node:** `U-KEYS-LH` / README "Which parts are in the order".

- The README reads "Nexperia 74HC165D, C5613, a 'Preferred' Extended part"
  `[repo hardware/boards/key-board-lh/README.md:82]`.
- The sheet field is `74HC165D,653` `[repo hardware/cluster/key-register/key-register.kicad_sch:402]`.
  `,653` is the reel suffix, so this is the same part today. It is still a
  second copy, in a second spelling, with no forbidden pattern to guard it
  (CLAUDE.md rule 1).
- The same README says, one line later, "The sheets are the source of every
  part number."
- Stock and Preferred status are also volatile, and the README does not date
  them.

**Fix:** "The parts are JLC Basic except the 74HC165 (Preferred Extended, no
Economic loading fee, as of 2026-09-27). Numbers: the sheets, or
`fab/key-board-lh-bom-jlc.csv`." Drop the MPN and LCSC number from the prose.

### K4-5 [low] The switches' "MPN" in the hand list is prose, not a part number

**Node:** `SW-LH1..5`, BOM row `SW1-n`,
`fab/key-board-lh-hand-assembly.csv`.

- The MPN field reads `"KS-33 Red (linear) - bought, BOM row SW1-n"`
  `[repo hardware/cluster/key-switch-network/key-switch-network.kicad_sch:499]`
  `[repo fab/key-board-lh-hand-assembly.csv]`.
- The manifest's Gateron drawing names an orderable code,
  `KS-33H10B050NN` ("Low Profile 2.0 Red … Black Bottom Housing")
  `[repo datasheets/MANIFEST.csv, Gateron KS-33 vendor drawing row, URL]`.
- The row says the switches were bought on Amazon `[repo hardware/cluster/bom.csv SW1-n]`,
  so which KS-33 revision is in hand (1.0 or 2.0) is not recorded.

**Fix:** Put the Gateron code of the switches actually bought in `MPN`, or
leave `MPN` empty and keep the sentence in `Note`. A reorder then gets the
same housing.

### K4-6 [low] The ordering section is not quite enough to place an order

**Node:** README "Ordering it — JLCPCB", `PCB-CLUSTER`, `J-CHAIN`,
`fab/key-board-lh-hand-assembly.csv`.

- **Order quantity is not stated.** Economic PCBA at 1.2 mm Green/Black takes
  2–30 boards `[datasheets/fab/JLCPCB-PCBA-CAPABILITIES.pdf, "PCB Specs for Economic PCB Assembly"]`.
  JLC's bare-board minimum is 5, of which 2 or more can be assembled
  `[from memory]`. `PCB-CLUSTER` qty 2 is one LH and one RH, which are two
  different designs, so each is a separate order with spares.
- **J-CHAIN's source is only "buy from Samtec or a distributor."**
  - JLC/LCSC C17202657 has stock 0
    `[web JLC API, keyword C17202657: stockCount 0, library "expand"]`. That
    agrees with the row.
  - A search found `SHF-106-01-L-D-SM` and other RA pin counts at
    DigiKey/Mouser, but not `SHF-106-01-L-D-RA` itself
    `[web WebSearch "SHF-106-01-L-D-RA" stock Digikey OR Mouser]`. Samtec
    direct is the only source not yet disproved.
  - The part is single-sourced. The row's note says so, and says the one
    stocked alternative is not a drop-in, which is correct. The order,
    though, cannot complete without a J-CHAIN in hand.
- **The hand list covers only the parts on the schematic.** The four
  `MECH-KB-SCREW`, the four standoffs (pressed by the plate vendor) and the
  `CBL-CHAIN` appear only in the README's prose steps.

**Fix:** Add a quantity line and "J-CHAIN: order from samtec.com (samples or
buy), lead time checked at order". Optionally, add the mechanical kit
(`MECH-KB-SCREW` ×4, `CBL-CHAIN` ×1) to the hand-assembly list as rows the
board draws on.

### K4-7 [advisory] `SW1-n`'s "placed exactly to BOM qty" is a coincidence of two different 2s

**Node:** `SW1-n`, `R-KEY-SER`, `C-KEY`; `check-netlist.py` instances.

- `check-netlist.py` counts each circuit netlist × `replicated` and does not
  read the boards' `board-netlist.yaml` `[repo tools/check-netlist.py check_global]`.
- `key-switch-network` is replicated 21, and each copy includes `SW1-n`
  `[repo hardware/cluster/key-switch-network/netlist.yaml:10]`. So the checker
  counts 21 switches placed against the row's 21 `[run: python3 tools/check-netlist.py --strict → 104 exact]`.
- But the 21 networks are 19 keys + 2 **spare-switch bits: "networks fitted,
  no cutouts"** `[repo config/key-layout.yaml:160]`. The row's 21 are 19 fitted
  + **2 loose spares** `[repo hardware/cluster/bom.csv SW1-n notes]`.
- The numbers agree, but for different reasons. If a spare bit becomes a key,
  or a spare switch is dropped, the check will report the wrong thing silently.
- For this board the count is right. It places 5 switches, 5+1 `R-KEY-PU`,
  5 `R-KEY-SER`, 5 `C-KEY`, 1 `U-KEYS`, 1 `C-DECOUPLE-165`, 1 `J-CHAIN` and
  5 `TP-CHAIN` `[repo board-netlist.yaml]`, and none of LH's spare bits is a
  spare-switch bit `[repo config/key-layout.yaml:137]`.

**Fix (after the freeze):** count switch footprints from the board netlists,
or mark the two spare-switch networks' `SW1-n` as not fitted.

### K4-8 [advisory] J-CHAIN's 0.65 mm drill against a 0.41 mm square tail leaves no margin at JLC's lower hole tolerance

**Node:** `J-CHAIN`, footprint `woody:IDC-Header_2x06_P1.27mm_Samtec_SHF_Horizontal`.

- The footprint's drill is 0.65 mm `[repo hardware/lib/woody.pretty/IDC-Header_2x06_P1.27mm_Samtec_SHF_Horizontal.kicad_mod pad 1]`.
- The tail is .016 [0.41] square `[datasheets/connectors/SAMTEC-SHF-1XX-01-X-D-XX-PRINT.pdf, sheet 1]`,
  so its diagonal is 0.41 × √2 = 0.580 mm `[calc]`.
- JLC's PTH tolerance is +0.13/−0.08 `[datasheets/fab/JLCPCB-PCB-CAPABILITIES.pdf, "Hole size tolerance"]`,
  so the smallest finished hole is 0.65 − 0.08 = 0.57 mm `[calc]`. That is
  under the diagonal.
- I did not find a recommended PCB hole in the banked print's text layer.

For K2/K3 to confirm: specify 0.7 mm, or cite Samtec's recommended hole.

### K4-9 [advisory] The `U-KEYS` row does not carry the fact that makes the vendor matter at 3.3 V

**Node:** `U-KEYS` (`mfr: multiple`), JLC substitution at order time.

- Nexperia's datasheet claims JESD8C (2.7–3.6 V) compliance
  `[datasheets/logic/74HC165-nexperia.pdf p.1]`. It is the fitted part, and
  it is well covered at 3.3 V.
- TI's datasheet gives no 3.3 V guarantee. The register already notes this
  (`config/figures.yaml` key-release-time `conservative_bound`, "If a TI
  SN74HC165 is the part fitted") `[repo config/figures.yaml:224]`.
- If C5613 is out of stock at order time, JLC's "alternative" picker can land
  a TI or other part, and nothing on the row says to prefer Nexperia or onsemi.

**Fix:** In the `U-KEYS` notes, add: "At 3.3 V prefer Nexperia (JESD8C) or
onsemi (3.0 V row); a TI SN74HC165 falls back to the conservative bound."

## Verified correct

- **LCSC numbers = MPN = BOM requirement**, each checked on the JLC part page
  and in the search API on 2026-09-27 `[web https://jlcpcb.com/partdetail/<C#>; JLC API]`:

  | Ref | LCSC | Part | Stock | JLC class | Row requirement |
  |---|---|---|---|---|---|
  | `U-KEYS` | C5613 | Nexperia 74HC165D,653, SOIC-16, 2–6 V | 335,541 | Extended, `preferredComponentFlag` true | 74HC165, SOIC-16 1.27 |
  | `C-DECOUPLE-165` | C49678 | YAGEO CC0805KRX7R9BB104, 100 nF 50 V X7R ±10 % 0805 | 18,078,416 | Basic | 100 nF X7R 0805 |
  | `C-KEY` | C53134 | Samsung CL21B473KBCNNNC, 47 nF 50 V X7R ±10 % 0805 | 204,454 | Basic | 47 nF X7R 0805 |
  | `R-KEY-SER` | C17408 | UNI-ROYAL 0805W8F1000T5E, 100 Ω ±1 % 125 mW 0805 | 9,587,039 | Basic | 100R 1 % 0805 |
  | `R-KEY-PU` (incl. `R-KEY-PU-FREE3`) | C17520 | UNI-ROYAL 0805W8F2201T5E, 2.2 kΩ ±1 % 0805 | 3,675,218 | Basic | 2k2 1 % 0805 |

- **The 74HC165 at 3.3 V.**
  - Supply is 2.0–6.0 V `[datasheets/logic/74HC165-nexperia.pdf p.1, p.6 Recommended operating conditions]`.
  - The 74HC165D is SO16 SOT109-1, body 3.9 mm `[ibid. p.2 Ordering information; §12 package outline]`. That matches `Package_SO:SOIC-16_3.9x9.9mm_P1.27mm`.
- **Footprints on the board match the sheets and the rows** `[run: parse of key-board-lh.kicad_pcb]`:
  - 0805 R/C on `B.Cu`, `smd`.
  - SOIC-16 on `B.Cu`.
  - 5 × `TestPoint_Pad_D1.0mm` on `B.Cu`, `exclude_from_bom`/`pos` (the `TP-CHAIN` package).
  - 4 × `MountingHole_2.2mm_M2`, `board_only`. They are NPTH in the drill file (T4 2.2, NonPlated) `[repo fab/key-board-lh.drl]`, which agrees with `MECH-KB-STANDOFF`'s "Board holes are NPTH".
  - The switch footprint's pads are identical to Gateron's banked footprint `[run: diff of pad lines vs datasheets/mechanical/GATERON-KS-33-SW_KS33_1u.kicad_mod]`.
- **`-bom-jlc.csv`** has JLC's four columns (Comment, Designator, Footprint, JLCPCB Part #) `[datasheets/fab/JLCPCB-KICAD-BOM-CPL-GUIDE.pdf, "The BOM"]`.
  - 18 designators = 5 `R-KEY-SER` + 6 `R-KEY-PU` + 5 `C-KEY` + 1 `C-DECOUPLE` + 1 `U-KEYS`, each once.
  - No switch, J-CHAIN, TP or hole in it.
- **`-cpl-jlc.csv`** has the columns Designator, Mid X, Mid Y, Layer, Rotation, in mm `[guide, "Step 5"]`.
  - It has the same 18 designators, all `Bottom`.
  - Its X/Y/rotation are identical to KiCad's `-pos.csv` `[repo fab/*.csv]`.
  - Its Y agrees with the `.kicad_pcb` placements (Y negated), e.g. `U-KEYS-LH` (150.5, 105.5, 90°).
- **`-hand-assembly.csv`** is J-CHAIN plus `SW-LH1..5`. The TPs (`Assembly none`) are rightly absent.
- **Sheet `Row` fields resolve to real rows.** `R-KEY-PU-FREE` is `Row R-KEY-PU`; no separate `R-KEY-PU-FREE` row exists, and none is needed.
- **Quantities.** These rows match the circuits' placements `[run: python3 tools/check-netlist.py --strict; own count over netlists × replicated]`:

  | Row | Qty | Basis |
  |---|---|---|
  | `U-KEYS` | 4 | ×4 |
  | `C-DECOUPLE-165` | 4 | |
  | `R-KEY-PU` | 24 | 21 + 3 free |
  | `R-KEY-SER` | 21 | |
  | `C-KEY` | 21 | |
  | `SW1-n` | 21 | see K4-7 |
  | `J-CHAIN` | 4 | = figure `chain-connectors`; the loom netlist places 4 |
  | `TP-CHAIN` | 10 | 5 per board × 2 |
  | `PCB-CLUSTER` | 2 | |
  | `CBL-CHAIN` | 2 | |
  | `MECH-KB-STANDOFF` | 8 | drc.echo "key-board standoffs" [4, 4] `[repo mechanical/drc.echo:56]` |
  | `MECH-KB-SCREW` | 8 | one per standoff |

- **`hardware/bom.csv` is current** `[run: python3 tools/merge-bom.py --check → 156 rows, 0 problems]`.
- **README fab claims:**
  - Economic PCBA is single-sided (SMT/THT), 0.8–1.6 mm.
  - At 1.2 mm it offers HASL (lead-free or leaded) only, in Green or Black `[datasheets/fab/JLCPCB-PCBA-CAPABILITIES.pdf]`.
  - Preferred Extended parts pay no Economic loading fee `[datasheets/fab/JLCPCB-PCBA-FAQ.pdf, Q7]`.
  - JLC adds fiducials `[ibid. Q12]`.
- **J-CHAIN sourcing claims in its row:** C17202657 = Samtec SHF-106-01-L-D-RA, stock 0 `[web JLC API]`. C42372552 = hanxia HX JN1.27-2x6 WZ H4.9, Extended, in stock `[web JLC part page]`.
