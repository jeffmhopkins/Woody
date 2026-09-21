# A12 — Datasheet coverage: what we know versus what we have merely asserted

**Agent A12, cold, 2026-09-21.** Slice: the cross-product between
`hardware/bom.csv` (135 rows) and `datasheets/` (75 banked files, 96 manifest
rows). I did not read `docs/review/**`. Provenance on every claim:
`[datasheet <file> p.N]`, `[repo <file>:<line>]`, `[calc]`.

**Method.** `tools/verify-datasheets.py` passes (75 verified, 21 blocked/not-fetched,
0 problems) `[repo tools/verify-datasheets.py]`. `pdftotext` and `pdfinfo` are **not
installed in this container**; I used `pymupdf` (present) for text and
`page.get_pixmap()` + visual reading for the drawings that have no text layer. Any
future script that shells out to `pdftotext` here gets nothing from *every*
document, not just the vector ones.

## Headline

1. **23 of 135 rows are cleanly covered; 10 more are covered with a caveat; 15
   partially; 13 named parts have nothing.** The other 74 are commodity passives
   with no MPN, where no datasheet can exist until a part is chosen.
2. **One outright package defect, unretrofittable:** `D-REVSHUNT` SS34 is
   specified `DO-214AC` and the banked datasheet says `SMC (DO-214AB)`.
3. **One live footprint contradiction between two corpus files:** `U-TVS-SPI` is
   `SOT-23-5` in `bom.csv` and `SOT-23-6` in `carrier.md`. The datasheet settles
   it: SOT23-5.
4. **The single biggest hole is not a passive — it is the ESP32-S3.** Two dev
   boards, every real-time timing argument and the whole pin map rest on a
   silicon datasheet that is not banked and has never had a manifest row, not
   even a `BLOCKED` one.
5. **`merge-manifests.py` under-reports the historical rows by three.** It
   matches part names with `==`, so three closed gaps are still printed as live.
6. **Seven banked documents carry their load-bearing numbers only as pictures.**
   Listed in §4, because the next script written against them will silently
   return nothing or — worse, for the Gateron sheet — return prose and no
   dimensions.

---

## Table 1 — every BOM row against the bank

Verdicts: **YES** right part and right package · **YES\*** right part, caveat in the
last column · **PARTIAL** the class, series or board is covered but not this exact
item · **NO** a named part with no document · **NO\*** a document exists and it
contradicts the row · **n/a** no MPN in the row, so nothing to bank yet.

| refdes | part | package the BOM asks for | covered? | document | is it the right document? |
|---|---|---|---|---|---|
| `SW1-n` | KS-33 Red (linear) | switch, plate mount | **YES** | mechanical/GATERON-KS-33-VENDOR-SPEC-DRAWING.pdf (+ -3D.step, 2 kicad_mod, ergogen .js) | Vendor spec for KS-33H10B050NN-Y24 'Low Profile 2.0 Red' = this row. p.6 carries the dimensioned drawing; **its dimensions are vector, not text** (p.6 text has only 0.2/0.4/1.7/3.0 - travel, not geometry). |
| `CAP1-n` | MT165-MX | keycap | **NO** | - | Live gap. Two manifest rows (MT165-MX keycap; MT165-MX vendor drawing) both BLOCKED. Nothing bounds Z stack above PLATE-TOP. |
| `U-MCU-RT` | ESP32-S3-Matrix | dev board, headers | **PARTIAL** | mechanical/WAVESHARE-ESP32-S3-MATRIX-SCHEMATIC.pdf + pinout/dimensions/function-block/pins.c | Board-level only. **The ESP32-S3 silicon datasheet is NOT banked**, and neither is the WS2812B-0807 fitted 64x on this board (schematic U1-U64, confirmed p.1). |
| `U-BREATH` | MPXV4006DP | case 1351-01, dual side ports, THT leads | **YES** | other-semi/MPXV4006DP.pdf + MPXV4006-AN1646.pdf | 'MPXV4006DP CASE 1351-01' verbatim on p.2 - matches this row's package cell exactly. |
| `U-ADC` | MCP3202-CI/SN | SOIC-8 (1.27mm pitch) | **YES** | other-semi/MCP3202-CI-SN.pdf | DS21034F. 8-pin SOIC covered p.1; I-grade -40..+85degC covered. The literal orderable 'MCP3202-CI/SN' does not appear - Microchip puts it in a separate product-ID block. |
| `U-IMU` | QMI8658C (onboard U-MCU-RT) | on dev board | **NO** | - | QMI8658C (QST). No datasheet anywhere in the bank, and no manifest row - not even a BLOCKED one. The only source is the dev-board schematic. |
| `U-KEYS` | 74HC165 | SOIC-16 (1.27mm pitch) | **YES** | other-semi/74HC165.pdf (TI SCLS116E) + -nexperia + -onsemi + -toshiba | TI p.1 orderable table: SN74HC165D / DR / DT = SOIC (D), 16-lead. Four independent vendors banked; onsemi is the one with the 3.0 V row. |
| `U-DISP` | T-Display-S3 AMOLED (base not Plus) | dev board, headers | **PARTIAL** | mechanical/LILYGO-T-DISPLAY-S3-AMOLED-SCHEMATIC.pdf + -3D.stp + -OUTLINE.dxf | Board-level. The AMOLED panel/driver (RM67162 class) has no document; nor does the ESP32-S3 on it. |
| `U-BUCK` | R-78E5.0-1.0 | SIP-3 THROUGH-HOLE | **YES** | discrete-and-power/R-78E5.0-1.0.pdf | RECOM R-78E-1.0 REV 9/2024. SIP3 11.6x8.5x10.4mm p.1; selection guide p.1 gives 8-28 V in / 93% @ min Vin / 85% @ max Vin for this exact part. |
| `LED-SIDE` | WS2815 (12V addressable) 60/m, 1m reel | flexible strip | **PARTIAL** | other-semi/WS2815.pdf (= mechanical/WS2815-worldsemi-datasheet.pdf) | The LED die is covered. **The strip assembly is not** - manifest row 'WS2815 LED strip' is BLOCKED, so LEDs/m, strip width and per-metre current have no document. |
| `U-DAC` | DAC8568CIPW | TSSOP-16 (0.65mm pitch) | **YES** | texas-instruments/DAC8568CIPW.pdf | TSSOP-16 covered p.1. Literal 'DAC8568CIPW' not in text; grade/temp suffix is in TI's separate orderable addendum. |
| `U-OPA-PITCH` | OPA2197 | SOIC-8 (1.27mm pitch) | **YES** | texas-instruments/OPA2197.pdf | SBOS736. Orderable table p.34: OPA2197IDR = SOIC (D) 8. |
| `U-OPA-GEN` | (none - OPA2197 used throughout) | n/a | **n/a** | - | qty 0, not-needed. |
| `R-PRECISION` | LT5400 1:1 quad (four equal 10k), MSOP-8 option | MSOP-8 MS8E (0.65mm pitch) WITH 1.88 x 1.68mm EXPOSED PAD | **YES*** | other-semi/LT5400.pdf (rev fa) | p.2 CONFIRMS both things this row depends on: 'MS8E PACKAGE 8-LEAD PLASTIC MSOP ... EXPOSED PAD (PIN 9) IS FLOATING', and Available Options 'LT5400-1  10k  10k  1:1'. The row currently sources the -1 option from [github]; it can now cite the datasheet. Caveat: rev fa predates LT5400-7, so -7 is not-in-document. |
| `J-CV` | PJ398SM (Thonkiconn) | THROUGH-HOLE | **YES** | connectors/PJ398SM-drawing.jpg + PJ398SM.kicad_mod | Thonk PJ398SM drawing: body 9 x 8.3mm, bushing D6 x 4.5mm thread, ~18mm behind panel, PCB layout 3.1/3.38/4.92 x 6.48. **Image only - no text layer at all.** |
| `SW-POWER` | SPST sub-miniature toggle, 6mm bushing | THROUGH-HOLE | **NO** | connectors/100SP1T2B3M2QEH.pdf is NOT this part | The banked E-Switch drawing is SPDT ON-NONE-ON with a 1/4-40 (6.35mm) bushing; this row wants SPST with a 6mm metric bushing. Panel hole differs (~6.4-6.5 + keyway vs 6.0). A document for the wrong part is not coverage. |
| `U-LOADSW` | LT1641-1CS8 + DPAK/SO-8 N-FET + sense R | SO-8 + DPAK or SO-8 FET | **PARTIAL** | discrete-and-power/LT1641.pdf (164112fc) + LT1641-DC1354A-demo-manual.pdf | The controller is covered to the page. **The N-FET and the sense resistor have no part number at all**, so no document can exist for them; R-ILIM is also 'open, value from E6'. |
| `J-UMBILICAL` | Neutrik etherCON D-series chassis (variant TBD) | panel mount | **YES*** | connectors/NE8FDP.pdf, NE8FDP-DATASHEET.pdf, NE8FDP.dxf, NE8FDV-DATASHEET.pdf, NE8FDV.kicad_mod, NEUTRIK-PG-DATA-CONNECTOR.pdf | Both candidate chassis variants are banked. Row still says 'variant TBD' - the documents can close it. NE8FDP.pdf has **zero text layer**; the 31mm flange, 26mm width, >=D24 cutout and 19+/-0.1 screw pitch are readable only by rendering. |
| `J-UMBILICAL-CABLE` | Neutrik NE8MC or NE8MX etherCON cable shell (variant TBD) | cable | **YES*** | connectors/NE8MC.pdf, NE8MC-DATASHEET.pdf, NE8MX.pdf, NE8MX6.pdf | Both candidates banked. NE8MC-DATASHEET p.1 adds a constraint nothing in the corpus carries: the shell ships protection elements for **cable diameter up to 5mm or 8mm** - that bounds CABLE-UMB. |
| `PANEL` | 2mm aluminium, 10HP x 3U (50.50 x 128.5mm) | n/a | **YES** | mechanical/EURORACK-3U-3HP-PANEL-apfaudio-pmod-r3.1.kicad_pcb + EURORACK-3U-PANEL-HP-TABLE-make_blanks.py | Doepfer 3U/HP geometry banked as executable data rather than a PDF. |
| `PLATE-TOP` | 1.20mm aluminium | n/a | **n/a** | - | Sheet stock; thickness is a figures.yaml figure (plate-thickness 1.20mm), not a datasheet. |
| `BODY-OAK` | TBD | n/a | **n/a** | - | TBD, material. |
| `SIDE-ACRYLIC` | TBD | n/a | **n/a** | - | TBD, material. |
| `BENCH` | n/a | n/a | **n/a** | - | Not a part. |
| `U-REF-BREATH` | REF5050AIDR | SOIC-8 (1.27mm pitch) | **YES** | texas-instruments/REF5050.pdf | SBOS410. p.3 family table lists REF5050AID / REF5050AIDGK; SOIC-8 'D'. (Grade A vs no-suffix is the open ref5050-grade figure, not a coverage gap.) |
| `U-BUF` | OPA2197IDR | SOIC-8 (1.27mm pitch) | **YES** | texas-instruments/OPA2197.pdf | OPA2197IDR = SOIC (D) 8, p.34. |
| `U-DIFFRX` | INA828IDR | SOIC-8 (1.27mm pitch) | **YES** | texas-instruments/INA828IDR.pdf | p.32 orderable: INA828ID / INA828IDR, SOIC (D) 8. |
| `J-USB` | USB-C receptacle | n/a | **n/a** | - | not-needed. |
| `U-ESD-USB` | USBLC6-2SC6 | n/a | **n/a** | - | not-needed. |
| `SW-BOOT` | TBD | n/a | **n/a** | - | not-needed. |
| `C-BULK-DISP` | TBD | 1206 / electrolytic THT | **n/a** | - | TBD/open, no MPN. |
| `TUBE` | silicone tube + dead-volume trap | n/a | **n/a** | - | Open, material. |
| `U-LVLSHIFT` | 74AHCT125 | SOIC-14 (1.27mm pitch) | **YES** | texas-instruments/SN74AHCT125.pdf | p.1 orderable: SN74AHCT125D / DR = SOIC (D) 14. |
| `U-LVL-MOD` | 74AHCT125 | SOIC-14 (1.27mm pitch) | **YES** | texas-instruments/SN74AHCT125.pdf | Same document. |
| `J-PWR-EURO` | 16-pin shrouded keyed IDC header | THROUGH-HOLE | **YES*** | connectors/WR-BHD-61201621621.pdf + 3M-303-SERIES-BOXED-HEADER.pdf | 16-pin (2x8) shrouded is in both. NOTE from the manifest: 3M's 303 table has no 12-pin entry, so J-CHAIN's 2x6 must come from the Wurth sheet. |
| `D-REVPOL` | 1N5817 | DO-41 THROUGH-HOLE | **YES** | discrete-and-power/1N5817.pdf | Diodes Inc. p.1: 'DO-41 Plastic' - matches this row's package cell. |
| `U-REG-DAC` | LM317LZ | TO-92 THROUGH-HOLE | **YES*** | texas-instruments/LM317LZ.pdf | The document is the LM317L family sheet: TO-92 (3) 4.30 x 4.30mm on p.1. The literal orderable 'LM317LZ' does not appear in the banked text - the file name is more specific than the document. |
| `R-REG-SET` | 150R / 475R 0.1% metal film | 0805 or through-hole | **PARTIAL** | discrete-and-power/ERA-3A-thin-film-0p1pct.pdf | **Size mismatch inside the series.** p.1: ERA-3A = 0603 0.1W; the 0805 0.125W part is ERA-6A. This row says '0805 or through-hole'. The document covers the family, so the fix is to name ERA6A, not to fetch anything. |
| `C-REG-ADJ` | 10uF / 1uF ceramic or tantalum | 0805 / 1206 | **n/a** | - | Generic ceramic/tantalum, no MPN. |
| `FB-IN` | Laird MI1206K601R-10 (600R @ 100MHz, 1206, 1.5A) | 1206 or 1210 | **YES** | discrete-and-power/MI1206K601R-10-ferrite-bead.pdf (+ HI1206N601R-10 as second source) | Laird drawing rev E. **169 characters of text on the whole sheet** - Z/R/XL axis labels and the bias legend (0/250/500/1000/1500mA) and nothing else. Every number this row quotes (600R nom, 0.080R DCR, 1500mA, 3.20x1.60x1.10) is in the picture. |
| `R-OUT-PROT` | 1k 1%, >=500mW | 1206 (3.2 x 1.6mm) | **n/a** | - | Commodity passive, no MPN in the row. No datasheet is possible until a part is chosen; the class specs (X7R/C0G, tolerance, voltage) are the only sourceable thing. |
| `C-DECOUPLE` | 100nF X7R 50V | 0805 (2.0 x 1.25mm) | **n/a** | - | Commodity passive, no MPN in the row. No datasheet is possible until a part is chosen; the class specs (X7R/C0G, tolerance, voltage) are the only sourceable thing. |
| `C-DECOUPLE-165` | 100nF X7R | 0805 (2.0 x 1.25mm) | **n/a** | - | Commodity passive, no MPN in the row. No datasheet is possible until a part is chosen; the class specs (X7R/C0G, tolerance, voltage) are the only sourceable thing. |
| `C-AA-ADC` | 47nF C0G/NP0 | 0805 (2.0 x 1.25mm) | **n/a** | - | Commodity passive, no MPN in the row. No datasheet is possible until a part is chosen; the class specs (X7R/C0G, tolerance, voltage) are the only sourceable thing. |
| `R-ADCDIV` | 10k / 15k 1% metal film | 0805 (2.0 x 1.25mm) | **n/a** | - | Commodity passive, no MPN in the row. No datasheet is possible until a part is chosen; the class specs (X7R/C0G, tolerance, voltage) are the only sourceable thing. |
| `C-STRIP-BULK` | 470-1000uF electrolytic, 16V | THROUGH-HOLE radial | **n/a** | - | Generic electrolytic. |
| `L-BUCK-IN` | 10-47uH power inductor, >=1A | SMD shielded or THT | **NO** | - | 10-47uH >=1A inductor, no MPN. It is one of the two inputs to carrier.md's input-LC damping [calc]; the other (ESR) is [from memory]. |
| `R-SPI-PULL` | 10k 1% | 0805 (2.0 x 1.25mm) | **n/a** | - | Commodity passive, no MPN in the row. No datasheet is possible until a part is chosen; the class specs (X7R/C0G, tolerance, voltage) are the only sourceable thing. |
| `R-SPI-SER` | 100R 1% | 0805 (2.0 x 1.25mm) | **n/a** | - | Commodity passive, no MPN in the row. No datasheet is possible until a part is chosen; the class specs (X7R/C0G, tolerance, voltage) are the only sourceable thing. |
| `R-OPAMP-IN` | 1k 1% | 0805 (2.0 x 1.25mm) | **n/a** | - | Commodity passive, no MPN in the row. No datasheet is possible until a part is chosen; the class specs (X7R/C0G, tolerance, voltage) are the only sourceable thing. |
| `D-JACK-CLAMP` | BAV99 | SOT-23 | **YES** | discrete-and-power/BAV99.pdf | Vishay BAV99, SOT-23. |
| `MECH-PTFE` | Porous hydrophobic PTFE plug | press-fit into the tube | **NO** | - | Porous PTFE plug, no MPN - and it is in the breath path. |
| `MECH-COAT` | Acrylic conformal coating | aerosol or brush | **n/a** | - | Consumable. |
| `MECH-GNDBOND` | Ring terminal + M3 hardware | THROUGH-HOLE | **n/a** | - | Hardware. |
| `MECH-WINDOW` | Acrylic window + thin diffuser | ~22mm sq, laser cut | **n/a** | - | Cut part. |
| `CABLE-UMB` | Cat5e STP patch lead, STRANDED, ~2m | RJ45 both ends | **PARTIAL** | connectors/NE8MC-DATASHEET.pdf bounds it | No cable datasheet; but the etherCON shell's 5mm/8mm cable-diameter elements (NE8MC-DATASHEET p.1) are the binding constraint and are now banked. |
| `MECH-MOUTH` | Tube end + small nib (lip locator) | turned or printed, removable | **n/a** | - | Made part. |
| `R-GAIN-INAMP` | 42.2k 0.1% thin film | 0805 | **PARTIAL** | discrete-and-power/ERA-3A-thin-film-0p1pct.pdf | 0.1% thin film class covered; same 0603-vs-0805 naming issue as R-REG-SET. |
| `R-BIAS-INAMP` | 1M 1% | 0805 | **n/a** | - | Commodity passive, no MPN in the row. No datasheet is possible until a part is chosen; the class specs (X7R/C0G, tolerance, voltage) are the only sourceable thing. |
| `R-SER-BREATH` | 10k 0.1% thin film | 0805 | **PARTIAL** | discrete-and-power/ERA-3A-thin-film-0p1pct.pdf | Same. |
| `C-FILT-BREATH` | 15nF C0G (diff) + 1.5nF C0G (cm x2) | 0805 | **n/a** | - | Commodity passive, no MPN in the row. No datasheet is possible until a part is chosen; the class specs (X7R/C0G, tolerance, voltage) are the only sourceable thing. |
| `C-OUT-BREATH` | 330nF film | 1206 or THT | **n/a** | - | Commodity passive, no MPN in the row. No datasheet is possible until a part is chosen; the class specs (X7R/C0G, tolerance, voltage) are the only sourceable thing. |
| `R-ILIM` | Sense resistor, value from E6 | 0805 or 1206 | **NO** | - | Open: 'value from E6'. No part, and the LT1641 fold-back law depends on it. |
| `R-SER-BREATH-INST` | 1k 1%, 1206 >=250mW | 1206 (3.2 x 1.6mm) | **n/a** | - | Commodity passive, no MPN in the row. No datasheet is possible until a part is chosen; the class specs (X7R/C0G, tolerance, voltage) are the only sourceable thing. |
| `C-FILT-MOD` | 82nF C0G/NP0 | 1210 or film - VERIFY | **n/a** | - | Commodity passive, no MPN in the row. No datasheet is possible until a part is chosen; the class specs (X7R/C0G, tolerance, voltage) are the only sourceable thing. |
| `R-MODGAIN` | 10k / 30k 1% metal film | 0805 (2.0 x 1.25mm) | **n/a** | - | Commodity passive, no MPN in the row. No datasheet is possible until a part is chosen; the class specs (X7R/C0G, tolerance, voltage) are the only sourceable thing. |
| `R-CLR-PU` | 10k 1% | 0805 (2.0 x 1.25mm) | **n/a** | - | Commodity passive, no MPN in the row. No datasheet is possible until a part is chosen; the class specs (X7R/C0G, tolerance, voltage) are the only sourceable thing. |
| `D-USBOR` | 1N5817 or SS14 | DO-41 THROUGH-HOLE | **YES*** | discrete-and-power/1N5817.pdf + SS14.pdf | Both options banked. **The package cell is wrong for one of them**: SS14 is SMA / DO-214AC (SS14.pdf p.1 'Case: SMA (DO-214AC)'), not the 'DO-41 THROUGH-HOLE' this row states. |
| `PCB-CARRIER` | 2-layer PCB - real-time carrier | ~100 x 45mm, 1.6mm | **n/a** | - | Fabricated. |
| `PCB-MODULE` | 2-layer PCB - 10HP CV interface | ~45 x 110mm, 1.6mm | **n/a** | - | Fabricated. |
| `HDR-DEV` | 2.54mm female header strip - machined or dual-wipe | THROUGH-HOLE | **PARTIAL** | connectors/TE-IDC-SOCKET-CATALOG-82012.pdf | Machined/dual-wipe SIP socket strip is not this catalogue; no exact document. |
| `WIRE-LOOM` | Ribbon, ground per signal - chained cluster to cluster | n/a | **PARTIAL** | connectors/TE-IDC-SOCKET-CATALOG-82012.pdf | Ribbon/IDC covered generically. |
| `C-BUCK-IN` | 100uF 25V electrolytic | THROUGH-HOLE radial | **NO** | - | '100uF 25V electrolytic' - the damping result explicitly depends on this part having real ESR, and no part is named. |
| `C-DECOUPLE-CARRIER` | 100nF X7R | 0805 (2.0 x 1.25mm) | **n/a** | - | Commodity passive, no MPN in the row. No datasheet is possible until a part is chosen; the class specs (X7R/C0G, tolerance, voltage) are the only sourceable thing. |
| `C-REF-OUT` | 10uF X7R | 1206 | **n/a** | - | Commodity passive, no MPN in the row. No datasheet is possible until a part is chosen; the class specs (X7R/C0G, tolerance, voltage) are the only sourceable thing. |
| `C-BULK-RAIL` | 100uF (+12V) / 47uF (-12V, +5V) 25V electrolytic | THROUGH-HOLE radial | **n/a** | - | Generic electrolytic. |
| `SKT-BREATH` | Machined SIP socket strip 2.54mm | THROUGH-HOLE | **NO** | - | Machined SIP socket strip - no document, no manifest row. |
| `LED-PANEL` | 3mm LED - diffused | THROUGH-HOLE | **NO** | - | 3mm diffused LED, no MPN. R-LED-PANEL's 2k2 depends on a V_f nobody has sourced. |
| `R-LED-PANEL` | 2k2 1% | 0805 (2.0 x 1.25mm) | **n/a** | - | Commodity passive, no MPN in the row. No datasheet is possible until a part is chosen; the class specs (X7R/C0G, tolerance, voltage) are the only sourceable thing. |
| `POT-RESP` | 50k linear, 9mm vertical, centre detent | PCB mount | **YES*** | connectors/RV09AF-40.pdf + R0904N.pdf + R0904N-thonk.pdf | 9mm vertical pots covered by two vendors. **The centre-detent variant is not shown to exist in either document** - that part of the row is unsourced. |
| `R-RESP` | 15k 1% | 0805 (2.0 x 1.25mm) | **n/a** | - | Commodity passive, no MPN in the row. No datasheet is possible until a part is chosen; the class specs (X7R/C0G, tolerance, voltage) are the only sourceable thing. |
| `D-RESP` | 1N4148 x2, antiparallel | SOD-123 or SOD-323 | **YES*** | discrete-and-power/1N4148W.pdf (Vishay, SOD-123) + 1N4148W-DIOTEC.pdf (SOD-123F) + 1N4148.pdf (DO-35) | Three documents, three packages. The row says '1N4148 x2' but the package cell says SOD-123/SOD-323, so the part named and the package named are different parts. The DO-35 1N4148.pdf is the trap: right number, wrong body. |
| `U-RESP` | OPA2197IDR | SOIC-8 | **YES** | texas-instruments/OPA2197.pdf | Same part as U-BUF. |
| `KNOB-BREATH` | Knob to match the pot shaft - 14mm MAX diameter | n/a | **NO** | - | No MPN; the 14mm ceiling is a [calc] from panel width, not a vendor figure. |
| `SW-THUMB` | KS-33 lighter variant - TBD at M1 | switch, plate mount | **PARTIAL** | mechanical/GATERON-KS-33-VENDOR-SPEC-DRAWING.pdf | The banked spec is the 50+/-15gf Red. A 'lighter variant' is by definition a different item code with no document. |
| `MECH-UBOLT` | U-bolt + backing washer plate + nylocs | THROUGH-HOLE | **n/a** | - | Hardware. |
| `MECH-BACKPLATE` | TBD - aluminium or ply | n/a | **n/a** | - | TBD. |
| `PLATE-THUMB` | 1.20mm aluminium | n/a | **n/a** | - | Sheet stock. |
| `MECH-THUMBREST` | TBD | n/a | **n/a** | - | TBD. |
| `R-KEY-PU` | 2k2 1% | 0805 (2.0 x 1.25mm) | **n/a** | - | Commodity passive, no MPN in the row. No datasheet is possible until a part is chosen; the class specs (X7R/C0G, tolerance, voltage) are the only sourceable thing. |
| `R-KEY-SER` | 100R 1% | 0805 (2.0 x 1.25mm) | **n/a** | - | Commodity passive, no MPN in the row. No datasheet is possible until a part is chosen; the class specs (X7R/C0G, tolerance, voltage) are the only sourceable thing. |
| `C-KEY` | 47nF X7R | 0805 (2.0 x 1.25mm) | **n/a** | - | Commodity passive, no MPN in the row. No datasheet is possible until a part is chosen; the class specs (X7R/C0G, tolerance, voltage) are the only sourceable thing. |
| `J-CHAIN` | 2x6 2.54mm IDC boxed header, keyed | THROUGH-HOLE, shrouded | **YES*** | connectors/WR-BHD-61201621621.pdf | 2x6 shrouded keyed. Wurth is the source - 3M's 303 series has no 12-pin entry. |
| `R-CHAIN-SER` | 100R 1% | 0805 (2.0 x 1.25mm) | **n/a** | - | Commodity passive, no MPN in the row. No datasheet is possible until a part is chosen; the class specs (X7R/C0G, tolerance, voltage) are the only sourceable thing. |
| `U-TVS-CHAIN` | 4-channel TVS array | SOT-23-6 | **NO** | - | No part chosen. Package cell SOT-23-6 is a wish, not a part. |
| `F-CHAIN` | 100mA polyfuse | 1206 | **YES*** | discrete-and-power/MF-PSMF010X-polyfuse.pdf | Document is right, **this row's package cell is wrong**: p.1 'Compact design to save board space - 0805 footprint' and p.3 'PSMF = 0805 Surface Mount'. The row still says 1206. Its own notes already say so - the column was never changed. |
| `HDR-SERVICE` | 2x3 2.54mm pin header | THROUGH-HOLE | **YES** | connectors/3M-303-SERIES-BOXED-HEADER.pdf | 2x3 = 6 pin, 15.4mm, in the 3M length table. |
| `MECH-SERVICECOVER` | Screwed cover plate ~12 x 40mm + 2x M2 | n/a | **n/a** | - | Made part. |
| `MECH-FASTENER` | M3 socket cap screw + threaded insert or tapped plate boss | THROUGH-HOLE | **n/a** | - | Hardware. |
| `ENDCAP-MOUTH` | TBD - acrylic sheet, same stock as SIDE-ACRYLIC | flat part | **n/a** | - | Cut part. |
| `ENDCAP-TAIL` | TBD - oak, same stock as BODY-OAK | flat part | **n/a** | - | Cut part. |
| `U-TVS-SPI` | SP0504BAHT or equivalent 4-channel 5V array | SOT-23-5 (0.95mm pitch) | **YES** | discrete-and-power/SP0504BAHT.pdf | Ordering Information p.1, read by rendering: **SP0504BAHTG, CH 4, SOT23-5**. bom.csv is right; carrier.md:847 says SOT-23-6 and is wrong. |
| `D-TVS-BREATH` | PESD12VS1UB or equivalent 12V-standoff ESD diode | SOD-323 | **NO** | - | PESD12VS1UB named in the row, no document, no manifest row. 12V-standoff SOD-323 on the breath line is unverified. |
| `D-TVS-PWR` | SMAJ15A | DO-214AC | **YES** | discrete-and-power/SMAJ15A.pdf | Bourns SMAJ series p.1/p.3: SMA / DO-214AC. Matches the row. |
| `U-TVS-MODULE` | Same three groups, module end of the etherCON | as above | **PARTIAL** | - | 'Same three groups' - inherits SP0504BAHT + SMAJ15A + the unbanked PESD12VS1UB. |
| `D-REVSHUNT` | SS34 | DO-214AC | **NO*** | discrete-and-power/SS34.pdf CONTRADICTS the row | Vishay SS34 p.1: 'Case: SMC (DO-214AB)', repeated p.3 in the dimension table. **This row says DO-214AC (SMA).** There is no DO-214AC SS34. Either the footprint or the part number has to change - and it is unretrofittable protection on the +12V pin. |
| `ADH-WOOD` | PVA wood glue (Titebond II/III class) | n/a | **n/a** | - | Consumable. |
| `ADH-RTV` | RTV silicone - ALKOXY (alcohol) neutral cure, electronics-safe | n/a | **n/a** | - | Consumable - the alkoxy requirement is a chemistry constraint, not a datasheet. |
| `TRIM-GAIN` | 200R multiturn cermet | THROUGH-HOLE | **n/a** | - | Generic cermet. |
| `TRIM-OFFSET` | 10k multiturn cermet | THROUGH-HOLE | **n/a** | - | Generic cermet. |
| `C-FB-PITCH` | 2.2nF C0G/NP0 | 0805 (2.0 x 1.25mm) | **n/a** | - | Commodity passive, no MPN in the row. No datasheet is possible until a part is chosen; the class specs (X7R/C0G, tolerance, voltage) are the only sourceable thing. |
| `TRIM-BREATH-ZERO` | 10k multiturn cermet + divider from the LM317 5.21V rail | THROUGH-HOLE | **n/a** | - | Generic cermet. |
| `PCB-CLUSTER` | 2-layer PCB - key cluster board | small, 1.6mm | **n/a** | - | Fabricated. |
| `LK-SER` | 3-pad solder link | 0805-ish pad trio | **n/a** | - | Solder link. |
| `R-SER-TERM` | 10k 0805 | 0805 (2.0 x 1.25mm) | **n/a** | - | Commodity passive, no MPN in the row. No datasheet is possible until a part is chosen; the class specs (X7R/C0G, tolerance, voltage) are the only sourceable thing. |
| `R-LED-SER` | 330R 1% | 0805 (2.0 x 1.25mm) | **n/a** | - | Commodity passive, no MPN in the row. No datasheet is possible until a part is chosen; the class specs (X7R/C0G, tolerance, voltage) are the only sourceable thing. |
| `C-AA-PITCH` | 10nF C0G/NP0 | 0805 (2.0 x 1.25mm) | **n/a** | - | Commodity passive, no MPN in the row. No datasheet is possible until a part is chosen; the class specs (X7R/C0G, tolerance, voltage) are the only sourceable thing. |
| `C-TIMER-LOADSW` | 10uF low-leakage, 16V or better | THROUGH-HOLE radial or 1210 ceramic | **n/a** | - | Commodity passive, no MPN in the row. No datasheet is possible until a part is chosen; the class specs (X7R/C0G, tolerance, voltage) are the only sourceable thing. |
| `C-GATE-LOADSW` | 82nF C0G/NP0 or film, 50V | 0805 or 1206 | **n/a** | - | Commodity passive, no MPN in the row. No datasheet is possible until a part is chosen; the class specs (X7R/C0G, tolerance, voltage) are the only sourceable thing. |
| `R-FB-HI` | 35.7k 1% thin film | 0805 (2.0 x 1.25mm) | **PARTIAL** | discrete-and-power/ERA-3A-thin-film-0p1pct.pdf | 1% thin film 0805 = ERA6A grade; value itself is set from LT1641.pdf. |
| `R-FB-LO` | 5.11k 1% thin film | 0805 (2.0 x 1.25mm) | **PARTIAL** | discrete-and-power/ERA-3A-thin-film-0p1pct.pdf | Same. |
| `R-GATE-SER` | 10R 5% | 0805 (2.0 x 1.25mm) | **n/a** | - | Commodity passive, no MPN in the row. No datasheet is possible until a part is chosen; the class specs (X7R/C0G, tolerance, voltage) are the only sourceable thing. |
| `R-GATE-COMP` | 1k 5% | 0805 (2.0 x 1.25mm) | **n/a** | - | Commodity passive, no MPN in the row. No datasheet is possible until a part is chosen; the class specs (X7R/C0G, tolerance, voltage) are the only sourceable thing. |
| `D-CLAMP-BREATH` | BAV99 | SOT-23 | **n/a** | - | Commodity passive, no MPN in the row. No datasheet is possible until a part is chosen; the class specs (X7R/C0G, tolerance, voltage) are the only sourceable thing. |
| `R-TRIM-RANGE` | Range-setting resistors for the two module trimmers | 0805 (2.0 x 1.25mm) | **n/a** | - | Commodity passive, no MPN in the row. No datasheet is possible until a part is chosen; the class specs (X7R/C0G, tolerance, voltage) are the only sourceable thing. |
| `C-FILT-PITCH` | 10nF C0G/NP0 | 0805 (2.0 x 1.25mm) | **n/a** | - | Commodity passive, no MPN in the row. No datasheet is possible until a part is chosen; the class specs (X7R/C0G, tolerance, voltage) are the only sourceable thing. |
| `R-BIAS-DAC` | 100k 1% | 0805 (2.0 x 1.25mm) | **n/a** | - | Commodity passive, no MPN in the row. No datasheet is possible until a part is chosen; the class specs (X7R/C0G, tolerance, voltage) are the only sourceable thing. |
| `R-LDAC` | 10k 1% | 0805 (2.0 x 1.25mm) | **n/a** | - | Commodity passive, no MPN in the row. No datasheet is possible until a part is chosen; the class specs (X7R/C0G, tolerance, voltage) are the only sourceable thing. |
| `R-ISO-REF` | 10R 1% | 0805 (2.0 x 1.25mm) | **n/a** | - | Commodity passive, no MPN in the row. No datasheet is possible until a part is chosen; the class specs (X7R/C0G, tolerance, voltage) are the only sourceable thing. |
| `U-MCU-SPARE` | Spare ESP32-S3-Matrix + spare T-Display-S3 AMOLED | n/a | **PARTIAL** | as U-MCU-RT and U-DISP | Spares of the same two boards. |
| `POT-GAIN` | 50k, taper TBD at E10 | THROUGH-HOLE 9mm vertical | **YES** | connectors/RV09AF-40.pdf | Taiwan Alpha RV09 9mm vertical - this row's named manufacturer. |
| `POT-OFFSET` | 10k linear | THROUGH-HOLE 9mm vertical | **YES** | connectors/RV09AF-40.pdf | Same. |
| `R-GAIN-FLOOR` | 7.15k 1% | 0805 (2.0 x 1.25mm) | **n/a** | - | Commodity passive, no MPN in the row. No datasheet is possible until a part is chosen; the class specs (X7R/C0G, tolerance, voltage) are the only sourceable thing. |
| `R-BREATH-SUM` | 10k / 40.2k 1% | 0805 (2.0 x 1.25mm) | **n/a** | - | Commodity passive, no MPN in the row. No datasheet is possible until a part is chosen; the class specs (X7R/C0G, tolerance, voltage) are the only sourceable thing. |
| `R-BREATH-OFF` | 21.0k / 95.3k 1% | 0805 (2.0 x 1.25mm) | **n/a** | - | Commodity passive, no MPN in the row. No datasheet is possible until a part is chosen; the class specs (X7R/C0G, tolerance, voltage) are the only sourceable thing. |
---

## Table 2 — every unsourced claim, against the bank

I grepped the whole design corpus for `[from memory]` (15 instances), `[web…]` (3),
`[calc]` (38) and for load-bearing numbers carrying no marker at all. The
`[calc]` instances are arithmetic on values sourced elsewhere and are not
re-listed unless an *input* is unsourced. Outcomes: **CONFIRMED** /
**CONTRADICTED** / **STILL UNSOURCEABLE**.

| # | claim | where | outcome | what the document says | marker it should carry |
|---|---|---|---|---|---|
| 1 | "FSPI IO_MUX pins are GPIO9–14" | `[repo hardware/controller/carrier.md:655]` | **CONFIRMED, but by a document that is not banked** | Espressif ESP32-S3 datasheet v2.2, IO MUX pin-function table p.21: GPIO9 `FSPIHD`, GPIO10 `FSPICS0`, GPIO11 `FSPID`, GPIO12 `FSPICLK`, GPIO13 `FSPIQ`, GPIO14 `FSPIWP`. I read this off a copy sitting in an agent scratchpad (`esp32s3.pdf`, 87 pp) — **it is fetchable and it is not in `datasheets/`** | `[datasheet esp32-s3 v2.2 p.21]` once banked; until then it must stay `[from memory]` |
| 2 | "load regulation ~0.3 % per 100 mA" → 25.8 mA moves the ADC reference 0.077 %, 3.2 LSB | `[repo hardware/controller/carrier.md:394]`, repeated `[repo hardware/controller/carrier.md:497]` | **CONFIRMED as to which part, and the worst case is ~1.7× worse than stated** | The dev board's 3V3 LDO is `U49 ME6217C33M5G` `[datasheet WAVESHARE-ESP32-S3-MATRIX-SCHEMATIC.pdf p.1]`, and its Load Regulation is **ΔVOUT 10 mV typ / 50 mV max over 1 mA ≤ IOUT ≤ 300 mA** `[datasheet ME6217C33M5G.pdf p.4]`. `[calc]` pro-rata over the 299 mA span, a 25.8 mA step is 0.86 mV typ / **4.31 mV max** = 0.026 % / **0.131 %** of 3.3 V = 1.1 LSB typ / **5.4 LSB max** of 4096. The page's 3.2 LSB is between them, and the sentence "still fine, and no longer negligible" survives — but the bound is 5.4 LSB, not 3.2 | `[datasheet ME6217C33M5G p.4]` + `[calc]`, stating the pro-rata assumption (the datasheet bounds only the endpoint difference) |
| 3 | "400 µA against a family-typical ±2 mA" input clamp | `[repo hardware/controller/carrier.md:347]` | **CONTRADICTED — the spec does not exist for this part** | MCP3202 Absolute Maximum Ratings `[datasheet MCP3202-CI-SN.pdf p.2]` give **"All Inputs and Outputs w.r.t. VSS … −0.6 V to VDD + 0.6 V"** and **no input clamp current at any value**. The whole ≥10 kΩ argument is built against a number the document does not contain; worse, the abs-max as written is a *voltage* limit, which 4.7 V on a pin with VDD ≈ 0 V violates regardless of current | delete the `±2 mA` comparison or re-derive it against the voltage limit; the datasheet cannot support the present form |
| 4 | MCP3202 "clock limit `[from memory]`", used as 0.9 MHz in the loop budget | `[repo hardware/controller/carrier.md:836]`, `[repo hardware/controller/carrier.md:648]` | **CONFIRMED, with the same shape of caveat as the 74HC165** | Timing table `[datasheet MCP3202-CI-SN.pdf p.3]`: fCLK max **1.8 MHz at VDD = 5 V**, **0.9 MHz at VDD = 2.7 V**. **There is no 3.3 V row.** The page runs 3.3 V at 0.9 MHz, i.e. it takes the 2.7 V row conservatively — correct, and it should say so rather than leaving it as memory | `[datasheet MCP3202 DS21034F p.3 — 2.7 V row, no 3.3 V row published]` |
| 5 | "Gate count depends on `BI`" … `BI` `[from memory]` | `[repo hardware/controller/carrier.md:848]` | **CONFIRMED — and the marker is stale against its own file** | The same document already resolves it at `[repo hardware/controller/carrier.md:716-718]` and again at `:860` ("verified against the datasheet 2026-09-21"): the recommended application circuit ties L1 pin 6 `BI` to pin 5 `GND` `[datasheet WS2815.pdf p.4, "Typical application circuit / 1. Recommended application circuit"]`. Two gates stay spare. Only the §8 table row still says `[from memory]` | `[datasheet WS2815.pdf p.4]` |
| 6 | "capped around 40 MHz rather than 80" (GPIO matrix vs IO_MUX) | `[repo hardware/controller/carrier.md:658]` | **STILL UNSOURCEABLE** | Not a datasheet parameter — it lives in the ESP32-S3 *Technical Reference Manual*, chapter "IO MUX and GPIO Matrix", which the datasheet only cross-references `[datasheet esp32-s3 v2.2 p.18, p.25]`. No TRM is banked or has a manifest row. The page already says it is irrelevant at 2 MHz | keep `[from memory]`, or bank the TRM |
| 7 | "GPIO1/GPIO2 are high-impedance for the bootloader window (order 100–300 ms)" | `[repo hardware/controller/carrier.md:686]` | **STILL UNSOURCEABLE** | ROM-bootloader timing is not in the ESP32-S3 datasheet. This one matters: it is the justification for `R-LED-PD`, which "cannot be added later" | keep `[from memory]`; a scope trace at E1 settles it, not a fetch |
| 8 | "ESR of a 100 µF / 25 V radial ≈ 0.5–1 Ω" → Q ≈ 0.5–0.9, no peaking | `[repo hardware/controller/carrier.md:131]` | **STILL UNSOURCEABLE, and structurally so** | `C-BUCK-IN` names no manufacturer or part, so no document can exist. The page itself flags the exposure ("This result depends on `C-BUCK-IN` being an electrolytic with real ESR"). `L-BUCK-IN` is the same: "10–47 µH ≥1 A", no MPN | unchanged until a part is chosen — this is a BOM gap wearing a provenance marker |
| 9 | "WS2815 strips (~10 mm wide each)" | `[repo hardware/controller/carrier.md:902]` | **STILL UNSOURCEABLE** | The banked WS2815 document is the 5050 LED, not the strip. Strip width is an assembler's dimension and the assembler row is `BLOCKED` | keep `[from memory]`; it feeds the 45 mm carrier / side-channel conflict |
| 10 | "The 97 mm above is built from `[from memory]` component envelopes — the Neutrik drawing, the Thonkiconn panel dimension and the pot bushing were all behind a blocked proxy" | `[repo docs/decisions/0004-cv-interface-module.md:770]` | **CONFIRMED for two of the three inputs — this sentence is now out of date** | etherCON: flange **31 [1.22] mm tall × 26 [1.02] wide**, panel cutout **≥Ø24 [.945]** with two ≥Ø3.2 holes at **19 ±0.1** `[datasheet NE8FDP.pdf p.1 — no text layer, read by rendering at 160 dpi]`; panel thickness max 4 mm `[datasheet NE8FDP-DATASHEET.pdf p.2]`. Thonkiconn: body **9 × 8.3 mm**, bushing **Ø6**, thread 4.5 mm, ~18 mm behind panel `[datasheet PJ398SM-drawing.jpg — image only]`. Pot bushing: `[datasheet RV09AF-40.pdf]` / `[datasheet R0904N.pdf]` are banked | rewrite the caveat: the etherCON row and the jack row are sourced; only the pot row and the 1:1 paper check remain |
| 11 | "13.35 mm of aluminium each side of the bore" | `[repo docs/decisions/0004-cv-interface-module.md:743]` | **CONTRADICTED, by 0.1 mm** | The drawing's cutout is **≥Ø24** `[datasheet NE8FDP.pdf p.1]`. `[calc]` (50.50 − 24)/2 = **13.25 mm**. 13.35 implies a Ø23.8 bore, i.e. *below the minimum cutout*. The companion figure in the same sentence is exactly right: flange 26 mm → (50.50 − 26)/2 = 12.25 mm of visible panel | `[datasheet NE8FDP.pdf p.1]` + `[calc]` |
| 12 | "the buck is ~90 % efficient at a 12 V input, not the 85 % this document used — 85 % is the 28 V-input figure" | `[repo docs/decisions/0005-power-architecture.md:171]` | **CONFIRMED verbatim** | Selection Guide `[datasheet R-78E5.0-1.0.pdf p.1]`: R-78E5.0-1.0, input **8–28 V**, efficiency **93 % @ min Vin**, **85 % @ max Vin**. So 85 % is indeed the 28 V figure and ~90 % at 11.4 V is a sound interpolation | `[datasheet R-78E5.0-1.0.pdf p.1]` |
| 13 | WS2815 strip current table — 30/m 0.50 A, **60/m 1.01 A**, single hue 0.34 A, 40 % 0.13 A | `[repo docs/decisions/0014-lighting.md:129-132]` | **STILL UNSOURCEABLE — and it carries no marker at all** | `[calc]` 1.01 A ÷ 50 LEDs = **20.2 mA per LED at full white**. The banked datasheet gives **Quiescent Current 2.1 mA** and **RGB Channel Constant Current 15 mA** `[datasheet WS2815.pdf p.3]`. Those two give 47.1 mA/LED if each channel draws its 15 mA from +12 V, or 17.1 mA/LED if the channel current is shared down a series string. **The table matches neither**, and the LED datasheet cannot settle it — the die-per-channel arrangement is the *strip assembler's*, and that row is `BLOCKED`. This is the one place where a blocked row still holds up a live number | needs a marker either way; today it is an unattributed number carrying the umbilical budget and the thermal clamp |
| 14 | "the 0.98 W sustained-fault figure … has never had a source" | `[repo hardware/bom.csv:103]` | **CONFIRMED as not-in-document** | I searched the whole banked SP0504BAHT sheet: it is specified by pulse (IEC 61000-4-2, 8/20 µs) and carries **no steady-state power dissipation figure at all** `[datasheet SP0504BAHT.pdf, 8 pp]`. The row's own inference from the ESD7104 is upheld for this part too | `[datasheet SP0504BAHT.pdf — not in document]` |
| 15 | `U-TVS-SPI` is **SOT-23-6** | `[repo hardware/controller/carrier.md:847]` | **CONTRADICTED** | Ordering Information `[datasheet SP0504BAHT.pdf p.1, read by rendering]`: **SP0504BAHTG — CH 4 — SOT23-5**. SOT23-6 is the 5-channel SP0505BAHTG. `[repo hardware/bom.csv:103]` already says SOT-23-5, so the two corpus files disagree and the schematic page is the wrong one | `[datasheet SP0504BAHT.pdf p.1]` |
| 16 | `D-REVSHUNT` SS34 in **DO-214AC** | `[repo hardware/bom.csv:107]` | **CONTRADICTED** | `[datasheet SS34.pdf p.1]` "MECHANICAL DATA Case: **SMC (DO-214AB)**", and the p.3 dimension table repeats it. DO-214AC is SMA — which is the **SS14**, a 1 A part `[datasheet SS14.pdf p.1]`. There is no DO-214AC SS34 in this document | `[datasheet SS34.pdf p.1]` |
| 17 | `F-CHAIN` polyfuse in **1206** | `[repo hardware/bom.csv:97]` (package column) | **CONTRADICTED — and already known, in the same row** | `[datasheet MF-PSMF010X-polyfuse.pdf p.1]` "Compact design to save board space — **0805 footprint**", and p.3's ordering key "PSMF = **0805** Surface Mount". The row's own notes say "ALSO THE PACKAGE IS WRONG: this part is 0805, this row says 1206" — **and the package column still says 1206.** The finding was written where the editor was, not where the reader looks | `[datasheet MF-PSMF010X-polyfuse.pdf p.1]` |
| 18 | "LT5400-1 is the four-equal-10k 1:1 quad … verified in committed BOMs on GitHub `[github]`" | `[repo hardware/bom.csv:15]` | **CONFIRMED, and the provenance can be upgraded off GitHub** | Available Options `[datasheet LT5400.pdf p.2]`: **LT5400-1, R2=R3 10k, R1=R4 10k, ratio 1:1**. The same page also says **"EXPOSED PAD (PIN 9) IS FLOATING"** and θJA 40 °C/W — the floating part is not in the row, and it is what decides whether the pad land needs a net | `[datasheet LT5400.pdf p.2]` |
| 19 | `U-BREATH` "case 1351-01" | `[repo hardware/bom.csv:5]` | **CONFIRMED verbatim** | `[datasheet MPXV4006DP.pdf p.2]` "MPXV4006DP **CASE 1351-01**" (and MPXV4006GP CASE 1369-01, which is the GP trap the row already documents) | `[datasheet MPXV4006DP.pdf p.2]` |
| 20 | Citation path `datasheets/discrete-and-power/MF-PSMF010X.pdf` | `[repo hardware/bom.csv:97]` | **BROKEN LINK** | The file is `MF-PSMF010X-polyfuse.pdf`. I checked all 44 distinct `datasheets/…` paths cited anywhere in the design corpus; **this is the only one that does not resolve** | fix the path |

### Two claims I could not reach, and say so

- **`TcOffset` for the MPXV4006DP** — the BOM row already records that the
  datasheet defines it in footnote 4 and never gives it a value. I confirmed the
  absence. Bench measurement, not a fetch.
- **`matrix-led-current`** — `config/figures.yaml` has it `blocked`, and the
  README's reasoning holds: Worldsemi publishes no WS2812B-0807 datasheet, the
  two XINGLIGHT surrogates disagree (12 vs 19 mA/channel), and nothing in the
  bank closes it. A current probe at E1 closes it.

---

## §3 — The 21 `BLOCKED` / `NOT-FETCHED` rows, ranked

`merge-manifests.py` prints 10 as historical. **It is undercounting by three.**
The test is `r[0].strip().lower() in banked` — exact string equality on the part
name `[repo tools/merge-manifests.py:53-56]` — so a blocked row whose name is a
prefix of the banked row's name is still printed as a live gap:

| blocked row | the banked row that closes it | why the tool misses it |
|---|---|---|
| `2.54mm IDC ribbon socket (mating half)` | `2.54mm IDC ribbon socket (mating half) - TE 622 / 636 / 609 series` → `connectors/TE-IDC-SOCKET-CATALOG-82012.pdf` | banked name has a suffix |
| `Gateron KS-33 vendor drawing` | `Gateron KS-33 vendor drawing and product specification (Low Profile 2.0 Red, linear)` → `mechanical/GATERON-KS-33-VENDOR-SPEC-DRAWING.pdf` | banked name has a suffix |
| `MPXV4006 AN1646` (the one `NOT-FETCHED`) | `MPXV4006DP application note AN1646` → `other-semi/MPXV4006-AN1646.pdf` | names differ in word order |

**So 13 of 21 are historical and 8 are live.** Of those 8, ranked by what they
actually block:

| rank | row | blocks | verdict |
|---|---|---|---|
| **1** | **`WS2815 LED strip` (assemblers)** | The 60/m current table in ADR 0014 (§Table 2 #13), and through it `umbilical-current` = 359 mA and the whole thermal-clamp argument. Also `carrier.md`'s ~10 mm strip width, which is one side of the 45 mm-carrier / side-channel conflict | **BLOCKS A DECISION.** The LED datasheet is banked and does not substitute for it |
| **2** | **`WS2812B-0807`** | `matrix-led-current`, `blocked` in `figures.yaml` | **BLOCKS, and cannot be unblocked by fetching** — established vendor negative. Current probe at E1 |
| **3** | **`MT165-MX keycap`** + **`MT165-MX keycap vendor drawing`** (two rows, one gap) | Z stack above `PLATE-TOP`: height, stem depth, profile all unpublished. Also an unresolved vendor disagreement on switch compatibility (Tai-Hao says Choc V1, Beekeeb says not-V1) that documents cannot settle | **BLOCKS the mechanical stack.** Two independent routes already failed |
| **4** | **`Sub-miniature SPST toggle 6 mm metric bushing`** | The panel hole for `SW-POWER`. The banked E-Switch drawing is a *different part* — SPDT, 1/4-40, ~6.4–6.5 mm + keyway | **BLOCKS a panel dimension**, and is the easiest of the four to close by choosing a specific part |
| 5–7 | `Ferrite bead ≥1A 600R@100MHz` (Murata/TDK representative), `…Murata BLM31 route`, `…TDK MPZ route` | nothing | **MERELY ABSENT.** The chosen part is banked with the bias curve that was the whole point; these are second sources. The Murata judgement is upheld in the README: Murata's PDF carries no bias curve either |
| 8 | `1N4148W` *(also listed historical)* | nothing | closed twice over: Vishay SOD-123 and Diotec SOD-123F both banked |

---

## §4 — Documents whose numbers exist only as pictures

`pdftotext` is not installed here at all, so the first failure mode is universal.
But even with a working extractor, these files return nothing or near-nothing,
**and they are disproportionately the ones carrying mechanical constraints.**
Measured with `pymupdf`, characters of extractable text per page:

| file | pages | chars/page | what is in the picture and nowhere else |
|---|---|---|---|
| `connectors/NE8FDP.pdf` | 1 | **0** | Flange 31 × 26 mm, ≥Ø24 cutout, 19 ±0.1 screw pitch, 34.55 / 36.3 mm depth. **The tallest item in the 10HP panel stack.** |
| `connectors/NE8MC.pdf` | 1 | **0** | Cable-shell outline and length |
| `connectors/PJ301M-12.pdf` | 1 | **0** (one raster image) | Jack outline; a scan, so even OCR would be needed |
| `connectors/PJ398SM-drawing.jpg` | — | **n/a, it is a JPG** | The entire Thonkiconn dimension set and PCB layout |
| `discrete-and-power/HI1206N601R-10-ferrite-bead.pdf` | 1 | **71** | The impedance-vs-DC-bias curves — axis labels only, no values |
| `discrete-and-power/MI1206K601R-10-ferrite-bead.pdf` | 1 | **169** | **The chosen bead's bias curve**, the single criterion FB-IN was selected on |
| `connectors/100SP1T2B3M2QEH.pdf` | 2 | **78** (p.1 = 0, p.2 = Mouser cover) | The whole E-Switch production drawing |
| `connectors/NE8MX.pdf`, `NE8MX6.pdf` | 1 | 424 / 398 | Partial: the outline dims *are* in the text layer; the rest is drawing |

**Two corrections to what the brief expected:**

- **`TE-IDC-SOCKET-CATALOG-82012.pdf` is fully text-bearing** — 2294 chars/page
  over 104 pages, including every page that mentions 622/636/609. It is not in
  this category.
- **`GATERON-KS-33-VENDOR-SPEC-DRAWING.pdf` is the dangerous case, and it is
  worse than a blank.** It averages 1841 chars/page, so a script "gets
  something" — five pages of spec prose. But the dimensioned drawing is p.6, and
  the only numbers in p.6's text are `0.2 / 0.4 / 1.7 / 3.0` (travel and
  tolerance). **The 12.2 mm height, the plate cutout and the PCB layout are
  vector.** A script that greps this file for dimensions returns prose and finds
  nothing, and nothing in the output says the extraction failed.

Also banked and inherently non-greppable, which is fine but worth listing so
nobody scripts against them either: `NE8FDP.dxf`, `NE8FDV.kicad_mod`,
`PJ398SM.kicad_mod`, `GATERON-KS-33-3D.step`, two Gateron `.kicad_mod`, the
Gateron ergogen `.js`, `LILYGO-…-3D.stp`, `LILYGO-…-OUTLINE.dxf`,
`WAVESHARE-…-dimensions.jpg`, `-function-block.png`, `-pinout.png`,
`-circuitpython-pins.c`, `EURORACK-3U-…kicad_pcb`, `…make_blanks.py`.

---

## §5 — Duplicates

**`WS2815` is the only duplicated content in the bank.** I hashed all 96 manifest
rows: exactly one SHA-256 appears twice —
`72e22d2f740c561d…` at `mechanical/WS2815-worldsemi-datasheet.pdf` **and**
`other-semi/WS2815.pdf`. Same 621,006-byte file, 8 pages, byte-identical.

No other duplicate exists by hash. Two near-duplicates are **not** duplicates and
should not be merged:

- `other-semi/XL-0807RGBC-WS2812B.pdf` (2022 rev) vs `-REV2024.pdf` — different
  files that **disagree** (12 vs 19 mA/channel), which is exactly why both are
  banked.
- `connectors/R0904N.pdf` vs `R0904N-thonk.pdf` — the vendor sheet and Thonk's
  reprint.
- The four `74HC165-*.pdf` are four vendors of one function, deliberately.

The corpus cites `other-semi/WS2815.pdf` three times and
`mechanical/WS2815-worldsemi-datasheet.pdf` never. Recommendation: keep one row,
or state in the `mechanical/` row's note that it is a copy — otherwise a future
reader updating one path leaves the other at an older revision, which is this
project's named failure mode applied to the bank itself.

---

## §6 — Ranked: what is genuinely still missing, and what it blocks

1. **The ESP32-S3 silicon datasheet (and the TRM).** Not banked, and — unlike
   every other gap here — **it has never had a manifest row at all**, so it is
   invisible to `verify-datasheets.py`, to the README's "what is still missing"
   section and to the merge tool. It underwrites the pin map, the IO_MUX
   argument, the GPIO-matrix clock cap, the boot-window claim that justifies an
   unretrofittable pair of pulldowns, and the 3.3 V logic levels that meet the
   74AHCT125. **It is reachable** — a copy of v2.2 was fetched into an agent
   scratchpad during this wave. *Blocks: four claims in `carrier.md`, two of them
   load-bearing for parts that cannot be added later.*
2. **The WS2815 strip assembly** (manifest row `BLOCKED`). *Blocks: the 0014
   current table, and through it `umbilical-current` 359 mA, the clamp-legal
   worst case, and the side-channel width conflict.* The chip datasheet is
   banked and is not a substitute.
3. **`QMI8658C` (the IMU).** No document, no manifest row, and ADR 0007 selects
   it. Same invisibility problem as the ESP32-S3. *Blocks: any ODR / noise /
   latency claim in the IMU path.*
4. **`PESD12VS1UB`** (`D-TVS-BREATH`, qty 2, SOD-323). A named part on the
   analog breath line with no document and no manifest row. *Blocks: the 12 V
   standoff and the capacitance it adds to a 500 Hz analog channel.*
5. **`MT165-MX` keycap.** Two blocked rows, two failed routes, vendor
   disagreement on switch compatibility. *Blocks: the Z stack above `PLATE-TOP`.*
6. **The `SW-POWER` toggle.** No part chosen; the banked drawing is a different
   switch. *Blocks: one panel hole. Cheapest of the six to close.*
7. **`U-LOADSW`'s N-FET and sense resistor, `L-BUCK-IN`, `C-BUCK-IN`,
   `LED-PANEL`, `SKT-BREATH`, `MECH-PTFE`, `U-TVS-CHAIN`.** Eight rows that name
   no manufacturer and no part number, so no document *can* be banked. Three of
   them carry arithmetic in the corpus anyway — the input-LC damping result
   (needs `C-BUCK-IN`'s ESR), `R-LED-PANEL`'s 2k2 (needs an LED `V_f`), and the
   LT1641 foldback (needs `R-ILIM`). **These are BOM gaps wearing provenance
   markers, and no amount of fetching closes them.**
8. **`LT5400` rev fc.** Rev fa answers the exposed-pad and the `-1` option
   completely. Rev fc is wanted only so that `LT5400-7` is *refuted* rather than
   *not-in-document*. Lowest priority of anything here.

### Fixes that need no fetch at all

- `hardware/bom.csv` `D-REVSHUNT`: `DO-214AC` → **`DO-214AB (SMC)`**, or change the part.
- `hardware/bom.csv` `F-CHAIN`: package column `1206` → **`0805`** (the note already says so).
- `hardware/bom.csv` `D-USBOR`: the package cell describes only the 1N5817 option; SS14 is SMA/DO-214AC.
- `hardware/controller/carrier.md:847`: `SOT-23-6` → **`SOT-23-5`**.
- `hardware/controller/carrier.md:848`: drop the `BI` `[from memory]` — the same file resolved it 130 lines earlier.
- `hardware/bom.csv` `F-CHAIN` note: path → `MF-PSMF010X-polyfuse.pdf`.
- `docs/decisions/0004-…:743`: `13.35 mm` → **`13.25 mm`** (≥Ø24 cutout).
- `docs/decisions/0004-…:770`: the "all behind a blocked proxy" caveat is now false for the etherCON and the jack.
- Rows citing **ERA-3A** for an **0805** part should name **ERA6A** — `[datasheet ERA-3A-thin-film-0p1pct.pdf p.1]`: 3A = 0603 0.1 W, 6A = 0805 0.125 W. The document covers the family; only the part name is wrong.
- `tools/merge-manifests.py:53-56`: exact-name matching under-reports closed gaps. Prefix or normalised matching would have printed 13, not 10.

### One structural recommendation

**A part with no manifest row is invisible to every tool in this repo.**
`verify-datasheets.py` checks that every *row* has a file and every *file* has a
row — it cannot check that every *BOM part* has a row. The ESP32-S3, the
QMI8658C and the PESD12VS1UB are all missing in exactly that blind spot, and
all three are named, selected parts. A ~20-line check that walks `bom.csv` and
reports named-manufacturer rows with no manifest row (blocked or banked) would
have surfaced them, and would keep surfacing them.
