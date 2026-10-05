# Body CAD — design notes

> **Status:** first model, 2026-09-26. Back to the [README](README.md).

How the stack is modelled, where the numbers come from, and what the first
model found. **This page does not restate dimensions or DRC results** — they
move, and a number copied here is the defect this repository keeps finding.
Values live in `config/body.yaml` and `config/key-layout.yaml` (each with a
source and a status); measured results live in [`drc.echo`](drc.echo),
regenerated on every build.

## Where the numbers come from

Three kinds, and `config/body.yaml` marks every leaf with one:

- **settled** — read off a banked document or decided in an ADR. The KS-33
  geometry, the NE8FAV's flange, holes and footprint, the Matrix board outline, the plate
  thickness (the register's `plate-thickness`).
- **nominal** — an ADR's working estimate: the oak thicknesses, the length
  budget, the side thickness.
- **tbd** — no document gives a number, so the model carries a placeholder and
  a `decided_by`. `drc.echo`'s second line lists every one in play, so no
  result can quietly rest on a guess.

Vendor geometry is **imported, not retyped**: the KS-33 is the banked STEP
solid meshed by `tools/cad.py`, and the etherCON is drawn from its banked
drawing.

## How the stack is modelled

- **The cassette** (owner, 2026-09-29; ADR 0025) is everything inside the
  shell as one unit: the key plate, one bottom plate, the two key boards and
  the main board, tied by a **column** at each of the key boards' eight
  corners. It is built and tested on the bench, dropped into the shell and
  bonded with RTV to the oak top and bottom; service is by cutting the
  silicone. Nothing screws into the wood but the U-bolt. A column, from the
  bottom: a PEM FHL-M2.5 stud pressed into the bottom plate, head flush in its
  underside; a spacer; the main board; an M2.5 female-female hex standoff
  threaded onto the stud and faced to the gap up to the key board (*"column
  standoff length (derived)"*); the key board; a spacer; the key plate; an
  M2.5 low-head screw down into the standoff, its head in a blind pocket in
  the oak top's underside (`export/oak-pockets.dxf`). The columns are
  vertical (*"columns vertical: the main board's mounts under the key
  boards'"*), and their threads, both ends of the standoff, are checked
  (*"column: stud thread in the standoff"*, *"column: screw thread in the
  standoff"*, *"column: stud and screw ends apart in the standoff"*). The
  cassette's height against the shell's, and what the silicone takes, is
  *"cassette height at the hardware's tolerance limits"*.
- **The key plate** is under the oak top, because keys are **flush with the
  top face at full travel** (decided 2026-09-26, ADR 0009). The oak top's
  thickness is not a parameter: it is the cap's height above the seat less
  the travel, derived in the model and printed in `drc.echo`. The oak carries
  one clearance hole per cap through it and, from below, a blind pocket over
  each column screw's head; the playing face is unbroken (*"column screw
  pockets clear of the wood top's cuts"*, *"column screw pockets leave wood
  over them"*). Each key board is a rectangle across the cavity with a column
  in each corner, `hardware.kb_mount_inset` in from both edges for the
  standoff's keep-out; the mouth ends run `boards.kb_end_margin` past the
  first cutout, far enough that the mouth columns clear the first thumb row,
  and the tail ends `boards.kb_tail_margin` past the last (*"key-board tail
  margin, least"* prints how short it may be). The screws' heads bear on
  plate metal (*"column screw heads bear on the key plate"*) and the spacers
  stay off the switch cutouts (*"key-board spacers clear of the switch
  cutouts"*). The plate + `hardware.kb_spacer_l` is the key boards' depth, at
  the depth the KS-33's pins allow (`docs/reference/ks33-geometry.md`;
  `switch.pcb_below_seat`): *"key-board mount sets the board depth"*, and
  *"key-board depth at the hardware's tolerance limits"*, a NOTE — the first
  board confirms the fit. The standoffs keep off the chain headers
  (*"column standoffs clear of the chain headers"*), and the count is
  *"key-board mounts"*. The wood's species is open (a hardwood, the owner's;
  ADR 0009).
  The key board's chain header's through-hole pin tails come up through the
  board toward the grounded plate and stop short of it (*"J-CHAIN pin tails
  clear of the key plate"*), so the plate is not cut over them
  (2026-09-27; the first layout cut a window there).
- **Thumb keys are flush with the bottom face at full travel** too (same date).
  The bottom plate is on the oak bottom's inside face, so the oak bottom is
  derived by the same rule as the oak top.
- **There is no display board** (owner, 2026-09-26: "remove the upper
  display ... we can do all this with the matrix led, keep things more
  compact and cleaner"; ADR 0015). The LED matrix on the top face is the
  instrument's only display, configuration is over Wi-Fi in a configuration mode since issue #37 (ADR 0015's amendment), and the body lost the
  display band at the mouth end.
- **The sides sit between the oak panels, in grooves** (decided 2026-09-26).
  Oak top and bottom run the full width; each acrylic side is one sheet
  standing in a groove along each panel's inner face, behind an oak lip
  (`stack.side_inset`, `groove_depth`, `groove_clear`). Glued into the bottom
  grooves, the U is still one sub-assembly; the top grooves locate the lid.
  **The grooves are the one cut in the stack that is not a through-cut** — a
  saw or router pass, exported on their own as `export/oak-grooves.dxf` so
  the through-cut outlines stay clean. The plate sits between the sides.
- **Thumb keys** mount upside down in the bottom plate on the oak bottom's
  inside face; the through-cut in the oak is the recess (ADR 0009). One plate
  serves both thumb clusters, the length of the main board (ADR 0025); every
  one of the main board's mounts has a stud pressed into it (*"bottom-plate
  studs clear of the plate's edges and cutouts"*, *"bottom-plate spacers clear
  of the thumb switch cutouts"*).
- **Key positions**: a key with `x`/`y` in `config/key-layout.yaml` is placed
  there. A key without one is placed on the provisional layout in
  `config/body.yaml`, where each run's spacing is its length over its gaps —
  there is deliberately no separate pitch value.
- **Every part is a 2D module** in its own sheet frame; the assembly only
  places them. `export/*.dxf` are those modules exactly.

## The length is derived

Since 2026-09-26 the owner's rule is *minimize total length*: the body is the
keys, a little at the mouth, and room for the connector at the tail. So the
model computes the length rather than reading it (`config/key-layout.yaml`'s
`envelope.length` is null), and `drc.echo` prints it with what set each end.
Several things can claim each end, and the largest wins:

- **Mouth end:** the first top cap plus `layout.mouth_extra`; the first
  thumb recess; or the breath sensor, which must stop short of the first
  thumb row's pins — and then the equal bands (below).
- **Tail end:** the **LED matrix on the top face, centred** after the keys
  (owner, 2026-09-26), with the etherCON and its adapter behind it; or the
  key board, J-UMB, the adapter and the etherCON's depth in a row; or the right-thumb cluster against the tail cap. (There is no service
  cover since 2026-09-26.)
- **The tail is stacked** (owner, 2026-09-26: "it's unacceptable to go this
  long" and "the matrix can be up higher out of the way and still allow the
  connectors"). The Matrix **sits just under the oak top** below its window:
  the key plate stops short of it, so the board's top face comes up to the
  oak and its LEDs stand up into the window opening, under the acrylic
  (owner, same day: "led matrix tighter to the acrylic"). **Since 2026-10-03
  it is mounted on a carrier board of its own, hung from the oak top**
  (ADR 0021 amendment 2026-10-03; `boards.matrix_mount`): two headers through
  its pad rows stand it on the carrier (`boards.matrix_hdr_h`, *"Matrix's
  back-side parts clear the carrier"*), and the carrier hangs on three
  spacers from inserts in the oak (*"Matrix carrier hangs from the oak"*).
  It lifts off with the lid. Off the Matrix's mouth edge, **nothing with the
  lid on since issue #37**: the tail-face USB-C extension is gone, and the
  Matrix's own USB-C is a recovery port reached with the lid off. A recovery
  plug (a right-angle USB-C turned down, `openings.usb_plug_turn`) still
  fits: the carrier keeps its slot under the receptacle, the key plate still
  stops in front of it, and the oak keeps its pocket over it (*"recovery USB-C
  plug clear of the oak top"*; review #19 F1). Under it, the main board's tail end with
  J-UMB on it. Behind it, the etherCON (an NE8FAV,
  ADR 0021) on its **adapter board**, which stands the connector's full
  height parallel to the tail cap. The connector **stands on the floor**, and
  the body is thick enough for it (owner, same day: set the body rather than
  pocket the oak — `body-thickness`, ADR 0009). Past the plate's end the
  ceiling is the oak top, so it is the connector's flange, floor to oak,
  that sets the thickness. `drc.echo` itemises "behind the Matrix", confirms
  J-UMB passes under it, and gives the thinnest body that works. **With the matrix centred, anything in front of or
  behind it counts twice, and the gap between the hands copies the result** —
  a straight USB-C plug cost about 24 mm of body, which is why the extension's
  plug was right-angle until issue #37 took it away.
- **The lights are a row of LEDs on the main board** (ADR 0028; before it
  one strip, ADR 0016): `lighting.led_count` WS2815B-V1 at one pitch, equal
  margins to the main board's ends (ADR 0028 amendment 2026-10-03; the pitch
  is drc.echo's *"LED row on the main board"*), LEDs up down the board's
  centreline, between the thumb switches' two rows of pins, lighting both sides
  through the cavity. The row is shifted along the body so the U-bolt station
  falls midway between two LEDs (*"LED row on the main board"*, *"LED row off
  the U-bolt station"*). How evenly the cavity lights the sides is the
  diffusion test's question. It comes before the main board is ordered,
  because the count and pitch are fixed when the board is made; the layout
  goes ahead of it with the row as it is (owner's choice (b), ADR 0028 amendment).
- **Every outer oak edge is rounded, as if sanded** (owner, 2026-09-26):
  the top and bottom panels' long edges, the lips beside the acrylic, and
  both end caps' outer faces and corners, at `stack.edge_r`. It goes on after
  cutting (router or sandpaper), so the DXFs carry square outlines except
  the caps' corners. The radius stays under the lip width
  (*"sanded edge radius leaves the lips a flat"*). Both end caps are oak.
- **The matrix window is frosted acrylic, flush with the oak top, on a lip of
  oak** (owner, 2026-09-26): a rebate in the oak top's upper face as deep as
  the acrylic, over a smaller opening through the oak lip. Like the
  side grooves it is a router pass, not a through-cut, so it exports on its
  own (`export/oak-rebates.dxf`); the acrylic is `export/matrix-window.dxf`.
  `drc.echo` reports the lip and the LED-to-window distance, which is what
  decides how soft the pixels look. In practice the matrix sets it.
- **There is no carrier board, and one main board** (ADR 0017; owner,
  2026-09-26: "instead of individual bottom boards, and the center board,
  maybe we can do one big long board?"). The thumb switches, both thumb
  registers and the carrier's circuits are on one board at the thumb level,
  from the mouth cap to the end of the right hand, the full width inside the
  sides. Its parts face up; the two key boards connect to it by ribbons (below);
  the Matrix's ribbon comes down to it from the Matrix carrier, and it runs on past the right-hand key
  board to the etherCON's adapter, carrying J-UMB (ADR 0021). **That tail
  end is full width** (owner, 2026-10-02; `boards.main_tail`). It was a
  tongue as wide as the adapter, narrowed for lid screws that ADR 0025
  removed. The corner it gains held nothing at the board's height; the
  USB-C receptacle that stood over it went with issue #37, and **J-MIDI**, the
  MIDI jack's lead header, is proposed in it (*"main board's tail end runs full
  width beside the etherCON adapter"*, *"J-MIDI and its plug under the Matrix
  carrier"*). It is clamped in the
  U-bolt's stack, on a spacer from the bottom plate with a washer and the nut
  above, with a clearance hole for each leg (ADR 0022 point 7, ADR 0025). It
  has no edge notches. Every one of its mounts is on the bottom plate: a
  column under each of the key boards' corners, and end mounts at the mouth
  and on the tongue with a nut — an end mount with a column within
  `hardware.end_mount_merge_d` is dropped (*"end mounts dropped beside a
  column"*) (ADR 0022 point 8, ADR 0025; *"main board
  mounts on the bottom plate"*). Each mount is the stud, the spacer and the
  board, on a plated `PWR_GND` hole that grounds both plates. Its underside
  faces the grounded bottom plate over its whole length (*"main board
  underside room over the bottom plate"*, *"J-CHAIN pin tails clear of the
  bottom plate"*). It is as thin as the key boards and as deep below its
  switches' seat (*"main board mount sets its depth"*); the soldered thumb
  switches carry it between the mounts. The near row of thumb switches is
  turned 180° so their pins point away from the centreline and the LED row.
  (Before it: a centre board stacked between the thumb boards and the key
  boards — that history is in git and ADR 0017.)
- **Its parts have room** — `drc.echo` prints the height under the key boards
  and where none is overhead, and both clear the regulator block and the
  breath sensor. **The breath sensor is at the mouth end** (owner, with this
  board), ports toward the tail: the thumb switches'
  pins leave the LED row the centreline band, and the sensor is too wide to sit
  beside it (*"breath sensor fits at the mouth end"*; the mouth end also
  claims room for it, *"what the mouth end needs"*).
- **Board clearances are real ones** (`boards.board_clear`): the owner
  rejected a model that put one board 0.5 mm over another's parts
  (2026-09-26: "once components are installed you'd have issues").
- **Between:** the key gaps, and the space between the hands.

**Equal bands (owner, 2026-09-26).** The space before the left hand and the
space between the hands are the same: the larger either needs, measured as
the plan drawing labels them (body end to first key centre, last left key to
first right key). `layout.equal_bands` switches it; `layout.gap` is then only
a minimum.

**The gap between the hands matches the keys-to-matrix gap (owner, same
date)** — the clear space from the last left cap to the first right cap equals
the clear space from the last cap to the matrix window's near edge
(`layout.gap_matches_matrix`). It overrides the equal bands for the gap, so
the mouth end and the gap are no longer equal; `layout.gap` stays a minimum,
for the U-bolt and thumb rest underneath. `drc.echo` prints both clear gaps.

**The LED matrix is centred after the keys (owner, same date)** — midway
between the last cap's slot edge and the tail face — and **only the tail
grows for it** (`layout.matrix_centred`). The connector still has to fit
behind the matrix, so the tail must be at least the cap edge plus twice
(half the board + clearance + connector depth). That makes the tail the
longest band; `drc.echo` prints what the tail needs and confirms the centring.

Every render aims at the body's centre or tail (`origin` in `outputs.yaml`),
so a length change reframes nothing.

## What the first model found

Each item is a rule in `drc.echo`; read the current value there. These are
the questions M4 has to answer, and several contradict something an ADR
currently says. None has been fixed by editing a document: fixing them is a
decision, not a correction.

1. **The etherCON panel stack — resolved by a recess.** The NE8FAV mounts
   from behind a panel of `ethercon.panel_max` at most, and the oak tail cap
   is thicker. A router pocket from outside leaves exactly that much oak
   where the flange clamps; it takes the flange's outline and the PUSH tab,
   which stands in it (ADR 0021). Like the counterbores it is not
   in the tail cap's DXF, which carries the through-cuts; the tail-face
   figure and *"tail cap recess for the etherCON inside the tail face"* give
   it. *"etherCON PUSH tab against the tail face"* says how far the tab
   stands proud.
2. **The etherCON body is taller than the cavity — resolved by the owner.**
   The body is now thick enough to take the connector standing on the floor
   (`body-thickness`, 2026-09-26).
   *Rules: "etherCON body inside the cavity height", "body thickness takes
   the etherCON on the floor".*
3. **The lane beside the etherCON takes the MIDI jack** (issue #37; owner,
   2026-10-04: "on the bottom face, and then just do a connector to the main
   board"). Until then a panel-mount USB-C extension's receptacle (`CBL-USB-EXT`)
   stood there, on end, behind an overmould pocket in the tail face; all of
   that is gone (ADR 0015, *Amendment, 2026-10-04*). The jack (`J-MIDI-OUT`, a
   Same Sky SJ5-43502PM, `config/body.yaml` `midi`) goes through the **oak
   bottom**, centred in the lane: a counterbore from inside takes its collar and
   leaves the oak its nut can clamp, and its nut stands under the bottom face. It
   is fitted from inside before the cassette drops in, and its lead (`CBL-MIDI`)
   plugs into J-MIDI on the main board with the lid off. The counterbore is a
   router pass, exported on its own (`export/oak-bottom-pockets.dxf`); the
   through-hole is in `export/oak-bottom.dxf`.
   *Rules: "MIDI jack in the oak bottom", "MIDI jack lead to J-MIDI", "J-MIDI
   and its plug under the Matrix carrier", "oak-bottom cuts at least 3 mm
   apart".*
4. **The display set the mouth end — resolved by the owner.** It is gone
   (ADR 0015), and the mouth end is now the equal band. *Rule: "what the
   mouth end needs".*
5. **Thumb recesses and the oak between them.** *Rule: "oak-bottom cuts at
   least 3 mm apart".* Since the thumb keys went to two rows across the body
   either side of each rest, at the top keys' pitch with one oak slot per row,
   and the spare cutouts went (owner, 2026-09-26), every cut passes. The
   left thumb's tail row is what nears the U-bolt legs (*"U-bolt legs clear
   of the thumb recesses"*). The arc and spares
   before it left 0.5 mm webs; that history is in git.
6. **The regulator block** fits wherever it stands on the main board.
   *Rule: "regulator block fits where it stands".*
7. **The main board is placed by the layout** — its length by the mouth cap
   and the right hand, its width by the sides — and each key board's chain
   header, with the main board's under it, is placed clear of the switches by
   the model (*"chain headers on the … boards clear of the switches"*).
8. **M3 into a 1.20 mm plate** was about two threads, which ruled out
   tapping the key plate for the lid screws. Since ADR 0025 there are no lid
   screws; the columns' threads are in their standoffs.

## The interference check

`mechanical/clash.txt` is every named solid in the model intersected with
every other (`tools/cad.py`, manifold3d), regenerated on every build. Parts
that go INTO each other by design are excused in `mechanical/clash-allow.yaml`,
each with its reason; a rule that stops matching is reported. Every solid is
an envelope — many sizes are tbd in `config/body.yaml` — so a clean pair is
only as good as those envelopes. Group the report's lines by these causes
(read the counts there, not here):

1. **Each key board is on a ribbon** (owner, 2026-09-26, ADR 0017), not a
   blind-mating header — and since 2026-09-27 a **through-hole IDC** one
   (ADR 0017's amendment): a 2×6 1.27 mm shrouded right-angle header on each
   board (`boards.chain_hdr_*`), the key board's **hanging from its underside
   directly over the main board's** — stacked, at the same place along the
   body — both in the far band beside the LED row and **both mouths facing
   the same way along the body**, clear of the switch pins above and below.
   The ribbon comes out of both plugs and **folds back on itself: closed, it
   is a flat hairpin lying along the body**: the `-RN2` cable leaves the main
   board's socket upward and the key board's downward, facing each other,
   and both legs lie between the two plugs' heights, running the same way to
   the fold, so it never stands across the LED row's light
   (`renders/section-ribbon.png`; *"key-chain ribbon closed: hairpin leg and
   fold radius"*, *"key-chain ribbon fold no tighter than its bend radius"*,
   *"key-chain ribbon hairpin inside the body"*, *"key-chain ribbon hairpin
   clear of the columns"*). Which way each hand's hairpin folds is
   `routing.chain_fold`, which says why. **Its length is the service
   position's** (owner: long enough "to have the top off and still connect
   the ribbon before tightening down"; since the cassette, ADR 0025,
   tightening down is screwing the key plate onto its columns): the key
   plate, with both key boards, held raised straight up off its columns while
   a hand plugs the main board's sockets (`routing.chain_service`,
   `routing.chain_raise`, `routing.chain_slack`; *"key-chain ribbon length
   (derived)"*). A ribbon long enough to lay the plate beside the body would
   fold into a hairpin that reaches the left-hand board's tail column. The
   cable is ordered by *"key-chain cable to order (FFSD length code)"*, which
   is the FFSD part number's length field, in inches. The key header's pin
   tails stop short of the plate (above).
2. **The hardware pages follow**: `hardware/interfaces/key-chain-loom/`
   describes the two ribbons (`J-CHAIN`, `CBL-CHAIN`) and the thumb chain in
   traces, and `chain-connectors` is derived from them. The key-board header
   is the main board's part mounted upside down, facing the same way, and the
   cable is ordered with its second socket's notch reversed (`-RN2`), which
   is what sends the two ends' cables toward each other; that makes the key
   board's pin numbers differ from the main board's — `key-chain-loom.md`
   says how.
3. **The breath tube** is short: the inlet's inner barb in the mouth cap (#36, *The breath inlet* in the README), then one clear tube, no trap (ADR 0003, 2026-10-05): along the inlet's axis, an S toward the near side and one U back onto the sensor's port, at `routing.tube_bend_r` and no tighter (*"breath tube bends no tighter than routing.tube_bend_r"*), across the LED row (*"breath tube crosses the LED row clear of it"*), all in the mouth band; the board has a
   slot in front of the sensor's lower port.
4. **The U-bolt has the middle station to itself** (ADR 0025: the lid
   screws that shared it, and the backplate, are gone). Its legs pass the oak
   bottom and the bottom plate, which spreads its pull over the oak (*"U-bolt
   spacers bear on the bottom plate"*). **The U-bolt is M3 until the strap
   hardware is chosen.** The LED strip that held it to M3 is gone (ADR 0028):
   no LED stands between the legs, so a bigger nut reaches nothing on the
   centreline, and what bounds its size is the neck of board between the legs
   and the thumb recesses (`hardware.ubolt_rod_d`). The board is in the U-bolt's clamp: a spacer fills the
   bottom plate to its underside (*"main board in the U-bolt's clamp"*), and
   *"main board neck at the U-bolt station"* gives the board every trace
   between the two halves must cross. (The stations ran through
   the side strips until ADR 0016 removed them.)
5. **The Matrix and the umbilical are wired onto the main board's tail
   end** (owner, 2026-09-26). The Matrix sits on a carrier board of its own
   (owner, 2026-10-03, ADR 0021 amendment 2026-10-03), hung from the oak top
   on three mounts (*"Matrix carrier hangs from the oak"*): two 1×10 headers
   through its pad rows (`HDR-MATRIX`), a notch round its USB-C (and room for a recovery plug, lid off).
   A plain 24-way IDC ribbon (allocation on `CBL-MCU-RIBBON`, ADR 0018) runs
   from `J-MCU-C`, hung under the carrier straight above J-MCU, down into
   J-MCU at the main board's near edge. It plugs there with the lid raised,
   as the key chain's do (*"Matrix ribbon length"*), and closed it folds flat
   between the two headers (*"Matrix ribbon closed: its folds between the
   sockets"*). **The umbilical has no cable inside the body** (ADR
   0021): the etherCON is soldered to its adapter, and J-UMB, a right-angle
   header, is soldered into the adapter and the tongue (*"J-UMB on the main
   board's tongue…"*, *"J-UMB's row lands on the adapter clear of the
   etherCON's footprint"*). The LED row stops short of J-MCU. The rows are
   `J-MCU` and `CBL-MCU-RIBBON` (`hardware/carrier/`), `J-UMBILICAL-INST`,
   `J-UMB` and `PCB-UMB-ADAPTER` (`hardware/interfaces/spi-link/`).
6. **The tail is clear.** The etherCON and its adapter, J-UMB, the MIDI jack,
   its lead and J-MIDI, and the Matrix meet nothing, and the connector fits the cavity without cutting the oak.

Found by the check and fixed as model bugs, not findings: the oak bottom's
missing counterbores, thumb boards drawn with switch holes, the display cut
too tight for the STEP's glass overhang, the etherCON housing drawn through
the tail cap, and several of the check's own first routings.

**Also found, outside the model:** the MPXV4006DP (case 1351-01) is a
**surface-mount** part (its datasheet's p.1 ordering table). It is now
soldered to the main board, with no socket; how it is fitted and swapped is in
`hardware/interfaces/breath-sense-link/breath-sense-link.md`, "Mounting".

**Found by the first PCB layout (2026-09-27, `docs/reference/tooling.md` §4):**
the key boards' ribbon connector was deeper than the envelope assumed, and
on a 1.6 mm board the KS-33's pins would show only about 0.1 mm below it.
Both were settled in ADR 0020: the key boards are `boards.key_board_t` thick,
and the connector's envelope now comes from the IDC header's banked full print
(`boards.chain_hdr_*`, ADR 0017's 2026-09-27 amendment). The model
now exports each key board's outline (`export/key-board-*.dxf`) and its
switch and connector positions (`export/pcb-geometry.echo`), which the PCB is
placed from. The main board's the same way: `export/main-board.dxf` is its
outline, with its full-width tail end, holes and the sensor's slot, and its
`main` entries in `export/pcb-geometry.echo` place the thumb switches (from
below), both chain headers, J-MCU, J-UMB, the sensor, the regulator block,
each LED of the row and the mounts, with how tall parts may stand under each key board
and where nothing may.

## Not modelled yet

The thumb rest lip, the silicone beads (ADR 0025), plate stiffening (ADR 0002 — open, and it changes the key plate),
and the diffuser standoff. The key boards are rectangles by decision (ADR
0020 point 3): their outlines are generated now (`export/key-board-*.dxf`),
and only their size moves, with the switch positions, which are provisional
until M3.
