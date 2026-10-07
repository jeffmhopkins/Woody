# 0021 — The instrument's etherCON is PCB-mounted, on an adapter joined to the main board

**Status:** Accepted. Decided by the owner, 2026-09-29. It settles ADR 0004's
open question *which etherCON variant at each end* **for the instrument's end
only**; the module's end is [ADR 0023](0023-module-ethercon-and-two-boards.md). **Amended twice on 2026-10-02**: the main board's tail end runs full width (*Amendment* below), and the Matrix moves onto the right-hand key board, with no ESD protection added to the USB (*Amendment, 2026-10-02 (2)*). **Amended again on 2026-10-03**: the Matrix moves onto a carrier board of its own, hung from the oak top, the right-hand key board goes back to its original length, and the Matrix is programmed over its own USB-C only (*Amendment, 2026-10-03*). **Amended on 2026-10-07**: the etherCON is centred on the tail face, the MIDI jack moves from the oak bottom to a corner of the tail face beside it, and `J-MIDI` becomes a side-entry header facing the tail (*Amendment, 2026-10-07*).

## Context

The instrument's etherCON was a feedthrough (Neutrik NE8FDP, `J-UMBILICAL`)
with an RJ45 socket at its back. A short patch lead (`CBL-UMB-PATCH`) ran from
that socket to a latching header (`J-UMB`) on the main board. That added two
contact interfaces to every conductor of the umbilical, including the +12 V
path and the breath pair. ADR 0004 recorded that as the cost of the
feedthrough and deferred the choice. The patch plug and its boot were also
the longest item behind the last key, so they set the body's length
(`mechanical/drc.echo`, *what the tail end needs*).

Owner, 2026-09-29: *"it's about time that we convert the ethercon connector
to a PCB type, if we need to make a little adapter board to hook the flex
connector to that's fine, otherwise, it might just be easier to extend the
main board down and mount it directly to that."*

## Decision

1. **The instrument's etherCON is a Neutrik NE8FAV** (`J-UMBILICAL-INST`):
   an A-series receptacle for a vertical PCB, mounted from behind the panel.
   Its drawing, data sheet and 3D model are banked
   (`datasheets/connectors/NEUTRIK-NE8FAV-*`). Every number the body CAD uses
   is in `config/body.yaml` `ethercon:`, each with its source.

2. **It is soldered to a small board of its own, the umbilical adapter**
   (`PCB-UMB-ADAPTER`). The adapter stands parallel to the tail cap, the
   flange's outline in size. Its tracks run each etherCON pin to the
   same-numbered pin of `J-UMB`, and it carries nothing else.

3. **`J-UMB` is now a 1 × 8, 2.54 mm right-angle pin header, soldered into
   both boards.** Its insulator lies on a **tongue of the main board**, its
   tails go down through the tongue and its posts through the adapter. The
   tongue runs from the main board's tail end to the adapter's rear face.
   Pin N is still etherCON pin N, so
   every "`J-UMB` pin N" on the carrier's pages still means the same
   conductor. There is no cable and no mated contact between the etherCON
   and the main board. `CBL-UMB-PATCH` is gone.

4. **Latch up.** ADR 0009 turned the NE8FDP 90° so that its 26 × 31 flange
   fitted the body's height. The NE8FAV's flange is square, so that reason
   no longer applies. The PUSH tab is on top, where a thumb finds it. The
   contact rows sit above the axis, which leaves the band below the axis
   for `J-UMB`'s row (`ethercon.rotated`).

5. **The tail cap has a recess from outside for it.** The NE8FAV allows a
   3 mm panel at most (`ethercon.panel_max`) and the oak cap is thicker, so
   a router pocket leaves exactly that much oak where the flange clamps. The
   recess takes the flange's outline, the PUSH tab and a margin
   (`ethercon.recess_margin`, decided with the cable connector in hand).
   Two of Neutrik's A-series screws go through its floor into the flange
   (`MECH-ETHERCON-SCREW`).

6. **Its two locating pegs are cut off flush.** They stand below the flange
   (`ethercon.peg_below`) and, with the connector on the floor latch up,
   point into the oak bottom. Drilling the floor for them would locate the
   connector a second time, against the cap's screws, across oak that moves;
   standing it higher would take more body than `body-thickness` has.

## Why not mount it on the main board directly

That was the owner's first suggestion, and the NE8FAH (the same connector
for a horizontal PCB) would do it. Both the NE8FAH and the NE8FAV put the
axis 12.5 mm above the flange's lower edge
[ds `NEUTRIK-NE8FAH-DRAWING.pdf`, `NEUTRIK-NE8FAV-DRAWING.pdf`]. On a
horizontal board that is also the height above the board's top face, and
the main board's top face is fixed by the thumb switches soldered into it
(`switch.thumb_pcb_below_seat`). The connector's body, a flange's height
above that face, would then stand 3 mm above the oak top's underside. Its
PUSH tab, which rises above the flange's outline, would stand about 7 mm
above it, through the cap's top edge [calc from `mechanical/drc.echo`'s
tail Z levels and the NE8FAH model]. The main board cannot drop at the tail
because it is one flat board, so the body would have to grow by at least
the first figure and the cap would lose its top edge to the second. The vertical-PCB part
on an adapter stands on the floor as the NE8FDP did.

A flex cable between the adapter and the main board was the other way to
join them. A right-angle header does the same job with no connector and no
cable. Its pins carry more current than the etherCON's own contacts do, and
ADR 0004 counted every contact interface as a cost.

## Consequences

- **Two contact interfaces fewer in every umbilical conductor**, and one
  cable fewer to make by hand.
- **The tail is shorter.** Removing the patch plug took away the claim that
  set the tail's length. The Matrix, centred after the keys, now sets it,
  and the body shortens by what `mechanical/drc.echo` *overall length*
  reports. The gap between the hands follows the keys-to-Matrix gap (owner,
  2026-09-26) and is now at its minimum, `layout.gap`. So the right-hand
  cluster moved toward the mouth. The left-hand ribbon's hairpin moved
  because it clears the lid screw between the hands. Both key boards were
  re-laid out from the body CAD. *(Since ADR 0025 there are no lid screws;
  the hairpins clear the cassette's columns.)*
- **The body could be thinner.** `mechanical/drc.echo` *body thickness takes
  the etherCON on the floor* reports the spare. `body-thickness` is the
  owner's figure and was not changed here.
- **The main board is longer, by the tongue.** The tongue is as wide as the
  adapter and notched where the last lid screws pass. It has standoffs
  under J-UMB's end. *(Since ADR 0025: no notches; the tongue's pair of mounts
  stands on the bottom plate, which stops short of J-UMB.)* *(2026-09-30,
  the owner, on a marked-up render: "I'm ok with it being more narrow, but
  ... my red line is inset just slightly which is not needed." On the side
  where the adapter's edge falls just inside the main board's, the tongue
  now runs straight on from the main board's edge with no step; the other
  side keeps its step to the adapter's width. `mechanical/drc.echo`
  *"main board's tongue flush with its edge on the near side of the
  adapter"* says which side and by how much.)* *(2026-10-02: no step on
  either side now. The board runs full width to the adapter. See the
  amendment below and `mechanical/drc.echo` *"main board's tail end runs
  full width beside the etherCON adapter"*.)*
- **Taking the main board out means unscrewing the etherCON from outside
  first.** The connector, the adapter and the board come out as one piece.
  The nose sits in the cap's bore, so the assembly slides back before it
  lifts.
- **The cable connector is unconfirmed.** The NE8FAV names "NE8MC* or any
  standard RJ45 plug" and excludes the NE8MC6-MO and NKE6S* cables. It does
  not name the NE8MX, the NE8MC's successor (`J-UMBILICAL-CABLE`).

**`J-UMB`'s part** was chosen the same day: hanxia HX PZ2.54-1x8P WZ
(`hardware/interfaces/spi-link/bom.csv`). Its drawing
(`datasheets/connectors/HANXIA-HX-PZ2.54-1x8P-WZ.pdf`) settles the insulator
and row height in `boards.umb_joint_*`. The 6.00 mm posts pass the adapter
with enough standing in front to trim, and the 3.00 mm tails pass the 1.2 mm
tongue.

## Open, and what decides each

| Item | Decided by |
|---|---|
| The recess margin round the flange and the PUSH tab | M4, with the cable connector in hand |
| The mounting screws' part and length for a 3 mm panel | M4, with the connector |
| Whether the NE8MX latches in the NE8FAV | Before buying the cable connectors |
| The module's end | E12/M7 (ADR 0004) |

## Amendment, 2026-10-02 — the main board's tail end runs full width

**Owner, 2026-10-02**, on the main board's tail: *"can you explain why we
have this cut out on the bottom main board? I feel like it's not necessary,
and that maybe we can get another LED down there"*, and *"I think maybe
because we changed how the ethercon connector is mounted that we have a
longer standing decision on the main board that is no longer valid. I feel
like the USB is high enough in the bottom of the controller that we can run
a cable without having to muck around with the PCB."*

**Why the cut-away was there.** Decision 3 made the tongue *as wide as the
adapter*, and the Consequences above say why it stayed narrow: it was
*notched where the last lid screws pass*. ADR 0025 removed the lid screws and
the notches; the narrow tongue outlived its reason. The 2026-09-30 note only
trimmed its near side. Nothing else ever claimed the corner.

**What stands in the corner, from the body CAD** (`[repo]` the model's
solids intersected with the corner past the right-hand key board and beside
the adapter's width, full cavity height; numbers as `mechanical/drc.echo`
and `mechanical/export/pcb-geometry.echo` print them):

| Solid | Where, over the corner | At the board's height? |
|---|---|---|
| USB-C extension receptacle (`CBL-USB-EXT`) | its back face reaches 0.1 mm over the board's end; the rest stands behind the adapter's rear face, beside the flange | no: its underside was 2.55 mm above the board's top face, inside the board's 2.62 mm parts height, so it now rises (below) |
| USB-C extension lead | from the Matrix's mouth edge down to the receptacle's back, over the corner | no: its underside stays more than 5 mm above the parts |
| Matrix ribbon, level run into `J-MCU` | its edge overhangs the old tongue's edge by about 2 mm | already over the board, with its own parts keep-out |
| Bottom plate | under the board, as everywhere | under it |
| Key plate, Matrix, its harness and parts | 19 mm and more above the board | no |

The etherCON, its adapter and `J-UMB` stand at and past the board's end
across the adapter's width only. So the corner held nothing at the board's
height, and the owner is right that the USB-C cable needs no cut in the board.

**Decision.** `boards.main_tail` = `full` (`config/body.yaml`): the main
board runs its whole width from the right-hand key board's end to the
adapter's rear face, so its outline is a plain rectangle. The corner it gains
is the 48.6 × 15.5 mm that *"main board's tail end runs full width beside the
etherCON adapter"* prints; `tongue` keeps the old outline if it is ever
wanted back. The tongue's two end mounts, `J-UMB`, the bottom plate's end
and the parts band at `J-UMB` do not move.

**The USB-C receptacle stands higher.** The receptacle's body reaches back to
the board's end, so it now stands `boards.board_clear` above the parts the
corner may carry (`boards.smt_h`), the clearance a key board keeps from the
parts under it, instead of centred in the cavity. It rises 1.57 mm `[calc:
10.1 + 2.62 + 1.5 + 12.5 / 2 = 20.47, against the centred 18.9]`, and the
tail-face slot and overmould pocket follow it; every USB-C rule still passes.
A receptacle bought deeper than `openings.usb_ext_depth` would now stand over
the board, which is why the clearance is vertical and not a gap along the body.
`pcb-geometry.echo` carries a *USB-C receptacle and lead* keep-out over the
corner: parts to `boards.smt_h`, nothing through-hole and tall.

**What the layout has to do** (the `.kicad_pcb` is the source; this
amendment does not touch it): take the new `main-board.dxf` outline and
the new keep-out; extend the pours and planes (`INST_POS12` on layer 3,
`PWR_GND`) into the corner; re-check the edge clearance along the old
tongue's far edge, where parts placed against it (`Q-INRUSH`'s gate network,
`R43`/`D20` at y 30.8) now have board beyond them. No placed part has to
move, and no net changes.

### Open — for the owner, with numbers

**A fourteenth LED.** The corner is off the centreline. On the centreline
past `J-MCU` an LED stands under the Matrix ribbon's level run and sees
11–15 % of the side faces past the key board (below), so it is not worth
having. In the corner it works. Sightlines from the emitter (board top +
`lighting.led_h`) to each acrylic side's inside face, through the CAD's
solids (`[calc]`, ray cast; a wall point counts if nothing stands between;
85 % is all of it above the board):

| LED | far side, x 250–270 / 270–290 / 290–320 | near side, same bands |
|---|---|---|
| `LED1` today (centreline, x 224.7) | 18 / 35 / 13 % | 0 / 2 / 4 % |
| **at x 274.7 (LED1 + 3 × the pitch then set in config), 13.5 mm off the centreline toward the near side** (superseded 2026-10-03: ADR 0028's amendment of that date puts the fourteenth in the row) | 17 / 59 / 36 % | 85 / 85 / 85 % |
| at x 258.0 (LED1 + 2 pitches), same offset | 48 / 29 / 7 % | 85 / 85 / 85 % |

The tail's near side is almost unlit today. The regulator block, 12.5 mm
tall on that side in front of `J-MCU`, shadows `LED1`. One LED in the corner
lights it. The far side gains most past the Matrix ribbon's drop. The near
side is 9 mm away against the row's ~22.5 mm, about six times the
irradiance `[calc: (22.5 / 9)²]`, so firmware would scale that LED down to
match. The diffusion test (ADR 0028) is the judge. What it changes:
`lighting.led_count` 13 → 14, plus the row's placement (it is off the
centreline, so the body CAD needs a second row record), and
`led-row-current` scaled by 14/13 `[calc: 14 × 0.18 W / 12 V = 210 mA upper,
14 × 13.1 mA = 183 mA lower, 28 mA blanked]`. The +15 mA is under 1 % of
U-ISO's rating. The register's `umbilical-current` upper bound would move
by the same 15 mA. `led-pwm-rail-ripple` and `led-pwm-pitch` scale with the
row's swing and should be re-simulated, not scaled. The new LED has to be
first in the data chain, because the data arrives at the tail:
`R-LED-SER` → the corner LED → `LED1` (superseded 2026-10-03, ADR 0028: the row's tail end is first). That adds about 50 mm of feed and
55 mm of return across the `J-MCU` area. The backup line follows ADR 0028
point 5: the corner LED's `DIN2` to GND, and `LED1`'s `DIN2` from the
feed. The refdes are renumbered in chain order. Firmware: one more pixel
(~30 µs more per frame at 800 kbit/s) and a per-LED gain for it. **Added
2026-10-02** by the owner ("Add it"; ADR 0028's amendment of that date). **Removed 2026-10-03**: put in the row that morning, then the row's tail-end LED taken out with the rest left where they stood, thirteen again (ADR 0028's two amendments of that date).

**`HDR-SERVICE` where it is, or elsewhere.** ADR 0018 point 4 puts it on the
main board, reached with the lid off. Since ADR 0025 that means cutting the
oak top free, with the key boards still over the main board. So it must sit
outside both key boards' outlines and near `J-MCU`, whose pins 21–24 it
takes. `EN` has no capacitor on the Matrix, so the shortest trace is worth
keeping. Its place on the tongue is the first layout's (`layout.yaml`
`J2`), recorded as `boards.service_hdr_at` (nominal). It is a vertical 1 × 5.
Nothing stands over it, so a right-angle or lower part gains nothing in
height. It can move into the new corner if the owner wants the tongue's far
side clear, as long as it stayed out of the corner LED's light (gone since 2026-10-03). Its tails then
stand past the bottom plate's end, over oak, and its plate window goes.

**A board-mount USB-C at the tail face** (owner's follow-up, 2026-10-02).
Candidate part: HRO `TYPE-C-31-M-12` (LCSC C165948, banked
`datasheets/connectors/HRO-TYPE-C-31-M-12.pdf`). It is 8.94 wide, 7.35
long and 3.26 tall over the board, and its shell stands only 0.40 past the
board's edge. On a finger of the main board beside the adapter, run on to
the tail cap's inside face, it fits across the lane and in height. Its
face would then be the cap's thickness behind the tail face, so the
plug's overmould needs a through-opening the overmould's size. Lying flat,
that is `openings.usb_overmold`'s wide side across the lane. From the
etherCON recess's 2 mm web to the cavity's side that leaves 14 mm against
the 15 the allowance asks, so it fails by 1 mm. The Matrix's `D+`/`D−`
(`IO19`/`IO20`) are on none of its pads or test points
`[ds WAVESHARE-ESP32-S3-MATRIX-SCHEMATIC.pdf]`. They reach the board only
by soldering to its USB-C's 0.5 mm-pitch contacts or by a short plug pigtail
into it, which is a cable again. All 24 ribbon conductors are allocated.
`IO2`/`IO3` are the spares that shield `IO7`, and they are not adjacent. The
board would carry CC1/CC2 5.1 kΩ to ground, an ESD array, and `VBUS` through
a Schottky onto the 5 V OR node beside `D-USBOR`. **Not adopted.** Decided
by the owner. A Matrix carrier board under the Matrix (headers on its pad
rows, an IDC header to `J-MCU`) fits the height under the Matrix. It leaves
the same `D+`/`D−` problem.

**The Matrix on an extension of the right-hand key board** (owner's
follow-up, 2026-10-02: *"would that be better to attach as a extension of
the right hand PCB?"*). Heights from the body CAD:

- The key board's top face is 30.5 (the plate's top, less
  `switch.pcb_below_seat`).
- The Matrix's underside is 31.4 (its top against the oak, less
  `boards.matrix_t`).
- So an extension would stand 0.9 mm below the Matrix's underside.
- The Matrix's back-side parts (`boards.matrix_under_h`: its USB-C, the
  ESP32-S3, the buttons) hang below that, through the board's plane at
  28.9–30.5. The figure was `[from memory]` then; it is read off the vendor
  STEP since 2026-10-03, and the deepest is the USB-C.

The extension therefore cannot lie flat under the Matrix. It would be two
rails under the pad rows, at 28.5 ± 11.43 across, with the middle open for
those parts. The opening also takes the extension cable's right-angle plug,
which stands at 24.4–31.4 in front of the Matrix's mouth edge. The 0.9 mm
gap needs bare header pins through both boards on a 0.9 mm shim. Without
the shim, the Matrix sits on the rails and drops 0.9 mm from the oak, and
its LED tops go from 2 to 2.9 mm under the acrylic. The key plate ends 1 mm
short of the Matrix (`plate_x1`), above the board's plane, so it is not in
the way. The extension adds about 46 mm to the board's 107 mm length, and
it cantilevers 37 mm past the board's tail columns to the Matrix's centre.
`CBL-MCU-RIBBON` would become a plain IDC ribbon from a header under the
extension straight down to `J-MCU`, with the same pin map. `EN`, `IO0` and
the extra 5 V and GND still need short wires from the Matrix's button pads
and test pads to the rails. The `D+`/`D−` problem is unchanged. **Adopted
by the owner the same day** (*Amendment, 2026-10-02 (2)*, below), which
corrects two things this paragraph got wrong: the key board's header numbers
the ribbon from the other edge, and the USB-C plug's lead must turn down.

**Found doing this:** the Matrix has **no ESD protection on its USB-C**.
`J1`'s D± run straight to the ESP32-S3
`[ds WAVESHARE-ESP32-S3-MATRIX-SCHEMATIC.pdf, USB block]`, so the tail-face
receptacle exposes the MCU's USB pins with nothing in between. `U-ESD-USB`'s
note (*"Dev boards carry these"*) is wrong for this board. That is a finding
for the owner and the BOM fragment's owner, not fixed here. **Decided in the
next amendment: no ESD protection is added.**

## Amendment, 2026-10-02 (2) — the Matrix on the right-hand key board; no USB ESD

> **Superseded on 2026-10-03** by the next amendment, except item 7 (no USB ESD)
> and item 6's plug, drawn where it really is: the Matrix is on its own carrier,
> the right-hand key board is back at its original length, and the rails, the
> shim, the four wires and `J-MCU-KB` are gone. Kept here as the record of what
> was decided that day.

**Decided by the owner, 2026-10-02**, on the options above:

> "I think d is right for the matrix vs hand soldering"
> "I don't think we need the esd protection added to the USB though"

### What is decided

1. **The Matrix (`U-MCU-RT`) mounts on the right-hand key board**
   (`config/body.yaml` `boards.matrix_mount`). Past its tail columns the board
   runs on as **two rails**, one under each of the Matrix's pad rows, out to
   the Matrix's tail edge. Each rail runs from the board's side to
   `boards.matrix_rail_in` past its pad row. The middle stays open for the
   Matrix's back-side parts and the USB-C plug. The Matrix stays where it was,
   centred under its window. The rails are in `mechanical/export/key-board-rh.dxf`
   and `pcb-geometry.echo` (`right_hand` `rail`).
2. **Bare header pins join each pad row to its rail through a shim**
   (`HDR-MATRIX` ×2, `MECH-MATRIX-SHIM` ×2). The shim is `boards.matrix_shim_t`,
   a little under the gap. So the Matrix's top stands just under the oak, not
   against it. That clearance takes the pins cut flush on the Matrix's top
   face, because its pad rows sit under the oak, outside the window's opening,
   and it takes the boards' thickness tolerance. drc.echo *"Matrix shim on the
   extension's rails"* holds the shim to the gap.
3. **Four short wires remain** (`W-MATRIX`): `TP2` and `TP3`, which share
   the 5 V and ground current with the pad row, and `EN` and `IO0` at the two
   buttons' pull-up terminals. None of these is on a pad row. They land on
   four wire pads on the near rail.
4. **The 24-wire ribbon soldered to the Matrix is gone.** `CBL-MCU-RIBBON` is
   now a plain 24-way IDC ribbon, crimped at both ends. It runs from
   `J-MCU-KB`, the same header as `J-MCU`, hung upside down from the key
   board's underside straight above it, down to `J-MCU`. Its allocation is
   unchanged (ADR 0018). **The paragraph above said "with the same pin map",
   and that is wrong for the key board's end.** A header hung upside down
   numbers the ribbon from the other edge, so `J-MCU-KB` pin *k* carries
   `J-MCU` pin 25 − *k*. The key-board socket is crimped turned over, as the
   key chain's `-RN2` cable reverses its key-board end (`key-chain-loom.md`).
   The key board's sheet draws it that way, and `tools/kicad.py check`
   (`check_matrix`) holds every pin of `J-MCU-KB`, `HDR-MATRIX` and
   `W-MATRIX` to the carrier's netlist. The ribbon's length is drc.echo
   *"Matrix ribbon length"*. It plugs at `J-MCU` with the key plate held
   raised, as the key chain's ribbons do: its slack is `routing.chain_raise`
   and `routing.chain_slack`, the same figures. Closed, that slack folds flat
   in four legs over `J-MCU` (*"Matrix ribbon closed: its folds between the
   sockets"*, the rule's name since 2026-10-03). This answers review #19 F4:
   the slack is a figure, it lies in a checked place, and `J-MCU` is reached
   with the key plate raised, so the plate is not over it then.
5. **The Matrix's grounds join the key board's `GND_CHAIN` pour.** That is
   the main board's ground under another name (`hardware/nets.yaml`). The
   Matrix's return therefore has both ribbons' grounds in parallel, and a pour
   on the key board instead of a track. A track along the rail would have
   added several times the four conductors' resistance to the path that the
   breath ADC's reference is regulated against (`carrier.md`). Its 5 V and
   3V3 are power tracks (`layout.yaml` `power_nets`).
6. **The USB-C plug's lead leaves downward** (`openings.usb_plug_turn`). The
   paragraph above put the right-angle plug in the open middle and stopped
   there. A lead leaving across the body at the plug's height runs into the
   far rail. Turned down, the lead leaves below the rails and passes under
   the far rail to the receptacle (drc.echo *"USB-C plug and lead clear of
   the right-hand key board's rails"*). The body's length does not move.
   **And the plug is drawn where it really is** (owner's review #19, F1).
   The Matrix's USB-C receptacle sits on its underside at the mouth edge, its
   axis `boards.matrix_usb` below the board, read off the vendor STEP. A
   plug's overmould is centred on that axis, so it rises past the key
   plate's underside and past the oak's. That was true on the lid too: the
   old drawing hung the plug below the board and so did not show it. Now
   the key plate stops a millimetre in front of the plug, which also opens
   `J-MCU`'s side to a hand. The oak top has a pocket over the plug, cut
   with the column-screw pockets to their depth (`oak-pockets.dxf`) and
   ending at the window's rebate. The receptacle is now among the Matrix's
   drawn parts, so the clash check sees it. The rule is drc.echo *"USB-C plug
   clear of the key plate and the oak top"*. The real plug, once
   `CBL-USB-EXT` is chosen, decides `openings.usb_overmold` and with it the
   pocket's depth.
7. **No ESD protection is added to the USB.** The Matrix's `D+`/`D−` reach
   the ESP32-S3 with nothing between, and the tail-face receptacle exposes
   them (*Found doing this*, above). The owner has heard that and accepts it.
   `U-ESD-USB` stays out (`hardware/unplaced.csv`), and its note now says why.
   Adding one later needs a board between the Matrix's USB-C and the
   receptacle, which none of these options has.

### The cantilever: no support, and what would change that

The rails reach past the board's tail columns to the Matrix's centre
(drc.echo *"Matrix on the right-hand key board's rails"*). Nothing holds the
tip from below. `config/body.yaml` `boards.matrix_support` is `none`, and
its source carries the arithmetic. The static sag is negligible, and the
stress under a hard jolt is a small part of FR-4's strength. Upward, the oak
top stops the Matrix within the shim's clearance. The first mode is a few
hundred hertz, far above the shakes and jabs the Matrix's IMU is there to
read (ADR 0007).

**The risk is ringing, not strength.** On the lid the Matrix was as stiff as
the body. On a cantilever, a key click can ring it, and the IMU is on the
Matrix. **What decides it:** an E-test on the first assembled instrument.
Tap the body and the keys with the IMU logging. If a mode falls inside the
gesture band, or rings through the firmware's filter, the setting becomes
`standoff`: a pair of M2.5 standoffs from the main board to the rails' tips.
The main board runs full width under them (`boards.main_tail`), so there is
room. The body CAD does not draw that case yet, and asserts so.

### Other risks, each with what decides it

- **The pad rows' side.** The body CAD puts the 5V..IO1 row on the near side
  with the USB-C edge toward the mouth. It takes that from the vendor's
  top-view pinout, `[ds WAVESHARE-ESP32-S3-MATRIX-pinout.png]`. A mirror
  would put 5 V on IO pins. **Check it against the Matrix in hand before the
  key board is ordered.**
- **The open middle's width** depends on the Matrix's back-side parts,
  `boards.matrix_under_h`, which was `[from memory]` that day. The rails' inside
  edges clear them by the margin the DRC above prints. Calipers on the board
  decide `boards.matrix_rail_in`.
- **The shim.** A stack thicker than the gap bends the rails up against the
  oak. That is harmless, but it preloads the joints. The first Matrix
  assembled on its board decides `boards.matrix_shim_t`.
- **Assembly order.** The Matrix is soldered to the key board before the key
  plate goes on, and a dead Matrix is a desolder of twenty pins and four wires
  on the bench. The main board is not touched (`CBL-MCU-RIBBON`).

### What this does not change

`J-MCU`, its place and its pin map; the main board's outline; the Matrix's
place under its window; ADR 0018's allocation. **What it leaves for others:**
the main board's layout gains the keep-outs under the rails and the
ribbon's fold (`pcb-geometry.echo`), with its re-layout.

## Amendment, 2026-10-03 — the Matrix on a carrier of its own; program over USB only

**Decided by the owner, 2026-10-03**, in four steps:

> "This cut[-out] feels wrong too, the matrix led board shouldn't have to have a cutout?"
> — then, of the study below: "2nd board then" (keep the rails)
> — then, of three ways to join J-MCU to its mate: option 1, "ALONG"
> — then: "So now the rh top board should not be extended, but back to original length I think"
> — and, asked how the Matrix then mounts: a "SEPARATE SMALL MATRIX CARRIER" (option c),
> "Hang from the lid", and "Program over USB only".

### Considered and rejected: a solid extension under the Matrix

The owner asked whether the right-hand key board could run on **solid**
under the Matrix, with the Matrix standing deeper. The study (2026-10-03,
off the vendor STEP and the body CAD):

- The Matrix's deepest back-side part is its USB-C receptacle
  (`boards.matrix_under_h`). A solid board under it puts the Matrix on pins
  that high above the board, which lifts its LEDs **above** the acrylic's
  underside at the key boards' fixed height: the Matrix stands higher, not
  deeper. A thinner acrylic would take it, with the LEDs much nearer the
  frost and the oak's lip round the window under drc.echo's minimum.
- **The plug decides it.** Any USB-C plug's overmould is centred on the
  receptacle's axis, so in front of the Matrix it crosses the key board's
  plane whatever the Matrix's height. A board there needs an opening for it,
  so "no cutout" cannot hold with the Matrix's USB-C at its mouth edge.
- The one way to no enclosed opening: the Matrix turned so its USB faces
  the tail, the board ending at the Matrix's tail edge with an edge notch,
  and the body about 8–10 mm longer. Not taken.

The owner kept the rails ("2nd board then"), then dropped the extension
altogether (below).

### What is decided

1. **The Matrix mounts on its own carrier board**,
   `hardware/boards/matrix-carrier/` (`PCB-MATRIX-CARRIER`,
   `config/body.yaml` `boards.matrix_mount` `"carrier"`). The **right-hand
   key board goes back to its original length**: its rectangle, as the
   left-hand one, with C9 (#6-5) and the KS-33's 3.0 mm holes kept. The
   rails, the shim (`MECH-MATRIX-SHIM`), the four wires (`W-MATRIX`) and
   `J-MCU-KB` are gone. Item 7 of the amendment above (no USB ESD) stands.
2. **The Matrix stays where it was, centred under its window.** Two 1×10
   headers (`HDR-MATRIX`, Hong Cheng HC-PZ254-11.5L-1x10PZ) stand on the
   carrier through its pad rows, and the Matrix sits on their plastic
   (`boards.matrix_hdr_h`). That clears its back-side parts over the carrier
   (`boards.matrix_under_rest_h`, the buttons) - drc.echo *"Matrix's
   back-side parts clear the carrier"*. The carrier is solid under the
   Matrix but for **a slot** in its mouth edge under the USB-C receptacle's
   shell, so review #19 F1 holds as it stood (*The carrier's outline*,
   below).
3. **The carrier hangs from the oak top** ("Hang from the lid"): at each
   mount an insert set in the oak's underside (`MECH-MX-INSERT`, CNC Kitchen
   M2.5 × 4.0), a spacer (`MECH-MX-SPACER`, Ettinger 5.52.043), the carrier,
   a washer and the column's screw (`MECH-MX-*`, `hardware.mx_*`). It lifts
   off with the lid, as the key boards do, and unplugs at `J-MCU`. **Three
   mounts, not four** (`boards.matrix_mount_corners`): every line from
   `J-MCU-C` to the near header row runs along the carrier's near strip,
   and a mount at its mouth-end corner left room for too few of them. The
   stack sets the Matrix's height; its top rises into a shallow relief in
   the oak (`openings.matrix_relief_d`, `oak-relief.dxf`), which leaves its
   LEDs where drc.echo *"LED tops under the frosted window"* says and the
   window's lip as *"oak lip under the frosted window"* says. The inserts
   leave `hardware.col_pocket_skin` of oak over them, and the screw's thread
   lands in the insert's length: drc.echo *"Matrix carrier hangs from the
   oak"*, *"Matrix carrier's mounts clear"*. Nothing is added on the main
   board, so the LED row's band and cone are untouched.
4. **`J-MCU-C` hangs under the carrier's arm, straight above `J-MCU`**, its
   mouth the same way, and pin *k* carries `J-MCU` pin 25 − *k*, as
   `J-MCU-KB` did; `tools/kicad.py check` (`check_matrix`) now holds the
   carrier's sheet to the carrier circuit's netlist. Closed, the ribbon's
   service slack folds flat in four legs between the two headers, short of
   the LED row's band (*"Matrix ribbon closed: its folds between the
   sockets"*); its thickness is now the banked cable's
   (`routing.mcu_ribbon_t`). `J-MCU`'s place is `boards.mcu_conn_at`, the
   main board's (option 1, along the near edge, off the LED row).
5. **Program over USB only.** The Matrix is programmed and recovered over
   its own USB-C - USB-Serial-JTAG through the tail receptacle (*since issue #37, with the lid off: the tail receptacle is gone, ADR 0015 amendment 2026-10-04*) - and, when
   that fails, with its own BOOT and RESET buttons, the lid off. **`EN` and
   `IO0` are no longer wired out**: `J-MCU` pins 23 and 24 are on no net,
   `HDR-SERVICE` is a 1×3 (TXD, RXD, GND; `service_hdr_pins`), and the
   Matrix's stand-in on the carrier circuit's sheet has its pad rows only.
   `TP2` and `TP3` are not used either: the pad row's 5 V and GND pins carry
   its supply (`CBL-MCU-RIBBON`'s rating, `matrix-led-current`).
6. **`C-EN` (C41) is removed**, and with it the C of Espressif's `CHIP_PU`
   RC (#14 A2, #11 F7). `EN` keeps only the Matrix's own `R8`, with no
   capacitor. **#14 A2's start-up RC is an accepted risk, by the owner's
   USB-only choice** (`hardware/carrier/service-uart/service-uart.md`). What
   would show it is a Matrix that does not start on a slow power-up; the
   E-test is a power cycle through the umbilical's soft start. If it fails,
   a 1 µF on the Matrix's own `EN` pad - `R8`'s node, beside Key1 - is the
   fix, on the Matrix, not on these boards. `R-TXD-SER` (R46) and the UART on
   `HDR-SERVICE` stay: `TX` and `RX` are on the Matrix's pad rows.

### The carrier's outline: option A

The owner, on the first carrier layout: *"Why the cutout? And we can
increase the width to acrylic to acrylic like the other boards?"* Shown the
numbers (2026-10-03), the owner chose **A**:

- **The width already is the key boards'**: the carrier runs side acrylic to
  side acrylic, as they do (both `cb_y`).
- **The arm stays narrow because the extension's plug stands beside it.**
  The right-angle plug off the Matrix's mouth edge, its lead turned down
  (`openings.usb_plug_turn`), comes down from the oak's pocket to below the
  carrier, and its lead runs on to the tail under it. A carrier full width in
  front of the Matrix would pass through the plug or its lead at any height.
- **The carrier keeps its height.** A lower carrier would clear the shell
  with no slot, but the Matrix ribbon's closed folds lie between `J-MCU` and
  `J-MCU-C` under the arm, and they already fold at about the least bend
  radius (drc.echo *"Matrix ribbon closed: its folds between the sockets"*).
  Moving `J-MCU` under the carrier meets the main board's end mount,
  `HDR-SERVICE` and the LED row.
- **So the cut-out becomes a slot for the shell only** (`boards.matrix_usb`
  plus `boards.matrix_notch_clear` each side and at its end), and the
  carrier's mouth edge is flush with the Matrix's, behind the plug.
- **The extension's plug is at most `openings.usb_ext_overmold_w` across**
  (`CBL-USB-EXT`, decided with calipers on the cable as bought; since issue #37 the lid-off recovery cable's plug). The study
  found that today's ribbon folds and `J-MCU-C`'s socket stood inside the
  15 mm overmould allowance by up to 2.6 mm, which no rule checked. Now the
  folds stop `board_clear` short of the plug, running back past `J-MCU`'s
  back instead, and drc.echo *"USB-C plug clear of the Matrix ribbon and
  J-MCU-C"* holds both.

Not taken: B, the Matrix's USB-C turned to the tail, the one true no-cut-out
rectangle, at about 8–10 mm more body; and C, the Matrix and its window moved
2 mm toward the far side.

### What this changes for the main board

`C41` comes off its sheet. `HDR-SERVICE` (its `J2`) becomes a 1×3,
`hanxia HX PZ2.54-1x3P ZZ` (LCSC C32713269), at `boards.service_hdr_at`.
`J-MCU` (its `J1`) pins 23 and 24 are on no net. The Matrix's stand-in (`A1`)
is not on the board, as before. Its root sheet loses the `EN` and `IO0` sheet
pins between the carrier and service-uart sheets.

### Open, and what decides each

| Open | What decides it |
|---|---|
| The pad rows' side (the 5V..IO1 row on the near side with the USB-C toward the mouth) | the Matrix in hand, before the carrier is ordered |
| The inserts in oak: they are sold for heat-setting in plastic | one set and pulled in a scrap of the chosen oak, before the lid is drilled |
| `EN`'s start-up with no C (#14 A2) | the power-cycle E-test above |
| Reaching the Matrix's BOOT and RESET buttons, on its underside over the carrier, for recovery (item 5) | the carrier's final outline (2026-10-03: the owner asked for no cut-out, which the plug and the ribbon's fold constrain); with the Matrix in hand, a probe through the gap or an access hole |

## Amendment, 2026-10-07 — the etherCON centred, the MIDI jack beside it on the tail face (issue #45)

The owner, 2026-10-07, verbatim:

> "TRS connector should be on the same side as the ethercon on the controller. The connector on the main PCB should be a 90deg facing the rear. Ethercon should be moved to be center of the bottom/back side as well (same face, just centered, TRS of midi to the side of that)"

and, after a first fit study reported that the jack could not stand beside the centred flange (wrongly; *The first study*, below):

> "TRS can go in corner"

### What is decided

1. **The NE8FAV is centred across the tail face** (`config/body.yaml`
   `ethercon.offset_y`, now settled). It still stands on the floor, latch up.
   J-UMB, the adapter and the main board's tongue follow it across.
2. **The MIDI jack (`J-MIDI-OUT`) goes through the tail cap, in a corner of the
   face** (`midi.corner`), not through the oak bottom. The NE8FAV's two panel
   screws take the upper-near and lower-far corners, so the jack has the other
   two; it is in the upper far one, because `J-MIDI` then sits on the main
   board's far side, where `HDR-SERVICE` is not. Its collar bears on the cap's
   inside face, its body stands in the lane between the flange and the side,
   and a counterbore from outside, round its nut and merging with the
   etherCON's recess, leaves the oak the thread can clamp. The oak bottom carries no jack.
3. **`J-MIDI` is a side-entry JST PH, S3B-PH-SM4-TB, its mouth facing the
   tail** (`midi.hdr_at`, `hdr_sz`), mouthward of J-UMB's pad row, so CBL-MIDI
   runs straight back past J-UMB's insulator and the adapter to the jack.

The fit is proved by `mechanical/drc.echo`: *"MIDI jack in the tail cap"* (the
panel, the counterbore and its oak to the face's edges, the etherCON's bore and
screw holes), *"tail cap web between the etherCON bore and the MIDI jack"*,
*"MIDI jack behind the tail cap"* (the collar to the flange, the side and the
oak top; the jack to the adapter, the main board and J-UMB) and *"J-MIDI
beside J-UMB, facing the tail"*.

### The first study, and why the corner

The first fit study (2026-10-07, before *"TRS can go in corner"*) reported
that the jack did not fit beside the centred flange. **That was wrong, on two
counts.** It read the jack's drawing as the config then did, a 10.0 collar
across its corners and a body as wide as the collar; the drawing's hex is the
nut, 10.0 across its flats, and the collar behind the thread is round
(`midi.jack_nut_af`, `jack_collar`, `jack_body`;
`hardware/carrier/midi-out/notes.md`). And it kept the oak minimum between the
jack's outside cut and the etherCON's recess, though both are cut from the
outer face and the jack's is the deeper, so they merge into one pocket and
the jack's hole is measured to the bore and the screw holes instead. With
both corrected, what binds is the collar in the lane behind the face, which
is the same at any height: the jack would also have fitted at the lane's
middle height.

**The corner is the owner's choice, and it is kept for what it buys outside
the face:** the jack sits further from the etherCON's axis than at the lane's
middle height, which leaves the most room between the TRS plug's overmould and
the cable connector's shell (*Open*, below).

### What this changes for the main board

`J-UMB` and the adapter's joint move with the etherCON's axis, and so do
`J-UMB`'s band of parts (`boards.umb_parts_d`) and the tongue's pads.
`J7` becomes the side-entry footprint
(`woody:JST_PH_S3B-PH-SM4-TB_1x03-1MP_P2.00mm_Horizontal`) at `midi.hdr_at`,
facing the tail, with `U-TVS-MIDI` and the two beads re-placed at it. The
routes into `J-UMB` and `J7` follow. The board is laid out separately, from
`mechanical/export/pcb-geometry.echo`.

### Open, and what decides each

| Open | What decides it |
|---|---|
| The jack's collar clears the flange, the side and the oak top by `midi.jack_clear` exactly, with nothing spare | the jack in hand in a test cap: a collar over its drawing's size meets the flange or the side |
| The TRS plug's overmould beside the etherCON cable connector's shell, both outside the face; and a thumb reaching the PUSH tab past the plug | `ethercon.recess_margin`'s decision, with J-UMBILICAL-CABLE and a TRS lead in hand |
| How far CBL-MIDI's housing stands past J-MIDI's face (`midi.hdr_plug_l`, from the through-hole header's mated drawing) | the SMT header's own mated drawing, or the parts in hand |
| The jack's hole and its counterbore round the nut (`midi.hole_d`, `cbore_clear`) | a test hole in an offcut of the tail cap's oak, with the part and the socket that turns its nut |
