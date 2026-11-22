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
| `lh_layout.py` | **The record of the layout** (ADR 0030): every part's place and every track and via, written out by hand with the reason for each. It rewrites `key-board-lh.kicad_pcb`. No router runs on this board |
| `key-board-lh.kicad_pcb` (+ `.kicad_pro`, which holds its design rules) | Written by `lh_layout.py`. Change the layout there and run it, so the reasons stay with the copper |
| `layout.yaml` | The limits the board is held to, and what its silkscreen says. `rules:` and `fab:` are read by **every** `pcb.py check`: the board's design settings must still say what they say. `silk:`, `heights:`, `standoff_footprint:`, `ground_net:` and `power_nets:` are read by the checks and by `lh_layout.py` |
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
- the board's thickness or outline differing from the body CAD's;
- a switch, mount hole or `J-CHAIN` not where the body CAD puts it, or
  turned or on the wrong side;
- a mount hole (H1–H4) that is not NPTH at the body CAD's size, or any copper
  (track, via, pour or another part's pad), on either layer, inside its
  keep-out: the column standoff's and the spacer's footprint, each grown by
  `hardware.kb_mount_float`, plus `rules.clearance` (ADR 0020).

**What holds the owner's rule (every key's network placed the same way round
its switch):** `lh_layout.py` places all five from one table (`KEY_NET`),
relative to each switch's position in the body CAD, and `check` holds each
switch where the body CAD puts it.

`kicad.py check` also holds `J-CHAIN`'s pins to the ribbon's netlist
(`hardware/interfaces/key-chain-loom/netlist.yaml`).

### How this board is laid out

By hand, in `lh_layout.py` (ADR 0030). The script's opening comment is the
floorplan and the reason for each choice; these are the rules the owner's
review of the copper set, 2026-11-20, and the next boards start from them:

- **The switch-side face is the ground plane, and it is whole.** No signal or
  power copper is on it. Every line on the parts face runs over it.
- **The parts face has no pour.** A second fill added nothing to a whole
  plane under slow lines, and the tracks cut it into regions joined by necks.
- **Every ground pad reaches the plane by its own short way:** a key's
  capacitor by a neck to its switch's through-hole ground pin, the register's
  pins and its capacitors by a via each, the header by its pins.
- **The plane meets every pin it joins through relief spokes**, so no joint
  is soldered into solid copper.
- **Nothing passes between a switch's pin and its pole.** Each key's series
  resistor stands beside the leg pin and its capacitor beside the ground pin,
  outside them, each on one short straight neck. The node runs under both
  pins, the pull-up hangs from its middle, and the key line leaves the end
  facing the register.
- **The chain's four lines run under the register**, between its pad rows,
  straight from the header: no line wraps a part and none crosses another.
- **3V3 is one trunk on the parts face**, with no via.
- **`J-CHAIN` stands vertical, its signal (even) row toward the register** and its ground row toward the mouth (ADR 0017, *Amendment, 2026-11-21*).

### Making the next board from this one

Start from a copy of `lh_layout.py` and of `layout.yaml` (`cluster:` and
`suffix:` name the cluster; the switches, mounts, `J-CHAIN` and outline then
come from the body CAD for it). Work out the floorplan from that board's
register pinout first, show the placement before drawing copper, then write
the tracks. Run `pcb.py check` until it passes, then `pcb.py render`. Write
the board's README from this one.

**No mount is plated.** All four stay unplated with their copper keep-outs:
the key plate is grounded through the columns at the main board's mounts
(ADR 0025; ADR 0020 Amendment 7).

## Ordering it — JLCPCB

This is the order sheet for **both** key boards. The right-hand board's
page gives only what differs (its part counts and its cost line).
JLC's limits and fees were read from the banked pages in `datasheets/fab/`
(snapshots of 2026-09-27). Stock, prices and footprints were checked on
2026-10-01. Anything marked `[from memory]` or *estimate* is to be confirmed
on JLC's live order form.

**Before you order, run the gates.** `python3 tools/pcb.py check
hardware/boards/key-board-lh` must report 0 errors, and `python3 tools/kicad.py
check --board key-board-lh` must PASS: this board's export, ERC, layout and
renders, the circuit sheets it places, and the checks of its `J-CHAIN` against
the main board and the ribbon (`docs/reference/tooling.md` §3). Another board's
layout or renders failing does not hold this order (review #6-3); the full
`kicad.py check` is the commit gate's. A PASS means `fab/` was written from
this board and these sheets, so it is the order. Then:

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
| Delivery format | Single PCB, **edge rails and fiducials added by JLCPCB** | Standard PCBA (*3*) makes both "Necessary" and takes a single board from 70 × 70 mm `[datasheets/fab/JLCPCB-PCBA-CAPABILITIES.pdf]`; each key board is under 70 mm across (its size is in its own `fab/*-job.gbrjob`, `"Size"`), so it ships on JLC's rails. Whether JLC's rails alone reach 70 mm across or it asks for a panel is the quote form's. Where the rails' tooling holes land is checked in the preview (*5*) |
| PCB thickness | `boards.key_board_t` (`config/body.yaml`) | ADR 0020 Amendment 6. `pcb.py check` holds the stackup to it, and the `.gbrjob` carries it |
| PCB colour | **White** (`layout.yaml` `fab: mask`; ADR 0028, *Amendment, 2026-10-02*) | The undersides face the LED row: white is the cavity's reflector. Standard PCBA has no colour or finish limit `[JLCPCB-PCBA-CAPABILITIES.pdf]`, which is why the order is Standard (*3*); Economic lists white at this thickness only with *leaded* HASL |
| Silkscreen | Black (`fab: silk`) | A white legend does not read on white mask |
| Material type | FR-4 TG135–140, the default | |
| Surface finish | **LeadFree HASL** (`fab: finish`) | The stackup and the `.gbrjob` say it; Standard PCBA takes it with white (*PCB colour*, above) |
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
| PCBA type | **Standard** | The owner, 2026-10-04 (#17 D1: "Standard PCBA (Recommended)"; ADR 0028, *Amendment, 2026-10-04*): white with lead-free HASL, which Economic does not list `[JLCPCB-PCBA-CAPABILITIES.pdf]`. The Extended-part count (#17 D6) mattered only under Economic, so it is moot |
| Assembly side | **Bottom side** | Every machine-placed part is on the bottom, the side facing the main board |
| PCBA qty | **2** | Standard assembles from 2 `[JLCPCB-PCBA-CAPABILITIES.pdf]`: one for the build, one spare |
| Tooling holes | Added by JLCPCB, on its rails | The board has none of its own. Where they land is checked in the preview (*5*, item 6) |
| Confirm parts placement | **Yes** | The rotations are corrected (*4*), but JLC's preview is still the last check, and this is the first order |
| Stencil | as the quote form offers it for Standard PCBA | Not a separate stencil order `[from memory]` |

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
| `C-DECOUPLE-165` | C6, C8 | C49678 | **Basic** | 19.3 M | $0.0189 | 0 |
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
6. **Where JLC's rails and tooling holes land** (review #6-6). They must be on the rails, clear of the board: of the ground pour, the switch pads and the four mounting holes. A tooling hole drilled inside the outline goes through whatever is there. If the preview shows one on the board, ask JLC to put it on the rails; if it cannot, order with rails it adds outside the outline, not holes in the board.

### 6. Cost estimate, one design, 5 PCBs with 2 assembled

*Estimates.* JLC's live quote replaces this table. **The PCBA fees below are the
banked FAQ's, which are Economic PCBA's**; the order is Standard (*3*), whose
setup and stencil cost more and are not banked `[from memory]`, and the rails
add board area. Read the subtotal as a floor.

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
| Hand parts: J1 | not read | DigiKey 1175-1627-ND (CNC Tech 3220-10-0100-00), Active and stocked on 2026-11-21 (its BOM row carries the source) |
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
- **`J-CHAIN`**, CNC Tech 3220-10-0100-00, a vertical 2×5 1.27 mm shrouded box header.
  - Stocked at DigiKey on 2026-11-21, status Active (its BOM row).
  - Any keyed, shrouded, vertical 2×5 1.27 mm box header of the same pattern fits the pads; hold its height and mouth depth to `boards.chain_hdr_h` and `boards.chain_plug_proud` first (its BOM row says why).
  - An instrument takes `chain-connectors` of them: two on this pair of key boards and two on the main board.
  - The second source is not cleared: its drawing could not be banked (`datasheets/MANIFEST.csv`, the XKB row).
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
| Layers / board size | 2; Standard PCBA ≥ 70 × 70 mm, on rails below that | — | 2 layers; outline from the body CAD, under 70 mm across: JLC's rails (*2*, Delivery format) | ok, on rails |
| Thickness | a standard FR-4 thickness; Standard PCBA has no thickness, colour or finish limit | `boards.key_board_t` | the stackup, held by `pcb.py check` | ok |
| Track width | ≥ 0.10 | `rules: track_min` | `rules: track` (every signal track) | 2.5× |
| Track/pad spacing | ≥ 0.10 (pad to track 0.10; SMD pad to pad 0.15) | `rules: clearance` | the rule (the pour is filled at it) | 2× |
| Copper to routed edge | ≥ 0.20 | `rules: edge_clearance` | ≥ the rule (DRC) | +0.1 |
| PTH drill | 0.15–6.3; ≥ 0.5 recommended for PTH | `rules: drill_min` | 0.70 (J1) | ok |
| NPTH drill | ≥ 0.50 | — | the mount holes (`standoff_footprint`) and the switch poles | ok |
| PTH annular ring | ≥ 0.18 absolute, 0.25 recommended | `fab: annular_min` | **0.185, J1's pads on the sides facing a neighbour** (the 1.07 pad across a 0.70 drill) | **+0.005: at the absolute minimum** (*Open*) |
| Via hole / diameter | ≥ 0.15 / 0.25; diameter ≥ hole + 0.10 (0.15 preferred); a 0.2–0.25 hole under 0.45 costs more | `rules: via_drill`, `via`, `via_min` | the rule on every via; ring 0.20 | ok, and no via surcharge |
| Via hole to hole / pad hole to hole | ≥ 0.20 / 0.45 | `fab: hole_to_hole` | ≥ the rule (DRC) | ok |
| PTH to track | ≥ 0.28 (0.35 recommended) | `fab: hole_clearance` | ≥ the rule (DRC) | at JLC's minimum by rule |
| Mask expansion / bridge | 1:1 opening; bridge between pads ≥ 0.13 in white or black, 1 oz (0.10 in green) | board setup: expansion 0 | the narrowest pad gap: 0.20 between J1's pads (1.27 pitch − 1.07 pad) | 1.5× `[calc: 0.20 / 0.13]` |
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
   - It goes on the bottom side, standing straight out of the board, **its key slot toward the mouth end** (ADR 0017, *Amendment, 2026-11-21*). The silkscreen marks it: the header's outline, with a bar on the side the slot goes.
   - **Backward will not take the ribbon.** The 2×5 pad grid fits the header either way round. Turned 180°, its slot faces away from the socket's key, and the socket goes in only with the ribbon twisted, which then puts 3V3 on a ground pin (`key-chain-loom.md`). Fit it with its slot at the bar.
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
   - **Made up here, not bought assembled**: two IDC sockets crimped on a cut length of flat cable (its BOM row names the parts). Cut the cable to `mechanical/drc.echo` "key-chain ribbon to cut". Crimp both sockets on the **same face** of the ribbon with their keys facing the **same way along it**, pin 1 on the same edge conductor at both ends (`key-chain-loom.md`, *Pin numbering*).
   - **Meter every cable before it is first powered**, not only the first one. Check it by *Bring-up*, step 2.
   - Plug it in with the key plate held raised straight up off its columns, before the plate is screwed down (`routing.chain_service`, `routing.chain_raise`). That is the position its length was derived for.
   - Closed, the ribbon leaves both sockets flat toward the mouth and makes one fold between them (`key-chain-loom.md`). **The two ends are not interchangeable:** the socket whose key faces away from the fold goes on the main board, the one whose key faces the fold on this board. A socket that only goes in with the ribbon twisted is the wrong end.
4. **Conformal coat** (`MECH-COAT`), once the board has passed *Bring-up*: brush it on the bottom (parts) face only, with J1's mouth masked, and leave the switch side bare (`cluster-boards.md`, *Still open*, says why).

## Bring-up

Before the first key board goes into an instrument, check it on the bench.
**There are no test pads** (owner, 2026-09-29: a one-off build is probed by
hand). Everything is reached at J1's pin tails on the bottom, which carry the
whole chain (`hardware/interfaces/key-chain-loom/key-chain-loom.md`, the
key-board end):

| J1 pin | Signal |
|---|---|
| 10 | 3V3 |
| 1, 3, 5, 7, 9 | GND |
| 2 | SCK |
| 4 | SH/LD |
| 6 | SER |
| 8 | QH |

A clip lead on the header's pin tails, or a spare ribbon with an IDC plug cut
open, is the bench harness.

1. **No shorts.** Measure J1 pin 10 (3V3) to pin 9 (GND) with no power: it must not read as a short.
2. **Every cable's pinout, with a meter, before it is first powered.**
   - With both ends free, conductor 10 at one end must reach the other socket's position 10 (3V3), and conductor 2 its position 2 (SCK): a straight cable (`key-board-chain-pinmap`, on `key-chain-loom.md`).
   - No two neighbouring conductors may read as a short: a mis-crimped socket bridges them.
   - Check every cable, spares and replacements included.
3. **Tie SER.** Nothing drives SER on the bench, and a floating CMOS input draws current and shifts in undefined bits. Tie J1 pin 6 (SER) to a GND pin or to pin 10 (3V3).
4. **Power.** Feed 3.3 V between J1 pin 10 (3V3) and a GND pin (current-limited to ~20 mA).
   - With no key pressed, and SER tied, the draw should be near zero: the register's quiescent current is microamps `[datasheets/logic/SN74HCS165-ti-scls828a.pdf p.6]`. A reading of milliamps with no key pressed is a fault.
   - Each pressed key adds its pull-up's current (`key-scan-current`, on `key-switch-network.md`).
5. **The chain.** Drive SH/LD low then high, then clock SCK, and watch QH.
   - It shifts out this board's eight bits, H first: LH1..LH5, then the two marker bits and the free bit, in `key-marker-and-bits/allocation.yaml`'s order. Idle, each key bit and the free bit read high, and the markers read the pattern `marker-bits` gives this device.
   - Each key reads low while pressed.
   - Clocks past the 8th shift in the level SER is tied to.
   - Firmware normally does this; with a logic analyser on J1's pins it is visible without one.
6. **The rail, in the instrument.** On the real main board and ribbon, scope the key board's VCC (J1 pin 10 to a GND pin, or across C6) while the chain shifts. `FB-CHAIN` and `C-DECOUPLE-165` form a lightly damped LC (the `FB-CHAIN` row). The simulation (`hardware/interfaces/key-chain-loom/sim/`, `rail-as-ordered`) keeps this rail well inside its limit with C7 fitted, and inside it even without C7 (`rail-without-bulk`), so expect at most a small ring after each burst and each key change. A larger one means the bead or the ribbon is not what the simulation assumes: record it in *Revisions*. The bench supply has no bead, so this step needs the main board.

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
| C6 | `C-DECOUPLE-165` | the register's decoupler, at VCC (pin 16) |
| C8 | `C-DECOUPLE-165` | the register's second decoupler, under its ground pin 8 (review #6-5) |
| C7 | `C-BULK-CHAIN` | the rail's reservoir, beside J1's 3V3 pin |
| U1 | `U-KEYS` | the register, SN74HCS165 |
| J1 | `J-CHAIN` | the key chain's header |
| H1-H4 | (board only) | the corner mounts' holes |

**Parts side (bottom):** every part's reference beside it. Each key's three
network parts carry theirs the same way round the network, as the parts sit
round the switch (the two resistors' along them, beside the column), with the
key's name (LH1..LH5) beside its capacitor;
J1's outline and the bar on its slot side; `MOUTH` and an arrow at the
mouth end; the title block (`layout.yaml` `silk:`).

**Switch side (top):** each switch's reference and key (`SW1 LH1`) beside it;
J1's reference, where it is soldered;
`MOUTH`; the title block again (`silk:` `top_at`).

## Revisions

| Rev | Date | What changed | Where |
|---|---|---|---|
| A | 2026-09-27 | First layout: every key's network the same T in the same place round its switch, six test pads in one row (QH, SER, GND, SCK, SH/LD, 3V3), C7 (`C-BULK-CHAIN`), silkscreen on both sides, no acute track junction (`pcb.py check` tests every join, a track ending mid-track included). Not yet ordered; re-laid out on the same date for the screwed corner mount (keep-outs from the nut and the spacer/washer; ADR 0020 Amendment 3 then moved the heads from plugged bores into blind pockets, which changes nothing on the board); on 2026-09-28, C7 made a fitted, machine-placed part (it had been a do-not-fit footprint; owner: it costs cents) and J-CHAIN's pads lengthened on their free side; the same day the corner mounts went to M2.5 for PEM studs pressed flush into the plate (ADR 0020 Amendment 4: larger holes and keep-outs, mounts 0.2 further in), and the washer dropped, the spacer taking its length; on 2026-09-29 re-laid out for the cassette's columns (ADR 0025): no bonded mount (Amendment 5's is superseded), the mouth end 0.6 and the tail end 0.2 longer, J-CHAIN 0.5 further toward the tail and the register, its decoupler, R11 and C7 moved 0.5 with it; on 2026-10-03 re-laid out for the KS-33's pin holes, Gateron's 3.0 mm on 3.4 mm pads (issue #6-1; ADR 0020 Amendment 8), each key's network 9.0 mm from its switch so its labels clear the bigger pads; on 2026-10-05 the mouth end lengthened and its two mounts moved with it, so the columns keep `hardware.col_web_min` of plate from the thumb switches' cutouts (issue #43; ADR 0025, Amendment 2026-10-05 (2)): the outline's mouth edge, H1, H2, their keep-outs and the pour's edge moved, every part and track where it was | git history of this directory |
| B | 2026-10-03 | C8, the register's second decoupler (the shared REG sheet gained it for review #6-5; the right-hand board's C9), placed by hand under U1's ground pin 8 on the bottom face: its 3V3 pad squared onto the 3V3 track's 45-degree run, its ground pad onto pin 8's ground line, both 0.4 mm. Nothing else moved. `pcb.py check` passes. Not yet ordered | `key-board-lh.kicad_pcb`, `layout.yaml` |
| C | 2026-11-20 | Laid out again, by hand (issue #48, ADR 0030): no router. `J-CHAIN` turned to face the mouth (ADR 0017, *Amendment, 2026-11-20*); the chain bus under the register; each key's resistor and capacitor outside its switch's pins; all signal and power copper on the parts face with no via; the switch-side face one whole ground plane and no pour on the parts face; relief spokes on every pin the plane joins. Reviewed by the owner as placement, then as copper. `pcb.py check` passes. Not yet ordered | `lh_layout.py`, `key-board-lh.kicad_pcb`, `layout.yaml` |
| D | 2026-11-21 | `J-CHAIN` is a vertical 2×5 header (ADR 0017, *Amendment, 2026-11-21*; issue #49): new footprint, pinned as the main board's, where the body CAD stands it; the chain bus and 3V3 redrawn from its even row into the register, C7 moved beside its 3V3 pin. Nothing else moved. `pcb.py check` passes. Not yet ordered | `lh_layout.py`, `key-board-lh.kicad_pcb`, `key-board-lh.kicad_sch` |
| — | 2026-10-04 | Silkscreen and title block read `rev A  2026-10-03` again, not B (review #6-7; the rule below). No copper moved; renders and `fab/` re-written | `key-board-lh.kicad_pcb`, `layout.yaml` `silk:` |

**The letters in this table are design history.** The silkscreen and title
block read `rev A` until a board has been fabricated, and the next order is B:
the rule for every board is the main board's
(`hardware/boards/main-board/README.md`, *Ordering it*, **Revision**; ADR 0020,
*Amendment 9*). So a change before the first order adds a row here and moves
only the date, in the title block, the silkscreen text and `layout.yaml`
`silk:` (so a re-layout keeps them); then re-render. Record any correction an
order needed (a part rotation in JLC's preview, a drill that did not fit) in
the row.

## Open, and what decides each

| Open | Decided by |
|---|---|
| **The switch positions: check on the boards in hand (rev A).** Final for rev A (owner, 2026-10-04; ADR 0010, *Amendment, 2026-10-04*): `config/body.yaml` `layout.lh_gaps`, `layout.lh_offsets` and the rest are `settled` | the rev A boards in hand; a change is rev B |
| The socket's stand-out from the header's mouth and its cable face's height, `boards.chain_plug_proud` and `boards.chain_plug_cable`, read off the two drawings: they set the room between the two mated sockets and the fold's radius (`drc.echo` "key-chain sockets clear of each other, mouth to mouth") | M4, the first mated pair |
| The mount's spacers, faced to `hardware.kb_spacer_l` (no stocked M2.5 spacer has that length), and the column's standoff and screw (`MECH-COL-STANDOFF`, `MECH-COL-SCREW`) | the first fit; M4, with the parts bought |
| The board depth at the hardware's tolerance limits: the worst case reaches the window's shoulder end (`drc.echo` "key-board depth at the hardware's tolerance limits") | the first board, fitted |
| The register's supply: JLC's stock is thin (above) | the first order |
| J-CHAIN's second source: the XKB part at LCSC is not cleared until its drawing is banked (above) | its drawing |
| J-CHAIN's pads' ring is at JLC's absolute minimum on the sides facing a neighbour. The 1.27 mm pitch both ways leaves no room there. The pads are lengthened on their free side instead (`hardware/lib/README.md`, the IDC header's row); the hole is the one the header's drawing asks for (`datasheets/connectors/CNCTECH-3220-XX-0100-00-1.27MM-BOX-HEADER-VERTICAL.pdf`, *Recommended PCB layout*) and stays (pre-fab review, issue #52 F6). Ask JLC's review to accept the thin side | the first order |
| Part orientation in JLC's placement preview. The CPL carries JLC's convention and each part's offset from JLC's own footprint (*Ordering*, 4), but no order has yet confirmed it | the first order's preview (*Ordering*, 5); record any correction in *Revisions* |
| The main board's end of the ribbon | the main board's layout |
