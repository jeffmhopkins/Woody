# STATUS — what landed, by finding id

Generated from the reports by `tools/extract-findings.py` (`FINDINGS.csv`); this
file answers every id in it. Measured against the branch tip after the fix
round (`claude/car-instrument-cad-design-xvqwv2`); the wave itself measured
`d46a3b0`. `VERIFIED.md` says how each was checked.

**Gates at the end of the round** `[run]`: `pcb.py check key-board-lh` 0 errors
(DRC warnings now fail); `kicad.py check` PASS; `check-staleness.py` PASS;
`merge-bom.py --check` 0 problems; `check-netlist.py --strict` exit 0;
`verify-datasheets.py` 0 problems; body CAD 0 DRC FAIL, 0 clashes.

**Count:** 107 fixed, 5 partly, 2 not fixed, 1 rejected, 1 accepted, stated — 116 findings.

| id | sev | disposition | where | evidence |
|---|---|---|---|---|
| K1-1 | medium | accepted, stated | see evidence | key-switch-network.md §2 "Every key edge breaks the 74HC165's input transition limit": the reviewer's arithmetic re-derived [calc: 104 444 ns/V release, 280.6x the interpolated 372 ns/V; 5 311 ns/V press, 14.3x; 87.6 µs in the band, 35 % of releases]; accepted as a data input captured on SH/LD's rising edge, ICC measured at bring-up; SN74HCS165 recorded as the owner's open choice (Still open) |
| K1-2 | medium | fixed | key-switch-network.md, key-switch-network/bom.csv (R-KEY-SER, C-KEY), config/figures.yaml, docs/reference/latency-budget.md | Verified: the page calls the RC a glitch filter, not the debounce. Debounce is firmware's release window, sized against `ks33-contact-bounce`. Forbidden patterns added for "free hardware debounce" and "a BOUNCE filter". |
| K1-3 | medium | fixed | key-switch-network.md, latency-budget.md, figures.yaml | Verified: both "125 µs" sentences now cite `key-release-time`. Patterns "125 µs release filter" and "125 µs the key network" added. The "mean 125 µs" lines are untouched. |
| K1-4 | low | fixed | key-marker-and-bits.md, ADR 0010, ADR 0004 | The count now cites `spare_bits_switches`. The item says what is still open (fitting, not bit placement). Dated notes added to ADR 0010's and ADR 0004's "three". |
| K1-5 | low | fixed | key-marker-and-bits.md | "11 of 31" does not reproduce: my own calc gives 3/2 reload points, and 1 is guaranteed. Replaced with the model and "not reliably caught; firmware must not count on it". |
| K1-6 | low | fixed | key-switch-network/bom.csv R-KEY-PU row; key-marker-and-bits.kicad_sch R-KEY-PU-FREE Note | row by the first docs pass; the sheet Note by kicad.py set-field, exported and rendered |
| K1-7 | low | fixed | key-switch-network.md §2, R-KEY-SER row | Verified: the resistor sits node→switch, and KS-33 is rated 10 mA 12 VDC [spec PDF]. The page now states the real role (divider, and limiting C-KEY's dump into the contact, ~33 mA peak [calc]). A larger value is left as an open trade. |
| K1-8 | low | fixed | key-switch-network.md | Verified: 10 kΩ × 47 nF = 470 µs, and the release crosses V_IH at ~561 µs. The page says 10 kΩ also means shrinking C-KEY. |
| K1-9 | low | fixed | key-switch-network.md; R-KEY-PU row; key-switch-network.kicad_sch C-KEY and R-KEY-SER Notes | pages by the first docs pass; sheet Notes by kicad.py set-field |
| K1-10 | low | fixed | key-register.md (Interfaces row and §1) | Verified with Nexperia p.4 Table 3 and ADR 0001: SH/LD is now described as level-sensitive, sampled when it returns HIGH. |
| K1-11 | low | fixed | see evidence | TP-SER-LH / TP-SER-RH on both board sheets (label CHAIN_SER_LH, HOP_LT_RH); TP-CHAIN row qty 12, SER tie on the bench; placed at the row's end on the LH board |
| K1-12 | advisory | fixed | see evidence | key-chain-loom.md, cluster-boards.md: U-TVS-CHAIN guards the MCU pins only; the hop nets and the key board land on 74HC165 pins rated >2 kV HBM [74HC165-nexperia.pdf p.1] - accepted; the spare channel cannot cover three hops |
| K1-13 | advisory | fixed | see evidence | C-BULK-CHAIN-LH/-RH, 10 µF 0805 dnp footprint on each board's 3V3; row C-BULK-CHAIN in key-chain-loom/bom.csv; pcb.py carries dnp / exclude-from-BOM to the footprint |
| K1-14 | advisory | fixed | key-switch-network.md, key-register.md, C-KEY row; key-register.kicad_sch U-KEYS Pins_source | Pins_source now cites 74HC165-nexperia.pdf p.3 and p.4 Table 2 [run: pdftotext p.4 "Table 2. Pin description"] |
| K2-1 | high | fixed | woody_body.scad chain_path; loom page, CBL-CHAIN row, ADR 0017, DESIGN.md, board README | main board's cable up, key board's down (-RN2, print sheet 1); a cable whose ends both leave downward is a standard cable, and wrong |
| K2-2 | medium | fixed | woody_body.scad; loom page, CBL-CHAIN row, ADR 0017, DESIGN.md | the hairpin lies between the plugs' heights; both hands fold toward the tail (routing.chain_fold), the right hand because toward the mouth it reached the gap's lid screws |
| K2-3 | medium | fixed | see evidence | board README, key-chain-loom.md, CBL-CHAIN row, ROADMAP: meter every cable before first power |
| K2-4 | low | fixed | see evidence | board README, loom page, CBL-CHAIN row, ADR 0017, DESIGN.md: order FFSD-06-D-<code>-01-N-RN2, code from drc "key-chain cable to order (FFSD length code)" |
| K2-5 | low | fixed | tools/kicad.py check | as K7-1 |
| K2-6 | low | fixed | see evidence | config/body.yaml chain comment: both prints banked, stand-in FFSD-06-D-xx.xx-01-N-RN2 |
| K2-7 | advisory | fixed | see evidence | plus the docs: board README and J-CHAIN row explain the mouth arrow and pin-1 dot |
| K2-8 | advisory | fixed | hardware/nets.yaml | `GND_CHAIN` now gives both ends: main-board pins 1/3/5/7/9, key-board pins 4/6/8/10/12. |
| K3-1 | medium | fixed | see evidence | pcb_route.py: every SMD pad blocks vias of its own net too (OWN_PAD_GAP); re-laid board: 0 of 43 vias on or in an SMD pad [run: pcbnew HitTest + polygon distance] |
| K3-2 | medium | fixed | tools/pcb.py check | as K7-5: the two unchecked limits (silk line width, silk to pad) now checked, and warnings fail |
| K3-3 | low | fixed | see evidence | fit_footprint_silk widens library silk to fab silk_line_min and drops strokes nearer a pad opening than silk_to_pad; silk_dot/arrow at SILK_W; pin-1 dot moved to 1.3 mm; pcb.py check's own silk checks report 0 |
| K3-4 | low | fixed | see evidence | J-CHAIN footprint drill 0.70 on 1.07 pads; arithmetic in hardware/lib/README.md |
| K3-5 | low | fixed | see evidence | KS-33 footprint drill 1.3; arithmetic in hardware/lib/README.md; first switch confirms |
| K3-6 | low | partly | see evidence | commit() tests collinearity on grid cells, merge_tracks post-pass: 684 -> 243 segments, 0 collinear joints [run]. 4 acute junctions remain [run: 75°, 50°, 32°, 55°], all GND_CHAIN, inside the same-net pour, which fills round them only where the wedge is wider than its 0.25 mm minimum; not removed by the router |
| K3-7 | low | fixed | see evidence | layout.yaml networks: T round the KEY node (pcb.py network_parts); signal vias on KEY nets no longer forced |
| K3-8 | advisory | fixed | see evidence | C-DECOUPLE-165-LH across U-KEYS pins 16/15: each 2.25 mm centre to centre [run] |
| K3-9 | low | fixed | see evidence | PCB title block from layout.yaml silk:, full stackup (finish, mask, silk colour, 1 oz) by set_stackup |
| K3-10 | advisory | fixed | tools/pcb.py render; fab/ | key-board-lh-PTH.drl and key-board-lh-NPTH.drl [run: ls fab/, 16 files] |
| K3-11 | low | fixed | see evidence | layout.yaml rules comment cites the banked 0.10/0.10 mm |
| K3-12 | advisory | fixed | see evidence | as K5-11 |
| K3-13 | advisory | fixed | see evidence | the register's label is searched beside its courtyard (beside()), not printed under the body |
| K4-1 | medium | fixed | see evidence | board README: the CPL is the guide's Method 1 (raw KiCad rotations); the guide credits rotation fixes only to a plugin this flow does not use, so JLC's preview is the check; pcb.py docstring says the same |
| K4-2 | low | fixed | hardware/unplaced.csv (MECH-KB-STANDOFF) | Part class is marked OPEN. PEM's M2 standoffs are microPEM, not SO/BSO [web, as K4 cited]. No part number invented. The row says to buy the nearest catalogue length and re-check `switch.pcb_below_seat_window`. The other worker is banking PEM PDFs; the [web] cite can move to them once they have MANIFEST rows. |
| K4-3 | low | partly | see evidence | research pass banked YAGEO, UNI-ROYAL and Samsung catalogue PDFs (.manifest-R13); Samsung's per-part sheet was not fetchable (the catalogue has the neighbouring CL21B473KBANNN, p.27); U-KEYS Pins_source cites Nexperia, the part bought |
| K4-4 | low | fixed | board README | MPN/LCSC prose removed; points at the sheets and fab/*-bom-jlc.csv |
| K4-5 | low | partly | hardware/cluster/bom.csv SW1-n | the row records that the Gateron order code is unknown (bought from Amazon) and where it goes once known; the sheet MPN stays prose until then |
| K4-6 | low | fixed | see evidence | board README: upload list, order options, what is bought separately, J-CHAIN from Samtec with sourcing open |
| K4-7 | advisory | rejected | — | The claim is wrong. SW1-n's "2 spares (octave up/down)" are the switches for the two `spare_bits_switches` positions, so it is the same 2, not two different ones. Dropping a spare makes the BOM 20 against 21 placed, which the checker reports. It does not pass silently. |
| K4-8 | advisory | fixed | see evidence | as K3-4: J-CHAIN drill 0.70 on 1.07 pads |
| K4-9 | advisory | fixed | key-register/bom.csv (U-KEYS) | Added the vendor preference at 3.3 V (Nexperia JESD8C / onsemi 3.0 V row). TI falls back to `conservative_bound`. |
| K5-1 | high | fixed | see evidence | as K2-1 |
| K5-2 | medium | fixed | drc "key-chain cable to order (FFSD length code)"; README, loom page, CBL-CHAIN row | inches overall over both sockets, -0.125 in covered |
| K5-3 | medium | fixed | see evidence | chain_lift = hardware.ubolt_drop in the service length; routing.chain_service source |
| K5-4 | low | fixed | see evidence | plate window removed; rule "J-CHAIN pin tails clear of the key plate" from boards.chain_hdr_tail (print sheet 2 C-C) |
| K5-5 | medium | fixed | see evidence | hardware.kb_standoff_edge 3.0 (MSO4-M2, PEM MPF p5); rule "key-board standoffs clear of the switch cutouts" 3.61 mm; inset 3.0 |
| K5-6 | low | fixed | see evidence | "key-board standoff length window" [2.0, 2.4] from switch.pcb_below_seat_window; stocked-length NOTE with the shim; MECH-KB-STANDOFF row |
| K5-7 | low | fixed | hardware/unplaced.csv (MECH-KB-SCREW) | Screw length now has a maximum for a through standoff: `key_board_t` + drc "key-board standoff length (derived)" + `plate-thickness`, cited by name. Oak top resting on the plate verified in DESIGN.md:31. |
| K5-8 | low | fixed | see evidence | mechanical/clash-allow.yaml text no longer states the 1.6 mm board's 0.75 mm |
| K5-9 | low | fixed | see evidence | switch.pcb_t: the main board's, status tbd, decided by its layout |
| K5-10 | low | fixed | see evidence | cluster_margin = boards.kb_end_margin; the new clash it caused (lid screw into the breath sensor) fixed by a floor on fastener_x[0] and rule "mouth lid screws clear of the breath sensor" |
| K5-11 | low | fixed | see evidence | ADR 0020 point 3 dated note; woody_body.scad comment; tooling.md: no rule area on the PCB, none needed - the model's parts envelope |
| K5-12 | advisory | fixed | see evidence | as K2-6 |
| K5-13 | advisory | fixed | see evidence | boards.cluster_smt_h cites the Nexperia datasheet section 12 SOT109-1 |
| K5-14 | advisory | fixed | see evidence | loom page, board README Open table, CBL-CHAIN row, ROADMAP: chain_plug_proud decides whether the cable clears the shroud |
| K5-15 | advisory | fixed | see evidence | board README: the DXF is the outline only; the M2 holes are footprints from pcb-geometry.echo, in the NPTH drill file |
| K5-16 | advisory | fixed | see evidence | as K3-4 |
| K6-1 | high | fixed | see evidence | board README status box and first Open row: switch positions provisional until M2/M3, orderable as a prototype |
| K6-2 | medium | fixed | cluster-boards.md | The outline is now cited as the body CAD's (ADR 0020 point 3, DXF), with positions provisional until M3. Status line updated; the variant-table sentence now points at the hierarchical sheets and `allocation.yaml` (ADR 0019). |
| K6-3 | medium | fixed | cluster-boards.md | "Still open" now lists the standoff part, the plate alloy and stiffening. §5 cites the drc standoff line and `switch.pcb_below_seat(_window)` instead of 2.0–2.4 / 5.10 / 1.9 / 3.2–3.6. |
| K6-4 | medium | fixed | cluster-boards.md | The "63" total is dropped. It now cites the R-KEY-PU (`key-pullup-qty`), R-KEY-SER and C-KEY rows (these sum to 66). |
| K6-5 | medium | fixed | key-marker-and-bits.md | Same fix as K1-4. |
| K6-6 | medium | fixed | see evidence | as K5-11 |
| K6-7 | medium | fixed | tools/pcb.py check; board README; tooling.md; layout.yaml comment | the board's design rules are compared with layout.yaml, and the docs say so |
| K6-8 | medium | fixed | ADR 0019 amendment, CLAUDE.md bullet, docs/reference/tooling.md | tooling.md now lists Manufacturer, MPN, LCSC, Assembly [run: grep tooling.md] |
| K6-9 | low | fixed | see evidence | layout.yaml rules comment cites the banked 0.10/0.10 mm |
| K6-10 | low | fixed | see evidence | layout.yaml: the placement comment rewritten (the typo gone, "LH4 between the LH4 and LH5 switches"), no dated history line |
| K6-11 | low | fixed | see evidence | board README: prerequisites (setup-env.sh) and the full sequence after a sheet edit |
| K6-12 | low | partly | see evidence | the three retired designs: body.yaml standoff and prints comments, woody_body.scad flat-flex comment, all fixed; ADR 0018 line 11 left as the decision's own context |
| K6-13 | low | fixed | see evidence | tooling.md: three pipelines incl. the PCB; prerequisites; the retired key in the past tense |
| K6-14 | low | fixed | see evidence | tooling.md: the PNGs are rendered from the .kicad_sch, which is the source |
| K6-15 | low | fixed | see evidence | tooling.md: three library models, fetched by setup-env.sh; render refuses a missing one |
| K6-16 | low | fixed | cluster-boards.md, docs/reference/ks33-geometry.md | Pole and pin numbers replaced by `switch.pole_tip_below_seat` / `pcb_below_seat` / `boards.key_board_t`. The owner page now uses the vendor's 5.75 via body.yaml. |
| K6-17 | low | fixed | board README, key-chain-loom.md | both cite key-scan-current |
| K6-18 | low | fixed | key-switch-network.md | Toshiba filename corrected, and the SW peer is now `SW1-n` (`SW-THUMB` is an option on LT). |
| K6-19 | low | fixed | key-switch-network.md, key-register.md | Both pages now point at their `.kicad_sch` and render. They say netlist.yaml is exported and must not be edited. |
| K6-20 | low | fixed | ADR 0019 | "six ... nineteen" replaced by a citation of `replicated:` (21 networks). |
| K6-21 | low | fixed | see evidence | DESIGN.md: key-board outlines are generated from the body CAD; plate-window text removed |
| K6-22 | low | fixed | see evidence | board README Open table: conformal coating added |
| K6-23 | advisory | fixed | see evidence | board README: making the next board from layout.yaml incl. networks:, silk legend, revisions table, bring-up idle word |
| K6-24 | advisory | fixed | docs/decisions/README.md, ADR 0017 Status | Format now allows a dated in-ADR Amendment for a partial reversal. 0017 Status names its amendment. Index re-sorted (0014); 0019/0020 rows note their amendments. |
| K6-25 | advisory | fixed | key-marker-and-bits.md | "Proposed levels" renamed "Levels". "on the display" now says there is no display (ADR 0015) and the counter's surfacing is firmware F7. |
| K6-26 | advisory | fixed | ADR 0020 point 4 | "reaches the steel" changed to "reaches the standoff or the screw head". |
| K6-27 | low | fixed | see evidence | board README: Basic/Extended status cited [web, JLC part pages and API, 2026-09-27] |
| K7-1 | high | fixed | tools/kicad.py check | J-CHAIN pins against the loom netlist J-CHAIN-KEY-<LH/RH>, and the loom's own 13-k rule; a CHAIN_SCK/CHAIN_SHLD swap on a scratch sheet was reported on both pins |
| K7-2 | high | fixed | tools/pcb.py check | stackup thickness against pcb-geometry.echo and body.yaml boards.key_board_t, Edge.Cuts against the key-board DXF within 0.05 mm, switch model height; each fired on a scratch breakage (1.6 mm stackup, outline moved 0.3 mm, SW-LH2 model 3.0) |
| K7-3 | medium | fixed | tools/pcb.py render | Assembly=none only on a symbol excluded from the BOM; R-KEY-PU set to none on a scratch copy stopped render with nothing written |
| K7-4 | medium | fixed | tools/kicad.py check | remedy names python3 tools/pcb.py render <board dir>; stale files grouped per remedy |
| K7-5 | medium | fixed | tools/pcb.py check | design settings against layout.yaml rules:/fab:, fab tests set to ignore fail, every DRC warning fails, own silk checks (off board, line width, text, silk to pad); each fired on a scratch breakage |
| K7-6 | medium | fixed | tools/kicad.py check | a stray file in fab/ or a render with no ledger row fails; three stray files on a scratch copy reported |
| K7-7 | low | fixed | tools/pcb.py render | check first, 3D models present, built in scratch and swapped in; a refused render left every output hash unchanged |
| K7-8 | low | fixed | tools/pcb.py check | switch rotation against the CAD plus switch_rot, flipped switches rejected, J-CHAIN on the bottom; SW-LH3 turned 180 on a scratch copy reported |
| K7-9 | low | fixed | see evidence | cad_geometry's "ribbon" line and build's no_parts strip removed |
| K7-10 | low | fixed | tools/setup-env.sh; tools/pcb.py render | the three 3D models fetched (kicad-packages3D 9.0.0, byte-identical to the installed files); render refuses a missing model; the script passes bash -n but its download loop was not run end to end in the sandbox |
| K7-11 | low | fixed | tools/pcb.py layout | exit 1 on a failed route, board left as it was; built in scratch and swapped on success [run: scratch power_track 3.0] |
| K7-12 | low | fixed | tools/pcb.py check / layout | a missing switch or J-CHAIN is an error line with the DRC report still printed; no layout.yaml gives a clear error |
| K7-13 | advisory | not fixed | - | advisory: re-layout is geometrically identical but not byte-identical; no fingerprint command added |
| K7-14 | advisory | partly | tools/kicad.py check | kicad.py check runs pcb.py check on every laid-out board and now enforces its rules against layout.yaml; it is still not in the commit gate (needs kicad-cli); measured ~5 s, so cheap to add |
| K7-15 | advisory | not fixed | - | advisory; the full CAD rebuild time was not re-measured against the documented timeout |
| K7-16 | low | fixed | see evidence | board README: as K6-11 |
| K8-1 | medium | fixed | woody_body.scad drc "key board to main board gap"; ADR 0017 | the gap is printed (17.4, K8-1's own corrected figure); ADR 0017 no longer says a 2.54 mm IDC "fits nowhere": against "main board parts room under the key boards" it fits nominally and not at its worst case, and says so with a dated note |
| K8-2 | medium | fixed | see evidence | body.yaml standoff comment: "at each corner of the board" |
| K8-3 | medium | fixed | ADR 0020 point 5 + Status | Dated note says the board was grown (point 3) and J-CHAIN sits between the switches (pcb-geometry.echo "chain", drc "chain headers ... clear of the switches"). No route/fold text touched. |
| K8-4 | low | fixed | see evidence | as K5-9 |
| K8-5 | low | fixed | see evidence | as K6-15 |
| K8-6 | low | fixed | see evidence | hardware/lib/README.md cites the full print; body.yaml chain_* sources now cite the SHF and FFSD full prints [verified: FFSD print .120 and positions x .050 + .165] |
| K8-7 | low | fixed | see evidence | repo-maintenance.md §1: fab/ contents, ledgered against the .kicad_pcb and the sheets; stray files fail |
| K8-8 | low | fixed | ADRs 0001, 0009 (×2), 0013; figures.yaml | 20-way changed to 24-way (ADR 0018). The "spare positions open" clause in 0009 is resolved. New figure `mcu-ribbon-ways` (owner carrier.md) with forbidden "20-way ribbon"; ADR 0018's narration does not match it. |
| K8-9 | medium | fixed | config/figures.yaml, key-chain-loom/notes.md | New figure `key-board-chain-pinmap` (owner key-chain-loom.md, value "key-board pin = 13 - main-board pin"). Grepped first: the only hits were notes.md's dated history, which now carries "superseded". Bare "key-board pin 8/4" not added: both are grounds under 13−n. Bare FFC-CHAIN/200528/ffc_conn fired on nine legitimate history lines, so only their data spellings are patterns. Checker PASS. |
| K8-10 | low | fixed | see evidence | layout.yaml via comment and tooling.md: the via rule is JLC's "0.1 over the hole", held also to the PTH ring by KiCad's one annular rule; track/space cites the banked 0.10/0.10 |
| K8-11 | advisory | fixed | see evidence | boards.chain_plug_proud source: not given by either print, DO NOT SCALE, an estimate until a mated pair is measured |
| K8-12 | advisory | fixed | key-chain-loom/bom.csv (J-CHAIN), ADR 0017 | "all four positions" changed to "every J-CHAIN position (chain-connectors)". Owner-page statements left alone. |
| K8-13 | advisory | fixed | ks33-geometry.md; woody_body.scad "flat flex" comment; DESIGN.md "banked full print" | all three edges; the git --since trap needs no change |

**Ids in `FINDINGS.csv` that are not this wave's findings:** `H4-9`, `M2-3`,
`M2-5` are cited by a report from earlier waves and introduced by none here
(`CITED ONLY`); nothing to answer.

## Open, and for whom

- **K1-1: 74HC165 or SN74HCS165** — the owner (`key-switch-network.md`, Still open).
- **MECH-KB-STANDOFF** (K4-2, K5-5, K5-6 follow-on): MSO4-M2-3 needs a shim or ADR 0020's fallback; PEM and the plate vendor, M4.
- **K4-6: J-CHAIN's source** — 0 at JLC; the first order.
- **K7-13, K7-15** not fixed (advisory); **K7-14** partly: `kicad.py check` is not in the commit gate.
- **K3-6** partly: 4 acute GND junctions remain inside the ground pour.
- **K4-5** partly: the switches' order code is unknown.
