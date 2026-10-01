# Left-hand key board — `key-board-lh`

The left hand's five keys (LH1–LH5) and their register. The board is held
under the key plate by the cassette's columns, one at each corner (ADR 0025,
ADR 0020 Amendment 7), and one IDC ribbon runs from it to
the main board (ADR 0017, amended). **This board is the project's worked
example.** Every other board is laid out, checked and ordered the way this one
is.

> **Status: orderable as a prototype, not as the instrument's board.** The
> five switch positions this board is built around are **provisional until
> M2/M3**. They come from `config/body.yaml` `layout.lh_gaps` (`nominal`) and
> `layout.lh_offsets` (`tbd`), which stand in until the ergonomic work of M2
> fills `config/key-layout.yaml`'s `x`/`y` (every one `null` on purpose), and
> ROADMAP M3 locks them: "nothing expensive gets cut before M3". An order
> before then is a bring-up board. It proves the circuit, the chain, the fab
> outputs and the assembly, and it can go on a mule. When a key moves, the
> switches, the plate cutouts and the outline all move, and the board gets a
> new revision (below).

What each circuit does, and why, is on its page:
- [`key-register`](../../cluster/key-register/key-register.md)
- [`key-switch-network`](../../cluster/key-switch-network/key-switch-network.md)
- [`key-marker-and-bits`](../../cluster/key-marker-and-bits/key-marker-and-bits.md)
- [`cluster-boards.md`](../../cluster/cluster-boards.md)
- the ribbon: [`key-chain-loom.md`](../../interfaces/key-chain-loom/key-chain-loom.md)

This page covers the board as a made thing.

## Files — what is source, what is generated

| File | What it is |
|---|---|
| `key-board-lh.kicad_sch` (+ the three circuit sheets it places) | **Source.** Every connection, and each part's identity: `Row`, `Pins`, `Manufacturer`, `MPN`, `LCSC`, `Assembly` (ADR 0019) |
| `key-board-lh.kicad_pcb` (+ `.kicad_pro`, which holds its design rules) | **Source**, once laid out: edit it in KiCad 9 |
| `layout.yaml` | The first layout's inputs, and the limits the board is held to. `networks:`, `parts:`, `silk:`, `route:`, `route_first:`, `standoff_footprint:`, `ground_net:` and `power_nets:` are read only by `pcb.py layout`. `rules:`, `fab:` and `connect_first:` are read by **every** `pcb.py check` too: the board's design settings must still say what they say, and each `connect_first` path must stay within its `max_mm` (below) |
| `board-netlist.yaml` | Exported from the sheets (`tools/kicad.py export`) |
| `*.sch.png`, `*.pcb-*.png` | Renders, recorded in `hardware/SHEETS.csv` |
| `fab/` | **Generated** by `tools/pcb.py render`, and recorded in the ledger against the board *and* the sheets. Never edit it by hand: `kicad.py check` fails on a stale file, and on any file in `fab/` that no tool wrote |

`key-board-lh.kicad_prl` (KiCad's per-user view state) is gitignored.

`fab/` holds:
- Gerbers: both coppers, pastes, silkscreens and masks, plus the edge.
- `key-board-lh-job.gbrjob`, which carries the stackup: thickness, finish, mask and silk colour.
- Two drill files, as JLCPCB takes them: `key-board-lh-PTH.drl` (plated: the switch pins, `J-CHAIN` and the vias) and `key-board-lh-NPTH.drl` (unplated: the switches' centre-pole holes and the four corner mount holes, which must stay unplated, ADR 0020). The drill sizes and their arithmetic are in `hardware/lib/README.md`.
- `key-board-lh-pos.csv`, KiCad's own placement export.
- For JLCPCB:
  - `key-board-lh-bom-jlc.csv` — the machine-placed parts, with LCSC numbers.
  - `key-board-lh-cpl-jlc.csv` — their placement.
  - `key-board-lh-hand-assembly.csv` — the parts fitted by hand.

### Rebuild and check

**Prerequisites:** KiCad 9 with its Python module (`pcbnew`), OpenSCAD for the
body CAD, `rsvg-convert`, and the three KiCad 3D models this board's renders
need. `sudo bash tools/setup-env.sh` installs all of them
(`docs/reference/tooling.md` §1). `pcb.py render` refuses to run without the
models rather than render a board with parts missing.

After editing **a circuit sheet**, rebuild everything that places it, in this
order. The same sequence is in `docs/reference/tooling.md` §3:

```
python3 tools/kicad.py export hardware/cluster/<circuit>     # each circuit sheet you edited -> its netlist.yaml
python3 tools/kicad.py export hardware/boards/key-board-lh   # the board -> board-netlist.yaml, ERC
python3 tools/kicad.py export hardware/boards/key-board-rh   # every other board that places the circuit
python3 tools/kicad.py render hardware/cluster/<circuit>     # sheet PNGs, for each of the above
python3 tools/kicad.py render hardware/boards/key-board-lh
python3 tools/kicad.py render hardware/boards/key-board-rh
python3 tools/pcb.py check hardware/boards/key-board-lh      # the layout against the sheets, the fab limits and the body CAD
python3 tools/pcb.py render hardware/boards/key-board-lh     # PCB renders and fab/ (refuses a board that fails check)
python3 tools/kicad.py check                                 # everything above is current; runs pcb.py check too
```

After editing **only the `.kicad_pcb`**, the last three lines are enough.

`pcb.py check` fails on any of these (`docs/reference/tooling.md` §4 has the
full list and the reasons):
- a DRC error **or warning**;
- a schematic-parity difference, or an unrouted connection;
- a design setting that no longer matches `layout.yaml` `rules:`/`fab:`, or
  **any** DRC test set to *ignore* that is not on `tools/pcb.py` `IGNORE_OK`
  (each entry there carries its reason);
- a silkscreen line or text under `fab:`'s minimums, a filled silk shape
  thinner than the minimum line, silk too near a pad's mask opening, silk on
  a via, or silk off the board (KiCad's DRC does not test these);
- a placed silkscreen mark under a part's body (its courtyard), on either
  side, where it could not be read with the part fitted;
- two tracks of one net meeting on one layer at under 90° (an acid trap),
  including a track that ends in the middle of another; a wedge whose apex a
  via or pad of the net fills is not one;
- a `layout.yaml` `connect_first:` connection with no track path of its own,
  or a longer one than its `max_mm` (the decoupler's return to the register's
  ground pin);
- the board's thickness or outline differing from the body CAD's;
- a switch, mount hole or `J-CHAIN` not where the body CAD puts it, or
  turned or on the wrong side;
- a mount hole (H1–H4) that is not NPTH at the body CAD's size, or any copper
  (track, via, pour or another part's pad), on either layer, inside its
  keep-out: the column standoff's and the spacer's footprint, each grown by
  `hardware.kb_mount_float`, plus `rules.clearance` (ADR 0020).

**What holds the owner's rule (every key's network placed the same way round
its switch) after the layout:** only the switches' positions. `layout`
places the networks from the one pattern and stops if any key's three KEY
pads are not the three nearest its T's junction; `check` holds each switch
where the body CAD puts it. Nothing re-checks the networks' own positions
once the `.kicad_pcb` is edited by hand.

`kicad.py check` also holds `J-CHAIN`'s pins to the ribbon's netlist
(`hardware/interfaces/key-chain-loom/netlist.yaml`).

`tools/pcb.py layout … --force` rebuilds the board from scratch, from
`layout.yaml` and the body CAD. It overwrites any hand edits, so run it only
while `layout.yaml` is still the record of the layout. If the router cannot
finish a net, it exits 1 and leaves the existing board as it was.
`docs/reference/tooling.md` §4 covers the tools.

### Making the next board from this one

The right-hand board, or any other simple board, starts from a copy of
`layout.yaml`:
- `cluster:` and `suffix:` name the cluster (`right_hand`, `RH`). The switches,
  mount holes, `J-CHAIN` and outline then come from the body CAD for that cluster.
- `networks:` gives ONE PATTERN for every key: where the T's junction sits
  relative to the key's switch, and which way its resistors and capacitor
  turn. `tools/pcb.py` `network_parts` places each key's three parts from its
  switch's position in the body CAD, so every key's network sits the same way
  round its switch. A key that cannot take the pattern goes under `except:`,
  with the reason; on this board none does.
- `route_first:` names the nets routed before the rest, in order. They are
  the chain nets reaching `J-CHAIN`'s far (odd) row, which a track can reach
  only from behind the header. On this board they also include three key
  lines, which would otherwise be boxed in at the register:
  - `/KEY_LH5` goes first, because U1.14's only way out is a via between the
    pin rows, which SCK would otherwise take;
  - `/KEY_LH4` and `/KEY_LH1` go straight after the chain nets.

  With that order, every net routes on the first pass. `layout.yaml` says why,
  line by line.
- **No mount is plated.** All four stay unplated with their copper
  keep-outs: the key plate is grounded through the columns at the main
  board's mounts (ADR 0025). Amendment 5's `bond_mount` is gone from
  `layout.yaml`; `tools/pcb.py` still supports the key for a board that needs one.
- `connect_first:` names pad-to-pad connections routed before everything,
  each with the `max_mm` that `pcb.py check` then holds it to: here the
  decoupler's return to the register's ground pin. Name the new board's pads.
- `parts:` places everything else: the register, its decoupler, the free-bit
  pull-ups and `C-BULK-CHAIN-<suffix>`.
- `rules:`, `fab:` (the board house), `silk:` (title, revision, date; `at`
  for the parts side, `top_at` for the switch side),
  `standoff_footprint:`, `route:`, `ground_net:` and `power_nets:` are copied
  as they are. `power_nets:` names that board's rail.

Then run `pcb.py layout`, and move parts in `layout.yaml` until `pcb.py check`
passes. Write the board's README from this one.

## Ordering it — JLCPCB

This is the order sheet for **both** key boards. The right-hand board's
page gives only what differs (its part counts and its cost line).
JLC's limits and fees were read from the banked pages in `datasheets/fab/`
(snapshots of 2026-09-27). Stock, prices and footprints were checked on
2026-10-01. Anything marked `[from memory]` or *estimate* is to be confirmed
on JLC's live order form.

**Before you order, run the gates.** `python3 tools/pcb.py check
hardware/boards/key-board-lh` must report 0 errors, and `python3 tools/kicad.py
check` must PASS. A PASS means `fab/` was written from this board and these
sheets, so it is the order. Then:

### 1. What to upload

| Upload | File | How |
|---|---|---|
| **Gerber** (the bare board) | a zip of `fab/`'s nine `.gbr` files, both `.drl` files and the `.gbrjob` | `cd hardware/boards/key-board-lh/fab && zip /tmp/key-board-lh-gerbers.zip *.gbr *.drl *.gbrjob`. Write the zip **outside** `fab/`: `kicad.py check` fails on any file in `fab/` that no tool wrote |
| **BOM** (PCBA step) | `fab/key-board-lh-bom-jlc.csv` | Columns `Comment, Designator, Footprint, JLCPCB Part #`, as the banked guide asks `[datasheets/fab/JLCPCB-KICAD-BOM-CPL-GUIDE.pdf]` |
| **CPL** (PCBA step) | `fab/key-board-lh-cpl-jlc.csv` | Columns `Designator, Mid X, Mid Y, Layer, Rotation`, mm. The rotations are already in JLC's convention (*4. Rotations*, below) |

Do **not** upload `-pos.csv` (KiCad's own placement, with KiCad's
rotations) or `-hand-assembly.csv`. They are for the builder.

### 2. The PCB options, top to bottom on JLC's form

The option names are as JLC's quote form showed them `[from memory]`.
Where the form has an option that is not listed here, leave it at its default.

| Option | Pick | Why |
|---|---|---|
| Base material | FR-4 | |
| Layers | 2 | |
| Dimensions | read from the Gerber (do not type them) | The outline is the body CAD's, `mechanical/export/key-board-lh.dxf` |
| PCB qty | **5** (the fewest JLC makes `[from memory]`) | Two are assembled (*3. Assembly options*). The rest are bare spares for a re-work or a second build |
| Product type | Industrial/Consumer electronics | |
| Different design | 1 | |
| Delivery format | Single PCB | Not a panel: Economic PCBA takes single boards from 10 × 10 mm `[datasheets/fab/JLCPCB-PCBA-CAPABILITIES.pdf]` |
| PCB thickness | `boards.key_board_t` (`config/body.yaml`) | ADR 0020 Amendment 6. `pcb.py check` holds the stackup to it, and the `.gbrjob` carries it |
| PCB colour | Green (`layout.yaml` `fab: mask`) | At this thickness Economic PCBA offers green with HASL or ENIG, 2–50 boards `[JLCPCB-PCBA-CAPABILITIES.pdf, "PCB Specs for Economic PCB Assembly"]` |
| Silkscreen | White (`fab: silk`) | |
| Material type | FR-4 TG135–140, the default | |
| Surface finish | **LeadFree HASL** (`fab: finish`) | The stackup and the `.gbrjob` say it; Economic PCBA offers it at this thickness (above) |
| Outer copper weight | 1 oz (`fab: copper_oz`) | Every limit in the DFM table (below) is JLC's 1 oz figure |
| Via covering | Tented, the default | No via is a test point (the board has none, *Bring-up*) |
| Min via hole size / diameter | the default (0.3 mm hole) | Both boards' vias are `layout.yaml` `rules: via_drill` / `via`, which JLC does not charge extra for (DFM table) |
| Board outline tolerance | ±0.2 mm (regular) | The mounts are holes, not the outline; the outline only has to clear the cavity |
| Confirm production file | **Yes** | JLC's engineer sends the production Gerber back. Check J1's pads (*Open*: their thin ring) before it is made |
| Mark on PCB / Remove order number | **No** (JLC prints its number where it chooses) | Neither face is seen in the instrument. "Yes" costs extra `[from memory]`, and "Specify a location" needs a marker on the silkscreen that this board does not have |
| Flying probe test | Fully test (the default for a 2-layer prototype) | |
| Gold fingers, castellated holes, edge plating, impedance control | No / none | None of them is on this board |

### 3. Assembly options (turn on "PCB Assembly")

| Option | Pick | Why |
|---|---|---|
| PCBA type | **Economic** | Single-sided placement is all it needs `[JLCPCB-PCBA-CAPABILITIES.pdf]` |
| Assembly side | **Bottom side** | Every machine-placed part is on the bottom, the side facing the main board |
| PCBA qty | **2** | Economic assembles from 2 `[JLCPCB-PCBA-CAPABILITIES.pdf]`: one for the build, one spare |
| Tooling holes | Added by JLCPCB | The board has none of its own |
| Confirm parts placement | **Yes** | The rotations are corrected (*4*), but JLC's preview is still the last check, and this is the first order |
| Stencil | included in Economic PCBA | Not a separate stencil order |

Then, in the BOM step, **confirm every row matched its LCSC number**. Leave
the hand parts (switches, J1) out: they are not in the BOM file. Do not accept
a substitute for U1 (below).

### 4. The parts, and their rotations

Every machine-placed part is in JLC's library, checked on 2026-10-01 `[web, JLC
component-search API (jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList), 2026-10-01]`.
The part numbers come from the sheets (`LCSC`, `MPN`), and the fab BOM is
generated from them, so they are not repeated here.

| BOM row | Refs (this board) | LCSC | Library | Stock at JLC, 2026-10-01 | Unit price, 2026-10-01 | KiCad → JLC rotation offset |
|---|---|---|---|---|---|---|
| `R-KEY-SER` | R1, R3, R5, R7, R9 | C17408 | **Basic** | 9.39 M | $0.0042 | 0 |
| `R-KEY-PU` | R2, R4, R6, R8, R10, R11 | C17520 | **Basic** | 3.64 M | $0.0046 | 0 |
| `C-KEY` | C1–C5 | C53134 | **Basic** | 202 k | $0.0173 | 0 |
| `C-DECOUPLE-165` | C6 | C49678 | **Basic** | 19.3 M | $0.0189 | 0 |
| `C-BULK-CHAIN` | C7 | C15850 | **Basic** | 5.01 M | $0.0651 | 0 |
| `U-KEYS` | U1 | C2864745 | **Extended** (not Preferred) | **112** | $1.086 | **−90** |

- **One Extended part, so one feeder fee per design**: $3 `[datasheets/fab/JLCPCB-PCBA-FAQ.pdf, FAQ 6]`. The Basic parts have none.
- **U1's stock is thin**: 112 on 2026-09-27, 2026-09-30 and 2026-10-01. Both key-board designs take 2 each at a prototype run, so 4 in all.
  - Digi-Key held 5,845 on 2026-09-27 `[web https://www.digikey.com/en/products/detail/texas-instruments/SN74HCS165DR/13563029, 2026-09-27]`.
  - **If JLC is short, buy it there.** Then either send it to JLC as a consigned part, or leave it off the JLC order and fit it by hand (SOIC-16, 1.27 mm pitch).
  - **Do not let JLC substitute a plain 74HC165** or a 74LV165A. The part must have Schmitt-trigger inputs with no input transition-rate limit (the `U-KEYS` row says why).
- **Rotations.** `fab/*-cpl-jlc.csv` is no longer KiCad's raw angle. `tools/pcb.py render` makes two corrections (`hardware/lib/README.md`, *JLC's rotations*):
  - A bottom part's angle is mirrored to 180° − KiCad's.
  - The per-part offset in `hardware/lib/jlc-rotation.csv` is added, read from JLC's own footprint for that LCSC number, which is banked in `datasheets/` (each row names its file).
  - The register's offset is **−90°**. JLC's SOIC-16 lies with its rows along x, pin 1 bottom left; KiCad's lies with its rows along y, pin 1 top left.
  - The 0805s' pad 1 is at −x in both libraries, so their offset is 0.
  - Before this correction, U1 would have shown a quarter-turn out in the preview.
- **US-sourced hand build.** The UNI-ROYAL resistors stay for JLC assembly, because they are Basic parts with no feeder fee. No US distributor stocks them (DigiKey had no result `[web https://www.digikey.com/en/products/result?keywords=0805W8F1000T5E, 2026-09-27]`).
  - For a board built by hand from US stock, use YAGEO RC0805FR-07100RL (100R) and RC0805FR-072K2L (2k2). DigiKey 311-100CRCT-ND / 311-2.20KCRCT-ND; LCSC C105577 / C114561, which are JLC **Extended** (233 k and 1.07 M in stock on 2026-10-01) `[web https://www.digikey.com/en/products/result?keywords=RC0805FR-07100RL; …=RC0805FR-072K2L, 2026-09-27; JLC component-search API, 2026-10-01]`.
  - The capacitors' parts are already at DigiKey.
- **To change a part**, set its `LCSC`/`MPN` fields in the circuit sheet and re-render. The BOM row (`hardware/cluster/bom.csv` etc.) says what the part must be; the sheet says which one is bought. A new LCSC number needs its row in `hardware/lib/jlc-rotation.csv`; until it has one, `render` names it on the console.

### 5. The placement preview: what to check before paying

JLC shows the bottom side with its own footprints drawn at the CPL's
positions. Check:
1. **Every part sits on its pads.** If every part is offset by the same amount, the origin is wrong. Stop: the CPL and the Gerbers share KiCad's page origin, so this should not happen.
2. **U1's pin-1 mark** (JLC's dot or bevel) lands on the board's U1 pin-1 silk mark, at the register's corner nearest pin 1. Pins 1–8 run along one row and 9–16 back along the other. A quarter-turn means the offset is wrong; a half-turn means the bottom-side mirror is wrong. Either way, correct it in the preview and record it in *Revisions*.
3. **The passives** sit along their pad pairs. None of them is polarised (all MLCC or chip resistors), so only the axis matters.
4. **C7** (`C-BULK-CHAIN`) is beside J1's 3V3 pin.
5. **No part is drawn at J1 or at the switches.** They are hand parts. If JLC has added them, it has matched a footprint it should not have: remove them.

### 6. Cost estimate, one design, 5 PCBs with 2 assembled

*Estimates.* JLC's live quote replaces this table.

| Item | Left hand | Source |
|---|---|---|
| 5 bare PCBs, 2-layer, under 100 × 100 mm | $2.00 | `[web https://jlcpcb.com/, 2026-10-01: "From $2.00 / 5 pcs"]`. This board is inside 100 × 100 (its outline, `mechanical/export/key-board-lh.dxf`) |
| Lead-free HASL surcharge | about $1–2 | *estimate* `[from memory]` |
| PCBA setup | $8.00 | `[datasheets/fab/JLCPCB-PCBA-FAQ.pdf, FAQ 1]` |
| Stencil | $1.50 | same |
| SMT joints | $0.18 | [calc: (18 two-pad parts × 2 + U1's 16) = 52 joints × 2 boards × $0.0017] |
| Extended-part feeder fee (U1) | $3.00 | FAQ 6 |
| Machine-placed parts, 2 boards | about $2.61 | [calc: per board 5 × 0.0042 + 6 × 0.0046 + 5 × 0.0173 + 0.0189 + 0.0651 + 1.086 = $1.305, at the 2026-10-01 unit prices above; JLC adds attrition spares, so a little more] |
| **JLC subtotal** | **about $18–19** | before shipping |
| Shipping to the US | about $10–25 | *estimate* `[from memory]`. It depends on the method, and both designs ship together if ordered together |
| Hand parts: J1 | $2.83 each | DigiKey SHF-106-01-L-D-RA-ND, 8 in stock, 4-week factory lead time `[web https://www.digikey.com/en/products/detail/samtec-inc/SHF-106-01-L-D-RA/8410402, 2026-10-01]` |
| Hand parts: switches, `CBL-CHAIN`, mount hardware | not priced here | Below |

### 7. Bought separately, for the hand assembly

Only the first two are on `fab/key-board-lh-hand-assembly.csv`. Sourcing was
read on 2026-09-27 except where dated; check stock at order.
- **The switches** (BOM row `SW1-n`): Gateron **KS-33H10B050NN-Y24**, Low Profile 2.0 Red, the code on the sheet and the hand list.
  - **Order `-Y24` exactly.** The suffix is the bottom housing's colour, not a year: `-Y24` is black and `-Y31` white.
  - The white-housing spec gives a longer total travel than the black one the body is drawn from (`switch.total_travel`), which would break the flush rule `[datasheets/mechanical/GATERON-KS-33-VENDOR-SPEC-DRAWING.pdf; datasheets/mechanical/GATERON-KS-33-SPEC-WHITE-HOUSING-KS-33H10B050NN-Y31.pdf]`.
  - Not the Silent, and not the Low Profile 3.0.
  - Gateron's own store sells the black-housing Red `[web https://www.gateron.com/products/gateron-ks-33-low-profile-switch-set, 2026-09-27]`. Whether it ships from a US warehouse is unverified, and its price could not be read on 2026-10-01 (the page carries none outside its script).
  - US sellers found (e.g. LumeKeebs) sell "KS-33 2.0 Red" without naming the housing or the code `[web https://lumekeebs.com/products/gateron-ks-33-low-profile-2-0-mechanical-switches, 2026-09-27]`, so check the code on the packaging.
- **`J-CHAIN`**, Samtec SHF-106-01-L-D-RA.
  - JLC/LCSC has none: C17202657, stock 0 on 2026-09-27 and again on 2026-10-01 `[JLC component-search API]`.
  - DigiKey had **only 8**, with a **4-week factory lead time**, on 2026-09-27, 2026-09-30 and 2026-10-01 (above).
  - An instrument takes `chain-connectors` of them: two on this pair of key boards and two on the main board. Eight is one build and its spares. Failing that, buy from Samtec direct (reel variants and samples).
  - Its sourcing is open (its BOM row, and *Open* below).
- **The corner mount hardware.** At each corner: a spacer (`MECH-KB-SPACER`), and the column's standoff and screw (`MECH-COL-STANDOFF`, `MECH-COL-SCREW`), which are bought with the cassette.
  - What each must be, the quantities and the sources are those rows in `hardware/unplaced.csv`; their prices are not repeated here.
  - The spacers and standoffs are faced to length before fitting. The mount is described in *Assembling*, step 2.
- **`CBL-CHAIN`**, one per board, ordered as in *Assembling*, step 3.

### 8. DFM: JLC's limits against this board

JLC's figures are from `datasheets/fab/JLCPCB-PCB-CAPABILITIES.pdf` (the
2-layer, 1 oz rows). This board's figures are **read from the board**: the
design rules in `key-board-lh.kicad_pro`, which `pcb.py check` holds equal to
`layout.yaml` `rules:`/`fab:`, and which KiCad's DRC (0 errors, 0 warnings)
proves every item meets. Where a figure is the smallest instance actually on
the board, it was measured with `pcbnew` on 2026-10-01, and the right-hand
board's are the same.

| Rule | JLC (2-layer, 1 oz) | Held by (rule) | Smallest on the board | Margin |
|---|---|---|---|---|
| Layers / board size | 2; Economic PCBA ≥ 10 × 10 mm | — | 2 layers; outline from the body CAD | ok |
| Thickness | a standard FR-4 thickness; at this one Economic PCBA takes green HASL/ENIG | `boards.key_board_t` | the stackup, held by `pcb.py check` | ok |
| Track width | ≥ 0.10 | `rules: track_min` | `rules: track` (every signal track) | 2.5× |
| Track/pad spacing | ≥ 0.10 (pad to track 0.10; SMD pad to pad 0.15) | `rules: clearance` | the rule (the pour is filled at it) | 2× |
| Copper to routed edge | ≥ 0.20 | `rules: edge_clearance` | ≥ the rule (DRC) | +0.1 |
| PTH drill | 0.15–6.3; ≥ 0.5 recommended for PTH | `rules: drill_min` | 0.70 (J1) | ok |
| NPTH drill | ≥ 0.50 | — | the mount holes (`standoff_footprint`) and the switch poles | ok |
| PTH annular ring | ≥ 0.18 absolute, 0.25 recommended | `fab: annular_min` | **0.185, J1's pads on the sides facing a neighbour** (the 1.07 pad across a 0.70 drill) | **+0.005: at the absolute minimum** (*Open*) |
| Via hole / diameter | ≥ 0.15 / 0.25; diameter ≥ hole + 0.10 (0.15 preferred); a 0.2–0.25 hole under 0.45 costs more | `rules: via_drill`, `via`, `via_min` | the rule on every via (30 on this board, 33 on the right-hand one); ring 0.20 | ok, and no via surcharge |
| Via hole to hole / pad hole to hole | ≥ 0.20 / 0.45 | `fab: hole_to_hole` | ≥ the rule (DRC) | ok |
| PTH to track | ≥ 0.28 (0.35 recommended) | `fab: hole_clearance` | ≥ the rule (DRC) | at JLC's minimum by rule |
| Mask expansion / bridge | 1:1 opening; bridge ≥ 0.10 between pads (green, 1 oz) | board setup: expansion 0 | the narrowest pad gap: 0.20 between J1's pads (1.27 pitch − 1.07 pad) | 2× |
| Silkscreen line width | ≥ 0.15 | `fab: silk_line_min` | 0.15 (footprint strokes widened to it, `hardware/lib/README.md`) | at minimum |
| Silkscreen text height | ≥ 1.0 (stroke ≥ 0.15, ratio 1:6 preferred) | `fab: silk_text_min` | 1.0 high, 0.18 stroke | at minimum height; stroke ok |
| Pad to silkscreen | ≥ 0.15 | `fab: silk_to_pad` | ≥ the rule (DRC, and `pcb.py check`) | ok |
| Hole tolerance | +0.13 / −0.08 | — | the switch-pin and J1 drills are sized for −0.08 (`hardware/lib/README.md`) | ok |

Nothing on the board needs a non-standard option. The three items at JLC's
minimum are the silk line, the silk text height and J1's ring. The silk ones
are what JLC prints by default. J1's ring is an *Open* item, for JLC's review
to accept.

To change a limit, change it in KiCad's Board Setup **and** in `layout.yaml`,
and say why. `pcb.py check` fails if the two differ. The silkscreen limits
that KiCad's DRC does not test are checked by `pcb.py` itself (above).

## Assembling the rest by hand

1. **J1** (`J-CHAIN`; the part is on its BOM row and the sheet).
   - It goes on the bottom side, **mouth toward the tail**. The silkscreen marks it: an arrow beside the header points out of its mouth, and pin 1's dot is behind the pins, away from the mouth.
   - **Backward is 3V3 on ground.** The 2×6 pad grid fits the header either way round. Turned 180°, the header puts the ribbon's 3V3 on a ground pin (`key-chain-loom.md`). Fit it with its mouth at the arrow.
   - Seat it flat and solder it from the top (switch) side.
   - The plate has **no window** over the tails. Seated flat, they stop short of the grounded plate (`mechanical/drc.echo` "J-CHAIN pin tails clear of the key plate"), so do not trim them or leave the header standing proud.
2. **The corner mounts, and the switches.** Each of the board's four corners is one of the cassette's columns (ADR 0025; ADR 0020 Amendment 7; the section is `mechanical/renders/section-kb-mount.png`). From the top down: an M2.5 low-head screw whose head bears on the key plate's top face; the key plate; a spacer (Ettinger 5.52.015, faced to `hardware.kb_spacer_l`); the board; and the column's standoff, which is already threaded onto its stud in the bottom plate and clamps the main board. The screw goes down through the plate, the spacer and the board into the standoff. The key board is fitted on the bench, with the rest of the cassette, before anything goes into the wood.
   - **The spacer is not optional**: with the plate it sets the board's depth (`drc.echo` "key-board mount sets the board depth"). Measure each faced spacer with calipers before fitting: `hardware.kb_spacer_l`, within `kb_spacer_l_tol`.
   - Clip the five KS-33s into the key plate's cutouts.
   - Plug the ribbon into this board's J1 (step 3).
   - Stand the board on its four standoffs, set a spacer on each corner, lower the key plate onto the switch pins and the spacers, and drive the four screws into the standoffs.
   - **Then** solder the switch pins, from the bottom. Soldering with the board fixed at depth is what holds it at the depth the pins were designed for (`switch.pcb_below_seat`). How far the hardware's tolerances can move it is `drc.echo` "key-board depth at the hardware's tolerance limits" (*Open* below). Soldering from the bottom needs the key plate, with its board, off the columns and turned over: do it before the cassette's ribbon is plugged at the main board, or with the plate held raised (step 3).
   - **Last, the cassette goes into the shell**, and the oak top is RTV-bonded onto the key plate (ADR 0025), the screws' heads finding their pockets. For service afterwards the silicone is cut and the screws come out from above.
3. **The ribbon** (`CBL-CHAIN`).
   - **Order it as** `FFSD-06-D-<code>-01-N-RN2`. `<code>` is `mechanical/drc.echo` "key-chain cable to order (FFSD length code)", **written with two digits before the point**: Samtec's field is `XX.XX` `[datasheets/connectors/SAMTEC-FFSD-XX-X-XX.XX-01-PRINT.pdf, part-number block]`, so a length under 10 in takes a leading zero, as DigiKey lists FFSD-06-D-06.00-01-N `[web https://www.digikey.com/en/products/detail/samtec-inc/FFSD-06-D-06-00-01-N/6678085, 2026-09-27]`. The print takes any overall length in that field above a 1.00 in minimum; it states increments only for the daisy-chain option, which this cable does not use (same print, sheet 1). Type the full part number into Samtec's configurator and check it echoes back before paying, since the series is non-returnable. It is the overall length in **inches**, over both sockets, as the FFSD print measures it, with the print's −0.125 in tolerance already covered. `-RN2` reverses the notch on the second socket. **Do not type the millimetre length** ("key-chain ribbon length (derived)") into the part number: read as inches, it orders a cable about 25 times too long.
   - **Meter every cable before it is first powered**, not only the first one. Check it by *Bring-up*, step 2.
   - Plug it in with the key plate held raised straight up off its columns, before the plate is screwed down (`routing.chain_service`, `routing.chain_raise`). That is the position its length was derived for.
   - With `-RN2`, the main board's socket's cable leaves **upward** and the key board's leaves **downward**. The two face each other, and closed, the ribbon folds into a flat hairpin between the two plugs' heights (`key-chain-loom.md`). **A cable whose ends both leave downward is a standard cable, without `-RN2`, and it is wrong.**
4. **Conformal coat** (`MECH-COAT`), once the board has passed *Bring-up*: brush it on the bottom (parts) face only, with J1's mouth masked, and leave the switch side bare (`cluster-boards.md`, *Still open*, says why).

## Bring-up

Before the first key board goes into an instrument, check it on the bench.
**There are no test pads** (owner, 2026-09-29: a one-off build is probed by
hand). Everything is reached at J1's pin tails on the bottom, which carry the
whole chain (`hardware/interfaces/key-chain-loom/key-chain-loom.md`, the
key-board end):

| J1 pin | Signal |
|---|---|
| 3 | 3V3 |
| 4, 6, 8, 10, 12 | GND |
| 11 | SCK |
| 9 | SH/LD |
| 7 | SER |
| 5 | QH |

A clip lead on the header's pin tails, or a spare ribbon with an IDC plug cut
open, is the bench harness.

1. **No shorts.** Measure J1 pin 3 (3V3) to pin 4 (GND) with no power: it must not read as a short.
2. **Every cable's pinout, with a meter, before it is first powered.**
   - With both ends free, conductor 10 at one end must reach the other socket's position 3 (3V3), and conductor 2 its position 11 (SCK).
   - That is the `-RN2` map, key pin = 13 − main pin (`key-chain-loom.md`). The map is symmetric, so either end can be taken as the main-board end.
   - A cable without `-RN2` looks right on the drawn route and puts 3V3 on a ground pin. Nothing mechanical shows it, so check every cable, spares and replacements included.
3. **Tie SER.** Nothing drives SER on the bench, and a floating CMOS input draws current and shifts in undefined bits. Tie J1 pin 7 (SER) to a GND pin or to pin 3 (3V3).
4. **Power.** Feed 3.3 V between J1 pin 3 (3V3) and a GND pin (current-limited to ~20 mA).
   - With no key pressed, and SER tied, the draw should be near zero: the register's quiescent current is microamps `[datasheets/logic/SN74HCS165-ti-scls828a.pdf p.6]`. A reading of milliamps with no key pressed is a fault.
   - Each pressed key adds its pull-up's current (`key-scan-current`, on `key-switch-network.md`).
5. **The chain.** Drive SH/LD low then high, then clock SCK, and watch QH.
   - It shifts out this board's eight bits, H first: LH1..LH5, then the two marker bits and the free bit, in `key-marker-and-bits/allocation.yaml`'s order. Idle, each key bit and the free bit read high, and the markers read the pattern `marker-bits` gives this device.
   - Each key reads low while pressed.
   - Clocks past the 8th shift in the level SER is tied to.
   - Firmware normally does this; with a logic analyser on J1's pins it is visible without one.
6. **The rail, in the instrument.** On the real main board and ribbon, scope the key board's VCC (J1 pin 3 to a GND pin, or across C6) while the chain shifts. `FB-CHAIN` and `C-DECOUPLE-165` form a lightly damped LC (the `FB-CHAIN` row). The simulation (`hardware/interfaces/key-chain-loom/sim/`, `rail-as-ordered`) keeps this rail well inside its limit with C7 fitted, and inside it even without C7 (`rail-without-bulk`), so expect at most a small ring after each burst and each key change. A larger one means the bead or the ribbon is not what the simulation assumes: record it in *Revisions*. The bench supply has no bead, so this step needs the main board.

## The silkscreen

Both sides carry it, every mark clear of the parts, so it reads with them
fitted: `pcb.py check` fails any silkscreen under a part's body (its
courtyard). The parts side is mirrored so it reads from below. The straight-down
renders, `key-board-lh.pcb-plan-bottom.png` and `-plan-top.png`, show it as a
builder sees it.

**References are plain numbers** (owner, 2026-09-28): R1, C1, U1, as the
schematic, the placement file and the hand-assembly list all name them. Each
part's BOM row is its `Row` field; the sheet a key's network sits on (LH1..LH5)
is how the tools find it.

| Reference | BOM row | What it is |
|---|---|---|
| SW*n*, *n* = 1-5 | `SW1-n` | the switch of key LH*n* |
| R(2*n*-1): R1, R3, R5, R7, R9 | `R-KEY-SER` | key LH*n*'s series resistor |
| R(2*n*): R2, R4, R6, R8, R10 | `R-KEY-PU` | key LH*n*'s pull-up |
| C*n*: C1-C5 | `C-KEY` | key LH*n*'s capacitor |
| R11 | `R-KEY-PU` | the free input's pull-up (sheet FREE3) |
| C6 | `C-DECOUPLE-165` | the register's decoupler |
| C7 | `C-BULK-CHAIN` | the rail's reservoir, beside J1's 3V3 pin |
| U1 | `U-KEYS` | the register, SN74HCS165 |
| J1 | `J-CHAIN` | the key chain's header |
| H1-H4 | (board only) | the corner mounts' holes |

**Parts side (bottom):** every part's reference beside it. Each key's three
network parts carry theirs the same way round the network, as the parts sit
round the switch (the two resistors' along them, beside the column), with the
key's name (LH1..LH5) beside its capacitor;
J1's pin 1 dot and an arrow out of its mouth; `MOUTH` and an arrow at the
mouth end; the title block (`layout.yaml` `silk:`).

**Switch side (top):** each switch's reference and key (`SW1 LH1`) beside it;
J1 with pin 1's dot and the arrow out of its mouth, where it is soldered;
`MOUTH`; the title block again (`silk:` `top_at`).

## Revisions

| Rev | Date | What changed | Where |
|---|---|---|---|
| A | 2026-09-27 | First layout: every key's network the same T in the same place round its switch, six test pads in one row (QH, SER, GND, SCK, SH/LD, 3V3), C7 (`C-BULK-CHAIN`), silkscreen on both sides, no acute track junction (`pcb.py check` tests every join, a track ending mid-track included). Not yet ordered; re-laid out on the same date for the screwed corner mount (keep-outs from the nut and the spacer/washer; ADR 0020 Amendment 3 then moved the heads from plugged bores into blind pockets, which changes nothing on the board); on 2026-09-28, C7 made a fitted, machine-placed part (it had been a do-not-fit footprint; owner: it costs cents) and J-CHAIN's pads lengthened on their free side; the same day the corner mounts went to M2.5 for PEM studs pressed flush into the plate (ADR 0020 Amendment 4: larger holes and keep-outs, mounts 0.2 further in), and the washer dropped, the spacer taking its length; on 2026-09-29 re-laid out for the cassette's columns (ADR 0025): no bonded mount (Amendment 5's is superseded), the mouth end 0.6 and the tail end 0.2 longer, J-CHAIN 0.5 further toward the tail and the register, its decoupler, R11 and C7 moved 0.5 with it | git history of this directory |

To make a revision, edit the board in KiCad, change the revision and date in
the title block and in the silkscreen text, and copy them into
`layout.yaml` `silk:` so a re-layout keeps them. Then re-render and add a row
here. Record any correction an order needed (a part rotation in JLC's preview,
a drill that did not fit) in the row.

## Open, and what decides each

| Open | Decided by |
|---|---|
| **The switch positions** (`layout.lh_gaps`, `layout.lh_offsets` `tbd`; `config/key-layout.yaml` `x`/`y` replace them) | M2 on the mule, locked at M3 |
| The FFSD socket's stand-out from the header's mouth, `boards.chain_plug_proud`. The print does not dimension it, and it decides whether the cable clears the shroud's mouth at all, not only the ribbon's fold | M4, the first mated pair |
| The mount's spacers, faced to `hardware.kb_spacer_l` (no stocked M2.5 spacer has that length), and the column's standoff and screw (`MECH-COL-STANDOFF`, `MECH-COL-SCREW`) | the first fit; M4, with the parts bought |
| The board depth at the hardware's tolerance limits: the worst case reaches the window's shoulder end (`drc.echo` "key-board depth at the hardware's tolerance limits") | the first board, fitted |
| The register's supply: JLC's stock is thin (above) | the first order |
| J-CHAIN's supply: none at JLC, 8 at DigiKey (above); buy them with this order, or from Samtec. A stocked alternative is not a drop-in: its footprint is on three boards | the first order |
| J-CHAIN's pads' ring is at JLC's absolute minimum on the sides facing a neighbour. The 1.27 mm pitch both ways leaves no room there. The pads are lengthened on their free side instead (`hardware/lib/README.md`, the IDC header's row); ask JLC's review to accept the thin side | the first order |
| Part orientation in JLC's placement preview. The CPL carries JLC's convention and each part's offset from JLC's own footprint (*Ordering*, 4), but no order has yet confirmed it | the first order's preview (*Ordering*, 5); record any correction in *Revisions* |
| No 3D model of J-CHAIN in the renders (Samtec's is behind a login; `datasheets/.manifest-R12.csv` records the attempt) | nothing blocks on it |
| The main board's end of the ribbon | the main board's layout |
