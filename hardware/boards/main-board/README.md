# Main board — `main-board`

The one long board at the thumb level (ADR 0017). It carries:
- the thumb switches and both thumb registers;
- the carrier's circuits: the breath sensor's reference, buffer and ADC, power
  entry, the LED drive and the LED row (ADR 0028), the service header and the
  SPI egress;
- the key chain's two ribbon headers;
- `J-UMB`, where the umbilical arrives from the etherCON's adapter (ADR 0021).

The Matrix is on the lid and reaches it by a ribbon into `J-MCU`. The board
is part of the cassette (ADR 0025): every one of its mounts stands on the one
bottom plate, and eight of them are columns up to the key boards (ADR 0022 as
amended).

> **Status (wave 3, 2026-10-03): re-placed to its current design and NOT YET ROUTED.**
> The full-width tail's outline (ADR 0021 amendment), the fourteen LEDs in one even row
> (ADR 0028 amendment of 2026-10-03), `J-MCU` turned off the row to the near edge
> (`boards.mcu_conn_at`), the wave-2 and wave-3 parts (`R45`–`R47`, `C41`–`C43`, `U11`)
> and the review fixes (*Wave 3*, below) are placed (`layout.yaml`, `pcb.py layout
> --no-route`). **Routing waits for the Matrix branch's `J-MCU` / `J-MCU-KB` pair (#23)**,
> which may move `J-MCU` again; until it is routed `pcb.py check` fails on every
> unrouted connection and `kicad.py check` with it, and `fab/` and the renders are the
> last routed board's (rev D) - stale, and not to be ordered from. The sheets are the
> source and pass KiCad's ERC. Every part has its footprint and bought part on its
> symbol (`Footprint`, `Manufacturer`, `MPN`, `LCSC`, `Assembly`), from selections whose
> datasheets are banked, and every machine-placed part with a polarity or more than two
> pads has its JLC rotation (`hardware/lib/jlc-rotation.csv`). The board's outline and
> every placement the body fixes are exported (`mechanical/export/main-board.dxf`, the
> `main` entries in `mechanical/export/pcb-geometry.echo`). The thumb switch positions
> are provisional until M2/M3, as the key boards' are.

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
| `layout.yaml` | **First-layout input** for `tools/pcb.py layout` (`kind: main`): placement of everything the body CAD does not place, the stackup, planes, the `AGND_INST` island and its tie, the breath pair, net classes, keep-outs, heights. Once the board exists it records how the first layout was made (`docs/reference/tooling.md` §4, *The main board*) |
| `main-board.kicad_pcb`, `main-board.kicad_pro` | **The PCB, source from now on** — written once by `layout`, edited in KiCad after; `pcb.py check` holds it to the sheets, the body CAD and `layout.yaml` |

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
| C41 | `C-EN` | service-uart |
| C13, C14 | `C-DECOUPLE-165` | REG-LT, REG-RT |
| C3, C6–C8, C12, C204 | `C-DECOUPLE-CARRIER` | breath-adc, breath-excitation-reference, led-strip-drive |
| C9 | `C-FB-REF` | breath-excitation-reference |
| C40 | `C-INRUSH-GD` | power-entry-instrument |
| C39 | `C-INRUSH-GS` | power-entry-instrument |
| C15–C24 | `C-KEY` | LT1, LT2, LT3, LT4, RT1, RT2, RT3, RT4, sw+, sw- |
| C25–C38 | `C-LED` | led-strip-drive |
| C4, C5 | `C-REF-OUT` | breath-excitation-reference |
| C203 | `C-SENSOR-OUT` | breath-sense-link |
| C201 | `C-SENSOR-VS-BULK` | breath-sense-link |
| C202 | `C-SENSOR-VS-HF` | breath-sense-link |
| C10 | `C-STRIP-BULK` | power-entry-instrument |
| D21 | `D-INRUSH-RST` | power-entry-instrument |
| D7–D20 | `D-LED` | led-strip-drive |
| D1 | `D-REF-CLAMP` | breath-excitation-reference |
| D2 | `D-REVSHUNT` | power-entry-instrument |
| D5, D6 | `D-TVS-BREATH` | breath-sense-link |
| D3 | `D-TVS-PWR` | power-entry-instrument |
| D4 | `D-USBOR` | power-entry-instrument |
| FB1, FB2 | `FB-CHAIN` | root |
| J2 | `HDR-SERVICE` | service-uart |
| J4, J5 | `J-CHAIN` | root |
| J1 | `J-MCU` | carrier |
| J6 | `J-UMB` | root |
| L1 | `L-BUCK-IN` | power-entry-instrument |
| NT2 | `NT-AGND` | power-entry-instrument |
| NT1 | `NT-DIG` | carrier |
| Q1 | `Q-INRUSH` | power-entry-instrument |
| R47 | `R-ADC-VDD` | breath-adc |
| R5 | `R-ADCDIV-L` | breath-adc |
| R4 | `R-ADCDIV-U` | breath-adc |
| R34–R36 | `R-CHAIN-SER` | root |
| R45 | `R-CS-PULL-ADC` | breath-adc |
| R40 | `R-CS-PULL-INST` | carrier |
| R8 | `R-FB-REF` | breath-excitation-reference |
| R9 | `R-FBX-REF` | breath-excitation-reference |
| R44 | `R-HOP-SER` | root |
| R42 | `R-INRUSH-G` | power-entry-instrument |
| R43 | `R-INRUSH-GD` | power-entry-instrument |
| R41 | `R-INRUSH-GS` | power-entry-instrument |
| R7 | `R-ISO-REF` | breath-excitation-reference |
| R12, R14, R16, R18, R20, R22, R24, R26, R28, R30, R32, R33 | `R-KEY-PU` | LT1, LT2, LT3, LT4, RT1, RT2, RT3, RT4, sw+, sw-, FREE1, FREE2 |
| R13, R15, R17, R19, R21, R23, R25, R27, R29, R31 | `R-KEY-SER` | LT1, LT2, LT3, LT4, RT1, RT2, RT3, RT4, sw+, sw- |
| R10 | `R-LED-PD` | led-strip-drive |
| R11 | `R-LED-SER` | led-strip-drive |
| R6 | `R-REF-IN` | breath-excitation-reference |
| R38, R39 | `R-SER-BREATH-INST` | breath-sense-link |
| R37 | `R-SER-TERM` | root |
| R1–R3 | `R-SPI-SER` | carrier |
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
| U1 | `U-TVS-SPI` | carrier |

## Open, and what decides each

The first layout is `tools/pcb.py layout hardware/boards/main-board` (`kind:
main`; `docs/reference/tooling.md` §4, *The main board*). What it does not yet
finish, and every other open item:

| Item | Decided by |
|---|---|
| **The LED row's places** are the body CAD's (`pcb-geometry.echo` `main` `led`, *"LED row on the main board"* in `mechanical/drc.echo`): fourteen on the centreline at one pitch with equal margins to the board's ends (ADR 0028 amendment, 2026-10-03), `D7` (LED 1, first on the data line) at the tail end, `D20` at the mouth end; each `C-LED` 4.5 mm across (`layout.yaml` `led_caps:`). Reshuffled if the diffusion test moves the count. **The WS2815B-V1's chamfer marks pin 1 (NC)**; the footprint's silk triangle marks the chamfer, and JLCPCB's own footprint agrees (`hardware/lib/README.md`) | Layout; the side-light diffusion test; the first order's placement preview |
| **Passives may go on the underside** (owner, 2026-09-29). The underside faces the grounded bottom plate, `hardware.kb_spacer_l` below it, over the board's whole length since the cassette (ADR 0025). At `boards.board_clear` that leaves no room for a part (`mechanical/drc.echo` *"main board underside room over the bottom plate"*), so an underside part needs a **window cut through the bottom plate** under it, down to the oak (the second figure on that line), and must be clear of the thumb switches' housings, pins and the mounts' spacers. Through-hole tails face the plate too: the next row. The thumb switches are already underside parts | The layout; each window goes into the bottom plate's outline in the body CAD |
| **Through-hole tails under the board** (2026-10-01): every part with plated through-hole pins pokes its tails out of the underside toward the grounded bottom plate — `J-CHAIN` ×2, `J-MCU`, `J-UMB`, `HDR-SERVICE` and `U-BUCK` (`config/body.yaml`, *THE THROUGH-HOLE TAILS UNDER THE MAIN BOARD*, says which and why these). `mechanical/drc.echo` *"through-hole tails under the main board clear of the bottom plate"* tests each against what is under it, and the body model draws them for `clash.txt`. `J-CHAIN`'s and `J-MCU`'s clear the plate as supplied. The plate ends short of `J-UMB`'s tail row, and has a window to the oak under `HDR-SERVICE` and under the regulator block (`pcb-geometry.echo` `main` `plate`). **`U-BUCK`'s pins are cut to `boards.tht_trim` below the board after soldering** — as supplied they reach the oak even through the window. `HDR-SERVICE` stands where `boards.service_hdr_at` puts it and `U-BUCK` inside the regulator block, or the window moves with them | A part moved off its window: move `boards.service_hdr_at` (or the block) and rebuild the body CAD; a new through-hole part: add it to `tht_tails` in `mechanical/cad/woody_body.scad` |
| **The references with no clear place on the silkscreen** stay on the fabrication layer; the layout names them when it writes the board | Hand-placed in KiCad, or room made round them |
| **The revision letter on the silkscreen** reads `rev A  2026-09-30` (`layout.yaml` `silk:`, the `.kicad_pcb`), while the table below runs to D | **Decided (owner, 2026-10-03): this table's letters are design iterations only; the silkscreen reads `rev A` on the first board fabricated**, so it stays A until a board is made and the next order is B | First order |
| **Routing (wave 3)**: placed, not routed (*Status*). `J-MCU` is at `config/body.yaml` `boards.mcu_conn_at`, the one figure the Matrix branch's `J-MCU` / `J-MCU-KB` pair sets (#23); at the value both branches carry, `mechanical/drc.echo` *"columns vertical"* asks column mount 7 (x 247.7, y 11.1) to move 0.8 mm - the pair's study settles it. Then `pcb.py route`, `check`, `render` | The Matrix branch's merge (#23), then routing |
| **`INST_POS12`–`PWR_GND` stitching capacitors** near `J-MCU`, `J-UMB` and the analog end (#8-8): signals change layers between the two planes' references more than 20 mm from the nearest `C-LED`. New parts on the sheets, so the owner's | Owner (a sheet change) |
| **`C203` at `U10` pin 4** (MPXV4006DP Fig. 3): pin 4 is the corner of `U10`'s own courtyard, at the mouth and far edges, so no 0805 can stand within 3 mm of it on the top face; `C203` stands at `U3`'s input, the net's other end, as before. Nearer needs an underside part and a bottom-plate window under it | Owner |
| **Through-hole tails' margin over the grounded plate** (#8-11: `J-CHAIN` 0.75 mm, `J-MCU` 0.8 mm): an insulating sheet on the plate under the tail fields, or a trim length on the hand-assembly sheet | Owner, before assembly |
| **Standard or Economic PCBA, white mask** (#17 D1): *Ordering it*, below | Owner, before the order |
| **The umbilical adapter** (`PCB-UMB-ADAPTER`) is a separate small board: its schematic is [`../umb-adapter/`](../umb-adapter/README.md), not laid out | With this board's layout |

What the first layout settled, and where it is held:
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
- **The regulator block holds `U-BUCK` alone** (a rule area), `C-STRIP-BULK`,
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
- **`U-BREATH`'s decoupling** (fix round F1; wave 3): `C202` (10 nF), `C201` (1 µF) and `C8`
  (100 nF) on `VS` in that order from pin 2 - `C202` at the nearest place `U10`'s own
  courtyard leaves, 6.3 mm - inside the island; `C203` on `SENSOR_RAW` at `U-BUF`'s input,
  since pin 4 is walled in by the sensor's own courtyard (*Open*); `C204` at `U-BUF`'s `V+`.
- **`U-ADC`'s reference filter** (owner, 2026-10-03; #8-3): `R47` feeds `ADC_VDD` from
  `DEV_3V3`; `C3` (100 nF) with its `ADC_VDD` pad straight over pin 8, `C42` (22 µF) and `C2`
  (10 µF) on a short `ADC_VDD` run beside it, every return into the island under `U-ADC`,
  a few mm from pin 4's own via; `R45` (`CS_ADC`'s pull-up) on a stub from pin 1.
- **`U-REF-BREATH`'s input** (#8-7): `C6` (100 nF) across pins 2 and 4, `C4` (10 µF) above
  pin 2 between `U4` and `U3`.
- **`R44`** (`R-HOP-SER`, fix round F6) at `REG-LT`'s `QH`, pin 9 (`layout.yaml` `parts:`).
- **`Q-INRUSH` and its gate network** in the tail strip above the LED row, between LED2 and
  LED1, where the corner LED stood for a day; its drain meets the layer-3 plane by three
  vias (`fanout_count:`).
- **The power paths carry no via** (#8-6): `UMBILICAL_POS12`, `BUCK_IN`, `BUCK_A_OUT` and
  `INST_5V_A` route on layer 1 only (a net class's `layers:`), 0.5 mm; where a power part
  meets a plane it does so by two or three vias (`Q-INRUSH`'s drain, the clamps' and bulk
  capacitors' returns, `L-BUCK-IN`).
- **The clamps at their connector** (#8-9): `D-TVS-PWR` (D3) beside `J-UMB`'s pins 3 and 6,
  `D-REVSHUNT` (D2) beside it; the buck's caps at the module (#8-7): `C11` at `U5`'s input,
  `C43` (owner, 2026-10-03) at its output, returned to its GND pin.
- **`U11`** (`U-TVS-CHAIN`) at `J5`, as `U9` at `J4`, its pin 2 to `PWR_GND` by its own via.
- **The routing policy** (owner, 2026-10-03; `docs/reference/tooling.md`): free 45° routing
  on both outer layers, no layer direction anywhere - no region of this board is a bus
  crossing that needs one. The analog block's nets prefer layer 1, over the island
  (`layer_cost:`; #8-5: layer 4's reference is the LEDs' +12 V plane), and take layer 4
  only where the block's density leaves no other way (VS across the feedback ring,
  REF_5V round U4). The breath pair is guarded: every other net the router lays keeps
  0.75 mm (3W) off its legs (`pairs:` `guard:`; #8-4).

## Ordering it — JLCPCB

**Not to be ordered until it is routed and `pcb.py check` and `kicad.py check` pass**: then
`fab/` is this board. JLC's limits are from the banked pages in `datasheets/fab/`; the
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
| Delivery format | **Owner's choice** with the PCBA type (below) | |
| PCBA side | Top | Every machine part is on the top face; the thumb switches (underneath) are fitted by hand |
| Assembly | `fab/main-board-bom-jlc.csv`, `-cpl-jlc.csv`; `-hand-assembly.csv` for the rest | One BOM row per LCSC number, its MPN as the Comment (#17 D5) |

**The PCBA type is the owner's (#17 D1)** [ds `datasheets/fab/JLCPCB-PCBA-CAPABILITIES.pdf`]:
- **Economic PCBA** offers 4-layer boards in **green only** (its *PCB Specs for Economic PCB
  Assembly* table: the 4-layer rows - 1.0, 1.2, 1.6 mm - are green; white appears only in the
  1.6 mm *Red/White, Leaded HASL* row of the 2-layer group; the table's layer column does not
  render in the banked copy, so the grouping is read from the rows' thicknesses). So this
  board as specified - white, lead-free HASL, 4 layers - is **not an Economic board**, and
  white with leaded HASL is not offered at 4 layers either.
- **Standard PCBA** has no colour or finish limit ("No limit"), so it **does** take white
  with lead-free HASL. It asks **edge rails and fiducials** ("Necessary"; JLC adds 5 mm
  rails with 1 mm fiducials and 2 mm tooling holes [ds `JLCPCB-PCB-CAPABILITIES.pdf`,
  *Mouse bites Panel*]) and a **single board of at least 70 × 70 mm**: this one is 292.4 ×
  42.0, so it goes as a panel or with rails that widen it - and at 292 mm long it is past the
  250 × 250 mm panel JLC recommends, which the PCBA FAQ allows at the customer's risk of
  bending. The board carries no fiducials of its own; on rails it needs none.
- **Or green mask** under Economic, which gives up ADR 0028's white reflector on this board.

**Revision.** The silkscreen reads `rev A` with the layout's date (`layout.yaml` `silk:`): the
owner decided (2026-10-03) that the first board fabricated is A, whatever the design
iterations below are lettered.

## Revisions

| Rev | Date | What changed | Where |
|---|---|---|---|
| — | 2026-09-29 | Schematic: the carrier circuits migrated to KiCad and placed with the thumb clusters and the interfaces' main-board parts. Not laid out | git history of this directory |
| A | 2026-09-30 | First layout by `tools/pcb.py` (`kind: main`): placed, four layers, planes and island, routed but for the connections under *Open* | `layout.yaml`, `main-board.kicad_pcb` |
| B | 2026-10-01 | Re-laid out on the merged sheets (`Q-INRUSH`, `INST_POS12` the layer-3 plane) and footprints (`J-MCU`, `J-UMB`, the LED's chamfer at pin 1); `U-BREATH` turned so its ports face the tail; decouplers to their ICs' power pins; the reference's feedback network stacked as its ring; routed by the tool's own router with layer directions and rip-up, Freerouting dropped (owner: "routing is super sloppy... similar horizontal and vertical layers"); `pcb.py check` passed then | `layout.yaml`, `main-board.kicad_pcb`, `docs/reference/tooling.md` §4 |
| C | 2026-10-01 | Re-laid out with fix rounds F1 (`U-BREATH` and `U-BUF` decoupling, `C201`-`C204`), F6 (`R44` at `REG-LT`'s `QH`) and F4 (`KS-33` 2.8 mm pads, by `pcb.py update-footprints --pads-resized`); `VS`'s caps turned so their `VS` pads share a row; all but one connection routed | `layout.yaml`, `main-board.kicad_pcb` |
| D | 2026-10-01 | `IO34` routed into `J-MCU` pin 14 by hand, `IO36`'s escape from pin 12 re-routed (*What the first layout settled*); `pcb.py check` passed then, to the 2026-10-01 outline; renders and `fab/` written | `main-board.kicad_pcb`, `fab/` |
| E | 2026-10-03 | Wave 3 (#8, #17, #19, #6): the full-width tail's outline; fourteen LEDs in one even row (ADR 0028 amendment); `J-MCU` off the row at the near edge, `HDR-SERVICE` to the tail corner (`config/body.yaml`); `R45`-`R47`, `C41`-`C43`, `U11` placed; the ADC's filter on an island grown to take it, `C6` at `U4`, the TVS at its connector, the buck's caps at the module; KS-33 holes 3.0 mm (ADR 0020 Amendment 8); the routing policy's free routing. Placed; routing waits for #23 | `layout.yaml`, `main-board.kicad_pcb` |
