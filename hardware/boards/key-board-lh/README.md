# Left-hand key board — `key-board-lh`

The left hand's five keys (LH1–LH5) and their register. The board is screwed to
the underside of the key plate (ADR 0020), and one IDC ribbon runs from it to
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
  keep-out: the nut's and the spacer's/washer's footprint, each grown by
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
- `route_first:` names the nets that must be routed before the key lines:
  those reaching `J-CHAIN`'s far (odd) row, which a track can reach only from
  behind the header.
- `connect_first:` names pad-to-pad connections routed before everything,
  each with the `max_mm` that `pcb.py check` then holds it to: here the
  decoupler's return to the register's ground pin. Name the new board's pads.
- `parts:` places everything else: the register, its decoupler, the free-bit
  pull-ups, `C-BULK-CHAIN-<suffix>` and the six test pads.
- `rules:`, `fab:` (the board house), `silk:` (title, revision, date; `at`
  for the parts side, `top_at` for the switch side, `legend_at` for the test
  pads' legend),
  `standoff_footprint:`, `route:`, `ground_net:` and `power_nets:` are copied
  as they are. `power_nets:` names that board's rail.

Then run `pcb.py layout`, and move parts in `layout.yaml` until `pcb.py check`
passes. Write the board's README from this one.

## Ordering it — JLCPCB

Everything below was checked against JLCPCB's banked pages
(`datasheets/fab/`) on 2026-09-27.

**What to upload:**
1. **PCB:** `fab/` zipped: every `.gbr` file, both `.drl` files and the `.gbrjob`.
2. **Assembly BOM:** `fab/key-board-lh-bom-jlc.csv`.
3. **Assembly CPL:** `fab/key-board-lh-cpl-jlc.csv`.

**The bare board** — the options to pick:

| Setting | Value | Why |
|---|---|---|
| Layers | 2 | |
| Quantity | 5, the fewest JLC makes `[from memory]`; assemble 2 | Economic PCBA assembles 2–30 boards `[datasheets/fab/JLCPCB-PCBA-CAPABILITIES.pdf, "PCB Specs for Economic PCB Assembly"]`. The right-hand board is a different design and a separate order, and it has no layout yet (below) |
| Thickness | `boards.key_board_t` | `config/body.yaml` (ADR 0020); a standard JLC thickness `[datasheets/fab/JLCPCB-PCB-CAPABILITIES.pdf]`. `pcb.py check` holds the stackup to it |
| Material | FR-4 | |
| Surface finish | HASL lead-free | At this thickness, Economic assembly offers HASL only `[JLCPCB-PCBA-CAPABILITIES.pdf]`. `layout.yaml` `fab: finish`, in the stackup and the Gerber job file |
| Solder mask / silkscreen | Green / White | `layout.yaml` `fab:`. Economic assembly at this thickness offers green or black |
| Copper | 1 oz | `layout.yaml` `fab: copper_oz` |
| Outline | from the Gerbers | The outline is the body CAD's key board, `mechanical/export/key-board-lh.dxf`, which holds only the outline (its size is there). The four M2 holes are footprints placed from `mechanical/export/pcb-geometry.echo`, in the NPTH drill file |

**The limits this board is held to.** JLCPCB's own limits are banked in
`datasheets/fab/` and written into `layout.yaml` `fab:`. The first layout
copied them into the board's design rules (`key-board-lh.kicad_pro`), and every
`pcb.py check` compares the two, so neither can drift from the other
unreported. To change a limit, change both: in KiCad's Board Setup and in
`layout.yaml`, and say why. The silkscreen limits that KiCad's DRC does not
test are checked by `pcb.py` itself (above).

**Assembly: Economic PCBA, bottom side only**

- **Every machine-placed part is on the bottom** (the side facing the main board).
  - The designators are the plain references on the silkscreen (R1, C6, U1); *The silkscreen*, below, maps each to its BOM row.
- **Check every part's orientation in JLC's placement preview before you pay.**
  - The CPL carries KiCad's own rotations, with KiCad's column headers renamed to JLC's (the banked guide's Method 1, `datasheets/fab/JLCPCB-KICAD-BOM-CPL-GUIDE.pdf`).
  - That guide attributes automatic rotation corrections only to the Fabrication Toolkit plugin (its Method 2). This flow does not use the plugin, so **nothing corrects the rotations**: JLC's preview is the only check.
  - Bottom-side parts are the ones most often shown wrong `[from memory]`, and every part here is on the bottom.
  - The register's (U1) pin 1 is marked on the silkscreen, and that is the one to look at.
  - Record any correction the first order needs in *Revisions* (below), so the next order does not rediscover it.
- **Which parts are in the order.** The resistors and capacitors are JLC **Basic** parts. The register, TI's SN74HCS165DR, is an **Extended** part, not a "Preferred" one, so it carries JLC's feeder-loading fee on Economic assembly ("$3 per extended component", FAQ 6 `[datasheets/fab/JLCPCB-PCBA-FAQ.pdf]`).
  - **Its stock at JLC is thin**: about 112 on 2026-09-27 `[web https://jlcpcb.com/partdetail/TexasInstruments-SN74HCS165DR/C2864745, 2026-09-27]`. Digi-Key held 5,845 at $0.73 the same day `[web https://www.digikey.com/en/products/detail/texas-instruments/SN74HCS165DR/13563029, 2026-09-27]`. **If JLC is short, buy it from Digi-Key** and either send it to JLC as a consigned part or leave it off the JLC order and fit it by hand (SOIC-16, 1.27 mm pitch).
  - **Do not let JLC substitute a plain 74HC165** or a 74LV165A: the part must have Schmitt-trigger inputs with no input transition-rate limit (the `U-KEYS` row says why).
  - Library status as of 2026-09-27 `[web, JLC part pages: jlcpcb.com/partdetail/…/C17408, …/C17520, …/C49678, …/C53134, …/C2864745, and JLC's component-search API]`. It can change, so check it at order.
  - The other part numbers are not repeated here. They are on the sheets, and in `fab/key-board-lh-bom-jlc.csv`.
- **Not in the order:**
  - SW1-SW5 and J1 (`J-CHAIN`), which are in `fab/key-board-lh-hand-assembly.csv`;
  - C7 (`C-BULK-CHAIN`), a do-not-fit footprint (*Bring-up*, step 6);
  - the test pads and the M2 holes, which are copper and drill only.
- **Bought separately, for the hand assembly.** Only the first two are on the hand list. Sourcing facts below were read on 2026-09-27; check stock at order.
  - **The switches** (BOM row `SW1-n`): Gateron **KS-33H10B050NN-Y24**, Low Profile 2.0 Red, the code on the sheet and the hand list. **Order `-Y24` exactly.** The suffix is the bottom housing's colour, not a year: `-Y24` is black and `-Y31` white. The white-housing spec gives a longer total travel than the black one the body is drawn from (`switch.total_travel`), which would break the flush rule `[datasheets/mechanical/GATERON-KS-33-VENDOR-SPEC-DRAWING.pdf; datasheets/mechanical/GATERON-KS-33-SPEC-WHITE-HOUSING-KS-33H10B050NN-Y31.pdf]`. Not the Silent, not the Low Profile 3.0. Gateron's own store sells the black-housing Red `[web https://www.gateron.com/products/gateron-ks-33-low-profile-switch-set, 2026-09-27]`; whether it ships from a US warehouse is unverified. US sellers found (e.g. LumeKeebs) sell "KS-33 2.0 Red" without naming the housing or the code `[web https://lumekeebs.com/products/gateron-ks-33-low-profile-2-0-mechanical-switches, 2026-09-27]`, so check the code on the packaging.
  - **`J-CHAIN`**, Samtec SHF-106-01-L-D-RA. JLC/LCSC had none (C17202657, stock 0 `[web, JLC API, 2026-09-27]`). DigiKey SHF-106-01-L-D-RA-ND had **only 8 in stock**, with a **4-week factory lead time** `[web https://www.digikey.com/en/products/detail/samtec-inc/SHF-106-01-L-D-RA/8410402, 2026-09-27]`. Eight covers one instrument's two boards with few spares; failing that, Samtec direct (reel variants and samples). Its sourcing is open (its BOM row, and *Open* below).
  - **The corner mount hardware**: one screw, spacer, washer and nut per corner, four corners per board, and a dot of epoxy per head (`ADH-EPOXY`). What each must be, the quantities and the sources are the `MECH-KB-*` rows in `hardware/unplaced.csv`; their prices are not repeated here. The mount is described in *Assembling*, step 2.
  - **`CBL-CHAIN`**, one per board, ordered as in *Assembling*, step 3.
  - **C7** (`C-BULK-CHAIN`), only if *Bring-up* step 6 needs it: Samsung CL21A106KAYNNNE (10 µF X5R 0805), LCSC C15850, a JLC **Basic** part `[web https://jlcpcb.com/partdetail/SamsungElectroMechanics-CL21A106KAYNNNE/C15850, 2026-09-27; datasheets/discrete-and-power/SAMSUNG-CL21A106KAYNNNE-SPECSHEET.pdf]`. It is do-not-fit on this board, so it is in no order; this is the part to fit.
- **A US-sourced hand build.** The UNI-ROYAL resistors stay for JLC assembly: they are JLC **Basic** parts, with no feeder fee. No US distributor stocks them (DigiKey had no result `[web https://www.digikey.com/en/products/result?keywords=0805W8F1000T5E, 2026-09-27]`). For a board built by hand from US stock, use YAGEO RC0805FR-07100RL (100R) and RC0805FR-072K2L (2k2): DigiKey 311-100CRCT-ND / 311-2.20KCRCT-ND; LCSC C105577 / C114561, which are JLC **Extended** `[web https://www.digikey.com/en/products/result?keywords=RC0805FR-07100RL; …=RC0805FR-072K2L; https://jlcpcb.com/partdetail/YAGEO-RC0805FR07100RL/C105577; …/YAGEO-RC0805FR072K2L/C114561, all 2026-09-27]`. The capacitors' parts are already at DigiKey.
- **One instrument needs two key boards, and the right-hand board cannot be ordered yet.** `hardware/boards/key-board-rh/` is schematic only: no layout, no `fab/`, no README. It is laid out from this one (*Making the next board*, above).
- **The sheets are the source of every part number.** To change a part, set its `LCSC`/`MPN` fields in the circuit sheet and re-render. The BOM row (`hardware/cluster/bom.csv` etc.) says what the part must be; the sheet says which one is bought.

## Assembling the rest by hand

1. **J1** (`J-CHAIN`; the stand-in is on its BOM row).
   - It goes on the bottom side, **mouth toward the tail**. The silkscreen marks it: an arrow beside the header points out of its mouth, and pin 1's dot is behind the pins, away from the mouth.
   - **Backward is 3V3 on ground.** The 2×6 pad grid fits the header either way round. Turned 180°, the header puts the ribbon's 3V3 on a ground pin (`key-chain-loom.md`). Fit it with its mouth at the arrow.
   - Seat it flat and solder it from the top (switch) side.
   - The plate has **no window** over the tails. Seated flat, they stop short of the grounded plate (`mechanical/drc.echo` "J-CHAIN pin tails clear of the key plate"), so do not trim them or leave the header standing proud.
2. **The corner mounts, and the switches.** Each of the board's four corners hangs from the plate on one screw (ADR 0020, Amendment 3; the section is `mechanical/renders/section-kb-mount.png`). From the top down: an M2 × 8 ISO 4762 socket-head screw whose head sits on the plate's top face, the plate's clearance hole (`hardware.kb_plate_hole`), then below the plate a Würth 9774020943R spacer, an ISO 7092 washer (the small series, not DIN 125), the board, and an ISO 4032 nut underneath. Once the lid is bonded, each head sits in a blind pocket drilled up into the wood top's underside (`hardware.kb_pocket_d`); nothing goes through the playing face. The parts are the `MECH-KB-*` rows.
   - **All of this happens before the plate is bonded to the wood.** The heads cannot be reached afterwards.
   - **The spacer and the washer are not optional**: with the plate they set the board's depth (`drc.echo` "key-board mount sets the board depth"). Check a sample washer with calipers before fitting: its thickness range is `hardware.kb_washer_t_range`.
   - Clip the five KS-33s into the key plate's cutouts.
   - Drop a screw down through each of the board's four holes in the plate, from its top face. Below the plate, put a spacer, then a washer, on each screw.
   - Lift the board onto the switch pins and the four screws, and run a nut onto each screw from underneath. Tighten each nut while holding its head with a 1.5 mm hex key from above.
   - **Epoxy each head to the plate** (`ADH-EPOXY`): a dot beside the head, where its edge meets the plate, kept inside the pocket's footprint (`hardware.kb_pocket_d`), below the head's top and out of its socket, so it stands no taller than `hardware.kb_pocket_clear` above the head. Let it cure before anything torques a nut again. It is what lets the nuts come off from below once the lid is bonded: without it a loosened nut spins its screw.
   - **Then** solder the switch pins, from the bottom. Soldering with the board screwed on at depth is what holds it at the depth the pins were designed for (`switch.pcb_below_seat`). How far the hardware's tolerances can move it is `drc.echo` "key-board depth at the hardware's tolerance limits" (*Open* below).
   - **Last, the plate is RTV-bonded to the wood top** (ADR 0009's adhesives table), the heads going up into their pockets. Keep the beads off the pockets. For service afterwards, undo the nuts from below; the epoxied heads stay put.
3. **The ribbon** (`CBL-CHAIN`).
   - **Order it as** `FFSD-06-D-<code>-01-N-RN2`. `<code>` is `mechanical/drc.echo` "key-chain cable to order (FFSD length code)", **written with two digits before the point**: Samtec's field is `XX.XX` `[datasheets/connectors/SAMTEC-FFSD-XX-X-XX.XX-01-PRINT.pdf, part-number block]`, so a length under 10 in takes a leading zero, as DigiKey lists FFSD-06-D-06.00-01-N `[web https://www.digikey.com/en/products/detail/samtec-inc/FFSD-06-D-06-00-01-N/6678085, 2026-09-27]`. Whether Samtec accepts a length that is not on its catalogue's list, to 0.01 in, is **unverified**: confirm the full part number in Samtec's configurator before paying, since the series is non-returnable. It is the overall length in **inches**, over both sockets, as the FFSD print measures it, with the print's −0.125 in tolerance already covered. `-RN2` reverses the notch on the second socket. **Do not type the millimetre length** ("key-chain ribbon length (derived)") into the part number: read as inches, it orders a cable about 25 times too long.
   - **Meter every cable before it is first powered**, not only the first one. Check it by *Bring-up*, step 2.
   - Plug it in with the lid laid face down beside the body, off its far edge, before the lid is screwed down. The body stands on its U-bolt with a block under its other end (`routing.chain_service`). That is the position its length was derived for.
   - With `-RN2`, the main board's socket's cable leaves **upward** and the key board's leaves **downward**. The two face each other, and closed, the ribbon folds into a flat hairpin between the two plugs' heights (`key-chain-loom.md`). **A cable whose ends both leave downward is a standard cable, without `-RN2`, and it is wrong.**

## Bring-up

Before the first key board goes into an instrument, check it on the bench. The
six test pads are on the bottom, TP1-TP6, and the legend beside the title says
what each probes: TP1 QH, TP2 SER, TP3 GND, TP4 SCK, TP5 SH/LD, TP6 3V3.

1. **No shorts.** Measure TP6 (3V3) to TP3 (GND) with no power: it must not read as a short.
2. **Every cable's pinout, with a meter, before it is first powered.**
   - With both ends free, conductor 10 at one end must reach the other socket's position 3 (3V3), and conductor 2 its position 11 (SCK).
   - That is the `-RN2` map, key pin = 13 − main pin (`key-chain-loom.md`). The map is symmetric, so either end can be taken as the main-board end.
   - A cable without `-RN2` looks right on the drawn route and puts 3V3 on a ground pin. Nothing mechanical shows it, so check every cable, spares and replacements included.
3. **Tie SER.** Nothing drives SER on the bench, and a floating CMOS input draws current and shifts in undefined bits. Tie TP2 (SER) to TP3 (GND) or TP6 (3V3) (the `TP-CHAIN` row).
4. **Power.** Feed 3.3 V between TP6 (3V3) and TP3 (GND) (current-limited to ~20 mA).
   - With no key pressed, and SER tied, the draw should be near zero: the register's quiescent current is microamps `[datasheets/logic/SN74HCS165-ti-scls828a.pdf p.6]`. A reading of milliamps with no key pressed is a fault.
   - Each pressed key adds its pull-up's current (`key-scan-current`, on `key-switch-network.md`).
5. **The chain.** Drive SH/LD low then high, then clock SCK, and watch QH.
   - It shifts out this board's eight bits, H first: LH1..LH5, then the two marker bits and the free bit, in `key-marker-and-bits/allocation.yaml`'s order. Idle, each key bit and the free bit read high, and the markers read the pattern `marker-bits` gives this device.
   - Each key reads low while pressed.
   - Clocks past the 8th shift in the level SER is tied to.
   - Firmware normally does this; with a logic analyser on the test pads it is visible without one.
6. **The rail, in the instrument.** On the real main board and ribbon, scope the key board's VCC (TP6 to TP3) while the chain shifts. `FB-CHAIN` and `C-DECOUPLE-165` form a lightly damped LC (the `FB-CHAIN` row). The simulation (`hardware/interfaces/key-chain-loom/sim/`, `rail-as-ordered`) keeps this rail inside its limit with C7 empty, so expect a small ring after each burst and each key change, not a large one; if the real rail rings more than the simulation says, fit C7 (the part is under *Ordering it*, bought separately). The bench supply has no bead, so this step needs the main board.

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
| C7 | `C-BULK-CHAIN` | the rail's reservoir, do not fit (*Bring-up*, step 6) |
| U1 | `U-KEYS` | the register, SN74HCS165 |
| J1 | `J-CHAIN` | the key chain's header |
| TP1-TP6 | `TP-CHAIN` | the test pads: QH, SER, GND, SCK, SH/LD, 3V3 |
| H1-H4 | (board only) | the corner mounts' holes |

**Parts side (bottom):** every part's reference beside it. Each key's three
network parts carry theirs the same way round the network, as the parts sit
round the switch (the two resistors' along them, beside the column), with the
key's name (LH1..LH5) beside its capacitor. `DNP` after C7's; the test pads'
references beside them, and a legend by the title saying what each probes;
J1's pin 1 dot and an arrow out of its mouth; `MOUTH` and an arrow at the
mouth end; the title block (`layout.yaml` `silk:`, the legend at `legend_at`).

**Switch side (top):** each switch's reference and key (`SW1 LH1`) beside it;
J1 with pin 1's dot and the arrow out of its mouth, where it is soldered;
`MOUTH`; the title block again (`silk:` `top_at`).

## Revisions

| Rev | Date | What changed | Where |
|---|---|---|---|
| A | 2026-09-27 | First layout: every key's network the same T in the same place round its switch, six test pads in one row (QH, SER, GND, SCK, SH/LD, 3V3), C7 (`C-BULK-CHAIN`) footprint (do not fit), silkscreen on both sides, no acute track junction (`pcb.py check` tests every join, a track ending mid-track included). Not yet ordered; re-laid out on the same date for the screwed corner mount (keep-outs from the nut and the spacer/washer; ADR 0020 Amendment 3 then moved the heads from plugged bores into blind pockets, which changes nothing on the board) | git history of this directory |

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
| The wood species of the top: the owner may use a harder wood than oak. It sets whether `hardware.kb_pocket_wall` and `hardware.kb_pocket_skin` (placeholders, `[from memory]`) are enough wood round and over each head pocket | the owner, before the top is cut; M2 pockets a scrap of it |
| The board depth at the hardware's tolerance limits: the worst case reaches the window's shoulder end (`drc.echo` "key-board depth at the hardware's tolerance limits") | the first board, fitted |
| The register's supply: JLC's stock is thin (above) | the first order |
| J-CHAIN's source: none at JLC, 8 at DigiKey on 2026-09-27 (above); buy the stand-in there or from Samtec, or validate a stocked alternative against its print (its BOM row) | the first order |
| J-CHAIN's pads' annular ring is at JLC's absolute minimum, not its recommended one: the 1.27 mm pitch leaves no room for a larger pad (`hardware/lib/README.md`, the IDC header's row) | the first order |
| Whether Samtec takes the FFSD length code to 0.01 in (*Assembling*, step 3) | Samtec's configurator, at order |
| Part orientation in JLC's placement preview (above) | the first order |
| C7 (`C-BULK-CHAIN`) fitted or not | *Bring-up*, step 6 |
| Conformal coating of the key boards (`cluster-boards.md`, *Still open*) | ADR 0009, M4 |
| No 3D model of J-CHAIN in the renders (Samtec's is behind a login; `datasheets/.manifest-R12.csv` records the attempt) | nothing blocks on it |
| The main board's end of the ribbon | the main board's layout |
