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

> **Status (wave 3, 2026-10-04): re-laid out to its current design and ROUTED (rev I: traces cleaned up #33, planes stitched #8-8, iron room #34);
> `pcb.py check` passes.** The full-width tail's outline (ADR 0021 amendment), thirteen
> LEDs in one even row, its tail-end place empty (ADR 0028's amendments of 2026-10-03),
> `J-MCU` turned off the row to the near edge (`boards.mcu_conn_at`), the wave-2 and
> wave-3 parts and the review fixes (*Wave 3*, below) are placed, on the Matrix branch's
> merged sheets (#23: `HDR-SERVICE` 1x3, `J-MCU` pins 23/24 on no net, programming by
> USB only). The breath pair runs the far edge with its guards and strip (*The breath
> corridor*). `fab/` and the renders are this board's. The sheets are the
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
| D21 | `D-INRUSH-RST` | power-entry-instrument |
| D8–D20 | `D-LED` | led-strip-drive |
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
| **The LED row's places** are the body CAD's (`pcb-geometry.echo` `main` `led`, *"LED row on the main board"* in `mechanical/drc.echo`): fourteen places on the centreline at one pitch with equal margins to the board's ends and thirteen LEDs in them from the mouth end, the tail-end place empty (ADR 0028's amendments of 2026-10-03), `D8` (LED 1, first on the data line) at the tail end, `D20` at the mouth end (`D7` / `C25` went with the removed LED); each `C-LED` 4.5 mm across (`layout.yaml` `led_caps:`). Reshuffled if the diffusion test moves the count. **The WS2815B-V1's chamfer marks pin 1 (NC)**; the footprint's silk triangle marks the chamfer, and JLCPCB's own footprint agrees (`hardware/lib/README.md`) | Layout; the side-light diffusion test; the first order's placement preview |
| **Passives may go on the underside** (owner, 2026-09-29). The underside faces the grounded bottom plate, `hardware.kb_spacer_l` below it, over the board's whole length since the cassette (ADR 0025). At `boards.board_clear` that leaves no room for a part (`mechanical/drc.echo` *"main board underside room over the bottom plate"*), so an underside part needs a **window cut through the bottom plate** under it, down to the oak (the second figure on that line), and must be clear of the thumb switches' housings, pins and the mounts' spacers. Through-hole tails face the plate too: the next row. The thumb switches are already underside parts | The layout; each window goes into the bottom plate's outline in the body CAD |
| **Through-hole tails under the board** (2026-10-01): every part with plated through-hole pins pokes its tails out of the underside toward the grounded bottom plate — `J-CHAIN` ×2, `J-MCU`, `J-UMB`, `HDR-SERVICE` and `U-BUCK` (`config/body.yaml`, *THE THROUGH-HOLE TAILS UNDER THE MAIN BOARD*, says which and why these). `mechanical/drc.echo` *"through-hole tails under the main board clear of the bottom plate"* tests each against what is under it, and the body model draws them for `clash.txt`. `J-CHAIN`'s and `J-MCU`'s clear the plate as supplied. The plate ends short of `J-UMB`'s tail row, and has a window to the oak under `HDR-SERVICE` and under the regulator block (`pcb-geometry.echo` `main` `plate`). **`U-BUCK`'s pins are cut to `boards.tht_trim` below the board after soldering** — as supplied they reach the oak even through the window. `HDR-SERVICE` stands where `boards.service_hdr_at` puts it and `U-BUCK` inside the regulator block, or the window moves with them | A part moved off its window: move `boards.service_hdr_at` (or the block) and rebuild the body CAD; a new through-hole part: add it to `tht_tails` in `mechanical/cad/woody_body.scad` |
| **The references with no clear place on the silkscreen** stay on the fabrication layer; the layout names them when it writes the board | Hand-placed in KiCad, or room made round them |
| **`C203` at `U10` pin 4** (MPXV4006DP Fig. 3): pin 4 is the corner of `U10`'s own courtyard, at the mouth and far edges, so no 0805 can stand within 3 mm of it on the top face; `C203` stands at `U3`'s input, the net's other end, as before. Nearer needs an underside part and a bottom-plate window under it | Owner |
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
- **`Q-INRUSH` and its gate network** by `J-UMB`, inboard of the breath pair's hop down
  (*The breath corridor*), so `UMBILICAL_POS12` reaches it from pin 3 without crossing the pair;
  its drain meets the layer-3 plane by three vias (`fanout_count:`).
- **The power paths carry no small via** (#8-6): `UMBILICAL_POS12`, `BUCK_IN`, `BUCK_A_OUT`
  and `INST_5V_A` route on layer 1, 0.5 mm, layer 4 costing them twenty times as much
  (a net class's `layer_cost:`); where one must change layers - the 5 V crossing the
  LED row or the chain lines - it does so through one
  1.0 / 0.6 mm via (a class's `via:`), not the signals' 0.3 drill; where a power part
  meets a plane it does so by two or three vias (`Q-INRUSH`'s drain, the clamps' and bulk
  capacitors' returns, `L-BUCK-IN`).
- **The clamps at their connector** (#8-9): `D-TVS-PWR` (D3) beside `J-UMB`'s pins 3 and 6,
  `D-REVSHUNT` (D2) beside it; the buck's caps at the module (#8-7): `C11` at `U5`'s input,
  `C43` (owner, 2026-10-03) at its output, returned to its GND pin.
- **Soldering-iron room round the hand-soldered pads** (#34; `layout.yaml` `iron_room:`, held by
  `pcb.py check`): every other part's courtyard 2.0 mm from a thumb switch's pin pads on the top
  face, where they are soldered, and 1.5 mm from `U10`'s. Each switch's key network (its
  `R-KEY-PU`, `C-KEY`, `R-KEY-SER`) stood between the switch's own pins, touching them, so each
  moved as one group, out of the pins' way to the nearest clear place, routed again: `LT1`
  +12.0 / 0 mm (x / y), `LT2` +9.25 / +11.75, `LT3` -12.0 / -4.25, `LT4` +7.5 / +7.75, `RT1`
  -7.5 / -7.75, `RT2` +11.25 / +11.75, `RT3` -11.0 / -0.75, `RT4` +7.5 / +8.25, spare `sw-`
  +11.0 / -3.0. **Not met, and why** (`iron_room:` `except:`, each with its reason). **Owner, 2026-10-04,
  in the working chat:** the networks stay where they moved (*"Keep moved"*); `SW2` and `SW6`
  beside their far mounts' nuts (`H2`, `H6`, 1.32 mm) and `SW8` beside `J5` (0.01 mm), all placed
  by the body CAD, are **accepted for rev A** (the key layout is final for it) and checked on the
  boards in hand. **`U10` beside `R7` and `U3`: the owner, 2026-10-04, accepted the sensor's
  iron room after the correction below - *"Keep it, solder carefully"*.** Measured pad to pad:
  `U10` pin 5 to `R7` pad 2 0.80 mm; pins 5-8 to `U3`'s pin-1 row 1.59 mm (courtyards 0.28 and
  0.86 mm). The near pins are `U10`'s own no-connect row 5-8, its mechanical joints, and they
  face `R7` and `U3`; pins 1-4 (NC, VS, GND, Vout) are the far-edge row with open room. `R7` and
  `U3` are machine-fitted, so they are on the board before `U10`. A fine tip's straight line
  (0.4 mm wide, from each pin's outer end, 0.3 mm off every other pad) is clear for pin 8 from
  straight down the board, for pins 6 and 7 within about 15 degrees of that, and for pin 5 from
  the mouth end or about 30 degrees to it. The hand-assembly sheet's Fit column (`U-BREATH`'s
  `Fit` field) says how: tip size, tape, pin by pin.
  `layout.yaml` `networks:` still records the first layout's pattern between the pins.
- **The planes stitched** (#8-8; owner, 2026-10-04, in the working chat: *"add 2-3 now"*):
  `C-STITCH-12V` from `INST_POS12` to `PWR_GND` at `J-MCU` (`C45`), `J-UMB` (`C46`) and the
  analog end (`C47`, on `PWR_GND` beside the island), each pad to its plane by its own via
  (`power-entry-instrument.md` §2, *Plane stitching*).
- **`U11`** (`U-TVS-CHAIN`) at `J5`, as `U9` at `J4`, its pin 2 to `PWR_GND` by its own via.
- **The routing policy** (owner, 2026-10-03; `docs/reference/tooling.md`): free 45° routing
  on both outer layers, no layer direction anywhere - no region of this board is a bus
  crossing that needs one. The analog block's nets prefer layer 1, over the island
  (`layer_cost:`; #8-5: layer 4's reference is the LEDs' +12 V plane). Since the trace
  cleanup (#33) two analog legs touch layer 4 besides the breath pair. `VS`, in two short
  hops - over `SENSOR_RAW` below the sensor and under `REF_5V` in `U3`'s belly - because
  `VS` must reach both `R7` and `R8` from the sensor's side of the `SENSOR_RAW` run (*The
  analog block*, below). And `SENSOR_BUFFERED_OUT`'s branch to `R4`, from the pair's tail
  via, 12.7 mm on layer 4 over `INST_POS12`: a layer-1 path exists only through
  `SENSOR_RAW`, `REF_5V` and `REF_VIN`, all locked hand routes. It is acceptable because
  the net there is the buffer's output - driven, low impedance - not the sensor's node; the
  owner accepted it on 2026-10-04 (review #35, R17: *"Accept, fix the README"*). The
  breath pair is guarded: every other net the router lays keeps 0.75 mm (3W) off its
  legs (`pairs:` `guard:`; #8-4).
- **The analog block** (#33, hand routes, locked so `pcb.py finish` and `rescue` leave
  them): every net of it runs on layer 1 over the `AGND_INST` island on layer 2 but `VS`'s
  two hops.
  - `SENSOR_RAW`, the sensor's output: one layer-1 run, no via, from `U10` pin 4 down
    between `U10`'s unconnected pads 6 and 7 into `U3`'s belly and pin 5, then on to `C203`
    (it had six vias and ~10 mm on layer 4, half of it over the +12 V plane).
  - `REF_MINUS`, the buffer's inverting input: from `U3` pin 2 straight down the gap between
    the feedback column (`R7`, `R9`, `C9`, `R8`) and `U3`, to `C9` and `R8`; no via.
  - `VS`: `R7` to `R8` down `U3`'s belly beside `SENSOR_RAW`, one hop under `REF_5V`, and
    up the column's side to `R8` pin 1; from `R7` to the sensor and its capacitors, one hop
    over `SENSOR_RAW`. `REF_5V` and `REF_VIN` all on layer 1, no via.
  - Checked, unchanged: `ADC_IN` (`R4`/`R5`/`C1` to `U-ADC` pin 2), `ADC_VDD` (`R47`, `C2`,
    `C42`, `C3`), `BUF_OUT`, `AC_FB_MID` - layer 1, no via, wholly over the island; no
    digital or LED net within 1 mm of any analog net on its layer.
- **The breath corridor** (owner, 2026-10-03: *"Main board, analog breath should not run
  under LEDs down the length"*, then *"the analog path should just be routed along the
  top. Not the bottom is crossing the board twice. Unneedingly"*; `layout.yaml` `pairs:`,
  `islands:`). The top of the board's plots is its **far edge**, where the sensor stands.
  The breath signal and its `AGND` leg run as one guarded pair on layer 4:
  - **One hop up at the mouth**, from the buffer `U3` (mid-board) at x 18.8 to the far
    edge, beside the sensor `U10` and clear of LED13's courtyard.
  - **Along the far edge** (y 47.3) to x 289.5, round each far column mount (`H2`, `H4`,
    `H6`, `H8`) by one concentric arc, r 5 mm about its centre, entered and left by 3 mm
    fillets (owner, 2026-10-04: *"curve around standoffs much better and be mirrored
    around them"*, then *"reduce all of them down to the same size"*). At `H2` and `H6` the
    far-row switch's leg pad (`SW2` / `SW6` pin 1) stands 6.2 mm from the mount on its tail
    side, so the detour goes on round that pin, r 3 mm, joined by their common tangent,
    and back up to the edge between the switch's two pins with a 3 mm fillet - clear of
    the switch's 5.25 mm centre hole, which a sweep under both pins crossed (tried and
    withdrawn, 2026-10-04: `pcb.py check` now fails any copper within the hole clearance
    of an unplated hole or cut-out on any layer, and a drawn path is checked before it is
    laid). The same arc at every mount, asymmetric only there. The path is drawn, not searched
    (`pcb_route.route_pair_smooth`): the legs and guards are the same path offset, KiCad
    arcs, one spacing all the way. Layer 4, not 1: the far-row keys' T networks stand on
    layer 1 between the edge and their switch pins.
  - **One hop down** into the series resistors `R38` / `R39` at `J-UMB` pins 1 and 2.
  - **No crossing of the LED row, and nothing on the near edge.** Its reference is an
    `AGND_INST` strip cut out of layer 3 under the whole run and both hops (`strip:
    true`), so neither the LEDs' +12 V plane nor their return is under it.
  - **The power block moved to the near edge** to make room (`config/body.yaml`
    `boards.tall_side` near, `boards.tall_at_x`): the bulk pair `C10` / `C44`, `U5` in
    the regulator block, `C11`, `D4`, and `L1` above `H7`. Distances `[calc, body mm from
    the courtyards]`: the pair at y 47.3 (its outer guard at ~48.1) against the buck's
    switching loop (`U5`, `L1`, `C11`, all at y ≤ 21.7) is **over 24 mm** away, with the
    LED row between them; from the LEDs' courtyards, ~13 mm.
  - **Guard traces** (`pairs:` `guard_traces:`, `pcb_route.guard_traces`): an `AGND_INST`
    track each side of the coupled run, one clearance off the legs, stitched into the
    strip at least every 5 mm - about 540 mm of guard and ~97 vias. **Left with the 3W
    keep-off only** (0.75 mm, `guard:`), where there is no room for a guard with two
    stitching vias: two spans of 2.0 mm, on the exit fillets at `H4` and `H8`; `route`
    prints each one.
  - Moved for it: `R-CHAIN-SER` to the far side of the row where the block stood,
    `U-LVLSHIFT` and the LED data by LED1, `Q-INRUSH`'s network by `J-UMB`, `R-SPI-SER`
    between `J-MCU` and `J-UMB`. `J-MCU`'s SPI and IO lines never run beside the pair.

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
`U-BUCK` (U5) is cut to `boards.tht_trim`. `J-UMB` (J6) and `HDR-SERVICE` (J2) stand over oak,
past the plate's end and through a window, and clear it as supplied (`mechanical/drc.echo`
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
