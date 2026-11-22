# Main board — `main-board`

The one long board at the thumb level (ADR 0017). It carries:
- the thumb switches and both thumb registers;
- the carrier's circuits: the breath sensor's reference, buffer and ADC, power
  entry, the LED drive and the LED row (ADR 0028), the service header and the
  SPI egress;
- the key chain's two ribbon headers;
- `J-UMB`, where the umbilical arrives from the etherCON's adapter (ADR 0021).

The Matrix is on the right-hand key board's rails (ADR 0021 amendment
2026-10-02) and reaches it by an IDC ribbon from that board into `J-MCU`. The board
is part of the cassette (ADR 0025): every one of its mounts stands on the one
bottom plate, and eight of them are columns up to the key boards (ADR 0022 as
amended).

> **Status (2026-11-21): laid out by hand (#48, ADR 0030), the two `J-CHAIN` headers vertical since #49; `pcb.py check` passes.**
> `main_layout.py` places every part and writes out every track and via; no router ran.
> It follows the two key boards and the Matrix carrier: both `J-CHAIN` headers stand
> straight under theirs, and `J-MCU` takes the ribbon's new pin order. The outline, the thirteen
> LEDs, the switches, the mounts and the connectors are where the body CAD puts them
> (`mechanical/export/main-board.dxf`, the `main` entries in
> `mechanical/export/pcb-geometry.echo`). `fab/` and the renders are this board's. The
> sheets are the source and pass KiCad's ERC. Every part has its footprint and bought
> part on its symbol (`Footprint`, `Manufacturer`, `MPN`, `LCSC`, `Assembly`), from
> selections whose datasheets are banked, and every machine-placed part with a polarity
> or more than two pads has its JLC rotation (`hardware/lib/jlc-rotation.csv`). The
> thumb switch positions are provisional until M2/M3, as the key boards' are.

What each circuit does, and why, is on its page:
- [`carrier.md`](../../carrier/carrier.md), the board's own page, and its
  circuits:
  - [`breath-adc`](../../carrier/breath-adc/breath-adc.md)
  - [`breath-excitation-reference`](../../carrier/breath-excitation-reference/breath-excitation-reference.md)
  - [`power-entry-instrument`](../../carrier/power-entry-instrument/power-entry-instrument.md)
  - [`service-uart`](../../carrier/service-uart/service-uart.md)
  - [`led-strip-drive`](../../carrier/led-strip-drive/led-strip-drive.md)
- The thumb clusters:
  - [`key-register`](../../cluster/key-register/key-register.md)
  - [`key-switch-network`](../../cluster/key-switch-network/key-switch-network.md)
  - [`key-marker-and-bits`](../../cluster/key-marker-and-bits/key-marker-and-bits.md)
- The interfaces whose main-board parts the root sheet draws:
  - [`key-chain-loom`](../../interfaces/key-chain-loom/key-chain-loom.md)
  - [`breath-sense-link`](../../interfaces/breath-sense-link/breath-sense-link.md)
  - [`spi-link`](../../interfaces/spi-link/spi-link.md)

## Files — what is source, what is generated

| File | What it is |
|---|---|
| `main-board.kicad_sch` (+ the circuit sheets it places) | **Source.** Every connection, and each part's identity (ADR 0019) |
| `board-netlist.yaml` | Exported from the sheets (`tools/kicad.py export hardware/boards/main-board`), with KiCad's ERC over the whole hierarchy |
| `*.sch.png`, `*.pcb-*.png` | Renders, recorded in `hardware/SHEETS.csv` |
| `fab/` | **Generated** by `tools/pcb.py render` (Gerbers, drill, placement), recorded in the ledger against the board and the sheets. Never edit it by hand: `kicad.py check` fails on a stale file, and on any file in `fab/` that no tool wrote |
| `fp-lib-table` | Registers `hardware/lib/woody.pretty` (the KS-33, `J-CHAIN`, `J-MCU`, `J-UMB`, MPXV4006DP and WS2815B-V1 footprints, and through them their 3D models) for this project |
| `sym-lib-table` | Registers `hardware/lib/woody.kicad_sym` (the WS2815B-V1's symbol) for this project |
| `main_layout.py` | **The record of the layout** (ADR 0030): every part's place and every track and via, written out by hand with the reason for each. It rewrites `main-board.kicad_pcb`. No router runs on this board |
| `main-board.kicad_pcb`, `main-board.kicad_pro` | Written by `main_layout.py`. Change the layout there and run it, so the reasons stay with the copper; `pcb.py check` holds the board to the sheets, the body CAD and `layout.yaml` |
| `layout.yaml` | The limits the board is held to (`kind: main`): the rules, the stackup, the planes, the `AGND_INST` island and its tie, the breath pair's keep-off, the net classes, keep-outs, heights, iron room, and what its silkscreen says |

The root sheet places, once per instance:
- **the six carrier circuits**;
- **`breath-sense-link`**, whose parts are all on this board;
- **the two thumb registers** (`REG-LT`, `REG-RT`);
- **one key network per thumb key**, plus one at each of the right thumb's
  two reserved spare positions (`sw+`, `sw-`);
- **one pull-up per free bit** (`FREE1`, `FREE2`).

The registers' inputs are wired as `hardware/cluster/key-marker-and-bits/allocation.yaml`
says. Its own parts are the interface circuits' main-board halves:
- from key-chain-loom: both `J-CHAIN` headers, the series resistors, the
  SER terminator, the two beads and the clamp;
- from spi-link: `J-UMB`.

On this board the chain's return is `PWR_GND` and its 3V3 is `DEV_3V3`
(`hardware/nets.yaml`).

`tools/kicad.py check` holds the board to three things:
- the registers' wiring against `allocation.yaml`;
- each `J-CHAIN` pin against the loom's `J-CHAIN-MAIN-<LH|RH>`;
- ERC.

## The references

Numeric, as the key boards'. The BOM row each one buys from is its `Row` field.

| References | BOM row | Sheet |
|---|---|---|
| C1 | `C-AA-ADC` | breath-adc |
| C2 | `C-ADC-BULK` | breath-adc |
| C42 | `C-ADC-VDD` | breath-adc |
| C11 | `C-BUCK-IN` | power-entry-instrument |
| C43 | `C-BUCK-OUT` | power-entry-instrument |
| C13, C14, C205, C206 | `C-DECOUPLE-165` | REG-LT, REG-RT |
| C3, C6–C8, C12, C204 | `C-DECOUPLE-CARRIER` | breath-adc, breath-excitation-reference, led-strip-drive |
| C9 | `C-FB-REF` | breath-excitation-reference |
| C40 | `C-INRUSH-GD` | power-entry-instrument |
| C39 | `C-INRUSH-GS` | power-entry-instrument |
| C15–C24 | `C-KEY` | LT1, LT2, LT3, LT4, RT1, RT2, RT3, RT4, sw+, sw- |
| C26–C38 | `C-LED` | led-strip-drive |
| C4, C5 | `C-REF-OUT` | breath-excitation-reference |
| C203 | `C-SENSOR-OUT` | breath-sense-link |
| C201 | `C-SENSOR-VS-BULK` | breath-sense-link |
| C202 | `C-SENSOR-VS-HF` | breath-sense-link |
| C10, C44 | `C-STRIP-BULK` | power-entry-instrument |
| C45–C47 | `C-STITCH-12V` | power-entry-instrument |
| C207, C208 | `C-USBOR` | power-entry-instrument (#39) |
| D21 | `D-INRUSH-RST` | power-entry-instrument |
| D8–D20 | `D-LED` | led-strip-drive |
| D1 | `D-REF-CLAMP` | breath-excitation-reference |
| D2 | `D-REVSHUNT` | power-entry-instrument |
| D5, D6 | `D-TVS-BREATH` | breath-sense-link |
| D3 | `D-TVS-PWR` | power-entry-instrument |
| FB1, FB2 | `FB-CHAIN` | root |
| FB3, FB4 | `FB-MIDI` | midi-out (#37) |
| J2 | `HDR-SERVICE` | service-uart |
| J4, J5 | `J-CHAIN` | root |
| J7 | `J-MIDI` | midi-out (#37; side entry facing the tail since #45) |
| J8 | `J-MIDI-OUT` | midi-out (#37; through the tail cap since #45, not on this board: `layout.yaml` `not_on_board:`) |
| J1 | `J-MCU` | carrier |
| J6 | `J-UMB` | root |
| L1 | `L-BUCK-IN` | power-entry-instrument |
| NT2 | `NT-AGND` | power-entry-instrument |
| NT1 | `NT-DIG` | carrier |
| Q1 | `Q-INRUSH` | power-entry-instrument |
| Q2 | `Q-USBOR` | power-entry-instrument (#39) |
| R54, R55 | `R-ADC-SER` | breath-adc |
| R47 | `R-ADC-VDD` | breath-adc |
| R5 | `R-ADCDIV-L` | breath-adc |
| R4 | `R-ADCDIV-U` | breath-adc |
| R34–R36 | `R-CHAIN-SER` | root |
| R45 | `R-CS-PULL-ADC` | breath-adc |
| R40 | `R-CS-PULL-INST` | carrier |
| R8 | `R-FB-REF` | breath-excitation-reference |
| R9 | `R-FBX-REF` | breath-excitation-reference |
| R44 | `R-HOP-SER` | root |
| R52, R53 | `R-HOP-SER` | root |
| R42 | `R-INRUSH-G` | power-entry-instrument |
| R43 | `R-INRUSH-GD` | power-entry-instrument |
| R41 | `R-INRUSH-GS` | power-entry-instrument |
| R7 | `R-ISO-REF` | breath-excitation-reference |
| R12, R14, R16, R18, R20, R22, R24, R26, R28, R30, R32, R33 | `R-KEY-PU` | LT1, LT2, LT3, LT4, RT1, RT2, RT3, RT4, sw+, sw-, FREE1, FREE2 |
| R13, R15, R17, R19, R21, R23, R25, R27, R29, R31 | `R-KEY-SER` | LT1, LT2, LT3, LT4, RT1, RT2, RT3, RT4, sw+, sw- |
| R10 | `R-LED-PD` | led-strip-drive |
| R50, R51 | `R-MIDI` | midi-out (#37) |
| R48, R49 | `R-MIDI-PU` | led-strip-drive (#37) |
| R11 | `R-LED-SER` | led-strip-drive |
| R6 | `R-REF-IN` | breath-excitation-reference |
| R38, R39 | `R-SER-BREATH-INST` | breath-sense-link |
| R37 | `R-SER-TERM` | root |
| R1–R3 | `R-SPI-SER` | carrier |
| R56 | `R-RXD-SER` | service-uart |
| R46 | `R-TXD-SER` | service-uart |
| SW1–SW10 | `SW1-n` | LT1, LT2, LT3, LT4, RT1, RT2, RT3, RT4, sw+, sw- |
| U2 | `U-ADC` | breath-adc |
| U10 | `U-BREATH` | breath-sense-link |
| U5 | `U-BUCK` | power-entry-instrument |
| U3 | `U-BUF` | breath-excitation-reference |
| U7, U8 | `U-KEYS` | REG-LT, REG-RT |
| U6 | `U-LVLSHIFT` | led-strip-drive |
| A1 | `U-MCU-RT` | carrier |
| U4 | `U-REF-BREATH` | breath-excitation-reference |
| U9, U11 | `U-TVS-CHAIN` | root |
| U12 | `U-TVS-MIDI` | midi-out (#37) |
| U1 | `U-TVS-SPI` | carrier |
| U13 | `U-USBOR` | power-entry-instrument (#39) |

## Open, and what decides each

What is still open:

| Item | Decided by |
|---|---|
| **The LED row's places** are the body CAD's (`pcb-geometry.echo` `main` `led`, *"LED row on the main board"* in `mechanical/drc.echo`): thirteen LEDs on the centreline, `D8` (LED 1, first on the data line) past the Matrix ribbon and `D9` before it, the same distance from its edge, and `D9` to `D20` at one pitch to the mouth end (`lighting.led_tail_x`, `led_ribbon_x`, `led_pitch`; ADR 0028's amendment of 2026-11-21, whose point 2 is the LED that stands level with `J5`) (`D7` / `C25` went with the removed LED); each `C-LED` in the row on the mouth side of its LED, but `D8`'s beyond `D3`, which stands in the row between them, and `D20`'s on its far side, off the breath sensor (`main_layout.py`). Reshuffled if the diffusion test moves the count. **The WS2815B-V1's chamfer marks pin 1 (NC)**; the footprint's silk triangle marks the chamfer, and JLCPCB's own footprint agrees (`hardware/lib/README.md`) | Layout; the side-light diffusion test; the first order's placement preview |
| **Passives may go on the underside** (owner, 2026-09-29). The underside faces the grounded bottom plate, `hardware.kb_spacer_l` below it, over the board's whole length since the cassette (ADR 0025). At `boards.board_clear` that leaves no room for a part (`mechanical/drc.echo` *"main board underside room over the bottom plate"*), so an underside part needs a **window cut through the bottom plate** under it, down to the oak (the second figure on that line), and must be clear of the thumb switches' housings, pins and the mounts' spacers. Through-hole tails face the plate too: the next row. The thumb switches are already underside parts | The layout; each window goes into the bottom plate's outline in the body CAD |
| **Through-hole tails under the board** (2026-10-01): every part with plated through-hole pins pokes its tails out of the underside toward the grounded bottom plate — `J-CHAIN` ×2, `J-MCU`, `J-UMB` and `U-BUCK` (`config/body.yaml`, *THE THROUGH-HOLE TAILS UNDER THE MAIN BOARD*, says which and why these). `mechanical/drc.echo` *"through-hole tails under the main board clear of the bottom plate"* tests each against what is under it, and the body model draws them for `clash.txt`. `J-CHAIN`'s and `J-MCU`'s clear the plate as supplied. The plate ends short of `J-UMB`'s tail row, and has a window to the oak under the regulator block (`HDR-SERVICE` is surface mount since 2026-10-06, owner, and needs none) (`pcb-geometry.echo` `main` `plate`). **`U-BUCK`'s pins are cut to `boards.tht_trim` below the board after soldering** — as supplied they reach the oak even through the window. `U-BUCK` stands inside the regulator block, or the window moves with it | A part moved off its window: move the block and rebuild the body CAD; a new through-hole part: add it to `tht_tails` in `mechanical/cad/woody_body.scad` |
| **The references with no clear place on the silkscreen** stay on the fabrication layer. `tools/pcb_silk.py` (#54) places every one that has a clear place within reach of its part, on a leader line where the place is not beside it; `python3 tools/pcb_silk.py hardware/boards/main-board --audit` lists the ones left, which stand in the tightest groups (the inrush corner at the tail, the far-edge rows over the key registers) | **Decided** (owner, 2026-11-22, #54): they stay off the silkscreen, on the fab layer's assembly drawing only; no part moves for a label |
| **`C203` at `U10` pin 4** (MPXV4006DP Fig. 3): pin 4 is the corner of `U10`'s own courtyard, at the mouth and far edges, so no 0805 can stand within 3 mm of it on the top face; `C203` stands at `U3`'s input, the net's other end, as before. Nearer needs an underside part and a bottom-plate window under it | Owner |
| **`J-CHAIN` ×2 and `J-MCU` (and `J-MCU-C` on the Matrix carrier, the same footprint): their pads**' ring is at JLC's absolute minimum on the sides facing a neighbour (`fab: annular_min`; pre-fab review, issue #52 F6). It stays: the hole is the one the header's drawing asks for (`datasheets/connectors/CNCTECH-3220-XX-0100-00-1.27MM-BOX-HEADER-VERTICAL.pdf`, *Recommended PCB layout*), a smaller one gives the ring a few hundredths and takes them from the post's fit, and the pitch leaves the pad no room to grow that way (`hardware/lib/README.md`, the IDC header's row). Ask JLC's review of the production file to accept the thin side | The first order |
| **The umbilical adapter** (`PCB-UMB-ADAPTER`) is a separate small board: its schematic is [`../umb-adapter/`](../umb-adapter/README.md), not laid out | With this board's layout |

What the layout holds, and where:
- **Four layers** (ADR 0017 amendment 2026-09-29), JLCPCB's stack
  `JLC04161H-7628` [ds `datasheets/fab/JLCPCB-IMPEDANCE-STACKUPS.pdf`]. Layer 2 `PWR_GND`, layer 3
  the +12 V behind `Q-INRUSH` (`INST_POS12`, `power-entry-instrument.md` §1a); the +12 V
  ahead of it and the other rails are tracks (`layout.yaml` `net_classes:`). **`AGND_INST` is an island on layer 2** round the analog block,
  its moat bridged once by `NT-AGND` (NT2) on `U-ADC`'s tail side, where its digital pins
  (5-7) cross the moat inside the tie's window (`power-entry-instrument.md` §2); since wave 3
  the island takes all of `U-ADC` and the pocket above it where `ADC_VDD`'s capacitors
  stand (#8-3). `check` fails a second tie, an island pad off the island, and any layer-1
  track crossing the moat but at the tie or as the breath pair.
- **White solder mask** both faces, black legend (`layout.yaml` `fab:`; ADR 0028).
- **Every mount plated on `PWR_GND`**, pads both faces, no other net's copper under
  its hardware (`check`); the U-bolt legs' holes unplated, the outer layers kept
  clear round their hardware.
- **The regulator block holds `U-BUCK` alone** (a rule area), against the near edge
  (`boards.tall_side`; the far edge carries the breath pair), `C-STRIP-BULK`,
  `C-BUCK-IN` and `L-BUCK-IN` beside it where their heights fit (`check_heights`).
- **`A1` (the Matrix) and the spare switches `SW9`, `SW10`** are on the sheets and
  not on this board (`layout.yaml` `not_on_board:`, reported as notes); the spare
  positions' networks are placed.
- **`NT1`** at `J-UMB` pin 8 (ADR 0018); **`U-TVS-SPI`** on the J-MCU side of
  `R-SPI-SER`, where its three channels now are.
- **The thumb switches on the underside**, where the body CAD puts them, the near
  row turned 180° (ADR 0022).
- **`U-BREATH`'s ports point to the tail**, as the body CAD and
  `breath-sense-link.md` (*Mounting*) put them, which turns its pins 1–4 (`VS`,
  `GND`, `Vout`) to the board's far edge, away from the rest of the analog block;
  the island reaches round them (`layout.yaml` `cad_parts:`, `islands:`).
- **Every part's place and every track and via are `main_layout.py`'s** (ADR 0030). Its
  header gives the floorplan and why each part stands where it does; each stage's
  function gives its lines in the order the signal runs. In outline:
  - **The analog block** is laid out along its signal from the sensor's pins outward, on
    layer 1 over the island. The ADC's chip select and 3V3 arrive on the bottom face and
    come up inside the island, so only its three SPI lines cross the island's edge,
    beside `NT-AGND`.
  - **The breath pair** (owner, 2026-10-03: *"the analog path should just be routed along
    the top"*, the far edge): the buffer's output and its `AGND` leg side by side on
    layer 4 from the buffer along the far edge to `R38` / `R39` at `J-UMB`, stepping
    inboard at 45 degrees under each far column mount. The `AGND` leg is the inboard
    line, between the signal and every key. Its reference is the `AGND_INST` strip cut
    out of layer 3 under it. Every other net's copper on that layer, and every via,
    keeps 3W off it (`layout.yaml` `pairs:` `guard:`, held by `pcb.py check`). It has no
    guard tracks: nothing else runs in that band on that layer.
  - **The LED data line stays on the top face** from the second LED to the mouth end.
    The first LED stands beyond the driver, in the row's tail-end place, so its two
    lines (`LED_DI` to it, `LED_D1` back from it) each take a lane on the bottom face
    under the driver: two vias a line. Each LED's capacitor stands in the row beside
    it, and their supply and ground pads reach the planes by vias beside them.
  - **The bottom face carries the lines that run the board's length**: the chain's
    trunk north of the LED row, the ADC's four lines and its 3V3 south of it, and each
    near-row key's line where it crosses under the row.
  - **The power paths carry no via** (#8-6): `UMBILICAL_POS12`, `BUCK_IN`, `BUCK_A_OUT`
    and `INST_5V_A` to the 5 V OR are top-face tracks from end to end. Where a power
    part meets a plane it does so by more than one via: three at `Q-INRUSH`'s drain, two
    at each bulk capacitor's pad, the buck's capacitors' returns, `L-BUCK-IN` and
    `D-TVS-PWR`. `D-REVSHUNT`'s anode is a track to `J-UMB`'s own ground pin.
  - **Ground**: every surface pad on `PWR_GND` has a via beside it, or shares one with
    the pad facing it. None stands in a pad (ADR 0030, point 5): the three clamps' middle
    pins, `U9` pin 2, `U11` pin 2 and `U1` pin 2, have theirs just off the pad, the line
    that passed there stepped clear of it.
- **Soldered ground pins meet the plane through relief spokes**, as on the key boards.
  Two exceptions: `J-MCU`'s ground pins, where a 1.27 mm header leaves room for
  one spoke and the rules ask two (the same exception the carrier's end of the ribbon
  takes, ADR 0030), and the mounts, which are clamped and never soldered.
- **The clamps at their connector** (#8-9): `D-REVSHUNT` (D2) beside `J-UMB`'s pins 3 and
  6, and `D-TVS-PWR` (D3) on a top-face track from D2's pad, in the LED row on the mouth
  side of the first LED since that LED took the tail-end place; the buck's capacitors at
  the module (#8-7).
- **Soldering-iron room round the hand-soldered pads** (#34; `layout.yaml` `iron_room:`,
  held by `pcb.py check`): every other part's courtyard 2.0 mm from a thumb switch's pin
  pads on the top face, where they are soldered, and 1.5 mm from `U10`'s. This layout
  meets it everywhere, with no exception listed.
- **The planes stitched** (#8-8; owner, 2026-10-04, in the working chat: *"add 2-3 now"*):
  `C-STITCH-12V` from `INST_POS12` to `PWR_GND` at `J-MCU` (`C45`), `J-UMB` (`C46`) and the
  analog end (`C47`, on `PWR_GND` beside the island), each pad to its plane by its own via
  (`power-entry-instrument.md` §2, *Plane stitching*).

## Ordering it — JLCPCB

**Not to be ordered until it is routed and its gates pass**: `python3 tools/pcb.py check
hardware/boards/main-board` reports 0 errors and `python3 tools/kicad.py check --board
main-board` PASSes - this board's export, ERC, layout and renders, the circuit sheets it
places, and the cross-board connector checks (`docs/reference/tooling.md` §3); another
board's failures do not hold this order (review #6-3). Then `fab/` is this board. JLC's limits are from the banked pages in `datasheets/fab/`; the
pattern is the key boards' order sheet (`hardware/boards/key-board-lh/README.md`,
*Ordering it*), and only what differs is here.

| Option | Pick | Why |
|---|---|---|
| Layers | **4** | ADR 0017 amendment 2026-09-29 |
| Stack-up | **JLC04161H-7628** (`layout.yaml` `stackup:`) | JLC's standard 4-layer 1.6 mm stack; the `.gbrjob` carries it [ds `JLCPCB-IMPEDANCE-STACKUPS.pdf`] |
| Thickness | 1.6 mm (`switch.pcb_t`) | `pcb.py check` holds it |
| Mask / silk | **White / black** (`fab:`) | ADR 0028: the top face is the LED row's first reflector |
| Surface finish | LeadFree HASL (`fab: finish`) | 4-layer FR-4 takes HASL; only 6 layers and up do not [ds `JLCPCB-PCB-CAPABILITIES.pdf`, *Surface Finish*] |
| Copper | 1 oz outer, 0.5 oz inner (the stack's) | |
| Delivery format | Single PCB, **edge rails and fiducials added by JLCPCB** | Standard PCBA asks both, and a board of at least 70 × 70 mm; this one has neither and is narrower (below) |
| PCBA side | Top | Every machine part is on the top face; the thumb switches (underneath) are fitted by hand |
| Assembly | `fab/main-board-bom-jlc.csv`, `-cpl-jlc.csv`; `-hand-assembly.csv` for the rest | One BOM row per LCSC number, its MPN as the Comment (#17 D5) |

**PCBA type: Standard** (owner, 2026-10-04, #17 D1: "Standard PCBA (Recommended)"; ADR 0028,
*Amendment, 2026-10-04*) [ds `datasheets/fab/JLCPCB-PCBA-CAPABILITIES.pdf`]:
- **Why not Economic**: its *PCB Specs for Economic PCB Assembly* table lists 4-layer boards in
  green only (the 4-layer rows - 1.0, 1.2, 1.6 mm - are green; white appears only in the 1.6 mm
  *Red/White, Leaded HASL* row of the 2-layer group; the table's layer column does not render
  in the banked copy, so the grouping is read from the rows' thicknesses). Standard has no
  colour or finish limit ("No limit"), so it takes white with lead-free HASL.
- **Rails and fiducials, JLC's.** Standard asks edge rails and fiducials ("Necessary"; JLC's
  are 5 mm rails with 1 mm fiducials and 2 mm tooling holes [ds `JLCPCB-PCB-CAPABILITIES.pdf`,
  *Mouse bites Panel*]) and a single board of at least 70 × 70 mm: this one is 292.5 × 42.1
  (`fab/`'s `.gbrjob`), so it goes with rails added by JLCPCB, which widen it; whether JLC's
  rails alone reach 70 mm or it asks for a panel is the quote form's. At 292 mm long it is past
  the 250 × 250 mm panel JLC recommends, which the PCBA FAQ allows at the customer's risk of
  bending. The board carries no fiducials of its own; on rails it needs none.
- **The Extended-part count** (#17 D6) is moot: it mattered only under Economic PCBA.
- **The placement preview**: check it as the key boards' order sheet says
  (`hardware/boards/key-board-lh/README.md`, *Ordering it*, 5), including **where JLC's rails
  and tooling holes land**: on the rails, clear of the board's ground pour, the switch pads and
  the mounting holes. If JLC has put a tooling hole inside the board, ask for it on the rails
  instead.

**Through-hole tails** (owner, 2026-10-04, #8-11: "Trim length"; ADR 0017, *Amendment,
2026-10-04*). `fab/main-board-hand-assembly.csv`'s **Fit** column gives the length each hand
part's tails and their solder are cut to below the board's bottom face, computed by `pcb.py
render` from the `config/body.yaml` figures `layout.yaml` `hand_trim:` names, with the arithmetic
in the cell; a sheet with no Fit column was rendered before `hand_trim:` existed, so re-render
it (`pcb.py render`) before assembly. `J-MCU` (J1) and both `J-CHAIN` (J4, J5) stand over the grounded bottom plate:
their limit is `hardware.kb_spacer_l` (the board's bottom face above the plate) less
`boards.tail_clear` (the least air the body allows between a tail and what is under it).
`U-BUCK` (U5) is cut to `boards.tht_trim`. `J-UMB` (J6) stands over oak,
past the plate's end, and clears it as supplied (`mechanical/drc.echo`
*"through-hole tails under the main board clear of the bottom plate"*): no cut. The thumb
switches enter from below, so their tails are on the top face.

**Revision - the rule for every board.** A board's silkscreen and title block read `rev A`,
with its layout's date (`layout.yaml` `silk:`), until a board has been fabricated; the next
order is B. The letters in each board's *Revisions* table are design history only. The owner
decided it for this board on 2026-10-03 and for every board on 2026-10-04 (review #6-7: "Yes,
all rev A"; ADR 0020, *Amendment 9*); the key boards' pages cite this paragraph. `pcb.py check` fails a board whose title block or silkscreen has lost either (`check_title`, #33).

## Revisions

| Rev | Date | What changed | Where |
|---|---|---|---|
| — | 2026-09-29 | Schematic: the carrier circuits migrated to KiCad and placed with the thumb clusters and the interfaces' main-board parts. Not laid out | git history of this directory |
| A | 2026-09-30 | First layout by `tools/pcb.py` (`kind: main`): placed, four layers, planes and island, routed but for the connections under *Open* | `layout.yaml`, `main-board.kicad_pcb` |
| B | 2026-10-01 | Re-laid out on the merged sheets (`Q-INRUSH`, `INST_POS12` the layer-3 plane) and footprints (`J-MCU`, `J-UMB`, the LED's chamfer at pin 1); `U-BREATH` turned so its ports face the tail; decouplers to their ICs' power pins; the reference's feedback network stacked as its ring; routed by the tool's own router with layer directions and rip-up, Freerouting dropped (owner: "routing is super sloppy... similar horizontal and vertical layers"); `pcb.py check` passed then | `layout.yaml`, `main-board.kicad_pcb`, `docs/reference/tooling.md` §4 |
| C | 2026-10-01 | Re-laid out with fix rounds F1 (`U-BREATH` and `U-BUF` decoupling, `C201`-`C204`), F6 (`R44` at `REG-LT`'s `QH`) and F4 (`KS-33` 2.8 mm pads, by `pcb.py update-footprints --pads-resized`); `VS`'s caps turned so their `VS` pads share a row; all but one connection routed | `layout.yaml`, `main-board.kicad_pcb` |
| D | 2026-10-01 | `IO34` routed into `J-MCU` pin 14 by hand, `IO36`'s escape from pin 12 re-routed (*What the first layout settled*); `pcb.py check` passed then, to the 2026-10-01 outline; renders and `fab/` written | `main-board.kicad_pcb`, `fab/` |
| E | 2026-10-03 | Wave 3 (#8, #17, #19, #6): the full-width tail's outline; thirteen LEDs in one even row laid out for fourteen (ADR 0028's amendments); `C-STRIP-BULK` two 6.3 x 7.7 polymer cans (`C10`, `C44`); `J-MCU` off the row at the near edge, `HDR-SERVICE` to the tail corner (`config/body.yaml`); `R45`-`R47`, `C41`-`C43`, `U11` placed; the ADC's filter on an island grown to take it, `C6` at `U4`, the TVS at its connector, the buck's caps at the module; KS-33 holes 3.0 mm (ADR 0020 Amendment 8); the routing policy's free routing. Placed; routing waits for #23 | `layout.yaml`, `main-board.kicad_pcb` |
| F | 2026-10-04 | Wave 3, routed: the Matrix branch merged (#23: `C41` gone, `HDR-SERVICE` 1x3 in place, `J-MCU` pins 23/24 on no net, `C205`/`C206` the key registers' second decouplers); the breath pair drawn along the far edge with arcs round `H2`, `H4`, `H6`, `H8`, its guard traces and the layer-3 `AGND_INST` strip; the power block against the near edge; the rest by the router, `complete` and a few hand routes at `J-MCU`'s foot (`INST_5V_A` pin 17 to pin 3 and on to `U6`); `pcb.py check` passes; renders and `fab/` written | `layout.yaml`, `main-board.kicad_pcb`, `fab/`, `tools/pcb_route.py`, `tools/pcb_main.py`, `tools/pcb.py` |
| G | 2026-10-04 | Trace cleanup (#33; owner: *"not drastic changes ... pretty up the runs, get rid of unnecessary weaving and via usage and make sure analog circuits are the best they can be"*): no part moved; the analog block re-laid by hand on layer 1 (*The analog block*: `SENSOR_RAW` 6 vias to none, `REF_MINUS` and `REF_5V` 2 to none); every other unlocked signal run routed again where that came out shorter, straighter or with fewer vias, string-pulled to straight and 45-degree runs, loops and doubled copper taken out; the breath pair, its guards and arcs untouched; `pcb.py check` passes; renders and `fab/` written | `main-board.kicad_pcb`, `fab/` |
| H | 2026-10-04 | The planes stitched (#8-8; owner: *"add 2-3 now"*): `C45`–`C47` (`C-STITCH-12V`) on the power-entry sheet and placed at `J-MCU`, `J-UMB` and the analog end, each pad to its plane by its own via; nothing else moved | `power-entry-instrument.kicad_sch`, `main-board.kicad_pcb`, `fab/` |
| I | 2026-10-04 | Iron room (#34): the eight thumb keys' networks and the spare `sw-` network moved out from between their switch's pins (*What the first layout settled*), the nets they cut routed again by `complete` and cleaned as in G; `pcb.py check` now holds the room (`iron_room:`) | `layout.yaml`, `main-board.kicad_pcb`, `fab/`, `tools/pcb.py` |
| J | 2026-10-05 | Routing review #35 pass 2 (`docs/review/2026-10-04-main-board-routing/REPORT.md`, owner: *"slight detours in longer runs for no reason ... via transfers [not] actually needed"*): the five proven single-run fixes (R1-R5); the U8 / J5 fan-in re-laid as one group, `DEV_3V3` first on layer 1, then the key lines, the chain, the IO bus (R6-R11, R21: 82 -> 72 vias on those nets); `CHAIN_SHLD` over the top of J4 (R12) and shortened at J5 (R13); `IO36` from `R2` to `U1` with no via (R16); the overlapping ends joined (R18); the worst pad entries on their pad's centre (R19); the near-edge bus at one 0.8 mm pitch where local (R20); `C1`, `D5`, `D6` values to the sheets (owner: *"Yes, go ahead"*). #37: `J-MIDI` (`J7`) in the freed tail corner, `U12`, `FB3`/`FB4`, `R50`/`R51`, `R48`/`R49`; `U6` gates B and C on `IO6`/`IO2`. #39: `D4` (`D-USBOR`) out, the 5 V OR (`Q2`, `U13`, `C207`, `C208`) in its place on layer 1. No other part moved; the breath pair, its guards and the analog hand routes untouched | `main-board.kicad_pcb`, `layout.yaml`, `fab/` |
| K | 2026-10-07 | #45, board half (owner approved the layout): `J-UMB` (`J6`) on the centred etherCON axis (`pcb-geometry.echo` `J-UMB`); `J-MIDI` (`J7`) the side-entry S3B-PH-SM4-TB at `config/body.yaml` `midi.hdr_at`, turned so its mouth faces the tail, height key `JST_PH_S3B-PH-SM4-TB` (`layout.yaml` `heights:`). `D2`, `D3`, `C46`, `NT1` moved with `J-UMB`'s pins; the breath pair's `R38`/`R39`/`D5`/`D6` moved 5 mm, not 7 (7 put `R38` on `J7`'s fixing pad), `D5`/`D6` turned so each signal pad faces its pin; the pair's tails (`layout.yaml` `pairs:` `tails`) shortened with them and three guard stitching vias moved along their guards off `J7`'s pads - the coupled run, the guards' geometry and the planes untouched. `R41`, `R42` and `D21` off `J7`'s courtyard and `R38`'s place; `FB3`/`FB4` in line with `J7`'s pads, `U12` past its face in the corner the top-entry header left. Re-routed only `J6`'s and `J7`'s nets and what the moves cut (`MIDI_*_R`, the inrush gate, `DEV_3V3`'s run to `R40`): `UMBILICAL_POS12`, `DEV_3V3`, the gate, `MIDI_TIP_R` and `MIDI_RING` by hand, locked; the rest by `pcb.py finish` with a scratch `route_fence:` round the corner (without one its rip-up takes up locked copper's nets: Open). `pcb.py check` 0 errors on the scratch copy | `layout.yaml`, `main-board.kicad_pcb` |
| L | 2026-11-20 | Laid out again by hand (#48, ADR 0030): every part placed and every track and via written out in `main_layout.py`, no router. Both `J-CHAIN` headers turned with the key boards', `J-MCU` on the ribbon's new pin order. The analog block along its signal; the breath pair on layer 4 along the far edge in straight runs and 45-degree steps, no guard tracks; the LED data on the top face; soldered ground pins on relief spokes. `layout.yaml` no longer carries a placement or a routing order | `main_layout.py`, `main-board.kicad_pcb`, `layout.yaml`, `fab/` |
| M | 2026-11-20 | The first LED (`D8`) moved from over the Matrix ribbon to the row's tail-end place (owner, the same day; ADR 0028's amendment; `lighting.led_empty_slot`). The LED driver and its parts moved a step toward the mouth, `D3` and `C26` into the row between the driver and `D8`, and the tail end's lines were written out again: the 3V3 trunk and the first LED's two data lines in three lanes under the driver | `main_layout.py`, `main-board.kicad_pcb`, `fab/`, `config/body.yaml` |
| N | 2026-11-21 | Both `J-CHAIN` headers are vertical 2×5 headers (ADR 0017, *Amendment, 2026-11-21*; issue #49): new footprint where the body CAD stands each, straight under its key board's; each header's five lines, the chain trunk's ends and each hop's line redrawn to its pads. No other part moved and the analog block is untouched. `pcb.py check` passes. Not yet ordered | `main_layout.py`, `main-board.kicad_pcb`, `main-board.kicad_sch`, `layout.yaml` |
| O | 2026-11-21 | The LED row respaced (owner; ADR 0028's amendment of 2026-11-21): `D8` past the Matrix ribbon, `D9` before it at the same distance, `D9` to `D20` at one pitch to the mouth end (`lighting.led_tail_x`, `led_ribbon_x`, `led_pitch`). `J-MCU` is the vertical 2×12 header where the body CAD stands it (ADR 0018, *Amendment, 2026-11-21*; issue #49), and its fan-out is written out again: the odd row leaves toward the near edge and round the header's ends as before, the even row toward the far side. `U-REF-BREATH` (`U4`) turned a quarter turn off the mouth-end LED and the island's notch under it closed; `D20`'s capacitor north of it; the chain's three series resistors, the regulator's inductor and `C208` moved clear of `D9` and the header; the key combs and their taps moved off the LEDs they met. `pcb.py check` passes. Not yet ordered | `main_layout.py`, `main-board.kicad_pcb`, `layout.yaml`, `fab/`, `config/body.yaml` |
| P | 2026-11-21 | Copper cleanup, trace by trace (owner): `J-MCU`'s odd row leaves in short lanes hard under its pads, toward the tail on top and toward the mouth on the bottom, and no line goes round the header's end; the two register blocks stand closer to their chain headers; the bottom lanes run straight from the tail to the analog block and step there; every right angle with room for a diagonal has one. Then four more (owner): `R11` stands beside the LED driver's output, so that line is one short straight piece; the chain's return from `J-MCU` pin 24 turns once; the four lane lines turn once from under the header straight into their lanes, with `IO7` and `IO38` on vias between them; `C11` is turned round, so inductor, input capacitor and regulator are joined by one straight line. A last cold pass measured every run against its shortest 45-degree path: `C43` is turned round so the regulator's output goes straight up into it. The breath pair keeps to the far edge between the mounts, away from the LED row and the tail's digital lines (owner): its steps under the mounts are its only detours and they stay. No via stands in a pad any more (owner; ADR 0030, point 5): the three clamps' ground vias are just off their pads. `tools/pcb.py check`: 0 errors. |
| Q | 2026-11-22 | The hops from each key board into its thumb register get the third hop's resistor (owner, 2026-11-21; pre-fab review F1; issue #51; `key-chain-loom.md`, *The hop hold time*): `R52` at `J4` and `R53` at `J5`, each on the line from its header's pin 8, where that header's bead stood. Each resistor's register-side pad runs straight to its clamp's fourth channel (`U9`'s was spare; `U11`'s was on the header's side of the net), with the hop's via on that line and the line on under the register as before. Each bead moved a row toward the far edge; the right one is turned, pad 1 toward its 3V3 line, and its other pad's line turns back between the bead and the resistor. One via more a hop. The breath pair and the analog block are untouched (their tracks compared, identical). `tools/pcb.py check`: 0 errors. |
| R | 2026-11-22 | Pre-fab review fixes (issue #52, F1 to F5). `R54` and `R55` (`R-ADC-SER`, `breath-adc.md`, *The SPI branch*) stand on the top face a quarter of the way along the two SPI lanes to the ADC, each between two vias on its own lane, and the lanes west of them are `ADC_CLK` and `ADC_DIN`. The ADC's supply resistor `R47` has its own 3V3 track: a sixth bottom lane from a via on the top 3V3 line just past `J-MCU`'s rows to a via inside the analog block, so the key pull-ups' current shares only the first few millimetres from `J-MCU` pin 15 with it and none of the board's length. The six lanes stand a quarter of a millimetre nearer the near edge so the new one clears the U-bolt leg's keep-out, and 3V3's lane stands a via's room off them. `R56` (`R-RXD-SER`) is beside `J2`, in the line to its pin 2. `J-MCU` pin 6 is ground. `INST_5V_A` is 0.7 mm from `J-MCU` pin 2 past the resistor row and 0.8 mm from there to `Q2`. The breath pair and the analog nets are untouched (their tracks compared, identical). `tools/pcb.py check`: copper clean; its one error is the body CAD's board outline export, stale until the renders are rebuilt. |
| S | 2026-11-22 | Room at the pads, and the 3V3 lane wider (owner, 2026-11-21: lines that pass close to one pad moved off it where there is room, supply tracks wider where there is room; issue #52 W1, W2). Found by measuring every track against every pad of another net. Moved: the LED row's data lines under each next LED's unused pad, the two long key lines along the near edge, `J-MCU`'s bottom lanes off its soldered pins and the service lines beside its even row, the 3V3 loop at `U8`, both MIDI lines at `U12`, the 5 V line in its corridor between the resistor row and the chain's return, the 12 V turn at `D20`, `R54`'s line past `R55`. Left where they are: a line already midway between two pads or a pad and another line (`KEY_LT1` at `C13`, 3V3 between `U8`'s pins, the 5 V line between `R36` and `R37`, `LED_D10`), the 3V3 line under `R1` to `R3` (a lane's width from `IO36`), and everything in the analog block. The 3V3 lanes keep their widths: the ADC's own lane is in a bundle with no room and its resistance is small beside `R-ADC-VDD`, and the key pull-ups' lane, widened for most of its length in this pass, was put back to one width the next morning (owner, 2026-11-22: no track that steps in width). The breath pair and the analog nets are untouched (their tracks compared, identical). `tools/pcb.py check`: 0 errors. |
| T | 2026-11-22 | No needless steps, one exit from every key switch, and pins entered through their centres (owner, 2026-11-22; issue #52). The 5 V line and the 12 V entry are each one width for their whole run. `ADC_DIN`'s bottom line runs straight to its via beside `U2` pin 5, with no step at its end. Every key switch's line leaves its pin straight for `KEY_EXIT` in `main_layout.py`, measured from the pin's centre, before its first turn; it is the key boards' neck length, so the three boards agree. The far row's four then step once at 45 degrees to pass between the switch's ground pin and its centre post, and `SW3`, `SW5` and `SW7` already ran straight for longer. 12 V leaves `J6` pin 3 on one 45 degree line from the pin's centre. The two chain lines into `J4` and `J5` pin 6 arrive level with the pin's centre, and their small step is inside the clamp's pad. `MIDI_TIP` runs level from `FB3`. The chip-select line has one entry at its pull-up `R45`: pad, via and the line on to `U2` pin 1 stand in a row, where two tracks used to meet in the pad. Left as they are: the ground tie's short 45 degree line at `NT2`, which takes its via off the analog island, and the three staggered vias beside `U2`, one for each of three lines that arrive side by side underneath. |
| U | 2026-11-22 | How tracks meet, now a check (`check_joints`, `docs/reference/tooling.md` §4; owner, 2026-11-22; issue #52), and what it found here. Chip-select's via stands level with `R45` pin 2 and the line runs on straight past it before it turns. The four vias at `R54` and `R55` are each entered level, the step onto the lane half a millimetre away and no longer inside the via's ring. `R12`'s 3V3 via stood in the pad and now stands beside it, level with it. The 3V3 via under `R14` is on its line, and `R37`'s is reached straight down from the pad. The analog ground via at `D1` is on one 45 degree line from the pad. `VS` reaches `C202` by a T where it was a fork. Six square corners are cut at 45 degrees: 3V3's lane end under `U7`, `ADC_VDD` at `C3`, 12 V at `R6`, the 5 V switch's input at `U13`, and the right bead's line at `FB2`. `R8` stands level with `U3` pin 2, so the buffer's inverting input runs straight through the pin's pad into it, and `ADC_IN` is clear of `R5`'s pad before it turns. The breath pair is as it was. |
